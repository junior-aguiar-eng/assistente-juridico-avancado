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

PDF_STJ = RAIZ / "tests" / "casos" / "stj_aresp_2432194.pdf"


@pytest.fixture(scope="module")
def doc():
    d, _ = extract.extrair(PDF_STJ)
    return d


@pytest.fixture(scope="module")
def idx(doc):
    return {doc["document_id"]: doc}


def bloco(doc, trecho):
    return next(b for b in doc["blocks"] if trecho in b["text"])


def codigos(r, campo="erros"):
    return [e["codigo"] for e in getattr(r, campo)]


# ------------------------------------------------------------------ fixtures de dados válidos
@pytest.fixture
def facts(doc):
    did = doc["document_id"]
    b1 = bloco(doc, "Sessão Virtual de 10/03/2026 a 16/03/2026")
    b2 = bloco(doc, "JOSÉ alegou ofensa ao art. 205 do CC/2002. Sustentou")
    return {"schema_version": "1", "matter_id": "teste", "facts": [
        {"id": "f001", "kind": "documentado", "text": "O julgamento foi em sessão virtual de 10 a 16/03/2026.",
         "date": {"original": "10/03/2026", "iso": "2026-03-10", "precision": "dia"},
         "source": {"document_id": did, "block_id": b1["id"], "locator": b1["locator"],
                    "excerpt": "Sessão Virtual de 10/03/2026 a 16/03/2026"}},
        {"id": "f002", "kind": "alegacao", "text": "O agravante alegou ofensa ao art. 205 do CC.",
         "alleged_by": "agravante (José Augusto Ribeiro Representação)",
         "source": {"document_id": did, "block_id": b2["id"], "locator": b2["locator"],
                    "excerpt": "JOSÉ alegou ofensa ao art. 205 do CC/2002"}},
        {"id": "f003", "kind": "inferencia", "text": "O prazo discutido é o decenal geral.", "basis": ["f002"]},
        {"id": "f004", "kind": "lacuna", "text": "Não há cópia do acórdão de origem nos autos fornecidos."},
    ]}


@pytest.fixture
def claims(doc):
    b = bloco(doc, "se submete ao prazo quinquenal específico do art. 206")
    return {"schema_version": "1", "claims": [{
        "id": "c001", "tipo": "precedente", "central": True,
        "proposition": "O STJ aplica o prazo quinquenal do art. 206, § 5º, I, do CC à dívida líquida em instrumento particular.",
        "proposition_scope": "ementa", "status": "supported", "existence": "confirmada", "quote_status": "conferida",
        "applicability": "STJ, 3ª Turma, AREsp em recuperação judicial; vale como indicação para cobrança de dívida líquida em instrumento particular.",
        "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida",
                     "url": "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202302535191",
                     "retrieved_at": "2026-10-17", "content_hash": doc["sha256"], "text_scope": "inteiro_teor",
                     "document_id": doc["document_id"], "block_id": b["id"],
                     "pinpoint": {"locator": b["locator"], "excerpt": "se submete ao prazo quinquenal específico do art. 206"}}],
    }]}


def fonte(**kw):
    base = {"source_id": "s1", "origin": "oficial", "access": "lida", "url": "https://x.gov.br/a",
            "document_id": "doc-teste",
            "retrieved_at": "2026-10-17", "content_hash": "a" * 64, "text_scope": "texto_legal",
            "pinpoint": {"locator": "art. 1º", "excerpt": "texto da fonte lida pelo revisor"}}
    base.update(kw)
    return base


def claim(**kw):
    base = {"id": "c1", "proposition": "p", "status": "supported", "existence": "confirmada",
            "quote_status": "conferida", "sources": [fonte()]}
    base.update(kw)
    return {"schema_version": "1", "claims": [base]}


# ------------------------------------------------------------------ facts
def test_facts_validos_contra_extracao_real(facts, idx):
    r = validate.validar_facts(facts, idx)
    assert r.erros == [] and r.avisos == []
    assert validate.resumo("facts", facts, r) == {"total": 4, "documentado": 1, "alegacao": 1, "inferencia": 1, "lacuna": 1, "informado": 0}


def test_facts_documentado_e_alegacao_exigem_fonte_e_autor(facts):
    f = copy.deepcopy(facts)
    del f["facts"][0]["source"]
    del f["facts"][1]["alleged_by"]
    cods = [(e["codigo"], e["caminho"]) for e in validate.validar_facts(f).erros]
    assert ("campo_obrigatorio", "$.facts[0].source") in cods
    assert ("campo_obrigatorio", "$.facts[1].alleged_by") in cods


def test_facts_inferencia_precisa_de_base_existente_e_nao_circular(facts):
    f = copy.deepcopy(facts)
    f["facts"][2]["basis"] = ["f999", "f003"]
    assert codigos(validate.validar_facts(f)) == ["referencia_inexistente", "referencia_circular"]
    del f["facts"][2]["basis"]
    assert codigos(validate.validar_facts(f)) == ["campo_obrigatorio"]


def test_facts_ids_duplicados_e_invalidos(facts):
    f = copy.deepcopy(facts)
    f["facts"][1]["id"] = "f001"
    f["facts"][2]["basis"] = ["f001"]  # f002 deixou de existir ao renomear
    f["facts"][3]["id"] = "f 4!"
    assert set(codigos(validate.validar_facts(f))) == {"id_duplicado", "id_invalido"}


@pytest.mark.parametrize("data,cod", [
    ({"original": "10/03/2026", "iso": "2026-03", "precision": "dia"}, "data_incoerente"),
    ({"original": "10/03/2026", "iso": "2026-03-10", "precision": "indefinida"}, "data_incoerente"),
    ({"original": "10/03/2026", "iso": "2026-02-30", "precision": "dia"}, "data_invalida"),
    ({"original": "10/03/2026", "iso": "2026-13", "precision": "mes"}, "data_invalida"),
    ({"original": "10/03/2026", "precision": "ano"}, "campo_obrigatorio"),
    ({"original": "10/03/2026", "iso": None, "precision": "decada"}, "valor_invalido"),
])
def test_facts_data_ambigua_nao_ganha_precisao(facts, data, cod):
    f = copy.deepcopy(facts)
    f["facts"][0]["date"] = data
    assert codigos(validate.validar_facts(f)) == [cod]


def test_facts_data_indefinida_e_parcial_validas(facts):
    f = copy.deepcopy(facts)
    f["facts"][0]["date"] = {"original": "03/2026", "iso": "2026-03", "precision": "mes"}
    f["facts"][1]["date"] = {"original": "art. 205", "iso": None, "precision": "indefinida"}
    assert validate.validar_facts(f).erros == []


def test_facts_conflitos(facts):
    f = copy.deepcopy(facts)
    f["facts"][0]["conflicts_with"] = ["f002"]
    r = validate.validar_facts(f)
    assert r.erros == [] and codigos(r, "avisos") == ["conflito_nao_reciproco"]
    f["facts"][0]["conflicts_with"] = ["f777"]
    assert codigos(validate.validar_facts(f)) == ["referencia_inexistente"]


def test_facts_conferencia_com_extracao(facts, idx, doc):
    f = copy.deepcopy(facts)
    del f["facts"][0]["date"]
    f["facts"][0]["source"]["excerpt"] = "Sessão Virtual de 11/03/2026"
    f["facts"][1]["source"]["document_id"] = "doc-inexistente"
    cods = codigos(validate.validar_facts(f, idx))
    assert cods == ["trecho_nao_encontrado", "documento_nao_extraido"]
    f = copy.deepcopy(facts)
    f["facts"][0]["source"]["block_id"] = "b9999"
    assert codigos(validate.validar_facts(f, idx)) == ["bloco_inexistente"]


def test_facts_trecho_com_reticencias_confere(facts, idx):
    f = copy.deepcopy(facts)
    f["facts"][0]["source"]["excerpt"] = "Sessão Virtual de 10/03/2026 [...] 16/03/2026"
    r = validate.validar_facts(f, idx)
    assert r.erros == [] and r.avisos == []


def test_facts_aviso_quando_trecho_esta_em_citacao(facts, idx, doc):
    b = bloco(doc, "Na espécie, Petromais")
    f = copy.deepcopy(facts)
    f["facts"][1]["source"].update(block_id=b["id"], locator=b["locator"], excerpt="Na espécie, Petromais Distribuidora")
    r = validate.validar_facts(f, idx)
    assert r.erros == [] and codigos(r, "avisos") == ["trecho_em_citacao"]


# ------------------------------------------------------------------ claims
def test_claim_supported_valida_contra_extracao_real(claims, idx):
    r = validate.validar_claims(claims, idx)
    assert r.erros == [] and r.avisos == []
    assert validate.resumo("claims", claims, r)["supported"] == 1


def test_claim_hash_e_trecho_conferidos_com_o_arquivo_lido(claims, idx):
    c = copy.deepcopy(claims)
    c["claims"][0]["sources"][0]["content_hash"] = "b" * 64
    assert codigos(validate.validar_claims(c, idx)) == ["hash_diverge"]
    c = copy.deepcopy(claims)
    c["claims"][0]["sources"][0]["pinpoint"]["excerpt"] = "prazo decenal do art. 205"
    assert codigos(validate.validar_claims(c, idx)) == ["trecho_nao_encontrado"]


def test_claim_unverified_com_fonte_inacessivel_e_valido_e_central_gera_aviso():
    c = claim(status="unverified", existence="indisponivel", central=True,
              sources=[{"source_id": "s1", "origin": "oficial", "access": "source_missing",
                        "url": "https://scon.stj.jus.br", "error": "HTTP 403 (desafio anti-robô)"}])
    c["claims"][0].pop("quote_status")
    r = validate.validar_claims(c)
    assert r.erros == [] and codigos(r, "avisos") == ["tese_central_nao_verificada"]
    assert validate.resumo("claims", c, r)["centrais_pendentes"] == ["c1"]


def test_claim_unverified_sem_fontes_e_valido():
    c = claim(status="unverified", existence="nao_confirmada", sources=[])
    c["claims"][0].pop("quote_status")
    assert validate.validar_claims(c).erros == []


def test_claim_unverified_com_fonte_lida_e_erro():
    assert codigos(validate.validar_claims(claim(status="unverified"))) == ["unverified_com_fonte_lida"]


def test_claim_estados_que_exigem_leitura_sem_fonte_lida():
    nao_lida = [{"source_id": "s1", "origin": "oficial", "access": "nao_acessada"}]
    for st, extra in (("supported", {}), ("partial", {"reason": "r", "missing": "m"}), ("unsupported", {"reason": "r"})):
        assert "estado_sem_fonte_lida" in codigos(validate.validar_claims(claim(status=st, sources=nao_lida, **extra)))


def test_claim_so_fonte_secundaria_tem_teto_partial():
    c = claim(sources=[fonte(origin="secundaria")])
    assert "teto_partial_sem_fonte_oficial" in codigos(validate.validar_claims(c))
    p = claim(status="partial", sources=[fonte(origin="secundaria")], reason="só fonte secundária", missing="leitura da fonte oficial")
    assert validate.validar_claims(p).erros == []


def test_claim_ementa_nao_equivale_a_inteiro_teor():
    c = claim(tipo="precedente", sources=[fonte(text_scope="ementa")])
    assert "ementa_nao_equivale_a_inteiro_teor" in codigos(validate.validar_claims(c))
    c = claim(tipo="precedente", proposition_scope="ementa", sources=[fonte(text_scope="ementa")])
    assert validate.validar_claims(c).erros == []
    c = claim(tipo="precedente", sources=[fonte(text_scope="inteiro_teor")])
    assert validate.validar_claims(c).erros == []
    c = claim(tipo="sumula", sources=[fonte(text_scope="ementa")])  # só precedente e tema exigem inteiro teor por padrão
    assert validate.validar_claims(c).erros == []


def test_claim_supported_exige_citacao_conferida():
    assert codigos(validate.validar_claims(claim(quote_status="nao_conferida"))) == ["citacao_nao_conferida"]
    assert codigos(validate.validar_claims(claim(quote_status="divergente"))) == ["citacao_nao_conferida"]


def test_claim_inexistencia_nunca_decorre_de_busca_vazia_ou_acesso_negado():
    for exist in ("nao_confirmada", "indisponivel"):
        for st, extra in (("supported", {}), ("unsupported", {"reason": "r"})):
            assert "existencia_incompativel" in codigos(validate.validar_claims(claim(status=st, existence=exist, **extra)))
    r = validate.validar_claims(claim(existence="inexistente"))
    assert codigos(r) == ["valor_invalido"]


def test_claim_partial_e_unsupported_exigem_motivo():
    assert codigos(validate.validar_claims(claim(status="partial"))) == ["campo_obrigatorio", "campo_obrigatorio"]
    assert codigos(validate.validar_claims(claim(status="unsupported"))) == ["campo_obrigatorio"]
    c = claim(status="unsupported", reason="o acórdão diz o contrário", sources=[fonte(origin="secundaria")])
    assert codigos(validate.validar_claims(c)) == ["unsupported_exige_fonte_oficial"]
    c = claim(status="unsupported", reason="o acórdão diz o contrário")
    assert validate.validar_claims(c).erros == []


def test_claim_tese_central_parcial_gera_aviso():
    c = claim(status="partial", central=True, reason="r", missing="m")
    assert codigos(validate.validar_claims(c), "avisos") == ["tese_central_sem_apoio_pleno"]


def test_claim_fonte_lida_exige_url_data_hash_escopo_e_pinpoint():
    c = claim(sources=[{"source_id": "s1", "origin": "oficial", "access": "lida"}])
    cods = [(e["caminho"].rsplit(".", 1)[-1]) for e in validate.validar_claims(c).erros]
    assert {"document_id", "url", "retrieved_at", "content_hash", "text_scope", "pinpoint"} <= set(cods)
    c = claim(sources=[fonte(content_hash="XYZ", retrieved_at="ontem")])
    assert set(codigos(validate.validar_claims(c))) == {"hash_invalido", "data_invalida"}


def test_claim_pinpoint_sem_leitura_e_erro():
    c = claim(status="unverified", sources=[fonte(access="source_missing")])
    assert codigos(validate.validar_claims(c)) == ["pinpoint_sem_leitura"]


def test_claim_norma_supported_avisa_vigencia_e_legal_time_resolve():
    c = claim(tipo="norma")
    assert codigos(validate.validar_claims(c), "avisos") == ["vigencia_nao_verificada"]
    c = claim(tipo="norma", sources=[fonte(legal_time={"as_of": "2026-10-17", "vigencia": "vigente"})])
    r = validate.validar_claims(c)
    assert r.erros == [] and r.avisos == []
    c = claim(tipo="norma", sources=[fonte(legal_time={"as_of": "2026-10-17", "vigencia": "talvez"})])
    assert codigos(validate.validar_claims(c)) == ["valor_invalido"]


def test_claim_enums_invalidos_e_ids():
    c = claim(status="confirmed", tipo="lei")
    assert codigos(validate.validar_claims(c)) == ["valor_invalido", "valor_invalido"]
    c = claim()
    c["claims"].append(copy.deepcopy(c["claims"][0]))
    assert "id_duplicado" in codigos(validate.validar_claims(c))


# ------------------------------------------------------------------ estrutura e CLI
def test_estrutura_e_schema_version():
    assert codigos(validate.validar({"foo": 1})[1]) == ["estrutura"]
    assert codigos(validate.validar({"facts": [], "claims": []})[1]) == ["estrutura"]
    assert "schema_version" in codigos(validate.validar_claims({"schema_version": "2", "claims": []}))
    assert codigos(validate.validar_facts([1, 2])) == ["estrutura"]


def _cli(tmp_path, obj, *extra, nome="a.json"):
    f = tmp_path / nome
    f.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "validate.py"), str(f), *extra],
                       capture_output=True, cwd=RAIZ)
    return r.returncode, json.loads(r.stdout.decode("utf-8"))


def test_cli_valido_invalido_e_estrito(tmp_path, claims, doc):
    ext = tmp_path / "extract.json"
    ext.write_text(json.dumps({"documents": [doc]}, ensure_ascii=False), encoding="utf-8")
    cod, saida = _cli(tmp_path, claims, "--extracoes", str(ext))
    assert cod == 0 and saida["valido"] and saida["tipo"] == "claims" and saida["erros"] == []
    c = copy.deepcopy(claims)
    c["claims"][0]["sources"][0]["content_hash"] = "c" * 64
    cod, saida = _cli(tmp_path, c, "--extracoes", str(ext))
    assert cod == 1 and saida["erros"][0]["codigo"] == "hash_diverge"
    c = claim(tipo="norma")  # só aviso
    cod, _ = _cli(tmp_path, c)
    assert cod == 0
    cod, saida = _cli(tmp_path, c, "--estrito")
    assert cod == 1 and saida["avisos"][0]["codigo"] == "vigencia_nao_verificada"


def test_cli_arquivo_ilegivel(tmp_path):
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "validate.py"), str(tmp_path / "nao_existe.json")],
                       capture_output=True, cwd=RAIZ)
    saida = json.loads(r.stdout.decode("utf-8"))
    assert r.returncode == 1 and saida["erros"][0]["codigo"] == "arquivo_ilegivel"


# ------------------------------------------------------------------ localizador e data conferidos (C4)
def test_localizador_que_nao_bate_com_onde_o_trecho_esta_e_erro(facts, idx):
    b = bloco(doc_unico := next(iter(idx.values())), "Brasília, 16 de março de 2026")  # só existe na p.16
    f = copy.deepcopy(facts)
    f["facts"] = [{"id": "f1", "kind": "documentado", "text": "x", "source": {
        "document_id": doc_unico["document_id"], "locator": "p.2", "excerpt": "Brasília, 16 de março de 2026"}}]
    erros = validate.validar_facts(f, idx).erros
    assert [e["codigo"] for e in erros] == ["localizador_incoerente"] and "p.16" in erros[0]["mensagem"]
    f["facts"][0]["source"]["block_id"] = b["id"]  # com block_id também
    assert codigos(validate.validar_facts(f, idx)) == ["localizador_incoerente"]
    f["facts"][0]["source"]["locator"] = b["locator"]
    assert validate.validar_facts(f, idx).erros == []


def test_localizador_aceita_pagina_da_ocorrencia_faixa_e_texto_livre(facts, idx, doc):
    f = copy.deepcopy(facts)
    f["facts"][0]["source"].pop("block_id")
    loc = f["facts"][0]["source"]["locator"]
    pag = loc.split(".")[1]
    for ok in (f"p.{pag}", f"p.{pag}, termo de julgamento", f"fls. 3, p. {pag}", f"p.{int(pag) - 1}-{int(pag) + 1}",
               "termo de julgamento"):  # texto livre sem página não é verificável: não reprova
        f["facts"][0]["source"]["locator"] = ok
        assert validate.validar_facts(f, idx).erros == [], ok


def test_localizador_de_paragrafo_em_arquivo_sem_paginas(tmp_path):
    md = tmp_path / "n.md"
    md.write_text("\n\n".join(["# Fatos", "O réu foi citado em 10/03/2023.", "O autor pagou R$ 500,00."]) + "\n",
                  encoding="utf-8")
    d, _ = extract.extrair(md)
    idx_md = {d["document_id"]: d}
    base = {"schema_version": "1", "facts": [{"id": "f1", "kind": "documentado", "text": "x", "source": {
        "document_id": d["document_id"], "locator": "par.2", "excerpt": "O réu foi citado em 10/03/2023"}}]}
    assert validate.validar_facts(base, idx_md).erros == []
    base["facts"][0]["source"]["locator"] = "par.3"
    assert codigos(validate.validar_facts(base, idx_md)) == ["localizador_incoerente"]


def test_data_precisa_estar_no_trecho_citado(facts, idx):
    f = copy.deepcopy(facts)
    f["facts"][0]["date"] = {"original": "01/01/1999", "iso": "1999-01-01", "precision": "dia"}
    erros = validate.validar_facts(f, idx).erros
    assert [e["codigo"] for e in erros] == ["data_fora_do_trecho"] and erros[0]["caminho"] == "$.facts[0].date.original"
    assert codigos(validate.validar_facts(f)) == ["data_fora_do_trecho"]  # vale também sem extração
    f["facts"][0]["date"] = {"original": "10/03/2026", "iso": "2026-03-10", "precision": "dia"}
    assert validate.validar_facts(f, idx).erros == []
