"""Preenchimento de modelo DOCX com campos de procedência explícita.

  lint  CAMPOS.json [--modelo M.docx] [--extracoes E.json]     confere os campos (e os {{marcadores}} do modelo)
  gerar CAMPOS.json MODELO.docx SAIDA.docx [--extracoes E.json] [--aceitar-inferidos]

Estados de cada campo:
  extraido        valor copiado de um documento: exige fonte {document_id, locator, trecho}; o valor tem de aparecer,
                  literalmente, dentro do trecho (e o trecho, no bloco extraído, quando há extracao.json)
  informado       dito pelo usuário: exige informado_em (data) e fala (a mensagem do usuário, literal), que contém o valor;
                  pedido genérico ("ponha o mais provável") não é informação do campo
  inferido        deduzido: exige razao; só entra no documento com --aceitar-inferidos, sempre marcado
  pendente        sem prova: o marcador fica no documento, destacado
  conflito        duas ou mais fontes divergem (candidatos): o marcador fica, destacado
  nao_se_aplica   exige motivo; entra como marca destacada para o advogado decidir o destino da cláusula
Nenhum campo é preenchido por memória do modelo: sem prova, o marcador {{campo}} vira [PENDENTE: campo].
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_util as du  # noqa: E402

ESTADOS = ("extraido", "informado", "inferido", "pendente", "conflito", "nao_se_aplica")
_NOME = re.compile(r"^[a-z][a-z0-9_]*$")
_MARCADOR = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def _ns(s: str) -> str:
    return " ".join(str(s).split())


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def marcadores(modelo: Path) -> list[str]:
    import docx

    doc = docx.Document(str(modelo))
    achados = []
    for p in du.paragrafos(doc):
        achados += _MARCADOR.findall(du.texto_simples(p))
    return achados


def _bloco(extracoes, document_id, locator):
    """Bloco do documento; None se o documento não existe, False se o localizador não existe nele."""
    for d in extracoes.get("documents", [extracoes] if "blocks" in extracoes else []):
        if d.get("document_id") == document_id:
            for b in d["blocks"]:
                loc = str(b.get("locator", ""))
                if loc == locator or loc.endswith("." + str(locator)):
                    return b
            return False
    return None


_SENSIVEL = re.compile(r"poder|capacidade|represent|assin", re.I)
_CPF = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
_CNPJ = re.compile(r"(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)")


def _checar_identificadores(extracoes, valor, fonte, onde, avisar):
    """CPF/CNPJ extraído: avisa se os documentos trazem outro identificador do mesmo tipo (pode ser outra pessoa, ou conflito)."""
    for rx, nome in ((_CNPJ, "CNPJ"), (_CPF, "CPF")):
        if rx.fullmatch(_ns(valor)):
            digitos = re.sub(r"\D", "", valor)
            outros = {}
            for d in extracoes.get("documents", [extracoes] if "blocks" in extracoes else []):
                for b in d["blocks"]:
                    for m in rx.finditer(b["text"]):
                        if re.sub(r"\D", "", m.group()) != digitos:
                            outros.setdefault(re.sub(r"\D", "", m.group()), []).append(f"{d.get('document_id')}:{b.get('locator')}")
            if outros:
                avisar("possivel_conflito", onde, f"os documentos trazem {len(outros)} outro(s) {nome} além deste "
                       f"(ex.: {next(iter(outros.values()))[0]}): confirme de quem é cada um; se for o mesmo campo, use 'conflito'")
            return


def lint(campos: dict, modelo: Path | None = None, extracoes: dict | None = None) -> dict:
    erros, avisos = [], []

    def e(cod, onde, msg):
        erros.append({"codigo": cod, "onde": onde, "mensagem": msg})

    def a(cod, onde, msg):
        avisos.append({"codigo": cod, "onde": onde, "mensagem": msg})

    lista = campos.get("campos")
    if not isinstance(lista, list):
        e("estrutura", "campos", "falta a lista 'campos'")
        return {"erros": erros, "avisos": avisos}
    vistos = set()
    for i, c in enumerate(lista):
        nome = c.get("nome")
        w = f"campos[{i}]({nome})"
        if not isinstance(nome, str) or not _NOME.match(nome):
            e("nome_invalido", w, "nome em minúsculas, dígitos e _, começando por letra")
            continue
        if nome in vistos:
            e("nome_duplicado", w, "nome repetido")
        vistos.add(nome)
        est = c.get("estado")
        if est not in ESTADOS:
            e("estado_invalido", w, f"estado deve ser um de {ESTADOS}")
            continue
        valor = c.get("valor")
        if est in ("extraido", "informado", "inferido") and (not isinstance(valor, str) or not valor.strip()):
            e("valor_ausente", w, f"estado {est} exige 'valor' (texto não vazio)")
        if est in ("pendente", "conflito", "nao_se_aplica") and valor not in (None, ""):
            e("valor_em_estado_sem_valor", w, f"estado {est} não leva 'valor': campo sem prova não pode ter valor")
        if est == "extraido":
            f = c.get("fonte") or {}
            if not all(isinstance(f.get(k), str) and f.get(k).strip() for k in ("document_id", "locator", "trecho")):
                e("fonte_incompleta", w, "extraido exige fonte com document_id, locator e trecho")
            elif isinstance(valor, str) and _ns(valor) not in _ns(f["trecho"]):
                e("valor_fora_do_trecho", w, "o valor não aparece, literalmente, no trecho citado")
            elif extracoes is not None:
                b = _bloco(extracoes, f["document_id"], f["locator"])
                if b is None:
                    e("documento_desconhecido", w, f"document_id {f['document_id']} não está na extração")
                elif b is False:
                    e("localizador_inexistente", w, f"localizador {f['locator']} não existe no documento")
                elif _ns(f["trecho"]) not in _ns(b["text"]):
                    e("trecho_fora_do_bloco", w, "o trecho não está no bloco indicado da extração")
                else:
                    _checar_identificadores(extracoes, valor, f, w, a)
            if isinstance(valor, str) and len(_ns(f.get("trecho", ""))) < len(_ns(valor)) + 12:
                a("trecho_minimo", w, "o trecho é praticamente só o valor: cite a frase que mostra de quem ou do que é o dado")
        elif est == "informado":
            try:
                date.fromisoformat(str(c.get("informado_em")))
            except ValueError:
                e("informado_em_invalido", w, "informado exige 'informado_em' (data AAAA-MM-DD)")
            fala = c.get("fala")
            if not isinstance(fala, str) or not fala.strip():
                e("informado_sem_fala", w, "informado exige 'fala': a mensagem do usuário, literal, que traz o valor")
            elif isinstance(valor, str) and _ns(valor) not in _ns(fala):
                e("valor_fora_da_fala", w, "o valor não aparece na fala do usuário citada: dado que o usuário não deu não é 'informado'")
        elif est == "inferido":
            if not str(c.get("razao") or "").strip():
                e("razao_ausente", w, "inferido exige 'razao'")
            if _SENSIVEL.search(nome):
                e("inferido_em_campo_sensivel", w, "poderes, capacidade e representação não se inferem: peça o dado ou deixe pendente")
            a("campo_inferido", w, "valor deduzido: só entra no documento com --aceitar-inferidos e sempre marcado")
        elif est in ("pendente", "nao_se_aplica"):
            if not str(c.get("motivo") or "").strip():
                e("motivo_ausente", w, f"{est} exige 'motivo'")
        elif est == "conflito":
            cand = c.get("candidatos")
            if not isinstance(cand, list) or len({_ns(x.get("valor", "")) for x in cand if isinstance(x, dict)}) < 2:
                e("candidatos_insuficientes", w, "conflito exige 2+ candidatos com valores diferentes")
    if modelo is not None:
        usados = marcadores(Path(modelo))
        for m in sorted(set(usados) - vistos):
            e("marcador_sem_campo", m, "o modelo tem o marcador {{" + m + "}} mas não há campo com esse nome")
        for m in sorted(vistos - set(usados)):
            a("campo_sem_uso", m, "o campo não aparece no modelo")
    return {"erros": erros, "avisos": avisos}


def _marca(texto: str, modelo_run):
    from lxml import etree

    r = du.novo_run(modelo_run, texto)
    rpr = r.find(du.q("rPr"))
    if rpr is None:
        rpr = etree.Element(du.q("rPr"))
        r.insert(0, rpr)
    h = etree.SubElement(rpr, du.q("highlight"))
    h.set(du.q("val"), "yellow")
    return r


def gerar(campos: dict, modelo: Path, saida: Path, extracoes: dict | None = None, aceitar_inferidos: bool = False) -> dict:
    import docx

    modelo, saida = Path(modelo), Path(saida)
    if saida.resolve() == modelo.resolve():
        raise ValueError("a saída não pode ser o próprio modelo")
    l = lint(campos, modelo, extracoes)
    if l["erros"]:
        return {"gerado": False, "motivo": "campos com erro: corrija antes de gerar", **l}
    antes = _sha(modelo)
    por_nome = {c["nome"]: c for c in campos["campos"]}
    doc = docx.Document(str(modelo))
    contagem: dict[str, int] = {}
    pend: dict[str, str] = {}
    for p in du.paragrafos(doc):
        while True:
            m = _MARCADOR.search(du.texto_simples(p))
            if not m:
                break
            c = por_nome[m.group(1)]
            est = c["estado"]
            runs = du.isolar(p, m.group(0), 0)
            if est in ("extraido", "informado"):
                novo_run = du.novo_run(runs[0], c["valor"])
            elif est == "inferido" and aceitar_inferidos:
                novo_run = _marca(f"{c['valor']} [INFERIDO: confirmar]", runs[0])
            else:
                rot = {"nao_se_aplica": "NÃO SE APLICA", "conflito": "CONFLITO",
                       "inferido": "PENDENTE (inferido não aceito)"}.get(est, "PENDENTE")
                novo_run = _marca(f"[{rot}: {c['nome']}]", runs[0])
                pend[c["nome"]] = est
            runs[0].addprevious(novo_run)
            for r in runs:
                r.getparent().remove(r)
            contagem[c["nome"]] = contagem.get(c["nome"], 0) + 1
    saida.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida))
    if _sha(modelo) != antes:
        raise RuntimeError("o modelo foi alterado: abortado")
    n_campos = len(campos["campos"])
    sem_prova = [c["nome"] for c in campos["campos"] if c["estado"] in ("pendente", "conflito", "inferido")]
    escalar = []
    if n_campos and len(sem_prova) / n_campos > 1 / 3:
        escalar.append(f"mais de um terço dos campos sem prova ({len(sem_prova)} de {n_campos})")
    escalar += [f"campo sensível sem prova: {n}" for n in sem_prova if _SENSIVEL.search(n)]
    return {"gerado": True, "saida": str(saida), "saida_sha256": _sha(saida), "modelo_sha256": antes,
            "preenchidos": {n: k for n, k in contagem.items() if n not in pend}, "marcados_no_documento": pend,
            "completo": not pend, "escalar": escalar, "avisos": l["avisos"],
            "aviso": "Campos em amarelo precisam de decisão. Valor 'extraido' vale só enquanto o documento de origem for o mesmo."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    li = sub.add_parser("lint")
    li.add_argument("campos")
    li.add_argument("--modelo")
    li.add_argument("--extracoes")
    g = sub.add_parser("gerar")
    g.add_argument("campos")
    g.add_argument("modelo")
    g.add_argument("saida")
    g.add_argument("--extracoes")
    g.add_argument("--aceitar-inferidos", action="store_true")
    n = ap.parse_args(argv)
    try:
        campos = json.loads(Path(n.campos).read_text(encoding="utf-8"))
        ext = json.loads(Path(n.extracoes).read_text(encoding="utf-8")) if n.extracoes else None
        if n.cmd == "lint":
            res = lint(campos, Path(n.modelo) if n.modelo else None, ext)
            cod = 1 if res["erros"] else 0
        else:
            res = gerar(campos, Path(n.modelo), Path(n.saida), ext, n.aceitar_inferidos)
            cod = 0 if res.get("gerado") else 1
    except (ValueError, OSError, RuntimeError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
