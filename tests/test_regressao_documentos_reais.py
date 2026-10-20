"""R07/R10: estrutura conferida no PDF público; não é gabarito jurídico."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import ocr  # noqa: E402

PASTA = RAIZ / "tests" / "casos" / "regressao"
R07 = PASTA / "R07_tjmg_ai_176803.pdf"
R10 = PASTA / "R10_picos_oficio_106_2022.pdf"
XREF = PASTA / "taquaral_oficio_38_2025_xref.pdf"


def test_r06_ementa_transcrita_nao_vira_secao_principal_do_stf():
    doc, _ = extract.extrair(PASTA / "R06_stf_are_1563128_rg.pdf")
    assert doc["status"] == "partial" and doc["page_count"] == 11
    assert any(a["codigo"] == "secao_aninhada_ambigua" and a["pagina"] == 9 for a in doc["warnings"])
    citacao = next(b for b in doc["blocks"] if "EMENTA: AGRAVO INTERNO." in b["text"])
    assert citacao["page"] == 9 and citacao["section"] == "decisao" and citacao["is_quote"]
    assert all(b["page"] <= 2 for b in doc["blocks"] if b["section"] == "ementa")


def test_r07_delimita_acordao_e_voto_sem_confundir_com_ementa():
    doc, _ = extract.extrair(R07)
    assert doc["status"] == "partial" and doc["page_count"] == 12
    assert "secao_aninhada_ambigua" in {a["codigo"] for a in doc["warnings"]}
    segmentos = extract.segmentos(doc)
    ementa = next(s for s in segmentos if s["section"] == "ementa")
    acordao = next(s for s in segmentos if s["section"] == "acordao")
    voto = next(s for s in segmentos if s["section"] == "voto")
    assert ementa["page"] == ementa["page_end"] == 1
    # O nome do relator abre a página 2 antes do título V O T O.
    assert acordao["page"] == 1 and acordao["page_end"] == 2
    assert voto["page"] == 2 and voto["page_end"] == 12
    assert "DAR PROVIMENTO AO RECURSO" in acordao["text"]
    assert "Trata-se de agravo de instrumento" in voto["text"]
    assert "Trata-se de agravo de instrumento" not in ementa["text"]
    assert "Trata-se de agravo de instrumento" not in acordao["text"]
    assert all(b["locator"] and b["page"] for b in doc["blocks"])


def test_r10_original_e_imagem_real_sem_camada_textual():
    import pdfplumber

    with pdfplumber.open(R10) as pdf:
        assert len(pdf.pages) == 1
        assert not pdf.pages[0].chars and pdf.pages[0].images
    doc, _ = extract.extrair(R10)
    assert doc["status"] == "no_text" and doc["page_count"] == 1
    assert not doc["blocks"]
    assert "pagina_sem_texto" in {a["codigo"] for a in doc["warnings"]}


def test_r10_ocr_real_mantem_estado_partial_e_localizadores():
    exe = ocr.localizar_tesseract()
    if exe is None or "por" not in ocr.idiomas(exe):
        pytest.skip("R10 exige Tesseract com idioma por para o gabarito em português")
    doc, _ = extract.extrair(R10, ocr=True)
    assert doc["status"] == "partial" and doc["page_count"] == 1
    assert "ocr_aplicado" in {a["codigo"] for a in doc["warnings"]}
    assert doc["blocks"] and all("ocr" in b["tags"] for b in doc["blocks"])
    assert all(b["page"] == 1 and b["locator"] == "p.1" for b in doc["blocks"])
    texto = " ".join(b["text"] for b in doc["blocks"])
    for trecho in ("106/2022 PGM", "23 de Maio de 2022", "Centro Especializado", "Ministério da Saúde"):
        assert trecho.casefold() in texto.casefold()


@pytest.mark.parametrize("usar_ocr", [False, True])
def test_pdf_real_com_xref_deslocado_nao_vira_documento_sem_texto(usar_ocr, tmp_path):
    cache = tmp_path / "cache"
    antes = XREF.read_bytes()
    doc, hit = extract.extrair(XREF, str(cache), ocr=usar_ocr)
    assert not hit
    assert doc["status"] == "failed"
    assert doc["warnings"][0]["codigo"] == "erro_de_leitura"
    assert "páginas" in doc["warnings"][0]["detalhe"]
    assert not list(cache.glob("*.json"))
    assert XREF.read_bytes() == antes


def test_fixtures_reais_conferem_com_os_bytes_registrados_na_coleta():
    proveniencia = json.loads((PASTA / "proveniencia-r07-r10.json").read_text(encoding="utf-8"))
    for fonte in proveniencia["documentos"]:
        bruto = (RAIZ / fonte["arquivo"]).read_bytes()
        assert len(bruto) == fonte["bytes"]
        assert hashlib.sha256(bruto).hexdigest() == fonte["sha256"]
