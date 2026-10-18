"""Cronologia: relevância, sigilo, exposição de fatos, versões e janelas (após a comparação com a referência)."""
import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import cronologia  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
FACTS = CASOS / "mapeamento_stj" / "facts.json"
MATTER = CASOS / "triagem_stj" / "matter.json"
EXTRACAO = CASOS / "verificacao_stj" / "extracao.json"
AVISO = (RAIZ / "shared" / "aviso-padrao.md").read_text(encoding="utf-8")


def D(original, iso, precision):
    return {"original": original, "iso": iso, "precision": precision}


def fato(fid, data=None, kind="alegacao", **kw):
    f = {"id": fid, "kind": kind, "text": f"Fato {fid}."}
    if kind in ("documentado", "alegacao"):
        f["source"] = {"document_id": "doc-x", "locator": "p.1", "excerpt": data["original"] if data else "trecho"}
    if kind == "alegacao":
        f["alleged_by"] = "autor"
    if data:
        f["date"] = data
    f.update(kw)
    return f


def escrever(tmp_path, nome, obj):
    p = tmp_path / nome
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p


def matter_com(tmp_path, **conf):
    m = json.loads(MATTER.read_text(encoding="utf-8"))
    m["matter"]["confidentiality"].update(conf)
    return escrever(tmp_path, "m.json", m)


def gerar(tmp_path, facts=FACTS, matter=None, **kw):
    r = cronologia.gerar(facts, tmp_path / "t.json", tmp_path / "c.md", matter=matter, **kw)
    return r, json.loads((tmp_path / "t.json").read_text(encoding="utf-8")), (tmp_path / "c.md").read_text(encoding="utf-8")


# ------------------------------------------------------------------ relevância e enquadramento
def test_relevancia_aparece_com_o_papel_do_cliente_e_a_secao_de_eventos_altos(tmp_path):
    _, t, md = gerar(tmp_path, matter=MATTER)
    assert t["enquadramento"]["papel"] == "interessado" and "fato-chave" in md.lower()
    assert "perspectiva do papel registrado: **interessado**" in md
    assert "## Eventos de relevância alta" in md and "Por que importa: Narra a data do contrato" in md
    por = {e["fact_id"]: e for e in t["entradas"]}
    assert por["f004"]["relevancia"] == "alta" and por["f001"]["relevancia"] == "media"
    assert "| ALTA |" in md and "| média |" in md


def test_relevancia_incerta_e_marcada_e_sem_data_alta_tambem_entra_nos_eventos(tmp_path):
    fs = {"schema_version": "1", "facts": [
        fato("a", D("10/03/2023", "2023-03-10", "dia"), relevancia="alta", relevancia_motivo="fato-chave", relevancia_incerta=True),
        fato("b", kind="informado", relevancia="alta", relevancia_motivo="o cliente diz que é central")]}
    _, t, md = gerar(tmp_path, escrever(tmp_path, "f.json", fs))
    assert "ALTA (incerta)" in md and "relevância incerta: confirmar" in md
    assert "**b** (sem data)" in md and "informado pelo usuário, sem documento" in md


def test_fonte_adicional_e_mostrada_como_tambem_em(tmp_path):
    f = fato("a", D("10/03/2023", "2023-03-10", "dia"))
    f["other_sources"] = [{"document_id": "doc-y", "locator": "p.7", "excerpt": "10/03/2023"}]
    _, t, md = gerar(tmp_path, escrever(tmp_path, "f.json", {"schema_version": "1", "facts": [f]}))
    assert t["entradas"][0]["outras_fontes"] == [{"document_id": "doc-y", "locator": "p.7"}]
    assert "também em doc-y, p.7" in md


# ------------------------------------------------------------------ exposição de fatos e sigilo
def test_exposicao_de_fatos_exige_matter_e_so_traz_relevancia_alta_ou_media(tmp_path):
    with pytest.raises(ValueError, match="exige --matter"):
        cronologia.gerar(FACTS, tmp_path / "t.json", tmp_path / "c.md", formato="fatos")
    _, t, md = gerar(tmp_path, matter=MATTER, formato="fatos")
    assert md.startswith("# Exposição de fatos")
    linhas = [l for l in md.splitlines() if l[:2].rstrip(".").isdigit() or l.startswith(("1.", "2.", "3.", "4."))]
    assert len(linhas) == 4  # f004, f005, f006 e f001; f003 (baixa) e fatos sem data ficam de fora
    assert "Segundo decisão da Corte local (TJSP), transcrita no voto, em" in md
    assert "f003" not in md.split("## Fora desta exposição")[0]  # f003 (baixa) só aparece na lista dos não narrados
    fora = md.split("## Fora desta exposição")[1]
    assert "f003" in fora and "f002" in fora  # nada some sem aviso


def test_triagem_mista_oculta_o_que_nao_e_ok_e_o_usuario_pode_incluir(tmp_path):
    f = json.loads(FACTS.read_text(encoding="utf-8"))
    for x in f["facts"]:
        if x["id"] in ("f005", "f006"):
            x["priv"] = "flag"
        if x["id"] == "f004":
            x.pop("priv")  # sem marca vale como 'review'
    escrever(tmp_path, "f.json", f)
    m = matter_com(tmp_path, privilegio="misto")
    _, t, md = gerar(tmp_path, tmp_path / "f.json", m, formato="fatos")
    assert "3 entrada(s) relevante(s) ficaram de fora por sinalização de sigilo" in md
    corpo = md.split("## Fatos, em ordem")[1]
    assert "14 de maio de 2020" not in corpo and "novembro de 2013" not in corpo  # f006 (flag) e f004 (sem marca)
    assert md.count("[documentado;") == 1  # só f001, que tem priv ok
    _, _, md2 = gerar(tmp_path, tmp_path / "f.json", m, formato="fatos", incluir_sinalizados=True)
    assert "por reconhecimento expresso do usuário" in md2 and "ficaram de fora" not in md2
    assert md2.count("[alegação de") == 3


def test_triagem_mista_no_formato_de_trabalho_mostra_coluna_de_sigilo(tmp_path):
    f = json.loads(FACTS.read_text(encoding="utf-8"))
    f["facts"][3]["priv"] = "review"
    escrever(tmp_path, "f.json", f)
    _, _, md = gerar(tmp_path, tmp_path / "f.json", matter_com(tmp_path, privilegio="misto"))
    assert "| Sigilo |" in md and "🔒" in md and "Entradas sem marca `priv: ok` aparecem como sinalizadas" in md


def test_fontes_nao_trialadas_impedem_a_exposicao_de_fatos(tmp_path):
    m = matter_com(tmp_path, privilegio="nao_triado")
    with pytest.raises(ValueError, match="triagem de sigilo"):
        cronologia.gerar(FACTS, tmp_path / "t.json", tmp_path / "c.md", matter=m, formato="fatos")
    cronologia.gerar(FACTS, tmp_path / "t.json", tmp_path / "c.md", matter=m)  # formato de trabalho continua possível


def test_segredo_de_justica_aparece_no_cabecalho(tmp_path):
    _, _, md = gerar(tmp_path, matter=matter_com(tmp_path, segredo_de_justica=True, consultas_externas="proibidas"))
    assert "Processo em segredo de justiça" in md and "art. 189" in md


def test_matter_invalido_impede_a_cronologia(tmp_path):
    m = json.loads(MATTER.read_text(encoding="utf-8"))
    m["matter"]["as_of"] = "2999-01-01"
    with pytest.raises(ValueError, match="matter.json inválido"):
        cronologia.gerar(FACTS, tmp_path / "t.json", tmp_path / "c.md", matter=escrever(tmp_path, "m.json", m))


# ------------------------------------------------------------------ versões, janelas, aviso
def test_versao_incrementa_com_a_versao_anterior(tmp_path):
    cronologia.gerar(FACTS, tmp_path / "t1.json", tmp_path / "c1.md")
    r1 = json.loads((tmp_path / "t1.json").read_text(encoding="utf-8"))
    assert r1["versao"] == 1
    r = cronologia.gerar(FACTS, tmp_path / "t2.json", tmp_path / "c2.md", anterior=tmp_path / "t1.json")
    assert r["versao"] == 2 and "versão 2" in (tmp_path / "c2.md").read_text(encoding="utf-8")


def test_janelas_sem_eventos_so_quando_pedidas_e_consideram_sobreposicao(tmp_path):
    fs = {"schema_version": "1", "facts": [
        fato("a", D("2020", "2020", "ano")),
        fato("b", D("15/02/2021", "2021-02-15", "dia")),   # dentro do ano de a: sem janela
        fato("c", D("10/03/2022", "2022-03-10", "dia")),   # janela de ~13 meses depois de fev/2021... ano 2020 termina em 2020-12-31
        fato("d", D("20/03/2022", "2022-03-20", "dia"))]}
    p = escrever(tmp_path, "f.json", fs)
    _, t, md = gerar(tmp_path, p)
    assert t["janelas_sem_eventos"] == [] and "Janelas sem eventos" not in md
    _, t, md = gerar(tmp_path, p, janela_meses=6)
    assert [j["entre"] for j in t["janelas_sem_eventos"]] == [["b", "c"]]
    assert t["janelas_sem_eventos"][0]["meses"] > 12 and "Janelas sem eventos" in md and "lacuna de documentos" in md


def test_todo_relatorio_termina_com_o_aviso_padrao(tmp_path):
    texto_aviso = AVISO.split("> ", 1)[1].strip().splitlines()[0]
    for formato in ("trabalho", "fatos"):
        _, _, md = gerar(tmp_path, matter=MATTER, formato=formato)
        assert md.rstrip().endswith(texto_aviso) and "não constitui parecer" in md.lower()


def test_conferir_continua_valido_para_cronologia_gerada_com_matter(tmp_path):
    gerar(tmp_path, matter=MATTER, janela_meses=3)
    assert cronologia.conferir(FACTS, tmp_path / "t.json")["atualizada"] is True


def test_exposicao_recusa_matter_sem_campo_privilegio(tmp_path):
    m = json.loads(MATTER.read_text(encoding="utf-8"))
    m["matter"]["confidentiality"].pop("privilegio")
    (tmp_path / "m.json").write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(ValueError, match="privilegio ausente"):
        cronologia.gerar(FACTS, tmp_path / "t.json", tmp_path / "c.md", matter=tmp_path / "m.json", formato="fatos")


def test_reformatar_o_facts_sem_mudar_fato_nao_invalida_a_cronologia(tmp_path):
    f = tmp_path / "facts.json"
    f.write_bytes(FACTS.read_bytes())
    cronologia.gerar(f, tmp_path / "t.json", tmp_path / "c.md")
    f.write_text(json.dumps(json.loads(f.read_text(encoding="utf-8")), ensure_ascii=False, indent=4), encoding="utf-8")
    r = cronologia.conferir(f, tmp_path / "t.json")
    assert r["atualizada"] is True and r["facts_json_mudou"] is True and r["conteudo_diverge"] is False
    obj = json.loads(f.read_text(encoding="utf-8"))
    obj["facts"][0]["text"] += " (alterado)"
    f.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    assert cronologia.conferir(f, tmp_path / "t.json")["atualizada"] is False
