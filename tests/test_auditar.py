"""Gate final: checagem técnica e aprovação humana ligada a hashes, nos casos reais do STJ."""
import copy
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import auditar  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
VERIF = CASOS / "verificacao_stj"
MAPA = CASOS / "mapeamento_stj"


def _cli(script, *args, cwd):
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / script), *map(str, args)],
                       capture_output=True, cwd=cwd, stdin=subprocess.DEVNULL)
    return r.returncode, json.loads(r.stdout.decode("utf-8"))


@pytest.fixture
def caso(tmp_path):
    """Cópia do caso com extração refeita por caminhos relativos, como em um caso de verdade."""
    pasta = tmp_path / "caso"
    shutil.copytree(VERIF / "fontes", pasta / "fontes")
    shutil.copy(VERIF / "claims.json", pasta / "claims.json")
    shutil.copy(MAPA / "facts.json", pasta / "facts.json")
    cod, _ = _cli("extract.py", "fontes/stj_inteiro_teor.pdf", "fontes/cc_compilado.md", "--no-cache",
                  "--saida", "extracao.json", cwd=pasta)
    assert cod == 0
    return pasta


def auditoria(pasta, modo="analise", **kw):
    return auditar.auditar(kw.get("facts", str(pasta / "facts.json")), kw.get("claims", str(pasta / "claims.json")),
                           [str(pasta / "extracao.json")], modo, base=pasta)


def res(qc):
    return {g["id"]: g["resultado"] for g in qc["gates"]}


# ------------------------------------------------------------------ checagem técnica
def test_caso_de_verificacao_fica_pronto_para_revisao_com_pendencias(monkeypatch):
    monkeypatch.chdir(RAIZ)
    qc = auditar.auditar(None, str(VERIF / "claims.json"), [str(VERIF / "extracao.json")], base=VERIF)
    assert qc["estado_tecnico"] == "revisao_pronta"
    assert res(qc) == {
        "G00_extracao_presente": "aprovado", "G01_schema_facts": "nao_aplicavel", "G02_schema_claims": "aprovado", "G03_cobertura_leitura": "aprovado",
        "G04_originais_intactos": "aprovado", "G05_fontes_lidas_conferem": "aprovado",
        "G06_teses_centrais": "aprovado", "G07_proposicoes_refutadas": "alerta", "G08_avisos_do_validador": "aprovado",
        "G10_aviso_no_relatorio": "nao_aplicavel", "G11_conflitos_de_interesse": "nao_aplicavel",
        "G12_sigilo_das_fontes": "nao_aplicavel"}
    assert {(p["item"], p["motivo"]) for p in qc["pendencias"]} == {
        ("c002", "estado unsupported"), ("c003", "estado unverified"), ("c005", "estado partial"),
        ("c002", "a fonte oficial lida contradiz a proposição: levar ao advogado antes de seguir")}
    assert qc["revisao_humana"] == {"estado": "pendente"}
    assert "não é aprovação" in qc["aviso"]


def test_caso_de_mapeamento_pronto_com_avisos_e_lacuna_pendente(monkeypatch):
    monkeypatch.chdir(RAIZ)
    qc = auditar.auditar(str(MAPA / "facts.json"), None, [str(VERIF / "extracao.json")], base=MAPA)
    assert qc["estado_tecnico"] == "revisao_pronta"
    assert res(qc)["G01_schema_facts"] == "aprovado" and res(qc)["G08_avisos_do_validador"] == "alerta"
    g08 = next(g for g in qc["gates"] if g["id"] == "G08_avisos_do_validador")
    assert g08["detalhe"] == "trecho_em_citacao x3"
    assert ("lacuna", "f008") in {(p["origem"], p["item"]) for p in qc["pendencias"]}


def test_artefatos_listam_pacote_e_fontes_com_hash(caso):
    qc = auditoria(caso)
    por_tipo = {}
    for a in qc["artefatos"]:
        por_tipo.setdefault(a["tipo"], []).append(a["caminho"])
        assert len(a["sha256"]) == 64
    assert por_tipo["facts"] == ["facts.json"] and por_tipo["claims"] == ["claims.json"]
    assert por_tipo["extracao"] == ["extracao.json"]
    assert sorted(por_tipo["fonte"]) == ["fontes/cc_compilado.md", "fontes/stj_inteiro_teor.pdf"]


def test_fonte_alterada_depois_da_leitura_bloqueia(caso):
    with open(caso / "fontes" / "stj_inteiro_teor.pdf", "ab") as f:
        f.write(b"\n")
    qc = auditoria(caso)
    assert qc["estado_tecnico"] == "bloqueado"
    assert res(qc)["G04_originais_intactos"] == "reprovado" and res(qc)["G05_fontes_lidas_conferem"] == "reprovado"


def test_tese_central_sem_apoio_so_bloqueia_na_entrega_fundamentada(caso):
    c = json.loads((caso / "claims.json").read_text(encoding="utf-8"))
    c1 = c["claims"][0]
    c1.update(status="partial", reason="só a ementa foi lida", missing="voto", quote_status="nao_conferida")
    (caso / "claims.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    analise = auditoria(caso, "analise")
    assert res(analise)["G06_teses_centrais"] == "alerta" and analise["estado_tecnico"] == "revisao_pronta"
    fund = auditoria(caso, "fundamentada")
    assert res(fund)["G06_teses_centrais"] == "reprovado" and fund["estado_tecnico"] == "bloqueado"


def test_pacote_invalido_bloqueia_com_o_motivo(caso):
    c = json.loads((caso / "claims.json").read_text(encoding="utf-8"))
    c["claims"][0]["sources"][0]["pinpoint"]["excerpt"] = "prazo decenal do art. 205"
    (caso / "claims.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    qc = auditoria(caso)
    g = next(g for g in qc["gates"] if g["id"] == "G02_schema_claims")
    assert g["resultado"] == "reprovado" and "trecho_nao_encontrado" in g["detalhe"]
    assert qc["estado_tecnico"] == "bloqueado"


def test_documento_nao_lido_exige_lacuna_que_o_nomeie(tmp_path):
    from pypdf import PdfWriter

    pasta = tmp_path / "c"
    pasta.mkdir()
    w = PdfWriter()
    w.add_blank_page(595, 842)
    with open(pasta / "escaneado.pdf", "wb") as fh:
        w.write(fh)
    (pasta / "nota.txt").write_text("Contrato assinado em 10/03/2023.", encoding="utf-8")
    _cli("extract.py", "escaneado.pdf", "nota.txt", "--no-cache", "--saida", "extracao.json", cwd=pasta)

    def facts(texto):
        return {"schema_version": "1", "facts": [{"id": "f001", "kind": "lacuna", "text": texto}]}

    (pasta / "facts.json").write_text(json.dumps(facts("Falta o contrato original."), ensure_ascii=False), encoding="utf-8")
    qc = auditar.auditar(str(pasta / "facts.json"), None, [str(pasta / "extracao.json")], base=pasta)
    g03 = next(g for g in qc["gates"] if g["id"] == "G03_cobertura_leitura")
    assert g03["resultado"] == "reprovado" and "escaneado.pdf" in g03["detalhe"] and qc["estado_tecnico"] == "bloqueado"
    (pasta / "facts.json").write_text(
        json.dumps(facts("Documento escaneado.pdf não lido: sem camada de texto."), ensure_ascii=False), encoding="utf-8")
    qc = auditar.auditar(str(pasta / "facts.json"), None, [str(pasta / "extracao.json")], base=pasta)
    g03b = next(g for g in qc["gates"] if g["id"] == "G03_cobertura_leitura")
    assert g03b["resultado"] == "alerta" and "document_id" in g03b["detalhe"]  # ligação só pelo nome é fraca
    assert qc["estado_tecnico"] == "revisao_pronta"
    did = json.loads((pasta / "extracao.json").read_text(encoding="utf-8"))["documents"][0]["document_id"]
    forte = facts("Não lido: sem camada de texto.")
    forte["facts"][0]["document_id"] = did
    (pasta / "facts.json").write_text(json.dumps(forte, ensure_ascii=False), encoding="utf-8")
    qc = auditar.auditar(str(pasta / "facts.json"), None, [str(pasta / "extracao.json")], base=pasta)
    assert next(g for g in qc["gates"] if g["id"] == "G03_cobertura_leitura")["resultado"] == "aprovado"


# ------------------------------------------------------------------ aprovação humana ligada a hashes
def _aprovar(pasta, qc, **kw):
    (pasta / "qc.json").write_text(json.dumps(qc, ensure_ascii=False), encoding="utf-8")
    base = dict(revisor="Dra. Maria Souza", registro="OAB/AL 0000", declaracao="Li o pacote e as fontes citadas.")
    base.update(kw)
    return auditar.aprovar(pasta / "qc.json", **base)


def test_aprovacao_vale_enquanto_nada_muda_e_cai_quando_algo_muda(caso):
    qc = auditoria(caso)
    ap = _aprovar(caso, qc)
    (caso / "aprovacao.json").write_text(json.dumps(ap), encoding="utf-8")
    assert ap["decisao"] == "aprovada" and ap["revisor"]["nome"] == "Dra. Maria Souza"
    st = auditar.status(caso / "qc.json", caso / "aprovacao.json")
    assert st["revisao_humana"] == "aprovada" and st["alterados"] == []
    # muda um byte do claims.json
    texto = (caso / "claims.json").read_bytes()  # bytes: a conversão de fim de linha mudaria o hash no Linux
    (caso / "claims.json").write_bytes(texto + b"\n")
    st = auditar.status(caso / "qc.json", caso / "aprovacao.json")
    assert st["revisao_humana"] == "invalidada" and st["alterados"] == ["claims.json"]
    (caso / "claims.json").write_bytes(texto)  # volta ao original
    assert auditar.status(caso / "qc.json", caso / "aprovacao.json")["revisao_humana"] == "aprovada"
    # muda a fonte lida
    with open(caso / "fontes" / "cc_compilado.md", "ab") as f:
        f.write(b"\n")
    st = auditar.status(caso / "qc.json", caso / "aprovacao.json")
    assert st["revisao_humana"] == "invalidada" and st["alterados"] == ["fontes/cc_compilado.md"]


def test_nova_auditoria_invalida_a_aprovacao_anterior(caso):
    ap = _aprovar(caso, auditoria(caso))
    (caso / "aprovacao.json").write_text(json.dumps(ap), encoding="utf-8")
    # uma nova auditoria com resultado diferente (outro modo) substitui o qc.json e derruba a aprovação anterior
    (caso / "qc.json").write_text(json.dumps(auditoria(caso, "fundamentada"), ensure_ascii=False), encoding="utf-8")
    st = auditar.status(caso / "qc.json", caso / "aprovacao.json")
    assert st["revisao_humana"] == "invalidada" and "qc.json" in st["alterados"]


def test_sem_aprovacao_o_estado_e_pendente(caso):
    (caso / "qc.json").write_text(json.dumps(auditoria(caso), ensure_ascii=False), encoding="utf-8")
    assert auditar.status(caso / "qc.json")["revisao_humana"] == "pendente"
    assert auditar.status(caso / "qc.json", caso / "nao_existe.json")["revisao_humana"] == "pendente"


def test_pacote_bloqueado_nao_pode_ser_aprovado(caso):
    with open(caso / "fontes" / "stj_inteiro_teor.pdf", "ab") as f:
        f.write(b"\n")
    qc = auditoria(caso)
    with pytest.raises(ValueError, match="bloqueado"):
        _aprovar(caso, qc)
    ap = _aprovar(caso, qc, decisao="reprovada", nota="fonte substituída")  # reprovar é sempre possível
    assert ap["decisao"] == "reprovada"


def test_nao_aprova_pacote_que_mudou_depois_da_auditoria(caso):
    qc = auditoria(caso)
    (caso / "facts.json").write_text((caso / "facts.json").read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="mudou desde a auditoria"):
        _aprovar(caso, qc)


@pytest.mark.parametrize("campo,valor", [("revisor", "  "), ("declaracao", "")])
def test_aprovacao_exige_pessoa_e_declaracao(caso, campo, valor):
    with pytest.raises(ValueError):
        _aprovar(caso, auditoria(caso), **{campo: valor})


# ------------------------------------------------------------------ CLI
def test_cli_fluxo_completo_e_codigos_de_saida(caso, monkeypatch):
    args = ["auditar", "--facts", "facts.json", "--claims", "claims.json", "--extracoes", "extracao.json",
            "--tipo-entrega", "interna", "--saida", "qc.json"]
    cod, qc = _cli("auditar.py", *args, cwd=caso)
    assert cod == 0 and qc["estado_tecnico"] == "revisao_pronta"
    # por processo sem terminal (como um agente ou script chamaria), a aprovação é recusada
    cod, ap = _cli("auditar.py", "aprovar", "qc.json", "--revisor", "Dr. João Lima", "--declaracao", "Revisei.",
                   "--saida", "aprovacao.json", cwd=caso)
    assert cod == 1 and "terminal interativo" in ap["erro"] and not (caso / "aprovacao.json").exists()
    # o revisor, em terminal interativo, digita a frase de confirmação
    frase = "APROVO " + auditar._sha(caso / "qc.json")[:8]
    _digitar(monkeypatch, frase + "\n")
    monkeypatch.chdir(caso)
    assert auditar.main(["aprovar", "qc.json", "--revisor", "Dr. João Lima", "--declaracao", "Revisei.",
                         "--saida", "aprovacao.json"]) == 0
    assert json.loads((caso / "aprovacao.json").read_text(encoding="utf-8"))["decisao"] == "aprovada"
    cod, st = _cli("auditar.py", "status", "qc.json", "aprovacao.json", cwd=caso)
    assert cod == 0 and st["revisao_humana"] == "aprovada"
    (caso / "facts.json").write_text((caso / "facts.json").read_text(encoding="utf-8") + " ", encoding="utf-8")
    cod, st = _cli("auditar.py", "status", "qc.json", "aprovacao.json", cwd=caso)
    assert cod == 1 and st["revisao_humana"] == "invalidada"
    cod, qc = _cli("auditar.py", "auditar", "--tipo-entrega", "interna", "--saida", "x.json", cwd=caso)
    assert cod == 1 and "informe --facts" in qc["erro"]
    with open(caso / "fontes" / "cc_compilado.md", "ab") as f:
        f.write(b"\n")
    cod, qc = _cli("auditar.py", *args, cwd=caso)
    assert cod == 1 and qc["estado_tecnico"] == "bloqueado"


# ------------------------------------------------------------------ correções da revisão crítica (C1, C2)
class _TTY(io.StringIO):
    """stdin que se declara terminal interativo, como o painel de terminal do revisor."""

    def isatty(self):
        return True


def _digitar(monkeypatch, texto):
    """Simula o revisor digitando em um console interativo (o stdin real nunca é console nos testes)."""
    monkeypatch.setattr(sys, "stdin", _TTY(texto))
    monkeypatch.setattr(auditar, "_stdin_e_console", lambda: True)


def test_sem_extracao_nada_e_conferido_e_a_entrega_fundamentada_bloqueia(caso):
    analise = auditar.auditar(None, str(caso / "claims.json"), [], "analise", base=caso)
    assert res(analise)["G00_extracao_presente"] == "alerta" and analise["estado_tecnico"] == "revisao_pronta"
    fund = auditar.auditar(None, str(caso / "claims.json"), [], "fundamentada", base=caso)
    assert res(fund)["G00_extracao_presente"] == "reprovado" and fund["estado_tecnico"] == "bloqueado"
    g00 = next(g for g in fund["gates"] if g["id"] == "G00_extracao_presente")
    assert "nenhum trecho" in g00["detalhe"]


def test_fonte_oficial_sem_local_file_nao_e_reconferivel(caso):
    c = json.loads((caso / "claims.json").read_text(encoding="utf-8"))
    for cl in c["claims"]:
        for s in cl["sources"]:
            s.pop("local_file", None)
    (caso / "claims.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    analise = auditoria(caso, "analise", facts=None)
    g05 = next(g for g in analise["gates"] if g["id"] == "G05_fontes_lidas_conferem")
    assert g05["resultado"] == "alerta" and "c001" in g05["detalhe"] and "c004" in g05["detalhe"]
    assert ("fonte_nao_reconferivel", "c001") in {(p["origem"], p["item"]) for p in analise["pendencias"]}
    assert analise["estado_tecnico"] == "revisao_pronta"
    fund = auditoria(caso, "fundamentada", facts=None)
    assert res(fund)["G05_fontes_lidas_conferem"] == "reprovado" and fund["estado_tecnico"] == "bloqueado"


def _args_aprovar(caso, decisao="aprovada"):
    return ["aprovar", str(caso / "qc.json"), "--revisor", "Dra. Maria Souza", "--registro", "OAB/AL 0000",
            "--declaracao", "Li o pacote.", "--decisao", decisao, "--saida", str(caso / "ap.json")]


def test_aprovacao_so_com_a_frase_digitada_pelo_revisor_em_terminal(caso, monkeypatch):
    (caso / "qc.json").write_text(json.dumps(auditoria(caso), ensure_ascii=False), encoding="utf-8")
    frase = "APROVO " + auditar._sha(caso / "qc.json")[:8]
    _digitar(monkeypatch, "aprovo\n")  # frase errada
    assert auditar.main(_args_aprovar(caso)) == 1 and not (caso / "ap.json").exists()
    _digitar(monkeypatch, "")  # nada digitado
    assert auditar.main(_args_aprovar(caso)) == 1 and not (caso / "ap.json").exists()
    _digitar(monkeypatch, frase + "\n")
    assert auditar.main(_args_aprovar(caso)) == 0
    ap = json.loads((caso / "ap.json").read_text(encoding="utf-8"))
    assert ap["decisao"] == "aprovada" and ap["revisor"] == {"nome": "Dra. Maria Souza", "registro": "OAB/AL 0000"}


def test_reprovar_tambem_exige_terminal_e_a_frase_propria(caso, monkeypatch):
    (caso / "qc.json").write_text(json.dumps(auditoria(caso), ensure_ascii=False), encoding="utf-8")
    sha8 = auditar._sha(caso / "qc.json")[:8]
    _digitar(monkeypatch, f"APROVO {sha8}\n")  # a frase de aprovar não vale para reprovar
    assert auditar.main(_args_aprovar(caso, "reprovada")) == 1
    _digitar(monkeypatch, f"REPROVO {sha8}\n")
    assert auditar.main(_args_aprovar(caso, "reprovada")) == 0
    assert json.loads((caso / "ap.json").read_text(encoding="utf-8"))["decisao"] == "reprovada"


def test_sem_terminal_a_aprovacao_e_recusada_mesmo_com_a_frase(caso):
    (caso / "qc.json").write_text(json.dumps(auditoria(caso), ensure_ascii=False), encoding="utf-8")
    cod, out = _cli("auditar.py", *_args_aprovar(caso), cwd=caso)
    assert cod == 1 and "terminal interativo" in out["erro"] and not (caso / "ap.json").exists()


def test_confirmacao_nao_registra_pacote_bloqueado_nem_alterado(caso, monkeypatch):
    with open(caso / "fontes" / "stj_inteiro_teor.pdf", "ab") as f:
        f.write(b"\n")
    (caso / "qc.json").write_text(json.dumps(auditoria(caso), ensure_ascii=False), encoding="utf-8")
    frase = "APROVO " + auditar._sha(caso / "qc.json")[:8]
    _digitar(monkeypatch, frase + "\n")
    assert auditar.main(_args_aprovar(caso)) == 1 and not (caso / "ap.json").exists()  # bloqueado


# ------------------------------------------------------------------ cronologia atualizada (Fase 3)
def test_cronologia_desatualizada_bloqueia_a_entrega(caso):
    import cronologia

    cronologia.gerar(caso / "facts.json", caso / "timeline.json", caso / "cronologia.md", extracoes=[caso / "extracao.json"])
    qc = auditar.auditar(str(caso / "facts.json"), None, [str(caso / "extracao.json")], base=caso,
                         timeline=str(caso / "timeline.json"))
    assert res(qc)["G09_cronologia_atualizada"] == "aprovado" and qc["estado_tecnico"] == "revisao_pronta"
    assert any(a["tipo"] == "timeline" for a in qc["artefatos"])
    f = json.loads((caso / "facts.json").read_text(encoding="utf-8"))
    f["facts"].append({"id": "f099", "kind": "lacuna", "text": "Falta o contrato original."})
    (caso / "facts.json").write_text(json.dumps(f, ensure_ascii=False), encoding="utf-8")
    qc = auditar.auditar(str(caso / "facts.json"), None, [str(caso / "extracao.json")], base=caso,
                         timeline=str(caso / "timeline.json"))
    assert res(qc)["G09_cronologia_atualizada"] == "reprovado" and qc["estado_tecnico"] == "bloqueado"
    qc = auditar.auditar(None, str(caso / "claims.json"), [str(caso / "extracao.json")], base=caso,
                         timeline=str(caso / "timeline.json"))
    assert res(qc)["G09_cronologia_atualizada"] == "reprovado"  # cronologia sem facts.json


def test_status_sem_aprovacao_tambem_detecta_artefato_alterado(tmp_path):
    caso = tmp_path / "c"
    shutil.copytree(RAIZ / "tests" / "casos" / "verificacao_stj", caso)
    qc = auditar.auditar(None, str(caso / "claims.json"), [str(caso / "extracao.json")], base=caso)
    (caso / "qc.json").write_text(json.dumps(qc), encoding="utf-8")
    assert auditar.status(caso / "qc.json")["alterados"] == []
    (caso / "claims.json").write_bytes((caso / "claims.json").read_bytes() + b" ")
    st = auditar.status(caso / "qc.json")
    assert st["alterados"] == ["claims.json"] and st["liberado_para_uso"] is False


def test_cli_exige_tipo_de_entrega(tmp_path):
    with pytest.raises(SystemExit):
        auditar.main(["auditar", "--claims", "c.json", "--saida", "x.json"])
