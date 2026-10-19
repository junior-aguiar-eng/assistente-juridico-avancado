"""Vínculo obrigatório entre fontes lidas e documentos extraídos (CX-01)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import auditar  # noqa: E402
import extract  # noqa: E402
import validate  # noqa: E402


@pytest.fixture
def pacote(tmp_path):
    fonte = tmp_path / "fonte.txt"
    fonte.write_text("Art. 1. Texto da fonte oficial fornecida para conferência.", encoding="utf-8")
    doc, _ = extract.extrair(fonte)
    bloco = doc["blocks"][0]
    claims = {"schema_version": "1", "claims": [{
        "id": "c1", "central": True, "proposition": bloco["text"],
        "status": "supported", "existence": "confirmada", "quote_status": "conferida",
        "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida",
                     "local_file": str(fonte), "retrieved_at": "2026-10-17",
                     "content_hash": doc["sha256"], "text_scope": "texto_legal",
                     "document_id": doc["document_id"],
                     "pinpoint": {"locator": bloco["locator"], "excerpt": bloco["text"]}}],
    }]}
    return tmp_path, doc, claims


@pytest.mark.parametrize("com_extracao", [False, True])
@pytest.mark.parametrize("document_id", [None, "", "   ", 7, [], {}])
@pytest.mark.parametrize("origem", ["oficial", "secundaria"])
def test_fonte_lida_exige_document_id_textual(pacote, com_extracao, document_id, origem):
    _, doc, claims = pacote
    claims["claims"][0]["sources"][0]["origin"] = origem
    claims["claims"][0]["sources"][0]["document_id"] = document_id
    r = validate.validar_claims(claims, {doc["document_id"]: doc} if com_extracao else None)
    assert any(e["caminho"] == "$.claims[0].sources[0].document_id" for e in r.erros)


def test_omitir_id_nao_permite_aprovar_trecho_inventado(pacote):
    _, doc, claims = pacote
    fonte = claims["claims"][0]["sources"][0]
    del fonte["document_id"]
    fonte["pinpoint"] = {"locator": "p.999", "excerpt": "Trecho inventado que não existe no documento fornecido."}
    r = validate.validar_claims(claims, {doc["document_id"]: doc})
    assert r.erros


@pytest.mark.parametrize("indice", [{}, {"doc-outro": {}}])
def test_fonte_lida_nao_pode_apontar_documento_ausente(pacote, indice):
    _, _, claims = pacote
    r = validate.validar_claims(claims, indice)
    assert "documento_nao_extraido" in [e["codigo"] for e in r.erros]


def test_fonte_lida_valida_continua_aceita(pacote):
    _, doc, claims = pacote
    r = validate.validar_claims(claims, {doc["document_id"]: doc})
    assert r.erros == [] and r.avisos == []


@pytest.mark.parametrize("campo", ["excerpt", "content_hash"])
def test_id_valido_nao_dispensa_conferencia_de_trecho_e_hash(pacote, campo):
    _, doc, claims = pacote
    fonte = claims["claims"][0]["sources"][0]
    if campo == "excerpt":
        fonte["pinpoint"][campo] = "Outro texto que não consta no documento extraído."
    else:
        fonte[campo] = "0" * 64
    r = validate.validar_claims(claims, {doc["document_id"]: doc})
    assert ("trecho_nao_encontrado" if campo == "excerpt" else "hash_diverge") in [e["codigo"] for e in r.erros]


@pytest.mark.parametrize("acesso", ["nao_acessada", "source_missing"])
def test_fonte_nao_lida_nao_exige_document_id(acesso):
    claims = {"schema_version": "1", "claims": [{
        "id": "c1", "proposition": "Proposição aguardando leitura.", "status": "unverified",
        "existence": "nao_confirmada",
        "sources": [{"source_id": "s1", "origin": "oficial", "access": acesso}],
    }]}
    assert validate.validar_claims(claims, {}).erros == []


@pytest.mark.parametrize("modo", ["analise", "fundamentada"])
@pytest.mark.parametrize("falha", ["sem_id", "extracao_vazia", "documento_ausente"])
def test_auditoria_bloqueia_fonte_sem_vinculo(pacote, modo, falha):
    pasta, doc, claims = pacote
    if falha == "sem_id":
        del claims["claims"][0]["sources"][0]["document_id"]
    elif falha == "documento_ausente":
        claims["claims"][0]["sources"][0]["document_id"] = "doc-inexistente"
    cp, ep = pasta / "claims.json", pasta / "extracao.json"
    cp.write_text(json.dumps(claims), encoding="utf-8")
    ep.write_text(json.dumps({"documents": [] if falha == "extracao_vazia" else [doc]}), encoding="utf-8")
    qc = auditar.auditar(None, cp, [ep], modo=modo, base=pasta)
    assert qc["estado_tecnico"] == "bloqueado"
    gate = next(g for g in qc["gates"] if g["id"] == "G02_schema_claims")
    assert gate["resultado"] == "reprovado"


def test_auditoria_continua_aceitando_pacote_com_vinculo(pacote):
    pasta, doc, claims = pacote
    cp, ep = pasta / "claims.json", pasta / "extracao.json"
    cp.write_text(json.dumps(claims), encoding="utf-8")
    ep.write_text(json.dumps({"documents": [doc]}), encoding="utf-8")
    qc = auditar.auditar(None, cp, [ep], modo="fundamentada", base=pasta)
    assert qc["estado_tecnico"] == "revisao_pronta"


@pytest.mark.parametrize("document_id", [[], {}])
def test_auditoria_reprova_id_nao_textual_sem_excecao(pacote, document_id):
    pasta, doc, claims = pacote
    claims["claims"][0]["sources"][0]["document_id"] = document_id
    cp, ep = pasta / "claims.json", pasta / "extracao.json"
    cp.write_text(json.dumps(claims), encoding="utf-8")
    ep.write_text(json.dumps({"documents": [doc]}), encoding="utf-8")
    qc = auditar.auditar(None, cp, [ep], modo="fundamentada", base=pasta, reverificar=1)
    assert qc["estado_tecnico"] == "bloqueado"


@pytest.mark.parametrize("comando", ["validate", "auditar"])
def test_cli_mantem_pacote_historico_bloqueado(tmp_path, comando):
    raiz = Path(__file__).resolve().parent.parent
    caso = raiz / "tests" / "casos" / "verificacao_stj"
    args = [str(caso / "claims.json"), "--extracoes", str(caso / "extracao.json")]
    if comando == "auditar":
        args = ["auditar", "--claims", *args, "--tipo-entrega", "interna", "--saida", str(tmp_path / "qc.json")]
    r = subprocess.run([sys.executable, "-B", str(raiz / "scripts" / f"{comando}.py"), *args],
                       cwd=raiz, capture_output=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 1
    resultado = json.loads(r.stdout.decode("utf-8"))
    if comando == "validate":
        assert resultado["valido"] is False
        assert {e["caminho"] for e in resultado["erros"]} == {
            "$.claims[0].sources[1].document_id", "$.claims[4].sources[0].document_id"}
    else:
        assert resultado["estado_tecnico"] == "bloqueado"
        assert resultado["faixa"] == "nao_entregar"
