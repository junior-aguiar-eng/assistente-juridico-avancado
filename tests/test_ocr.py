"""OCR opcional: página digitalizada sem texto vira texto com tag 'ocr', status partial e aviso; sem Tesseract, aviso explícito."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import ocr  # noqa: E402

TESSERACT = ocr.localizar_tesseract()
PRECISA_OCR = pytest.mark.skipif(TESSERACT is None, reason="Tesseract não instalado")

LINHAS = ["CONTRATO DE PRESTACAO DE SERVICOS", "Clausula 1. O prazo e de 24 meses.", "Valor mensal: R$ 1.500,00"]


def pdf_escaneado(caminho, linhas=LINHAS, paginas=1):
    from PIL import Image, ImageDraw, ImageFont

    imgs = []
    for _ in range(paginas):
        img = Image.new("RGB", (1240, 1754), "white")  # A4 a 150 dpi
        d = ImageDraw.Draw(img)
        fonte = ImageFont.load_default(size=44)
        for i, l in enumerate(linhas):
            d.text((120, 200 + i * 90), l, fill="black", font=fonte)
        imgs.append(img)
    imgs[0].save(caminho, "PDF", resolution=150.0, save_all=True, append_images=imgs[1:])


def cods(doc):
    return [a["codigo"] for a in doc["warnings"]]


def test_sem_ocr_pagina_escaneada_continua_sem_texto(tmp_path):
    f = tmp_path / "scan.pdf"
    pdf_escaneado(f)
    doc, _ = extract.extrair(f)
    assert doc["status"] == "no_text" and "ocr_aplicado" not in cods(doc)


@PRECISA_OCR
def test_com_ocr_le_o_texto_marca_ocr_e_fica_partial(tmp_path):
    f = tmp_path / "scan.pdf"
    pdf_escaneado(f)
    doc, _ = extract.extrair(f, ocr=True)
    texto = " ".join(b["text"] for b in doc["blocks"]).upper()
    assert "CONTRATO" in texto and "PRESTACAO" in texto and "24 MESES" in texto
    assert doc["status"] == "partial" and "ocr_aplicado" in cods(doc)
    assert doc["blocks"] and all("ocr" in b["tags"] for b in doc["blocks"] if b["section"] != "rodape")
    assert all(b["locator"] and b["page"] == 1 for b in doc["blocks"])


@PRECISA_OCR
def test_sem_idioma_portugues_o_aviso_diz_o_custo():
    lang, aviso = ocr.escolher_idioma(TESSERACT)
    if lang == "por":
        assert aviso is None
    else:
        assert lang == "eng" and "por" in aviso


@PRECISA_OCR
def test_cache_separa_resultado_com_e_sem_ocr(tmp_path):
    f = tmp_path / "scan.pdf"
    pdf_escaneado(f)
    cache = str(tmp_path / "cache")
    a, hit_a = extract.extrair(f, cache)
    b, hit_b = extract.extrair(f, cache, ocr=True)
    c, hit_c = extract.extrair(f, cache, ocr=True)
    assert (hit_a, hit_b, hit_c) == (False, False, True)
    assert a["status"] == "no_text" and b["status"] == "partial" and c["status"] == "partial"


def test_pdf_com_texto_nativo_nao_aciona_ocr(tmp_path):
    doc, _ = extract.extrair(RAIZ / "tests" / "casos" / "verificacao_stj" / "fontes" / "stj_inteiro_teor.pdf", ocr=True)
    assert "ocr_aplicado" not in cods(doc) and not any("ocr" in b["tags"] for b in doc["blocks"])


def test_tesseract_ausente_vira_aviso_e_nao_erro(tmp_path, monkeypatch):
    monkeypatch.setattr(ocr, "localizar_tesseract", lambda: None)
    f = tmp_path / "scan.pdf"
    pdf_escaneado(f)
    doc, _ = extract.extrair(f, ocr=True)
    assert doc["status"] == "no_text" and "ocr_indisponivel" in cods(doc)


def test_validador_avisa_quando_o_trecho_vem_de_ocr():
    import validate

    doc = {"document_id": "doc-1", "blocks": [{"id": "b1", "locator": "p.1", "text": "O prazo e de 24 meses contados da assinatura.",
                                               "tags": ["ocr"], "page": 1, "is_quote": False, "section": "corpo"}]}
    r = validate.Resultado()
    validate._conferir_trecho(r, "$.x", {"document_id": "doc-1", "block_id": "b1"}, "p.1", "O prazo e de 24 meses", {"doc-1": doc})
    assert [a["codigo"] for a in r.avisos] == ["trecho_de_ocr"] and not r.erros
