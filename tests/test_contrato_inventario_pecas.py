"""Contrato ORG-01: esquema e exemplos artificiais; não testa classificação automática."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

RAIZ = Path(__file__).resolve().parent.parent
SCHEMA = RAIZ / "docs" / "contratos" / "pecas-v1.schema.json"
EXEMPLOS = RAIZ / "tests" / "casos" / "pecas_contrato" / "exemplos.json"


def carregar():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    exemplos = json.loads(EXEMPLOS.read_text(encoding="utf-8"))["exemplos"]
    return Draft202012Validator(schema, format_checker=FormatChecker()), exemplos


def test_esquema_e_draft_2020_12_valido():
    Draft202012Validator.check_schema(json.loads(SCHEMA.read_text(encoding="utf-8")))


@pytest.mark.parametrize("caso_id", ["CT01", "CT02", "CT03", "CT04", "CT05", "CT06", "CT07"])
def test_exemplos_anonimos_respeitam_contrato_e_conservam_texto(caso_id):
    validador, exemplos = carregar()
    caso = next(c for c in exemplos if c["id"] == caso_id)
    inv = caso["inventario"]
    validador.validate(inv)
    assert inv["origem"]["arquivo_sha256"] == hashlib.sha256(caso["origem_simulada_utf8"].encode()).hexdigest()
    assert inv["origem"]["extracao_sha256"] == hashlib.sha256(caso["extracao_json_utf8"].encode()).hexdigest()
    pacote = json.loads(caso["extracao_json_utf8"])
    ext = next(d for d in pacote["documents"] if d["document_id"] == inv["origem"]["document_id"])
    config = json.dumps(pacote["run"]["params"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert inv["origem"]["configuracao_sha256"] == hashlib.sha256(config.encode()).hexdigest()
    assert sorted(p["numero"] for p in inv["paginas"]) == list(range(1, inv["origem"]["total_paginas"] + 1))
    blocos = {b["id"]: b for b in ext["blocks"]}
    fragmentos = {f["id"]: f for f in inv["fragmentos"]}
    assert len(fragmentos) == len(inv["fragmentos"])
    pecas = {p["id"]: p for p in inv["pecas"]}
    assert len(pecas) == len(inv["pecas"])
    for bid, bloco in blocos.items():
        fs = sorted((f for f in fragmentos.values() if f["block_id"] == bid), key=lambda f: f["inicio"])
        assert fs and fs[0]["inicio"] == 0 and fs[-1]["fim"] == len(bloco["text"])
        assert all(a["fim"] == b["inicio"] for a, b in zip(fs, fs[1:]))
        assert "".join(bloco["text"][f["inicio"]:f["fim"]] for f in fs) == bloco["text"]
    for f in fragmentos.values():
        assert f["block_id"] in blocos
        assert 0 <= f["inicio"] < f["fim"] <= len(blocos[f["block_id"]]["text"])
        assert 1 <= f["paginas"]["inicio"] <= f["paginas"]["fim"] <= inv["origem"]["total_paginas"]
        if f["destino"]["classe"] == "peca":
            assert f["destino"]["piece_id"] in pecas
    for p in pecas.values():
        assert fragmentos[p["inicio"]]["destino"] == {"classe": "peca", "piece_id": p["id"]}
        assert fragmentos[p["fim"]]["destino"] == {"classe": "peca", "piece_id": p["id"]}
        assert p["limites"]["estado"] == p["tipo"]["estado"] == "proposto"
    for s in inv["secoes"]:
        assert s["piece_id"] in pecas
        assert all(fragmentos[f]["destino"] == {"classe": "peca", "piece_id": s["piece_id"]} for f in s["fragmentos"])


@pytest.mark.parametrize("mutacao", [
    "versao", "hash", "offset", "fim", "tipo", "conferencia", "evento_modelo", "revisao", "campo_extra",
    "instante_invalido", "instante_sem_fuso",
])
def test_esquema_recusa_estrutura_incompativel(mutacao):
    validador, exemplos = carregar()
    inv = copy.deepcopy(exemplos[0]["inventario"])
    if mutacao == "versao": inv["schema_version"] = "2"
    elif mutacao == "hash": inv["origem"]["arquivo_sha256"] = "a" * 32
    elif mutacao == "offset": inv["fragmentos"][0]["inicio"] = -1
    elif mutacao == "fim": inv["fragmentos"][0]["fim"] = 0
    elif mutacao == "tipo": inv["pecas"][0]["tipo_proposto"] = "tipo_inventado"
    elif mutacao == "conferencia": inv["pecas"][0]["limites"]["estado"] = "conferido"
    elif mutacao == "evento_modelo": inv["eventos"][0]["acao"] = "conferir_limites"
    elif mutacao == "revisao": inv["revisao"] = 0
    elif mutacao == "campo_extra": inv["aprovacao_juridica"] = True
    elif mutacao == "instante_invalido": inv["eventos"][0]["instante"] = "data-invalida"
    elif mutacao == "instante_sem_fuso": inv["eventos"][0]["instante"] = "2026-10-22T00:00:00"
    assert list(validador.iter_errors(inv)), mutacao


def test_gabarito_r07_tem_particao_fisica_confirmada_e_hash_do_manifesto():
    g = json.loads((EXEMPLOS.parent / "ORG-R07-PRIVADO-fronteiras.json").read_text(encoding="utf-8"))
    manifesto = json.loads((RAIZ / "tests/casos/regressao/manifesto-privado-org.json").read_text(encoding="utf-8"))
    caso = next(c for c in manifesto["casos"] if c["id"] == "ORG-R07-PRIVADO")
    assert g["arquivo_sha256"] == caso["sha256"]
    assert g["total_paginas"] == 38
    assert [(p["tipo"], p["pagina_inicio"], p["pagina_fim"]) for p in g["pecas"]] == [
        ("sentenca", 1, 24), ("acordao", 25, 38)]
    assert g["conferencia_paginas"]["estado"] == "conferido"
    assert g["conferencia_paginas"]["ator_tipo"] == "humano"
    assert g["ancora_tecnica"]["estado"] == "proposto"


def test_revisao_simulada_preserva_historico_da_peca_removida_e_invalida_conferencia():
    validador, _ = carregar()
    caso = json.loads(EXEMPLOS.read_text(encoding="utf-8"))["revisoes"][0]
    anterior = json.loads(caso["anterior_json_utf8"])
    atual = caso["inventario"]
    validador.validate(anterior)
    validador.validate(atual)
    assert atual["inventario_id"] == anterior["inventario_id"]
    assert atual["origem"] == anterior["origem"]
    assert atual["revisao"] == anterior["revisao"] + 1
    assert atual["anterior_sha256"] == hashlib.sha256(caso["anterior_json_utf8"].encode()).hexdigest()
    assert atual["eventos"][:len(anterior["eventos"])] == anterior["eventos"]
    removidos = {p["id"] for p in anterior["pecas"]} - {p["id"] for p in atual["pecas"]}
    assert removidos == {"p002"}
    assert atual["eventos"][-1]["acao"] == "corrigir"
    assert removidos <= set(atual["eventos"][-1]["alvos"])
    assert all(f["destino"]["piece_id"] == "p001" for f in atual["fragmentos"])
    assert atual["pecas"][0]["fim"] == "f002"
    for dimensao in ("limites", "tipo"):
        assert anterior["pecas"][0][dimensao]["estado"] == "conferido"
        assert atual["pecas"][0][dimensao] == {"estado": "proposto", "evento_id": None}
