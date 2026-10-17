import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import cronologia  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
FACTS = CASOS / "mapeamento_stj" / "facts.json"
EXTRACAO = CASOS / "verificacao_stj" / "extracao.json"


def fato(fid, kind="alegacao", data=None, **kw):
    f = {"id": fid, "kind": kind, "text": f"Fato {fid}."}
    if kind in ("documentado", "alegacao"):
        f["source"] = {"document_id": "doc-x", "locator": "p.1", "excerpt": data["original"] if data else "trecho"}
    if kind == "alegacao":
        f["alleged_by"] = "autor"
    if data:
        f["date"] = data
    f.update(kw)
    return f


def D(original, iso, precision):
    return {"original": original, "iso": iso, "precision": precision}


def facts_obj(*fatos):
    return {"schema_version": "1", "matter_id": "t", "facts": list(fatos)}


def build(*fatos):
    return cronologia.construir(facts_obj(*fatos), "0" * 64)


# ------------------------------------------------------------------ ordenação e precisão
def test_ordem_cronologica_do_caso_real_e_secao_sem_data(tmp_path):
    saida = cronologia.gerar(FACTS, tmp_path / "t.json", tmp_path / "c.md", extracoes=[EXTRACAO])
    t = json.loads((tmp_path / "t.json").read_text(encoding="utf-8"))
    assert [e["fact_id"] for e in t["entradas"]] == ["f004", "f005", "f006", "f001"]
    assert [e["ordem"] for e in t["entradas"]] == [1, 2, 3, 4]
    assert {s["fact_id"] for s in t["sem_data"]} == {"f002", "f003", "f007", "f008"}
    assert all(not e["ordem_incerta_com"] for e in t["entradas"])
    assert saida["resumo"] == {"total": 8, "com_data": 4, "sem_data": 4, "ordem_incerta": 0,
                               "por_kind": {"documentado": 2, "alegacao": 4, "inferencia": 1, "lacuna": 1}}
    assert saida["avisos_do_validador"] == 3  # os três fatos narrados em citação


def test_data_parcial_mantem_a_precisao_e_nao_vira_dia():
    t = build(fato("a", data=D("novembro de 2013", "2013-11", "mes")), fato("b", data=D("2017", "2017", "ano")))
    a, b = t["entradas"]
    assert a["data"] == D("novembro de 2013", "2013-11", "mes") and a["intervalo"] == {"inicio": "2013-11-01", "fim": "2013-11-30"}
    assert b["intervalo"] == {"inicio": "2017-01-01", "fim": "2017-12-31"}
    assert t["entradas"][0]["fact_id"] == "a"


def test_fevereiro_bissexto_no_intervalo_do_mes():
    t = build(fato("a", data=D("fev/2024", "2024-02", "mes")))
    assert t["entradas"][0]["intervalo"]["fim"] == "2024-02-29"


def test_intervalos_que_se_sobrepoem_tem_ordem_incerta_nos_dois_sentidos():
    t = build(fato("mes", data=D("novembro de 2013", "2013-11", "mes")),
              fato("dia", data=D("15/11/2013", "2013-11-15", "dia")),
              fato("outro", data=D("20/12/2013", "2013-12-20", "dia")))
    por = {e["fact_id"]: e for e in t["entradas"]}
    assert por["mes"]["ordem_incerta_com"] == ["dia"] and por["dia"]["ordem_incerta_com"] == ["mes"]
    assert por["outro"]["ordem_incerta_com"] == []
    assert t["resumo"]["ordem_incerta"] == 2


def test_mesmo_dia_tem_ordem_incerta_e_ano_engloba_o_mes():
    t = build(fato("a", data=D("01/03/2020", "2020-03-01", "dia")), fato("b", data=D("01/03/2020", "2020-03-01", "dia")),
              fato("c", data=D("2020", "2020", "ano")))
    por = {e["fact_id"]: e for e in t["entradas"]}
    assert por["a"]["ordem_incerta_com"] == ["b", "c"] and por["c"]["ordem_incerta_com"] == ["a", "b"]


def test_data_indefinida_e_fato_sem_data_nunca_entram_na_linha_do_tempo():
    t = build(fato("a", data=D("início de 2023", None, "indefinida")), fato("b", kind="lacuna"),
              fato("c", kind="inferencia", basis=["a"]), fato("d", data=D("10/03/2023", "2023-03-10", "dia")))
    assert [e["fact_id"] for e in t["entradas"]] == ["d"]
    motivos = {s["fact_id"]: s["motivo"] for s in t["sem_data"]}
    assert "indefinida" in motivos["a"] and motivos["b"] == "sem campo 'date'" and set(motivos) == {"a", "b", "c"}


def test_ordenacao_e_deterministica_independente_da_ordem_de_entrada():
    fs = [fato(x, data=D(d, d, "dia")) for x, d in (("z", "2020-01-02"), ("y", "2020-01-02"), ("x", "2019-12-31"))]
    a = build(*fs)
    b = build(*reversed(fs))
    assert [e["fact_id"] for e in a["entradas"]] == [e["fact_id"] for e in b["entradas"]] == ["x", "y", "z"]


def test_tipo_do_fato_e_autor_da_alegacao_aparecem_na_cronologia(tmp_path):
    cronologia.gerar(FACTS, tmp_path / "t.json", tmp_path / "c.md")
    md = (tmp_path / "c.md").read_text(encoding="utf-8")
    assert "alegação de decisão da Corte local (TJSP), transcrita no voto" in md
    assert "documentado |" in md and "## Sem data" in md and "## Lacunas" in md
    assert "Nenhum prazo foi calculado" in md


def test_markdown_escapa_barras_e_nao_calcula_intervalos(tmp_path):
    f = fato("a", data=D("10/03/2023", "2023-03-10", "dia"), text="Valor | cláusula 3")
    g = fato("b", data=D("10/03/2024", "2024-03-10", "dia"))
    p = tmp_path / "f.json"
    p.write_text(json.dumps(facts_obj(f, g)), encoding="utf-8")
    cronologia.gerar(p, tmp_path / "t.json", tmp_path / "c.md")
    md = (tmp_path / "c.md").read_text(encoding="utf-8")
    assert "Valor \\| cláusula 3" in md
    for palavra in ("dias", "meses depois", "anos depois", "prazo de"):
        assert palavra not in md.replace("Nenhum prazo foi calculado", "")


def test_conflitos_sao_listados_e_nao_resolvidos():
    t = build(fato("a", data=D("01/01/2020", "2020-01-01", "dia"), conflicts_with=["b"]),
              fato("b", data=D("02/01/2020", "2020-01-02", "dia"), conflicts_with=["a"]))
    assert t["conflitos"] == [["a", "b"]]
    assert "decide" in cronologia.markdown(t)


# ------------------------------------------------------------------ recusa, diferenças e atualização
def test_facts_invalido_nao_gera_cronologia(tmp_path):
    ruim = facts_obj(fato("a", data=D("10/03/2023", "2023-03", "dia")))
    p = tmp_path / "f.json"
    p.write_text(json.dumps(ruim), encoding="utf-8")
    with pytest.raises(ValueError, match="facts.json inválido"):
        cronologia.gerar(p, tmp_path / "t.json", tmp_path / "c.md")
    assert not (tmp_path / "t.json").exists()


def test_diferencas_entre_versoes_e_conferencia_de_cronologia_desatualizada(tmp_path):
    base = json.loads(FACTS.read_text(encoding="utf-8"))
    f1 = tmp_path / "f1.json"
    f1.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
    cronologia.gerar(f1, tmp_path / "t1.json", tmp_path / "c1.md")
    assert cronologia.conferir(f1, tmp_path / "t1.json")["atualizada"] is True
    novo = copy.deepcopy(base)
    novo["facts"] = [f for f in novo["facts"] if f["id"] != "f001"]
    f006 = next(f for f in novo["facts"] if f["id"] == "f006")
    f006["date"] = {"original": "14 de maio de 2020", "iso": "2020-05", "precision": "mes"}  # dia vira mês
    novo["facts"].append({"id": "f009", "kind": "lacuna", "text": "Falta a decisão do TJSP."})
    f2 = tmp_path / "f2.json"
    f2.write_text(json.dumps(novo, ensure_ascii=False), encoding="utf-8")
    assert cronologia.conferir(f2, tmp_path / "t1.json") == {"atualizada": False, "facts_json_mudou": True,
                                                              "conteudo_diverge": True}
    saida = cronologia.gerar(f2, tmp_path / "t2.json", tmp_path / "c2.md", anterior=tmp_path / "t1.json")
    assert saida["mudancas"] == {"novos": ["f009"], "removidos": ["f001"], "alterados": ["f006"], "reordenados": []}
    assert "## Alterações desde a versão anterior" in (tmp_path / "c2.md").read_text(encoding="utf-8")


def test_conferencia_detecta_timeline_adulterada_mesmo_com_facts_igual(tmp_path):
    p = tmp_path / "f.json"
    p.write_text(FACTS.read_text(encoding="utf-8"), encoding="utf-8")
    cronologia.gerar(p, tmp_path / "t.json", tmp_path / "c.md")
    t = json.loads((tmp_path / "t.json").read_text(encoding="utf-8"))
    t["entradas"][0]["data"]["iso"] = "1999-01"
    (tmp_path / "t.json").write_text(json.dumps(t), encoding="utf-8")
    assert cronologia.conferir(p, tmp_path / "t.json") == {"atualizada": False, "facts_json_mudou": False,
                                                           "conteudo_diverge": True}


def test_cli_gerar_e_conferir(tmp_path):
    def cli(*args):
        r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "cronologia.py"), *map(str, args)],
                           capture_output=True, cwd=RAIZ, stdin=subprocess.DEVNULL)
        return r.returncode, json.loads(r.stdout.decode("utf-8"))

    cod, res = cli("gerar", "--facts", FACTS, "--saida-json", tmp_path / "t.json", "--saida-md", tmp_path / "c.md")
    assert cod == 0 and res["entradas"] == 4
    assert cli("conferir", "--facts", FACTS, "--timeline", tmp_path / "t.json")[0] == 0
    cod, res = cli("gerar", "--facts", tmp_path / "nao_existe.json", "--saida-json", tmp_path / "x.json",
                   "--saida-md", tmp_path / "x.md")
    assert cod == 1 and "erro" in res
