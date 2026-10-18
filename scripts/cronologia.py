"""Cronologia a partir do facts.json: ordena sem inventar precisão e sem calcular prazos.

  gerar    --facts F.json --saida-json T.json --saida-md C.md [--matter M.json] [--formato trabalho|fatos]
           [--anterior T0.json] [--extracoes E.json ...] [--janela-meses N] [--incluir-sinalizados]
  conferir --facts F.json --timeline T.json     diz se a cronologia ainda corresponde aos fatos

Cada data vira um intervalo (dia, mês ou ano inteiros). Fatos cujos intervalos se sobrepõem têm
ordem incerta e são marcados; fatos sem data (ou com data indefinida) vão para uma seção própria.
Alegação continua alegação: o tipo de cada fato aparece na cronologia. A relevância (alta, média,
baixa) é marca do revisor, aplicada da perspectiva do papel do cliente registrado no matter.json.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402

SCHEMA_VERSION = "1"
ROTULO = {"documentado": "documentado", "alegacao": "alegação", "inferencia": "inferência", "lacuna": "lacuna",
          "informado": "informado pelo usuário, sem documento"}
PRECISAO = {"dia": "dia", "mes": "mês", "ano": "ano", "indefinida": "indefinida"}
SELO_REL = {"alta": "ALTA", "media": "média", "baixa": "baixa"}
NOTA = ("Nenhum prazo foi calculado: a cronologia só ordena. Datas parciais mantêm a precisão do documento "
        "(mês ou ano inteiros). Entre fatos com intervalos que se sobrepõem a ordem é incerta (marcados com ⚠).")
RAIZ = Path(__file__).resolve().parent.parent
AVISO_PADRAO = next(l.lstrip("> ").strip() for l in (RAIZ / "shared" / "aviso-padrao.md").read_text(encoding="utf-8").splitlines()
                    if l.startswith("> "))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _intervalo(d):
    if not isinstance(d, dict) or not d.get("iso") or d.get("precision") == "indefinida":
        return None
    iso, prec = d["iso"], d["precision"]
    if prec == "dia":
        return iso, iso
    if prec == "mes":
        ultimo = calendar.monthrange(int(iso[:4]), int(iso[5:7]))[1]
        return f"{iso}-01", f"{iso}-{ultimo:02d}"
    return f"{iso}-01-01", f"{iso}-12-31"


def _fonte(f):
    s = f.get("source")
    return {"document_id": s.get("document_id"), "locator": s.get("locator")} if isinstance(s, dict) else None


def _outras(f):
    return [{"document_id": o.get("document_id"), "locator": o.get("locator")}
            for o in (f.get("other_sources") or []) if isinstance(o, dict)]


def _extras(f):
    return {"relevancia": f.get("relevancia"), "relevancia_motivo": f.get("relevancia_motivo"),
            "relevancia_incerta": bool(f.get("relevancia_incerta")), "priv": f.get("priv"), "outras_fontes": _outras(f)}


def _janelas(entradas, meses):
    if not meses or len(entradas) < 2:
        return []
    saida, fim_max, id_fim = [], date.fromisoformat(entradas[0]["intervalo"]["fim"]), entradas[0]["fact_id"]
    for e in entradas[1:]:
        ini = date.fromisoformat(e["intervalo"]["inicio"])
        gap = (ini - fim_max).days / 30.44
        if gap >= meses:
            saida.append({"entre": [id_fim, e["fact_id"]], "de": fim_max.isoformat(), "ate": ini.isoformat(),
                          "meses": round(gap, 1)})
        fim = date.fromisoformat(e["intervalo"]["fim"])
        if fim > fim_max:
            fim_max, id_fim = fim, e["fact_id"]
    return saida


def construir(facts_obj: dict, facts_sha: str, matter: dict | None = None, janela_meses: int = 0) -> dict:
    fatos = [f for f in facts_obj["facts"] if isinstance(f, dict)]
    datados, sem_data = [], []
    for f in fatos:
        iv = _intervalo(f.get("date"))
        if iv is None:
            d = f.get("date")
            motivo = "sem campo 'date'" if not isinstance(d, dict) else f"data indefinida ({d.get('original')!r})"
            sem_data.append({"fact_id": f["id"], "kind": f["kind"], "text": f["text"], "motivo": motivo,
                             "fonte": _fonte(f), **_extras(f)})
        else:
            datados.append((iv, f))
    datados.sort(key=lambda x: (x[0][0], x[0][1], x[1]["id"]))
    entradas = []
    for i, (iv, f) in enumerate(datados):
        incertos = [g["id"] for j, (iv2, g) in enumerate(datados)
                    if j != i and iv[0] <= iv2[1] and iv2[0] <= iv[1]]
        e = {"ordem": i + 1, "fact_id": f["id"], "kind": f["kind"], "text": f["text"],
             "data": {k: f["date"].get(k) for k in ("original", "iso", "precision")},
             "intervalo": {"inicio": iv[0], "fim": iv[1]}, "ordem_incerta_com": sorted(incertos),
             "fonte": _fonte(f), "conflitos": sorted(f.get("conflicts_with") or []), **_extras(f)}
        if f["kind"] == "alegacao":
            e["alleged_by"] = f.get("alleged_by")
        entradas.append(e)
    conflitos = sorted({tuple(sorted((f["id"], x))) for f in fatos for x in (f.get("conflicts_with") or [])})
    lacunas = [{"fact_id": f["id"], "text": f["text"]} for f in fatos if f["kind"] == "lacuna"]
    por_kind = {k: sum(1 for f in fatos if f["kind"] == k) for k in ROTULO}
    m = (matter or {}).get("matter", {}) if matter else {}
    enquadramento = {"papel": m.get("client_role"), "fato_chave": m.get("fato_chave"),
                     "privilegio": (m.get("confidentiality") or {}).get("privilegio"),
                     "segredo_de_justica": (m.get("confidentiality") or {}).get("segredo_de_justica")} if matter else None
    return {"schema_version": SCHEMA_VERSION, "matter_id": facts_obj.get("matter_id") or m.get("matter_id"),
            "facts_sha256": facts_sha, "politica": NOTA, "enquadramento": enquadramento,
            "entradas": entradas, "sem_data": sem_data, "conflitos": [list(c) for c in conflitos], "lacunas": lacunas,
            "janelas_sem_eventos": _janelas(entradas, janela_meses),
            "resumo": {"total": len(fatos), "com_data": len(entradas), "sem_data": len(sem_data),
                       "ordem_incerta": sum(1 for e in entradas if e["ordem_incerta_com"]), "por_kind": por_kind,
                       "por_relevancia": {k: sum(1 for f in fatos if f.get("relevancia") == k) for k in SELO_REL}}}


def diferencas(atual: dict, anterior: dict) -> dict:
    a = {e["fact_id"]: e for e in atual["entradas"]} | {s["fact_id"]: s for s in atual["sem_data"]}
    b = {e["fact_id"]: e for e in anterior["entradas"]} | {s["fact_id"]: s for s in anterior["sem_data"]}
    chaves = ("text", "kind", "data", "fonte", "relevancia", "priv")
    return {"novos": sorted(set(a) - set(b)), "removidos": sorted(set(b) - set(a)),
            "alterados": sorted(k for k in set(a) & set(b) if any(a[k].get(c) != b[k].get(c) for c in chaves)),
            "reordenados": sorted(e["fact_id"] for e in atual["entradas"]
                                  if e["fact_id"] in b and "ordem" in b[e["fact_id"]] and e["ordem"] != b[e["fact_id"]]["ordem"])}


def _cel(s) -> str:
    return " ".join(str(s or "").split()).replace("|", "\\|")


def _fonte_txt(f, outras=()) -> str:
    base = f"{f['document_id']}, {f['locator']}" if f else "sem fonte (inferência, informado ou lacuna)"
    extra = "; ".join(f"{o['document_id']}, {o['locator']}" for o in outras)
    return base + (f"; também em {extra}" if extra else "")


def _sinalizado(item, posture) -> bool:
    """Em triagem mista, só 'ok' circula; sem marca vale como 'review' (sinalizar demais se corrige)."""
    return posture == "misto" and item.get("priv") not in ("ok",)


def _tipo(e) -> str:
    return ROTULO[e["kind"]] + (f" de {_cel(e.get('alleged_by'))}" if e["kind"] == "alegacao" else "")


def _selo(e) -> str:
    if not e.get("relevancia"):
        return ""
    return SELO_REL[e["relevancia"]] + (" (incerta)" if e.get("relevancia_incerta") else "")


def _cabecalho(t, formato, n_avisos, incluir_sinalizados):
    enq = t.get("enquadramento") or {}
    L = [f"# {'Exposição de fatos' if formato == 'fatos' else 'Cronologia'}{': ' + t['matter_id'] if t.get('matter_id') else ''}", "",
         f"_{t['politica']}_", ""]
    L.append(f"Fatos: {t['resumo']['total']} ({t['resumo']['com_data']} datados, {t['resumo']['sem_data']} sem data); "
             f"ordem incerta em {t['resumo']['ordem_incerta']}. Gerada de `facts.json` com sha256 `{t['facts_sha256'][:12]}`"
             f", versão {t.get('versao', 1)}.")
    if enq.get("papel"):
        L.append(f"Marcas de relevância aplicadas da perspectiva do papel registrado: **{enq['papel']}**."
                 + (f" Fato-chave: {_cel(enq['fato_chave'])}" if enq.get("fato_chave") else ""))
    if enq.get("privilegio"):
        L.append(f"Triagem de sigilo profissional das fontes: **{enq['privilegio']}**."
                 + (" Entradas sem marca `priv: ok` aparecem como sinalizadas (🔒)." if enq["privilegio"] == "misto" else ""))
    if enq.get("segredo_de_justica"):
        L.append("⚠ Processo em segredo de justiça: confirme que a circulação deste material é permitida (CPC, art. 189).")
    if incluir_sinalizados:
        L.append("⚠ Incluídas, por reconhecimento expresso do usuário, as entradas sinalizadas quanto a sigilo (`--incluir-sinalizados`).")
    if n_avisos:
        L.append(f"O validador emitiu {n_avisos} aviso(s) sobre os fatos: veja a saída de `validate.py`.")
    return L


def markdown(t: dict, mudancas=None, n_avisos=0, formato="trabalho", incluir_sinalizados=False) -> str:
    posture = (t.get("enquadramento") or {}).get("privilegio")
    L = _cabecalho(t, formato, n_avisos, incluir_sinalizados)
    if formato == "fatos":
        L += ["", "## Fatos, em ordem", ""]
        n = 0
        for e in t["entradas"]:
            if e["relevancia"] not in ("alta", "media") or e["kind"] == "lacuna":
                continue
            if _sinalizado(e, posture) and not incluir_sinalizados:
                continue
            n += 1
            data = e["data"]["original"]
            abre = {"documentado": f"Em {data}", "alegacao": f"Segundo {_cel(e.get('alleged_by'))}, em {data}",
                    "inferencia": f"Infere-se, em {data}", "informado": f"Informado pelo usuário, sem documento, em {data}"}[e["kind"]]
            L.append(f"{n}. {abre} ({PRECISAO[e['data']['precision']]}): {_cel(e['text'])} "
                     f"[{_tipo(e)}; fonte: {_cel(_fonte_txt(e['fonte'], e['outras_fontes']))}]"
                     + (" ⚠ ordem incerta." if e["ordem_incerta_com"] else ""))
        if not n:
            L.append("- nenhum fato com relevância alta ou média liberado para esta exposição")
        ocultos = sum(1 for e in t["entradas"] if e["relevancia"] in ("alta", "media") and _sinalizado(e, posture)
                      and not incluir_sinalizados)
        if ocultos:
            L.append(f"\n{ocultos} entrada(s) relevante(s) ficaram de fora por sinalização de sigilo; use `--incluir-sinalizados` "
                     "só com a confirmação do advogado.")
        fora = []
        for e in t["entradas"]:
            if e["relevancia"] not in ("alta", "media"):
                fora.append(f"{e['fact_id']} (relevância {e['relevancia'] or 'não avaliada'})")
            elif e["kind"] == "lacuna":
                fora.append(f"{e['fact_id']} (lacuna)")
            elif _sinalizado(e, posture) and not incluir_sinalizados:
                fora.append(f"{e['fact_id']} (sigilo)")
        fora += [f"{s['fact_id']} (sem data)" for s in t["sem_data"]]
        if fora:
            L += ["", "## Fora desta exposição", "",
                  "Registrados no `facts.json`, mas não narrados acima: " + "; ".join(fora) + "."]
    else:
        mista = posture == "misto"
        L += ["", "## Em ordem", "", "| # | Data | Precisão | Tipo | Relevância | " + ("Sigilo | " if mista else "") + "Fato | Fonte |",
              "|---|---|---|---|---|" + ("---|" if mista else "") + "---|---|"]
        for e in t["entradas"]:
            marca = " ⚠" if e["ordem_incerta_com"] else ""
            sig = f" {'🔒' if _sinalizado(e, posture) else 'ok'} |" if mista else ""
            L.append(f"| {e['ordem']}{marca} | {_cel(e['data']['original'])} | {PRECISAO[e['data']['precision']]} | "
                     f"{_tipo(e)} | {_selo(e)} |{sig} {_cel(e['text'])} | {_cel(_fonte_txt(e['fonte'], e['outras_fontes']))} |")
        if not t["entradas"]:
            L.append("| | | | | | " + ("| " if mista else "") + "nenhum fato datado | |")
        incertas = [e for e in t["entradas"] if e["ordem_incerta_com"]]
        if incertas:
            L += ["", "### Ordem incerta", ""]
            L += [f"- {e['fact_id']} pode vir antes ou depois de {', '.join(e['ordem_incerta_com'])} (intervalos se sobrepõem)."
                  for e in incertas]
        chave = [e for e in t["entradas"] + [s for s in t["sem_data"]] if e.get("relevancia") == "alta"]
        if chave:
            L += ["", "## Eventos de relevância alta", ""]
            L += [f"- **{e['fact_id']}** ({e['data']['original'] if 'data' in e else 'sem data'}): {_cel(e['text'])}. "
                  f"Por que importa: {_cel(e.get('relevancia_motivo'))}" + (" _(relevância incerta: confirmar)_" if e.get("relevancia_incerta") else "")
                  for e in chave]
        if t.get("janelas_sem_eventos"):
            L += ["", "## Janelas sem eventos", ""]
            L += [f"- entre {a} e {b}: {j['meses']} meses sem fato registrado (de {j['de']} a {j['ate']}). "
                  "Pode ser lacuna de documentos: confira antes de concluir qualquer coisa."
                  for j in t["janelas_sem_eventos"] for a, b in [j["entre"]]]
        L += ["", "## Sem data", ""]
        L += [f"- **{s['fact_id']}** ({ROTULO[s['kind']]}): {_cel(s['text'])} — {s['motivo']}" for s in t["sem_data"]] or ["- nenhum"]
        L += ["", "## Conflitos entre fatos", ""]
        L += [f"- {a} x {b}: o pacote não decide qual vale." for a, b in t["conflitos"]] or ["- nenhum registrado"]
        L += ["", "## Lacunas", ""]
        L += [f"- {x['fact_id']}: {_cel(x['text'])}" for x in t["lacunas"]] or ["- nenhuma registrada"]
    if mudancas is not None:
        L += ["", "## Alterações desde a versão anterior", ""]
        L += [f"- {nome}: {', '.join(ids) if ids else 'nenhum'}" for nome, ids in mudancas.items()]
    L += ["", "---", "", f"> {AVISO_PADRAO}"]
    return "\n".join(L) + "\n"


def gerar(facts_path, saida_json, saida_md, anterior=None, extracoes=(), matter=None, formato="trabalho",
          incluir_sinalizados=False, janela_meses=0):
    fp = Path(facts_path)
    obj = json.loads(fp.read_text(encoding="utf-8"))
    idx = validate.carregar_extracoes(extracoes) if extracoes else None
    r = validate.validar_facts(obj, idx)
    if r.erros:
        raise ValueError("facts.json inválido: " + "; ".join(f"{e['codigo']} em {e['caminho']}" for e in r.erros[:6]))
    m = json.loads(Path(matter).read_text(encoding="utf-8")) if matter else None
    if m is not None:
        rm = validate.validar_matter(m, idx)
        if rm.erros:
            raise ValueError("matter.json inválido: " + "; ".join(f"{e['codigo']} em {e['caminho']}" for e in rm.erros[:6]))
        if formato == "fatos" and (m["matter"].get("confidentiality") or {}).get("privilegio") in (None, "nao_triado"):
            raise ValueError("as fontes não passaram por triagem de sigilo (privilegio ausente ou nao_triado): triar antes de "
                             "gerar a exposição de fatos")
    if formato == "fatos" and m is None:
        raise ValueError("a exposição de fatos exige --matter (papel, sigilo e privilégio entram no cabeçalho e no filtro)")
    t = construir(obj, _sha(fp), m, janela_meses)
    ant = json.loads(Path(anterior).read_text(encoding="utf-8")) if anterior else None
    t["versao"] = (ant.get("versao", 1) + 1) if ant else 1
    mud = diferencas(t, ant) if ant else None
    if mud is not None:
        t["mudancas"] = mud
    t["formato"] = formato
    t["gerado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    Path(saida_json).write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(saida_md).write_text(markdown(t, mud, len(r.avisos), formato, incluir_sinalizados), encoding="utf-8")
    return {"entradas": len(t["entradas"]), "sem_data": len(t["sem_data"]), "avisos_do_validador": len(r.avisos),
            "versao": t["versao"], "resumo": t["resumo"], "mudancas": mud}


def conferir(facts_path, timeline_path) -> dict:
    fp = Path(facts_path)
    t = json.loads(Path(timeline_path).read_text(encoding="utf-8"))
    novo = construir(json.loads(fp.read_text(encoding="utf-8")), _sha(fp))
    igual_arquivo = t.get("facts_sha256") == novo["facts_sha256"]
    igual_conteudo = all(t.get(k) == novo[k] for k in ("entradas", "sem_data", "lacunas", "conflitos"))
    # vale o conteúdo, não os bytes: reformatar o JSON sem mudar nenhum fato não invalida a cronologia
    return {"atualizada": igual_conteudo, "facts_json_mudou": not igual_arquivo, "conteudo_diverge": not igual_conteudo}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--facts", required=True)
    g.add_argument("--saida-json", required=True)
    g.add_argument("--saida-md", required=True)
    g.add_argument("--anterior")
    g.add_argument("--extracoes", action="append", default=[])
    g.add_argument("--matter")
    g.add_argument("--formato", choices=("trabalho", "fatos"), default="trabalho")
    g.add_argument("--incluir-sinalizados", action="store_true")
    g.add_argument("--janela-meses", type=int, default=0)
    c = sub.add_parser("conferir")
    c.add_argument("--facts", required=True)
    c.add_argument("--timeline", required=True)
    n = ap.parse_args(argv)
    try:
        if n.cmd == "gerar":
            res, cod = gerar(n.facts, n.saida_json, n.saida_md, n.anterior, n.extracoes, n.matter, n.formato,
                             n.incluir_sinalizados, n.janela_meses), 0
        else:
            res = conferir(n.facts, n.timeline)
            cod = 0 if res["atualizada"] else 1
    except (ValueError, OSError, KeyError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
