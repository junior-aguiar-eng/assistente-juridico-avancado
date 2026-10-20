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


@pytest.mark.parametrize("obj", [None, [], {}, {"error": "falha remota"}, {"hits": None},
                                 {"hits": {}}, {"hits": {"hits": None}}, {"hits": {"hits": {}}},
                                 {"hits": {"hits": [None]}}, {"hits": {"hits": [{"_source": None}]}},
                                 {"hits": {"hits": [{"_source": {}}]}},
                                 {"hits": {"hits": [{"_source": {"numeroProcesso": "outro"}}]}}])
def test_resposta_invalida_nao_vira_processo_ausente_ou_encontrado(monkeypatch, obj):
    monkeypatch.setattr(datajud, "_post", lambda *a, **k: (200, obj))
    res = datajud.consultar(VALIDO, chave="chave-sintetica")
    assert res["status"] == "erro_de_acesso"
    assert res["motivo"] and "resultados" not in res
    assert "chave-sintetica" not in json.dumps(res)


@pytest.mark.parametrize("sinal", [{"timed_out": True}, {"_shards": {"failed": 1}}])
@pytest.mark.parametrize("hits", [[], [{"_source": {"numeroProcesso": "10002846720218260547"}}]])
def test_busca_incompleta_nao_vira_resultado_conclusivo(monkeypatch, sinal, hits):
    obj = {"hits": {"hits": hits}, **sinal}
    monkeypatch.setattr(datajud, "_post", lambda *a, **k: (200, obj))
    res = datajud.consultar(VALIDO, chave="chave-sintetica")
    assert res["status"] == "erro_de_acesso" and "resultados" not in res


def test_busca_valida_vazia_nao_confunde_zero_com_falha(monkeypatch):
    obj = {"timed_out": False, "_shards": {"total": 1, "successful": 1, "failed": 0},
           "hits": {"total": {"value": 0, "relation": "eq"}, "hits": []}}
    monkeypatch.setattr(datajud, "_post", lambda *a, **k: (200, obj))
    res = datajud.consultar(VALIDO, chave="chave-sintetica")
    assert res["status"] == "nao_encontrado" and "não prova" in res["aviso"]


def test_cli_resposta_invalida_sai_com_erro_e_json(monkeypatch, capsys):
    monkeypatch.setattr(datajud, "chave_publica", lambda: "chave-sintetica")
    monkeypatch.setattr(datajud, "_post", lambda *a, **k: (200, {}))
    assert datajud.main(["consultar", VALIDO]) == 1
    obj = json.loads(capsys.readouterr().out)
    assert obj["status"] == "erro_de_acesso" and "resultados" not in obj


def test_chave_vem_do_ambiente_antes_da_wiki(monkeypatch):
    monkeypatch.setenv("DATAJUD_API_KEY", " abc ")
    assert datajud.chave_publica() == "abc"


@pytest.mark.parametrize("erro", [TimeoutError("The read operation timed out"),
                                 urllib.error.URLError("timed out")])
def test_timeout_de_transporte_e_falha_nunca_processo_ausente(monkeypatch, erro):
    def falhar(*a, **k):
        raise erro

    monkeypatch.setattr(datajud, "_post", falhar)
    res = datajud.consultar(VALIDO, chave="chave-sintetica")
    assert res["status"] == "erro_de_acesso"
    assert "timed out" in res["motivo"]
    assert "resultados" not in res
    assert "chave-sintetica" not in json.dumps(res)


def test_chave_nunca_aparece_no_repositorio():
    for arq in list((RAIZ / "scripts").glob("*.py")) + list((RAIZ / "tests").glob("*.py")) + list((RAIZ / "docs").glob("*")):
        assert ("cDZHYzlZ" + "a0Jad") not in arq.read_text(encoding="utf-8", errors="ignore"), arq


@pytest.mark.parametrize("valor", [None, "0", "", "false"])
def test_rede_desligada_nao_consulta_datajud(monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("JURIS_REDE", raising=False)
    else:
        monkeypatch.setenv("JURIS_REDE", valor)
    monkeypatch.setattr(datajud, "consultar", lambda *a, **k: pytest.fail("rede não autorizada"))
    with pytest.raises(pytest.skip.Exception):
        test_consulta_real_ao_tjsp()


def test_consulta_real_ao_tjsp():
    if os.environ.get("JURIS_REDE") != "1":
        pytest.skip("teste de rede: defina JURIS_REDE=1")
    res = datajud.consultar(VALIDO)
    assert res["status"] == "encontrado", res
