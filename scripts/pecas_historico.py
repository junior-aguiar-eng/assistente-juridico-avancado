"""Comparação da revisão corrente com o snapshot anterior imutável."""
from datetime import datetime, timedelta
import re


def _instante(texto):
    # RFC 3339 também admite segundo intercalar; normalizar somente para comparar.
    salto = bool(re.search(r':60(?:[.,]|Z|z|[+-])', texto))
    if salto:
        texto = re.sub(r':60(?=[.,Zz+-])', ':59', texto)
    return datetime.fromisoformat(texto.replace('Z', '+00:00').replace('z', '+00:00')) + timedelta(seconds=int(salto))


def _objetos(inv):
    return {x['id']: (g, x) for g in ('fragmentos', 'pecas', 'secoes', 'eventos', 'pendencias') for x in inv[g]}


def _apoios(inv, p):
    return sorted((f for f in inv['fragmentos'] if f['destino'] == {'classe': 'peca', 'piece_id': p['id']}), key=lambda f: f['id'])


def _assinatura(inv, obj, dimensao):
    fs = {f['id']: f for f in inv['fragmentos']}
    if dimensao == 'conferencia':
        return (obj['piece_id'], obj['tipo_proposto'], obj['fragmentos'], [fs.get(fid) for fid in obj['fragmentos']])
    evidencias = [(e, [fs.get(fid) for fid in e['fragmentos']]) for e in obj['evidencias']]
    base = (_apoios(inv, obj), evidencias)
    if dimensao == 'tipo':
        return (obj['tipo_proposto'], base)
    return (obj['inicio'], obj['fim'], obj['ordem'], base)


def validar_historico(inv, anterior_bytes, erro, ler_json, sha, esquema):
    def falha(mensagem):
        erro('historico_incompativel', '/historico', mensagem)

    try:
        instantes = [_instante(e['instante']) for e in inv['eventos']]
        if any(a > b for a, b in zip(instantes, instantes[1:])):
            falha('Eventos fora de ordem cronológica.')
    except (ValueError, OverflowError):
        falha('Data de evento incompatível com a cronologia.')
    if inv['revisao'] == 1:
        if anterior_bytes is not None:
            falha('Revisão inicial não recebe revisão anterior.')
        return set(), 0
    if not isinstance(anterior_bytes, bytes):
        falha('Revisão posterior exige bytes do snapshot anterior.')
        return set(), 0
    try:
        anterior = ler_json(anterior_bytes)
        if not esquema.is_valid(anterior):
            raise ValueError('snapshot incompatível')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        falha('Snapshot anterior inválido.')
        return set(), 0
    prev = _objetos(anterior)
    atuais = _objetos(inv)
    prefixo = len(anterior['eventos'])
    if (sha(anterior_bytes) != inv['anterior_sha256'] or inv['revisao'] != anterior['revisao'] + 1
            or inv['inventario_id'] != anterior['inventario_id'] or inv['origem'] != anterior['origem']
            or inv['eventos'][:prefixo] != anterior['eventos']):
        falha('Hash, contador, identidade, origem ou prefixo histórico incompatível.')
    novos = inv['eventos'][prefixo:]
    posicoes = {e['id']: i for i, e in enumerate(inv['eventos'])}
    correcoes = [e for e in novos if e['acao'] == 'corrigir']
    alvos_corrigidos = {alvo for e in correcoes for alvo in e['alvos']}
    historicos = {alvo for e in anterior['eventos'] for alvo in e['alvos']}
    for oid, (grupo, obj) in atuais.items():
        if oid in prev and prev[oid][0] != grupo:
            falha('Identidade reutilizada em outra classe de objeto.')
        elif oid not in prev and oid in historicos:
            falha('Identidade histórica removida não pode ser reutilizada.')
    # Toda alteração material exige evento corrigir; conferências são comparadas separadamente.
    for oid in prev.keys() | atuais.keys():
        antes = prev.get(oid)
        depois = atuais.get(oid)
        if (antes or depois)[0] == 'eventos':
            continue
        if antes is not None and depois is None and oid not in alvos_corrigidos:
            falha('ID removido deve constar explicitamente nos alvos de correção para permanecer no histórico.')
        def material(item):
            if item is None:
                return None
            grupo, obj = item
            return grupo, {k: v for k, v in obj.items() if k not in ('limites', 'tipo', 'conferencia', 'proposta_evento_id')}
        if material(antes) != material(depois):
            # Um fragmento alterado também pode ser documentado pela correção da peça afetada.
            ligados = {oid}
            for item in (antes, depois):
                if item and item[0] == 'fragmentos' and item[1]['destino']['classe'] == 'peca':
                    ligados.add(item[1]['destino']['piece_id'])
            if not ligados & alvos_corrigidos:
                falha('Alteração material sem evento de correção do objeto afetado.')
    for grupo, dimensoes in (('pecas', ('limites', 'tipo')), ('secoes', ('conferencia',))):
        antigos = {x['id']: x for x in anterior[grupo]}
        for obj in inv[grupo]:
            antigo = antigos.get(obj['id'])
            for dim in dimensoes:
                estado = obj[dim]
                mudou = antigo is None or _assinatura(anterior, antigo, dim) != _assinatura(inv, obj, dim)
                if mudou:
                    eventos = [e for e in correcoes if obj['id'] in e['alvos']]
                    if not eventos:
                        falha('Dimensão alterada sem correção referenciada.')
                        continue
                    ultima = max(posicoes[e['id']] for e in eventos)
                    if grupo == 'pecas' and obj['proposta_evento_id'] not in {e['id'] for e in eventos}:
                        falha('Peça alterada mantém evento de proposta anterior.')
                    if estado['estado'] != 'proposto' and posicoes.get(estado['evento_id'], -1) <= ultima:
                        falha('Conferência anterior preservada após alteração material.')
                elif antigo and estado != antigo[dim] and estado['estado'] != 'proposto' and posicoes.get(estado['evento_id'], -1) < prefixo:
                    falha('Mudança de conferência exige novo evento humano.')
    return set(prev) | {anterior['inventario_id']}, prefixo
