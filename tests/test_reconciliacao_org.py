"""Controles da reconciliação: casos distintos e regras sem ativação."""
import json
import hashlib
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent


def ler(caminho):
    return json.loads((RAIZ / caminho).read_text(encoding="utf-8"))


def test_corpus_publico_nao_e_substituido_por_ids_privados_recuperados():
    casos = (ler("tests/casos/regressao/manifesto.json")["casos"]
             + ler("tests/casos/regressao/manifesto-privado-org.json")["casos"])
    assert len({c["id"] for c in casos}) == len(casos)
    por_id = {c["id"]: c for c in casos}
    assert por_id["R07"]["arquivo"].endswith("R07_tjmg_ai_176803.pdf")
    assert por_id["R07"]["esperado"]["paginas"] == 12
    assert por_id["R10"]["arquivo"].endswith("R10_picos_oficio_106_2022.pdf")
    assert por_id["R10"]["esperado"]["paginas"] == 1
    for ident, gabarito, paginas in [
        ("ORG-R07-PRIVADO", "tests/casos/pecas_contrato/ORG-R07-PRIVADO-fronteiras.json", 38),
        ("ORG-R10-PRIVADO", "tests/casos/ocr_qualidade/ORG-R10-PRIVADO-amostras.json", 2),
    ]:
        caso = por_id[ident]
        amostra = ler(gabarito)
        assert amostra["caso_id"] == ident
        assert caso["sha256"] == amostra["arquivo_sha256"]
        assert caso["esperado"]["paginas"] == amostra["total_paginas"] == paginas
        assert caso["situacao"] == "privado_local"
        assert ident in caso["arquivo_esperado"]
        publico = por_id[ident.removeprefix("ORG-").removesuffix("-PRIVADO")]
        assert caso["arquivo_esperado"] != publico["arquivo"]
        assert caso["sha256"] != hashlib.sha256((RAIZ / publico["arquivo"]).read_bytes()).hexdigest()


def test_regras_recuperadas_nao_ativam_pacotes_locais():
    regras = []
    for caminho in (RAIZ / "rules/br").glob("*.json"):
        regras.extend(json.loads(caminho.read_text(encoding="utf-8"))["regras"])
    assert len(regras) == 21  # 19 anteriores + 2 do pacote NDA (art. 195 da Lei 9.279/1996), todas inativas
    assert all(r["status"] == "inativa" for r in regras)
