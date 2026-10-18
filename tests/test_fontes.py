import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import fontes  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
MATTER = json.loads((CASOS / "triagem_stj" / "matter.json").read_text(encoding="utf-8"))
CC_MD = CASOS / "verificacao_stj" / "fontes" / "cc_compilado.md"
PDF_STJ = CASOS / "verificacao_stj" / "fontes" / "stj_inteiro_teor.pdf"
URL_STJ = "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202302535191"


def ids(res):
    return [p["id"] for p in res["pontes"]]


def estados(res):
    return {p["id"]: p["estado"] for p in res["pontes"]}


# ------------------------------------------------------------------ registro e plano
def test_registro_de_pontes_e_coerente():
    reg = json.loads(fontes.REGISTRO_PONTES.read_text(encoding="utf-8"))
    pontes = reg["pontes"]
    assert len({p["id"] for p in pontes}) == len(pontes)
    for p in pontes:
        assert set(p) >= {"id", "tipos", "ordem", "origem", "como", "requer", "envia_termos_do_caso", "limites"}
        assert p["origem"] in ("oficial", "secundaria") and set(p["tipos"]) <= set(reg["tipos"])
    for tipo in reg["tipos"]:
        assert [p for p in pontes if tipo in p["tipos"] and p["id"] == "usuario_fornece"], tipo  # sempre há último recurso


def test_plano_sem_matter_lista_na_ordem_com_oficial_antes_do_secundario():
    r = fontes.plano("norma")
    assert ids(r) == ["planalto_compilado", "consultar_artigo", "usuario_fornece"]
    assert r["pontes"][0]["origem"] == "oficial" and r["pontes"][1]["origem"] == "secundaria"
    assert r["tem_ponte_oficial"] and r["aviso"] is None
    s = fontes.plano("precedente_stj")
    assert ids(s) == ["forgelex_stj", "stj_inteiro_teor", "stj_dados_abertos", "usuario_fornece"]
    assert s["pontes"][0]["origem"] == "secundaria"  # localiza; a leitura oficial vem depois


def test_plano_com_o_matter_do_caso_real():
    r = fontes.plano("precedente_stf", MATTER)
    assert estados(r) == {"stf_navegador": "disponivel", "usuario_fornece": "disponivel"}
    r = fontes.plano("precedente_stj", MATTER)
    assert estados(r)["forgelex_stj"] == "disponivel"


def test_politica_de_consultas_externas_filtra_pontes_que_enviam_termos():
    m = copy.deepcopy(MATTER)
    m["matter"]["confidentiality"] = {"nivel": "sigiloso", "consultas_externas": "proibidas", "politica_modelo": "x"}
    r = fontes.plano("precedente_stj", m)
    assert estados(r)["forgelex_stj"] == "excluida" and estados(r)["stj_inteiro_teor"] == "disponivel"
    assert "proíbe" in next(p for p in r["pontes"] if p["id"] == "forgelex_stj")["motivo"]
    stf = fontes.plano("precedente_stf", m)
    assert estados(stf)["stf_navegador"] == "excluida" and not stf["tem_ponte_oficial"] and "teto" in stf["aviso"]
    m["matter"]["confidentiality"]["consultas_externas"] = "somente_termos_genericos"
    r = fontes.plano("precedente_stj", m)
    assert estados(r)["forgelex_stj"] == "restrita" and "genéricos" in next(
        p for p in r["pontes"] if p["id"] == "forgelex_stj")["motivo"]


def test_capacidade_nao_registrada_torna_a_ponte_indisponivel():
    m = copy.deepcopy(MATTER)
    m["matter"]["capabilities"] = {"ocr": False}
    r = fontes.plano("norma", m)
    assert estados(r) == {"planalto_compilado": "indisponivel", "consultar_artigo": "indisponivel",
                          "usuario_fornece": "disponivel"}
    assert "fetch_oficial" in r["pontes"][0]["motivo"]


def test_plano_tipo_desconhecido():
    with pytest.raises(ValueError, match="tipo desconhecido"):
        fontes.plano("jurisprudencia_do_mundo")


# ------------------------------------------------------------------ baixar (rede simulada)
@pytest.fixture
def rede(monkeypatch):
    """Substitui o acesso à rede por respostas controladas e conta as tentativas."""
    estado = {"respostas": [], "chamadas": []}

    def falso(url, usar_ua=True, timeout=30):
        estado["chamadas"].append((url, usar_ua))
        r = estado["respostas"].pop(0) if len(estado["respostas"]) > 1 else estado["respostas"][0]
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(fontes, "_baixar_bytes", falso)
    return estado


def test_download_oficial_grava_hash_e_registra(rede, tmp_path):
    pdf = b"%PDF-1.4\n conteudo do acordao"
    rede["respostas"] = [(200, {"Content-Type": "application/pdf"}, pdf)]
    reg = tmp_path / "fontes" / "registro.json"
    e = fontes.baixar(URL_STJ, tmp_path / "fontes", reg)
    assert e["status"] == "lida" and e["origem"] == "oficial" and e["sha256"] == fontes._sha_bytes(pdf)
    assert Path(e["local_file"]).read_bytes() == pdf and e["local_file"].endswith(".pdf")
    assert e["source_id"] == "src-" + e["sha256"][:12]
    obj = json.loads(reg.read_text(encoding="utf-8"))
    assert obj["schema_version"] == "1" and obj["fontes"][0]["url"] == URL_STJ
    assert len(rede["chamadas"]) == 1 and rede["chamadas"][0][1] is True  # com User-Agent de navegador


def test_mesmo_nome_com_bytes_diferentes_guarda_as_duas_versoes(rede, tmp_path):
    rede["respostas"] = [(200, {"Content-Type": "application/pdf"}, b"%PDF-1.4 A")]
    a = fontes.baixar(URL_STJ, tmp_path, tmp_path / "r.json", nome="acordao.pdf")
    rede["respostas"] = [(200, {"Content-Type": "application/pdf"}, b"%PDF-1.4 B")]
    b = fontes.baixar(URL_STJ, tmp_path, tmp_path / "r.json", nome="acordao.pdf")
    assert a["local_file"] != b["local_file"] and Path(a["local_file"]).read_bytes() == b"%PDF-1.4 A"
    rede["respostas"] = [(200, {"Content-Type": "application/pdf"}, b"%PDF-1.4 B")]
    c = fontes.baixar(URL_STJ, tmp_path, tmp_path / "r.json", nome="acordao.pdf")
    assert c["local_file"] == b["local_file"]  # mesmos bytes: reaproveita
    assert len(json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))["fontes"]) == 3


def test_inteiro_teor_que_volta_como_html_generico_nao_vira_fonte_lida(rede, tmp_path):
    url = "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202401637939"
    rede["respostas"] = [(200, {"Content-Type": "text/html;charset=ISO-8859-1"}, b"<html>STJ - Integra de Acordaos</html>")]
    reg = tmp_path / "r.json"
    e = fontes.baixar(url, tmp_path / "f", reg)
    assert e["status"] == "source_missing" and "conteudo_inesperado" in e["motivo"]
    assert not (tmp_path / "f").exists() or not list((tmp_path / "f").iterdir())  # nada é guardado como fonte
    assert json.loads(reg.read_text(encoding="utf-8"))["fontes"][0]["status"] == "source_missing"
    # uma URL qualquer em HTML continua sendo página lida; o exigir explícito vale em qualquer URL
    rede["respostas"] = [(200, {"Content-Type": "text/html"}, b"<html>oi</html>")]
    assert fontes.baixar("https://www.stf.jus.br/x", tmp_path / "g")["status"] == "lida"
    rede["respostas"] = [(200, {"Content-Type": "text/html"}, b"<html>oi</html>")]
    assert fontes.baixar("https://www.stf.jus.br/x", tmp_path / "h", exigir="pdf")["status"] == "source_missing"


@pytest.mark.parametrize("nome", ["../../evil.pdf", "..\\..\\evil.pdf", "..", ".", "/etc/passwd", "C:\\Windows\\x.pdf"])
def test_nome_de_arquivo_nunca_sai_da_pasta_de_destino(rede, tmp_path, nome):
    rede["respostas"] = [(200, {"Content-Type": "application/pdf"}, b"%PDF-1.4 X")]
    destino = tmp_path / "fontes"
    e = fontes.baixar(URL_STJ, destino, nome=nome)
    assert e["status"] == "lida"
    gravado = Path(e["local_file"]).resolve()
    assert gravado.parent == destino.resolve() and gravado.is_file()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["fontes"]


@pytest.mark.parametrize("resposta", [
    (403, {"Cf-Mitigated": "challenge"}, b"<html>Just a moment</html>"),
    (202, {"x-amzn-waf-action": "challenge"}, b""),
    (202, {}, b""),
    (200, {"Content-Type": "text/html"}, "<html><title>Verificação de segurança — Senado Federal</title>".encode("utf-8")),
])
def test_desafio_anti_robo_nao_e_contornado_nem_repetido(rede, tmp_path, resposta):
    rede["respostas"] = [resposta]
    e = fontes.baixar("https://scon.stj.jus.br/SCON/", tmp_path, tmp_path / "r.json")
    assert e["status"] == "source_missing" and "não contornado" in e["motivo"]
    assert len(rede["chamadas"]) == 1  # sem nova tentativa com outro cabeçalho
    assert not list(tmp_path.glob("*.pdf")) and not list(tmp_path.glob("*.html"))
    assert json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))["fontes"][0]["status"] == "source_missing"


def test_falha_de_rede_tenta_duas_vezes_com_navegador_e_uma_sem(rede, tmp_path):
    rede["respostas"] = [TimeoutError("lento"), ConnectionResetError("reset"), OSError("fim")]
    e = fontes.baixar("https://exemplo.gov.br/x", tmp_path)
    assert e["status"] == "source_missing" and "OSError" in e["motivo"]
    assert [u for _, u in rede["chamadas"]] == [True, True, False]


def test_404_nao_insiste(rede, tmp_path):
    rede["respostas"] = [(404, {}, b"nao achei")]
    e = fontes.baixar("https://exemplo.gov.br/x", tmp_path)
    assert e["status"] == "source_missing" and "HTTP 404" in e["motivo"] and len(rede["chamadas"]) == 1


def test_pdf_com_bytes_inesperados_gera_aviso_e_origem_nao_oficial_e_secundaria(rede, tmp_path):
    rede["respostas"] = [(200, {"Content-Type": "application/pdf"}, b"<html>erro disfarcado</html>")]
    e = fontes.baixar("https://nexojuris.ia.br/doc", tmp_path)
    assert e["origem"] == "secundaria" and any("conteudo_inesperado" in a for a in e["avisos"])


@pytest.mark.parametrize("url,origem", [
    ("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm", "oficial"),
    ("https://processo.stj.jus.br/SCON/x", "oficial"), ("https://portal.stf.jus.br/", "oficial"),
    ("https://legis.senado.leg.br/dadosabertos/x", "oficial"), ("https://nexojuris.ia.br/mcp", "secundaria"),
    ("https://planalto.gov.br.evil.com/x", "secundaria"), ("https://evilplanalto.gov.br.com/x", "secundaria"),
])
def test_classificacao_da_origem_nao_se_deixa_enganar_por_host_parecido(url, origem):
    assert fontes.classificar_origem(url) == origem


def test_planalto_usa_fetch_oficial_registra_tachados_e_avisa_versao_nao_compilada(tmp_path):
    falso = tmp_path / "fetch_falso.py"
    falso.write_text("import sys\nopen(sys.argv[2], 'w', encoding='utf-8').write('Art. 1. Texto ~~revogado~~ e vigente.')\n",
                     encoding="utf-8")
    e = fontes.baixar("https://www.planalto.gov.br/ccivil_03/leis/x.htm", tmp_path / "f", tmp_path / "r.json",
                      fetch_oficial=falso)
    assert e["status"] == "lida" and e["via"] == "fetch_oficial.py" and e["content_type"] == "text/markdown"
    assert any("nao_compilada" in a for a in e["avisos"]) and any("tachado" in a for a in e["avisos"])
    assert Path(e["local_file"]).read_text(encoding="utf-8").startswith("Art. 1.")
    ausente = fontes.baixar("https://www.planalto.gov.br/x_compilada.htm", tmp_path / "f", fetch_oficial=tmp_path / "nao.py")
    assert ausente["status"] == "source_missing" and "ausente" in ausente["motivo"]


def test_download_real_do_stj_tem_o_mesmo_texto_do_caso_de_teste(tmp_path):
    if os.environ.get("JURIS_REDE") != "1":
        pytest.skip("teste de rede: defina JURIS_REDE=1")
    e = fontes.baixar(URL_STJ, tmp_path / "fontes", tmp_path / "r.json")
    assert e["status"] == "lida" and e["origem"] == "oficial"
    novo, _ = extract.extrair(e["local_file"])
    antigo, _ = extract.extrair(PDF_STJ)
    assert novo["status"] == "ok" and novo["text_sha256"] == antigo["text_sha256"]


# ------------------------------------------------------------------ anotações de alteração (vigência à época)
def test_anotacoes_no_cc_real_dispositivo_sem_alteracao_e_dispositivo_revogado():
    r = fontes.anotacoes(CC_MD, "206", "5", "I", "2013-11")
    assert r["dispositivo_localizado"] and r["anotacoes"] == []
    assert r["legal_time_sugerido"]["vigencia"] == "nao_verificada" and "não prova" in r["legal_time_sugerido"]["motivo"]
    r = fontes.anotacoes(CC_MD, "206", "1", "II", "2013-11")
    a = r["anotacoes"][0]
    assert (a["tipo"], a["ano"], a["relacao"], a["posterior_aos_fatos"]) == ("revogado", 2024, "no_dispositivo", True)
    assert "Lei nº 15.040" in a["texto"] and a["lei_url"].endswith("#art133")
    assert "posterior" in r["legal_time_sugerido"]["motivo"]
    r = fontes.anotacoes(CC_MD, "206", "1", "II", "2025-02")
    assert r["anotacoes"][0]["posterior_aos_fatos"] is False


def test_anotacoes_artigo_com_redacao_dada_e_artigo_inexistente():
    r = fontes.anotacoes(CC_MD, "206-A", data_fatos="2013-11")
    assert r["anotacoes"][0]["tipo"] == "redacao" and r["anotacoes"][0]["ano"] == 2022
    with pytest.raises(ValueError, match="não encontrado"):
        fontes.anotacoes(CC_MD, "99999")
    assert fontes.anotacoes(CC_MD, "206", "9", None)["dispositivo_localizado"] is False


def test_anotacoes_relacao_entre_dispositivo_e_anotacao(tmp_path):
    md = tmp_path / "lei.md"
    md.write_text("\n".join([
        "Art. 10. Regra.", "", "§ 1", "o", "Texto do parágrafo.", "", "I - primeiro;", "",
        "II - segundo;", "[(Incluído pela Lei nº 5, de 2020)](u/5)", "", "§ 2", "o", "Outro parágrafo.",
        "[(Redação dada pela Lei nº 7, de 2018)](u/7)", "", "I - tem-se que;", "",
        "Art. 11. Seguinte."]), encoding="utf-8")
    sub = fontes.anotacoes(md, "10", "1", None, "2019")  # consulta o § 1º; a anotação está num inciso dele
    assert [(a["dispositivo"], a["relacao"], a["posterior_aos_fatos"]) for a in sub["anotacoes"]] == [
        ("art. 10, § 1º, inciso II", "em_subdispositivo", True)]
    sup = fontes.anotacoes(md, "10", "2", "I", "2019")  # consulta inciso do § 2º; a anotação é do próprio § 2º
    assert [(a["relacao"], a["posterior_aos_fatos"]) for a in sup["anotacoes"]] == [("em_dispositivo_superior", False)]
    nenhum = fontes.anotacoes(md, "10", "1", "I", "2019")  # inciso I do § 1º: sem anotação própria nem superior
    assert nenhum["anotacoes"] == [] and nenhum["dispositivo_localizado"]
    mesmo = fontes.anotacoes(md, "10", "2", None, "2018")
    assert mesmo["anotacoes"][0]["mesmo_ano_dos_fatos"] is True and "mesmo ano" in mesmo["legal_time_sugerido"]["motivo"]


# ------------------------------------------------------------------ CLI
def test_cli_plano_anotacoes_e_erro(tmp_path):
    def cli(*args):
        r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "fontes.py"), *map(str, args)],
                           capture_output=True, cwd=RAIZ, stdin=subprocess.DEVNULL)
        return r.returncode, json.loads(r.stdout.decode("utf-8"))

    cod, r = cli("plano", "--tipo", "precedente_stj", "--matter", CASOS / "triagem_stj" / "matter.json")
    assert cod == 0 and r["pontes"][0]["id"] == "forgelex_stj"
    cod, r = cli("anotacoes", CC_MD, "--artigo", "206", "--paragrafo", "1", "--inciso", "II", "--data-fatos", "2013-11")
    assert cod == 0 and r["anotacoes"][0]["tipo"] == "revogado"
    cod, r = cli("plano", "--tipo", "nada")
    assert cod == 1 and "tipo desconhecido" in r["erro"]


# ------------------------------------------------------------------ atualidade do registro e portais para o usuário
def test_registro_de_pontes_declara_atualidade_e_vence_com_o_tempo():
    from datetime import date

    reg = json.loads(fontes.REGISTRO_PONTES.read_text(encoding="utf-8"))
    assert {"last_verified", "freshness_window_days", "freshness_category", "verified_against"} <= set(reg)
    em_dia = fontes.plano("norma", hoje=date(2026, 12, 1))
    assert em_dia["desatualizado"] is False and em_dia["aviso"] is None
    velho = fontes.plano("norma", hoje=date(2027, 3, 1))
    assert velho["desatualizado"] is True and "refaça a sondagem" in velho["aviso"] and velho["verificado_em"] == "2026-10-17"


def test_plano_traz_portais_para_o_usuario_conferir_quando_a_ponte_falha():
    r = fontes.plano("precedente_stj")
    urls = [p["url"] for p in r["portais_para_o_usuario"]]
    assert "https://scon.stj.jus.br/SCON/" in urls
    assert any("anti-robô" in p["nota"] for p in r["portais_para_o_usuario"])
    reg = json.loads(fontes.REGISTRO_PONTES.read_text(encoding="utf-8"))
    assert set(reg["portais_para_o_usuario"]) <= set(reg["tipos"])
    assert all(p["url"].startswith("https://") and p["nota"] for ps in reg["portais_para_o_usuario"].values() for p in ps)
