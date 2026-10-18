"""Pacotes de regras de revisão contratual: rascunhos com o texto literal da lei, sempre INATIVOS até revisão jurídica.

  gerar  --fonte CC.md --url URL --saida-dir rules/br [--lido-em AAAA-MM-DD]   escreve os pacotes-rascunho
  validar [--dir rules/br] [--fonte CC.md]                                      confere estrutura, ativação e texto literal
  listar [--dir rules/br] [--incluir-inativas]                                  regras que podem ser usadas

Uma regra só é usada se `status` for "ativa" **e** houver `revisao.revisor` e `revisao.data`. Este script nunca ativa
regra: a ativação é um ato do revisor jurídico, editando o arquivo. O texto literal vem da versão compilada do Planalto;
parâmetro de mercado ou regra de outra jurisdição não vira regra brasileira.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

NORMA = "Lei nº 10.406/2002 (Código Civil)"
RASCUNHO = "Rascunho do mantenedor técnico: pergunta de revisão não revisada por profissional do Direito."

# (id, pacote, artigo, tópico, pergunta de revisão)
CODIGO_CIVIL = [
    ("civ-412", "servicos_saas", "412", "cláusula penal: teto", "A cláusula penal ou multa ultrapassa o valor da obrigação principal?"),
    ("civ-413", "servicos_saas", "413", "cláusula penal: redução", "O valor da multa é manifestamente excessivo para a natureza e a finalidade do negócio, ou há cumprimento parcial?"),
    ("civ-421a", "servicos_saas", "421-A", "paridade e alocação de riscos", "A alocação de riscos e as regras de revisão foram previstas e respeitadas, ou há elemento concreto que afasta a presunção de paridade?"),
    ("civ-422", "servicos_saas", "422", "boa-fé", "Alguma cláusula impede a conduta de boa-fé na conclusão ou na execução do contrato?"),
    ("civ-423", "servicos_saas", "423", "adesão: ambiguidade", "O contrato é de adesão e tem cláusula ambígua ou contraditória a interpretar a favor do aderente?"),
    ("civ-424", "servicos_saas", "424", "adesão: renúncia antecipada", "O contrato é de adesão e a cláusula renuncia antecipadamente a direito resultante da natureza do negócio?"),
    ("civ-473", "servicos_saas", "473", "resilição unilateral", "A denúncia unilateral respeita o aviso e o investimento considerável feito pela outra parte?"),
    ("civ-478", "servicos_saas", "478", "onerosidade excessiva", "Em contrato de execução continuada, há cláusula que afasta a resolução por onerosidade excessiva?"),
    ("civ-598", "servicos_saas", "598", "prestação de serviço: prazo máximo", "O prazo de prestação de serviço regido pelo Código Civil passa de quatro anos?"),
]
PENDENCIAS_NDA = [
    "Lei nº 9.279/1996, art. 195, XI e XII (concorrência desleal e segredo de empresa): texto compilado ainda não lido",
    "Lei nº 13.709/2018 (LGPD), no que o NDA trata de dado pessoal: texto compilado ainda não lido",
    "Prazo de vigência do dever de sigilo e foro: sem regra legal específica; decisão do revisor jurídico",
]
_CABECALHO = re.compile(r"^(Art\.\s*\d|LIVRO|T[ÍI]TULO|CAP[ÍI]TULO|Se[cç][aã]o|Subse[cç][aã]o|\*\*)")
_REDACAO = re.compile(r"\[\((?P<n>[^\]]*?)\)\]\([^)]*\)", re.S)


def _ns(s: str) -> str:
    return " ".join(s.split())


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def extrair_artigo(texto: str, numero: str) -> dict:
    """Texto literal do artigo no Markdown compilado. Recusa artigo revogado, tachado ou não encontrado."""
    linhas = texto.splitlines()
    rx = re.compile(r"^Art\.\s*" + re.escape(numero).replace(r"\-", "-") + r"(?![\d\-A-Za-z])")
    ini = next((i for i, l in enumerate(linhas) if rx.match(l)), None)
    if ini is None:
        raise ValueError(f"art. {numero} não encontrado no texto compilado")
    fim = ini + 1
    while fim < len(linhas) and not _CABECALHO.match(linhas[fim]):
        fim += 1
    bruto = "\n".join(linhas[ini:fim])
    if "~~" in bruto or re.search(r"\(Revogad", bruto):
        raise ValueError(f"art. {numero} tachado ou revogado: não é fonte de regra")
    redacao = list(dict.fromkeys(_ns(m.group("n")) for m in _REDACAO.finditer(bruto)))
    limpo = _REDACAO.sub("", bruto)
    paragrafos = [_ns(p) for p in re.split(r"\n\s*\n", limpo) if _ns(p)]
    return {"texto_literal": "\n".join(paragrafos), "redacao": redacao}


def gerar(fonte: Path, url: str, saida_dir: Path, lido_em: str | None = None) -> dict:
    bruto = Path(fonte).read_bytes()
    texto = bruto.decode("utf-8")
    lido_em = lido_em or date.today().isoformat()
    date.fromisoformat(lido_em)
    pacotes: dict[str, list] = {}
    for rid, pacote, art, topico, pergunta in CODIGO_CIVIL:
        art_ = extrair_artigo(texto, art)
        pacotes.setdefault(pacote, []).append({
            "id": rid, "topico": topico, "pergunta_de_revisao": pergunta, "status": "inativa",
            "revisao": {"revisor": None, "data": None, "observacao": None}, "nota": RASCUNHO,
            "fonte": {"norma": NORMA, "artigo": art, "url": url, "arquivo_sha256": _sha(bruto), "lido_em": lido_em,
                      "versao": "compilada", **art_}})
    pacotes.setdefault("nda", [])
    saida_dir = Path(saida_dir)
    saida_dir.mkdir(parents=True, exist_ok=True)
    escritos = []
    for nome, regras in pacotes.items():
        obj = {"schema_version": "1", "pacote": nome, "jurisdicao": "BR", "regras": regras,
               "pendencias_de_fonte": PENDENCIAS_NDA if nome == "nda" else []}
        (saida_dir / f"{nome}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        escritos.append({"pacote": nome, "regras": len(regras)})
    return {"escritos": escritos, "status": "todas inativas e sem revisão", "lido_em": lido_em}


def _ativa(r: dict) -> bool:
    rev = r.get("revisao") or {}
    return r.get("status") == "ativa" and bool(rev.get("revisor")) and bool(rev.get("data"))


def validar(dir_: Path, fonte: Path | None = None) -> dict:
    erros, avisos = [], []
    texto = Path(fonte).read_text(encoding="utf-8") if fonte else None
    ids = set()
    for arq in sorted(Path(dir_).glob("*.json")):
        obj = json.loads(arq.read_text(encoding="utf-8"))
        for r in obj.get("regras", []):
            w = f"{arq.name}:{r.get('id')}"
            if r.get("id") in ids:
                erros.append({"codigo": "id_duplicado", "onde": w})
            ids.add(r.get("id"))
            if r.get("status") not in ("inativa", "ativa"):
                erros.append({"codigo": "status_invalido", "onde": w})
            if r.get("status") == "ativa" and not _ativa(r):
                erros.append({"codigo": "ativa_sem_revisor", "onde": w,
                              "mensagem": "regra ativa exige revisao.revisor e revisao.data"})
            f = r.get("fonte") or {}
            if not (f.get("norma") and f.get("artigo") and f.get("texto_literal") and f.get("url") and f.get("lido_em")):
                erros.append({"codigo": "fonte_incompleta", "onde": w})
            elif texto is not None:
                try:
                    atual = extrair_artigo(texto, f["artigo"])["texto_literal"]
                    if atual != f["texto_literal"]:
                        erros.append({"codigo": "texto_diverge_da_fonte", "onde": w,
                                      "mensagem": "o texto da regra não é o da versão compilada lida"})
                except ValueError as e:
                    erros.append({"codigo": "artigo_indisponivel", "onde": w, "mensagem": str(e)})
        for p in obj.get("pendencias_de_fonte", []):
            avisos.append({"codigo": "pendencia_de_fonte", "onde": arq.name, "mensagem": p})
    return {"erros": erros, "avisos": avisos, "regras": len(ids)}


def carregar(dir_: Path, pacote: str, incluir_inativas: bool = False) -> dict:
    """Regras do pacote que podem ser usadas; as demais voltam em `excluidas` com o motivo."""
    arq = Path(dir_) / f"{pacote}.json"
    if not arq.is_file():
        raise ValueError(f"pacote '{pacote}' não existe em {dir_}")
    obj = json.loads(arq.read_text(encoding="utf-8"))
    usadas, excluidas = [], []
    for r in obj.get("regras", []):
        if _ativa(r) or incluir_inativas:
            usadas.append({**r, "uso": "revisada" if _ativa(r) else "RASCUNHO_NAO_REVISADO"})
        else:
            excluidas.append({"id": r["id"], "motivo": "inativa ou sem revisor jurídico"})
    return {"pacote": pacote, "regras": usadas, "excluidas": excluidas, "pendencias_de_fonte": obj.get("pendencias_de_fonte", [])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--fonte", required=True)
    g.add_argument("--url", required=True)
    g.add_argument("--saida-dir", required=True)
    g.add_argument("--lido-em")
    v = sub.add_parser("validar")
    v.add_argument("--dir", default="rules/br")
    v.add_argument("--fonte")
    l = sub.add_parser("listar")
    l.add_argument("--dir", default="rules/br")
    l.add_argument("--pacote", default="servicos_saas")
    l.add_argument("--incluir-inativas", action="store_true")
    n = ap.parse_args(argv)
    try:
        if n.cmd == "gerar":
            res, cod = gerar(Path(n.fonte), n.url, Path(n.saida_dir), n.lido_em), 0
        elif n.cmd == "validar":
            res = validar(Path(n.dir), Path(n.fonte) if n.fonte else None)
            cod = 1 if res["erros"] else 0
        else:
            res, cod = carregar(Path(n.dir), n.pacote, n.incluir_inativas), 0
    except (ValueError, OSError, KeyError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
