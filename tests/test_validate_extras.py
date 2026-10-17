"""Campos acrescentados após a comparação com os repositórios de referência."""
import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import extract  # noqa: E402
import privacidade  # noqa: E402
import triagem  # noqa: E402
import validate  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
MATTER = json.loads((CASOS / "triagem_stj" / "matter.json").read_text(encoding="utf-8"))
PDF = CASOS / "verificacao_stj" / "fontes" / "stj_inteiro_teor.pdf"


def cods(lista):
    return [x["codigo"] for x in lista]


@pytest.fixture(scope="module")
def doc():
    return extract.extrair(PDF)[0]


@pytest.fixture(scope="module")
def idx(doc):
    return {doc["document_id"]: doc}


def fonte(**kw):
    base = {"source_id": "s1", "origin": "oficial", "access": "lida", "url": "https://x.gov.br/a",
            "retrieved_at": "2026-10-17", "content_hash": "a" * 64, "text_scope": "texto_legal",
            "pinpoint": {"locator": "art. 1º", "excerpt": "texto"}}
    base.update(kw)
    return base


def claim(**kw):
    base = {"id": "c1", "proposition": "p", "status": "supported", "existence": "confirmada",
            "quote_status": "conferida", "sources": [fonte()]}
    base.update(kw)
    return {"schema_version": "1", "claims": [base]}


def fato(fid="f1", kind="informado", **kw):
    f = {"id": fid, "kind": kind, "text": f"Fato {fid}."}
    f.update(kw)
    return f


def facts(*fs):
    return {"schema_version": "1", "facts": list(fs)}


# ------------------------------------------------------------------ privacidade.py
def test_cpf_cnpj_e_cartao_so_valem_com_digito_verificador():
    assert privacidade.cpf_valido("529.982.247-25") and privacidade.cpf_valido("52998224725")
    assert not privacidade.cpf_valido("529.982.247-26") and not privacidade.cpf_valido("111.111.111-11")
    assert privacidade.cnpj_valido("11.222.333/0001-81") and not privacidade.cnpj_valido("11.222.333/0001-82")
    assert privacidade.luhn_valido("4111 1111 1111 1111") and not privacidade.luhn_valido("4111 1111 1111 1112")


def test_detectar_mascara_e_nao_confunde_numero_cnj_nem_repete_o_valor():
    t = ("CPF 529.982.247-25, CNPJ 11.222.333/0001-81, cartão 4111 1111 1111 1111, joao.silva@exemplo.com.br, "
         "fone (82) 99999-1234, processo 1000284-67.2021.8.26.0547 e 10002846720218260547.")
    ach = privacidade.detectar(t)
    assert [a["tipo"] for a in ach] == ["cpf", "cnpj", "cartao", "email", "telefone"]
    mascaras = " ".join(a["mascara"] for a in ach)
    for completo in ("529.982.247", "11.222.333", "4111 1111", "joao.silva", "99999"):
        assert completo not in mascaras
    assert [a["mascara"] for a in ach][0] == "***.***.***-25"


def test_detectar_numero_de_20_digitos_e_cpf_invalido_nao_sao_dado_pessoal():
    assert privacidade.detectar("processo 10002846720218260547 e número 123.456.789-00") == []


# ------------------------------------------------------------------ claims
def test_source_relation_so_em_unsupported_e_gravidade_informada():
    r = validate.validar_claims(claim(status="unsupported", reason="r"))
    assert r.erros == [] and cods(r.avisos) == ["relacao_nao_informada"]
    ok = claim(status="unsupported", reason="r", source_relation="contradiz")
    assert validate.validar_claims(ok).erros == [] and validate.validar_claims(ok).avisos == []
    assert validate.resumo("claims", ok, None)["contraditas"] == ["c1"]
    assert cods(validate.validar_claims(claim(source_relation="contradiz")).erros) == ["relacao_incompativel"]
    assert cods(validate.validar_claims(claim(status="unsupported", reason="r", source_relation="talvez")).erros) == ["valor_invalido"]


def test_precedente_supported_pede_aplicabilidade_e_norma_nao():
    precedente = claim(tipo="precedente", proposition_scope="ementa")
    assert cods(validate.validar_claims(precedente).avisos) == ["aplicabilidade_nao_registrada"]
    precedente["claims"][0]["applicability"] = "STJ, 3ª Turma, fatos análogos"
    assert validate.validar_claims(precedente).avisos == []
    assert "aplicabilidade_nao_registrada" not in cods(validate.validar_claims(claim(tipo="sumula")).avisos)


def test_depends_on_referencia_proposicoes_existentes_e_nao_a_si_mesma():
    obj = claim(depends_on=["c1", "c9"])
    assert cods(validate.validar_claims(obj).erros) == ["referencia_circular", "referencia_inexistente"]
    obj["claims"][0]["depends_on"] = "c2"
    assert cods(validate.validar_claims(obj).erros) == ["tipo_invalido"]


def test_obtained_via_aceita_so_os_dois_modos_e_campos_de_apoio_sao_texto():
    assert validate.validar_claims(claim(sources=[fonte(obtained_via="user_supplied_source")])).erros == []
    assert cods(validate.validar_claims(claim(sources=[fonte(obtained_via="memoria")])).erros) == ["valor_invalido"]
    assert cods(validate.validar_claims(claim(suggested_fix="", draft_locator="  ")).erros) == ["tipo_invalido", "tipo_invalido"]


def test_dado_pessoal_no_pinpoint_gera_aviso_sem_repetir_o_valor():
    obj = claim(sources=[fonte(pinpoint={"locator": "p.1", "excerpt": "CPF 529.982.247-25 do agravante"})])
    r = validate.validar_claims(obj)
    assert cods(r.avisos).count("dado_pessoal_no_trecho") == 1 and "529.982" not in json.dumps(r.avisos)
    obj["claims"][0]["sources"][0]["pinpoint"]["excerpt"] = "CPF [...] do agravante"
    assert "dado_pessoal_no_trecho" not in cods(validate.validar_claims(obj).avisos)


# ------------------------------------------------------------------ facts
def test_fato_informado_pelo_usuario_nao_exige_documento_mas_avisa():
    r = validate.validar_facts(facts(fato()))
    assert r.erros == [] and cods(r.avisos) == ["fato_informado_sem_documento"]
    assert validate.resumo("facts", facts(fato()), r)["informado"] == 1


def test_other_sources_sao_conferidas_como_a_fonte_principal(doc, idx):
    did = doc["document_id"]
    f = fato("f1", "documentado", source={"document_id": did, "locator": "p.16", "excerpt": "Brasília, 16 de março de 2026"},
             other_sources=[{"document_id": did, "locator": "p.2", "excerpt": "Brasília, 18 de março de 2026"}])
    assert validate.validar_facts(facts(f), idx).erros == []
    f["other_sources"][0]["excerpt"] = "Brasília, 31 de dezembro de 2026"
    assert cods(validate.validar_facts(facts(f), idx).erros) == ["trecho_nao_encontrado"]
    f["other_sources"] = [{"locator": "p.2"}]
    assert cods(validate.validar_facts(facts(f)).erros) == ["campo_obrigatorio", "campo_obrigatorio"]
    f["other_sources"] = "texto"
    assert cods(validate.validar_facts(facts(f)).erros) == ["tipo_invalido"]


def test_relevancia_alta_exige_motivo_e_excesso_de_alta_gera_aviso():
    assert cods(validate.validar_facts(facts(fato(relevancia="alta"))).erros) == ["campo_obrigatorio"]
    assert validate.validar_facts(facts(fato(relevancia="alta", relevancia_motivo="é o fato-chave"))).erros == []
    assert cods(validate.validar_facts(facts(fato(relevancia="critica"))).erros) == ["valor_invalido"]
    assert cods(validate.validar_facts(facts(fato(relevancia_incerta="sim"))).erros) == ["tipo_invalido"]
    muitos = facts(*[fato(f"f{i}", relevancia="alta", relevancia_motivo="x") for i in range(6)])
    assert "relevancia_excessiva" in cods(validate.validar_facts(muitos).avisos)
    equilibrado = facts(*[fato(f"f{i}", relevancia="alta" if i < 2 else "media", relevancia_motivo="x") for i in range(6)])
    assert "relevancia_excessiva" not in cods(validate.validar_facts(equilibrado).avisos)


def test_priv_aceita_ok_flag_review():
    for v in ("ok", "flag", "review"):
        assert validate.validar_facts(facts(fato(priv=v))).erros == []
    assert cods(validate.validar_facts(facts(fato(priv="talvez"))).erros) == ["valor_invalido"]


def test_dado_pessoal_no_trecho_de_fato():
    f = fato("f1", "alegacao", alleged_by="parte", source={"document_id": "d", "locator": "p.1", "excerpt": "e-mail fulano@exemplo.com.br"})
    assert "dado_pessoal_no_trecho" in cods(validate.validar_facts(facts(f)).avisos)


# ------------------------------------------------------------------ matter
def com(mudanca):
    m = copy.deepcopy(MATTER)
    mudanca(m["matter"])
    return m


def test_matter_do_caso_real_com_partes_conferidas_contra_a_extracao(idx):
    r = validate.validar_matter(MATTER, idx)
    assert r.erros == [] and r.avisos == []
    errado = com(lambda m: m["partes"][0]["source"].update(excerpt="AGRAVANTE : OUTRA PESSOA"))
    assert cods(validate.validar_matter(errado, idx).erros) == ["trecho_nao_encontrado"]
    sem = com(lambda m: m["partes"][0].pop("source"))
    assert cods(validate.validar_matter(sem).avisos) == ["parte_sem_fonte"]
    assert cods(validate.validar_matter(com(lambda m: m["partes"][0].update(papel="rei"))).erros) == ["valor_invalido"]


def test_conflitos_ausente_e_aviso_e_cada_status_tem_seus_campos():
    r = validate.validar_matter(com(lambda m: m.pop("conflicts")))
    assert r.erros == [] and cods(r.avisos) == ["conflitos_nao_registrados"]
    cleared = {"status": "cleared", "method": "sistema do escritório", "cleared_by": "Dra. X", "cleared_date": "2026-10-01",
               "checked_against": ["Usina Santa Rita", "José Augusto Ribeiro"]}
    assert validate.validar_matter(com(lambda m: m.update(conflicts=cleared))).erros == []
    faltando = {"status": "cleared", "method": "sistema"}
    caminhos = {e["caminho"].rsplit(".", 1)[-1] for e in validate.validar_matter(com(lambda m: m.update(conflicts=faltando))).erros}
    assert caminhos == {"cleared_by", "cleared_date", "checked_against"}
    assert cods(validate.validar_matter(com(lambda m: m.update(conflicts={"status": "waived"}))).erros) == ["campo_obrigatorio"]
    assert validate.validar_matter(com(lambda m: m.update(conflicts={"status": "waived", "waiver_rationale": "renúncia assinada"}))).erros == []
    r = validate.validar_matter(com(lambda m: m.update(conflicts={"status": "pending", "owner": "Dr. Y"})))
    assert r.erros == [] and cods(r.avisos) == ["conflitos_pendentes"]


def test_conflitos_not_run_so_passa_sem_aviso_com_bypass_completo_e_ainda_assim_avisa():
    r = validate.validar_matter(com(lambda m: m.update(conflicts={"status": "not-run"})))
    assert cods(r.avisos) == ["conflitos_nao_verificados"]
    parcial = {"status": "not-run", "override": {"by": "Dr. Y"}}
    assert cods(validate.validar_matter(com(lambda m: m.update(conflicts=parcial))).erros) == ["campo_obrigatorio"]
    total = {"status": "not-run", "override": {"by": "Dr. Y", "date": "2026-10-17", "rationale": "urgência; checagem em curso"}}
    r = validate.validar_matter(com(lambda m: m.update(conflicts=total)))
    assert r.erros == [] and cods(r.avisos) == ["conflitos_com_bypass_registrado"]


def test_privilegio_e_segredo_de_justica():
    def conf(**kw):
        base = {"nivel": "restrito", "consultas_externas": "proibidas", "politica_modelo": "nada sai"}
        base.update(kw)
        return com(lambda m: m.update(confidentiality=base))

    assert cods(validate.validar_matter(conf()).avisos) == ["privilegio_nao_registrado"]
    assert validate.validar_matter(conf(privilegio="triado")).avisos == []
    assert cods(validate.validar_matter(conf(privilegio="nao_triado")).avisos) == ["fontes_sem_triagem_de_sigilo"]
    assert cods(validate.validar_matter(conf(privilegio="x")).erros) == ["valor_invalido"]
    assert validate.validar_matter(conf(privilegio="misto", segredo_de_justica=True)).avisos == []
    r = validate.validar_matter(conf(privilegio="triado", consultas_externas="permitidas", segredo_de_justica=True))
    assert set(cods(r.avisos)) == {"sigilo_com_consultas_externas", "segredo_com_consultas_externas"}
    assert cods(validate.validar_matter(conf(privilegio="triado", segredo_de_justica="sim")).erros) == ["tipo_invalido"]


# ------------------------------------------------------------------ triagem: privacidade e capacidades
def test_triagem_privacidade_so_com_valores_mascarados(tmp_path):
    texto = "Cliente CPF 529.982.247-25, e-mail maria@exemplo.com.br. Empresa CNPJ 11.222.333/0001-81."
    ext = {"documents": [{"document_id": "doc-x", "path": "a.pdf", "blocks": [
        {"id": "b0001", "locator": "p.1", "text": texto}, {"id": "b0002", "locator": "p.2", "text": "sem dado"}]}]}
    f = tmp_path / "e.json"
    f.write_text(json.dumps(ext), encoding="utf-8")
    res = triagem.privacidade([f])
    assert res["total_geral"] == 3 and set(res["achados"]) == {"cpf", "cnpj", "email"}
    assert res["achados"]["cpf"]["documentos"]["doc-x"]["ocorrencias"][0] == {
        "locator": "p.1", "block_id": "b0001", "mascara": "***.***.***-25"}
    assert "529.982" not in json.dumps(res) and "maria@" not in json.dumps(res)
    assert any("[...]" in r for r in res["recomendacoes"])


def test_triagem_capacidades_ocr_sempre_falso_e_detecta_bibliotecas():
    c = triagem.capacidades()
    assert c["ocr"] is False and c["detectado"]["pdfplumber"] is True and c["detectado"]["python_docx"] is True
    assert "forgelex" in c["observacao"]
