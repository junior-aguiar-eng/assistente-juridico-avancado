import copy
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import triagem  # noqa: E402
import validate  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
MATTER = CASOS / "triagem_stj" / "matter.json"
PDF = CASOS / "verificacao_stj" / "fontes" / "stj_inteiro_teor.pdf"


@pytest.fixture
def matter():
    return json.loads(MATTER.read_text(encoding="utf-8"))


def cods(lista):
    return [x["codigo"] for x in lista]


def liberar(pasta):
    for p in Path(pasta).rglob("*"):
        if p.is_file():
            os.chmod(p, stat.S_IWRITE | stat.S_IREAD)


# ------------------------------------------------------------------ matter.json
def test_matter_do_caso_real_valido_e_so_com_o_aviso_esperado(matter):
    tipo, r = validate.validar(matter)
    assert tipo == "matter" and r.erros == [] and r.avisos == []
    assert validate.resumo("matter", matter, r) == {"matter_id": "aresp-2432194", "ramo": "empresarial",
                                                    "nivel": "publico", "processos": 2}


def test_modelo_gerado_pelo_init_nao_valida_ate_a_triagem_ser_feita():
    r = validate.validar_matter(triagem.modelo_matter("caso-1"))
    caminhos = {e["caminho"] for e in r.erros}
    assert {"$.matter.objective", "$.matter.client_role", "$.matter.jurisdiction.ramo", "$.matter.as_of",
            "$.matter.confidentiality.nivel"} <= caminhos
    assert "$.matter.confidentiality.consultas_externas" not in caminhos  # opcional: o padrão é 'permitidas'


@pytest.mark.parametrize("mudanca,codigo", [
    (lambda m: m.update(matter_id="caso 1!"), "id_invalido"),
    (lambda m: m.update(objective="  "), "tipo_invalido"),
    (lambda m: m.update(client_role="advogado"), "valor_invalido"),
    (lambda m: m.update(as_of="17/10/2026"), "data_invalida"),
    (lambda m: m.update(as_of="2999-01-01"), "data_futura"),
    (lambda m: m.update(facts_date="2027-01"), "data_incoerente"),
    (lambda m: m.update(facts_date="2013-13-40"), "data_invalida"),
    (lambda m: m["jurisdiction"].update(uf="sp"), "valor_invalido"),
    (lambda m: m["jurisdiction"].update(ramo="penal"), "valor_invalido"),
    (lambda m: m["confidentiality"].update(consultas_externas="talvez"), "valor_invalido"),
    (lambda m: m.update(capabilities={"ocr": "sim"}), "tipo_invalido"),
    (lambda m: m.update(documentos=[1]), "tipo_invalido"),
])
def test_matter_campos_invalidos(matter, mudanca, codigo):
    m = copy.deepcopy(matter)
    mudanca(m["matter"])
    assert codigo in cods(validate.validar_matter(m).erros)


def test_numero_de_processo_com_digito_errado_e_recusado(matter):
    m = copy.deepcopy(matter)
    m["matter"]["processos"] = [{"numero": "1000284-68.2021.8.26.0547"}, "texto qualquer"]
    erros = validate.validar_matter(m).erros
    assert cods(erros) == ["cnj_invalido", "cnj_invalido"]
    assert "dígito verificador" in erros[0]["mensagem"]


def test_sigilo_exige_politica_para_o_modelo_e_avisa_sobre_consultas_externas(matter):
    m = copy.deepcopy(matter)
    m["matter"]["confidentiality"] = {"nivel": "sigiloso", "consultas_externas": "permitidas", "privilegio": "triado"}
    r = validate.validar_matter(m)
    assert r.erros == [] and cods(r.avisos) == ["politica_modelo_nao_registrada", "sigilo_com_consultas_externas"]
    m["matter"]["confidentiality"] = {"nivel": "sigiloso", "consultas_externas": "proibidas",
                                      "politica_modelo": "nenhum trecho sai da máquina", "privilegio": "triado"}
    r = validate.validar_matter(m)
    assert r.erros == [] and r.avisos == []


def test_papel_e_jurisdicao_nao_informados_sao_aviso_e_nao_erro(matter):
    m = copy.deepcopy(matter)
    m["matter"]["client_role"] = "nao_informado"
    m["matter"]["jurisdiction"] = {"ramo": "nao_informado"}
    r = validate.validar_matter(m)
    assert r.erros == [] and cods(r.avisos) == ["papel_nao_informado", "jurisdicao_nao_informada"]


def test_arquivo_com_matter_e_facts_e_recusado(matter):
    matter["facts"] = []
    assert cods(validate.validar(matter)[1].erros) == ["estrutura"]


# ------------------------------------------------------------------ init e inventário
def test_init_cria_pastas_e_nao_sobrescreve_matter(tmp_path):
    caso = tmp_path / "c"
    res = triagem.init(caso, "caso-1")
    assert set(res["pastas_criadas"]) == {"input", "derived", "outputs", "runs"}
    assert all((caso / p).is_dir() for p in triagem.PASTAS)
    assert res["matter_json"].startswith("criado")
    (caso / "matter.json").write_text("{}", encoding="utf-8")
    again = triagem.init(caso, "caso-1")
    assert again["pastas_criadas"] == [] and again["matter_json"] == "mantido"
    assert (caso / "matter.json").read_text(encoding="utf-8") == "{}"


def test_inventario_hashes_nao_extraiveis_e_mudancas(tmp_path):
    caso = tmp_path / "c"
    triagem.init(caso, "caso-1")
    (caso / "input" / "peticao.txt").write_text("texto", encoding="utf-8")
    (caso / "input" / "planilha.xls").write_bytes(b"PK")
    sub = caso / "input" / "anexos"
    sub.mkdir()
    (sub / "a.txt").write_text("anexo", encoding="utf-8")
    inv = triagem.inventario(caso)
    assert set(inv["arquivos"]) == {"peticao.txt", "planilha.xls", "anexos/a.txt"}
    assert inv["nao_extraiveis"] == ["planilha.xls"] and inv["mudancas_desde_o_inventario_anterior"] is None
    assert len(inv["arquivos"]["peticao.txt"]["sha256"]) == 64
    (caso / "input" / "novo.txt").write_text("novo", encoding="utf-8")
    inv = triagem.inventario(caso)
    assert inv["mudancas_desde_o_inventario_anterior"] == {"novos": ["novo.txt"], "removidos": [], "alterados": []}
    (caso / "input" / "peticao.txt").write_text("texto ALTERADO", encoding="utf-8")
    (sub / "a.txt").unlink()
    inv = triagem.inventario(caso)
    assert inv["mudancas_desde_o_inventario_anterior"]["alterados"] == ["peticao.txt"]
    assert inv["mudancas_desde_o_inventario_anterior"]["removidos"] == ["anexos/a.txt"]
    assert "original alterado" in inv["aviso"]
    # o inventário de referência não foi regravado com o original alterado
    guardado = json.loads((caso / "derived" / "inventario.json").read_text(encoding="utf-8"))["arquivos"]
    assert guardado["peticao.txt"]["sha256"] != inv["arquivos"]["peticao.txt"]["sha256"]


def test_travar_marca_originais_como_somente_leitura(tmp_path):
    caso = tmp_path / "c"
    triagem.init(caso, "caso-1")
    alvo = caso / "input" / "peticao.txt"
    alvo.write_text("texto", encoding="utf-8")
    try:
        triagem.inventario(caso, travar=True)
        with pytest.raises(PermissionError):
            alvo.write_text("sobrescrito", encoding="utf-8")
        assert alvo.read_text(encoding="utf-8") == "texto"
    finally:
        liberar(caso)


def test_inventario_sem_init_falha_com_mensagem(tmp_path):
    with pytest.raises(ValueError, match="init"):
        triagem.inventario(tmp_path / "inexistente")


# ------------------------------------------------------------------ números de processo
def test_numeros_cnj_reais_do_acordao_do_stj_sao_validos():
    doc, _ = extract.extrair(PDF)
    ext = CASOS / ".." / ".." / ".pytest_tmp"  # arquivo temporário abaixo
    ext.mkdir(exist_ok=True)
    f = ext / "extracao_stj.json"
    f.write_text(json.dumps({"documents": [doc]}, ensure_ascii=False), encoding="utf-8")
    res = triagem.processos([f])
    nums = {v["numero"] for v in res["validos"]}
    assert "1000284-67.2021.8.26.0547" in nums and "2021235-23.2022.8.26.0000" in nums
    assert len(res["validos"]) == 6
    assert all(o["locator"] == "p.15" for v in res["validos"] for o in v["ocorrencias"])
    assert res["candidatos_invalidos"] == []


def test_processos_formatos_candidato_invalido_e_numero_dentro_de_sequencia_longa(tmp_path):
    texto = ("Processo 1000284-67.2021.8.26.0547 e o mesmo na forma corrida 10002846720218260547. "
             "Número com erro: 1000284-68.2021.8.26.0547. Sequência longa 0181202110002846720218260547018120211 ignorada.")
    ext = {"documents": [{"document_id": "doc-x", "blocks": [{"id": "b0001", "locator": "p.1", "text": texto}]}]}
    f = tmp_path / "e.json"
    f.write_text(json.dumps(ext), encoding="utf-8")
    res = triagem.processos([f])
    assert [v["numero"] for v in res["validos"]] == ["1000284-67.2021.8.26.0547"]
    assert len(res["validos"][0]["ocorrencias"]) == 2  # formatado e corrido contam como o mesmo processo
    assert [c["numero"] for c in res["candidatos_invalidos"]] == ["1000284-68.2021.8.26.0547"]
    assert "dígito verificador" in res["candidatos_invalidos"][0]["motivo"]


# ------------------------------------------------------------------ CLI
def _cli(*args):
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "triagem.py"), *map(str, args)],
                       capture_output=True, cwd=RAIZ, stdin=subprocess.DEVNULL)
    return r.returncode, json.loads(r.stdout.decode("utf-8"))


def test_cli_init_inventario_e_erro(tmp_path):
    caso = tmp_path / "c"
    cod, res = _cli("init", caso, "--id", "caso-9")
    assert cod == 0 and "input" in res["pastas_criadas"]
    (caso / "input" / "a.txt").write_text("a", encoding="utf-8")
    cod, res = _cli("inventario", caso)
    assert cod == 0 and "a.txt" in res["arquivos"]
    cod, res = _cli("inventario", tmp_path / "nada")
    assert cod == 1 and "init" in res["erro"]
    cod, tipo = (lambda r: (r.returncode, json.loads(r.stdout.decode("utf-8"))))(subprocess.run(
        [sys.executable, "-P", str(RAIZ / "scripts" / "validate.py"), str(caso / "matter.json")],
        capture_output=True, cwd=RAIZ, stdin=subprocess.DEVNULL))
    assert cod == 1 and tipo["tipo"] == "matter" and not tipo["valido"]
