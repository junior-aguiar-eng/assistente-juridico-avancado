"""Pré-checagem de contrato, validação do issues.json e pacotes de regras (rascunhos inativos)."""
import copy
import json
import sys
from pathlib import Path

import docx
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import contrato  # noqa: E402
import extract  # noqa: E402
import regras  # noqa: E402

CC = RAIZ / "tests" / "casos" / "verificacao_stj" / "fontes" / "cc_compilado.md"
LGPD = RAIZ / "tests" / "casos" / "regras_fontes" / "lgpd_compilado.md"
LPI = RAIZ / "tests" / "casos" / "regras_fontes" / "l9279_compilado.md"
REGRAS = RAIZ / "rules" / "br"


def extrair_contrato(tmp_path, paragrafos):
    d = docx.Document()
    for p in paragrafos:
        d.add_paragraph(p)
    f = tmp_path / "c.docx"
    d.save(f)
    doc, _ = extract.extrair(f)
    return {"documents": [doc]}, doc


CONTRATO = [
    "MINUTA - CONTRATO DE PRESTAÇÃO DE SERVIÇOS",
    "1. Objeto. A CONTRATADA prestará os serviços descritos no Anexo I e no Anexo II.",
    "2. Preço. O preço é de R$ ________ mensais, reajustado conforme a cláusula 9.",
    "3. Multa. Em caso de atraso, multa de 10% do valor do contrato, observado o item 2.1.",
    "4. Foro. Fica eleito o foro de [preencher].",
    "ANEXO I - Escopo dos serviços",
    "Descrição do escopo.",
]


def test_precheck_aponta_branco_anexo_remissao_assinatura_e_minuta(tmp_path):
    ext, doc = extrair_contrato(tmp_path, CONTRATO)
    r = contrato.precheck(ext)["documentos"][0]
    por = {}
    for a in r["achados"]:
        por.setdefault(a["tipo"], []).append(a)
    assert len(por["campo_em_branco"]) == 2 and all(a["locator"] for a in por["campo_em_branco"])
    assert [a["trecho"] for a in por["anexo_ausente"]] and "Anexo II" in por["anexo_ausente"][0]["trecho"]
    assert len(por["anexo_ausente"]) == 1  # o Anexo I existe
    restos = sorted(a["mensagem"].split("cláusula/item ")[1].split(",")[0] for a in por["remissao_sem_destino"])
    assert restos == ["2.1", "9"]
    assert "marca_de_minuta" in por and "assinatura_nao_identificada" in por
    assert r["contagem"]["campo_em_branco"] == 2


def test_precheck_contrato_limpo_nao_inventa_achado(tmp_path):
    ext, _ = extrair_contrato(tmp_path, [
        "CONTRATO DE PRESTAÇÃO DE SERVIÇOS", "1. Objeto. Serviços de consultoria.", "2. Preço. R$ 1.000,00 mensais, conforme a cláusula 1.",
        "2.1 Reajuste anual. Aplica-se o item 2.", "Maceió, 10 de março de 2026.", "Assinatura das partes e de duas testemunhas."])
    assert contrato.precheck(ext)["documentos"][0]["achados"] == []


def test_precheck_repassa_aviso_de_alteracao_rastreada(tmp_path):
    import redline_docx

    d = docx.Document()
    d.add_paragraph("1. Objeto. Serviços por 12 meses.")
    d.add_paragraph("Assinatura das partes.")
    f = tmp_path / "o.docx"
    d.save(f)
    redline_docx.aplicar(f, [{"acao": "substituir", "de": "12 meses", "para": "24 meses"}], tmp_path / "r.docx")
    doc, _ = extract.extrair(tmp_path / "r.docx")
    tipos = [a["mensagem"] for a in contrato.precheck({"documents": [doc]})["documentos"][0]["achados"] if a["tipo"] == "aviso_da_extracao"]
    assert tipos and tipos[0].startswith("alteracoes_rastreadas")


# ------------------------------------------------------------------ issues.json
@pytest.fixture
def ext_e_issue(tmp_path):
    ext, doc = extrair_contrato(tmp_path, ["1. Objeto. Serviços.", "3. Multa. Em caso de atraso, multa de 10% do valor total do contrato."])
    bloco = next(b for b in doc["blocks"] if "Multa" in b["text"])
    issue = {"id": "i1", "titulo": "Multa elevada", "clausula": "3", "document_id": doc["document_id"], "locator": bloco["locator"],
             "clause_text": bloco["text"], "severidade_juridica": "alta", "severidade_negocial": "media",
             "descricao": "A multa de 10% do contrato pode ser reduzida pelo juiz.",
             "base": [{"tipo": "regra", "rule_id": "civ-413"}], "sugestao": "multa de 2% do valor da parcela em atraso"}
    return ext, {"schema_version": "1", "posicao_da_parte": "contratante", "issues": [issue]}


# as 21 regras foram ativadas pelo revisor em 30/10/2026 (a civ-598 com ressalva de enquadramento)
def regras_com_civ598_inativa(tmp_path):
    """Cópia de rules/br com a civ-598 inativa: cenário de regra de rascunho, já que as 21 regras reais estão ativas."""
    pasta = tmp_path / "regras_rascunho"
    pasta.mkdir()
    for arq in REGRAS.glob("*.json"):
        obj = json.loads(arq.read_text(encoding="utf-8"))
        for r in obj["regras"]:
            if r["id"] == "civ-598":
                r["status"] = "inativa"
                r["revisao"] = {"revisor": None, "data": None, "observacao": None}
                r["nota"] = "Rascunho do mantenedor técnico: pergunta de revisão não revisada por profissional do Direito."
        (pasta / arq.name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return pasta


def cods(r):
    return [x["codigo"] for x in r["erros"]]


def test_apontamento_comercial_admite_avaliacao_juridica_pendente(ext_e_issue):
    ext, iss = ext_e_issue
    iss["issues"][0].update(severidade_juridica="nao_avaliada", motivo_nao_avaliada="Somente parâmetro comercial informado.",
                            base=[{"tipo": "pratica_do_cliente", "nota": "Cliente quer negociar a duração."}])
    r = contrato.validar_issues(iss, ext, REGRAS, "servicos_saas")
    assert r["erros"] == []
    assert r["avaliacao_juridica_pendente"] == ["i1"]
    assert r["entregavel"] is False and r["rascunho"] is False
    assert "avaliacao_juridica_pendente" in {a["codigo"] for a in r["avisos"]}


def test_avaliacao_juridica_pendente_exige_motivo(ext_e_issue):
    ext, iss = ext_e_issue
    iss["issues"][0].update(severidade_juridica="nao_avaliada", base=[{"tipo": "pratica_do_cliente", "nota": "Política comercial."}])
    assert "motivo_nao_avaliada_ausente" in cods(contrato.validar_issues(iss, ext))


@pytest.mark.parametrize("grau", ["baixa", "media", "alta", "critica"])
def test_pratica_comercial_nao_sustenta_graduacao_juridica(ext_e_issue, grau):
    ext, iss = ext_e_issue
    iss["issues"][0].update(severidade_juridica=grau, base=[{"tipo": "pratica_do_cliente", "nota": "Preferência comercial."}])
    r = contrato.validar_issues(iss, ext)
    assert "severidade_sem_base_juridica" in cods(r)
    assert not r["entregavel"]


def test_regra_nao_conferida_nao_libera_graduacao_comercial(ext_e_issue):
    ext, iss = ext_e_issue
    iss["issues"][0].update(severidade_juridica="baixa", base=[
        {"tipo": "pratica_do_cliente", "nota": "Preferência comercial."}, {"tipo": "regra", "rule_id": "inventada"}])
    r = contrato.validar_issues(iss, ext)
    assert r["entregavel"] is False
    assert "regra_nao_conferida" in {a["codigo"] for a in r["avisos"]}


def test_issue_com_regra_rascunho_e_barrada_e_com_permissao_vira_aviso(ext_e_issue, tmp_path):
    ext, iss = ext_e_issue
    rascunho = regras_com_civ598_inativa(tmp_path)
    iss["issues"][0]["base"] = [{"tipo": "regra", "rule_id": "civ-598"}]  # inativa nesta cópia
    r = contrato.validar_issues(iss, ext, rascunho, "servicos_saas")
    assert cods(r) == ["regra_nao_revisada"]
    r2 = contrato.validar_issues(iss, ext, rascunho, "servicos_saas", permitir_rascunho=True)
    assert r2["erros"] == [] and "regra_rascunho" in [x["codigo"] for x in r2["avisos"]]


def test_regra_ativada_pelo_revisor_sustenta_o_apontamento(ext_e_issue, tmp_path):
    ext, iss = ext_e_issue
    pasta = tmp_path / "regras"
    pasta.mkdir()
    pacote = json.loads((REGRAS / "servicos_saas.json").read_text(encoding="utf-8"))
    for r in pacote["regras"]:
        if r["id"] == "civ-413":
            r["status"] = "ativa"
            r["revisao"] = {"revisor": "Dra. Exemplo (OAB fictícia)", "data": "2026-10-20", "observacao": "teste"}
    (pasta / "servicos_saas.json").write_text(json.dumps(pacote, ensure_ascii=False), encoding="utf-8")
    assert contrato.validar_issues(iss, ext, pasta, "servicos_saas")["erros"] == []
    assert regras.validar(pasta)["erros"] == []


@pytest.mark.parametrize("mutar, codigo", [
    (lambda i: i.update(severidade_juridica="gravissima"), "severidade_juridica_invalida"),
    (lambda i: i.pop("severidade_negocial"), "severidade_negocial_invalida"),
    (lambda i: i.update(base=[]), "alta_sem_base"),
    (lambda i: i.update(base=[{"tipo": "mercado_eua", "nota": "padrão americano"}]), "tipo_de_base_invalido"),
    (lambda i: i.update(base=[{"tipo": "regra", "rule_id": "civ-999"}]), "regra_inexistente"),
    (lambda i: i.update(severidade_juridica="critica", base=[{"tipo": "pratica_do_cliente", "nota": "política interna"}]), "critica_sem_base_juridica"),
    (lambda i: i.update(base=[{"tipo": "pratica_do_cliente"}], severidade_juridica="media"), "pratica_sem_nota"),
    (lambda i: i.update(clause_text="Em caso de atraso, multa de 10% do valor total"), "clausula_truncada"),
    (lambda i: i.update(clause_text="Texto que não está no contrato nenhum."), "clausula_fora_do_documento"),
    (lambda i: i.update(locator="docx.par.99"), "clausula_nao_localizada"),
    (lambda i: i.pop("locator"), "localizador_ausente"),
    (lambda i: i.update(sugestao=i["clause_text"]), "sugestao_igual_ao_original"),
    (lambda i: i.pop("descricao"), "campo_ausente"),
])
def test_validador_de_issues_barra(ext_e_issue, mutar, codigo):
    ext, iss = ext_e_issue
    iss = copy.deepcopy(iss)
    mutar(iss["issues"][0])
    assert codigo in cods(contrato.validar_issues(iss, ext, REGRAS, "servicos_saas", permitir_rascunho=True))


def test_posicao_da_parte_e_obrigatoria(ext_e_issue):
    ext, iss = ext_e_issue
    iss.pop("posicao_da_parte")
    assert "posicao_ausente" in cods(contrato.validar_issues(iss, ext, REGRAS, "servicos_saas", permitir_rascunho=True))


def test_sem_extracao_avisa_que_nao_conferiu_o_texto(ext_e_issue):
    _, iss = ext_e_issue
    iss["issues"][0]["base"] = [{"tipo": "fonte", "source_id": "src-abc", "url": "https://www.planalto.gov.br/x", "retrieved_at": "2026-10-18", "locator": "art. 413"}]
    r = contrato.validar_issues(iss)
    assert r["erros"] == [] and "trecho_nao_conferido" in [x["codigo"] for x in r["avisos"]]


# ------------------------------------------------------------------ pacotes de regras
def test_pacotes_so_tem_ativas_as_regras_revisadas_e_batem_com_a_fonte():
    r = regras.validar(REGRAS, fontes={"cc": CC, "lgpd": LGPD, "lpi": LPI})
    assert r["erros"] == [] and r["regras"] == 21
    for arq in REGRAS.glob("*.json"):
        for regra in json.loads(arq.read_text(encoding="utf-8"))["regras"]:
            assert regra["status"] == "ativa" and regra["revisao"]["revisor"] and regra["revisao"]["data"]
            assert regra["fonte"]["url"].startswith("https://www.planalto.gov.br/") and regra["fonte"]["versao"] == "compilada"


def test_carregar_nao_entrega_regra_inativa_a_menos_que_peca_e_ela_vem_marcada(tmp_path):
    assert {r["id"] for r in regras.carregar(REGRAS, "servicos_saas")["regras"]} == {"civ-412", "civ-413", "civ-421a", "civ-422", "civ-423", "civ-424", "civ-473", "civ-478", "civ-598"}
    com = regras.carregar(REGRAS, "servicos_saas", incluir_inativas=True)["regras"]
    assert len(com) == 9 and not [r for r in com if r["uso"] == "RASCUNHO_NAO_REVISADO"]
    # numa cópia com a civ-598 inativa, ela só vem se pedida e marcada como rascunho
    rascunho = regras_com_civ598_inativa(tmp_path)
    assert "civ-598" not in {r["id"] for r in regras.carregar(rascunho, "servicos_saas")["regras"]}
    inc = regras.carregar(rascunho, "servicos_saas", incluir_inativas=True)["regras"]
    assert {r["id"] for r in inc if r["uso"] == "RASCUNHO_NAO_REVISADO"} == {"civ-598"}
    assert len(regras.carregar(REGRAS, "lgpd")["regras"]) == 10 and regras.carregar(REGRAS, "lgpd")["excluidas"] == []


def _copia_com_fontes(tmp_path):
    import shutil
    raiz = tmp_path / "repo"
    shutil.copytree(REGRAS, raiz / "rules" / "br")
    shutil.copytree(RAIZ / "tests" / "casos" / "regras_fontes" / "anpd", raiz / "tests" / "casos" / "regras_fontes" / "anpd")
    return raiz, raiz / "rules" / "br"


def test_fontes_complementares_anpd_conferem_com_o_arquivo_guardado_e_nao_ativam_regra():
    r = regras.validar(REGRAS, fontes={"cc": CC, "lgpd": LGPD, "lpi": LPI})
    assert r["erros"] == [] and not [a for a in r["avisos"] if a["codigo"].startswith("fonte_complementar")]
    lgpd = regras.carregar(REGRAS, "lgpd", incluir_inativas=True)
    assert {f["id"]: f["aplica_a"] for f in lgpd["fontes_complementares"]} == {"anpd-2-2022": ["lgpd-41", "lgpd-48"], "anpd-15-2024": ["lgpd-48"], "anpd-18-2024": ["lgpd-41"], "anpd-19-2024": ["lgpd-33"], "anpd-32-2026": ["lgpd-33"]}
    assert [len(f["arquivos"]) for f in lgpd["fontes_complementares"]] == [2, 1, 1, 1, 1]
    # fonte complementar não ativa nem desativa regra: o status vem só do campo da regra
    assert all(r["uso"] == "revisada" for r in regras.carregar(REGRAS, "lgpd")["regras"])
    art6 = next(a for f in lgpd["fontes_complementares"] for a in f["artigos"] if a["artigo"] == "6" and f["id"] == "anpd-15-2024")
    assert "prazo de três dias úteis" in art6["texto_literal"] and "vinte dias úteis" in art6["texto_literal"]


def test_fonte_complementar_com_texto_alterado_hash_errado_ou_regra_inexistente_e_erro(tmp_path):
    raiz, pasta = _copia_com_fontes(tmp_path)
    arq = pasta / "fontes" / "anpd.json"
    ok = json.loads(arq.read_text(encoding="utf-8"))
    assert regras.validar(pasta)["erros"] == []

    obj = json.loads(json.dumps(ok))
    obj["fontes"][0]["artigos"][2]["texto_literal"] = obj["fontes"][0]["artigos"][2]["texto_literal"].replace("três dias úteis", "cinco dias úteis")
    arq.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    assert "fonte_complementar_texto_diverge" in [e["codigo"] for e in regras.validar(pasta)["erros"]]

    obj = json.loads(json.dumps(ok))
    obj["fontes"][0]["arquivos"][1]["arquivo_sha256"] = "0" * 64
    arq.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    assert "fonte_complementar_hash_diverge" in [e["codigo"] for e in regras.validar(pasta)["erros"]]

    obj = json.loads(json.dumps(ok))
    obj["fontes"][1]["aplica_a"] = ["lgpd-999"]
    arq.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    assert "fonte_complementar_regra_inexistente" in [e["codigo"] for e in regras.validar(pasta)["erros"]]


def test_pacote_nda_tem_so_o_art_195_literal_ativado_pelo_revisor_e_lista_o_que_falta():
    nda = regras.carregar(REGRAS, "nda", incluir_inativas=True)
    assert {r["id"] for r in regras.carregar(REGRAS, "nda")["regras"]} == {"pi-195-xi", "pi-195-xii"} and len(nda["pendencias_de_fonte"]) == 3
    assert {r["id"] for r in nda["regras"]} == {"pi-195-xi", "pi-195-xii"}
    for r in nda["regras"]:
        f = r["fonte"]
        assert r["status"] == "ativa" and r["revisao"]["revisor"] and r["revisao"]["data"] and r["uso"] == "revisada"
        assert f["norma_id"] == "lpi" and "9.279" in f["norma"] and f["url"].endswith("/leis/l9279.htm") and f["artigo"] == "195"
        assert f["texto_literal"].startswith("Art. 195. Comete crime de concorrência desleal quem:")
        assert "mesmo após o término do contrato" in f["texto_literal"] and "obtidos por meios ilícitos" in f["texto_literal"]
        assert f["dispositivos_revogados"] == [] and "~~" not in f["texto_literal"] and "Vigência" not in f["texto_literal"]
    assert any("207 e 209" in p for p in nda["pendencias_de_fonte"])  # a via civil segue fora das regras


def test_pacote_nda_diverge_se_o_texto_for_alterado(tmp_path):
    pasta = tmp_path / "r"
    pasta.mkdir()
    obj = json.loads((REGRAS / "nda.json").read_text(encoding="utf-8"))
    f = obj["regras"][0]["fonte"]
    f["texto_literal"] = f["texto_literal"].replace("sem autorização", "com autorização")
    (pasta / "nda.json").write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    assert "texto_diverge_da_fonte" in [e["codigo"] for e in regras.validar(pasta, fontes={"lpi": LPI})["erros"]]
    assert regras.validar(pasta)["erros"] == []  # sem a fonte, só a estrutura é conferida


def test_ativar_sem_revisor_e_erro(tmp_path):
    pasta = tmp_path / "r"
    pasta.mkdir()
    pacote = json.loads((REGRAS / "servicos_saas.json").read_text(encoding="utf-8"))
    r598 = next(r for r in pacote["regras"] if r["id"] == "civ-598")
    assert r598["status"] == "ativa"
    r598["revisao"] = {"revisor": None, "data": None, "observacao": None}  # ativa, mas sem o registro do revisor
    (pasta / "servicos_saas.json").write_text(json.dumps(pacote, ensure_ascii=False), encoding="utf-8")
    assert "ativa_sem_revisor" in [e["codigo"] for e in regras.validar(pasta)["erros"]]
    assert "civ-598" not in {r["id"] for r in regras.carregar(pasta, "servicos_saas")["regras"]}  # e ela continua sem ser usada


def test_texto_alterado_a_mao_diverge_da_fonte(tmp_path):
    pasta = tmp_path / "r"
    pasta.mkdir()
    pacote = json.loads((REGRAS / "servicos_saas.json").read_text(encoding="utf-8"))
    pacote["regras"][0]["fonte"]["texto_literal"] += " Acrescentei isto."
    (pasta / "servicos_saas.json").write_text(json.dumps(pacote, ensure_ascii=False), encoding="utf-8")
    assert "texto_diverge_da_fonte" in [e["codigo"] for e in regras.validar(pasta, CC)["erros"]]


def test_extrair_artigo_recusa_artigo_inexistente_e_nao_confunde_421_com_421a():
    texto = CC.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="não encontrado"):
        regras.extrair_artigo(texto, "99999")
    a421 = regras.extrair_artigo(texto, "421")["texto_literal"]
    assert a421.startswith("Art. 421.") and "421-A" not in a421.split("\n")[0]


def test_texto_literal_nao_guarda_marcacao_de_link_da_conversao_da_pagina(tmp_path):
    fonte = tmp_path / "lei.md"
    fonte.write_text(
        "Art. 1º Aplica-se o disposto na [Lei nº 9.307, de 1996 (Lei de Arbitragem)](../../../LEIS/L9307.htm) e no "
        "[art. 1º da Lei nº 12.527](../../_Ato/L12527.htm#art1).\n\nArt. 2º Outro.\n", encoding="utf-8")
    texto = regras.extrair_artigo(fonte.read_text(encoding="utf-8"), "1")["texto_literal"]
    assert "](" not in texto and "[" not in texto
    assert "Lei nº 9.307, de 1996 (Lei de Arbitragem)" in texto and "art. 1º da Lei nº 12.527" in texto
    for r in regras.carregar(REGRAS, "lgpd", incluir_inativas=True)["regras"]:
        assert "](" not in r["fonte"]["texto_literal"], r["id"]


def test_texto_literal_cola_o_caput_isolado_sem_perder_a_alinea_separada(tmp_path):
    fonte = tmp_path / "lei.md"
    fonte.write_text(
        "Art. 1º Texto.\n\n§ 1º A exceção do inciso I do\n\ncaput\n\ndeste artigo vale.\n\n"
        "II - garantia, ou\n\ng) item separado.\n\nArt. 2º Outro.\n", encoding="utf-8")
    texto = regras.extrair_artigo(fonte.read_text(encoding="utf-8"), "1")["texto_literal"]
    assert "§ 1º A exceção do inciso I do caput deste artigo vale." in texto.split("\n")
    assert "g) item separado." in texto.split("\n")
    for r in regras.carregar(REGRAS, "lgpd", incluir_inativas=True)["regras"]:
        assert "\ncaput\n" not in "\n" + r["fonte"]["texto_literal"] + "\n", r["id"]


def test_pacote_lgpd_tem_texto_literal_sem_dispositivo_revogado_ou_vetado():
    pacote = {r["id"]: r for r in regras.carregar(REGRAS, "lgpd", incluir_inativas=True)["regras"]}
    assert set(pacote) == {f"lgpd-{n}" for n in (7, 11, 18, 33, 37, 39, 41, 42, 46, 48)}
    art7 = pacote["lgpd-7"]["fonte"]
    assert art7["dispositivos_revogados"] == ["§ 1º", "§ 2º"] and "Revogado" not in art7["texto_literal"]
    art41 = pacote["lgpd-41"]["fonte"]
    assert art41["dispositivos_revogados"] == ["§ 4º"] and "VETADO" not in art41["texto_literal"].upper()
    for r in pacote.values():
        f = r["fonte"]
        assert f["norma_id"] == "lgpd" and "13.709" in f["norma"] and f["url"].endswith("l13709compilado.htm")
        assert "Vigência" not in f["texto_literal"] and "Seção" not in f["texto_literal"]
        assert r["status"] == "ativa" and r["revisao"]["revisor"] and r["revisao"]["data"]


def test_pacote_lgpd_diverge_se_o_texto_for_alterado(tmp_path):
    pasta = tmp_path / "r"
    pasta.mkdir()
    obj = json.loads((REGRAS / "lgpd.json").read_text(encoding="utf-8"))
    obj["regras"][0]["fonte"]["texto_literal"] = obj["regras"][0]["fonte"]["texto_literal"].replace("hipóteses", "situações")
    (pasta / "lgpd.json").write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    assert "texto_diverge_da_fonte" in [e["codigo"] for e in regras.validar(pasta, fontes={"lgpd": LGPD})["erros"]]
    assert regras.validar(pasta)["erros"] == []  # sem a fonte, só a estrutura é conferida


def test_apontamento_com_regra_civil_avisa_uma_vez_que_o_cdc_pode_incidir(ext_e_issue):
    ext, iss = ext_e_issue  # base: civ-413, do pacote servicos_saas
    r = contrato.validar_issues(iss, ext, REGRAS, "servicos_saas")
    assert r["erros"] == [] and [x["codigo"] for x in r["avisos"]].count("cdc_pode_incidir") == 1
    iss["issues"].append(dict(iss["issues"][0], id="i2", base=[{"tipo": "regra", "rule_id": "civ-422"}]))
    r2 = contrato.validar_issues(iss, ext, REGRAS, "servicos_saas")
    assert [x["codigo"] for x in r2["avisos"]].count("cdc_pode_incidir") == 1  # um aviso por validação, não por apontamento
    iss["issues"] = [dict(iss["issues"][0], base=[{"tipo": "regra", "rule_id": "lgpd-42"}])]
    assert "cdc_pode_incidir" not in [x["codigo"] for x in contrato.validar_issues(iss, ext, REGRAS, "lgpd")["avisos"]]


def test_issue_pode_citar_regra_de_dois_pacotes(ext_e_issue, tmp_path):
    ext, iss = ext_e_issue
    rascunho = regras_com_civ598_inativa(tmp_path)
    iss["issues"][0]["base"] = [{"tipo": "regra", "rule_id": "civ-598"}, {"tipo": "regra", "rule_id": "lgpd-42"}]
    r = contrato.validar_issues(iss, ext, rascunho, "servicos_saas,lgpd", permitir_rascunho=True)
    assert r["erros"] == [] and [a["codigo"] for a in r["avisos"]].count("regra_rascunho") == 1  # só civ-598 é rascunho
    assert "regra_inexistente" in cods(contrato.validar_issues(iss, ext, rascunho, "servicos_saas", permitir_rascunho=True))


def test_critica_apoiada_so_em_rascunho_nunca_passa_nem_com_permissao(ext_e_issue, tmp_path):
    ext, iss = ext_e_issue
    iss["issues"][0].update(severidade_juridica="critica", base=[{"tipo": "regra", "rule_id": "civ-598"}])
    r = contrato.validar_issues(iss, ext, regras_com_civ598_inativa(tmp_path), "servicos_saas", permitir_rascunho=True)
    assert "critica_sem_base_juridica" in cods(r) and r["rascunho"] is True and r["entregavel"] is False


def test_fonte_inventada_nao_sustenta_apontamento(ext_e_issue):
    ext, iss = ext_e_issue
    iss["issues"][0].update(severidade_juridica="critica", base=[{"tipo": "fonte", "source_id": "s-inventada"}])
    r = contrato.validar_issues(iss, ext, REGRAS, "servicos_saas")
    assert "fonte_incompleta" in cods(r) and "critica_sem_base_juridica" in cods(r)


def test_resultado_limpo_e_entregavel(ext_e_issue):
    ext, iss = ext_e_issue
    iss["issues"][0]["base"] = [{"tipo": "fonte", "source_id": "s1", "local_file": "fontes/cc.md", "retrieved_at": "2026-10-18", "locator": "art. 413"}]
    r = contrato.validar_issues(iss, ext, REGRAS, "servicos_saas")
    assert r["erros"] == [] and r["rascunho"] is False and r["entregavel"] is True


def test_linha_de_assinatura_nao_e_campo_em_branco_nem_falta_de_assinatura(tmp_path):
    ext, _ = extrair_contrato(tmp_path, ["1. Objeto. Serviços.", "São Paulo, ____ de ____ de 2026.",
                                         "____________ CONTRATANTE        ____________ CONTRATADA"])
    assert contrato.precheck(ext)["documentos"][0]["achados"] == []
