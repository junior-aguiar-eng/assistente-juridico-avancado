"""G04/G05/G10: fontes reconferíveis e relatório externo, sem dados de clientes."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import auditar  # noqa: E402
import extract  # noqa: E402

MATRIZ = [
    ("analise", "interna", "alerta"),
    ("fundamentada", "interna", "reprovado"),
    ("analise", "cliente", "reprovado"),
    ("analise", "peticao", "reprovado"),
    ("analise", "contrato", "reprovado"),
    ("fundamentada", "cliente", "reprovado"),
]


def escrever(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p


@pytest.fixture
def caso(tmp_path):
    fonte = tmp_path / "fonte.md"
    fonte.write_text("Fonte sintética de controle.  A obrigação descrita vence em dez dias.\n", encoding="utf-8")
    doc, _ = extract.extrair(fonte)
    assert doc["status"] == "ok" and doc["sha256"] != doc["text_sha256"]
    trecho = doc["blocks"][0]["text"]
    claims = {"schema_version": "1", "claims": [{
        "id": "c1", "tipo": "outro", "central": True, "proposition": trecho,
        "proposition_scope": "inteiro_teor", "status": "supported", "existence": "confirmada",
        "quote_status": "conferida", "applicability": "Controle sintético, sem aplicação jurídica.",
        "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida",
                     "url": "https://www.stj.jus.br/controle-sintetico", "local_file": str(fonte),
                     "retrieved_at": "2026-10-22", "content_hash": doc["sha256"],
                     "document_id": doc["document_id"], "text_scope": "inteiro_teor",
                     "pinpoint": {"locator": doc["blocks"][0]["locator"], "excerpt": trecho}}],
    }]}
    matter = {"schema_version": "1", "matter": {
        "matter_id": "controle", "objective": "Controle sintético dos gates", "client_role": "interessado",
        "jurisdiction": {"ramo": "civel", "tribunal": "STJ", "uf": "DF"}, "as_of": "2026-10-22",
        "confidentiality": {"nivel": "publico", "privilegio": "nao_aplicavel"},
        "conflicts": {"status": "nao_aplicavel", "motivo": "Teste sintético sem cliente"},
    }}
    rel = tmp_path / "relatorio.md"
    rel.write_text("# Controle sintético\n\n" + (RAIZ / "shared/aviso-padrao.md").read_text(encoding="utf-8"), encoding="utf-8")
    escrever(tmp_path / "matter.json", matter)
    return {"base": tmp_path, "fonte": fonte, "doc": doc, "claims": claims, "relatorio": rel}


def rodar(caso, modo="fundamentada", tipo="interna", relatorio=True, cli=False):
    p = caso["base"]
    cp = escrever(p / "claims.json", caso["claims"])
    ep = escrever(p / "extracao.json", {"documents": [caso["doc"]]})
    if cli:
        args = [sys.executable, "-P", str(RAIZ / "scripts/auditar.py"), "auditar", "--claims", str(cp),
                "--extracoes", str(ep), "--matter", str(p / "matter.json"), "--modo", modo,
                "--tipo-entrega", tipo, "--saida", str(p / "qc.json")]
        if relatorio:
            args += ["--relatorio", str(caso["relatorio"])]
        r = subprocess.run(args, cwd=p, capture_output=True, stdin=subprocess.DEVNULL)
        qc = json.loads(r.stdout.decode("utf-8"))
        assert r.returncode == (1 if qc["estado_tecnico"] == "bloqueado" else 0)
        assert json.loads((p / "qc.json").read_text(encoding="utf-8")) == qc
    else:
        qc = auditar.auditar(None, cp, [ep], modo=modo, base=p, matter=p / "matter.json",
                             tipo_entrega=tipo, relatorios=[caso["relatorio"]] if relatorio else [])
        escrever(p / "qc.json", qc)
    assert next(g for g in qc["gates"] if g["id"] == "G02_schema_claims")["resultado"] == "aprovado"
    return qc, {g["id"]: g["resultado"] for g in qc["gates"]}


@pytest.mark.parametrize("modo,tipo,esperado", MATRIZ)
@pytest.mark.parametrize("alvo", ["original", "fonte"])
def test_ausencia_bloqueia_fundamentada_ou_externa(caso, modo, tipo, esperado, alvo):
    ausente = str(caso["base"] / "ausente.md")
    if alvo == "original":
        caso["doc"]["path"] = ausente
        gate = "G04_originais_intactos"
    else:
        caso["claims"]["claims"][0]["sources"][0]["local_file"] = ausente
        gate = "G05_fontes_lidas_conferem"
    qc, gates = rodar(caso, modo, tipo)
    assert gates[gate] == esperado
    assert qc["estado_tecnico"] == ("bloqueado" if esperado == "reprovado" else "revisao_pronta")


@pytest.mark.parametrize("modo,tipo", [("analise", "interna"), ("fundamentada", "interna"), ("analise", "cliente")])
@pytest.mark.parametrize("campo_hash", ["sha256", "text_sha256"])
@pytest.mark.parametrize("integro", [True, False])
def test_hash_textual_exige_os_bytes_do_documento_extraido(caso, modo, tipo, campo_hash, integro):
    fonte = caso["claims"]["claims"][0]["sources"][0]
    fonte["content_hash"] = caso["doc"][campo_hash]
    copia = caso["base"] / "outra-fonte.md"
    copia.write_bytes(caso["fonte"].read_bytes() if integro else b"Documento sintetico diferente.")
    fonte["local_file"] = str(copia)
    qc, gates = rodar(caso, modo, tipo)
    assert gates["G04_originais_intactos"] == "aprovado"
    assert gates["G05_fontes_lidas_conferem"] == ("aprovado" if integro else "reprovado")
    assert qc["estado_tecnico"] == ("revisao_pronta" if integro else "bloqueado")


def test_arquivo_normalizado_nao_substitui_original_por_igualar_hash_textual(caso):
    normalizado = caso["base"] / "texto-normalizado.md"
    normalizado.write_text(" ".join(caso["fonte"].read_text(encoding="utf-8").split()), encoding="utf-8")
    assert hashlib.sha256(normalizado.read_bytes()).hexdigest() == caso["doc"]["text_sha256"]
    fonte = caso["claims"]["claims"][0]["sources"][0]
    fonte.update(local_file=str(normalizado), content_hash=caso["doc"]["text_sha256"])
    qc, gates = rodar(caso)
    assert gates["G04_originais_intactos"] == "aprovado"
    assert gates["G05_fontes_lidas_conferem"] == "reprovado" and qc["estado_tecnico"] == "bloqueado"


@pytest.mark.parametrize("modo,tipo,_", MATRIZ)
def test_relatorio_obrigatorio_para_entrega_externa(caso, modo, tipo, _):
    qc, gates = rodar(caso, modo, tipo, relatorio=False)
    assert gates["G10_aviso_no_relatorio"] == ("nao_aplicavel" if tipo == "interna" else "reprovado")
    assert qc["estado_tecnico"] == ("revisao_pronta" if tipo == "interna" else "bloqueado")


@pytest.mark.parametrize("falha,gate", [("original", "G04_originais_intactos"),
                                     ("fonte", "G05_fontes_lidas_conferem"),
                                     ("hash_textual", "G05_fontes_lidas_conferem"),
                                     ("relatorio", "G10_aviso_no_relatorio")])
def test_cli_bloqueia_e_status_nao_libera(caso, falha, gate):
    fonte = caso["claims"]["claims"][0]["sources"][0]
    if falha == "original":
        caso["doc"]["path"] = str(caso["base"] / "original-ausente.md")
    elif falha == "fonte":
        fonte["local_file"] = str(caso["base"] / "fonte-ausente.md")
    elif falha == "hash_textual":
        substituto = caso["base"] / "substituto.md"
        substituto.write_text("Texto sintético distinto.", encoding="utf-8")
        fonte.update(local_file=str(substituto), content_hash=caso["doc"]["text_sha256"])
    qc, gates = rodar(caso, tipo="cliente", relatorio=falha != "relatorio", cli=True)
    assert gates[gate] == "reprovado" and qc["estado_tecnico"] == "bloqueado"
    assert auditar.status(caso["base"] / "qc.json")["liberado_para_uso"] is False
    with pytest.raises(ValueError, match="bloqueado"):
        auditar.aprovar(caso["base"] / "qc.json", "Revisor fictício do teste", None, "Controle sintético.")


def test_fonte_perdida_depois_da_auditoria_invalida_status(caso):
    qc, _ = rodar(caso)
    assert qc["estado_tecnico"] == "revisao_pronta"
    # Retirar só o arquivo sintético do caminho auditado; o original permanece no temporário.
    caso["fonte"].rename(caso["base"] / "fonte-movida.md")
    st = auditar.status(caso["base"] / "qc.json")
    assert st["ausentes"] and st["liberado_para_uso"] is False
