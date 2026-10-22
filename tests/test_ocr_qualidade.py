"""Qualidade técnica de OCR; dados artificiais, sem gabarito humano implícito."""
import hashlib
import math
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))
import ocr


def precisa(nome):
    assert hasattr(ocr, nome), f'Falta {nome} no OCR de produção'
    return getattr(ocr, nome)


@pytest.mark.parametrize('largura,altura', [(595,842),(2513,2932),(2935,3018),(100000,100000)])
def test_rasterizacao_limitada_preserva_proporcao_e_orcamento(largura, altura):
    dpi = precisa('resolucao_limitada')(largura, altura)
    w, h = math.ceil(largura*dpi/72), math.ceil(altura*dpi/72)
    assert 0 < dpi <= 300
    assert w*h <= ocr.MAX_PIXELS and max(w,h) <= ocr.MAX_LADO


@pytest.mark.parametrize('largura,altura', [(0,842),(-1,842),(math.inf,842),(595,math.nan)])
def test_recusa_dimensoes_invalidas(largura,altura):
    with pytest.raises(ValueError): precisa('resolucao_limitada')(largura,altura)


CABECALHO = 'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'

def tsv(conf='90',left='10',texto='TEXTO',width='20'):
    return CABECALHO+f'5\t1\t1\t1\t1\t1\t{left}\t20\t{width}\t10\t{conf}\t{texto}\n'


def test_tsv_mapeia_cada_eixo_para_pontos_e_preserva_baixa_confianca():
    r = precisa('ler_tsv')(tsv()+tsv('20',left='40',texto='INCERTO').split('\n',1)[1], largura_pdf=1000,altura_pdf=2000,largura_img=100,altura_img=400)
    l = r['linhas'][0]
    assert (l['x0'],l['x1'],l['top'],l['bottom']) == (100,600,100,150)
    assert l['text'] == 'TEXTO INCERTO'
    assert r['confianca'] == 55
    assert r['palavras'] == 2 and r['palavras_baixa_confianca'] == 1


@pytest.mark.parametrize('kwargs', [{'conf':'nan'},{'conf':'inf'},{'left':'ruim'},{'left':'-1'},{'width':'999'},{'conf':'101'}])
def test_tsv_malformado_nao_cria_texto_confiavel(kwargs):
    r = precisa('ler_tsv')(tsv(**kwargs),largura_pdf=1000,altura_pdf=2000,largura_img=100,altura_img=400)
    assert r['linhas'] == [] and r['confianca'] == 0
    assert r['palavras_descartadas'] == 1


def test_preprocessamento_e_derivado_sem_alterar_a_imagem_original():
    from PIL import Image
    img=Image.new('RGB',(50,40),'white'); img.putpixel((10,10),(0,0,0))
    antes=hashlib.sha256(img.tobytes()).hexdigest()
    out=precisa('preparar_imagem')(img,'mediana')
    assert out.size == img.size and out.mode == 'L'
    assert hashlib.sha256(img.tobytes()).hexdigest() == antes
    with pytest.raises(ValueError): ocr.preparar_imagem(img,'desconhecido')


def test_fingerprint_inclui_modelo_perfil_e_limites(tmp_path,monkeypatch):
    modelo=tmp_path/'por.traineddata'; modelo.write_bytes(b'modelo artificial A')
    monkeypatch.setenv('JURIS_TESSDATA',str(tmp_path))
    exe=ocr.localizar_tesseract()
    if not exe: pytest.skip('Tesseract ausente')
    a=precisa('configuracao')('padrao')
    assert a['modelo_sha256'] == hashlib.sha256(modelo.read_bytes()).hexdigest()
    assert a['cache_verificavel'] and a['max_pixels'] == ocr.MAX_PIXELS
    b=ocr.configuracao('mediana')
    assert a != b
    modelo.write_bytes(b'modelo artificial B')
    assert a['modelo_sha256'] != ocr.configuracao('padrao')['modelo_sha256']


def test_modelo_nao_identificado_nao_autoriza_reuso_de_cache(tmp_path,monkeypatch):
    monkeypatch.setenv('JURIS_TESSDATA',str(tmp_path))
    r=precisa('configuracao')('padrao')
    assert not r['cache_verificavel'] and r['modelo_sha256'] is None


def test_extrator_oferece_perfil_opcional_e_separa_cache(tmp_path):
    from test_ocr import pdf_escaneado
    import extract
    if ocr.localizar_tesseract() is None: pytest.skip('Tesseract ausente')
    p=tmp_path/'s.pdf'; pdf_escaneado(p)
    padrao,h1=extract.extrair(p,str(tmp_path/'cache'),ocr=True)
    mediana,h2=extract.extrair(p,str(tmp_path/'cache'),ocr=True,ocr_perfil='mediana')
    outra,h3=extract.extrair(p,str(tmp_path/'cache'),ocr=True,ocr_perfil='mediana')
    assert (h1,h2,h3)==(False,False,True)
    assert padrao['ocr_configuracao']['perfil']=='padrao'
    assert mediana['ocr_configuracao']['perfil']=='mediana'
    assert mediana['status']==outra['status']=='partial'


def test_proporcao_de_palavras_incertas_mantem_alerta_mesmo_com_media_alta(monkeypatch,tmp_path):
    import extract
    monkeypatch.setattr(ocr,'localizar_tesseract',lambda:'exe-simulado')
    monkeypatch.setattr(ocr,'escolher_idioma',lambda _:('por',None))
    monkeypatch.setattr(ocr,'ler_paginas',lambda *a,**k:{1:{'linhas':[{'text':'Texto artificial','x0':0,'x1':10,'top':1,'bottom':2,'gap':0}],
        'confianca':80,'palavras':4,'palavras_baixa_confianca':1,'palavras_descartadas':1}})
    avisos=[]
    extract._aplicar_ocr(tmp_path/'fake.pdf',[(100,100,[])],[1],avisos)
    codes={a['codigo'] for a in avisos}
    assert {'ocr_baixa_confianca','ocr_dados_descartados'} <= codes


def test_limite_preserva_a4_a_300dpi_e_imagem_fonte_r10_a_72dpi():
    assert precisa('resolucao_limitada')(595,842)==300
    assert ocr.resolucao_limitada(2935,3018,72)==72


def test_fingerprint_registra_bibliotecas_que_rasterizam_e_filtram():
    from importlib.metadata import version
    r=precisa('configuracao')()
    assert r['bibliotecas']['Pillow']==version('Pillow')
    assert r['bibliotecas']['pypdfium2']==version('pypdfium2')


def test_resolucao_opcional_chega_ao_motor_e_separa_cache(tmp_path,monkeypatch):
    from test_ocr import pdf_escaneado
    import extract
    if not ocr.localizar_tesseract(): pytest.skip('Tesseract ausente')
    original=tmp_path/'s.pdf'; pdf_escaneado(original)
    vistos=[]
    ler=ocr.ler_paginas
    def observar(*a,**kw):
        vistos.append(kw['dpi']); return ler(*a,**kw)
    monkeypatch.setattr(ocr,'ler_paginas',observar)
    a,hit1=extract.extrair(original,str(tmp_path/'cache'),ocr=True,ocr_perfil='mediana',ocr_dpi=72)
    b,hit2=extract.extrair(original,str(tmp_path/'cache'),ocr=True,ocr_perfil='mediana',ocr_dpi=150)
    assert (hit1,hit2)==(False,False) and vistos==[72,150]
    assert a['ocr_configuracao']['dpi']==72 and b['ocr_configuracao']['dpi']==150


@pytest.mark.parametrize('dpi',[0,-1,math.inf,math.nan])
def test_extrator_recusa_resolucao_ocr_invalida_sem_crash(tmp_path,dpi):
    from test_ocr import pdf_escaneado
    import extract
    p=tmp_path/'s.pdf'; pdf_escaneado(p)
    doc,_=extract.extrair(p,ocr=True,ocr_dpi=dpi)
    assert doc['status']=='failed'
    assert doc['warnings'][0]['codigo']=='parametro_invalido'


def test_cli_nao_serializa_nan_da_resolucao_em_json(tmp_path):
    import subprocess
    from test_ocr import pdf_escaneado
    p=tmp_path/'s.pdf'; pdf_escaneado(p)
    r=subprocess.run([sys.executable,str(RAIZ/'scripts/extract.py'),str(p),'--ocr','--ocr-dpi','nan','--no-cache'],capture_output=True,text=True)
    assert r.returncode==2 and r.stdout==''
    assert 'resolução' in r.stderr


@pytest.mark.parametrize('linha',[
    '5\t1\t1\t1\t1\t2\t40\t20\t20\t10\t10\n',
    '5\t1\t1\t1\t1\t2\t40\t20\t20\t10\t99\tARTIGO\t593\n',
])
def test_tsv_truncado_ou_com_campos_extras_e_contabilizado(linha):
    r=ocr.ler_tsv(tsv('99',texto='VALIDO')+linha,largura_pdf=1000,altura_pdf=2000,largura_img=100,altura_img=400)
    assert r['palavras_descartadas']==1
    assert r['palavras']==1 and r['linhas'][0]['text']=='VALIDO'


def test_tsv_cabecalho_incompleto_falha_explicitamente():
    with pytest.raises(ValueError): ocr.ler_tsv('conf\ttext\n99\tVALIDO\n',largura_pdf=100,altura_pdf=200,largura_img=100,altura_img=200)


@pytest.mark.parametrize('rotacao,esperado',[
    (0,(150,200,250,250)),(90,(550,150,600,250)),
    (180,(350,550,450,600)),(270,(200,350,250,450)),
])
def test_ocr_cropbox_preserva_origem_e_escala_com_rotacoes(tmp_path,monkeypatch,rotacao,esperado):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject,NameObject,RectangleObject
    import subprocess
    from PIL import Image,ImageOps
    w=PdfWriter(); pg=w.add_blank_page(width=600,height=800)
    pg.cropbox=RectangleObject([100,100,500,700])
    stream=DecodedStreamObject(); stream.set_data(b'0 0 0 rg 150 550 100 50 re f')
    pg[NameObject('/Contents')]=w._add_object(stream)
    if rotacao: pg.rotate(rotacao)
    path=tmp_path/'crop.pdf'
    with path.open('wb') as f: w.write(f)
    def motor(cmd,**kw):
        img=Image.open(next(a for a in cmd if a.endswith('.png'))).convert('L')
        box=ImageOps.invert(img).point(lambda v:255 if v>128 else 0).getbbox()
        x,y,xx,yy=box
        saida=CABECALHO+f'5\t1\t1\t1\t1\t1\t{x}\t{y}\t{xx-x}\t{yy-y}\t99\tRETANGULO\n'
        return subprocess.CompletedProcess(cmd,0,saida.encode(),b'')
    monkeypatch.setattr(ocr.subprocess,'run',motor)
    r=ocr.ler_paginas('motor-simulado',path,[1],'por',dpi=72)[1]['linhas'][0]
    assert (r['x0'],r['top'],r['x1'],r['bottom'])==pytest.approx(esperado,abs=1)
