"""Caso real do STJ (AREsp 2.432.194/SP) e do CC art. 206: verificação ponta a ponta.

Fontes lidas em 17/10/2026: inteiro teor em PDF (processo.stj.jus.br) e CC compilado (Planalto).
"""
import copy
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import validate  # noqa: E402

CASO = RAIZ / "tests" / "casos" / "verificacao_stj"
PDF_NOVO = CASO / "fontes" / "stj_inteiro_teor.pdf"
PDF_ANTIGO = RAIZ / "tests" / "casos" / "stj_aresp_2432194.pdf"
CC_MD = CASO / "fontes" / "cc_compilado.md"


@pytest.fixture(scope="module")
def pdf():
    return extract.extrair(PDF_NOVO)[0]


@pytest.fixture(scope="module")
def idx(pdf):
    md = extract.extrair(CC_MD)[0]
    return {pdf["document_id"]: pdf, md["document_id"]: md}


@pytest.fixture
def claims():
    return json.loads((CASO / "claims.json").read_text(encoding="utf-8"))


def test_claims_historicos_bloqueados_por_fontes_sem_document_id(claims, idx):
    r = validate.validar_claims(claims, idx)
    assert [(e["codigo"], e["caminho"]) for e in r.erros] == [
        ("campo_obrigatorio", "$.claims[0].sources[1].document_id"),
        ("campo_obrigatorio", "$.claims[4].sources[0].document_id"),
    ]
    assert r.avisos == []
    estados = {c["id"]: c["status"] for c in claims["claims"]}
    assert estados == {"c001": "supported", "c002": "unsupported", "c003": "unverified",
                       "c004": "supported", "c005": "partial"}


def test_mesmo_acordao_baixado_duas_vezes_tem_bytes_diferentes_e_texto_igual(pdf):
    antigo = extract.extrair(PDF_ANTIGO)[0]
    assert antigo["sha256"] != pdf["sha256"]
    assert antigo["text_sha256"] == pdf["text_sha256"]
    assert [b["text"] for b in antigo["blocks"]] == [b["text"] for b in pdf["blocks"]]


def test_hash_do_texto_serve_de_identidade_quando_o_arquivo_difere(claims_stj_reconferiveis, idx, pdf):
    c = copy.deepcopy(claims_stj_reconferiveis)
    c["claims"][0]["sources"][0]["content_hash"] = pdf["text_sha256"]
    assert validate.validar_claims(c, idx).erros == []
    c["claims"][0]["sources"][0]["content_hash"] = extract.extrair(PDF_ANTIGO)[0]["sha256"]
    assert [e["codigo"] for e in validate.validar_claims(c, idx).erros] == ["hash_diverge"]


def test_ementa_em_itens_inteiros_nas_duas_copias_do_pdf(pdf):
    itens = [b for b in pdf["blocks"] if b["section"] == "ementa" and re.match(r"^[1-6]\. ", b["text"])]
    assert [b["text"][0] for b in itens] == list("123456") * 2
    assert all(b["text"].rstrip().endswith(".") for b in itens)
    assert any(b["locator"] == "p.1-2" for b in itens)  # item 2 atravessa a quebra de página


def test_tese_falsa_nao_passa_como_apoiada(claims_stj_reconferiveis, idx):
    c = copy.deepcopy(claims_stj_reconferiveis)
    c["claims"][0]["sources"][0]["pinpoint"]["excerpt"] = "se submete ao prazo decenal do art. 205 do CC/2002"
    erros = validate.validar_claims(c, idx).erros
    assert [e["codigo"] for e in erros] == ["trecho_nao_encontrado"]


def test_citacao_inventada_permanece_unverified_e_nao_vira_inexistente(claims):
    c3 = next(c for c in claims["claims"] if c["id"] == "c003")
    assert c3["status"] == "unverified" and c3["existence"] == "nao_confirmada"
    pronto = copy.deepcopy(claims)
    next(c for c in pronto["claims"] if c["id"] == "c003").update(status="unsupported", reason="não existe")
    assert "existencia_incompativel" in [e["codigo"] for e in validate.validar_claims(pronto).erros]


def test_fonte_secundaria_nao_eleva_ao_estado_supported(claims, idx):
    c = copy.deepcopy(claims)
    c5 = next(x for x in c["claims"] if x["id"] == "c005")
    c5.update(status="supported", quote_status="conferida")
    cods = [e["codigo"] for e in validate.validar_claims(c, idx).erros]
    assert "teto_partial_sem_fonte_oficial" in cods


def test_artigo_do_cc_lido_na_versao_compilada_sem_trecho_tachado(idx):
    md = next(d for d in idx.values() if d["media_type"] == "text/markdown")
    alvo = [b for b in md["blocks"] if "pretensão de cobrança de dívidas líquidas constantes de instrumento" in b["text"]]
    assert alvo and "~~" not in alvo[0]["text"]
    assert any(b["text"] == "§ 5º Em cinco anos:" for b in md["blocks"])
