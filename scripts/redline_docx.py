"""Gera uma cópia do DOCX com as alterações propostas como controle de alterações (w:ins / w:del).

  python scripts/redline_docx.py ORIGINAL.docx EDICOES.json SAIDA.docx [--autor NOME] [--issues ISSUES.json]

EDICOES.json: {"edicoes": [
  {"acao": "substituir", "de": "trecho atual", "para": "trecho novo"},
  {"acao": "excluir", "de": "trecho atual"},
  {"acao": "inserir_apos", "ancora": "trecho existente", "texto": "texto novo"}]}

Com --issues, cada edição exige issue_id e o trecho de origem (de/ancora) deve constar literalmente
no clause_text do apontamento. O relatório identifica o arquivo e seu hash. Isso confere o vínculo
mecânico, não a base jurídica nem o mérito da alteração; valide issues.json separadamente.

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


def _carregar_issues(caminho: Path) -> tuple[dict, str]:
    conteudo = caminho.read_bytes()
    obj = json.loads(conteudo.decode("utf-8"))
    lista = obj.get("issues") if isinstance(obj, dict) else None
    if not isinstance(lista, list):
        raise ValueError("issues.json exige uma lista 'issues'")
    por_id = {}
    for it in lista:
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"].strip():
            raise ValueError("cada apontamento exige id textual não vazio")
        if it["id"] in por_id:
            raise ValueError(f"id de apontamento duplicado: {it['id']}")
        if not isinstance(it.get("clause_text"), str) or not it["clause_text"].strip():
            raise ValueError(f"apontamento {it['id']} exige clause_text não vazio")
        por_id[it["id"]] = it
    return por_id, hashlib.sha256(conteudo).hexdigest()


def _conferir_vinculo(ed: dict, por_id: dict | None) -> None:
    if por_id is None:
        raise du.EdicaoRecusada("issues_ausentes", "issue_id exige o arquivo --issues para conferir o vínculo")
    iid = ed.get("issue_id")
    if not isinstance(iid, str) or not iid.strip():
        raise du.EdicaoRecusada("issue_id_ausente", "cada edição com --issues exige issue_id textual não vazio")
    if iid not in por_id:
        raise du.EdicaoRecusada("issue_desconhecida", f"issue_id {iid} não existe no arquivo de apontamentos")
    trecho = ed.get("ancora" if ed.get("acao") == "inserir_apos" else "de")
    if not isinstance(trecho, str) or not trecho.strip() or trecho not in por_id[iid]["clause_text"]:
        raise du.EdicaoRecusada("trecho_fora_da_issue", "de/ancora deve ser trecho literal da cláusula do apontamento")


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


def aplicar(original: Path, edicoes: list[dict], saida: Path, autor: str = "Revisão (a confirmar)",
            *, issues: Path | None = None) -> dict:
    import docx

    original, saida = Path(original), Path(saida)
    if saida.resolve() == original.resolve() or (saida.exists() and saida.samefile(original)):
        raise ValueError("a saída não pode ser o próprio original")
    por_id, metadados = None, {}
    if issues is not None:
        issues = Path(issues)
        if saida.resolve() == issues.resolve() or (saida.exists() and saida.samefile(issues)):
            raise ValueError("a saída não pode sobrescrever o arquivo de apontamentos")
        por_id, hash_issues = _carregar_issues(issues)
        metadados = {"issues": str(issues), "issues_sha256": hash_issues}
    antes = _sha(original)
    doc = docx.Document(str(original))
    data = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    n_id, resultados = 9000, []
    for i, ed in enumerate(edicoes, 1):
        res = {"n": i, "acao": ed.get("acao")}
        vincular = issues is not None or "issue_id" in ed
        if vincular:
            res.update(issue_id=ed.get("issue_id"), vinculo_conferido=False)
        try:
            acao = ed.get("acao")
            if acao not in ("substituir", "excluir", "inserir_apos"):
                raise du.EdicaoRecusada("acao_invalida", f"ação desconhecida: {acao!r}")
            if vincular:
                _conferir_vinculo(ed, por_id)
                res["vinculo_conferido"] = True
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
            res["resultado"] = "aplicada"
        except du.EdicaoRecusada as e:
            res.update(resultado="recusada", codigo=e.codigo, detalhe=e.detalhe)
        resultados.append(res)
    saida.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida))
    if _sha(original) != antes:
        raise RuntimeError("o original foi alterado: abortado")
    return {**metadados, "original": str(original), "original_sha256": antes, "saida": str(saida), "saida_sha256": _sha(saida),
            "autor_das_alteracoes": autor, "aplicadas": sum(r["resultado"] == "aplicada" for r in resultados),
            "recusadas": sum(r["resultado"] == "recusada" for r in resultados), "edicoes": resultados,
            "aviso": "Alterações propostas e rastreadas: nada vale até o advogado aceitar ou rejeitar cada uma no Word."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("original")
    ap.add_argument("edicoes")
    ap.add_argument("saida")
    ap.add_argument("--autor", default="Revisão (a confirmar)")
    ap.add_argument("--issues", help="apontamentos vinculados por issue_id em cada edição; valide-os antes com contrato.py")
    n = ap.parse_args(argv)
    try:
        ed = json.loads(Path(n.edicoes).read_text(encoding="utf-8"))["edicoes"]
        res = aplicar(Path(n.original), ed, Path(n.saida), n.autor, issues=Path(n.issues) if n.issues else None)
        cod = 0 if not res["recusadas"] else 2
    except (ValueError, OSError, KeyError, RuntimeError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
