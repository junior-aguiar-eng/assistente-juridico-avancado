"""Rigor adicional da revisão crítica: citação como apoio, inteiro teor, trecho curto, hífen, blocos, narrativa."""
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import auditar  # noqa: E402
import extract  # noqa: E402
import validate  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
VERIF = CASOS / "verificacao_stj"
PDF = VERIF / "fontes" / "stj_inteiro_teor.pdf"


def cods(lista):
    return [x["codigo"] for x in lista]


@pytest.fixture(scope="module")
def doc():
    return extract.extrair(PDF)[0]


@pytest.fixture(scope="module")
def idx(doc):
    return {doc["document_id"]: doc}


def claim(doc, excerpt, **kw):
    base = {"id": "c1", "tipo": "precedente", "proposition": "p", "status": "supported", "existence": "confirmada",
            "quote_status": "conferida", "proposition_scope": "inteiro_teor",
            "applicability": "STJ, 3ª Turma; fatos análogos",
            "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida", "url": "https://processo.stj.jus.br/x",
                         "retrieved_at": "2026-10-17", "content_hash": doc["sha256"], "text_scope": "inteiro_teor",
                         "document_id": doc["document_id"], "pinpoint": {"locator": "p.5", "excerpt": excerpt}}]}
    base.update(kw)
    return {"schema_version": "1", "claims": [base]}


TRANSCRITO = "Na espécie, Petromais Distribuidora de Petróleo Ltda, em novembro de 2013 firmou, com a agravada"
DO_RELATOR = "CONHEÇO, portanto, do agravo e passo ao exame do recurso especial"


# ------------------------------------------------------------------ A2: apoio só em texto transcrito
def test_precedente_supported_com_apoio_so_em_texto_transcrito_e_erro(doc, idx):
    r = validate.validar_claims(claim(doc, TRANSCRITO), idx)
    assert "trecho_so_em_citacao" in cods(r.erros)
    ok = validate.validar_claims(claim(doc, DO_RELATOR), idx)
    assert "trecho_so_em_citacao" not in cods(ok.erros)


def test_cited_text_declarado_libera_e_exige_booleano(doc, idx):
    r = validate.validar_claims(claim(doc, TRANSCRITO, cited_text=True), idx)
    assert r.erros == [] and r.avisos == []
    assert cods(validate.validar_claims(claim(doc, DO_RELATOR, cited_text="sim"), idx).erros) == ["tipo_invalido"]


def test_citacao_em_norma_ou_estado_menor_so_avisa(doc, idx):
    norma = validate.validar_claims(claim(doc, TRANSCRITO, tipo="norma"), idx)
    assert "trecho_so_em_citacao" not in cods(norma.erros) and "trecho_em_citacao" in cods(norma.avisos)
    parcial = validate.validar_claims(claim(doc, TRANSCRITO, status="partial", reason="r", missing="m"), idx)
    assert "trecho_so_em_citacao" not in cods(parcial.erros) and "trecho_em_citacao" in cods(parcial.avisos)


def test_basta_uma_fonte_oficial_com_apoio_fora_da_citacao(doc, idx):
    c = claim(doc, TRANSCRITO)
    s2 = copy.deepcopy(c["claims"][0]["sources"][0])
    s2.update(source_id="s2", pinpoint={"locator": "p.5", "excerpt": DO_RELATOR})
    c["claims"][0]["sources"].append(s2)
    assert "trecho_so_em_citacao" not in cods(validate.validar_claims(c, idx).erros)


# ------------------------------------------------------------------ A3: inteiro teor precisa ter voto
def test_inteiro_teor_sem_relatorio_nem_voto_e_erro(doc):
    so_ementa = copy.deepcopy(doc)
    so_ementa["blocks"] = [b for b in so_ementa["blocks"] if b["section"] in ("cabecalho", "ementa", "acordao")]
    idx2 = {doc["document_id"]: so_ementa}
    ementa = next(b["text"] for b in so_ementa["blocks"] if b["section"] == "ementa" and b["text"].startswith("3. "))
    c = claim(doc, ementa[3:90], proposition_scope="ementa")
    r = validate.validar_claims(c, idx2)
    assert "inteiro_teor_sem_voto" in cods(r.erros)
    c["claims"][0]["sources"][0]["text_scope"] = "ementa"
    assert "inteiro_teor_sem_voto" not in cods(validate.validar_claims(c, idx2).erros)
    assert "inteiro_teor_sem_voto" not in cods(validate.validar_claims(claim(doc, DO_RELATOR), {doc["document_id"]: doc}).erros)


# ------------------------------------------------------------------ A5: trecho curto, hífen e blocos consecutivos
def test_trecho_curto_avisa_e_reticencias_nao_contam_como_palavra():
    f = {"schema_version": "1", "facts": [{"id": "f1", "kind": "alegacao", "alleged_by": "a", "text": "t",
                                           "source": {"document_id": "d", "locator": "p.1", "excerpt": "art. 206"}}]}
    assert cods(validate.validar_facts(f).avisos) == ["trecho_curto"]
    f["facts"][0]["source"]["excerpt"] = "a pretensão [...] de cobrança [...]"
    assert "trecho_curto" not in cods(validate.validar_facts(f).avisos)  # 4 palavras fora as reticências
    f["facts"][0]["source"]["excerpt"] = "o réu firmou o contrato em novembro"
    assert validate.validar_facts(f).avisos == []


def doc_sintetico(*textos, paginas=None):
    blocos = [{"id": f"b{i + 1:04d}", "locator": f"p.{(paginas or [1] * len(textos))[i]}", "page": (paginas or [1] * len(textos))[i],
               "page_end": (paginas or [1] * len(textos))[i], "section": "voto", "text": t, "is_quote": False, "tags": []}
              for i, t in enumerate(textos)]
    return {"document_id": "doc-sint", "media_type": "application/pdf", "blocks": blocos}


def fatos_com(excerpt, locator="p.1", kind="alegacao"):
    f = {"id": "f1", "kind": kind, "text": "t", "source": {"document_id": "doc-sint", "locator": locator, "excerpt": excerpt}}
    if kind == "alegacao":
        f["alleged_by"] = "a"
    return {"schema_version": "1", "facts": [f]}


def test_hifenizacao_de_fim_de_linha_nao_reprova_trecho_certo():
    d = doc_sintetico("O réu incorreu em descum- primento do contrato celebrado entre as partes.")
    idx = {"doc-sint": d}
    r = validate.validar_facts(fatos_com("incorreu em descumprimento do contrato celebrado"), idx)
    assert r.erros == []


def test_trecho_que_atravessa_dois_blocos_consecutivos_confere_e_o_localizador_vale_para_a_faixa():
    d = doc_sintetico("O contrato foi assinado pelas partes em 10 de março de 2023 e previa o", "pagamento em doze parcelas mensais.",
                      paginas=[3, 4])
    idx = {"doc-sint": d}
    exc = "assinado pelas partes em 10 de março de 2023 e previa o pagamento em doze parcelas"
    assert validate.validar_facts(fatos_com(exc, "p.3"), idx).erros == []
    assert validate.validar_facts(fatos_com(exc, "p.4"), idx).erros == []  # a faixa 3-4 inclui a página 4
    assert cods(validate.validar_facts(fatos_com(exc, "p.9"), idx).erros) == ["localizador_incoerente"]
    assert cods(validate.validar_facts(fatos_com("pagamento em doze parcelas mensais e juros de mora"), idx).erros) == ["trecho_nao_encontrado"]


# ------------------------------------------------------------------ M1: documentado na narrativa
def test_documentado_na_narrativa_avisa_e_o_dispositivo_e_o_termo_de_julgamento_nao(doc, idx):
    def fato(excerpt, locator):
        return {"schema_version": "1", "facts": [{"id": "f1", "kind": "documentado", "text": "t", "source": {
            "document_id": doc["document_id"], "locator": locator, "excerpt": excerpt}}]}

    narra = validate.validar_facts(fato("O Ministério Público Federal opinou pelo desprovimento do agravo", "p.5"), idx)
    assert cods(narra.avisos) == ["documentado_em_narrativa"] and narra.erros == []
    ato = validate.validar_facts(fato("Nessas condições, CONHEÇO do agravo para CONHECER em parte do recurso especial", "p.14"), idx)
    assert ato.avisos == []
    termo = validate.validar_facts(fato("Brasília, 16 de março de 2026", "p.16"), idx)
    assert termo.avisos == []
    como_alegacao = fato("O Ministério Público Federal opinou pelo desprovimento do agravo", "p.5")
    como_alegacao["facts"][0].update(kind="alegacao", alleged_by="relator")
    assert "documentado_em_narrativa" not in cods(validate.validar_facts(como_alegacao, idx).avisos)


# ------------------------------------------------------------------ A6 e A7 na auditoria
@pytest.fixture(scope="module")
def base(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("rigor")
    shutil.copytree(VERIF / "fontes", pasta / "fontes")
    shutil.copy(VERIF / "claims.json", pasta / "claims.json")
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "extract.py"), "fontes/stj_inteiro_teor.pdf",
                        "fontes/cc_compilado.md", "--no-cache", "--saida", "extracao.json"], cwd=pasta,
                       capture_output=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 0
    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(595, 842)
    with open(pasta / "escaneado.pdf", "wb") as fh:
        w.write(fh)
    subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "extract.py"), "escaneado.pdf", "--no-cache",
                    "--saida", "ext_escaneado.json"], cwd=pasta, capture_output=True, stdin=subprocess.DEVNULL)
    return pasta


def gravar(base, nome, obj):
    p = base / nome
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return str(p)


def g03(qc):
    return next(g for g in qc["gates"] if g["id"] == "G03_cobertura_leitura")


def test_lacuna_ligada_ao_documento_por_document_id_e_forte_e_por_nome_e_so_alerta(base):
    ext = json.loads((base / "ext_escaneado.json").read_text(encoding="utf-8"))["documents"][0]
    did = ext["document_id"]

    def facts(lacuna):
        return gravar(base, "facts_lac.json", {"schema_version": "1", "facts": [lacuna]})

    def auditoria(path):
        return auditar.auditar(path, None, [str(base / "ext_escaneado.json")], base=base)

    pelo_nome = auditoria(facts({"id": "f1", "kind": "lacuna", "text": "Documento escaneado.pdf não lido: sem texto."}))
    assert g03(pelo_nome)["resultado"] == "alerta" and "document_id" in g03(pelo_nome)["detalhe"]
    forte = auditoria(facts({"id": "f1", "kind": "lacuna", "text": "Não lido: sem camada de texto.", "document_id": did}))
    assert g03(forte)["resultado"] == "aprovado" and "por document_id" in g03(forte)["detalhe"]
    nenhuma = auditoria(facts({"id": "f1", "kind": "lacuna", "text": "Falta o contrato original."}))
    assert g03(nenhuma)["resultado"] == "reprovado"
    assert cods(validate.validar_facts({"schema_version": "1", "facts": [
        {"id": "f1", "kind": "lacuna", "text": "x", "document_id": 7}]}).erros) == ["tipo_invalido"]


def test_sem_teses_centrais_e_reprovacao_em_fundamentada_e_externa_salvo_declaracao(base):
    c = json.loads((base / "claims.json").read_text(encoding="utf-8"))
    c["claims"] = [x for x in c["claims"] if x["id"] == "c004"]  # c004 não é central
    caminho = gravar(base, "claims_sem_central.json", c)
    ext = [str(base / "extracao.json")]
    analise = auditar.auditar(None, caminho, ext, "analise", base=base)
    assert next(g for g in analise["gates"] if g["id"] == "G06_teses_centrais")["resultado"] == "alerta"
    fund = auditar.auditar(None, caminho, ext, "fundamentada", base=base)
    assert next(g for g in fund["gates"] if g["id"] == "G06_teses_centrais")["resultado"] == "reprovado"
    externa = auditar.auditar(None, caminho, ext, "analise", base=base, tipo_entrega="cliente")
    assert next(g for g in externa["gates"] if g["id"] == "G06_teses_centrais")["resultado"] == "reprovado"
    declarado = auditar.auditar(None, caminho, ext, "fundamentada", base=base, sem_teses_centrais=True)
    g06 = next(g for g in declarado["gates"] if g["id"] == "G06_teses_centrais")
    assert g06["resultado"] == "alerta" and "declarado pelo usuário" in g06["detalhe"]


# ------------------------------------------------------------------ M4: chave do cache
def test_chave_do_cache_depende_da_versao_das_bibliotecas(tmp_path, monkeypatch):
    texto = tmp_path / "a.txt"
    texto.write_text("Texto de teste.", encoding="utf-8")
    cache = tmp_path / "cache"
    extract.extrair(texto, cache)
    antes = sorted(p.name for p in cache.glob("*.json"))
    monkeypatch.setattr(extract, "PARAMS_HASH", "outraslibs")
    extract.extrair(texto, cache)
    depois = sorted(p.name for p in cache.glob("*.json"))
    assert len(antes) == 1 and len(depois) == 2 and extract.EXTRACTOR_VERSION in antes[0]
    assert set(extract._versoes_das_bibliotecas()) == {"pdfplumber", "pdfminer.six", "python-docx", "lxml"}
