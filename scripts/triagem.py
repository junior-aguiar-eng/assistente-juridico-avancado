"""Apoio mecânico à triagem de um caso: pasta de trabalho, inventário dos originais e números de processo.

  init CASO --id ID                 cria input/ derived/ outputs/ runs/ e um matter.json a preencher
  inventario CASO [--travar]        lista os arquivos de input/ com sha256; compara com o inventário anterior;
                                    --travar marca os originais como somente leitura
  processos EXTRACAO.json [...]     acha números CNJ nos textos extraídos e confere o dígito verificador
  privacidade EXTRACAO.json [...]   dados pessoais (CPF, CNPJ, cartão, e-mail, telefone) com valor mascarado
  capacidades                       o que este ambiente consegue fazer (bibliotecas, fetch_oficial, git)

A triagem em si (perguntas ao usuário, papel, jurisdição, sigilo) é feita pela skill br-triagem;
os dados vão para matter.json e são validados por validate.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cnj  # noqa: E402
import extract  # noqa: E402
import privacidade as privacidade_mod  # noqa: E402

PASTAS = ("input", "derived", "outputs", "runs")
_CNJ = re.compile(r"(?<![\d.-])\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}(?![\d-])|(?<!\d)\d{20}(?!\d)")


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def modelo_matter(matter_id: str) -> dict:
    """matter.json a preencher: os campos obrigatórios ficam nulos até a triagem e o validador os cobra."""
    return {"schema_version": "1", "matter": {
        "matter_id": matter_id, "objective": None, "client_role": None,
        "jurisdiction": {"ramo": None, "tribunal": None, "uf": None},
        "as_of": None, "facts_date": None,
        "confidentiality": {"nivel": None, "consultas_externas": None, "politica_modelo": None, "privilegio": None,
                            "segredo_de_justica": None},
        "conflicts": None, "partes": [],
        "capabilities": {"ocr": False}, "processos": [], "documentos": [], "lacunas_iniciais": []}}


def init(caso: Path, matter_id: str) -> dict:
    criadas = []
    for nome in PASTAS:
        d = caso / nome
        if not d.exists():
            d.mkdir(parents=True)
            criadas.append(nome)
    mj = caso / "matter.json"
    existia = mj.exists()
    if not existia:
        mj.write_text(json.dumps(modelo_matter(matter_id), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"caso": str(caso), "pastas_criadas": criadas, "matter_json": "mantido" if existia else "criado (a preencher)"}


def inventario(caso: Path, travar: bool = False) -> dict:
    entrada = caso / "input"
    if not entrada.is_dir():
        raise ValueError(f"não existe {entrada}: rode 'init' primeiro")
    atual = {}
    arquivos = []
    for raiz, dirs, nomes in os.walk(entrada, followlinks=False):  # nunca entra em diretório que é link
        dirs[:] = [d for d in dirs if not (Path(raiz) / d).is_symlink()]
        for d in os.listdir(raiz):
            if (Path(raiz) / d).is_symlink() and (Path(raiz) / d).is_dir():
                arquivos.append(Path(raiz) / d)  # o link de diretório é registrado, não percorrido
        arquivos += [Path(raiz) / n for n in nomes]
    for p in sorted(set(arquivos)):
        rel = p.relative_to(entrada).as_posix()
        if p.is_symlink():  # link: não lê o destino (pode apontar para fora da pasta do caso)
            atual[rel] = {"sha256": None, "bytes": 0, "extensao": p.suffix.lower(), "extraivel": False,
                          "link_simbolico": True}
            continue
        atual[rel] = {"sha256": _sha(p), "bytes": p.stat().st_size, "extensao": p.suffix.lower(),
                      "extraivel": p.suffix.lower() in extract.EXTENSOES}
        if travar:
            os.chmod(p, stat.S_IREAD)
    arq = caso / "derived" / "inventario.json"
    anterior = json.loads(arq.read_text(encoding="utf-8"))["arquivos"] if arq.is_file() else None
    mudancas = {"novos": [], "removidos": [], "alterados": []}
    if anterior is not None:
        mudancas = {"novos": sorted(set(atual) - set(anterior)), "removidos": sorted(set(anterior) - set(atual)),
                    "alterados": sorted(k for k in atual if k in anterior and atual[k]["sha256"] != anterior[k]["sha256"])}
    saida = {"gerado_em": _agora(), "travado": travar, "arquivos": atual,
             "nao_extraiveis": sorted(k for k, v in atual.items() if not v["extraivel"]),
             "mudancas_desde_o_inventario_anterior": mudancas if anterior is not None else None}
    (caso / "derived").mkdir(exist_ok=True)
    # o inventário anterior é a referência dos originais: só é regravado se nada mudou nos que já existiam
    if anterior is None or not (mudancas["alterados"] or mudancas["removidos"]):
        arq.write_text(json.dumps({"gerado_em": saida["gerado_em"], "arquivos": atual}, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    else:
        saida["aviso"] = "original alterado ou removido: o inventário de referência foi mantido; investigue antes de seguir"
    return saida


def processos(extracoes) -> dict:
    achados: dict[str, list] = {}
    for e in extracoes:
        obj = json.loads(Path(e).read_text(encoding="utf-8"))
        for d in obj.get("documents", [obj] if "blocks" in obj else []):
            for b in d.get("blocks", []):
                for m in _CNJ.finditer(b["text"]):
                    n = cnj.parse(m.group())
                    achados.setdefault(n.formatado if n else m.group(), []).append(
                        {"document_id": d.get("document_id"), "block_id": b["id"], "locator": b.get("locator")})
    validos, candidatos = [], []
    for num, oc in sorted(achados.items()):
        ok, motivo = cnj.validar(num)
        reg = {"numero": cnj.parse(num).formatado if cnj.parse(num) else num, "ocorrencias": oc}
        if ok:
            validos.append(reg)
        else:
            candidatos.append({**reg, "motivo": motivo})
    return {"validos": validos, "candidatos_invalidos": candidatos,
            "observacao": "candidato inválido pode ser outro número de 20 dígitos ou erro de digitação: confira no original"}


def privacidade(extracoes) -> dict:
    """Dados pessoais nos textos extraídos, com localizador e valor mascarado (nunca o valor completo)."""
    por_tipo: dict[str, dict] = {t: {"total": 0, "documentos": {}} for t in privacidade_mod.TIPOS}
    for e in extracoes:
        obj = json.loads(Path(e).read_text(encoding="utf-8"))
        for d in obj.get("documents", [obj] if "blocks" in obj else []):
            for b in d.get("blocks", []):
                for a in privacidade_mod.detectar(b["text"]):
                    t = por_tipo[a["tipo"]]
                    t["total"] += 1
                    doc = t["documentos"].setdefault(d.get("document_id"), {"path": d.get("path"), "ocorrencias": []})
                    doc["ocorrencias"].append({"locator": b.get("locator"), "block_id": b["id"], "mascara": a["mascara"]})
    com_dado = {t: v for t, v in por_tipo.items() if v["total"]}
    return {"achados": com_dado, "total_geral": sum(v["total"] for v in por_tipo.values()),
            "recomendacoes": [
                "Revise este relatório antes de compartilhar a pasta do caso: os valores aqui estão mascarados.",
                "extracao.json, o cache e os textos extraídos contêm os valores completos: mantenha-os só na máquina.",
                "Em facts.json e claims.json, troque o número por [...] no trecho citado.",
                "Se o caso exige consulta externa, use apenas termos genéricos (sem CPF, CNPJ, nomes ou número de processo)."]}


def capacidades() -> dict:
    """O que este ambiente consegue fazer. Ferramentas MCP e navegador do app dependem da sessão e não são detectáveis aqui."""
    import importlib.util
    import shutil

    def lib(nome):
        return importlib.util.find_spec(nome) is not None

    fetch = Path(__file__).resolve().parent / "fetch_oficial.py"
    if not fetch.is_file():
        fetch = Path.home() / ".claude" / "scripts" / "fetch_oficial.py"
    import ocr as ocr_mod

    exe = ocr_mod.localizar_tesseract()
    lang, aviso_ocr = ("", "Tesseract não encontrado") if not exe else ocr_mod.escolher_idioma(exe)
    return {"detectado": {"python": sys.version.split()[0], "pdfplumber": lib("pdfplumber"), "python_docx": lib("docx"),
                          "lxml": lib("lxml"), "fetch_oficial": fetch.is_file(), "git": shutil.which("git") is not None},
            "ocr": bool(lang), "ocr_idioma": lang or None, "ocr_aviso": aviso_ocr, "tesseract": exe,
            "observacao": "ocr verdadeiro significa que 'extract.py --ocr' pode ser usado (resultado sempre partial e marcado). "
                          "Registre forgelex e navegador_app no matter.json só depois de confirmar que as ferramentas "
                          "existem nesta sessão."}


def resumir_pecas(extracoes, pecas=(), *, anteriores=(), exigir=False):
    """Organização declarada e suas restrições; não propõe nem confere fronteiras."""
    import pecas_uso
    return pecas_uso.carregar_contexto(extracoes, pecas, anteriores=anteriores, exigir=exigir).resumo()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("privacidade")
    pv.add_argument("extracoes", nargs="+")
    sub.add_parser("capacidades")
    i = sub.add_parser("init")
    i.add_argument("caso")
    i.add_argument("--id", required=True)
    v = sub.add_parser("inventario")
    v.add_argument("caso")
    v.add_argument("--travar", action="store_true")
    p = sub.add_parser("processos")
    p.add_argument("extracoes", nargs="+")
    pp = sub.add_parser("pecas", help="resumo dos inventários vinculados, sem transcrever documentos")
    pp.add_argument("--extracoes", action="append", default=[])
    import pecas_uso
    pecas_uso.adicionar_argumentos(pp)
    n = ap.parse_args(argv)
    try:
        if n.cmd == "init":
            res = init(Path(n.caso), n.id)
        elif n.cmd == "inventario":
            res = inventario(Path(n.caso), n.travar)
        elif n.cmd == "privacidade":
            res = privacidade(n.extracoes)
        elif n.cmd == "capacidades":
            res = capacidades()
        elif n.cmd == "pecas":
            res = resumir_pecas(n.extracoes, n.pecas, anteriores=n.pecas_anterior, exigir=n.exigir_pecas)
        else:
            res = processos(n.extracoes)
        cod = 0 if res.get("valido", True) else 1
    except (ValueError, OSError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
