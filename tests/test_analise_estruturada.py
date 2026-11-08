"""Contrato aditivo: integridade técnica não é aprovação jurídica (dados sintéticos)."""
import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
CASOS = ROOT / 'tests/casos/analise_contrato/exemplos.json'


def api():
    assert (ROOT / 'scripts/analise_estruturada.py').is_file(), 'EV-01: validador/renderizador ausente'
    return importlib.import_module('analise_estruturada')


def caso(nome='POS-01'):
    data = json.loads(CASOS.read_text(encoding='utf-8'))
    item = next(c for c in data['positivos'] if c['id'] == nome)
    return copy.deepcopy(item['analise']), {k: v.encode('utf-8') for k, v in item['entradas_utf8'].items()}


def substituir(obj, entradas, aid, value):
    bruto = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    entradas[aid] = bruto
    meta = next(i for i in obj['inputs'] if i['artifact_id'] == aid)
    meta['sha256'] = hashlib.sha256(bruto).hexdigest()
    if obj['execution_ref']['input_id'] == aid:
        obj['execution_ref']['sha256'] = meta['sha256']


def codes(resultado):
    return {e['codigo'] for e in resultado['erros']}


def test_referencia_resolve_snapshot_exato():
    obj, entradas = caso()
    antes = copy.deepcopy((obj, entradas))
    r = api().validar_analise(obj, entradas)
    assert r['valido'], r['erros']
    assert r['resultado_tecnico']['integrity'] == 'valida'
    assert set(r['referencias_resolvidas']) == {'ref-ato', 'ref-relato', 'ref-norma'}
    assert (obj, entradas) == antes


def test_segundo_positivo_preserva_insuficiencia_de_prova():
    obj, entradas = caso('POS-02')
    r = api().validar_analise(obj, entradas)
    assert r['valido'], r['erros']
    assert r['resultado_tecnico']['review_readiness'] == 'com_restricoes'


def test_referencia_incompativel_reprova():
    obj, entradas = caso()
    entradas['fatos'] += b' '
    r = api().validar_analise(obj, entradas)
    assert not r['valido'] and 'snapshot_divergente' in codes(r)
    assert r['resultado_tecnico']['integrity'] == 'invalida'


@pytest.mark.parametrize('alvo,valor', [('input_id', 'ausente'), ('item_id', 'inexistente'), ('collection', 'claims')])
def test_referencia_quebrada_ou_colecao_errada(alvo, valor):
    obj, entradas = caso()
    obj['references'][0][alvo] = valor
    assert not api().validar_analise(obj, entradas)['valido']


def test_relato_nao_vira_prova_primaria():
    obj, entradas = caso()
    obj['issues'][0]['evidence'][0]['origin'] = 'primaria'
    r = api().validar_analise(obj, entradas)
    assert 'prova_primaria_incompativel' in codes(r)


def test_resultado_tecnico_nao_aprova_entrega():
    obj, entradas = caso()
    obj['technical_result']['aprovado_por_profissional'] = True
    r = api().validar_analise(obj, entradas)
    assert not r['valido'] and 'estrutura_invalida' in codes(r)


def test_markdown_preserva_limites_do_json():
    obj, _ = caso('POS-02')
    md = api().renderizar_analise(obj)
    assert 'COM RESTRIÇÕES' in md and 'não libera uso externo' in md
    assert 'Fontes externas não verificadas pelo renderizador' in md
    assert 'A perícia original não integra o pacote sintético.' in md
    for secao in ['Síntese e alcance', 'Questões centrais', 'Pedidos e resultado',
                  'Provas e fundamentos', 'Limitações e pesquisa', 'Decisões profissionais', 'Fontes e cobertura']:
        assert secao in md
    for ref in obj['references']:
        assert ref['id'] in md
    assert md.index('Síntese e alcance') < md.index('Questões centrais') < md.index('Pedidos e resultado')


def test_renderer_nao_omite_posicoes_alternativas_achados_e_ligacoes():
    obj, _ = caso('POS-02')
    md = api().renderizar_analise(obj)
    for valor in ['A alternativa mantém a restrição probatória.', 'Pesquisa depende de fonte primária.',
                  'A defesa sustenta a leitura restrita.', 'A consequência limita o uso da prova relatada.',
                  'achado-prova', 'decisao-prova', 'pesquisa-prova', 'q-efeito', 'pedido-1']:
        assert valor in md


def test_markdown_escapa_conteudo_ativo_sem_seguir_instrucoes():
    obj, entradas = caso()
    obj['overview']['context']['text'] = '<script>alert(1)</script> [abra](javascript:alert(1)) ![img](https://exemplo.invalid/x)'
    md = api().renderizar_analise(obj)
    assert '<script>' not in md and '[abra](javascript:' not in md and '![img](' not in md
    assert api().validar_analise(obj, entradas)['valido']


def test_schema_publicado_e_estrito():
    p = ROOT / 'docs/contratos/analise-v1.schema.json'
    assert p.is_file(), 'EV-01: schema ausente'
    schema = json.loads(p.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    val = Draft202012Validator(schema, format_checker=FormatChecker())
    obj, _ = caso()
    assert val.is_valid(obj)
    obj['unknown'] = True
    assert not val.is_valid(obj)


@pytest.mark.parametrize('campo,valor', [('schema_version', '1'), ('revision', True),
    ('created_at', '2026-10-22'), ('as_of', '2026-02-30'), ('analysis_id', 'id com espaço')])
def test_tipos_e_formatos_incompativeis(campo, valor):
    obj, entradas = caso()
    obj[campo] = valor
    assert not api().validar_analise(obj, entradas)['valido']


@pytest.mark.parametrize('caminho', ['../fonte.json', 'a/../../fonte.json', '/fonte.json',
    'C:/segredo.json', r'\\servidor\fonte', 'a\\..\\fonte', 'arquivo.json:stream', 'a//b.json'])
def test_nao_aceita_caminhos_fora_da_raiz(caminho):
    obj, entradas = caso()
    obj['inputs'][0]['path'] = caminho
    assert 'caminho_inseguro' in codes(api().validar_analise(obj, entradas))


def test_nao_le_arquivos_de_caminhos_declarados(tmp_path):
    obj, entradas = caso()
    alvo = tmp_path / 'nao-ler.json'
    alvo.write_text('conteudo diferente', encoding='utf-8')
    obj['inputs'][0]['path'] = 'nao-ler.json'
    assert api().validar_analise(obj, entradas)['valido']
    assert alvo.read_text(encoding='utf-8') == 'conteudo diferente'


def test_chaves_duplicadas_e_nan_reprovam_entradas():
    for bruto in [b'{"facts":[],"facts":[]}', b'{"value":NaN}']:
        obj, entradas = caso()
        entradas['fatos'] = bruto
        next(i for i in obj['inputs'] if i['artifact_id'] == 'fatos')['sha256'] = hashlib.sha256(bruto).hexdigest()
        assert 'entrada_invalida' in codes(api().validar_analise(obj, entradas))


@pytest.mark.parametrize('valor', [None, [], 'texto', {'x': []}])
def test_objeto_invalido_retorna_erro_controlado(valor):
    assert not api().validar_analise(valor, {})['valido']


def test_fonte_secundaria_nao_vira_supported():
    obj, entradas = caso()
    claims = json.loads(entradas['teses'])
    claims['claims'][0]['sources'][0]['origin'] = 'secundaria'
    substituir(obj, entradas, 'teses', claims)
    assert 'legado_invalido' in codes(api().validar_analise(obj, entradas))


def test_partial_nao_e_promovido_por_afirmacao_sustentada():
    obj, entradas = caso()
    claims = json.loads(entradas['teses'])
    c = claims['claims'][0]
    c.update(status='partial', reason='Leitura limitada.', missing='Exame autônomo pendente.')
    substituir(obj, entradas, 'teses', claims)
    assert 'qualificacao_incompativel' in codes(api().validar_analise(obj, entradas))


def test_atribuicao_ambigua_nao_e_aptidao_irrestrita():
    obj, entradas = caso()
    ext = json.loads(entradas['extracao'])
    ext['documents'][0]['blocks'][1]['tags'] = ['atribuicao_ambigua']
    substituir(obj, entradas, 'extracao', ext)
    assert 'restricao_omitida' in codes(api().validar_analise(obj, entradas))


def test_citacao_nao_e_fala_propria():
    obj, entradas = caso()
    ext = json.loads(entradas['extracao'])
    ext['documents'][0]['blocks'][1]['is_quote'] = True
    substituir(obj, entradas, 'extracao', ext)
    obj['issues'][0]['positions'][0]['speaker']['mode'] = 'fala_propria'
    assert 'atribuicao_incompativel' in codes(api().validar_analise(obj, entradas))


def test_cobertura_nao_pode_omitir_bloco():
    obj, entradas = caso()
    obj['coverage'].pop()
    assert 'cobertura_incompleta' in codes(api().validar_analise(obj, entradas))


def test_cobertura_rejeita_sobreposicao_offset_e_documento_errados():
    for mudanca in ['duplicar', 'offset', 'documento']:
        obj, entradas = caso()
        if mudanca == 'duplicar': obj['coverage'].append(copy.deepcopy(obj['coverage'][0]))
        elif mudanca == 'offset': obj['coverage'][0]['end'] = 999999
        else: obj['coverage'][0]['document_id'] = 'doc-errado'
        assert not api().validar_analise(obj, entradas)['valido']


def test_nao_examinado_nao_vira_analise_apta():
    obj, entradas = caso()
    obj['coverage'][0]['treatment'] = 'nao_examinado'
    obj['coverage'][0]['reason'] = 'Não houve leitura.'
    assert 'restricao_omitida' in codes(api().validar_analise(obj, entradas))


def test_afirmacao_material_exige_base_e_inferencia_exige_justificativa():
    obj, entradas = caso()
    obj['issues'][0]['preliminary_conclusion']['basis_refs'] = []
    assert not api().validar_analise(obj, entradas)['valido']
    obj, entradas = caso()
    obj['issues'][0]['preliminary_conclusion'].pop('justification')
    assert not api().validar_analise(obj, entradas)['valido']


def test_lacuna_nao_pode_inventar_documento_lido():
    obj, entradas = caso('POS-02')
    a = obj['issues'][0]['alternatives'][0]
    a.update(nature='relato_documental', basis_refs=['ref-inventada'])
    assert not api().validar_analise(obj, entradas)['valido']


def test_ids_novos_unicos_e_relacoes_validas():
    obj, entradas = caso()
    obj['issues'][0]['id'] = obj['requests'][0]['id']
    assert 'id_duplicado' in codes(api().validar_analise(obj, entradas))
    obj, entradas = caso()
    obj['issues'][0]['related_requests'] = ['ausente']
    assert 'referencia_inexistente' in codes(api().validar_analise(obj, entradas))


def test_revision_exige_anterior_correto_e_nao_altera_original():
    obj, entradas = caso()
    anterior = copy.deepcopy(obj)
    raw = json.dumps(anterior, ensure_ascii=False).encode('utf-8')
    obj['revision'] = 2
    obj['previous_sha256'] = hashlib.sha256(raw).hexdigest()
    obj['inputs'].append({'artifact_id':'anterior', 'type':'analise_anterior', 'path':'derived/analise.rev-0001.json', 'sha256':obj['previous_sha256']})
    entradas['anterior'] = raw
    assert api().validar_analise(obj, entradas)['valido']
    obj['previous_sha256'] = '0' * 64
    assert 'historico_incompativel' in codes(api().validar_analise(obj, entradas))
    assert entradas['anterior'] == raw


def test_document_id_duplicado_nao_sobrescreve_indice():
    obj, entradas = caso()
    ext = json.loads(entradas['extracao'])
    ext['documents'].append(copy.deepcopy(ext['documents'][0]))
    substituir(obj, entradas, 'extracao', ext)
    assert 'origem_ambigua' in codes(api().validar_analise(obj, entradas))


def test_execucao_e_triagem_precisam_corresponder_ao_caso():
    obj, entradas = caso()
    obj['matter_id'] = 'outro-caso'
    assert 'triagem_incompativel' in codes(api().validar_analise(obj, entradas))
    obj, entradas = caso()
    obj['execution_ref']['sha256'] = '0' * 64
    assert 'execucao_incompativel' in codes(api().validar_analise(obj, entradas))


def test_renderer_rejeita_estrutura_invalida():
    with pytest.raises(ValueError):
        api().renderizar_analise({'schema_version':'analise-1'})


def test_fixtures_declaram_dois_positivos_e_cinco_contraexemplos():
    data = json.loads(CASOS.read_text(encoding='utf-8'))
    assert len(data['positivos']) == 2
    assert {x['id'] for x in data['contraexemplos']} == {f'NEG-0{i}' for i in range(1, 6)}
    assert data['proveniencia']['tipo'] == 'sintetico'


def test_cobertura_precisa_apontar_objeto_analitico():
    obj, entradas = caso()
    obj['coverage'][0]['analysis_ids'] = ['ator-parte']
    assert 'cobertura_invalida' in codes(api().validar_analise(obj, entradas))


def test_vinculos_entre_questoes_pedidos_e_pesquisas_sao_reciprocos():
    obj, entradas = caso('POS-02')
    obj['issues'][0]['research_ids'] = []
    obj['issues'][0]['empty_reasons']['research_ids'] = 'Sem pesquisa ligada.'
    assert 'relacao_incompativel' in codes(api().validar_analise(obj, entradas))


def test_achado_tecnico_impeditivo_nao_vira_decisao_juridica():
    obj, entradas = caso('POS-02')
    f = obj['findings'][0]
    f.update(category='integridade', impact='critico', action='decisao_profissional')
    assert 'restricao_omitida' in codes(api().validar_analise(obj, entradas))


def test_achado_impeditivo_declarado_nao_pode_ser_apto():
    obj, entradas = caso('POS-02')
    obj['technical_result']['blocking_findings'] = ['achado-prova']
    assert 'restricao_omitida' in codes(api().validar_analise(obj, entradas))


def test_manifesto_execucao_nao_aceita_segredos():
    obj, entradas = caso()
    ex = json.loads(entradas['execucao'])
    ex['configuration'] = {'nested': {'api_key': 'segredo-ficticio-de-teste'}}
    substituir(obj, entradas, 'execucao', ex)
    r = api().validar_analise(obj, entradas)
    assert 'execucao_incompativel' in codes(r)
    assert 'segredo-ficticio-de-teste' not in json.dumps(r)


def test_renderer_inclui_codigo_categoria_metodo_e_origem_do_achado():
    obj, _ = caso('POS-02')
    obj['findings'][0].update(impact='informativo', action='registrar')
    md = api().renderizar_analise(obj)
    for valor in ['prova\\_primaria\\_ausente', 'fundamentacao', 'exemplo-contrato', 'q-efeito', 'Conclusões sobre a prova']:
        assert valor in md


def test_json_nao_compativel_em_snapshots_nao_provoca_excecao():
    obj, entradas = caso()
    ext = json.loads(entradas['extracao'])
    ext['documents'][0]['blocks'][0]['section'] = {'nao':'texto'}
    substituir(obj, entradas, 'extracao', ext)
    r = api().validar_analise(obj, entradas)
    assert not r['valido'] and 'entrada_invalida' in codes(r)


def test_objetivo_tem_de_corresponder_a_triagem():
    obj, entradas = caso()
    obj['objective'] = 'Objetivo materialmente diferente do registro de triagem.'
    assert 'triagem_incompativel' in codes(api().validar_analise(obj, entradas))


def test_nao_promove_integridade_declarada_nao_verificada():
    obj, entradas = caso()
    obj['technical_result'].update(integrity='nao_verificada', review_readiness='bloqueada')
    r = api().validar_analise(obj, entradas)
    assert r['valido']
    assert r['resultado_tecnico']['integrity'] == 'nao_verificada'


def test_resultado_calculado_preserva_tambem_restricoes_declaradas():
    obj, entradas = caso()
    obj['technical_result'].update(review_readiness='com_restricoes', restrictions=['Limite adicional registrado pelo responsável.'])
    r = api().validar_analise(obj, entradas)
    assert r['valido']
    assert 'Limite adicional registrado pelo responsável.' in r['resultado_tecnico']['restrictions']


@pytest.mark.parametrize('valor', [None, {}, 'invalido', [None], [{'id':[]}], [{'id':'f001','source':[]}], [{'id':'f001','kind':'inferencia','basis':[{}]}]])
def test_facts_malformado_falha_controladamente(valor):
    obj, entradas = caso()
    substituir(obj, entradas, 'fatos', {'schema_version':'1', 'facts':valor})
    r = api().validar_analise(obj, entradas)
    assert not r['valido'] and 'legado_invalido' in codes(r)


def test_extracao_com_avisos_malformados_nao_e_aceita():
    obj, entradas = caso()
    ex = json.loads(entradas['extracao'])
    ex['documents'][0]['warnings'] = {'atribuicao_ambigua':True}
    substituir(obj, entradas, 'extracao', ex)
    assert 'entrada_invalida' in codes(api().validar_analise(obj, entradas))


def inventario(obj, entradas):
    from pecas_proposta import propor_inventario
    raw = 'original simulado'.encode()
    inv = propor_inventario(entradas['extracao'], arquivo_sha256=hashlib.sha256(raw).hexdigest(),
        fronteiras=[{'block_id':'b0001','offset':0,'tipo':'acordao'}])
    for aid, tipo, bruto in [('original', 'original', raw), ('inventario', 'pecas',
            json.dumps(inv, ensure_ascii=False).encode('utf-8'))]:
        entradas[aid] = bruto
        obj['inputs'].append({'artifact_id':aid,'type':tipo,'path':'derived/'+aid+'.json',
            'sha256':hashlib.sha256(bruto).hexdigest()})
    return inv


def test_inventario_integro_e_fontes_vinculadas_continuam_propostas():
    obj, entradas = caso('POS-02')
    inv = inventario(obj, entradas)
    fs = {f['block_id']:f for f in inv['fragmentos']}
    facts = json.loads(entradas['fatos'])
    for f in facts['facts']:
        fragmento = fs[f['source']['block_id']]
        f['source']['peca'] = {'inventario_id':inv['inventario_id'],
            'inventario_sha256':hashlib.sha256(entradas['inventario']).hexdigest(),
            'piece_id':fragmento['destino']['piece_id'],'fragmentos':[fragmento['id']]}
    substituir(obj, entradas, 'fatos', facts)
    # A proposição jurídica supported não usa o inventário proposto: precisa continuar bloqueada.
    r = api().validar_analise(obj, entradas)
    assert 'legado_invalido' in codes(r)
    claims = json.loads(entradas['teses'])
    claims['claims'] = []
    substituir(obj, entradas, 'teses', claims)
    obj['references'] = [r for r in obj['references'] if r['id'] != 'ref-norma']
    obj['issues'][0]['grounds'][0]['basis_refs'] = ['ref-ato']
    antes = copy.deepcopy((obj, entradas))
    r = api().validar_analise(obj, entradas)
    assert r['valido'], r['erros']
    assert r['resultado_tecnico']['review_readiness'] == 'com_restricoes'
    assert (obj, entradas) == antes
    assert all(e['ator']['tipo'] != 'humano' for e in inv['eventos'])


def test_referencia_peca_sem_original_fornecido_reprova():
    obj, entradas = caso('POS-02')
    inventario(obj, entradas)
    obj['inputs'] = [m for m in obj['inputs'] if m['artifact_id'] != 'original']
    entradas.pop('original')
    assert 'inventario_invalido' in codes(api().validar_analise(obj, entradas))


def fonte_indisponivel():
    obj, entradas = caso('POS-02')
    claims = json.loads(entradas['teses'])
    claims['claims'][0].update(status='unverified', existence='indisponivel', quote_status='nao_conferida',
        sources=[{'source_id':'sintetica','origin':'oficial','access':'source_missing','error':'Indisponibilidade simulada.'}])
    substituir(obj, entradas, 'teses', claims)
    obj['issues'][0]['grounds'][0].update(qualification='inconclusiva', limitations=['Autoridade não foi acessada.'])
    return obj, entradas


def test_fonte_indisponivel_nao_vira_prova_primaria():
    obj, entradas = fonte_indisponivel()
    obj['issues'][0]['evidence'].append({'reference_id':'ref-norma','role':'favoravel','origin':'primaria','limitation':'Não foi acessada.'})
    assert 'prova_primaria_incompativel' in codes(api().validar_analise(obj, entradas))


def test_pesquisa_nao_declara_fonte_inacessivel_como_examinada():
    obj, entradas = fonte_indisponivel()
    obj['research_tasks'][0]['examined_refs'] = ['ref-norma']
    assert 'leitura_incompativel' in codes(api().validar_analise(obj, entradas))


def test_restricoes_nao_rebaixam_bloqueio_declarado():
    obj, entradas = caso('POS-02')
    obj['technical_result'].update(integrity='invalida', review_readiness='bloqueada')
    r = api().validar_analise(obj, entradas)
    assert r['valido']
    assert r['resultado_tecnico']['review_readiness'] == 'bloqueada'


def test_documento_excluido_nao_sustenta_conclusoes():
    obj, entradas = caso()
    novo = json.loads(entradas['extracao'])
    novo['documents'][0]['document_id'] = 'doc-extra'
    bruto = json.dumps(novo, ensure_ascii=False).encode('utf-8')
    entradas['extracao-extra'] = bruto
    obj['inputs'].append({'artifact_id':'extracao-extra','type':'extracao','path':'derived/extra.json','sha256':hashlib.sha256(bruto).hexdigest()})
    obj['scope'].update(document_ids=['doc-extra'], exclusions=[{'document_id':'doc-sintetico','reason':'Fora do escopo desta análise.'}])
    for c in obj['coverage']:
        c.update(input_id='extracao-extra', document_id='doc-extra')
    assert 'referencia_fora_do_escopo' in codes(api().validar_analise(obj, entradas))


@pytest.mark.parametrize('aid', ['fatos', 'teses'])
def test_derivado_de_outro_caso_nao_e_aceito(aid):
    obj, entradas = caso()
    d = json.loads(entradas[aid]);d['matter_id'] = 'outro-caso'
    substituir(obj, entradas, aid, d)
    assert 'triagem_incompativel' in codes(api().validar_analise(obj, entradas))


def test_other_sources_nulo_aceito_pelo_legado_nao_provoca_excecao():
    obj, entradas = caso()
    d = json.loads(entradas['fatos']);d['facts'][0]['other_sources'] = None
    substituir(obj, entradas, 'fatos', d)
    r = api().validar_analise(obj, entradas)
    assert r['valido'], r['erros']


def test_qualificacao_propaga_limites_das_premissas_indiretas():
    obj, entradas = caso()
    d = json.loads(entradas['fatos'])
    d['facts'][0] = {'id':'f001','kind':'inferencia','text':'Inferência a partir de informação não documentada.','basis':['f003']}
    d['facts'].append({'id':'f003','kind':'informado','text':'Informação fictícia sem documento.'})
    substituir(obj, entradas, 'fatos', d)
    obj['references'].append({'id':'ref-premissa','input_id':'fatos','collection':'facts','item_id':'f003'})
    assert 'qualificacao_incompativel' in codes(api().validar_analise(obj, entradas))


def test_extracao_ok_sem_texto_nao_finge_leitura():
    obj, entradas = caso()
    ex = json.loads(entradas['extracao'])
    ex['documents'][0]['blocks'] = []
    substituir(obj, entradas, 'extracao', ex)
    assert 'entrada_invalida' in codes(api().validar_analise(obj, entradas))


def test_campo_extra_status_nao_promove_kind_de_fato():
    obj, entradas = caso()
    d = json.loads(entradas['fatos'])
    d['facts'][0] = {'id':'f001','kind':'informado','status':'supported','text':'Informação fictícia sem documento.'}
    substituir(obj, entradas, 'fatos', d)
    assert 'qualificacao_incompativel' in codes(api().validar_analise(obj, entradas))
