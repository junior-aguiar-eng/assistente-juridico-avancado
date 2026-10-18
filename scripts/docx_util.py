"""Edição de texto em parágrafos DOCX preservando a formatação: localizar um trecho que atravessa runs e isolá-lo.

Só enxerga runs diretos do parágrafo com um único w:t (texto simples). Hiperlinks, campos, tabulações e
alterações rastreadas existentes funcionam como barreira: trecho que as atravessa é recusado, não adivinhado.
"""
from __future__ import annotations

import copy

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
BARREIRA = "\x00"
_IGNORADOS = {"pPr", "bookmarkStart", "bookmarkEnd", "proofErr"}


class EdicaoRecusada(ValueError):
    def __init__(self, codigo: str, detalhe: str):
        super().__init__(f"{codigo}: {detalhe}")
        self.codigo = codigo
        self.detalhe = detalhe


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def _simples(r) -> bool:
    ts = r.findall(q("t"))
    return len(ts) == 1 and all(c.tag in (q("rPr"), q("t")) for c in r)


def mapa(p_el) -> list[tuple]:
    """[(elemento_ou_None, texto)] na ordem do parágrafo; None = barreira."""
    saida = []
    for c in p_el:
        nome = c.tag.rsplit("}", 1)[-1]
        if nome in _IGNORADOS:
            continue
        if nome == "r" and _simples(c):
            saida.append((c, c.find(q("t")).text or ""))
        else:
            saida.append((None, BARREIRA))
    return saida


def texto_simples(p_el) -> str:
    return "".join(t for _, t in mapa(p_el))


def _preservar(t) -> None:
    t.set(XML_SPACE, "preserve")


def _cortar(p_el, pos: int) -> None:
    """Garante uma fronteira de run na posição `pos` do texto do parágrafo."""
    acc = 0
    for el, txt in mapa(p_el):
        if el is not None and acc < pos < acc + len(txt):
            corte = pos - acc
            direita = copy.deepcopy(el)
            el.find(q("t")).text = txt[:corte]
            direita.find(q("t")).text = txt[corte:]
            _preservar(el.find(q("t")))
            _preservar(direita.find(q("t")))
            el.addnext(direita)
            return
        acc += len(txt)


def isolar(p_el, trecho: str, ocorrencia: int | None = None):
    """Isola `trecho` em runs próprios e devolve a lista de runs que o compõem.

    Sem `ocorrencia`, o trecho tem de ser único no parágrafo; com ela, usa a n-ésima (0 = primeira)."""
    if not trecho:
        raise EdicaoRecusada("trecho_vazio", "o trecho a localizar está vazio")
    total = texto_simples(p_el)
    ini = -1
    for _ in range((ocorrencia or 0) + 1):
        ini = total.find(trecho, ini + 1)
        if ini < 0:
            break
    if ini < 0:
        raise EdicaoRecusada("nao_localizado", f"'{trecho[:60]}' não está no texto simples do parágrafo")
    if ocorrencia is None and total.find(trecho, ini + 1) >= 0:
        raise EdicaoRecusada("ambiguo", f"'{trecho[:60]}' aparece mais de uma vez no parágrafo: use um trecho maior")
    fim = ini + len(trecho)
    if BARREIRA in total[ini:fim]:
        raise EdicaoRecusada("trecho_cruza_estrutura", "o trecho atravessa hiperlink, campo, tabulação ou alteração existente")
    _cortar(p_el, ini)
    _cortar(p_el, fim)
    acc, runs = 0, []
    for el, txt in mapa(p_el):
        if el is not None and txt and acc >= ini and acc + len(txt) <= fim:
            runs.append(el)
        acc += len(txt)
    return runs


def paragrafos(doc):
    """Parágrafos do corpo e de tabelas (elementos w:p), na ordem do documento."""
    return list(doc.element.body.iter(q("p")))


def achar_unico(doc, trecho: str):
    """Parágrafo que contém `trecho` no texto simples; recusa zero ocorrência ou mais de uma no documento."""
    achados = [p for p in paragrafos(doc) if trecho and trecho in texto_simples(p)]
    if not achados:
        raise EdicaoRecusada("nao_localizado", f"'{trecho[:60]}' não foi encontrado no texto simples do documento")
    n = sum(texto_simples(p).count(trecho) for p in achados)
    if n > 1:
        raise EdicaoRecusada("ambiguo", f"'{trecho[:60]}' aparece {n} vezes no documento: use um trecho maior")
    return achados[0]


def novo_run(modelo, texto: str):
    """Run novo com a formatação de `modelo`."""
    r = copy.deepcopy(modelo)
    for c in list(r):
        if c.tag != q("rPr"):
            r.remove(c)
    from lxml import etree

    t = etree.SubElement(r, q("t"))
    t.text = texto
    _preservar(t)
    return r
