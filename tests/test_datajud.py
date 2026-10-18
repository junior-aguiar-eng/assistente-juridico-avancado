"""DataJud: mapeamento de índice, número inválido, falhas explícitas e resposta simulada (sem rede)."""
import io
import json
import os
import sys
import urllib.error
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import cnj  # noqa: E402
import datajud  # noqa: E402

VALIDO = "1000284-67.2021.8.26.0547"  # TJSP, DV conferido


@pytest.mark.parametrize("numero, indice", [(VALIDO, "tjsp")])
def test_indice_pelo_segmento_e_tribunal(numero, indice):
    assert datajud.alias(cnj.parse(numero)) == indice


def numero_com(j, tr):
    base = cnj._base("1000284", "2021", str(j), f"{tr:02d}", "0547")
    dv = cnj.calcular_dv("1000284", "2021", str(j), f"{tr:02d}", "0547")
    return cnj.parse(f"1000284-{dv}.2021.{j}.{tr:02d}.0547")


@pytest.mark.parametrize("j, tr, esperado", [(8, 1, "tjac"), (8, 7, "tjdft"), (8, 26, "tjsp"), (8, 27, "tjto"),
                                             (4, 3, "trf3"), (5, 15, "trt15"), (3, 0, "stj"), (8, 28, None), (6, 1, None)])
def test_tabela_de_indices(j, tr, esperado):
    assert datajud.alias(numero_com(j, tr)) == esperado


def test_numero_invalido_nao_chega_a_rede(monkeypatch):
    monkeypatch.setattr(datajud, "_post", lambda *a, **k: pytest.fail("não deveria consultar"))
    assert datajud.consultar("123")["status"] == "numero_invalido"
    assert datajud.consultar("1000284-00.2021.8.26.0547")["status"] == "numero_invalido"  # DV errado


def test_tribunal_nao_coberto_e_dito(monkeypatch):
    monkeypatch.setattr(datajud, "_post", lambda *a, **k: pytest.fail("não deveria consultar"))
    assert datajud.consultar(str(numero_com(6, 1).formatado), chave="x")["status"] == "tribunal_nao_coberto"


def test_resposta_encontrada_e_nao_encontrada(monkeypatch):
    chamadas = []

    def falso(url, chave, corpo, timeout=40):
        chamadas.append((url, chave, corpo))
        if len(chamadas) == 1:
            return 200, {"hits": {"hits": [{"_source": {"numeroProcesso": "10002846720218260547", "classe": {"nome": "Procedimento Comum"},
                                                         "tribunal": "TJSP", "movimentos": [{}, {}], "assuntos": [{"nome": "Contratos"}]}}]}}
        return 200, {"hits": {"hits": []}}

    monkeypatch.setattr(datajud, "_post", falso)
    r = datajud.consultar(VALIDO, chave="CHAVE")
    assert r["status"] == "encontrado" and r["resultados"][0]["movimentos"] == 2 and "não é inteiro teor" in r["aviso"]
    assert chamadas[0][0].endswith("/api_publica_tjsp/_search") and chamadas[0][1] == "CHAVE"
    assert chamadas[0][2]["query"]["match"]["numeroProcesso"] == "10002846720218260547"
    r2 = datajud.consultar(VALIDO, chave="CHAVE")
    assert r2["status"] == "nao_encontrado" and "não prova" in r2["aviso"]


def test_401_aponta_para_a_troca_de_chave(monkeypatch):
    def falso(*a, **k):
        raise urllib.error.HTTPError("u", 401, "Unauthorized", {}, io.BytesIO(b""))

    monkeypatch.setattr(datajud, "_post", falso)
    r = datajud.consultar(VALIDO, chave="velha")
    assert r["status"] == "erro_http" and r["http"] == 401 and "wiki" in r["motivo"]


def test_chave_vem_do_ambiente_antes_da_wiki(monkeypatch):
    monkeypatch.setenv("DATAJUD_API_KEY", " abc ")
    assert datajud.chave_publica() == "abc"


def test_chave_nunca_aparece_no_repositorio():
    for arq in list((RAIZ / "scripts").glob("*.py")) + list((RAIZ / "tests").glob("*.py")) + list((RAIZ / "docs").glob("*")):
        assert ("cDZHYzlZ" + "a0Jad") not in arq.read_text(encoding="utf-8", errors="ignore"), arq


@pytest.mark.skipif(not os.environ.get("JURIS_REDE"), reason="JURIS_REDE não definida")
def test_consulta_real_ao_tjsp():
    assert datajud.consultar(VALIDO)["status"] == "encontrado"
