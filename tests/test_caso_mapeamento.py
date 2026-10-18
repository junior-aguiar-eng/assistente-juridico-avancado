"""Mapeamento de um caso real (acórdão do STJ AREsp 2.432.194/SP) em facts.json."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import validate  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
PDF = CASOS / "verificacao_stj" / "fontes" / "stj_inteiro_teor.pdf"
FACTS = CASOS / "mapeamento_stj" / "facts.json"


@pytest.fixture(scope="module")
def idx():
    d = extract.extrair(PDF)[0]
    return {d["document_id"]: d}


@pytest.fixture
def facts():
    return json.loads(FACTS.read_text(encoding="utf-8"))


def cods(lista):
    return [x["codigo"] for x in lista]


def test_facts_do_caso_validos_e_com_avisos_esperados(facts, idx):
    r = validate.validar_facts(facts, idx)
    assert r.erros == []
    # os três fatos materiais narrados na decisão transcrita foram registrados como alegação
    assert [a["caminho"] for a in r.avisos] == [f"$.facts[{i}].source.excerpt" for i in (3, 4, 5)]
    assert set(cods(r.avisos)) == {"trecho_em_citacao"}
    assert validate.resumo("facts", facts, r) == {"total": 8, "documentado": 2, "alegacao": 4, "inferencia": 1, "lacuna": 1, "informado": 0}


def test_fato_material_de_decisao_transcrita_nao_pode_passar_como_documentado(facts, idx):
    f = copy.deepcopy(facts)
    f["facts"][3]["kind"] = "documentado"
    del f["facts"][3]["alleged_by"]
    r = validate.validar_facts(f, idx)
    assert r.erros == []
    assert "documentado_em_citacao" in cods(r.avisos)
    avisos = cods(validate.validar_facts(f, idx).avisos)
    assert avisos.count("documentado_em_citacao") == 1 and avisos.count("trecho_em_citacao") == 2  # f004 trocou de aviso; f005 e f006 seguem como alegação


def test_atos_do_proprio_documento_sao_documentados_sem_aviso(facts, idx):
    so_atos = {"schema_version": "1", "facts": facts["facts"][:2]}
    r = validate.validar_facts(so_atos, idx)
    assert r.erros == [] and r.avisos == []


def test_datas_com_a_precisao_do_documento(facts):
    datas = {f["id"]: f["date"] for f in facts["facts"] if "date" in f}
    assert datas["f004"]["precision"] == "mes" and datas["f004"]["iso"] == "2013-11"
    assert datas["f006"] == {"original": "14 de maio de 2020", "iso": "2020-05-14", "precision": "dia"}
    f = copy.deepcopy(facts)
    f["facts"][3]["date"] = {"original": "novembro de 2013", "iso": "2013-11-01", "precision": "mes"}
    assert "data_incoerente" in cods(validate.validar_facts(f).erros)


def test_inferencia_depende_de_fatos_que_existem(facts):
    f = copy.deepcopy(facts)
    f["facts"] = [x for x in f["facts"] if x["id"] != "f005"]
    erros = validate.validar_facts(f).erros
    assert cods(erros) == ["referencia_inexistente"] and "f005" in erros[0]["mensagem"]


def test_trecho_alterado_ou_documento_trocado_e_recusado(facts, idx):
    f = copy.deepcopy(facts)
    f["facts"][4]["source"]["excerpt"] = "em 28 de novembro de 2018, o ora agravante firmou contrato"
    f["facts"][5]["source"]["document_id"] = "doc-000000000000"
    assert cods(validate.validar_facts(f, idx).erros) == ["trecho_nao_encontrado", "data_fora_do_trecho", "documento_nao_extraido"]


def test_inventario_mostra_todo_arquivo_inclusive_o_nao_lido(tmp_path):
    from pypdf import PdfWriter

    entrada = tmp_path / "input"
    entrada.mkdir()
    (entrada / "decisao.pdf").write_bytes(PDF.read_bytes())
    w = PdfWriter()
    w.add_blank_page(595, 842)
    with open(entrada / "escaneado.pdf", "wb") as fh:
        w.write(fh)
    (entrada / "nota.txt").write_text("Contrato assinado em 10/03/2023.\n\nValor: R$ 1.000,00.", encoding="utf-8")
    (entrada / "planilha.xls").write_bytes(b"PK\x03\x04")
    arquivos = sorted(str(p) for p in entrada.iterdir())
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "extract.py"), *arquivos, "--no-cache"],
                       capture_output=True, cwd=RAIZ)
    saida = json.loads(r.stdout.decode("utf-8"))
    por_nome = {Path(d["path"]).name: d for d in saida["documents"]}
    assert set(por_nome) == {"decisao.pdf", "escaneado.pdf", "nota.txt", "planilha.xls"}  # nenhum arquivo some
    assert {n: d["status"] for n, d in por_nome.items()} == {
        "decisao.pdf": "ok", "escaneado.pdf": "no_text", "nota.txt": "ok", "planilha.xls": "failed"}
    assert por_nome["planilha.xls"]["warnings"][0]["codigo"] == "extensao_nao_aceita"
    assert por_nome["escaneado.pdf"]["warnings"][0]["codigo"] == "pagina_sem_texto"
    assert r.returncode == 2  # há arquivo recusado


def test_lacuna_de_arquivo_nao_lido_e_valida_no_formato():
    f = {"schema_version": "1", "facts": [
        {"id": "f001", "kind": "lacuna", "text": "Documento escaneado.pdf não lido: sem camada de texto (OCR indisponível)."}]}
    assert validate.validar_facts(f).erros == []
