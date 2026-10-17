import json
import sys
from email.message import EmailMessage
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import validate  # noqa: E402


def gravar(tmp_path, msg, nome="m.eml"):
    p = tmp_path / nome
    p.write_bytes(msg.as_bytes())
    return p


def base_msg():
    m = EmailMessage()
    m["From"] = "Maria Souza <maria@exemplo.com.br>"
    m["To"] = "João Lima <joao@exemplo.com.br>"
    m["Date"] = "Mon, 10 Mar 2025 14:30:00 -0300"
    m["Subject"] = "Contrato de prestação de serviços: assinatura"
    return m


def test_email_texto_simples_cabecalho_corpo_e_citacao(tmp_path):
    m = base_msg()
    m.set_content("Prezado João,\n\nConfirmo a assinatura do contrato em 10/03/2025.\n\n> Em 09/03/2025, João escreveu:\n> Segue a minuta.\n")
    doc, _ = extract.extrair(gravar(tmp_path, m))
    assert doc["status"] == "ok" and doc["media_type"] == "message/rfc822"
    por = {b["locator"]: b for b in doc["blocks"]}
    assert por["email.cabecalho"]["text"].startswith("De: Maria Souza")
    assert "Assunto: Contrato de prestação de serviços: assinatura" in por["email.cabecalho"]["text"]
    assert por["email.corpo.par.2"]["text"].startswith("Confirmo a assinatura") and not por["email.corpo.par.2"]["is_quote"]
    assert por["email.corpo.par.3"]["is_quote"] and por["email.corpo.par.3"]["quote_basis"] == "marcador"
    assert doc["email"]["date_iso"] == "2025-03-10T14:30:00-03:00" and doc["email"]["anexos"] == []


def test_email_com_anexo_vira_partial_e_lista_os_nomes(tmp_path):
    m = base_msg()
    m.set_content("Segue o contrato assinado em anexo.")
    m.add_attachment(b"%PDF-1.4 conteudo", maintype="application", subtype="pdf", filename="contrato.pdf")
    doc, _ = extract.extrair(gravar(tmp_path, m))
    assert doc["status"] == "partial" and doc["email"]["anexos"] == ["contrato.pdf"]
    av = next(a for a in doc["warnings"] if a["codigo"] == "parte_nao_extraida")
    assert "contrato.pdf" in av["detalhe"]
    assert any(b["text"] == "Segue o contrato assinado em anexo." for b in doc["blocks"])


def test_email_so_html_extrai_texto_sem_scripts_e_avisa(tmp_path):
    m = base_msg()
    m.set_content("<html><body><script>roubar()</script><p>Valor: R$ 1.000,00</p><p>Prazo de 12 meses</p></body></html>",
                  subtype="html")
    doc, _ = extract.extrair(gravar(tmp_path, m))
    textos = " ".join(b["text"] for b in doc["blocks"])
    assert "R$ 1.000,00" in textos and "roubar" not in textos and "<p>" not in textos
    assert any(a["codigo"] == "corpo_html" for a in doc["warnings"])


def test_email_sem_corpo_e_data_ilegivel(tmp_path):
    bruto = (b"From: a@exemplo.com\r\nDate: ontem a tarde\r\nSubject: sem corpo\r\n"
             b"Content-Type: multipart/mixed; boundary=zz\r\n\r\n--zz--\r\n")
    p = tmp_path / "sem_corpo.eml"
    p.write_bytes(bruto)
    doc, _ = extract.extrair(p)
    codigos = {a["codigo"] for a in doc["warnings"]}
    assert codigos & {"sem_corpo", "corpo_vazio"} and doc["status"] == "partial"
    assert doc["email"]["date_iso"] is None and "data_do_cabecalho_ilegivel" in codigos


def test_email_charset_latin1_e_hash_do_texto_estavel(tmp_path):
    m = base_msg()
    m.set_content("Ação de cobrança: valor de R$ 500,00.", charset="iso-8859-1")
    doc, _ = extract.extrair(gravar(tmp_path, m))
    assert any("Ação de cobrança" in b["text"] for b in doc["blocks"])
    outro, _ = extract.extrair(gravar(tmp_path, m, "copia.eml"))
    assert outro["text_sha256"] == doc["text_sha256"] and outro["sha256"] == doc["sha256"]


def test_fato_pode_citar_o_email_pelo_localizador_de_paragrafo(tmp_path):
    m = base_msg()
    m.set_content("Prezado João,\n\nConfirmo a assinatura do contrato em 10/03/2025.")
    doc, _ = extract.extrair(gravar(tmp_path, m))
    idx = {doc["document_id"]: doc}
    f = {"schema_version": "1", "facts": [{"id": "f1", "kind": "alegacao", "alleged_by": "Maria Souza", "text": "Maria confirma a assinatura.",
         "date": {"original": "10/03/2025", "iso": "2025-03-10", "precision": "dia"},
         "source": {"document_id": doc["document_id"], "locator": "email.corpo.par.2", "excerpt": "assinatura do contrato em 10/03/2025"}}]}
    assert validate.validar_facts(f, idx).erros == []
    f["facts"][0]["source"]["locator"] = "email.corpo.par.1"
    assert [e["codigo"] for e in validate.validar_facts(f, idx).erros] == ["localizador_incoerente"]


def test_eml_aparece_como_extraivel_no_inventario(tmp_path):
    import triagem

    caso = tmp_path / "c"
    triagem.init(caso, "caso-1")
    m = base_msg()
    m.set_content("texto")
    (caso / "input" / "m.eml").write_bytes(m.as_bytes())
    assert triagem.inventario(caso)["nao_extraiveis"] == []
