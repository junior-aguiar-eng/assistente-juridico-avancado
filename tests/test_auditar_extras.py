"""Gate final: faixa de confiança, conflitos, sigilo, aviso nos relatórios, dependências e reverificação."""
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
import cronologia  # noqa: E402

CASOS = RAIZ / "tests" / "casos"
VERIF = CASOS / "verificacao_stj"
MATTER = CASOS / "triagem_stj" / "matter.json"
FACTS = CASOS / "mapeamento_stj" / "facts.json"
URL_STJ = "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202302535191"
URL_CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"


@pytest.fixture(scope="module")
def base(tmp_path_factory, claims_stj_reconferiveis):
    pasta = tmp_path_factory.mktemp("caso")
    shutil.copytree(VERIF / "fontes", pasta / "fontes")
    # Os fluxos positivos usam um subconjunto; o caso histórico completo segue bloqueado.
    (pasta / "claims.json").write_text(json.dumps(claims_stj_reconferiveis), encoding="utf-8")
    shutil.copy(FACTS, pasta / "facts.json")
    shutil.copy(MATTER, pasta / "matter.json")
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "extract.py"), "fontes/stj_inteiro_teor.pdf",
                        "fontes/cc_compilado.md", "--no-cache", "--saida", "extracao.json"], cwd=pasta,
                       capture_output=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 0
    return pasta


def escrever(base, nome, obj):
    p = base / nome
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return str(p)


def claims_de(base, manter=None, **extra):
    c = json.loads((base / "claims.json").read_text(encoding="utf-8"))
    if manter:
        c["claims"] = [x for x in c["claims"] if x["id"] in manter]
    return c


def aud(base, claims=None, facts=None, modo="analise", **kw):
    return auditar.auditar(facts, claims or str(base / "claims.json"), [str(base / "extracao.json")], modo, base=base, **kw)


def res(qc):
    return {g["id"]: g["resultado"] for g in qc["gates"]}


def detalhe(qc, gid):
    return next(g["detalhe"] for g in qc["gates"] if g["id"] == gid)


def matter_com(base, nome, **mudancas):
    m = json.loads((base / "matter.json").read_text(encoding="utf-8"))
    for caminho, valor in mudancas.items():
        alvo = m["matter"]
        *pais, folha = caminho.split(".")
        for p in pais:
            alvo = alvo.setdefault(p, {})
        if valor == "__remover__":
            alvo.pop(folha, None)
        else:
            alvo[folha] = valor
    return escrever(base, nome, m)


# ------------------------------------------------------------------ faixa de confiança
def test_faixa_alta_so_para_entrega_interna_sem_nenhuma_ressalva(base):
    limpo = escrever(base, "claims_limpo.json", claims_de(base, manter={"c001", "c004"}))
    qc = aud(base, limpo, matter=str(base / "matter.json"))
    assert qc["estado_tecnico"] == "revisao_pronta" and qc["pendencias"] == []
    assert not [g for g in qc["gates"] if g["resultado"] == "alerta"]
    assert qc["faixa"] == "alta" and qc["aprovacao_humana_obrigatoria"] is False and qc["tipo_entrega"] == "interna"


@pytest.mark.parametrize("tipo", ["cliente", "peticao", "contrato"])
def test_entrega_externa_nunca_fica_na_faixa_alta_e_exige_aprovacao_humana(base, tipo):
    limpo = escrever(base, "claims_limpo.json", claims_de(base, manter={"c001", "c004"}))
    qc = aud(base, limpo, matter=str(base / "matter.json"), tipo_entrega=tipo)
    assert qc["estado_tecnico"] == "revisao_pronta" and qc["faixa"] == "mista"
    assert qc["aprovacao_humana_obrigatoria"] is True


def test_pendencias_ou_alertas_tiram_da_faixa_alta_e_bloqueio_vira_nao_entregar(base):
    assert aud(base, matter=str(base / "matter.json"))["faixa"] == "mista"  # claims do caso têm pendências
    ruim = claims_de(base)
    ruim["claims"][0]["sources"][0]["content_hash"] = "d" * 64
    qc = aud(base, escrever(base, "claims_hash.json", ruim))
    assert qc["estado_tecnico"] == "bloqueado" and qc["faixa"] == "nao_entregar"


def test_status_so_libera_uso_com_aprovacao_quando_ela_e_obrigatoria(base, tmp_path):
    limpo = escrever(base, "claims_limpo.json", claims_de(base, manter={"c001", "c004"}))
    qc = aud(base, limpo, matter=str(base / "matter.json"))
    (base / "qc_interna.json").write_text(json.dumps(qc, ensure_ascii=False), encoding="utf-8")
    assert auditar.status(base / "qc_interna.json")["liberado_para_uso"] is True
    ext = aud(base, limpo, matter=str(base / "matter.json"), tipo_entrega="cliente")
    (base / "qc_cliente.json").write_text(json.dumps(ext, ensure_ascii=False), encoding="utf-8")
    assert auditar.status(base / "qc_cliente.json")["liberado_para_uso"] is False
    ap = auditar.aprovar(base / "qc_cliente.json", "Dra. Maria", "OAB/AL 1", "Revisei.")
    assert ap["faixa"] == "mista" and ap["tipo_entrega"] == "cliente"
    (base / "ap_cliente.json").write_text(json.dumps(ap), encoding="utf-8")
    st = auditar.status(base / "qc_cliente.json", base / "ap_cliente.json")
    assert st["revisao_humana"] == "aprovada" and st["liberado_para_uso"] is True


# ------------------------------------------------------------------ conflitos de interesse e sigilo
def test_conflito_de_interesse_cada_status(base):
    for status, extra in (("cleared", {"conflicts.method": "sistema", "conflicts.cleared_by": "Dra. X",
                                      "conflicts.cleared_date": "2026-10-01", "conflicts.checked_against": ["Usina"]}),
                          ("waived", {"conflicts.waiver_rationale": "renúncia assinada"}),
                          ("nao_aplicavel", {"conflicts.motivo": "estudo de decisão pública"})):
        m = matter_com(base, "m1.json", **{"conflicts": {}, "conflicts.status": status, **extra})
        assert res(aud(base, matter=m))["G11_conflitos_de_interesse"] == "aprovado", status


def test_conflito_pendente_ou_nao_feito_e_alerta_em_analise_e_bloqueia_em_fundamentada_e_externa(base):
    for conflitos in ({"status": "pending", "owner": "Dr. Y"}, {"status": "not-run"}):
        m = matter_com(base, "m2.json", conflicts=conflitos)
        qc = aud(base, matter=m)
        assert res(qc)["G11_conflitos_de_interesse"] == "alerta" and qc["estado_tecnico"] == "revisao_pronta"
        assert any(p["origem"] == "conflitos" for p in qc["pendencias"])
        assert res(aud(base, matter=m, modo="fundamentada"))["G11_conflitos_de_interesse"] == "reprovado"
        externa = aud(base, matter=m, tipo_entrega="cliente")
        assert res(externa)["G11_conflitos_de_interesse"] == "reprovado" and externa["faixa"] == "nao_entregar"


def test_bypass_de_conflito_registrado_e_alerta_visivel_nao_bloqueio(base):
    m = matter_com(base, "m3.json", conflicts={"status": "not-run", "override": {
        "by": "Dr. Y", "date": "2026-10-17", "rationale": "urgência; checagem em curso"}})
    qc = aud(base, matter=m, modo="fundamentada")
    assert res(qc)["G11_conflitos_de_interesse"] == "alerta" and "bypass" in detalhe(qc, "G11_conflitos_de_interesse")


def test_matter_invalido_reprova_e_entrega_externa_sem_matter_tambem(base):
    m = matter_com(base, "m4.json", as_of="2999-01-01")
    assert res(aud(base, matter=m))["G11_conflitos_de_interesse"] == "reprovado"
    externa = aud(base, tipo_entrega="peticao")
    assert res(externa)["G11_conflitos_de_interesse"] == "reprovado" and res(externa)["G12_sigilo_das_fontes"] == "reprovado"
    assert "exige o registro" in detalhe(externa, "G11_conflitos_de_interesse")


def test_sigilo_das_fontes_triagem_mista_nao_triado_e_segredo_de_justica(base):
    misto = matter_com(base, "m5.json", **{"confidentiality.privilegio": "misto"})
    fatos = json.loads((base / "facts.json").read_text(encoding="utf-8"))
    fatos["facts"][4]["priv"] = "flag"
    qc = aud(base, facts=escrever(base, "facts_priv.json", fatos), matter=misto)
    assert res(qc)["G12_sigilo_das_fontes"] == "alerta" and "1 fato(s) sem 'priv: ok'" in detalhe(qc, "G12_sigilo_das_fontes")
    assert any(p["origem"] == "sigilo" and "f005" in p["motivo"] for p in qc["pendencias"])
    nao = matter_com(base, "m6.json", **{"confidentiality.privilegio": "nao_triado"})
    assert res(aud(base, matter=nao))["G12_sigilo_das_fontes"] == "alerta"
    assert res(aud(base, matter=nao, tipo_entrega="cliente"))["G12_sigilo_das_fontes"] == "reprovado"
    segredo = matter_com(base, "m7.json", **{"confidentiality.segredo_de_justica": True})
    qc = aud(base, matter=segredo)
    assert res(qc)["G12_sigilo_das_fontes"] == "alerta" and any("art. 189" in p["motivo"] for p in qc["pendencias"])


# ------------------------------------------------------------------ aviso padrão nos relatórios
def test_relatorio_sem_aviso_padrao_alerta_e_bloqueia_em_fundamentada(base):
    com = base / "rel_com.md"
    com.write_text("# Relatório\n\nTexto.\n\n> Este material ... Não constitui parecer nem aconselhamento.\n", encoding="utf-8")
    sem = base / "rel_sem.md"
    sem.write_text("# Relatório\n\nTexto sem o aviso.\n", encoding="utf-8")
    assert res(aud(base, relatorios=[str(com)]))["G10_aviso_no_relatorio"] == "aprovado"
    qc = aud(base, relatorios=[str(com), str(sem)])
    assert res(qc)["G10_aviso_no_relatorio"] == "alerta" and "rel_sem.md" in detalhe(qc, "G10_aviso_no_relatorio")
    assert res(aud(base, relatorios=[str(sem)], modo="fundamentada"))["G10_aviso_no_relatorio"] == "reprovado"
    assert any(a["tipo"] == "relatorio" for a in qc["artefatos"])


def test_cronologia_gerada_pelo_pacote_ja_sai_com_o_aviso(base):
    cronologia.gerar(base / "facts.json", base / "t.json", base / "cron.md", matter=base / "matter.json")
    assert res(aud(base, relatorios=[str(base / "cron.md")]))["G10_aviso_no_relatorio"] == "aprovado"


# ------------------------------------------------------------------ dependências e escalação
def test_dependencia_de_proposicao_sem_apoio_e_contradicao_geram_pendencias(base):
    qc = aud(base)
    pend = {(p["origem"], p["item"]) for p in qc["pendencias"]}
    assert ("dependencia", "c005") not in pend  # c005 depende de c001, que está 'supported'
    assert ("escalar", "c002") in pend  # c002 é contradita pela fonte oficial lida
    c = claims_de(base)
    c["claims"][0]["depends_on"] = ["c003"]  # c001 passa a depender de c003, que está unverified
    qc = aud(base, escrever(base, "claims_dep.json", c))
    assert ("dependencia", "c001") in {(p["origem"], p["item"]) for p in qc["pendencias"]}
    assert "dependências em risco: c001 depende de c003 (unverified)" in detalhe(qc, "G07_proposicoes_refutadas")
    assert "contraditas pela fonte (escalar): c002" in detalhe(qc, "G07_proposicoes_refutadas")


# ------------------------------------------------------------------ reverificação das fontes
@pytest.fixture
def rede(monkeypatch, base):
    estado = {"urls": [], "falhar": set(), "trocar": {}}

    def falso(url, destino):
        estado["urls"].append(url)
        if url in estado["falhar"]:
            return {"status": "source_missing", "motivo": "desafio anti-robô: não contornado"}
        origem = estado["trocar"].get(url) or {URL_STJ: base / "fontes" / "stj_inteiro_teor.pdf",
                                               URL_CC: base / "fontes" / "cc_compilado.md"}[url.split("&")[0] if url.startswith(URL_STJ) else url]
        alvo = Path(destino) / origem.name
        shutil.copy(origem, alvo)
        return {"status": "lida", "local_file": str(alvo)}

    monkeypatch.setattr(auditar, "_baixar", falso)
    return estado


def com_urls(base):
    c = claims_de(base)
    c["claims"][3]["sources"][0]["url"] = URL_CC  # c004 (norma)
    return escrever(base, "claims_url.json", c)


def test_reverificar_fonte_igual_aprova_e_prioriza_tese_central(base, rede):
    qc = aud(base, com_urls(base), reverificar=1)
    assert res(qc)["G13_reverificacao"] == "aprovado" and detalhe(qc, "G13_reverificacao") == "1 igual(is)"
    assert rede["urls"] == [URL_STJ]  # a tese central (c001) vem primeiro


def test_reverificar_detecta_texto_diferente_alerta_em_analise_e_reprova_em_fundamentada(base, rede, tmp_path):
    outro = tmp_path / "stj_alterado.pdf"
    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(595, 842)
    with open(outro, "wb") as fh:
        w.write(fh)
    rede["trocar"][URL_STJ] = outro
    qc = aud(base, com_urls(base), reverificar=2)
    assert res(qc)["G13_reverificacao"] == "alerta" and "texto mudou em c001" in detalhe(qc, "G13_reverificacao")
    assert ("fonte_mudou", "c001") in {(p["origem"], p["item"]) for p in qc["pendencias"]}
    assert res(aud(base, com_urls(base), modo="fundamentada", reverificar=2))["G13_reverificacao"] == "reprovado"


def test_reverificar_falha_de_acesso_e_alerta_nunca_aprovacao(base, rede):
    rede["falhar"].add(URL_STJ)
    qc = aud(base, com_urls(base), reverificar=1)
    assert res(qc)["G13_reverificacao"] == "alerta" and "não foi possível reler: c001" in detalhe(qc, "G13_reverificacao")
    assert qc["estado_tecnico"] == "revisao_pronta"


def test_reverificar_sem_fonte_elegivel_e_alerta_e_zero_nao_aplica(base, rede):
    so_unverified = escrever(base, "claims_nada.json", claims_de(base, manter={"c003"}))
    assert res(aud(base, so_unverified, reverificar=3))["G13_reverificacao"] == "alerta"
    assert "G13_reverificacao" not in res(aud(base))


# ------------------------------------------------------------------ CLI
def test_cli_aceita_as_novas_opcoes(base):
    limpo = escrever(base, "claims_cli.json", claims_de(base, manter={"c001", "c004"}))
    r = subprocess.run([sys.executable, "-P", str(RAIZ / "scripts" / "auditar.py"), "auditar", "--claims", limpo,
                        "--extracoes", str(base / "extracao.json"), "--matter", str(base / "matter.json"),
                        "--tipo-entrega", "cliente", "--relatorio", str(base / "cron.md"), "--saida", str(base / "qc_cli.json")],
                       cwd=base, capture_output=True, stdin=subprocess.DEVNULL)
    qc = json.loads(r.stdout.decode("utf-8"))
    assert r.returncode == 0 and qc["tipo_entrega"] == "cliente" and qc["aprovacao_humana_obrigatoria"] is True
    assert res(qc)["G10_aviso_no_relatorio"] == "aprovado" and res(qc)["G11_conflitos_de_interesse"] == "aprovado"
