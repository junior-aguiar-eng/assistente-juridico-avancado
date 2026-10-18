"""Apoio mecânico à revisão de contrato: pré-checagem do texto extraído e validação do issues.json.

  precheck EXTRACAO.json [--documento ID]      campos em branco, anexos ausentes, remissões quebradas, assinatura, marca de minuta
  validar-issues ISSUES.json [--extracoes E.json] [--regras rules/br --pacote servicos_saas,lgpd] [--permitir-rascunho]

A pré-checagem só aponta o que o texto mostra, com localizador: não conclui nada jurídico. O issues.json é o produto do
revisor (pessoa ou modelo); aqui só se confere se cada apontamento tem texto completo da cláusula, severidade nos dois
eixos (jurídica e negocial) e base verificável. Regra de pacote não revisada não sustenta apontamento.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regras as regras_mod  # noqa: E402

_BRANCO = re.compile(r"_{3,}|\[\s*\]|\[\s*[●•…\.]+\s*\]|\.{6,}|\[\s*(?:preencher|inserir|a definir|nome|cnpj|cpf|data|valor|xxx)[^\]]{0,40}\]|\bX{3,}\b",
                     re.I)
_ANEXO_REF = re.compile(r"\bAnexo\s+([IVXLC]+|[A-Z]|\d+)\b")
_ANEXO_TITULO = re.compile(r"^\s*ANEXO\s+([IVXLC]+|[A-Z]|\d+)\b", re.I)
_CLAUSULA_DEF = re.compile(r"^\s*(?:cl[áa]usula\s+)?(\d+(?:\.\d+)*)\s*[.\-)–:]?\s+\S", re.I)
_REMISSAO = re.compile(r"\b(?:cl[áa]usulas?|subcl[áa]usulas?|ite(?:m|ns))\s+(\d+(?:\.\d+)*)", re.I)
_LINHA_ASSINATURA = re.compile(r"_{3,}.*(contratante|contratada|contratado|testemunha|outorgante|outorgado|divulgadora|receptora|parte)"
                               r"|[A-Za-zÀ-ú .]+,\s*_{2,}\s*de\s*_{2,}(\s*de\s*_{2,})?", re.I)
_ASSINATURA = re.compile(r"assinatura|assinam|assinado|firmam|testemunha|local e data|em \d{1,2} de \w+ de \d{4}", re.I)
_MINUTA = re.compile(r"\b(minuta|rascunho|draft|vers[ãa]o para discuss[ãa]o|confidencial para negocia[çc][ãa]o)\b", re.I)
SEV_JUR = ("baixa", "media", "alta", "critica")
SEV_NEG = ("baixa", "media", "alta")
TIPOS_BASE = ("regra", "fonte", "pratica_do_cliente")


def _ns(s) -> str:
    return " ".join(str(s).split())


def _docs(obj):
    return obj.get("documents", [obj] if "blocks" in obj else [])


def precheck(extracao: dict, documento: str | None = None) -> dict:
    docs = [d for d in _docs(extracao) if documento in (None, d.get("document_id"))]
    if not docs:
        raise ValueError("documento não encontrado na extração")
    saida = []
    for d in docs:
        blocos = [b for b in d["blocks"] if b.get("section") != "rodape"]
        achados = []

        def add(tipo, b, trecho, msg):
            achados.append({"tipo": tipo, "block_id": b["id"], "locator": b.get("locator"), "page": b.get("page"),
                            "trecho": _ns(trecho)[:100], "mensagem": msg})

        definidas = set()
        titulos_anexo = set()
        for b in blocos:
            m = _CLAUSULA_DEF.match(b["text"])
            if m:
                definidas.add(m.group(1))
                partes = m.group(1).split(".")
                definidas.update(".".join(partes[:i]) for i in range(1, len(partes)))
            t = _ANEXO_TITULO.match(b["text"])
            if t:
                titulos_anexo.add(t.group(1).upper())
        for b in blocos:
            for m in ([] if _LINHA_ASSINATURA.search(b["text"]) else _BRANCO.finditer(b["text"])):  # linha de assinatura não é campo esquecido
                add("campo_em_branco", b, b["text"][max(0, m.start() - 40):m.end() + 20], "campo aparentemente não preenchido")
            if not _ANEXO_TITULO.match(b["text"]):
                for m in _ANEXO_REF.finditer(b["text"]):
                    if m.group(1).upper() not in titulos_anexo:
                        add("anexo_ausente", b, b["text"][max(0, m.start() - 40):m.end() + 30],
                            f"o texto remete ao Anexo {m.group(1)}, mas nenhum anexo com esse título está no documento extraído")
            for m in _REMISSAO.finditer(b["text"]):
                if m.group(1) not in definidas:
                    add("remissao_sem_destino", b, b["text"][max(0, m.start() - 30):m.end() + 30],
                        f"remete à cláusula/item {m.group(1)}, que não aparece numerada no documento extraído")
            if _MINUTA.search(b["text"]):
                add("marca_de_minuta", b, b["text"], "o texto se apresenta como minuta ou rascunho")
        if blocos:
            cauda = blocos[int(len(blocos) * 0.8):]
            if not any(_ASSINATURA.search(b["text"]) or _LINHA_ASSINATURA.search(b["text"]) for b in cauda):
                achados.append({"tipo": "assinatura_nao_identificada", "block_id": None, "locator": None, "page": None,
                                "trecho": "", "mensagem": "não há bloco de assinatura, testemunhas ou local e data no final do documento"})
        for w in d.get("warnings", []):
            if w["codigo"] in ("alteracoes_rastreadas", "possivel_instrucao_embutida", "pagina_sem_texto",
                               "pagina_possivelmente_digitalizada", "layout_em_colunas_ou_tabela", "parte_nao_extraida"):
                achados.append({"tipo": "aviso_da_extracao", "block_id": None, "locator": None, "page": w.get("pagina"),
                                "trecho": "", "mensagem": f"{w['codigo']}: {w['detalhe'][:140]}"})
        cont: dict[str, int] = {}
        for a in achados:
            cont[a["tipo"]] = cont.get(a["tipo"], 0) + 1
        saida.append({"document_id": d.get("document_id"), "path": d.get("path"), "status_da_extracao": d.get("status"),
                      "achados": achados, "contagem": cont})
    return {"documentos": saida,
            "observacao": "A pré-checagem aponta o que o texto mostra; não é conclusão jurídica. Confira cada achado no original."}


def validar_issues(obj: dict, extracoes: dict | None = None, regras_dir: Path | None = None, pacote: str | None = None,
                   permitir_rascunho: bool = False) -> dict:
    erros, avisos = [], []
    rascunho_usado = False

    def e(cod, onde, msg):
        erros.append({"codigo": cod, "onde": onde, "mensagem": msg})

    def a(cod, onde, msg):
        avisos.append({"codigo": cod, "onde": onde, "mensagem": msg})

    lista = obj.get("issues")
    if not isinstance(lista, list):
        e("estrutura", "issues", "falta a lista 'issues'")
        return {"erros": erros, "avisos": avisos}
    if not obj.get("posicao_da_parte"):
        e("posicao_ausente", "posicao_da_parte", "diga qual parte o revisor representa: a severidade depende dela")
    regras = {}
    if regras_dir is not None and pacote:
        for nome in [x.strip() for x in str(pacote).split(",") if x.strip()]:  # vários pacotes: "servicos_saas,lgpd"
            carregado = regras_mod.carregar(Path(regras_dir), nome, incluir_inativas=True)
            regras.update({r["id"]: r for r in carregado["regras"]})
    blocos = {}
    if extracoes is not None:
        for d in _docs(extracoes):
            for b in d["blocks"]:
                blocos[(d.get("document_id"), b.get("locator"))] = b
    ids = set()
    for i, it in enumerate(lista):
        w = f"issues[{i}]({it.get('id')})"
        if not it.get("id") or it["id"] in ids:
            e("id_invalido", w, "id obrigatório e único")
        ids.add(it.get("id"))
        for campo in ("titulo", "descricao", "clausula", "clause_text"):
            if not str(it.get(campo) or "").strip():
                e("campo_ausente", w, f"falta '{campo}'")
        sj, sn = it.get("severidade_juridica"), it.get("severidade_negocial")
        if sj not in SEV_JUR:
            e("severidade_juridica_invalida", w, f"use uma de {SEV_JUR}")
        if sn not in SEV_NEG:
            e("severidade_negocial_invalida", w, f"use uma de {SEV_NEG}")
        base = it.get("base")
        if not isinstance(base, list) or not base:
            if sj in ("alta", "critica"):
                e("alta_sem_base", w, "severidade jurídica alta ou crítica exige ao menos uma base")
            else:
                a("sem_base", w, "apontamento sem base: é opinião do revisor")
            base = []
        juridica = 0
        for k, b in enumerate(base):
            wb = f"{w}.base[{k}]"
            tipo = b.get("tipo")
            if tipo not in TIPOS_BASE:
                e("tipo_de_base_invalido", wb, f"tipo deve ser um de {TIPOS_BASE}; parâmetro de mercado ou regra de outra jurisdição não é base")
            elif tipo == "regra":
                r = regras.get(b.get("rule_id"))
                if regras_dir is None:
                    a("regra_nao_conferida", wb, "sem --regras: a regra citada não foi conferida")
                elif r is None:
                    e("regra_inexistente", wb, f"rule_id {b.get('rule_id')} não existe no pacote")
                elif r.get("uso") != "revisada":
                    (a if permitir_rascunho else e)("regra_nao_revisada" if not permitir_rascunho else "regra_rascunho", wb,
                                                    "a regra é rascunho sem revisão jurídica: não sustenta apontamento")
                    rascunho_usado = True  # nunca conta como base jurídica, nem com --permitir-rascunho
                else:
                    juridica += 1
            elif tipo == "fonte":
                faltam = [k for k in ("source_id", "retrieved_at", "locator") if not str(b.get(k) or "").strip()]
                if not (b.get("local_file") or b.get("url")):
                    faltam.append("local_file ou url")
                try:
                    date.fromisoformat(str(b.get("retrieved_at")))
                except ValueError:
                    if "retrieved_at" not in faltam:
                        faltam.append("retrieved_at (AAAA-MM-DD)")
                if faltam:
                    e("fonte_incompleta", wb, "base do tipo fonte exige uma fonte realmente lida: falta " + ", ".join(faltam))
                else:
                    juridica += 1
            elif tipo == "pratica_do_cliente" and not str(b.get("nota") or "").strip():
                e("pratica_sem_nota", wb, "descreva a prática ou política do cliente em 'nota'")
        if sj == "critica" and juridica == 0:
            e("critica_sem_base_juridica", w, "severidade crítica não pode apoiar-se só em prática do cliente ou em regra não revisada")
        loc = it.get("locators") or ([it["locator"]] if it.get("locator") else [])
        if not loc:
            e("localizador_ausente", w, "informe 'locator' (ou 'locators') da cláusula")
        elif extracoes is not None:
            doc_id = it.get("document_id")
            encontrados = [blocos.get((doc_id, l)) for l in loc]
            if not doc_id or any(b is None for b in encontrados):
                e("clausula_nao_localizada", w, "document_id/locator não existem na extração")
            else:
                texto_bloco = _ns(" ".join(b["text"] for b in encontrados))
                ct = _ns(it.get("clause_text", ""))
                if ct and ct not in texto_bloco:
                    e("clausula_fora_do_documento", w, "clause_text não é trecho literal dos blocos indicados")
                elif ct and len(ct) < 0.9 * len(texto_bloco):
                    e("clausula_truncada", w, "clause_text cobre menos de 90% dos blocos indicados: cite a cláusula inteira")
        else:
            a("trecho_nao_conferido", w, "sem --extracoes: o texto da cláusula não foi conferido com o documento")
        if it.get("sugestao") and _ns(it["sugestao"]) == _ns(it.get("clause_text", "")):
            e("sugestao_igual_ao_original", w, "a sugestão repete a cláusula")
    return {"erros": erros, "avisos": avisos, "issues": len(lista), "rascunho": rascunho_usado,
            "entregavel": not erros and not rascunho_usado}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("precheck")
    p.add_argument("extracao")
    p.add_argument("--documento")
    v = sub.add_parser("validar-issues")
    v.add_argument("issues")
    v.add_argument("--extracoes")
    v.add_argument("--regras")
    v.add_argument("--pacote", default="servicos_saas", help="um ou mais pacotes separados por vírgula, ex.: servicos_saas,lgpd")
    v.add_argument("--permitir-rascunho", action="store_true")
    n = ap.parse_args(argv)
    try:
        if n.cmd == "precheck":
            res, cod = precheck(json.loads(Path(n.extracao).read_text(encoding="utf-8")), n.documento), 0
        else:
            ext = json.loads(Path(n.extracoes).read_text(encoding="utf-8")) if n.extracoes else None
            res = validar_issues(json.loads(Path(n.issues).read_text(encoding="utf-8")), ext,
                                 Path(n.regras) if n.regras else None, n.pacote, n.permitir_rascunho)
            cod = 1 if res["erros"] else 0
    except (ValueError, OSError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
