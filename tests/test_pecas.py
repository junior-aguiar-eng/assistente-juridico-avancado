"""Validação semântica em dados artificiais; sem texto de clientes."""
import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))
CASOS = RAIZ / 'tests/casos/pecas_contrato/exemplos.json'


def caso(cid='CT01'):
    c = next(c for c in json.loads(CASOS.read_text(encoding='utf-8'))['exemplos'] if c['id'] == cid)
    return copy.deepcopy(c['inventario']), c['extracao_json_utf8'].encode(), hashlib.sha256(c['origem_simulada_utf8'].encode()).hexdigest()


def validar(inv, ext, sha, anterior=None):
    assert (RAIZ / 'scripts/pecas.py').exists(), 'Falta o validador semântico de produção'
    return importlib.import_module('pecas').validar_inventario(inv, ext, arquivo_sha256=sha, anterior_bytes=anterior)


def codigos(r):
    assert r['valido'] == (not r['erros'])
    assert all(set(e) == {'codigo', 'onde', 'mensagem'} for e in r['erros'])
    return {e['codigo'] for e in r['erros']}


def extracao_alterada(inv, ext, alterar):
    obj = json.loads(ext)
    alterar(obj)
    bruto = json.dumps(obj, ensure_ascii=False).encode()
    inv['origem']['extracao_sha256'] = hashlib.sha256(bruto).hexdigest()
    return bruto


@pytest.mark.parametrize('cid', [f'CT{i:02}' for i in range(1, 8)])
def test_aceita_exemplos_de_contrato(cid):
    inv, ext, sha = caso(cid)
    r = validar(inv, ext, sha)
    assert r['valido'], r['erros']


@pytest.mark.parametrize('mudanca,codigo', [
    ('schema', 'estrutura_invalida'), ('hash_original', 'arquivo_divergente'),
    ('hash_extracao', 'extracao_divergente'), ('id_documento', 'origem_invalida'),
    ('documento_duplicado', 'origem_invalida'), ('config', 'origem_invalida'),
    ('versao_extrator', 'origem_invalida'), ('paginas_origem', 'origem_invalida'),
    ('json_invalido', 'origem_invalida'), ('blocos_invalidos', 'origem_invalida'),
    ('nan', 'origem_invalida'), ('chave_duplicada', 'origem_invalida'),
])
def test_recusa_identidade_e_estrutura(mudanca, codigo):
    inv, ext, sha = caso()
    if mudanca == 'schema': inv['schema_version'] = '2'
    elif mudanca == 'hash_original': sha = '0' * 64
    elif mudanca == 'hash_extracao': ext += b' '
    elif mudanca == 'id_documento': inv['origem']['document_id'] = 'ausente'
    elif mudanca == 'documento_duplicado': ext = extracao_alterada(inv, ext, lambda o: o['documents'].append(copy.deepcopy(o['documents'][0])))
    elif mudanca == 'config': inv['origem']['configuracao_sha256'] = '0' * 64
    elif mudanca == 'versao_extrator': inv['origem']['extrator']['versao'] = 'inexistente'
    elif mudanca == 'paginas_origem': inv['origem']['total_paginas'] += 1
    elif mudanca == 'json_invalido': ext = b'{'
    elif mudanca == 'blocos_invalidos': ext = extracao_alterada(inv, ext, lambda o: o['documents'][0].update(blocks=[None]))
    elif mudanca == 'nan': ext = b'{"documents":NaN}'
    elif mudanca == 'chave_duplicada': ext = b'{"documents":[],"documents":[]}'
    assert codigo in codigos(validar(inv, ext, sha))


def test_diagnosticos_nao_transcrevem_dados_do_inventario():
    inv, ext, sha = caso()
    inv['schema_version'] = 'SEGREDO-ARTIFICIAL'
    r = validar(inv, ext, sha)
    assert not r['valido']
    assert 'SEGREDO-ARTIFICIAL' not in json.dumps(r)


@pytest.mark.parametrize('mudanca,codigo', [
    ('id_duplicado', 'id_invalido'), ('id_reservado', 'id_invalido'),
    ('bloco_duplicado', 'id_invalido'), ('pagina_ausente', 'cobertura_invalida'),
    ('pagina_duplicada', 'cobertura_invalida'), ('bloco_ausente', 'referencia_inexistente'),
    ('destino_ausente', 'referencia_inexistente'), ('evidencia_ausente', 'referencia_inexistente'),
    ('pendencia_referencia', 'referencia_inexistente'), ('evento_alvo', 'referencia_inexistente'),
    ('offset_excede', 'intervalo_invalido'), ('offset_invertido', 'intervalo_invalido'),
    ('envelope_excede', 'intervalo_invalido'), ('precisao_falsa', 'intervalo_invalido'),
    ('perde_caractere', 'cobertura_invalida'), ('sobrepoe', 'cobertura_invalida'),
    ('limites_trocados', 'limites_incoerentes'), ('ordem_duplicada', 'limites_incoerentes'),
    ('secao_outra_peca', 'secao_fora_da_peca'), ('secao_sobreposta', 'secao_fora_da_peca'),
    ('evento_proposta', 'conferencia_invalida'), ('confirmacao_errada', 'conferencia_invalida'),
    ('tipo_desconhecido_sem_pendencia', 'pendencia_ausente'),
    ('config_ausente_sem_pendencia', 'pendencia_ausente'),
    ('localizacao_incerta_sem_pendencia', 'pendencia_ausente'),
    ('leitura_ocr_oculta', 'leitura_incoerente'), ('ocr_sem_pendencia', 'pendencia_ausente'),
    ('pagina_vazia_oculta', 'leitura_incoerente'), ('nao_atribuido_sem_pendencia', 'pendencia_ausente'),
])
def test_recusa_grafo_cobertura_conferencia_e_leitura(mudanca, codigo):
    cid = 'CT05' if mudanca in ('leitura_ocr_oculta', 'ocr_sem_pendencia', 'nao_atribuido_sem_pendencia') else 'CT01'
    inv, ext, sha = caso(cid)
    if mudanca == 'id_duplicado': inv['fragmentos'][0]['id'] = inv['inventario_id']
    elif mudanca == 'id_reservado': inv['inventario_id'] = 'pagina-99'
    elif mudanca == 'bloco_duplicado': ext = extracao_alterada(inv, ext, lambda o: o['documents'][0]['blocks'].append(copy.deepcopy(o['documents'][0]['blocks'][0])))
    elif mudanca == 'pagina_ausente': inv['paginas'].pop()
    elif mudanca == 'pagina_duplicada': inv['paginas'].append(copy.deepcopy(inv['paginas'][0]))
    elif mudanca == 'bloco_ausente': inv['fragmentos'][0]['block_id'] = 'ausente'
    elif mudanca == 'destino_ausente': inv['fragmentos'][0]['destino']['piece_id'] = 'ausente'
    elif mudanca == 'evidencia_ausente': inv['pecas'][0]['evidencias'][0]['fragmentos'] = ['ausente']
    elif mudanca == 'pendencia_referencia': inv['pendencias'].append({'id': 'pend-x', 'codigo': 'outro', 'referencias': ['ausente'], 'mensagem': 'Teste', 'material': True})
    elif mudanca == 'evento_alvo': inv['eventos'][0]['alvos'] = ['ausente']
    elif mudanca == 'offset_excede': inv['fragmentos'][0]['fim'] = 99999
    elif mudanca == 'offset_invertido': inv['fragmentos'][0]['inicio'] = inv['fragmentos'][0]['fim']
    elif mudanca == 'envelope_excede': inv['fragmentos'][0]['paginas']['fim'] = 3
    elif mudanca == 'precisao_falsa': inv['fragmentos'][0]['paginas']['fim'] = 2
    elif mudanca == 'perde_caractere': inv['fragmentos'][0]['inicio'] = 1
    elif mudanca == 'sobrepoe': inv['fragmentos'].append({**copy.deepcopy(inv['fragmentos'][0]), 'id': 'f-extra'})
    elif mudanca == 'limites_trocados': inv['pecas'][0]['fim'] = 'f002'
    elif mudanca == 'ordem_duplicada': inv['pecas'][1]['ordem'] = 1
    elif mudanca == 'secao_outra_peca': inv['secoes'][0]['fragmentos'] = ['f001']
    elif mudanca == 'secao_sobreposta': inv['secoes'].append({**copy.deepcopy(inv['secoes'][0]), 'id': 'sec-extra'})
    elif mudanca == 'evento_proposta': inv['pecas'][0]['proposta_evento_id'] = 'ausente'
    elif mudanca == 'confirmacao_errada': inv['pecas'][0]['tipo'] = {'estado': 'conferido', 'evento_id': 'ev-1'}
    elif mudanca == 'tipo_desconhecido_sem_pendencia': inv['pecas'][0]['tipo_proposto'] = 'nao_identificada'
    elif mudanca == 'config_ausente_sem_pendencia':
        ext = extracao_alterada(inv, ext, lambda o: o.pop('run'))
        inv['origem']['configuracao_sha256'] = None
    elif mudanca == 'localizacao_incerta_sem_pendencia': inv['fragmentos'][0]['paginas'].update(precisao='indeterminada', origem='indeterminada')
    elif mudanca == 'leitura_ocr_oculta': inv['paginas'][0]['leitura'] = 'texto_nativo'
    elif mudanca == 'ocr_sem_pendencia': inv['pendencias'] = [p for p in inv['pendencias'] if p['codigo'] != 'leitura_insuficiente']
    elif mudanca == 'pagina_vazia_oculta': inv['paginas'][0]['leitura'] = 'sem_texto'
    elif mudanca == 'nao_atribuido_sem_pendencia': inv['pendencias'] = [p for p in inv['pendencias'] if p['codigo'] != 'fragmento_nao_atribuido']
    assert codigo in codigos(validar(inv, ext, sha))


def test_recusa_intercalamento_de_pecas():
    inv, ext, sha = caso()
    inv['fragmentos'][2]['destino']['piece_id'] = 'p001'
    assert 'limites_incoerentes' in codigos(validar(inv, ext, sha))


def test_recusa_ordem_de_blocos_fonte_incompativel_com_paginas():
    inv, ext, sha = caso()
    ext = extracao_alterada(inv, ext, lambda o: o['documents'][0]['blocks'].reverse())
    assert 'limites_incoerentes' in codigos(validar(inv, ext, sha))


def test_pendencia_material_vira_aviso_sem_aprovar_leitura():
    inv, ext, sha = caso('CT05')
    r = validar(inv, ext, sha)
    assert r['valido']
    assert any(a['codigo'] == 'leitura_insuficiente' and a['material'] for a in r['avisos'])


def revisao():
    c = json.loads(CASOS.read_text(encoding='utf-8'))['revisoes'][0]
    inv = copy.deepcopy(c['inventario'])
    anterior = c['anterior_json_utf8'].encode()
    ext = json.loads(CASOS.read_text(encoding='utf-8'))['exemplos'][2]['extracao_json_utf8']
    # RH01 tem uma origem artificial própria, reconstruída pelo mesmo gerador.
    import runpy
    gerador = runpy.run_path(str(CASOS.parent / 'gerar_exemplos.py'))
    origem = gerador['exemplo']('RH01', [('PETIÇÃO UM.', 1, 1, 'corpo'), ('CONTINUAÇÃO.', 2, 2, 'corpo')],
                               ['p001', 'p002'], {'p001': 'peticao', 'p002': 'peticao'})
    return inv, origem['extracao_json_utf8'].encode(), hashlib.sha256(origem['origem_simulada_utf8'].encode()).hexdigest(), anterior


def test_aceita_fusao_preservando_alvo_historico_e_invalidando_conferencias():
    inv, ext, sha, anterior = revisao()
    r = validar(inv, ext, sha, anterior)
    assert r['valido'], r['erros']


@pytest.mark.parametrize('mudanca', [
    'sem_anterior', 'hash_anterior', 'contador', 'origem', 'prefixo', 'anterior_invalido',
    'confirmacao_antiga_tipo', 'confirmacao_antiga_limites', 'alvo_removido_inexistente',
    'evento_fora_de_ordem', 'sem_correcao', 'id_muda_classe',
])
def test_recusa_historico_incompativel(mudanca):
    inv, ext, sha, anterior = revisao()
    if mudanca == 'sem_anterior': anterior = None
    elif mudanca == 'hash_anterior': anterior += b' '
    elif mudanca == 'contador': inv['revisao'] = 3
    elif mudanca == 'origem': inv['inventario_id'] = 'outro-inventario'
    elif mudanca == 'prefixo': inv['eventos'][0]['motivo'] = 'Histórico reescrito'
    elif mudanca == 'anterior_invalido': anterior = b'{}'; inv['anterior_sha256'] = hashlib.sha256(anterior).hexdigest()
    elif mudanca.startswith('confirmacao_antiga_'):
        dim = mudanca.removeprefix('confirmacao_antiga_')
        inv['pecas'][0][dim] = json.loads(anterior)['pecas'][0][dim]
    elif mudanca == 'alvo_removido_inexistente': inv['eventos'][-1]['alvos'].append('nunca-existiu')
    elif mudanca == 'evento_fora_de_ordem': inv['eventos'][-1]['instante'] = '2026-10-21T23:00:00Z'
    elif mudanca == 'sem_correcao': inv['eventos'][-1]['acao'] = 'propor'
    elif mudanca == 'id_muda_classe': inv['pendencias'].append({'id': 'p002', 'codigo': 'outro', 'referencias': ['p001'], 'mensagem': 'Mudança de classe', 'material': True})
    cs = codigos(validar(inv, ext, sha, anterior))
    esperado = 'referencia_inexistente' if mudanca == 'alvo_removido_inexistente' else 'historico_incompativel'
    assert esperado in cs


def test_aceita_nova_conferencia_humana_apos_correcao():
    inv, ext, sha, anterior = revisao()
    for n, dim in enumerate(('limites', 'tipo'), 5):
        inv['eventos'].append({'id': f'ev-{n}', 'instante': f'2026-10-22T00:0{n}:00Z',
            'ator': {'tipo': 'humano', 'identificador': 'Pessoa simulada'}, 'acao': 'conferir_' + dim,
            'alvos': ['p001'], 'motivo': 'Nova conferência fictícia'})
        inv['pecas'][0][dim] = {'estado': 'conferido', 'evento_id': f'ev-{n}'}
    r = validar(inv, ext, sha, anterior)
    assert r['valido'], r['erros']


def test_conferencia_nao_pode_anteceder_a_correcao_material():
    inv, ext, sha, anterior = revisao()
    ev = {'id': 'ev-nova', 'instante': '2026-10-22T00:03:30Z',
          'ator': {'tipo': 'humano', 'identificador': 'Pessoa simulada'}, 'acao': 'conferir_tipo',
          'alvos': ['p001'], 'motivo': 'Conferência anterior à correção'}
    inv['eventos'].insert(-1, ev)
    inv['pecas'][0]['tipo'] = {'estado': 'conferido', 'evento_id': 'ev-nova'}
    assert 'historico_incompativel' in codigos(validar(inv, ext, sha, anterior))


def test_recusa_conferencia_anterior_ao_evento_da_proposta_atual():
    inv, ext, sha = caso()
    inv['eventos'].insert(0, {'id': 'ev-antes', 'instante': '2026-10-21T23:59:00Z',
        'ator': {'tipo': 'humano', 'identificador': 'Pessoa simulada'}, 'acao': 'conferir_tipo',
        'alvos': ['p001'], 'motivo': 'Conferência fictícia anterior à proposta'})
    inv['pecas'][0]['tipo'] = {'estado': 'conferido', 'evento_id': 'ev-antes'}
    assert 'conferencia_invalida' in codigos(validar(inv, ext, sha))


def test_recusa_limite_conferido_com_localizacao_indeterminada():
    inv, ext, sha = caso()
    inv['fragmentos'][0]['paginas'].update(precisao='indeterminada', origem='indeterminada')
    inv['pendencias'].append({'id': 'pend-incerta', 'codigo': 'localizacao_indeterminada',
        'referencias': ['f001'], 'mensagem': 'Posição incerta', 'material': True})
    inv['eventos'].append({'id': 'ev-humano', 'instante': '2026-10-22T00:01:00Z',
        'ator': {'tipo': 'humano', 'identificador': 'Pessoa simulada'}, 'acao': 'conferir_limites',
        'alvos': ['p001'], 'motivo': 'Conferência fictícia'})
    inv['pecas'][0]['limites'] = {'estado': 'conferido', 'evento_id': 'ev-humano'}
    assert 'conferencia_invalida' in codigos(validar(inv, ext, sha))


def test_alterar_apenas_tipo_preserva_conferencia_dos_limites_inalterados():
    _, ext, sha, anterior = revisao()
    inv = json.loads(anterior)
    inv['revisao'] = 2
    inv['anterior_sha256'] = hashlib.sha256(anterior).hexdigest()
    inv['pecas'][0]['tipo_proposto'] = 'contestacao'
    inv['pecas'][0]['tipo'] = {'estado': 'proposto', 'evento_id': None}
    inv['pecas'][0]['proposta_evento_id'] = 'ev-4'
    inv['eventos'].append({'id': 'ev-4', 'instante': '2026-10-22T00:04:00Z',
        'ator': {'tipo': 'sistema', 'identificador': 'Fixture'}, 'acao': 'corrigir',
        'alvos': ['p001'], 'motivo': 'Somente tipo alterado'})
    r = validar(inv, ext, sha, anterior)
    assert r['valido'], r['erros']


def test_configuracao_json_null_presente_tem_hash_diferente_de_configuracao_ausente():
    inv, ext, sha = caso()
    ext = extracao_alterada(inv, ext, lambda o: o['run'].update(params=None))
    inv['origem']['configuracao_sha256'] = hashlib.sha256(b'null').hexdigest()
    r = validar(inv, ext, sha)
    assert r['valido'], r['erros']


@pytest.mark.parametrize('campo', ['total', 'pagina', 'offset', 'ordem'])
def test_inteiros_matematicos_do_json_schema_nao_causam_excecao_nem_mutacao(campo):
    inv, ext, sha = caso()
    if campo == 'total': inv['origem']['total_paginas'] = 2.0
    elif campo == 'pagina': inv['paginas'][0]['numero'] = 1.0
    elif campo == 'offset': inv['fragmentos'][0]['inicio'] = 0.0
    elif campo == 'ordem': inv['pecas'][0]['ordem'] = 1.0
    antes = copy.deepcopy(inv)
    r = validar(inv, ext, sha)
    assert r['valido'], r['erros']
    assert inv == antes
    if campo == 'total': assert type(inv['origem']['total_paginas']) is float


@pytest.mark.parametrize('localizacao', [
    {'page': '1'}, {'page': 0}, {'pagina': 99}, {'page': True},
    {'page': 1, 'pagina': 2}, {'page': None, 'pagina': 1},
])
def test_aviso_com_localizacao_malformada_nao_oculta_ocr(localizacao):
    inv, ext, sha = caso()
    ext = extracao_alterada(inv, ext, lambda o: o['documents'][0].update(warnings=[{'codigo': 'ocr_aplicado', **localizacao}]))
    assert 'origem_invalida' in codigos(validar(inv, ext, sha))


@pytest.mark.parametrize('localizacao', [{}, {'pagina': None}, {'page': 1}])
def test_aviso_ocr_global_ou_local_nao_pode_virar_texto_nativo(localizacao):
    inv, ext, sha = caso()
    ext = extracao_alterada(inv, ext, lambda o: o['documents'][0].update(warnings=[{'codigo': 'ocr_aplicado', **localizacao}]))
    assert 'leitura_incoerente' in codigos(validar(inv, ext, sha))


def rodape_em_envelope(ext):
    obj = json.loads(ext)
    obj['documents'][0]['blocks'].append({'id': 'bfooter', 'text': 'RODAPÉ SIMULADO', 'page': 1,
        'page_end': 3, 'section': 'rodape', 'tags': ['repetido']})
    return json.dumps(obj, ensure_ascii=False).encode()


def test_rodape_em_envelope_nao_prova_texto_em_pagina_vazia():
    _, ext, sha = caso('CT07')
    ext = rodape_em_envelope(ext)
    import pecas_proposta
    inv = pecas_proposta.propor_inventario(ext, arquivo_sha256=sha)
    assert inv['paginas'][1]['leitura'] == 'sem_texto'
    assert validar(inv, ext, sha)['valido']
    inv['paginas'][1]['leitura'] = 'texto_nativo'
    assert 'leitura_incoerente' in codigos(validar(inv, ext, sha))


@pytest.mark.parametrize('aviso,leitura', [('pagina_ilegivel', 'nao_processada'), ('pagina_sem_texto', 'sem_texto')])
def test_blocos_vazios_e_rodape_nao_ocultam_falha_de_leitura(aviso, leitura):
    _, ext, sha = caso('CT07')
    obj = json.loads(rodape_em_envelope(ext))
    obj['documents'][0]['warnings'] = [{'codigo': aviso, 'pagina': 2}]
    obj['documents'][0]['blocks'].append({'id': 'bvazio', 'text': '', 'page': 2, 'page_end': 2})
    ext = json.dumps(obj).encode()
    import pecas_proposta
    inv = pecas_proposta.propor_inventario(ext, arquivo_sha256=sha)
    assert inv['paginas'][1]['leitura'] == leitura
    assert validar(inv, ext, sha)['valido']


def revisao_renomeia_fragmento(alvo_explicito):
    anterior, ext, sha = caso()
    bruto = json.dumps(anterior).encode()
    inv = copy.deepcopy(anterior)
    inv['revisao'] = 2
    inv['anterior_sha256'] = hashlib.sha256(bruto).hexdigest()
    inv['fragmentos'][0]['id'] = 'f-novo'
    p = inv['pecas'][0]
    p['inicio'] = p['fim'] = 'f-novo'
    p['evidencias'][0]['fragmentos'] = ['f-novo']
    p['proposta_evento_id'] = 'ev-2'
    inv['eventos'].append({'id': 'ev-2', 'instante': '2026-10-22T00:01:00Z',
        'ator': {'tipo': 'sistema', 'identificador': 'Fixture'}, 'acao': 'corrigir',
        'alvos': ['p001', 'f001'] if alvo_explicito else ['p001'], 'motivo': 'Renomeia fragmento artificial'})
    return inv, ext, sha, bruto


def test_remocao_exige_registrar_identidade_do_fragmento_no_evento():
    inv, ext, sha, anterior = revisao_renomeia_fragmento(False)
    assert 'historico_incompativel' in codigos(validar(inv, ext, sha, anterior))


def test_id_de_fragmento_removido_nao_pode_voltar_duas_revisoes_depois():
    anterior, ext, sha, original = revisao_renomeia_fragmento(True)
    assert validar(anterior, ext, sha, original)['valido']
    bruto = json.dumps(anterior).encode()
    inv = copy.deepcopy(anterior)
    inv['revisao'] = 3
    inv['anterior_sha256'] = hashlib.sha256(bruto).hexdigest()
    f = copy.deepcopy(inv['fragmentos'][0]); f.update(id='f001', fim=1)
    inv['fragmentos'][0]['inicio'] = 1
    inv['fragmentos'].insert(0, f)
    p = inv['pecas'][0]; p['inicio'] = 'f001'; p['proposta_evento_id'] = 'ev-3'
    inv['eventos'].append({'id': 'ev-3', 'instante': '2026-10-22T00:02:00Z',
        'ator': {'tipo': 'sistema', 'identificador': 'Fixture'}, 'acao': 'corrigir',
        'alvos': ['p001'], 'motivo': 'Tenta reutilizar ID removido'})
    assert 'historico_incompativel' in codigos(validar(inv, ext, sha, bruto))
