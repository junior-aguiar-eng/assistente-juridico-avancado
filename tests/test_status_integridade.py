"""CX-02: integridade e decisão humana prevalecem sobre a dispensa de aprovação."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import auditar  # noqa: E402


def gravar(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


@pytest.fixture(params=[False, True], ids=["interna_dispensa", "aprovacao_obrigatoria"])
def pacote(tmp_path, request):
    """QC mínimo com artefato real; mudanças posteriores não recalculam seu hash."""
    artefato = tmp_path / "entrega.txt"
    artefato.write_text("Conteúdo conferido na auditoria.", encoding="utf-8")
    qc = {"schema_version": "1", "estado_tecnico": "revisao_pronta",
          "faixa": "mista" if request.param else "alta",
          "tipo_entrega": "cliente" if request.param else "interna",
          "aprovacao_humana_obrigatoria": request.param,
          "artefatos": [{"caminho": "entrega.txt", "tipo": "entrega",
                         "sha256": hashlib.sha256(artefato.read_bytes()).hexdigest()}]}
    qcp, ap = tmp_path / "qc.json", tmp_path / "aprovacao.json"
    gravar(qcp, qc)
    return qcp, ap, artefato, qc


def registrar_decisao(pacote, decisao="aprovada"):
    qcp, ap, _, _ = pacote
    # Exercita o gerador real do registro, sem simular console ou aprovação de usuário.
    registro = auditar.aprovar(qcp, "Revisor de teste", "Registro sintético", "Fixture de regressão.",
                              decisao=decisao)
    gravar(ap, registro)


@pytest.mark.parametrize("arquivo_indicado", [False, True])
def test_sem_decisao_so_libera_pacote_integro_quando_aprovacao_dispensada(pacote, arquivo_indicado):
    qcp, ap, _, qc = pacote
    st = auditar.status(qcp, ap if arquivo_indicado else None)
    assert st["revisao_humana"] == "pendente"
    assert st["liberado_para_uso"] is (not qc["aprovacao_humana_obrigatoria"])
    assert st["alterados"] == [] and st["ausentes"] == []


@pytest.mark.parametrize("mudanca,campo", [("alterar", "alterados"), ("remover", "ausentes")])
def test_artefato_alterado_ou_ausente_bloqueia_sem_aprovacao(pacote, mudanca, campo):
    qcp, _, artefato, _ = pacote
    if mudanca == "alterar":
        artefato.write_text("Conteúdo substituído.", encoding="utf-8")
    else:
        artefato.unlink()
    st = auditar.status(qcp)
    assert st["liberado_para_uso"] is False
    assert st[campo] == ["entrega.txt"]


def test_revisao_reprovada_impede_liberacao_mesmo_quando_aprovacao_dispensada(pacote):
    registrar_decisao(pacote, "reprovada")
    st = auditar.status(pacote[0], pacote[1])
    assert st["revisao_humana"] == "reprovada"
    assert st["liberado_para_uso"] is False


def test_aprovacao_valida_de_pacote_integro_continua_liberando(pacote):
    registrar_decisao(pacote)
    st = auditar.status(pacote[0], pacote[1])
    assert st["revisao_humana"] == "aprovada"
    assert st["liberado_para_uso"] is True
    assert st["alterados"] == [] and st["ausentes"] == []


@pytest.mark.parametrize("mudanca,campo,esperado", [
    ("qc", "alterados", ["qc.json"]),
    ("artefato", "alterados", ["entrega.txt"]),
    ("ausente", "ausentes", ["entrega.txt"]),
])
def test_aprovacao_invalidada_nunca_libera_pacote(pacote, mudanca, campo, esperado):
    qcp, ap, artefato, qc = pacote
    registrar_decisao(pacote)
    if mudanca == "qc":
        qc["modo"] = "fundamentada"
        gravar(qcp, qc)
    elif mudanca == "artefato":
        artefato.write_text("Conteúdo substituído.", encoding="utf-8")
    else:
        artefato.unlink()
    st = auditar.status(qcp, ap)
    assert st["revisao_humana"] == "invalidada"
    assert st["liberado_para_uso"] is False
    assert st[campo] == esperado


@pytest.mark.parametrize("mudanca,campo", [("alterar", "alterados"), ("remover", "ausentes")])
def test_diagnostico_preserva_artefato_do_qc_ausente_na_aprovacao_antiga(pacote, mudanca, campo):
    qcp, ap, _, qc = pacote
    registrar_decisao(pacote)
    extra = qcp.parent / "anexo.txt"
    extra.write_text("Anexo incluído na auditoria nova.", encoding="utf-8")
    qc["artefatos"].append({"caminho": "anexo.txt", "tipo": "entrega",
                            "sha256": hashlib.sha256(extra.read_bytes()).hexdigest()})
    gravar(qcp, qc)
    if mudanca == "alterar":
        extra.write_text("Anexo alterado depois da auditoria nova.", encoding="utf-8")
    else:
        extra.unlink()
    st = auditar.status(qcp, ap)
    assert st["revisao_humana"] == "invalidada"
    assert st["liberado_para_uso"] is False
    assert "anexo.txt" in st[campo]
    assert "qc.json" in st["alterados"]


def test_estado_tecnico_bloqueado_nao_libera_pacote_sem_decisao(pacote):
    qcp, _, _, qc = pacote
    qc["estado_tecnico"] = "bloqueado"
    gravar(qcp, qc)
    assert auditar.status(qcp)["liberado_para_uso"] is False


@pytest.mark.parametrize("mudanca,revisao", [("reprovar", "reprovada"), ("qc", "invalidada")])
def test_cli_nao_libera_pacote_reprovado_ou_com_aprovacao_invalidada(pacote, mudanca, revisao):
    qcp, ap, _, qc = pacote
    registrar_decisao(pacote, "reprovada" if mudanca == "reprovar" else "aprovada")
    if mudanca == "qc":
        qc["modo"] = "fundamentada"
        gravar(qcp, qc)
    r = subprocess.run([sys.executable, "-B", str(RAIZ / "scripts" / "auditar.py"), "status", str(qcp), str(ap)],
                       capture_output=True, stdin=subprocess.DEVNULL, cwd=qcp.parent)
    assert r.returncode == 1
    st = json.loads(r.stdout.decode("utf-8"))
    assert st["revisao_humana"] == revisao
    assert st["liberado_para_uso"] is False
