import importlib
import json
import sys
from pathlib import Path

import pytest

RAIZ=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(RAIZ/'scripts'))


def modulo():
    assert (RAIZ/'scripts/diagnostico_ocr.py').exists(), 'Falta o diagnóstico de OCR reproduzível'
    return importlib.import_module('diagnostico_ocr')


def gabarito(estado='conferido'):
    return {'arquivo_sha256':'a'*64,'conferencia':{'estado':estado,'ator_tipo':'humano','ator':'Pessoa simulada'},
            'amostras':[{'id':'a1','pagina':1,'trecho':'RELATÓRIO'},{'id':'a2','pagina':2,'trecho':'art. 593'}]}


def test_avalia_trechos_por_pagina_sem_liberar_texto_integral():
    r=modulo().avaliar_amostras({1:{'linhas':[{'text':'R E L A T Ó R I O art. 593'}]},2:{'linhas':[]}},gabarito(),arquivo_sha256='a'*64)
    assert r['acertos']==1 and r['total']==2
    assert r['conferencia_humana_da_amostra']
    assert not r['uso_material_liberado']
    assert 'RELATÓRIO' not in json.dumps(r)


def test_gabarito_proposto_ou_ausente_nao_vira_conferencia_humana():
    m=modulo()
    r=m.avaliar_amostras({},gabarito('proposto'),arquivo_sha256='a'*64)
    assert not r['conferencia_humana_da_amostra']
    r=m.avaliar_amostras({},None,arquivo_sha256='a'*64)
    assert r['total']==0 and not r['conferencia_humana_da_amostra']


def test_recusa_gabarito_de_outro_original():
    with pytest.raises(ValueError): modulo().avaliar_amostras({},gabarito(),arquivo_sha256='b'*64)


def test_seis_amostras_reais_tem_confirmacao_humana_com_escopo_limitado():
    g=json.loads((RAIZ/'tests/casos/ocr_qualidade/ORG-R10-PRIVADO-amostras.json').read_text(encoding='utf-8'))
    assert g['conferencia']['estado']=='conferido'
    assert g['conferencia']['ator_tipo']=='humano'
    assert len(g['amostras'])==6
    assert [a['pagina'] for a in g['amostras']]==[1,1,1,2,2,2]
    assert g['conferencia']['escopo']=='apenas os seis trechos e páginas; não confirma transcrição integral, dados pessoais ou mérito'


def test_cli_real_nao_transcreve_conteudo_nem_modifica_original(tmp_path):
    import hashlib, subprocess
    import ocr
    from test_ocr import pdf_escaneado
    if not ocr.localizar_tesseract(): pytest.skip('Tesseract ausente')
    original=tmp_path/'scan.pdf'; pdf_escaneado(original)
    sha=hashlib.sha256(original.read_bytes()).hexdigest()
    g=gabarito('proposto'); g['arquivo_sha256']=sha
    g['amostras']=[{'id':'a1','pagina':1,'trecho':'CONTRATO'}]
    path=tmp_path/'g.json'; path.write_text(json.dumps(g))
    r=subprocess.run([sys.executable,str(RAIZ/'scripts/diagnostico_ocr.py'),'--original',str(original),
                      '--gabarito',str(path),'--perfil','mediana'],capture_output=True,text=True)
    assert r.stdout.strip(), 'CLI precisa retornar JSON de diagnóstico'
    obj=json.loads(r.stdout)
    assert r.returncode==0 and obj['execucao']=='concluida'
    assert obj['status_leitura']=='partial' and obj['amostra']['acertos']==1
    assert not obj['amostra']['conferencia_humana_da_amostra']
    assert not obj['amostra']['uso_material_liberado']
    assert 'CONTRATO' not in r.stdout
    assert hashlib.sha256(original.read_bytes()).hexdigest()==sha


def test_pdf_malformado_nao_vaza_conteudo_em_traceback(tmp_path):
    import subprocess
    import ocr
    if not ocr.localizar_tesseract(): pytest.skip('Tesseract ausente')
    original=tmp_path/'invalido.pdf'
    original.write_bytes(b'''%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >> endobj
4 0 obj << /Filter /Unknown /User (DADO_SINTETICO_PRIVADO) >> endobj
trailer << /Root 1 0 R /Encrypt 4 0 R /ID [(abc)(abc)] >>
%%EOF''')
    r=subprocess.run([sys.executable,str(RAIZ/'scripts/diagnostico_ocr.py'),'--original',str(original)],capture_output=True,text=True)
    assert 'DADO_SINTETICO_PRIVADO' not in r.stdout+r.stderr
    assert r.returncode==1 and json.loads(r.stdout)['execucao']=='falhou'
    assert r.stderr==''
