"""Saídas da pesquisa jurídica: claims iniciais (sempre unverified), plano por política do caso e vigência."""
import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import fontes  # noqa: E402
import validate  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
INICIAL = CASOS / "pesquisa_stj" / "claims_inicial.json"
MATTER = json.loads((CASOS / "triagem_stj" / "matter.json").read_text(encoding="utf-8"))


def cods(lista):
    return [x["codigo"] for x in lista]


def test_claims_iniciais_da_pesquisa_validam_e_nenhum_passa_de_unverified():
    obj = json.loads(INICIAL.read_text(encoding="utf-8"))
    r = validate.validar_claims(obj)
    assert r.erros == []
    assert {c["status"] for c in obj["claims"]} == {"unverified"}
    assert cods(r.avisos) == ["tese_central_nao_verificada", "tese_central_nao_verificada"]
    assert validate.resumo("claims", obj, r)["centrais_pendentes"] == ["c001", "c002"]


def test_pesquisa_nao_pode_marcar_fonte_lida_e_deixar_unverified():
    obj = json.loads(INICIAL.read_text(encoding="utf-8"))
    obj["claims"][0]["sources"] = [{
        "source_id": "s1", "origin": "oficial", "access": "lida", "url": "https://www.planalto.gov.br/x",
        "retrieved_at": "2026-10-17", "content_hash": "a" * 64, "text_scope": "texto_legal",
        "pinpoint": {"locator": "art. 206", "excerpt": "texto"}}]
    assert "unverified_com_fonte_lida" in cods(validate.validar_claims(obj).erros)  # leitura é de br-verificar-citacoes


def test_busca_vazia_nao_vira_inexistencia():
    obj = json.loads(INICIAL.read_text(encoding="utf-8"))
    c4 = next(c for c in obj["claims"] if c["id"] == "c004")
    assert c4["existence"] == "nao_confirmada"
    c4["status"], c4["reason"] = "unsupported", "não existe"
    assert "existencia_incompativel" in cods(validate.validar_claims(obj).erros)
    c4["status"], c4["existence"] = "unverified", "inexistente"
    assert "valor_invalido" in cods(validate.validar_claims(obj).erros)


def test_tema_do_stf_fica_sem_arquivo_e_o_plano_diz_que_a_ponte_e_manual():
    plano = fontes.plano("tema", MATTER)
    por_id = {p["id"]: p for p in plano["pontes"]}
    assert por_id["stf_navegador"]["estado"] == "disponivel" and "Manual" in por_id["stf_navegador"]["limites"]
    assert "PDF do inteiro teor não chegou ao disco" in por_id["stf_navegador"]["limites"]
    obj = json.loads(INICIAL.read_text(encoding="utf-8"))
    c3 = next(c for c in obj["claims"] if c["id"] == "c003")
    assert c3["sources"][0]["access"] != "lida" and "teto" in c3["sources"][0]["error"]


def test_vigencia_a_epoca_dos_fatos_usa_a_data_do_matter_e_o_art_206_do_caso_real():
    fatos = MATTER["matter"]["facts_date"]
    r = fontes.anotacoes(CASOS / "verificacao_stj" / "fontes" / "cc_compilado.md", "206", "5", "I", fatos)
    assert r["anotacoes"] == [] and r["data_fatos"] == "2013-11"
    assert r["legal_time_sugerido"]["vigencia"] == "nao_verificada"  # sem anotação não prova a redação à época
    obj = {"schema_version": "1", "claims": [{
        "id": "c1", "tipo": "norma", "proposition": "p", "status": "supported", "existence": "confirmada",
        "quote_status": "conferida",
        "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida", "url": "https://www.planalto.gov.br/x",
                     "retrieved_at": "2026-10-17", "content_hash": "b" * 64, "text_scope": "texto_legal",
                     "pinpoint": {"locator": "art. 206", "excerpt": "texto"},
                     "legal_time": {"as_of": "2026-10-17", "vigencia": r["legal_time_sugerido"]["vigencia"]}}]}]}
    resultado = validate.validar_claims(obj)
    assert resultado.erros == [] and resultado.avisos == []  # legal_time registrado como não verificada
    sem = copy.deepcopy(obj)
    del sem["claims"][0]["sources"][0]["legal_time"]
    assert cods(validate.validar_claims(sem).avisos) == ["vigencia_nao_verificada"]
