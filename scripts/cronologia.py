"""Cronologia a partir do facts.json: ordena sem inventar precisão e sem calcular prazos.

  gerar    --facts F.json --saida-json T.json --saida-md C.md [--anterior T0.json] [--extracoes E.json ...]
  conferir --facts F.json --timeline T.json     diz se a cronologia ainda corresponde aos fatos

Cada data vira um intervalo (dia, mês ou ano inteiros). Fatos cujos intervalos se sobrepõem têm
ordem incerta e são marcados; fatos sem data (ou com data indefinida) vão para uma seção própria.
Alegação continua alegação: o tipo de cada fato aparece na cronologia.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402

SCHEMA_VERSION = "1"
ROTULO = {"documentado": "documentado", "alegacao": "alegação", "inferencia": "inferência", "lacuna": "lacuna"}
PRECISAO = {"dia": "dia", "mes": "mês", "ano": "ano", "indefinida": "indefinida"}
NOTA = ("Nenhum prazo foi calculado: a cronologia só ordena. Datas parciais mantêm a precisão do documento "
        "(mês ou ano inteiros). Entre fatos com intervalos que se sobrepõem a ordem é incerta (marcados com ⚠).")


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


def construir(facts_obj: dict, facts_sha: str) -> dict:
    fatos = [f for f in facts_obj["facts"] if isinstance(f, dict)]
    datados, sem_data = [], []
    for f in fatos:
        iv = _intervalo(f.get("date"))
        if iv is None:
            d = f.get("date")
            motivo = "sem campo 'date'" if not isinstance(d, dict) else f"data indefinida ({d.get('original')!r})"
            sem_data.append({"fact_id": f["id"], "kind": f["kind"], "text": f["text"], "motivo": motivo,
                             "fonte": _fonte(f)})
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
             "fonte": _fonte(f), "conflitos": sorted(f.get("conflicts_with") or [])}
        if f["kind"] == "alegacao":
            e["alleged_by"] = f.get("alleged_by")
        entradas.append(e)
    conflitos = sorted({tuple(sorted((f["id"], x))) for f in fatos for x in (f.get("conflicts_with") or [])})
    lacunas = [{"fact_id": f["id"], "text": f["text"]} for f in fatos if f["kind"] == "lacuna"]
    por_kind = {k: sum(1 for f in fatos if f["kind"] == k) for k in ROTULO}
    return {"schema_version": SCHEMA_VERSION, "matter_id": facts_obj.get("matter_id"),
            "facts_sha256": facts_sha, "politica": NOTA, "entradas": entradas, "sem_data": sem_data,
            "conflitos": [list(c) for c in conflitos], "lacunas": lacunas,
            "resumo": {"total": len(fatos), "com_data": len(entradas), "sem_data": len(sem_data),
                       "ordem_incerta": sum(1 for e in entradas if e["ordem_incerta_com"]), "por_kind": por_kind}}


def diferencas(atual: dict, anterior: dict) -> dict:
    a = {e["fact_id"]: e for e in atual["entradas"]} | {s["fact_id"]: s for s in atual["sem_data"]}
    b = {e["fact_id"]: e for e in anterior["entradas"]} | {s["fact_id"]: s for s in anterior["sem_data"]}
    chaves = ("text", "kind", "data", "fonte")
    return {"novos": sorted(set(a) - set(b)), "removidos": sorted(set(b) - set(a)),
            "alterados": sorted(k for k in set(a) & set(b) if any(a[k].get(c) != b[k].get(c) for c in chaves)),
            "reordenados": sorted(e["fact_id"] for e in atual["entradas"]
                                  if e["fact_id"] in b and "ordem" in b[e["fact_id"]] and e["ordem"] != b[e["fact_id"]]["ordem"])}


def _cel(s) -> str:
    return " ".join(str(s or "").split()).replace("|", "\\|")


def _fonte_txt(f) -> str:
    return f"{f['document_id']}, {f['locator']}" if f else "sem fonte (inferência ou lacuna)"


def markdown(t: dict, mudancas=None, n_avisos=0) -> str:
    L = [f"# Cronologia{': ' + t['matter_id'] if t.get('matter_id') else ''}", "",
         f"_{t['politica']}_", "",
         f"Fatos: {t['resumo']['total']} ({t['resumo']['com_data']} datados, {t['resumo']['sem_data']} sem data); "
         f"ordem incerta em {t['resumo']['ordem_incerta']}. Gerada de `facts.json` com sha256 `{t['facts_sha256'][:12]}`."]
    if n_avisos:
        L.append(f"O validador emitiu {n_avisos} aviso(s) sobre os fatos: veja a saída de `validate.py`.")
    L += ["", "## Em ordem", "", "| # | Data | Precisão | Tipo | Fato | Fonte |", "|---|---|---|---|---|---|"]
    for e in t["entradas"]:
        marca = " ⚠" if e["ordem_incerta_com"] else ""
        tipo = ROTULO[e["kind"]] + (f" de {_cel(e.get('alleged_by'))}" if e["kind"] == "alegacao" else "")
        L.append(f"| {e['ordem']}{marca} | {_cel(e['data']['original'])} | {PRECISAO[e['data']['precision']]} | "
                 f"{tipo} | {_cel(e['text'])} | {_cel(_fonte_txt(e['fonte']))} |")
    if not t["entradas"]:
        L.append("| | | | | nenhum fato datado | |")
    incertas = [e for e in t["entradas"] if e["ordem_incerta_com"]]
    if incertas:
        L += ["", "### Ordem incerta", ""]
        L += [f"- {e['fact_id']} pode vir antes ou depois de {', '.join(e['ordem_incerta_com'])} (intervalos se sobrepõem)."
              for e in incertas]
    L += ["", "## Sem data", ""]
    L += [f"- **{s['fact_id']}** ({ROTULO[s['kind']]}): {_cel(s['text'])} — {s['motivo']}" for s in t["sem_data"]] or ["- nenhum"]
    L += ["", "## Conflitos entre fatos", ""]
    L += [f"- {a} x {b}: o pacote não decide qual vale." for a, b in t["conflitos"]] or ["- nenhum registrado"]
    L += ["", "## Lacunas", ""]
    L += [f"- {x['fact_id']}: {_cel(x['text'])}" for x in t["lacunas"]] or ["- nenhuma registrada"]
    if mudancas is not None:
        L += ["", "## Alterações desde a versão anterior", ""]
        L += [f"- {nome}: {', '.join(ids) if ids else 'nenhum'}" for nome, ids in mudancas.items()]
    return "\n".join(L) + "\n"


def gerar(facts_path, saida_json, saida_md, anterior=None, extracoes=()):
    fp = Path(facts_path)
    obj = json.loads(fp.read_text(encoding="utf-8"))
    idx = validate.carregar_extracoes(extracoes) if extracoes else None
    r = validate.validar_facts(obj, idx)
    if r.erros:
        raise ValueError("facts.json inválido: " + "; ".join(f"{e['codigo']} em {e['caminho']}" for e in r.erros[:6]))
    t = construir(obj, _sha(fp))
    mud = diferencas(t, json.loads(Path(anterior).read_text(encoding="utf-8"))) if anterior else None
    if mud is not None:
        t["mudancas"] = mud
    t["gerado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    Path(saida_json).write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(saida_md).write_text(markdown(t, mud, len(r.avisos)), encoding="utf-8")
    return {"entradas": len(t["entradas"]), "sem_data": len(t["sem_data"]), "avisos_do_validador": len(r.avisos),
            "resumo": t["resumo"], "mudancas": mud}


def conferir(facts_path, timeline_path) -> dict:
    fp = Path(facts_path)
    t = json.loads(Path(timeline_path).read_text(encoding="utf-8"))
    novo = construir(json.loads(fp.read_text(encoding="utf-8")), _sha(fp))
    igual_arquivo = t.get("facts_sha256") == novo["facts_sha256"]
    igual_conteudo = t.get("entradas") == novo["entradas"] and t.get("sem_data") == novo["sem_data"]
    return {"atualizada": igual_arquivo and igual_conteudo,
            "facts_json_mudou": not igual_arquivo, "conteudo_diverge": not igual_conteudo}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--facts", required=True)
    g.add_argument("--saida-json", required=True)
    g.add_argument("--saida-md", required=True)
    g.add_argument("--anterior")
    g.add_argument("--extracoes", action="append", default=[])
    c = sub.add_parser("conferir")
    c.add_argument("--facts", required=True)
    c.add_argument("--timeline", required=True)
    n = ap.parse_args(argv)
    try:
        if n.cmd == "gerar":
            res, cod = gerar(n.facts, n.saida_json, n.saida_md, n.anterior, n.extracoes), 0
        else:
            res = conferir(n.facts, n.timeline)
            cod = 0 if res["atualizada"] else 1
    except (ValueError, OSError, KeyError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
