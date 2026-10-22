"""Proposta heurística opcional; não é classificador jurídico nem conferência humana."""
from datetime import datetime, timezone
import re
import unicodedata

from pecas_validacao import leitura_fonte
from pecas import _documento, _json, _sha, _SCHEMA, validar_inventario

_TIPOS = set(_SCHEMA['$defs']['peca']['properties']['tipo_proposto']['enum'])
_TITULOS = {'sentenca': 'sentenca', 'acordao': 'acordao', 'despacho': 'despacho',
            'decisao interlocutoria': 'decisao_interlocutoria', 'peticao inicial': 'peticao_inicial',
            'contestacao': 'contestacao', 'manifestacao do ministerio publico': 'manifestacao_mp'}


def _titulo(b):
    if b.get('is_quote'):
        return None
    texto = b['text']
    normal = ''.join(''.join(c for c in unicodedata.normalize('NFD', ch) if not unicodedata.combining(c)).lower() for ch in texto)
    # A normalização abaixo não altera o comprimento de letras portuguesas pré-compostas.
    if len(normal) != len(texto):
        return None  # offsets nunca são adivinhados a partir de texto normalizado
    for titulo, tipo in _TITULOS.items():
        padrao = r'\s*'.join(re.escape(c) for c in titulo.replace(' ', ''))
        m = re.match(r'[^\w]*(' + padrao + r')(?=\s*(?:[.:\n]|$))', normal)
        if m:
            return {'block_id': b['id'], 'offset': m.start(1), 'tipo': tipo}
    return None


def propor_inventario(extracao_bytes: bytes, *, arquivo_sha256: str, document_id: str | None = None,
                       fronteiras: list[dict] | None = None) -> dict:
    """Novo inventário, nunca revisão implícita. Cortes manuais continuam propostos.

    Quando fornecidas, fronteiras substituem todos os detectores automáticos.
    Fronteira: block_id, offset Unicode, tipo; opcionalmente pagina_anterior e
    pagina_inicio para localizar visualmente um corte em bloco multipágina.
    """
    pacote = _json(extracao_bytes)
    docs = pacote.get('documents', [pacote])
    if document_id is None:
        if len(docs) != 1:
            raise ValueError('Selecionar exatamente um documento.')
        document_id = docs[0].get('document_id')
    doc = _documento(pacote, {'document_id': document_id})
    if doc.get('sha256') != arquivo_sha256:
        raise ValueError('Original divergente da extração.')
    blocos = {b['id']: b for b in doc['blocks']}
    cortes = {}
    for b in doc['blocks']:
        t = _titulo(b)
        if t and b.get('section') != 'rodape':
            cortes[(b['id'], t['offset'])] = t
    if fronteiras is not None:
        cortes = {}  # revisão manual substitui integralmente os detectores
    manuais = fronteiras or []
    for t in manuais:
        if not isinstance(t, dict) or set(t) - {'block_id', 'offset', 'tipo', 'pagina_anterior', 'pagina_inicio'}:
            raise ValueError('Fronteira manual incompatível.')
        b = blocos.get(t.get('block_id'))
        if (not b or type(t.get('offset')) is not int or not 0 <= t['offset'] < len(b['text'])
                or t.get('tipo') not in _TIPOS):
            raise ValueError('Fronteira manual incompatível com bloco ou taxonomia.')
        for campo in ('pagina_anterior', 'pagina_inicio'):
            if campo in t and (type(t[campo]) is not int or not b['page'] <= t[campo] <= b.get('page_end', b['page'])):
                raise ValueError('Página manual incompatível com envelope da fonte.')
        if ('pagina_anterior' in t) != ('pagina_inicio' in t):
            raise ValueError('Localização de corte exige as duas páginas adjacentes.')
        if 'pagina_inicio' in t and (t['offset'] == 0 or t['pagina_anterior'] > t['pagina_inicio']):
            raise ValueError('Localização manual incompatível com o corte.')
        if (b['id'], t['offset']) in cortes:
            raise ValueError('Duas fronteiras manuais na mesma posição.')
        cortes[(b['id'], t['offset'])] = {**t, '_manual': True}
    params = pacote.get('run', {}).get('params')
    from json import dumps
    config = None if 'params' not in pacote.get('run', {}) else _sha(dumps(params, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
    versoes = doc.get('extractor_versions', {})
    identidade = extracao_bytes if len(docs) == 1 else extracao_bytes + b'\0' + document_id.encode('utf-8')
    inv = {'schema_version': '1', 'inventario_id': 'inv-' + _sha(identidade)[:24], 'revisao': 1, 'anterior_sha256': None,
           'origem': {'document_id': document_id, 'arquivo_sha256': arquivo_sha256,
                      'extracao_sha256': _sha(extracao_bytes), 'total_paginas': doc['page_count'],
                      'extrator': {'nome': versoes.get('nome', 'extract'), 'versao': versoes.get('extractor', 'desconhecido')},
                      'configuracao_sha256': config},
           'metodo': {'nome': 'titulos_conservadores', 'versao': '0.1.0'},
           'paginas': [], 'fragmentos': [], 'pecas': [], 'secoes': [], 'eventos': [], 'pendencias': []}

    def pend(codigo, refs):
        inv['pendencias'].append({'id': f"pend-{len(inv['pendencias']) + 1}", 'codigo': codigo,
            'referencias': refs, 'mensagem': 'Proposta exige revisão específica desta condição.', 'material': True})

    leituras = {}
    for n in range(1, doc['page_count'] + 1):
        leitura = leitura_fonte(doc, n)
        leituras[n] = leitura
        inv['paginas'].append({'numero': n, 'leitura': leitura, 'origem': 'extracao'})
        if leitura != 'texto_nativo':
            codigo = {'ocr_parcial': 'leitura_insuficiente', 'sem_texto': 'pagina_sem_texto', 'nao_processada': 'pagina_nao_processada'}[leitura]
            pend(codigo, [f'pagina-{n}'])
    atual = None
    for b in doc['blocks']:
        if not b['text']:
            continue
        ts = sorted((t for (bid, _), t in cortes.items() if bid == b['id']), key=lambda t: t['offset'])
        por_offset = {t['offset']: t for t in ts}
        offsets = sorted({0, len(b['text'])} | set(por_offset))
        for inicio, fim in zip(offsets, offsets[1:]):
            t = por_offset.get(inicio)
            pagina = {'inicio': b['page'], 'fim': b.get('page_end', b['page']),
                      'precisao': 'pagina' if b['page'] == b.get('page_end', b['page']) else 'intervalo', 'origem': 'extracao'}
            anterior = next((c for c in reversed(ts) if c['offset'] <= inicio and 'pagina_inicio' in c), None)
            seguinte = next((c for c in ts if c['offset'] == fim and 'pagina_anterior' in c), None)
            if anterior: pagina['inicio'] = anterior['pagina_inicio']
            if seguinte: pagina['fim'] = seguinte['pagina_anterior']
            if anterior or seguinte:
                pagina.update(origem='conferencia_visual', precisao='pagina' if pagina['inicio'] == pagina['fim'] else 'intervalo')
            auxiliar = b.get('section') == 'rodape' or bool(re.match(r'(?i)^\s*(?:capa|índice|indice)\b', b['text']))
            insuficiente = any(leituras[n] != 'texto_nativo' for n in range(pagina['inicio'], pagina['fim'] + 1))
            if not auxiliar and not insuficiente:
                if t or atual is None:
                    # Cabeçalho inicial na mesma página pode integrar a primeira peça titulada.
                    if t and not t.get('_manual') and atual and atual['tipo_proposto'] == 'nao_identificada' and len(inv['pecas']) == 1 and b['page'] == inv['fragmentos'][0]['paginas']['inicio']:
                        atual['tipo_proposto'] = t['tipo']
                    else:
                        atual = {'id': f"p{len(inv['pecas']) + 1:03}", 'ordem': len(inv['pecas']) + 1,
                                 'tipo_proposto': t['tipo'] if t else 'nao_identificada', 'inicio': '', 'fim': '',
                                 'proposta_evento_id': 'ev-1', 'limites': {'estado': 'proposto', 'evento_id': None},
                                 'tipo': {'estado': 'proposto', 'evento_id': None}, 'evidencias': []}
                        inv['pecas'].append(atual)
                destino = {'classe': 'peca', 'piece_id': atual['id']}
            else:
                destino = {'classe': 'auxiliar' if auxiliar else 'nao_atribuido', 'motivo': 'Região auxiliar ou leitura insuficiente.'}
            f = {'id': f"f{len(inv['fragmentos']) + 1:04}", 'block_id': b['id'], 'inicio': inicio, 'fim': fim, 'paginas': pagina, 'destino': destino}
            inv['fragmentos'].append(f)
            if destino['classe'] == 'peca':
                atual['inicio'] = atual['inicio'] or f['id']
                atual['fim'] = f['id']
                if t or not atual['evidencias']:
                    atual['evidencias'].append({'sinal': ('outro' if t.get('_manual') else 'titulo') if t else 'continuidade', 'fragmentos': [f['id']],
                                              'observacao': 'Sinal de proposta; requer revisão e não confirma autoria ou natureza.'})
            elif destino['classe'] == 'nao_atribuido':
                pend('fragmento_nao_atribuido', [f['id']])
    for p in inv['pecas']:
        pend('limite_incerto', [p['id']])
        if p['tipo_proposto'] == 'nao_identificada': pend('tipo_nao_identificado', [p['id']])
    if config is None: pend('configuracao_nao_registrada', [inv['inventario_id']])
    inv['eventos'] = [{'id': 'ev-1', 'instante': datetime.now(timezone.utc).isoformat(),
                      'ator': {'tipo': 'sistema', 'identificador': 'proposta-conservadora-local'}, 'acao': 'propor',
                      'alvos': [p['id'] for p in inv['pecas']] or [inv['inventario_id']],
                      'motivo': 'Heurística opcional e cortes manuais como propostas, sem conferência humana automática.'}]
    resultado = validar_inventario(inv, extracao_bytes, arquivo_sha256=arquivo_sha256)
    if not resultado['valido']:
        raise ValueError('Proposta incompatível com a integridade do contrato; verificar fonte e cortes.')
    return inv
