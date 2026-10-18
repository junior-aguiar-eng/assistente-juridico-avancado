"""Corpus de acórdãos reais do STJ de órgãos diferentes, com gabarito objetivo: a ementa do conjunto de dados
abertos (fonte independente) tem de reaparecer na seção `ementa` extraída do PDF."""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402

PASTA = RAIZ / "tests" / "casos" / "stj_corpus"
GAB = json.loads((PASTA / "gabarito.json").read_text(encoding="utf-8"))


def palavras(s):
    s = unicodedata.normalize("NFKD", s).replace("�", "")
    return re.sub(r"[^A-Za-z0-9 ]", " ", s).lower().split()


def trigramas(w):
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


@pytest.fixture(scope="module")
def extracoes():
    return {c["numero_registro"]: extract.extrair(PASTA / c["arquivo"])[0] for c in GAB["casos"]}


@pytest.mark.parametrize("caso", GAB["casos"], ids=lambda c: f'{c["orgao"]}-{c["classe"]}')
def test_ementa_oficial_reaparece_na_secao_ementa(caso, extracoes):
    doc = extracoes[caso["numero_registro"]]
    ementa = trigramas(palavras(caso["ementa_oficial"]))
    extraido = trigramas(palavras(" ".join(b["text"] for b in doc["blocks"] if b["section"] == "ementa")))
    assert ementa and len(ementa & extraido) / len(ementa) >= 0.98


@pytest.mark.parametrize("caso", GAB["casos"], ids=lambda c: c["numero_registro"])
def test_estado_paginas_e_secoes_do_acordao(caso, extracoes):
    doc = extracoes[caso["numero_registro"]]
    assert hashlib.sha256((PASTA / caso["arquivo"]).read_bytes()).hexdigest() == caso["sha256"]
    assert doc["status"] == caso["esperado_da_extracao"]["status"] and doc["page_count"] == caso["esperado_da_extracao"]["paginas"]
    secoes = {b["section"] for b in doc["blocks"]}
    assert {"ementa", "acordao"} <= secoes and any(s in secoes for s in ("voto", "relatorio"))
    for b in doc["blocks"]:  # todo bloco tem localizador e página
        assert b["locator"] and b["page"]


def test_certidao_em_tabela_do_corte_especial_e_sinalizada_como_partial(extracoes):
    doc = extracoes["202300446420"]
    assert doc["status"] == "partial" and "layout_em_colunas_ou_tabela" in [a["codigo"] for a in doc["warnings"]]


def test_entrada_sem_inteiro_teor_esta_registrada_como_falha():
    reg = json.loads((PASTA / "registro.json").read_text(encoding="utf-8"))["fontes"]
    for s in GAB["sem_inteiro_teor"]:
        f = [x for x in reg if s["numero_registro"] in x["url"]]
        assert f and f[-1]["status"] == "source_missing" and "conteudo_inesperado" in f[-1]["motivo"]
