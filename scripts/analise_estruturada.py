"""Contrato analise-1: valida snapshots e renderiza; não analisa nem aprova mérito.

As entradas são bytes por artifact_id. Nenhum caminho dos insumos é aberto.
O renderizador isolado verifica somente a estrutura e não certifica fontes.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate
from pecas import _json, validar_inventario
from pecas_uso import ContextoPecas

_SCHEMA = json.loads((Path(__file__).resolve().parent.parent /
                      'docs/contratos/analise-v1.schema.json').read_text(encoding='utf-8'))
_VALIDATOR = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())
_EXEC = Draft202012Validator({'$defs': _SCHEMA['$defs'], '$ref': '#/$defs/execution'},
                            format_checker=FormatChecker())
_ID = re.compile(r'[A-Za-z0-9_-]+\Z')
_BLOCKING = {'reprocessar', 'bloqueada'}


def _segredos_declarados(obj):
    pendentes = [obj]
    chaves = {'api_key', 'apikey', 'password', 'secret', 'access_token', 'authorization', 'cookie', 'credentials'}
    while pendentes:
        value = pendentes.pop()
        if isinstance(value, dict):
            if any(k.casefold().replace('-', '_') in chaves for k in value):
                return True
            pendentes.extend(value.values())
        elif isinstance(value, list):
            pendentes.extend(value)
    return False


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _caminho_seguro(path):
    return (isinstance(path, str) and bool(path) and '\\' not in path and ':' not in path
            and not any(ord(c) < 32 for c in path) and not PureWindowsPath(path).drive
            and not PurePosixPath(path).is_absolute()
            and all(p not in ('', '.', '..') for p in path.split('/')))


def _assertions(obj):
    yield from obj['overview'].values()
    for q in obj['issues']:
        yield from q['positions']
        yield from q['grounds']
        yield q['preliminary_conclusion']
        yield from q['alternatives']
    for p in obj['requests']:
        for k in ('description', 'answer', 'effect'):
            yield p[k]


def _indexar_extracoes(parsed, metas, erro):
    idx, origins = {}, {}
    for aid, meta in metas.items():
        if meta['type'] != 'extracao' or aid not in parsed:
            continue
        value = parsed[aid]
        docs = value.get('documents', [value] if 'blocks' in value else [])
        if not isinstance(docs, list) or not docs:
            erro('entrada_invalida', aid, 'Extração sem documentos identificados.')
            continue
        for d in docs:
            if (not isinstance(d, dict) or not isinstance(d.get('document_id'), str)
                    or not _ID.fullmatch(d['document_id']) or not isinstance(d.get('blocks'), list)
                    or d.get('status') not in ('ok', 'partial', 'no_text')):
                erro('entrada_invalida', aid, 'Estrutura da extração incompatível.')
                continue
            did = d['document_id']
            if did in idx:
                erro('origem_ambigua', aid, 'Documento repetido no conjunto de extrações.')
                continue
            warnings = d.get('warnings', [])
            if (not isinstance(warnings, list) or any(not isinstance(w, dict)
                    or not isinstance(w.get('codigo'), str) for w in warnings)):
                erro('entrada_invalida', aid, 'Avisos da extração incompatíveis.')
                continue
            bids = set()
            valid = True
            for b in d['blocks']:
                if (not isinstance(b, dict) or not isinstance(b.get('id'), str)
                        or not _ID.fullmatch(b['id']) or b['id'] in bids
                        or not isinstance(b.get('text'), str)
                        or not isinstance(b.get('locator'), str)
                        or not isinstance(b.get('section'), (str, type(None)))
                        or (b.get('page') is not None and (type(b['page']) is not int or b['page'] < 1))
                        or (b.get('page_end') is not None and (type(b['page_end']) is not int
                            or b.get('page') is None or b['page_end'] < b['page']))
                        or not isinstance(b.get('tags', []), list)
                        or not all(isinstance(t, str) for t in b.get('tags', []))
                        or not isinstance(b.get('is_quote', False), bool)):
                    valid = False
                    break
                bids.add(b['id'])
            if not valid:
                erro('entrada_invalida', aid, 'Blocos incompatíveis ou repetidos.')
                continue
            if d['status'] == 'ok' and not any(b['text'].strip() for b in d['blocks']):
                erro('entrada_invalida', aid, 'Extração declarada legível não contém texto.')
                continue
            idx[did], origins[did] = d, aid
    return idx, origins


def _contexto_pecas(parsed, metas, entradas, idx, erro):
    invs = [a for a in metas if metas[a]['type'] == 'pecas' and a in parsed]
    if not invs:
        return None
    ctx = ContextoPecas()
    ctx.ativo = True
    ctx.indice = idx
    por_hash = {m['sha256']: a for a, m in metas.items()}
    for aid in invs:
        inv = parsed[aid]
        try:
            o = inv['origem']
            exid, orid = por_hash[o['extracao_sha256']], por_hash[o['arquivo_sha256']]
            if metas[exid]['type'] != 'extracao' or metas[orid]['type'] != 'original':
                raise ValueError('tipos incompatíveis')
            prev = por_hash.get(inv.get('anterior_sha256'))
            if prev and metas[prev]['type'] != 'pecas_anterior':
                raise ValueError('histórico incompatível')
            r = validar_inventario(inv, entradas[exid], arquivo_sha256=_sha(entradas[orid]),
                                   anterior_bytes=entradas[prev] if prev else None)
            if r['erros']:
                erro('inventario_invalido', aid, 'Inventário não passou suas invariantes legadas.')
                continue
            did = o['document_id']
            if did not in idx or did in ctx.documentos:
                raise ValueError('origem ambígua')
            ctx.documentos[did] = {'inv': inv, 'sha256': _sha(entradas[aid]), 'doc': idx[did]}
        except (KeyError, ValueError, TypeError, AttributeError, RecursionError):
            erro('inventario_invalido', aid, 'Fornecer snapshots exatos e original do inventário.')
    return ctx


def validar_analise(obj: dict, entradas: dict[str, bytes]) -> dict:
    """Valida forma, ligações e coerência; não infere apoio jurídico ou lê caminhos."""
    erros, avisos = [], []
    resolved = {}
    restricoes = set()

    def erro(code, path, msg):
        item = {'codigo': code, 'caminho': path, 'mensagem': msg}
        if item not in erros:
            erros.append(item)

    def aviso(code, path, msg):
        item = {'codigo': code, 'caminho': path, 'mensagem': msg}
        if item not in avisos:
            avisos.append(item)

    def resultado():
        return {'valido': not erros, 'erros': erros, 'avisos': avisos,
                'referencias_resolvidas': sorted(resolved),
                'resultado_tecnico': {'integrity': 'invalida' if erros else obj['technical_result']['integrity'],
                    'review_readiness': 'reprocessar' if erros else (
                        obj['technical_result']['review_readiness']
                        if obj['technical_result']['review_readiness'] in _BLOCKING else
                        'com_restricoes' if restricoes else obj['technical_result']['review_readiness']),
                    'restrictions': sorted(restricoes)}}

    try:
        structural = next(_VALIDATOR.iter_errors(obj), None)
    except (TypeError, ValueError, RecursionError):
        structural = True
    if structural:
        erro('estrutura_invalida', '$', 'Análise incompatível com o schema analise-1.')
        return resultado()
    if not isinstance(entradas, dict):
        erro('entrada_invalida', '/inputs', 'Fornecer bytes por artifact_id.')
        return resultado()
    restricoes.update(obj['technical_result']['restrictions'])

    metas, parsed, paths = {}, {}, set()
    for i, meta in enumerate(obj['inputs']):
        aid, path = meta['artifact_id'], meta['path']
        if aid in metas:
            erro('id_duplicado', '/inputs', 'Identidade de insumo repetida.')
        metas[aid] = meta
        if not _caminho_seguro(path):
            erro('caminho_inseguro', f'/inputs/{i}/path', 'Caminho relativo incompatível com a raiz autorizada.')
        if path.casefold() in paths:
            erro('origem_ambigua', '/inputs', 'Caminho de insumo repetido.')
        paths.add(path.casefold())
        bruto = entradas.get(aid)
        if not isinstance(bruto, bytes):
            erro('entrada_invalida', f'/inputs/{i}', 'Snapshot ausente ou não fornecido em bytes.')
            continue
        if _sha(bruto) != meta['sha256']:
            erro('snapshot_divergente', f'/inputs/{i}/sha256', 'Bytes diferentes do snapshot declarado.')
            continue
        if meta['type'] != 'original':
            try:
                parsed[aid] = _json(bruto)
                if not isinstance(parsed[aid], dict):
                    raise ValueError('objeto necessário')
            except (ValueError, UnicodeError, TypeError, RecursionError):
                erro('entrada_invalida', f'/inputs/{i}', 'Snapshot JSON UTF-8 estrito incompatível.')
    if set(entradas) != set(metas):
        erro('entrada_invalida', '/inputs', 'Manifesto e snapshots devem identificar o mesmo conjunto.')
    if erros:
        return resultado()

    idx, origins = _indexar_extracoes(parsed, metas, erro)
    matter_ids = [aid for aid, m in metas.items() if m['type'] == 'matter']
    if len(matter_ids) != 1:
        erro('triagem_incompativel', '/inputs', 'Fornecer uma triagem do caso.')
    else:
        matter = parsed[matter_ids[0]]
        try:
            r = validate.validar_matter(matter)
        except (KeyError, TypeError, ValueError, AttributeError, RecursionError):
            erro('triagem_incompativel', '/matter_id', 'Triagem incompatível com o contrato legado.')
            return resultado()
        if (r.erros or matter.get('matter', {}).get('matter_id') != obj['matter_id']
                or matter.get('matter', {}).get('as_of') != obj['as_of']
                or matter.get('matter', {}).get('objective') != obj['objective']):
            erro('triagem_incompativel', '/matter_id', 'Identidade/data ou contrato da triagem incompatíveis.')
    ex = obj['execution_ref']
    em = metas.get(ex['input_id'])
    if (not _caminho_seguro(ex['path']) or not em or em['type'] != 'execucao'
            or ex['path'] != em['path'] or ex['sha256'] != em['sha256']
            or not _EXEC.is_valid(parsed.get(ex['input_id']))
            or parsed[ex['input_id']]['run_id'] != obj['run_id']
            or _segredos_declarados(parsed[ex['input_id']])):
        erro('execucao_incompativel', '/execution_ref', 'Manifesto de execução incompatível com a análise.')
    previous = [a for a, m in metas.items() if m['type'] == 'analise_anterior']
    if obj['revision'] == 1:
        if obj['previous_sha256'] is not None or previous:
            erro('historico_incompativel', '/revision', 'Primeira revisão não tem análise anterior.')
    elif (len(previous) != 1 or metas[previous[0]]['sha256'] != obj['previous_sha256']
            or not _VALIDATOR.is_valid(parsed[previous[0]])
            or parsed[previous[0]]['analysis_id'] != obj['analysis_id']
            or parsed[previous[0]]['matter_id'] != obj['matter_id']
            or parsed[previous[0]]['revision'] + 1 != obj['revision']):
        erro('historico_incompativel', '/revision', 'Análise anterior, identidade ou sequência incompatível.')
    scope = set(obj['scope']['document_ids'])
    excluded = [e['document_id'] for e in obj['scope']['exclusions']]
    if (not scope <= set(idx) or len(excluded) != len(set(excluded))
            or set(excluded) & scope or scope | set(excluded) != set(idx)):
        erro('escopo_incompativel', '/scope', 'Documentos da extração precisam de inclusão/exclusão explícita.')
    if any(idx[d].get('status') != 'ok' for d in scope if d in idx):
        restricoes.add('Extração parcial ou sem texto no escopo.')
    if erros:
        return resultado()

    ctx = _contexto_pecas(parsed, metas, entradas, idx, erro)
    for aid, m in metas.items():
        if m['type'] not in ('facts', 'claims'):
            continue
        if parsed[aid].get('matter_id', obj['matter_id']) != obj['matter_id']:
            erro('triagem_incompativel', aid, 'Identidade declarada do derivado diverge do caso analisado.')
        try:
            function = validate.validar_facts if m['type'] == 'facts' else validate.validar_claims
            r = function(parsed[aid], idx, pecas=ctx, modo='analise')
            if r.erros:
                erro('legado_invalido', aid, 'Insumo recusado pelo contrato legado: ' + ', '.join(sorted({e['codigo'] for e in r.erros})))
            for w in r.avisos:
                aviso('legado_' + w['codigo'], aid, 'Ressalva do contrato legado; não é aprovação jurídica.')
                if w['codigo'].startswith('pecas_'):
                    restricoes.add('Inventário com conferências/pendências legadas não resolvidas.')
        except (KeyError, TypeError, ValueError, AttributeError, RecursionError):
            erro('legado_invalido', aid, 'Insumo incompatível com o validador legado.')
    if erros:
        return resultado()
    for ref in obj['references']:
        aid = ref['input_id']
        if aid not in metas or metas[aid]['type'] != ref['collection']:
            erro('referencia_inexistente', '/references', 'Artefato/coleção incompatível com a referência.')
            continue
        records = parsed[aid].get(ref['collection'], [])
        match = [x for x in records if isinstance(x, dict) and x.get('id') == ref['item_id']]
        if len(match) != 1:
            erro('referencia_inexistente', '/references', 'Item ausente ou ambíguo no snapshot.')
        elif ref['id'] in resolved:
            erro('id_duplicado', '/references', 'Referência repetida.')
        else:
            resolved[ref['id']] = (ref, match[0])

    def ligar(ids, universe, path):
        if any(x not in universe for x in ids):
            erro('referencia_inexistente', path, 'Ligação não encontrada no conjunto esperado.')

    actors = {a['id']: a for a in obj['actors']}
    issues = {q['id']: q for q in obj['issues']}
    requests = {p['id']: p for p in obj['requests']}
    research = {p['id']: p for p in obj['research_tasks']}
    decisions = {p['id']: p for p in obj['professional_decisions']}
    findings = {p['id']: p for p in obj['findings']}
    assertions = list(_assertions(obj))
    analytical_ids = set(issues) | set(requests) | {a['id'] for a in assertions}
    ids = [obj['analysis_id']] + [x['id'] for xs in (obj['actors'], obj['references'], obj['issues'],
          obj['requests'], obj['research_tasks'], obj['professional_decisions'], obj['findings'], assertions) for x in xs]
    if len(ids) != len(set(ids)):
        erro('id_duplicado', '$', 'Objetos novos precisam de identidades únicas.')
    known = set(ids) | set(idx)
    for a in actors.values():
        if 'matter_input_id' in a:
            if a['matter_input_id'] not in matter_ids:
                erro('referencia_inexistente', '/actors', 'Interlocutor não aponta a triagem fornecida.')
        else:
            ligar([a['reference_id']], resolved, '/actors')

    def fontes(refid, stack=()):
        if refid not in resolved:
            return []
        ref, record = resolved[refid]
        if ref['collection'] == 'claims':
            return [s for s in record.get('sources', []) if s.get('access') == 'lida']
        if record.get('kind') == 'inferencia':
            key = (ref['input_id'], record['id'])
            if key in stack:
                erro('referencia_circular', '/references', 'Ciclo nas premissas dos fatos.')
                return []
            r = []
            for fid in record.get('basis', []):
                # Premissas precisam ser referências explícitas desta análise.
                rid = next((k for k, (rr, _) in resolved.items() if rr['input_id'] == ref['input_id'] and rr['item_id'] == fid), None)
                if rid is None:
                    erro('referencia_inexistente', '/references', 'Premissa de inferência não foi vinculada à análise.')
                else:
                    r.extend(fontes(rid, stack + (key,)))
            return r
        return ([record['source']] if isinstance(record.get('source'), dict) else []) + (record.get('other_sources') or [])

    sources = {rid: fontes(rid) for rid in resolved}
    for rid, items in sources.items():
        if any(s.get('document_id') in excluded for s in items):
            erro('referencia_fora_do_escopo', '/references/' + rid, 'Documento excluído não pode sustentar a análise.')

    limited_cache = {}

    def limitado(rid, stack=()):
        if rid in limited_cache:
            return limited_cache[rid]
        if rid not in resolved or rid in stack:
            return True
        ref, record = resolved[rid]
        if ref['collection'] == 'facts' and record.get('kind') == 'inferencia':
            bases = [next((key for key, (rr, _) in resolved.items() if rr['input_id'] == ref['input_id']
                           and rr['item_id'] == fid), None) for fid in record.get('basis', [])]
            value = not bases or any(b is None or limitado(b, stack + (rid,)) for b in bases)
        else:
            state = record.get('status') if ref['collection'] == 'claims' else record.get('kind')
            value = state in ('partial', 'unverified', 'unsupported', 'lacuna', 'informado')
        limited_cache[rid] = value
        return value

    def blocos(refid):
        found = []
        for s in sources.get(refid, []):
            doc = idx.get(s.get('document_id'))
            if doc:
                pin = s.get('pinpoint', s)
                found.extend(validate._blocos_do_trecho(doc, s.get('block_id'), pin.get('excerpt', '')) or [])
        return found

    for a in assertions:
        ligar(a['basis_refs'], resolved, '/assertions/' + a['id'])
        if a['speaker']['entity_ref'] is not None:
            ligar([a['speaker']['entity_ref']], actors, '/assertions/' + a['id'] + '/speaker')
        if a['qualification'] != 'sustentada_no_escopo':
            restricoes.update(a['limitations'])
        if a['nature'] == 'limite':
            restricoes.add('Documento/elemento ausente: ' + a['missing_input'])
        for rid in a['basis_refs']:
            if rid not in resolved:
                continue
            ref, record = resolved[rid]
            if a['qualification'] == 'sustentada_no_escopo' and limitado(rid):
                erro('qualificacao_incompativel', '/assertions/' + a['id'], 'Afirmação não pode promover o estado da base.')
            if any('atribuicao_ambigua' in b.get('tags', []) for b in blocos(rid)):
                restricoes.add('Autoria ambígua em referência utilizada.')
            if (a['speaker']['mode'] == 'fala_propria' and blocos(rid)
                    and all(b.get('is_quote') for b in blocos(rid))):
                erro('atribuicao_incompativel', '/assertions/' + a['id'], 'Transcrição não pode ser declarada fala própria.')
    for q in obj['issues']:
        if q['status'] != 'analisada':
            restricoes.add('Questão sem conclusão no escopo: ' + q['id'])
        for field, universe in [('related_requests', requests), ('research_ids', research), ('decision_ids', decisions)]:
            ligar(q[field], universe, '/issues/' + q['id'] + '/' + field)
            for ident in q[field]:
                linked = universe.get(ident)
                if linked is not None and ((field == 'related_requests' and q['id'] not in linked['issue_ids'])
                        or (field != 'related_requests' and linked['issue_id'] != q['id'])):
                    erro('relacao_incompativel', '/issues/' + q['id'], 'Ligação não é recíproca.')
        for e in q['evidence']:
            rid = e['reference_id']
            ligar([rid], resolved, '/issues/' + q['id'] + '/evidence')
            if rid in resolved and e['origin'] == 'primaria':
                ref, record = resolved[rid]
                if (record.get('kind') in ('alegacao', 'inferencia', 'lacuna', 'informado')
                        or not fontes(rid)
                        or (ref['collection'] == 'claims' and not any(s.get('origin') == 'oficial' for s in fontes(rid)))
                        or any(b.get('is_quote') for b in blocos(rid))
                        or (ref['collection'] == 'claims' and record.get('cited_text'))):
                    erro('prova_primaria_incompativel', '/issues/' + q['id'], 'Relato/alegação não comprova exame de prova primária.')
    for p in obj['requests']:
        ligar([p['requester']], actors, '/requests')
        ligar(p['issue_ids'], issues, '/requests')
        if any(qid in issues and p['id'] not in issues[qid]['related_requests'] for qid in p['issue_ids']):
            erro('relacao_incompativel', '/requests', 'Pedido não está ligado reciprocamente à questão.')
        if p['result'] in ('nao_examinado', 'nao_localizado'):
            restricoes.add('Pedido sem resposta localizada: ' + p['id'])
    for r in obj['research_tasks']:
        ligar([r['issue_id']], issues, '/research_tasks')
        ligar(r['examined_refs'] + r['claim_refs'], resolved, '/research_tasks')
        ligar(r['counter_findings'], findings, '/research_tasks')
        if any(rid in resolved and not fontes(rid) for rid in r['examined_refs']):
            erro('leitura_incompativel', '/research_tasks', 'Referência sem fonte lida não pode constar como examinada.')
        if r['issue_id'] in issues and r['id'] not in issues[r['issue_id']]['research_ids']:
            erro('relacao_incompativel', '/research_tasks', 'Pesquisa não está ligada reciprocamente à questão.')
        if any(rid in resolved and resolved[rid][0]['collection'] != 'claims' for rid in r['claim_refs']):
            erro('referencia_inexistente', '/research_tasks', 'claim_refs deve apontar proposições.')
    for d in obj['professional_decisions']:
        ligar([d['issue_id']], issues, '/professional_decisions')
        ligar(d['basis_refs'], resolved, '/professional_decisions')
        if d['issue_id'] in issues and d['id'] not in issues[d['issue_id']]['decision_ids']:
            erro('relacao_incompativel', '/professional_decisions', 'Decisão não está ligada reciprocamente à questão.')
    for f in obj['findings']:
        ligar(f['targets'], known, '/findings')
        ligar(f['evidence_refs'], resolved, '/findings')
        if f['category'] == 'integridade' and f['impact'] != 'informativo' and f['action'] != 'reprocessar':
            erro('restricao_omitida', '/findings', 'Falha de integridade exige correção técnica, não decisão jurídica.')
        if f['impact'] != 'informativo':
            restricoes.add(f['reason'])
            if f['action'] == 'registrar':
                erro('restricao_omitida', '/findings', 'Achado material/crítico exige tratamento além de registro.')

    coverage = {}
    for c in obj['coverage']:
        did, bid = c['document_id'], c['block_id']
        blocks = {b['id']: b for b in idx.get(did, {}).get('blocks', [])}
        if did not in scope or origins.get(did) != c['input_id'] or bid not in blocks:
            erro('cobertura_invalida', '/coverage', 'Cobertura aponta origem fora do escopo ou inexistente.')
            continue
        if any(a not in analytical_ids for a in c['analysis_ids']):
            erro('cobertura_invalida', '/coverage', 'Cobertura deve apontar questão, pedido ou afirmação analítica.')
        if c['treatment'] == 'utilizado' and not c['analysis_ids']:
            erro('cobertura_invalida', '/coverage', 'Bloco utilizado precisa de ligação analítica.')
        b = blocks[bid]
        start, end = c.get('start', 0), c.get('end', len(b['text']))
        if not 0 <= start <= end <= len(b['text']) or (start == end and b['text']):
            erro('cobertura_invalida', '/coverage', 'Offsets fora do bloco.')
        coverage.setdefault((did, bid), []).append((start, end))
        if c['treatment'] in ('ilegivel', 'nao_examinado'):
            restricoes.add('Leitura/cobertura insuficiente: ' + did + '/' + bid)
        if 'inventario_id' in c:
            data = ctx.documentos.get(did) if ctx else None
            inv = data['inv'] if data else None
            if not inv or inv['inventario_id'] != c['inventario_id']:
                erro('cobertura_invalida', '/coverage', 'Inventário da cobertura incompatível.')
            elif 'piece_id' in c:
                fs = [f for f in inv['fragmentos'] if f['block_id'] == bid
                      and f['destino'] == {'classe': 'peca', 'piece_id': c['piece_id']}]
                if not any(f['inicio'] <= start <= end <= f['fim'] for f in fs):
                    erro('cobertura_invalida', '/coverage', 'Intervalo não pertence à peça declarada.')
                if 'secao_id' in c and not any(s['id'] == c['secao_id'] and s['piece_id'] == c['piece_id']
                        and any(f['id'] in s['fragmentos'] for f in fs) for s in inv['secoes']):
                    erro('cobertura_invalida', '/coverage', 'Seção incompatível com a peça/cobertura.')
    for did in scope:
        for b in idx[did]['blocks']:
            cursor = 0
            intervals = coverage.get((did, b['id']), [])
            for start, end in sorted(intervals):
                if start != cursor:
                    erro('cobertura_incompleta', '/coverage', 'Partição contém lacuna ou sobreposição.')
                cursor = end
            if not intervals or cursor != len(b['text']):
                erro('cobertura_incompleta', '/coverage', 'Cobertura não conserva todos os blocos do escopo.')
    t = obj['technical_result']
    ligar(t['blocking_findings'], findings, '/technical_result')
    blockers = {f['id'] for f in obj['findings'] if f['action'] == 'reprocessar'}
    if not blockers <= set(t['blocking_findings']):
        erro('restricao_omitida', '/technical_result', 'Achado impeditivo precisa permanecer visível.')
    if blockers and t['review_readiness'] not in _BLOCKING:
        erro('restricao_omitida', '/technical_result', 'Reprocessamento não permite aptidão para revisão.')
    if t['blocking_findings'] and t['review_readiness'] not in _BLOCKING:
        erro('restricao_omitida', '/technical_result', 'Achado declarado impeditivo exige bloqueio/reprocessamento.')
    if restricoes and (t['review_readiness'] == 'apta' or not t['restrictions']):
        erro('restricao_omitida', '/technical_result', 'Restrições conhecidas não permitem aptidão irrestrita.')
    if t['integrity'] != 'valida' and t['review_readiness'] not in _BLOCKING:
        erro('restricao_omitida', '/technical_result', 'Integridade declarada inválida exige bloqueio/reprocessamento.')
    aviso('limite_semantico', '$', 'Validade técnica não certifica completude, apoio jurídico ou aprovação profissional.')
    return resultado()


def _md(value):
    """Texto literal: não transformar documento em HTML, link ativo ou instrução."""
    value = html.escape(str(value), quote=False)
    value = value.replace('\r', ' ').replace('\n', ' ')
    return re.sub(r'([\\`*_{}\[\]()#!|>])', r'\\\1', value)


def renderizar_analise(obj: dict) -> str:
    """Renderiza estrutura válida; sem entradas, não verifica snapshots externos."""
    if not _VALIDATOR.is_valid(obj):
        raise ValueError('Análise incompatível com o schema analise-1.')
    esc = _md
    t = obj['technical_result']
    status = {'apta':'APTA À REVISÃO', 'com_restricoes':'COM RESTRIÇÕES',
              'reprocessar':'REPROCESSAR', 'bloqueada':'BLOQUEADA'}[t['review_readiness']]
    lines = ['# Análise estruturada — ' + esc(obj['analysis_id']), '',
             '**Estado declarado: ' + status + '** — não libera uso externo.', '',
             'Fontes externas não verificadas pelo renderizador. Aprovação profissional é separada.', '',
             'Revisão: ' + str(obj['revision']) + ' · Execução: ' + esc(obj['run_id']) +
             ' · Referência temporal: ' + esc(obj['as_of']), '']

    def texto(label, value):
        lines.append('**' + label + ':** ' + esc(value))
        lines.append('')

    def lista(label, values):
        texto(label, '; '.join(map(str, values)) if values else 'Lista vazia no artefato.')

    def assertion(a):
        texto(a['id'] + ' · ' + a['qualification'], a['text'])
        texto('Natureza / atribuição', a['nature'] + ' / ' + a['speaker']['mode'] +
              ' / ' + str(a['speaker']['entity_ref']))
        if a['speaker']['reason']:
            texto('Limite de autoria', a['speaker']['reason'])
        lista('Referências', a['basis_refs'])
        if 'justification' in a:
            texto('Justificativa', a['justification'])
        if 'missing_input' in a:
            texto('Elemento ausente', a['missing_input'])
        if a['limitations']:
            lista('Limitações', a['limitations'])

    lines += ['## 1. Síntese e alcance', '']
    texto('Objetivo', obj['objective'])
    texto('Escopo', obj['scope']['type'])
    lista('Documentos incluídos', obj['scope']['document_ids'])
    for x in obj['scope']['exclusions']:
        texto('Excluído: ' + x['document_id'], x['reason'])
    lista('Limites do escopo', obj['scope']['limitations'])
    lista('Restrições declaradas', t['restrictions'])
    lista('Achados impeditivos', t['blocking_findings'])
    for a in obj['overview'].values():
        assertion(a)
    lines += ['## 2. Questões centrais', '']
    for q in obj['issues']:
        lines += ['### ' + esc(q['id']) + ' — ' + esc(q['question']), '']
        texto('Importância', q['importance'] + ': ' + q['importance_reason'])
        texto('Estado', q['status'])
        for k in ('reason', 'next_action'):
            if q[k]: texto(k, q[k])
        for a in q['positions']: assertion(a)
        texto('Avaliação', q['assessment'])
        assertion(q['preliminary_conclusion'])
        for a in q['alternatives']: assertion(a)
        if q['alternatives_reason']: texto('Alternativas', q['alternatives_reason'])
        for k in ('related_requests', 'research_ids', 'decision_ids'): lista(k, q[k])
        for k, value in q['empty_reasons'].items(): texto('Ausência: ' + k, value)
    lines += ['## 3. Pedidos e resultado', '']
    for p in obj['requests']:
        texto(p['id'], p['result'] + ' · requerente: ' + p['requester'])
        lista('Questões', p['issue_ids'])
        for k in ('description', 'answer', 'effect'): assertion(p[k])
    lines += ['## 4. Provas e fundamentos', '']
    for q in obj['issues']:
        texto('Questão', q['id'])
        for e in q['evidence']:
            texto(e['reference_id'], e['role'] + ' · origem: ' + e['origin'])
            if e['limitation']: texto('Limite da prova', e['limitation'])
        for a in q['grounds']: assertion(a)
    lines += ['## 5. Limitações e pesquisa', '']
    for r in obj['research_tasks']:
        texto(r['id'] + ' · ' + r['status'], r['question'])
        for k in ('issue_id', 'reason', 'stop_reason'): texto(k, r[k])
        for k in ('permitted_terms', 'candidate_sources', 'examined_refs', 'claim_refs', 'counter_findings'): lista(k, r[k])
        for query in r['queries']: texto('Consulta', query['query'] + ' · ' + query['outcome'])
    for f in obj['findings']:
        if f['impact'] != 'informativo':
            texto(f['id'] + ' · ' + f['impact'] + ' · ' + f['action'], f['reason'])
            lista('Alvos', f['targets'])
            lista('Evidências', f['evidence_refs'])
            texto('Extensão/método', f['extent'] + ' · ' + f['method']['name'] + '/' + f['method']['version'])
    lines += ['## 6. Decisões profissionais', '']
    for d in obj['professional_decisions']:
        texto(d['id'], d['question'])
        for k in ('issue_id', 'reason', 'consequence'): texto(k, d[k])
        lista('Opções', d['options'])
        if d['recommendation']: texto('Recomendação preliminar', d['recommendation'])
        lista('Referências', d['basis_refs'])
    lines += ['## 7. Fontes e cobertura', '']
    for a in obj['actors']:
        texto(a['id'], a['label'] + ' · ' + a['role'])
    for r in obj['references']:
        texto(r['id'], r['input_id'] + '/' + r['collection'] + '/' + r['item_id'])
    for m in obj['inputs']:
        texto(m['artifact_id'], m['type'] + ' · ' + m['path'] + ' · SHA-256 ' + m['sha256'])
    for c in obj['coverage']:
        texto(c['document_id'] + '/' + c['block_id'], c['treatment'])
        if c['reason']: texto('Motivo', c['reason'])
        lista('Objetos analíticos', c['analysis_ids'])
        for k in ('start', 'end', 'inventario_id', 'piece_id', 'secao_id'):
            if k in c: texto(k, c[k])
    for f in obj['findings']:
        if f['impact'] == 'informativo':
            texto(f['id'] + ' · informativo', f['reason'])
            texto('Código/categoria/ação', f['code'] + ' · ' + f['category'] + ' · ' + f['action'])
            lista('Alvos', f['targets'])
            lista('Evidências', f['evidence_refs'])
            texto('Extensão/método', f['extent'] + ' · ' + f['method']['name'] + '/' + f['method']['version'])
    texto('Integridade declarada', t['integrity'])
    texto('Execução', obj['execution_ref']['path'] + ' · SHA-256 ' + obj['execution_ref']['sha256'])
    return '\n'.join(lines) + '\n'
