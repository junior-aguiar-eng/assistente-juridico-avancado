"""Vínculo somente leitura entre inventários íntegros e usos concretos de trechos."""
from __future__ import annotations

import hashlib
from bisect import bisect_left, bisect_right
from pathlib import Path
import re

from pecas import _json, validar_inventario


def _sha(bruto):
    return hashlib.sha256(bruto).hexdigest()


def _ler(caminho):
    p = Path(caminho)
    if p.is_symlink() or not p.is_file():
        raise ValueError('entrada indisponível')
    return p.read_bytes()


def adicionar_argumentos(parser):
    parser.add_argument('--pecas', nargs=2, action='append', default=[], metavar=('INVENTARIO', 'ORIGINAL'),
                        help='inventário e original autorizado (repetível); não confirma peças')
    parser.add_argument('--pecas-anterior', action='append', default=[], metavar='ANTERIOR',
                        help='bytes da revisão anterior de um inventário fornecido (repetível)')
    parser.add_argument('--exigir-pecas', action='store_true',
                        help='exigir referência de peça para fontes de documentos paginados')


def _paginas_ocorrencias(textos, fragmentos, trecho, normalizar, declaradas):
    """Páginas da mesma ocorrência textual; não combinar achados de peças distintas.

    Fragmento multipágina só fornece envelope. Não há mapa de caracteres por
    página; nesse caso o localizador precisa conservar todo esse envelope.
    """
    partes = [normalizar(x) for x in re.split(r'\[\.\.\.\]|…', trecho)]
    partes = [x for x in partes if x]
    texto = normalizar(' '.join(textos))
    comprimentos = [len(normalizar(x)) for x in textos]
    if sum(comprimentos) != len(texto):
        # NFC entre recortes pode compor caracteres; não inventar posição fina.
        yield {n for f in fragmentos for n in range(int(f['paginas']['inicio']), int(f['paginas']['fim'])+1)}
        return
    faixas, cursor = [], 0
    for tamanho, f in zip(comprimentos, fragmentos):
        faixas.append((cursor,cursor+tamanho,f))
        cursor += tamanho
    finais = [z for _,z,_ in faixas]

    def indice(posicao):
        return bisect_right(finais,posicao)

    def paginas(inicio,fim):
        return {n for _,_,f in faixas[indice(inicio):indice(fim-1)+1]
                for n in range(int(f['paginas']['inicio']),int(f['paginas']['fim'])+1)}

    # A última parte pode ocorrer várias vezes. Selecionar candidatos que
    # terminem no envelope final declarado evita aceitar a página de outro
    # trecho e evita repetir todas as combinações em uma página longa.
    terminos, procurar = [], 0
    if len(partes) > 1:
        while (pos := texto.find(partes[-1],procurar)) >= 0:
            fim = pos + len(partes[-1])
            f = fragmentos[indice(fim-1)]
            if int(f['paginas']['fim']) == max(declaradas):
                terminos.append(pos)
            procurar = pos + 1
    procurar = 0
    while partes and (inicio := texto.find(partes[0], procurar)) >= 0:
        procurar = inicio + 1
        if int(fragmentos[indice(inicio)]['paginas']['inicio']) != min(declaradas):
            continue
        fim = inicio + len(partes[0])
        if len(partes) == 1:
            yield paginas(inicio,fim)
            continue
        for parte in partes[1:-1]:
            pos = texto.find(parte, fim)
            if pos < 0:
                break
            fim = pos + len(parte)
        else:
            candidato = bisect_left(terminos,fim)
            if candidato < len(terminos):
                yield paginas(inicio,terminos[candidato]+len(partes[-1]))


class ContextoPecas:
    def __init__(self, exigir=False):
        self.exigir = exigir
        self.ativo = exigir
        self.documentos = {}
        self.indice = {}
        self.erros = []
        self.artefatos = []

    def erro(self, codigo, mensagem):
        self.erros.append({'codigo': 'pecas_' + codigo, 'caminho': '--pecas', 'mensagem': mensagem})

    def vinculos(self):
        return sorted(({'inventario_id': d['inv']['inventario_id'], 'document_id': did,
                        'revisao': d['inv']['revisao'], 'sha256': d['sha256']}
                       for did, d in self.documentos.items()), key=lambda d: d['inventario_id'])

    def pendencias_uso(self, dado, peca, fs, secao=None):
        inv, doc = dado['inv'], dado['doc']
        pendencias = []

        def pend(codigo, material=True):
            item = {'codigo': 'pecas_' + codigo, 'material': material,
                    'mensagem': 'Uso do trecho exige resolver ' + codigo + '; inventário não é aprovação.'}
            if item not in pendencias:
                pendencias.append(item)

        for dim in ('limites', 'tipo'):
            if peca[dim]['estado'] != 'conferido':
                pend(dim + '_nao_conferido')
        if secao and secao['conferencia']['estado'] != 'conferido':
            pend('secao_nao_conferida')
        if peca['tipo_proposto'] == 'nao_identificada':
            pend('tipo_nao_identificado')
        paginas = {n for f in fs for n in range(int(f['paginas']['inicio']), int(f['paginas']['fim']) + 1)}
        alvos = {inv['inventario_id'], peca['id']} | {f['id'] for f in fs} | {f'pagina-{n}' for n in paginas}
        alvos.update(s['id'] for s in inv['secoes'] if set(s['fragmentos']) & {f['id'] for f in fs})
        corpo_fs = [f for f in inv['fragmentos'] if f['destino'] == {'classe':'peca','piece_id':peca['id']}]
        corpo = ({f['id'] for f in corpo_fs} | {s['id'] for s in inv['secoes'] if s['piece_id'] == peca['id']}
                 | {f'pagina-{n}' for f in corpo_fs
                    for n in range(int(f['paginas']['inicio']),int(f['paginas']['fim'])+1)})
        if secao:
            alvos.add(secao['id'])
        for f in fs:
            if 'indeterminada' in (f['paginas']['precisao'], f['paginas']['origem']):
                pend('localizacao_indeterminada')
        if any(p['numero'] in paginas and p['leitura'] != 'texto_nativo' for p in inv['paginas']):
            pend('leitura_insuficiente')
        for p in inv['pendencias']:
            pertinentes = alvos | corpo if p['codigo'] in ('limite_incerto','tipo_nao_identificado') else alvos
            if set(p['referencias']) & pertinentes:
                pend(p['codigo'], p['material'])
        blocos = {f['block_id'] for f in fs}
        usados = [b for b in doc['blocks'] if b['id'] in blocos]
        if (any('atribuicao_ambigua' in b.get('tags', []) for b in usados)
                or len({bool(b.get('is_quote')) for b in usados}) > 1):
            pend('atribuicao_ambigua')
        for a in doc.get('warnings', []):
            pagina = a.get('page', a.get('pagina'))
            if pagina is None or pagina in paginas:
                pend('aviso_extracao')
        return pendencias

    def conferir_fonte(self, fonte, locator, trecho, idx):
        """Erros de identidade são incondicionais; pendências são avaliadas por modo."""
        import validate  # funções legadas de comparação/localização, sem ciclo na importação

        erros, pendencias = [], []

        def erro(codigo):
            erros.append({'codigo': 'pecas_' + codigo, 'mensagem': 'Referência de peça incompatível: ' + codigo + '.'})

        ref = fonte.get('peca')
        did = fonte.get('document_id')
        doc_idx = (idx or {}).get(did) if isinstance(did, str) else None
        exigida = did in self.documentos if isinstance(did, str) else False
        exigida = exigida or (self.exigir and (doc_idx is None or bool(doc_idx.get('page_count'))))
        if 'peca' not in fonte:
            if exigida:
                erro('referencia_ausente')
            return erros, pendencias
        campos = {'inventario_id', 'inventario_sha256', 'piece_id', 'fragmentos'}
        if (not isinstance(ref, dict) or not campos <= ref.keys() or ref.keys() - (campos | {'secao_id'})
                or not all(isinstance(ref.get(k), str) and ref[k].strip() for k in campos - {'fragmentos'})
                or not re.fullmatch('[0-9a-f]{64}', ref['inventario_sha256'])
                or not isinstance(ref.get('fragmentos'), list) or not ref['fragmentos']
                or not all(isinstance(x, str) and x for x in ref['fragmentos'])
                or len(set(ref['fragmentos'])) != len(ref['fragmentos'])
                or ('secao_id' in ref and (not isinstance(ref['secao_id'], str) or not ref['secao_id']))):
            erro('referencia_incompativel')
            return erros, pendencias
        dado = self.documentos.get(did) if isinstance(did, str) else None
        if dado is None:
            erro('inventario_ausente')
            return erros, pendencias
        inv, doc = dado['inv'], dado['doc']
        if (ref['inventario_id'] != inv['inventario_id'] or ref['inventario_sha256'] != dado['sha256']
                or doc_idx != doc):
            erro('referencia_incompativel')
            return erros, pendencias
        peca = next((p for p in inv['pecas'] if p['id'] == ref['piece_id']), None)
        fragmentos = {f['id']: f for f in inv['fragmentos']}
        fs = [fragmentos.get(fid) for fid in ref['fragmentos']]
        if (peca is None or any(f is None or f['destino'] != {'classe': 'peca', 'piece_id': ref['piece_id']} for f in fs)):
            erro('referencia_incompativel')
            return erros, pendencias
        ordem = {b['id']: i for i, b in enumerate(doc['blocks'])}
        ordenados = sorted(fs, key=lambda f: (ordem[f['block_id']], f['inicio']))
        if (fs != ordenados or (fonte.get('block_id') and any(f['block_id'] != fonte['block_id'] for f in fs))):
            erro('referencia_incompativel')
            return erros, pendencias
        blocos = {b['id']: b for b in doc['blocks']}
        for a, b in zip(fs, fs[1:]):
            continua = (a['block_id'] == b['block_id'] and a['fim'] == b['inicio']) or (
                ordem[b['block_id']] == ordem[a['block_id']] + 1
                and a['fim'] == len(blocos[a['block_id']]['text']) and b['inicio'] == 0)
            if not continua:
                erro('fragmentos_descontinuos')
        textos = [blocos[f['block_id']]['text'][int(f['inicio']):int(f['fim'])] for f in fs]
        if (not isinstance(trecho, str) or not validate._contem(' '.join(textos), trecho)
                or not re.search(r'\w', re.sub(r'\[\.\.\.\]|…', '', trecho))):
            erro('trecho_incompativel')
        paginas = {n for f in fs for n in range(int(f['paginas']['inicio']), int(f['paginas']['fim']) + 1)}
        ranges = validate._paginas_do_localizador(locator)
        if not ranges or any(a > z or any(n not in paginas for n in range(a, z + 1)) for a, z in ranges):
            erro('localizador_incompativel')
        elif isinstance(trecho,str):
            declaradas = {n for a,z in ranges for n in range(a,z+1)}
            if declaradas not in _paginas_ocorrencias(textos,fs,trecho,validate._norm,declaradas):
                erro('localizador_incompativel')
        secao = None
        if 'secao_id' in ref:
            secao = next((s for s in inv['secoes'] if s['id'] == ref['secao_id']), None)
            if (secao is None or secao['piece_id'] != peca['id'] or not set(ref['fragmentos']) <= set(secao['fragmentos'])):
                erro('secao_incompativel')
        if not erros:
            pendencias = self.pendencias_uso(dado, peca, fs, secao)
        return erros, pendencias

    def resumo(self):
        inventarios = []
        for vinculo in self.vinculos():
            dado = self.documentos[vinculo['document_id']]
            inv = dado['inv']
            ps = []
            for p in inv['pecas']:
                fs = [f for f in inv['fragmentos'] if f['destino'] == {'classe':'peca','piece_id':p['id']}]
                ps.append({'piece_id':p['id'], 'tipo_proposto':p['tipo_proposto'],
                           'limites':p['limites']['estado'], 'tipo':p['tipo']['estado'],
                           'pendencias':self.pendencias_uso(dado,p,fs)})
            inventarios.append({**vinculo, 'paginas':inv['paginas'], 'pecas':ps,
                                'pendencias':[{'codigo':p['codigo'],'material':p['material'],
                                               'referencias':p['referencias']} for p in inv['pendencias']]})
        return {'valido':not self.erros, 'exigir_pecas':self.exigir, 'inventarios':inventarios, 'erros':self.erros}


def carregar_contexto(extracoes=(), pecas=(), *, anteriores=(), exigir=False):
    """Não procura originais/extrações usando caminhos declarados por documentos."""
    contexto = ContextoPecas(exigir)
    contexto.ativo = bool(pecas or anteriores or exigir)
    if not contexto.ativo:
        return contexto
    try:
        fontes = {}
        documentos = {}
        for caminho in extracoes:
            bruto = _ler(caminho)
            obj = _json(bruto)
            docs = obj.get('documents', [obj])
            for doc in docs:
                did = doc.get('document_id')
                if did in documentos and documentos[did] != _sha(bruto):
                    raise ValueError('documento ambíguo entre extrações')
                documentos[did] = _sha(bruto)
                contexto.indice[did] = doc
            fontes[_sha(bruto)] = (bruto, Path(caminho))
        prevs = {}
        for p in anteriores:
            anterior_bytes = _ler(p)
            prevs[_sha(anterior_bytes)] = (anterior_bytes,Path(p))
        usados = set()
        for caminho, original in pecas:
            bruto = _ler(caminho)
            inv = _json(bruto)
            if not isinstance(inv, dict) or not isinstance(inv.get('origem'), dict):
                raise ValueError('inventário incompatível')
            origem = inv['origem']
            entrada = fontes.get(origem.get('extracao_sha256'))
            if entrada is None:
                contexto.erro('extracao_divergente', 'Extração exata não fornecida em --extracoes.')
                continue
            ep_bytes, ep = entrada
            op = Path(original)
            if op.is_symlink() or not op.is_file():
                raise ValueError('original indisponível')
            with op.open('rb') as arquivo:
                sha_original = hashlib.file_digest(arquivo, 'sha256').hexdigest()
            anterior = prevs.get(inv.get('anterior_sha256'))
            r = validar_inventario(inv, ep_bytes, arquivo_sha256=sha_original,
                                   anterior_bytes=anterior[0] if anterior else None)
            if r['erros']:
                for e in r['erros']:
                    contexto.erro(e['codigo'], e['mensagem'])
                continue
            did = origem['document_id']
            if did in contexto.documentos or any(d['inv']['inventario_id'] == inv['inventario_id'] for d in contexto.documentos.values()):
                contexto.erro('origem_ambigua', 'Forneça uma revisão corrente por documento e inventário.')
                continue
            pacote = _json(ep_bytes)
            doc = next(d for d in pacote.get('documents', [pacote]) if d['document_id'] == did)
            contexto.documentos[did] = {'inv':inv,'sha256':_sha(bruto),'doc':doc,'original':op}
            contexto.artefatos += [(Path(caminho),'inventario_pecas'),(op,'fonte'),(ep,'extracao')]
            if anterior:
                usados.add(inv['anterior_sha256'])
                contexto.artefatos.append((anterior[1],'inventario_pecas_anterior'))
        if set(prevs) - usados:
            contexto.erro('historico_incompativel', 'Revisão anterior sem vínculo com os inventários fornecidos.')
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
        contexto.erro('entrada_invalida', 'Insumos do inventário indisponíveis, ambíguos ou incompatíveis.')
    return contexto
