"""Métricas de avaliação: referências técnicas não conferem peças reais."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
from pathlib import PurePosixPath
from tempfile import TemporaryDirectory

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))


def modulo():
    assert (RAIZ / 'scripts/avaliar_pecas.py').is_file(), 'Falta avaliador ORG-05'
    return importlib.import_module('avaliar_pecas')


def manifesto():
    return json.loads((RAIZ / 'tests/casos/org05/manifesto.json').read_text(encoding='utf-8'))


@pytest.fixture
def pasta_externa():
    with TemporaryDirectory(prefix='juris-org05-test-') as pasta:
        yield Path(pasta)


def test_caminho_windows_recusado_tambem_em_posix(monkeypatch):
    m = modulo(); monkeypatch.setattr(m,'Path',PurePosixPath)
    assert not m._relativo('C:original.pdf')


def test_hash_de_codigo_independe_de_crlf_lf(tmp_path):
    a,b = tmp_path/'a.py',tmp_path/'b.py'
    a.write_bytes(b'print(1)\r\n'); b.write_bytes(b'print(1)\n')
    m = modulo()
    assert hasattr(m,'_sha_produto'), 'Falta hash portavel do codigo'
    assert m._sha_produto(a,'lf') == m._sha_produto(b,'lf')
    assert m._sha_produto(a,'bytes') != m._sha_produto(b,'bytes')


def test_manifesto_separa_processos_e_preserva_modalidades():
    m = manifesto()
    modulo().validar_manifesto(m)
    novos = [c for c in m['casos'] if c['grupo'] == 'avaliacao']
    assert len({c['processo_id'] for c in novos}) == 2
    assert {c['id'] for c in m['casos'] if c['referencia']['conferencia_humana']} == {'ORG05-P01', 'ORG05-P02'}
    assert all(c['referencia']['origem'] == 'modelo_tecnico' for c in m['casos'] if c['grupo'] == 'desenvolvimento')


@pytest.mark.parametrize('duplicar', ['processo', 'bytes', 'id', 'processo_normalizado'])
def test_recusa_vazamento_entre_coortes_e_ids_duplicados(duplicar):
    m = manifesto()
    c = copy.deepcopy(m['casos'][0]); c['grupo'] = 'desenvolvimento'; c['id'] = 'nova-observacao'
    if duplicar == 'processo': c['sha256'] = 'f' * 64
    if duplicar == 'bytes': c['processo_id'] = 'outro:123'
    if duplicar == 'id': c['id'] = m['casos'][0]['id']; c['processo_id'] = 'outro'; c['sha256'] = 'e' * 64
    if duplicar == 'processo_normalizado':
        c['processo_id'] = 'TJMG:10000250126307001'; c['sha256'] = 'e' * 64
    m['casos'].append(c)
    with pytest.raises(ValueError): modulo().validar_manifesto(m)


@pytest.mark.parametrize('campo,valor', [('modalidade','inventada'),('sha256','x'),('grupo','treino2')])
def test_manifesto_incompativel_falha_explicitamente(campo,valor):
    m = manifesto(); m['casos'][0][campo] = valor
    with pytest.raises(ValueError): modulo().validar_manifesto(m)


def test_conferencia_humana_nao_pode_ser_inferida_do_modelo():
    m = manifesto(); m['casos'][0]['referencia']['origem'] = 'modelo_tecnico'
    with pytest.raises(ValueError): modulo().validar_manifesto(m)


def test_confirmacao_do_titular_vincula_somente_dois_gabaritos_e_pdfs():
    m = manifesto()
    registro = json.loads((RAIZ / 'tests/casos/org05/conferencia-humana.json').read_text(encoding='utf-8'))
    assert registro['data'] == '2026-10-22'
    assert registro['declaracao'] == 'P01/P02 revisados e aprovados. proceda com a finalização da pendência, commit as alterações'
    assert {c['id'] for c in registro['casos']} == {'ORG05-P01', 'ORG05-P02'}
    for aprovado in registro['casos']:
        c = next(c for c in m['casos'] if c['id'] == aprovado['id'])
        ref = c['referencia']
        assert ref['origem'] == 'humano_identificado' and ref['conferencia_humana'] is True
        assert ref['revisor'] == registro['revisor']
        assert ref['registro_conferencia'] == 'tests/casos/org05/conferencia-humana.json'
        assert c['arquivo'] == aprovado['arquivo']
        assert hashlib.sha256((RAIZ / c['arquivo']).read_bytes()).hexdigest() == c['sha256'] == aprovado['sha256']
        gabarito = {'paginas': ref['paginas'], 'pecas': ref['pecas']}
        assert gabarito == aprovado['gabarito']
        assert gabarito['pecas'] == [{'inicio': 1, 'fim': ref['paginas'], 'tipo': 'acordao'}]
        payload = json.dumps(gabarito, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        assert hashlib.sha256(payload).hexdigest() == aprovado['gabarito_sha256']


@pytest.mark.parametrize('revisor', [None, '', '   ', 123])
def test_gabarito_humano_exige_revisor_identificado(revisor):
    m = manifesto(); m['casos'][0]['referencia']['revisor'] = revisor
    with pytest.raises(ValueError): modulo().validar_manifesto(m)


def test_metricas_contam_cortes_e_nao_inventam_denominador():
    ref = [{'inicio':1,'fim':16,'tipo':'acordao'}]
    pred = [{'inicio':1,'fim':2,'tipo':'nao_identificada'}, {'inicio':3,'fim':16,'tipo':'acordao'}]
    r = modulo().comparar(ref,pred)
    assert r['fronteiras_corretas'] == {'numerador':0,'denominador':0}
    assert r['fragmentacoes'] == 1 and r['fusoes'] == 0
    assert r['tipo_correto'] == {'numerador':0,'denominador':0}
    assert r['abstencoes'] == {'numerador':1,'denominador':2}


def test_controle_positivo_tipo_e_limites_e_fusao():
    ref = [{'inicio':1,'fim':2,'tipo':'sentenca'}, {'inicio':3,'fim':5,'tipo':'acordao'}]
    r = modulo().comparar(ref,ref)
    assert r['fronteiras_corretas'] == {'numerador':1,'denominador':1}
    assert r['tipo_correto'] == {'numerador':2,'denominador':2}
    assert r['fragmentacoes'] == r['fusoes'] == 0
    r = modulo().comparar(ref,[{'inicio':1,'fim':5,'tipo':'acordao'}])
    assert r['fusoes'] == 1 and r['tipo_correto']['denominador'] == 0


def test_ausencia_de_proposta_nao_vira_acerto_de_tipo():
    r = modulo().comparar([{'inicio':1,'fim':1,'tipo':'acordao'}],[])
    assert r['tipo_correto'] == {'numerador':0,'denominador':0}
    assert r['pecas_esperadas'] == 1 and r['pecas_propostas'] == 0
    assert r['pecas_correspondentes'] == {'numerador':0,'denominador':1}


@pytest.mark.parametrize('campo,valor',[('id','../saida'),('arquivo','../original.pdf'),
    ('arquivo','C:original.pdf'),('arquivo',r'\fora-da-raiz\documento.pdf'),
    ('arquivo',r'..\documento.pdf'),('arquivo',r'\\servidor\pasta\documento.pdf')])
def test_caminhos_do_manifesto_nao_escapam_da_raiz(campo,valor):
    m = manifesto(); m['casos'][0][campo] = valor
    with pytest.raises(ValueError): modulo().validar_manifesto(m)


def test_mesma_pagina_nao_simula_precisao_de_offset():
    ref = [{'inicio':1,'fim':1,'tipo':'sentenca'}, {'inicio':1,'fim':1,'tipo':'acordao'}]
    r = modulo().comparar(ref,ref)
    assert r['precisao'] == 'insuficiente_intrapagina'
    assert r['fronteiras_corretas']['denominador'] == 0
    assert r['tipo_correto']['denominador'] == 0


def test_propostas_intrapagina_nao_multiplicam_acertos():
    ref = [{'inicio':1,'fim':1,'tipo':'sentenca'}]
    r = modulo().comparar(ref,ref+ref)
    assert r['precisao'] == 'insuficiente_intrapagina'
    assert r['pecas_correspondentes'] == {'numerador':0,'denominador':0}
    assert r['tipo_correto'] == {'numerador':0,'denominador':0}


def test_consolidacao_canonicaliza_processo_sem_contar_modalidade_como_unidade():
    casos = [{'id':str(i),'processo_id':p,'natureza':'processo','grupo':'avaliacao',
              'modalidade':'nativo','execucao':'concluida','metricas':modulo().comparar([],[])}
             for i,p in enumerate(['tjmg:1.0000.25.012630-7/001','TJMG:10000250126307001'])]
    g = modulo().consolidar(casos)[0]
    assert g['observacoes'] == 2 and g['unidades'] == g['processos'] == 1


def test_rejeita_produto_alterado_e_original_divergente(pasta_externa):
    tmp_path = pasta_externa
    m = manifesto(); m['produto_sha256']['scripts/extract.py'] = 'f'*64
    p = tmp_path/'manifesto.json'; p.write_text(json.dumps(m),encoding='utf-8')
    with pytest.raises(ValueError,match='produto_alterado'): modulo().avaliar_manifesto(p,RAIZ,tmp_path/'saida')
    m = manifesto(); m['casos'] = [m['casos'][0]]; m['casos'][0]['sha256'] = 'f'*64
    p.write_text(json.dumps(m),encoding='utf-8')
    r = modulo().avaliar_manifesto(p,RAIZ,tmp_path/'saida')
    assert r['casos'][0]['execucao'] == 'falhou' and r['casos'][0]['motivo'] == 'original_divergente'
    assert r['grupos'][0]['avaliados'] == 0


def test_arquivo_ausente_fica_fora_dos_denominadores(pasta_externa):
    tmp_path = pasta_externa
    m = manifesto(); m['casos'] = [m['casos'][0]]; m['casos'][0]['arquivo'] = 'nao-existe.pdf'
    p = tmp_path/'manifesto.json'; p.write_text(json.dumps(m),encoding='utf-8')
    r = modulo().avaliar_manifesto(p,RAIZ,tmp_path/'saida')
    assert r['casos'][0]['execucao'] == 'nao_executada'
    assert r['grupos'][0]['avaliados'] == 0


def test_pdf_real_fluxo_preserva_proposta_e_bloqueia_material(pasta_externa):
    tmp_path = pasta_externa
    m = manifesto(); m['casos'] = [m['casos'][0]]
    p = tmp_path/'manifesto.json'; p.write_text(json.dumps(m),encoding='utf-8')
    antes = hashlib.sha256((RAIZ/m['casos'][0]['arquivo']).read_bytes()).hexdigest()
    r = modulo().avaliar_manifesto(p,RAIZ,tmp_path/'saida')
    c = r['casos'][0]
    assert c['execucao'] == 'concluida' and c['integridade_inventario']
    assert not c['conferencia_humana'] and not r['liberacao_material']
    assert c['integracao']['analise_sem_erros'] and c['integracao']['avisos_pecas']
    assert c['integracao']['fundamentada_bloqueada']
    assert c['integracao']['cronologia_preserva_vinculos']
    assert c['integracao']['g16_fundamentada'] == 'reprovado'
    assert hashlib.sha256((RAIZ/m['casos'][0]['arquivo']).read_bytes()).hexdigest() == antes
    assert r['grupos'][0]['processos'] == 1
    inv = json.loads((tmp_path/'saida'/c['id']/'pecas.json').read_text(encoding='utf-8'))
    assert all(e['ator']['tipo'] != 'humano' for e in inv['eventos'])


def test_totais_separam_processo_de_observacao_ocr():
    casos = [{'id':str(i),'processo_id':'mesmo','natureza':'processo','grupo':'desenvolvimento',
              'modalidade':m,'execucao':'concluida','metricas':modulo().comparar([],[])}
             for i,m in enumerate(['ocr','sem_ocr'])]
    grupos = modulo().consolidar(casos)
    assert len(grupos) == 2 and all(g['processos'] == 1 and g['observacoes'] == 1 for g in grupos)
