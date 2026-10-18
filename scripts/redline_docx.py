"""Gera uma cópia do DOCX com as alterações propostas como controle de alterações (w:ins / w:del).

  python scripts/redline_docx.py ORIGINAL.docx EDICOES.json SAIDA.docx [--autor NOME]

EDICOES.json: {"edicoes": [
  {"acao": "substituir", "de": "trecho atual", "para": "trecho novo"},
  {"acao": "excluir", "de": "trecho atual"},
  {"acao": "inserir_apos", "ancora": "trecho existente", "texto": "texto novo"}]}

O original nunca é alterado (a saída tem de ser outro caminho; o hash do original é conferido ao final).
Edição que não se localiza, que é ambígua ou que atravessa estrutura não suportada é recusada e relatada;
as demais são aplicadas. A saída mostra, para cada edição, o resultado. Quem decide aceitar é o advogado, no Word.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_util as du  # noqa: E402


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _elemento(tag: str, autor: str, data: str, n: int):
    from lxml import etree

    e = etree.Element(du.q(tag))
    e.set(du.q("id"), str(n))
    e.set(du.q("author"), autor)
    e.set(du.q("date"), data)
    return e


def _excluir_runs(runs, autor, data, n):
    d = _elemento("del", autor, data, n)
    runs[0].addprevious(d)
    for r in runs:
        d.append(r)  # move
        for t in r.findall(du.q("t")):
            t.tag = du.q("delText")
            t.set(du.XML_SPACE, "preserve")
    return d


def aplicar(original: Path, edicoes: list[dict], saida: Path, autor: str = "Revisão (a confirmar)") -> dict:
    import docx

    original, saida = Path(original), Path(saida)
    if saida.resolve() == original.resolve():
        raise ValueError("a saída não pode ser o próprio original")
    antes = _sha(original)
    doc = docx.Document(str(original))
    data = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    n_id, resultados = 9000, []
    for i, ed in enumerate(edicoes, 1):
        res = {"n": i, "acao": ed.get("acao")}
        try:
            acao = ed.get("acao")
            if acao in ("substituir", "excluir"):
                p = du.achar_unico(doc, ed.get("de", ""))
                runs = du.isolar(p, ed["de"])
                modelo = runs[0]
                d = _excluir_runs(runs, autor, data, n_id)
                n_id += 1
                if acao == "substituir":
                    ins = _elemento("ins", autor, data, n_id)
                    n_id += 1
                    ins.append(du.novo_run(modelo, ed.get("para", "")))
                    d.addnext(ins)
            elif acao == "inserir_apos":
                p = du.achar_unico(doc, ed.get("ancora", ""))
                runs = du.isolar(p, ed["ancora"])
                ins = _elemento("ins", autor, data, n_id)
                n_id += 1
                ins.append(du.novo_run(runs[-1], ed.get("texto", "")))
                runs[-1].addnext(ins)
            else:
                raise du.EdicaoRecusada("acao_invalida", f"ação desconhecida: {acao!r}")
            res["resultado"] = "aplicada"
        except du.EdicaoRecusada as e:
            res.update(resultado="recusada", codigo=e.codigo, detalhe=e.detalhe)
        resultados.append(res)
    saida.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida))
    if _sha(original) != antes:
        raise RuntimeError("o original foi alterado: abortado")
    return {"original": str(original), "original_sha256": antes, "saida": str(saida), "saida_sha256": _sha(saida),
            "autor_das_alteracoes": autor, "aplicadas": sum(r["resultado"] == "aplicada" for r in resultados),
            "recusadas": sum(r["resultado"] == "recusada" for r in resultados), "edicoes": resultados,
            "aviso": "Alterações propostas e rastreadas: nada vale até o advogado aceitar ou rejeitar cada uma no Word."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("original")
    ap.add_argument("edicoes")
    ap.add_argument("saida")
    ap.add_argument("--autor", default="Revisão (a confirmar)")
    n = ap.parse_args(argv)
    try:
        ed = json.loads(Path(n.edicoes).read_text(encoding="utf-8"))["edicoes"]
        res = aplicar(Path(n.original), ed, Path(n.saida), n.autor)
        cod = 0 if not res["recusadas"] else 2
    except (ValueError, OSError, KeyError, RuntimeError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
