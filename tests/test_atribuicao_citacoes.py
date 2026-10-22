"""Atribuição contextual: transcrição não é resultado do órgão que a cita."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import auditar  # noqa: E402
import extract  # noqa: E402
import validate  # noqa: E402
from test_extract_formatos import pdf_texto  # noqa: E402

PDF = RAIZ / "tests/casos/regressao/R07_tjmg_ai_176803.pdf"


def codigos(resultado):
    return {e["codigo"] for e in resultado.erros}


def claim(doc, bloco, **kw):
    c = {"id": "c1", "tipo": "precedente", "central": True,
         "proposition": "O órgão que assina o documento desproveu o recurso.",
         "status": "supported", "existence": "confirmada", "quote_status": "conferida",
         "proposition_scope": "inteiro_teor", "applicability": "Controle documental, sem novo caso jurídico.",
         "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida",
                      "obtained_via": "user_supplied_source", "local_file": doc["path"],
                      "retrieved_at": "2026-10-21", "content_hash": doc["sha256"],
                      "text_scope": "inteiro_teor", "document_id": doc["document_id"],
                      "pinpoint": {"locator": bloco["locator"], "excerpt": bloco["text"]}}]}
    c.update(kw)
    return {"schema_version": "1", "claims": [c]}


@pytest.fixture(scope="module")
def real():
    return extract.extrair(PDF)[0]


def localizar(doc, trecho):
    return next(b for b in doc["blocks"] if trecho in b["text"])


def test_real_ementa_transcrita_inclui_dispositivo_mas_nao_retorno_ao_voto(real):
    citado = localizar(real, "8. Recurso desprovido.")
    proprio = localizar(real, "À luz dessas considerações, DOU PROVIMENTO")
    assert citado["is_quote"]
    assert not proprio["is_quote"] and "atribuicao_ambigua" not in proprio["tags"]
    assert citado["section"] == proprio["section"] == "voto"
    assert real["status"] == "partial"


def test_real_validacao_recusa_atribuir_dispositivo_transcrito_ao_orgao_principal(real):
    trecho = localizar(real, "8. Recurso desprovido.")
    r = validate.validar_claims(claim(real, trecho), {real["document_id"]: real})
    assert "trecho_so_em_citacao" in codigos(r)


def test_real_resultado_proprio_e_atribuicao_explicita_da_transcricao_continuam_validos(real):
    idx = {real["document_id"]: real}
    proprio = localizar(real, "Vistos etc., acorda, em Turma")
    assert not validate.validar_claims(claim(real, proprio, proposition="O órgão deu provimento."), idx).erros
    citado = localizar(real, "8. Recurso desprovido.")
    c = claim(real, citado, cited_text=True,
              proposition="O precedente transcrito, identificado no trecho, registra recurso desprovido.")
    assert not validate.validar_claims(c, idx).erros


@pytest.mark.parametrize("via_cli", [False, True], ids=["api", "cli"])
def test_real_auditoria_bloqueia_atribuicao_indebida(real, tmp_path, via_cli):
    ep, cp = tmp_path / "extracao.json", tmp_path / "claims.json"
    ep.write_text(json.dumps({"documents": [real]}), encoding="utf-8")
    cp.write_text(json.dumps(claim(real, localizar(real, "8. Recurso desprovido."))), encoding="utf-8")
    # Declarar a leitura parcial para que a falha de G02 não seja confundida com G03.
    fp = tmp_path / "facts.json"
    fp.write_text(json.dumps({"schema_version": "1", "facts": [{"id": "l1", "kind": "lacuna",
                  "document_id": real["document_id"], "text": "Leitura parcial; conferir original."}]}), encoding="utf-8")
    if via_cli:
        cmd = [sys.executable, "-B", str(RAIZ / "scripts/auditar.py"), "auditar", "--claims", str(cp),
               "--facts", str(fp), "--extracoes", str(ep), "--tipo-entrega", "interna", "--modo", "fundamentada",
               "--saida", str(tmp_path / "qc.json")]
        p = subprocess.run(cmd, cwd=RAIZ, env=dict(os.environ, JURIS_REDE="0", PYTHONDONTWRITEBYTECODE="1"), capture_output=True)
        assert p.returncode == 1, p.stderr
        qc = json.loads(p.stdout)
    else:
        qc = auditar.auditar(fp, cp, [ep], modo="fundamentada", base=tmp_path, tipo_entrega="interna")
    gate = next(g for g in qc["gates"] if g["id"] == "G02_schema_claims")
    assert gate["resultado"] == "reprovado" and "trecho_so_em_citacao" in gate["detalhe"]
    assert qc["estado_tecnico"] == "bloqueado"


def sintetico(tmp_path, titulo="EMENTA: CONTROLE DE ATRIBUICAO.", offset=0, recuo=0,
              fechado=True, paginas_antes=0):
    def linha(y, text, citado=False):
        return (40 + offset + (recuo if citado else 0), y, text)
    paginas = [[linha(700, "Folha preliminar do ensaio.")]] * paginas_antes
    paginas += [[linha(700, "VOTO"), linha(675, "O relator passa a citar outro julgamento."),
                 linha(650, titulo), linha(625, "1. Premissa do precedente transcrito.", True),
                 linha(600, "2. Recurso desprovido no julgamento citado.", True),
                 linha(575, "(Tribunal Exemplo - Agravo, Relator(a): Pessoa Ficticia," if fechado
                       else "(Nota de leitura sem dados bibliograficos completos)", True)],
                [linha(700, "julgamento em 02/03/2024, publicacao em 05/03/2024)" if fechado
                       else "Continua a fundamentacao cuja autoria nao foi delimitada.", True),
                 linha(625, "Diante do exposto, dou provimento ao recurso em julgamento."),
                 linha(600, "Este e o resultado do orgao que assina o documento.")]]
    p = tmp_path / "ensaio.pdf"
    # O gerador mínimo recebe a sintaxe de string PDF; parênteses bibliográficos
    # devem ser escapados, sobretudo quando a referência atravessa páginas.
    paginas = [[(x, y, t.replace("\\", "\\\\").replace("(", r"\(").replace(")", r"\)"))
                for x, y, t in pagina] for pagina in paginas]
    pdf_texto(p, paginas)
    return extract.extrair(p)[0]


@pytest.mark.parametrize("titulo", ["EMENTA", "E M E N T A", "EMENTA: CONTROLE.", "Ementa: CONTROLE."])
@pytest.mark.parametrize("offset,recuo,antes", [(0, 0, 0), (27, 0, 3), (10, 100, 1)])
def test_transcricao_independe_de_caixa_recuo_e_numero_da_pagina(tmp_path, titulo, offset, recuo, antes):
    doc = sintetico(tmp_path, titulo, offset, recuo, paginas_antes=antes)
    citado = localizar(doc, "2. Recurso desprovido")
    assert citado["is_quote"]
    assert localizar(doc, "julgamento em 02/03/2024")["is_quote"]
    assert not localizar(doc, "Diante do exposto")["is_quote"]
    assert "atribuicao_ambigua" not in localizar(doc, "Diante do exposto")["tags"]


@pytest.mark.parametrize("cited_text", [False, True])
def test_sem_fechamento_seguro_ambiguidade_nao_vira_autoria_confirmada(tmp_path, cited_text):
    doc = sintetico(tmp_path, fechado=False)
    b = localizar(doc, "2. Recurso desprovido")
    assert "atribuicao_ambigua" in b["tags"]
    r = validate.validar_claims(claim(doc, b, cited_text=cited_text), {doc["document_id"]: doc})
    assert "atribuicao_ambigua" in codigos(r)


def test_ambiguidade_permanece_representavel_como_partial(tmp_path):
    doc = sintetico(tmp_path, fechado=False)
    b = localizar(doc, "2. Recurso desprovido")
    c = claim(doc, b, status="partial", reason="Autoria não delimitada.", missing="Conferência no original.")
    r = validate.validar_claims(c, {doc["document_id"]: doc})
    assert not r.erros and "atribuicao_ambigua" in {a["codigo"] for a in r.avisos}


def test_mesmo_trecho_em_duas_paginas_usa_autoria_do_localizador(tmp_path):
    doc = sintetico(tmp_path)
    citado = localizar(doc, "2. Recurso desprovido")
    outro = copy.deepcopy(citado)
    outro.update(id="proprio", page=9, page_end=9, locator="p.9", is_quote=False, quote_basis=None)
    doc["blocks"].append(outro)
    idx = {doc["document_id"]: doc}
    assert "trecho_so_em_citacao" in codigos(validate.validar_claims(claim(doc, citado), idx))
    assert not validate.validar_claims(claim(doc, outro), idx).erros


def test_trecho_que_cruza_autorias_nao_apaga_contexto_da_citacao(tmp_path):
    doc = sintetico(tmp_path)
    # Dois blocos consecutivos com origens distintas: a junção não pode transformar
    # a parte transcrita em fundamento próprio nem aceitar cited_text como certeza.
    referencia = localizar(doc, "julgamento em 02/03/2024")
    proprio = localizar(doc, "Diante do exposto")
    c = claim(doc, proprio, cited_text=True)
    c["claims"][0]["sources"][0]["pinpoint"]["excerpt"] = referencia["text"] + " " + proprio["text"]
    assert "atribuicao_ambigua" in codigos(validate.validar_claims(c, {doc["document_id"]: doc}))


@pytest.mark.parametrize("cited_text", [False, True])
def test_ocorrencias_com_autorias_distintas_na_mesma_pagina_exigem_desambiguar(tmp_path, cited_text):
    doc = sintetico(tmp_path)
    citado = localizar(doc, "2. Recurso desprovido")
    proprio = copy.deepcopy(citado)
    proprio.update(id="proprio", is_quote=False, quote_basis=None)
    doc["blocks"].append(proprio)
    c = claim(doc, citado, cited_text=cited_text)
    idx = {doc["document_id"]: doc}
    assert "atribuicao_ambigua" in codigos(validate.validar_claims(c, idx))
    # O block_id elimina a coincidência quando a página sozinha não distingue.
    c["claims"][0]["sources"][0]["block_id"] = proprio["id"]
    assert not validate.validar_claims(c, idx).erros


def test_fonte_secundaria_nao_converte_transcricao_oficial_em_fundamento_proprio(tmp_path):
    doc = sintetico(tmp_path)
    citado = localizar(doc, "2. Recurso desprovido")
    proprio = localizar(doc, "Diante do exposto")
    c = claim(doc, citado)
    secondary = copy.deepcopy(c["claims"][0]["sources"][0])
    secondary.update(source_id="s2", origin="secundaria",
                     pinpoint={"locator": proprio["locator"], "excerpt": proprio["text"]})
    c["claims"][0]["sources"].append(secondary)
    assert "trecho_so_em_citacao" in codigos(validate.validar_claims(c, {doc["document_id"]: doc}))


@pytest.mark.parametrize("fechamento_final", [False, True])
def test_referencia_interna_com_continuacao_nao_encerra_transcricao(tmp_path, fechamento_final):
    textos = ["VOTO", "O relator cita outro julgamento.", "EMENTA: ENSAIO.",
              "O julgado menciona (Relator: Pessoa Ficticia, julgamento em 2023) e prossegue na fundamentacao.",
              "2. Recurso desprovido no precedente transcrito."]
    if fechamento_final:
        textos += ["(Tribunal Exemplo, Relator: Outra Pessoa, julgamento em 2024)",
                   "Diante do exposto, dou provimento ao recurso proprio."]
    p = tmp_path / "referencia_interna.pdf"
    pdf_texto(p, [[(40, 780 - i * 35, t.replace("(", r"\(").replace(")", r"\)"))
                   for i, t in enumerate(textos)]])
    doc = extract.extrair(p)[0]
    citado = localizar(doc, "2. Recurso desprovido")
    if fechamento_final:
        assert citado["is_quote"]
        assert not localizar(doc, "Diante do exposto")["is_quote"]
    else:
        assert "atribuicao_ambigua" in citado["tags"]
        assert "atribuicao_ambigua" in codigos(validate.validar_claims(claim(doc, citado), {doc["document_id"]: doc}))


def test_cache_anterior_nao_reutiliza_atribuicao_antiga_e_preserva_historico(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    sha = hashlib.sha256(PDF.read_bytes()).hexdigest()
    antigo = cache / f"{sha[:32]}-0.4.2-{extract.PARAMS_HASH}.json"
    historico = {"document_id": "historico", "status": "ok", "blocks": [], "warnings": [],
                 "extractor_versions": {"extractor": "0.4.2"}}
    antigo.write_text(json.dumps(historico), encoding="utf-8")
    antes = antigo.read_bytes()
    doc, hit = extract.extrair(PDF, str(cache))
    assert not hit and doc["blocks"]
    assert localizar(doc, "8. Recurso desprovido.")["is_quote"]
    assert antigo.read_bytes() == antes
