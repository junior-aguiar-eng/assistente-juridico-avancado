"""Avaliação offline de peças com coortes separadas; nunca confere peças humanas."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re


def _sha(p):
    with p.open('rb') as arquivo:
        return hashlib.file_digest(arquivo,'sha256').hexdigest()


def _json(p):
    from pecas import _json as ler
    return ler(p.read_bytes())


def _sha_produto(p,normalizacao):
    if normalizacao == 'bytes':
        return _sha(p)
    if normalizacao != 'lf':
        raise ValueError('normalizacao_produto_invalida')
    return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def _relativo(nome):
    return (isinstance(nome,str) and bool(nome) and not Path(nome).is_absolute()
            and not PureWindowsPath(nome).anchor and '..' not in Path(nome).parts
            and '..' not in PureWindowsPath(nome).parts)


def _unidade(caso):
    return re.sub(r'[^a-z0-9]','',caso['processo_id'].lower())


def validar_manifesto(obj):
    """Metadados explícitos: bytes e processo impedem vazamento entre coortes."""
    try:
        if obj['schema_version'] != '1' or not isinstance(obj['casos'],list) or not obj['casos']:
            raise ValueError('manifesto_invalido')
        if not isinstance(obj['produto_sha256'],dict) or not obj['produto_sha256']:
            raise ValueError('produto_nao_fixado')
        for nome,sha in obj['produto_sha256'].items():
            if not _relativo(nome) or not re.fullmatch('[0-9a-f]{64}',sha):
                raise ValueError('produto_invalido')
        ids,unidades,hashes = set(),{},{}
        for c in obj['casos']:
            if (not re.fullmatch('[A-Za-z0-9_-]{1,80}',c['id']) or c['id'] in ids
                    or c['grupo'] not in ('desenvolvimento','avaliacao')
                    or c['modalidade'] not in ('nativo','sem_ocr','ocr')
                    or c['natureza'] not in ('processo','documento')
                    or not isinstance(c['processo_id'],str) or not c['processo_id'].strip()
                    or not _relativo(c['arquivo']) or not re.fullmatch('[0-9a-f]{64}',c['sha256'])):
                raise ValueError('caso_invalido')
            ids.add(c['id'])
            unidade = _unidade(c)
            for chave,tabela in ((unidade,unidades),(c['sha256'],hashes)):
                if chave in tabela and tabela[chave] != c['grupo']:
                    raise ValueError('vazamento_entre_coortes')
                tabela[chave] = c['grupo']
            ref = c['referencia']
            if (ref['origem'] not in ('modelo_tecnico','sintetico','humano_identificado')
                    or type(ref['conferencia_humana']) is not bool
                    or (ref['conferencia_humana'] and (ref['origem'] != 'humano_identificado'
                        or not isinstance(ref.get('revisor'),str) or not ref['revisor'].strip()))
                    or type(ref['paginas']) is not int or ref['paginas'] < 1
                    or not isinstance(ref['pecas'],list)):
                raise ValueError('referencia_invalida')
            ultimo = 1
            for p in ref['pecas']:
                if (type(p['inicio']) is not int or type(p['fim']) is not int
                        or not ultimo <= p['inicio'] <= p['fim'] <= ref['paginas']
                        or not isinstance(p['tipo'],str) or not p['tipo']):
                    raise ValueError('referencia_invalida')
                ultimo = p['fim']
            if 'amostras' in ref and (not isinstance(ref['amostras'],list)
                    or not all(isinstance(t,str) and t.strip() for t in ref['amostras'])):
                raise ValueError('amostras_invalidas')
    except (KeyError,TypeError,AttributeError):
        raise ValueError('manifesto_invalido') from None


def comparar(esperadas,propostas):
    """Envelopes de página, sem atribuir precisão de caracteres a uma referência."""
    razao = lambda n,d: {'numerador':n,'denominador':d}
    fina = any(a['fim'] >= b['inicio'] for lista in (esperadas,propostas) for a,b in zip(lista,lista[1:]))
    ref = Counter(p['inicio'] for p in esperadas[1:])
    pred = Counter(p['inicio'] for p in propostas[1:])
    por_intervalo = {(p['inicio'],p['fim']):p['tipo'] for p in esperadas}
    tipos = [(por_intervalo[(p['inicio'],p['fim'])],p['tipo']) for p in propostas
             if (p['inicio'],p['fim']) in por_intervalo
             and por_intervalo[(p['inicio'],p['fim'])] != 'nao_identificada']
    return {'precisao':'insuficiente_intrapagina' if fina else 'pagina',
        'pecas_esperadas':len(esperadas),'pecas_propostas':len(propostas),
        'pecas_correspondentes':razao(0,0) if fina else razao(
            sum((p['inicio'],p['fim']) in por_intervalo for p in propostas),len(esperadas)),
        'fronteiras_corretas':razao(0,0) if fina else razao(sum((ref & pred).values()),sum(ref.values())),
        'cortes_propostos':sum(pred.values()),
        'fragmentacoes':None if fina else sum((pred-ref).values()),
        'fusoes':None if fina else sum((ref-pred).values()),
        'tipo_correto':razao(0,0) if fina else razao(sum(a == b for a,b in tipos),len(tipos)),
        'abstencoes':razao(sum(p['tipo'] == 'nao_identificada' for p in propostas),len(propostas))}


def consolidar(casos):
    grupos = []
    for grupo,modo in sorted({(c['grupo'],c['modalidade']) for c in casos}):
        cs = [c for c in casos if (c['grupo'],c['modalidade']) == (grupo,modo)]
        feitos = [c for c in cs if c['execucao'] == 'concluida']
        r = {'grupo':grupo,'modalidade':modo,'observacoes':len(cs),
             'unidades':len({_unidade(c) for c in cs}),
             'processos':len({_unidade(c) for c in cs if c['natureza'] == 'processo'}),
             'avaliados':len(feitos),'nao_avaliados':len(cs)-len(feitos)}
        for metrica in ('fronteiras_corretas','pecas_correspondentes','tipo_correto','abstencoes'):
            r[metrica] = {k:sum(c['metricas'][metrica][k] for c in feitos)
                          for k in ('numerador','denominador')}
        for metrica in ('fragmentacoes','fusoes'):
            valores = [c['metricas'][metrica] for c in feitos if c['metricas'][metrica] is not None]
            r[metrica] = {'total':sum(valores),'casos_mensuraveis':len(valores)}
        grupos.append(r)
    return grupos


def _gravar(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return p


def _integrar(doc,inv,ep,ip,original,pasta):
    import auditar
    import cronologia
    import pecas_uso
    import triagem
    import validate
    f = next((f for f in inv['fragmentos'] if f['destino']['classe'] == 'peca'),None)
    if f is None:
        return {'execucao':'nao_executada','motivo':'nenhum_fragmento_atribuido'}
    b = next(b for b in doc['blocks'] if b['id'] == f['block_id'])
    fonte = {'document_id':doc['document_id'],'block_id':b['id'],
             'locator':f"p.{f['paginas']['inicio']}" if f['paginas']['inicio'] == f['paginas']['fim']
                       else f"p.{f['paginas']['inicio']}-{f['paginas']['fim']}",
             'excerpt':b['text'][f['inicio']:f['fim']],
             'peca':{'inventario_id':inv['inventario_id'],'inventario_sha256':_sha(ip),
                     'piece_id':f['destino']['piece_id'],'fragmentos':[f['id']]}}
    fatos = {'schema_version':'1','facts':[{'id':'observacao-1','kind':'alegacao',
        'text':'Registro de trecho para avaliação mecânica, sem conclusão sobre os fatos do processo.',
        'alleged_by':'documento fornecido','source':fonte}]}
    fp = _gravar(pasta/'facts.json',fatos)
    ctx = pecas_uso.carregar_contexto([ep],[(ip,original)],exigir=True)
    idx = validate.carregar_extracoes([ep])
    a = validate.validar_facts(fatos,idx,pecas=ctx)
    fnd = validate.validar_facts(fatos,idx,pecas=ctx,modo='fundamentada')
    tp,mp = pasta/'timeline.json',pasta/'timeline.md'
    cronologia.gerar(fp,tp,mp,extracoes=[ep],pecas=[(ip,original)],exigir_pecas=True)
    atual = cronologia.conferir(fp,tp,pecas_contexto=ctx)['atualizada']
    gates = {}
    for modo in ('analise','fundamentada'):
        qc = auditar.auditar(fp,None,[ep],modo=modo,base=pasta,
            pecas=[(ip,original)],exigir_pecas=True,timeline=tp)
        _gravar(pasta/f'qc-{modo}.json',qc)
        gates[modo] = next(g['resultado'] for g in qc['gates'] if g['id'] == 'G16_inventario_pecas')
    return {'execucao':'concluida','triagem_integra':triagem.resumir_pecas([ep],[(ip,original)])['valido'],
        'analise_sem_erros':not a.erros,'avisos_pecas':sorted({e['codigo'] for e in a.avisos if e['codigo'].startswith('pecas_')}),
        'fundamentada_bloqueada':bool(fnd.erros),
        'erros_fundamentada':sorted({e['codigo'] for e in fnd.erros}),
        'cronologia_preserva_vinculos':atual,'g16_analise':gates['analise'],
        'g16_fundamentada':gates['fundamentada']}


def avaliar_manifesto(manifesto,raiz,saida):
    """Saída nova explícita; arquivos originais e produto permanecem somente leitura."""
    import extract
    from pecas import validar_inventario
    from pecas_proposta import propor_inventario
    import validate
    raiz,saida = Path(raiz).resolve(),Path(saida).resolve()
    obj = _json(Path(manifesto))
    validar_manifesto(obj)
    for nome,esperado in obj['produto_sha256'].items():
        p = raiz/nome
        if (not p.resolve().is_relative_to(raiz) or p.is_symlink() or not p.is_file()
                or _sha_produto(p,obj.get('produto_normalizacao','bytes')) != esperado):
            raise ValueError('produto_alterado')
    if saida.is_relative_to(raiz):
        raise ValueError('saida_deve_ser_externa_ao_produto')
    saida.mkdir(parents=True,exist_ok=False)
    resultados = []
    for c in obj['casos']:
        r = {k:c[k] for k in ('id','processo_id','natureza','grupo','modalidade','sha256')}
        r.update(referencia_origem=c['referencia']['origem'],conferencia_humana=False)
        resultados.append(r)
        original = raiz/c['arquivo']
        if not original.resolve().is_relative_to(raiz):
            r.update(execucao='falhou',motivo='caminho_fora_da_raiz')
            continue
        if original.is_symlink() or not original.is_file():
            r.update(execucao='nao_executada',motivo='original_indisponivel')
            continue
        if _sha(original) != c['sha256']:
            r.update(execucao='falhou',motivo='original_divergente')
            continue
        pasta = saida/c['id']; pasta.mkdir()
        try:
            doc,_ = extract.extrair(original,ocr=c['modalidade'] == 'ocr')
            if doc['status'] == 'failed' or doc.get('page_count') != c['referencia']['paginas']:
                r.update(execucao='falhou',motivo='extracao_incompativel')
                continue
            ext = {'schema_version':'1','run':{'params':{**extract.PARAMS,'ocr':c['modalidade'] == 'ocr'}},'documents':[doc]}
            ep = _gravar(pasta/'extracao.json',ext)
            inv = propor_inventario(ep.read_bytes(),arquivo_sha256=c['sha256'])
            ip = _gravar(pasta/'pecas.json',inv)
            integro = validar_inventario(inv,ep.read_bytes(),arquivo_sha256=c['sha256'])['valido']
            fs = {f['id']:f for f in inv['fragmentos']}
            propostas = [{'inicio':fs[p['inicio']]['paginas']['inicio'],
                          'fim':fs[p['fim']]['paginas']['fim'],'tipo':p['tipo_proposto']} for p in inv['pecas']]
            amostras = c['referencia'].get('amostras',[])
            texto = ' '.join(b['text'] for b in doc['blocks'])
            r.update(execucao='concluida',extracao_status=doc['status'],paginas=doc['page_count'],
                integridade_inventario=integro,pecas_propostas=propostas,
                leitura=dict(Counter(p['leitura'] for p in inv['paginas'])),
                avisos_extracao=sorted({w['codigo'] for w in doc.get('warnings',[])}),
                metricas=comparar(c['referencia']['pecas'],propostas),
                amostras_textuais={'numerador':sum(validate._contem(texto,t) for t in amostras),'denominador':len(amostras)},
                integracao=_integrar(doc,inv,ep,ip,original,pasta))
        except (ValueError,OSError,TypeError,KeyError) as e:
            r.update(execucao='falhou',motivo='avaliacao_incompativel',erro_classe=type(e).__name__)
        if _sha(original) != c['sha256']:
            raise ValueError('original_alterado_durante_avaliacao')
    resultado = {'schema_version':'1','base_produto':obj['base_produto'],
        'fase':obj.get('fase','avaliacao_congelada'),
        'manifesto_sha256':_sha(Path(manifesto)),'produto_sha256':obj['produto_sha256'],
        'produto_normalizacao':obj.get('produto_normalizacao','bytes'),
        'liberacao_material':False,'casos':resultados,'grupos':consolidar(resultados),
        'limites':['Referências técnicas não equivalem a conferência humana ou revisão jurídica.',
                  'Denominadores zero indicam ausência de medição; fronteiras medidas por página.',
                  'Tipo só comparado em envelopes exatamente correspondentes; não mede classificação universal.',
                  'Amostras OCR não são transcrição integral nem taxa de erro de caracteres.',
                  'Proposta e consumidores congelados; mudanças posteriores exigem nova coorte de avaliação.']}
    _gravar(saida/'resultado.json',resultado)
    return resultado


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifesto',type=Path,required=True)
    p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--saida',type=Path,required=True)
    n = p.parse_args(argv)
    try:
        r = avaliar_manifesto(n.manifesto,n.raiz,n.saida)
        print(json.dumps({'execucao':'concluida','grupos':r['grupos'],'liberacao_material':False},ensure_ascii=False))
        return 1 if any(c['execucao'] == 'falhou' for c in r['casos']) else 0
    except (ValueError,OSError,TypeError) as e:
        print(json.dumps({'execucao':'falhou','erro':type(e).__name__,'motivo':str(e)},ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
