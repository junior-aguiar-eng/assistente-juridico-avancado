"""EV-02: avaliação offline pura de anotações, sem inferência ou aprovação jurídica.

O chamador fornece snapshots; nenhum caminho, rede, modelo ou credencial é aberto.
Notas e correspondências provêm de julgamento humano declarado e vinculado por hash.
"""
from collections import Counter, defaultdict
from datetime import date
from functools import wraps
import hashlib
import json
import math
import re
from statistics import mean, median

DIMENSOES = ('conexao', 'contraposicoes', 'consequencias', 'limites')
CLASSES = ('questao', 'pedido', 'argumento', 'fato', 'resultado', 'alcance')
ESTADOS = ('concluida', 'abstencao', 'falha', 'timeout', 'invalida', 'limite', 'nao_executada')
FALHAS = ESTADOS[2:]


def _dominio(func):
    @wraps(func)
    def executar(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (KeyError, TypeError, AttributeError, OverflowError):
            raise ValueError('estrutura_invalida') from None
    return executar


def sha_bytes(valor):
    return hashlib.sha256(valor).hexdigest()


def sha_objeto(obj):
    """Hash lógico JSON canônico; NÃO equivale ao hash dos bytes do arquivo bruto."""
    return sha_bytes(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                               separators=(',', ':'), allow_nan=False).encode('utf-8'))


def _exigir(condicao, codigo):
    if not condicao:
        raise ValueError(codigo)


def _texto(v):
    return isinstance(v, str) and bool(v.strip())


def _unidade(v):
    _exigir(_texto(v), 'identidade_invalida')
    s = re.sub(r'[^a-z0-9]', '', v.lower())
    _exigir(bool(s), 'identidade_invalida')
    return s


def _hash(v):
    return isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v) is not None


def _numero(v):
    return type(v) in (int, float) and math.isfinite(v) and v >= 0


def _inteiro(v, minimo=0):
    return type(v) is int and v >= minimo


def _ratio(n, d):
    return {'numerador': n, 'denominador': d, 'valor': n/d if d else None}


def _hashes(obj):
    _exigir(isinstance(obj, dict) and bool(obj), 'snapshots_invalidos')
    _exigir(all(_texto(k) and _hash(v) for k, v in obj.items()), 'snapshots_invalidos')


def _revisor(obj, campo='status'):
    _exigir(isinstance(obj, dict) and obj.get(campo) in ('pendente', 'conferido'), 'revisao_invalida')
    if obj[campo] == 'pendente':
        return False
    _exigir(_texto(obj.get('revisor')), 'revisor_ausente')
    try:
        date.fromisoformat(obj['data'])
    except (ValueError, TypeError, KeyError):
        raise ValueError('data_revisao_invalida') from None
    return True


def _itens(lista):
    _exigir(isinstance(lista, list), 'itens_invalidos')
    _exigir(all(isinstance(i, dict) and _texto(i.get('id')) for i in lista), 'item_invalido')
    idx = {i['id']: i for i in lista}
    _exigir(len(idx) == len(lista), 'item_duplicado')
    return idx


def _predicao(p):
    _exigir(isinstance(p, dict) and p.get('schema_version') == '1', 'predicao_invalida')
    for k in ('execucao_id', 'caso_id', 'serie_id', 'modelo_id'):
        _exigir(_texto(p.get(k)), 'metadados_execucao_invalidos')
    for k in ('processo_id', 'familia_id'):
        _unidade(p.get(k))
    _exigir(p.get('grupo') in ('desenvolvimento', 'reservado'), 'grupo_invalido')
    _exigir(p.get('variante') in ('A', 'B', 'C') and _inteiro(p.get('repeticao'), 1), 'variante_invalida')
    _exigir(p.get('experimento') in ('semantico', 'ponta_a_ponta')
            and p.get('condicao') in ('nativa', 'assistida'), 'experimento_invalido')
    _exigir(p.get('estado') in ESTADOS, 'estado_invalido')
    for k in ('config_sha256', 'prompt_sha256', 'produto_sha256'):
        _exigir(_hash(p.get(k)), 'hash_execucao_invalido')
    _hashes(p.get('entradas_sha256'))
    _exigir(_hash(p.get('saida_sha256')) or
            (p['estado'] in FALHAS and p.get('saida_sha256') is None), 'saida_nao_fixada')
    itens = _itens(p.get('itens'))
    _exigir(all(i.get('tipo') in ('afirmacao', 'limitacao') and _texto(i.get('texto'))
                for i in itens.values()), 'item_predicao_invalido')
    op = p.get('operacao')
    _exigir(isinstance(op, dict) and _inteiro(op.get('chamadas')), 'operacao_invalida')
    for k in ('custo_usd', 'latencia_segundos'):
        _exigir(op.get(k) is None or _numero(op.get(k)), 'operacao_invalida')
    return itens


def _gabarito(g, p):
    _exigir(isinstance(g, dict) and g.get('schema_version') == '1', 'gabarito_invalido')
    for k in ('caso_id', 'grupo', 'entradas_sha256'):
        _exigir(g.get(k) == p[k], 'gabarito_de_outro_caso_ou_snapshot')
    for k in ('processo_id', 'familia_id'):
        _exigir(_unidade(g.get(k)) == _unidade(p[k]), 'gabarito_de_outro_caso_ou_snapshot')
    revisto = _revisor(g.get('revisao'))
    itens = _itens(g.get('itens'))
    _exigir(bool(itens), 'gabarito_sem_itens')
    for i in itens.values():
        _exigir(i.get('classe') in CLASSES and _texto(i.get('descricao'))
                and type(i.get('central')) is bool and type(i.get('respondivel')) is bool,
                'item_gabarito_invalido')
        fontes = i.get('fontes')
        _exigir(isinstance(fontes, list) and bool(fontes), 'fonte_gabarito_ausente')
        _exigir(all(isinstance(f, dict) and f.get('artifact_id') in p['entradas_sha256']
                    and _texto(f.get('localizador')) for f in fontes), 'fonte_gabarito_invalida')
    rubrica = g.get('rubrica')
    _exigir(isinstance(rubrica, dict) and set(rubrica) == set(DIMENSOES), 'rubrica_invalida')
    for v in rubrica.values():
        _exigir(isinstance(v, dict) and type(v.get('aplicavel')) is bool
                and (v['aplicavel'] or _texto(v.get('motivo'))), 'rubrica_invalida')
    return itens, revisto


@_dominio
def avaliar_caso(predicao: dict, gabarito: dict, julgamento: dict) -> dict:
    """Conta anotações declaradas, sem ler/produzir conclusões ou autenticar pessoas.

    Entradas incoerentes levantam ValueError. Falta de conferência mantém avaliação
    pendente. Falhas técnicas com gabarito conferido têm cobertura/profundidade zero,
    preservando incerteza sobre tempo humano, referências e erros jurídicos.
    """
    p, g, j = predicao, gabarito, julgamento
    pi = _predicao(p)
    gi, ouro = _gabarito(g, p)
    revisado = _revisor(j)
    if revisado:
        _exigir(j.get('schema_version') == '1' and j.get('execucao_id') == p['execucao_id'],
                'julgamento_de_outra_execucao')
        _exigir(j.get('predicao_sha256') == sha_objeto(p)
                and j.get('gabarito_sha256') == sha_objeto(g), 'julgamento_desatualizado')
    resultado = {k: p[k] for k in ('execucao_id', 'caso_id', 'processo_id', 'familia_id',
                 'grupo', 'serie_id', 'modelo_id', 'config_sha256', 'prompt_sha256',
                 'produto_sha256', 'experimento', 'variante', 'repeticao', 'condicao', 'estado')}
    resultado.update(schema_version='avaliacao-1', avaliacao='pendente', metricas=None,
                     entradas_sha256=dict(p['entradas_sha256']), gabarito_sha256=sha_objeto(g),
                     criterios=None, profundidade=None, revisao_ativa_segundos=None,
                     perguntas_triviais=None, referencias=None,
                     operacao=dict(p['operacao']), erros_criticos=None)
    if not ouro or (not revisado and p['estado'] not in FALHAS):
        return resultado
    falha = p['estado'] in FALHAS
    corretos, abstencoes, indevidas, correspondencias = set(), set(), set(), []
    if not falha:
        correspondencias = j.get('correspondencias')
        _exigir(isinstance(correspondencias, list), 'correspondencias_invalidas')
        vistos, alvos = set(), set()
        for c in correspondencias:
            _exigir(isinstance(c, dict), 'correspondencia_invalida')
            a, b, estado = c.get('predicao_id'), c.get('gabarito_id'), c.get('resultado')
            _exigir(a in pi and a not in vistos and (b is None or b in gi and b not in alvos),
                    'correspondencia_invalida')
            _exigir(estado in ('correto', 'incorreto', 'abstencao_correta', 'abstencao_indevida'),
                    'correspondencia_invalida')
            vistos.add(a)
            if b is not None:
                alvos.add(b)
            if estado == 'correto':
                _exigir(b is not None and pi[a]['tipo'] == 'afirmacao' and gi[b]['respondivel'],
                        'acerto_incoerente')
                corretos.add(b)
            elif estado.startswith('abstencao'):
                _exigir(b is not None and pi[a]['tipo'] == 'limitacao', 'abstencao_incoerente')
                _exigir(gi[b]['respondivel'] == (estado == 'abstencao_indevida'), 'abstencao_incoerente')
                (abstencoes if estado == 'abstencao_correta' else indevidas).add(b)
        _exigir(vistos == set(pi), 'predicao_sem_julgamento')
    centrais = {k for k, v in gi.items() if v['central']}
    metricas = {'recall': _ratio(len(corretos), len(gi)),
                'precisao': _ratio(len(corretos), sum(i['tipo'] == 'afirmacao' for i in pi.values())),
                'centrais_tratados': _ratio(len(centrais & (corretos | abstencoes)), len(centrais)),
                'abstencoes_corretas': len(abstencoes), 'abstencoes_indevidas': len(indevidas),
                'por_classe': {classe: _ratio(sum(gi[k]['classe'] == classe for k in corretos),
                    sum(v['classe'] == classe for v in gi.values())) for classe in CLASSES}}
    profundidade = {}
    for d in DIMENSOES:
        nota = None if not g['rubrica'][d]['aplicavel'] else 0 if falha else j.get('profundidade', {}).get(d)
        _exigir(nota is None and not g['rubrica'][d]['aplicavel'] or
                type(nota) in (int, float) and math.isfinite(nota) and 0 <= nota <= 4, 'nota_invalida')
        if not falha and not g['rubrica'][d]['aplicavel']:
            _exigir(j.get('profundidade', {}).get(d) is None, 'nota_na_incoerente')
        profundidade[d] = nota
    refs, criticos, silenciosos, tempo, perguntas = None, None, None, None, None
    if revisado:
        _exigir(_numero(j.get('revisao_ativa_segundos')) and _inteiro(j.get('perguntas_triviais')),
                'medida_humana_invalida')
        tempo, perguntas = j['revisao_ativa_segundos'], j['perguntas_triviais']
        refs = j.get('referencias')
        _exigir(isinstance(refs, dict) and _inteiro(refs.get('resolvidas'))
                and _inteiro(refs.get('total')) and refs['resolvidas'] <= refs['total'], 'referencias_invalidas')
        refs = _ratio(refs['resolvidas'], refs['total'])
        erros = _itens(j.get('erros'))
        _exigir(all(type(e.get('critico')) is bool and type(e.get('silencioso')) is bool
                    and _texto(e.get('motivo')) for e in erros.values()), 'erro_invalido')
        criticos = sum(e['critico'] for e in erros.values())
        silenciosos = sum(e['critico'] and e['silencioso'] for e in erros.values())
    resultado.update(avaliacao='falha_tecnica' if falha else 'julgada', metricas=metricas,
                     profundidade=profundidade, revisao_ativa_segundos=tempo,
                     perguntas_triviais=perguntas, referencias=refs, erros_criticos=criticos,
                     criterios={'sem_erro_critico': criticos == 0 if revisado else None,
                                'sem_erro_critico_silencioso': silenciosos == 0 if revisado else None})
    return resultado


def _macro(rs, extrair):
    """Média das médias por processo; repetições não pesam como processos novos."""
    por_processo = defaultdict(list)
    for r in rs:
        v = extrair(r)
        if v is not None:
            por_processo[_unidade(r['processo_id'])].append(v)
    valores = [mean(v) for v in por_processo.values()]
    return _ratio(sum(valores), len(valores))


@_dominio
def agregar_resultados(resultados: list[dict]) -> list[dict]:
    """Não infere execuções ausentes: registrar cada posição planejada, até não executada.

    Séries, experimentos e recuperação assistida são estratos distintos. Médias
    jurídicas pendentes não viram zero; cobertura da avaliação explicita essa falta.
    """
    _exigir(isinstance(resultados, list), 'resultados_invalidos')
    grupos, ids, posicoes, series, contextos = defaultdict(list), set(), set(), {}, {}
    for r in resultados:
        _exigir(isinstance(r, dict) and r.get('schema_version') == 'avaliacao-1', 'resultado_invalido')
        _exigir(r['execucao_id'] not in ids, 'execucao_duplicada'); ids.add(r['execucao_id'])
        serie = (r['modelo_id'], r['config_sha256'], r['prompt_sha256'])
        _exigir(r['serie_id'] not in series or series[r['serie_id']] == serie, 'serie_instavel')
        series[r['serie_id']] = serie
        if r['experimento'] == 'semantico':
            unidade = (r['grupo'], _unidade(r['processo_id']))
            contexto = (r['entradas_sha256'], r['gabarito_sha256'])
            _exigir(unidade not in contextos or contextos[unidade] == contexto,
                    'contexto_semantico_variavel')
            contextos[unidade] = contexto
        chave = tuple(r[k] for k in ('serie_id', 'modelo_id', 'config_sha256', 'experimento', 'condicao', 'grupo', 'variante'))
        posicao = (*chave, _unidade(r['processo_id']), r['repeticao'])
        _exigir(posicao not in posicoes, 'repeticao_duplicada'); posicoes.add(posicao)
        grupos[chave].append(r)
    saida = []
    for chave, rs in sorted(grupos.items()):
        a = dict(zip(('serie_id', 'modelo_id', 'config_sha256', 'experimento', 'condicao', 'grupo', 'variante'), chave))
        medidos = [r for r in rs if r['metricas'] is not None]
        a.update(execucoes=len(rs), processos=len({_unidade(r['processo_id']) for r in rs}),
                 familias=len({_unidade(r['familia_id']) for r in rs}), estados=dict(Counter(r['estado'] for r in rs)),
                 cobertura_avaliacao=_ratio(len(medidos), len(rs)),
                 pior_recall=min((r['metricas']['recall']['valor'] for r in medidos), default=None))
        for nome in ('recall', 'precisao', 'centrais_tratados'):
            a[nome+'_micro'] = _ratio(sum(r['metricas'][nome]['numerador'] for r in medidos),
                                      sum(r['metricas'][nome]['denominador'] for r in medidos))
            a[nome+'_macro'] = _macro(medidos, lambda r: r['metricas'][nome]['valor'])
        a['profundidade'] = {d: _macro(medidos, lambda r: r['profundidade'][d]) for d in DIMENSOES}
        a['tempo_ativo_mediana_por_processo'] = {}
        for processo in sorted({_unidade(r['processo_id']) for r in rs}):
            tempos = [r['revisao_ativa_segundos'] for r in rs
                      if _unidade(r['processo_id']) == processo and r['revisao_ativa_segundos'] is not None]
            a['tempo_ativo_mediana_por_processo'][processo] = median(tempos) if tempos else None
        custos = [r['operacao']['custo_usd'] for r in rs if r['operacao']['custo_usd'] is not None]
        a['custo_usd_conhecido'] = sum(custos)
        a['custos_desconhecidos'] = len(rs)-len(custos)
        a['chamadas'] = sum(r['operacao']['chamadas'] for r in rs)
        a['erros_criticos_conhecidos'] = sum(r['erros_criticos'] for r in rs if r['erros_criticos'] is not None)
        a['execucoes_sem_julgamento_critico'] = sum(r['erros_criticos'] is None for r in rs)
        a['perguntas_triviais_conhecidas'] = sum(r['perguntas_triviais'] for r in rs if r['perguntas_triviais'] is not None)
        saida.append(a)
    return saida


@_dominio
def validar_corpus(manifesto: dict, entradas: dict[str, bytes]) -> dict:
    """Confere metadados/bytes, sobreposição e cobertura planejada, sem ler o mérito.

    duplicata_id é agrupamento curatorial de duplicatas substanciais. Hash não
    descobre parentesco recursal ou duplicata semântica ausente dos metadados.
    """
    _exigir(isinstance(manifesto, dict) and manifesto.get('schema_version') == '1'
            and isinstance(manifesto.get('casos'), list) and isinstance(entradas, dict), 'corpus_invalido')
    cs = manifesto['casos']; ids, artefatos, tabelas = set(), set(), [dict() for _ in range(4)]
    donos_bytes, bytes_repetidos = {}, set()
    for c in cs:
        _exigir(isinstance(c, dict) and _texto(c.get('id')) and c['id'] not in ids, 'caso_duplicado_ou_invalido')
        ids.add(c['id'])
        grupo = c.get('grupo'); _exigir(grupo in ('desenvolvimento', 'reservado'), 'grupo_invalido')
        for k in ('tribunal', 'origem'):
            _exigir(_texto(c.get(k)), 'metadados_corpus_invalidos')
        _exigir(c.get('modalidade') in ('nativo', 'digitalizado', 'misto')
                and _inteiro(c.get('paginas'), 1) and _inteiro(c.get('pecas'), 1), 'metadados_corpus_invalidos')
        for k, tabela in zip(('processo_id', 'familia_id', 'duplicata_id'), tabelas):
            unidade = _unidade(c.get(k))
            _exigir(unidade not in tabela or tabela[unidade] == grupo, 'vazamento_entre_coortes')
            if k == 'processo_id':
                _exigir(unidade not in tabela, 'processo_duplicado')
            tabela[unidade] = grupo
        aa = c.get('artefatos'); _exigir(isinstance(aa, list), 'artefatos_invalidos')
        _exigir({'original', 'extracao'} <= {a.get('tipo') for a in aa if isinstance(a, dict)}, 'snapshots_ausentes')
        for a in aa:
            _exigir(isinstance(a, dict) and _texto(a.get('id')) and a['id'] not in artefatos
                    and a.get('tipo') in ('original', 'extracao') and _hash(a.get('sha256')), 'artefato_invalido')
            artefatos.add(a['id']); b = entradas.get(a['id'])
            _exigir(isinstance(b, bytes) and bool(b) and sha_bytes(b) == a['sha256'], 'snapshot_ausente_ou_alterado')
            h = a['sha256']; tabela = tabelas[3]
            _exigir(h not in tabela or tabela[h] == grupo, 'vazamento_por_bytes')
            tabela[h] = grupo
            if h in donos_bytes and donos_bytes[h] != c['id']:
                bytes_repetidos.add(grupo)
            donos_bytes[h] = c['id']
    contagens = {g: sum(c['grupo'] == g for c in cs) for g in ('desenvolvimento', 'reservado')}
    reservados = [c for c in cs if c['grupo'] == 'reservado']
    estratos = {'acordao_isolado': sum(c['pecas'] == 1 and c['paginas'] <= 40 for c in reservados),
                '3_10_pecas': sum(3 <= c['pecas'] <= 10 and c['paginas'] <= 120 for c in reservados),
                '11_30_pecas': sum(11 <= c['pecas'] <= 30 and c['paginas'] <= 250 for c in reservados)}
    modalidades = dict(Counter(c['modalidade'] for c in reservados))
    lacunas = []
    for g, minimo in (('desenvolvimento', 6), ('reservado', 12)):
        if contagens[g] < minimo:
            lacunas.append(f'{g}: {contagens[g]}/{minimo} processos')
    for e, n in estratos.items():
        if n < 4:
            lacunas.append(f'{e}: {n}/4 processos reservados')
    for m, minimo in (('nativo', 6), ('digitalizado', 3), ('misto', 3)):
        if modalidades.get(m, 0) < minimo:
            lacunas.append(f'{m}: {modalidades.get(m, 0)}/{minimo} processos reservados')
    tribunais = len({_unidade(c['tribunal']) for c in reservados})
    origens_ocr = len({_unidade(c['origem']) for c in reservados if c['modalidade'] != 'nativo'})
    if tribunais < 3:
        lacunas.append(f'tribunais reservados: {tribunais}/3')
    if origens_ocr < 2:
        lacunas.append(f'origens OCR/misto reservadas: {origens_ocr}/2')
    familias = {g: len({_unidade(c['familia_id']) for c in cs if c['grupo'] == g}) for g in contagens}
    if any(familias[g] != contagens[g] for g in contagens):
        lacunas.append('famílias repetidas: processos não são unidades independentes')
    duplicatas = {g: len({_unidade(c['duplicata_id']) for c in cs if c['grupo'] == g}) for g in contagens}
    if any(duplicatas[g] != contagens[g] for g in contagens):
        lacunas.append('duplicatas substanciais repetidas: processos não são unidades independentes')
    if bytes_repetidos:
        lacunas.append('bytes repetidos entre processos da mesma coorte: ' + ', '.join(sorted(bytes_repetidos)))
    return {'valido': True, 'processos': contagens, 'familias': familias, 'estratos': estratos,
            'duplicatas_distintas': duplicatas, 'modalidades_reservadas': modalidades, 'tribunais_reservados': tribunais,
            'origens_ocr_reservadas': origens_ocr, 'cobertura_planejada': not lacunas, 'lacunas': lacunas}
