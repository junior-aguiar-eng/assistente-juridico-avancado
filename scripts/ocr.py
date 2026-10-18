"""OCR opcional (Tesseract) para páginas de PDF sem texto ou cobertas por imagem.

O resultado é sempre menos confiável que texto nativo: o extrator marca os blocos com a tag "ocr", o documento sai
`partial` e o validador avisa quando um trecho citado vem de OCR. Nada aqui baixa arquivo ou instala ferramenta.

  JURIS_TESSERACT   caminho do executável (senão: PATH e pastas padrão do Windows)
  JURIS_TESSDATA    pasta com os idiomas (.traineddata); padrão: ~/.juris-skills/tessdata, se existir
"""
from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

DPI = 300
TIMEOUT_PAGINA = 180
_PADROES_WINDOWS = (r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe")


def localizar_tesseract() -> str | None:
    env = os.environ.get("JURIS_TESSERACT")
    if env and Path(env).is_file():
        return env
    achado = shutil.which("tesseract")
    if achado:
        return achado
    return next((c for c in _PADROES_WINDOWS if Path(c).is_file()), None)


def _pasta_tessdata() -> str | None:
    """JURIS_TESSDATA, senão ~/.juris-skills/tessdata (onde fica o idioma 'por' quando o Tesseract do sistema não o tem)."""
    env = os.environ.get("JURIS_TESSDATA")
    if env:
        return env
    padrao = Path.home() / ".juris-skills" / "tessdata"
    return str(padrao) if any(padrao.glob("*.traineddata")) else None


def _cmd(exe: str, *args: str) -> list[str]:
    td = _pasta_tessdata()
    return [exe, *(["--tessdata-dir", td] if td else []), *args]  # a opção vem antes dos argumentos posicionais


def idiomas(exe: str) -> list[str]:
    r = subprocess.run(_cmd(exe, "--list-langs"), capture_output=True, timeout=60)
    linhas = (r.stdout + r.stderr).decode("utf-8", "replace").splitlines()
    return [l.strip() for l in linhas[1:] if l.strip() and not l.startswith("List of")]


def escolher_idioma(exe: str) -> tuple[str, str | None]:
    """('por', None) se o português está instalado; senão ('eng', aviso) e o aviso diz o que isso custa."""
    langs = idiomas(exe)
    if "por" in langs:
        return "por", None
    if "eng" in langs:
        return "eng", ("o idioma 'por' não está instalado no Tesseract: o OCR usa 'eng' e erra acentos e cedilha; "
                       "instale por.traineddata (tessdata) para um resultado utilizável em português")
    return "", "nenhum idioma utilizável instalado no Tesseract"


def ler_paginas(exe: str, pdf_path: Path, paginas: list[int], lang: str) -> dict[int, dict]:
    """{pagina: {"linhas": [...], "confianca": média 0-100}}; linhas no formato do extrator (pontos PDF)."""
    import pdfplumber

    saida: dict[int, dict] = {}
    esc = 72.0 / DPI
    with pdfplumber.open(pdf_path) as pdf, tempfile.TemporaryDirectory() as tmp:
        for n in paginas:
            img = pdf.pages[n - 1].to_image(resolution=DPI).original
            png = Path(tmp) / f"p{n}.png"
            img.convert("RGB").save(png)
            # "-c tessedit_create_tsv=1" em vez da config "tsv": a pasta de idiomas do usuário pode não ter configs/
            r = subprocess.run(_cmd(exe, str(png), "stdout", "-l", lang, "--psm", "3", "-c", "tessedit_create_tsv=1"),
                               capture_output=True, timeout=TIMEOUT_PAGINA)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.decode("utf-8", "replace")[:200])
            linhas: dict[tuple, dict] = {}
            confs = []
            leitor = csv.DictReader(io.StringIO(r.stdout.decode("utf-8", "replace")), delimiter="\t", quoting=csv.QUOTE_NONE)
            for w in leitor:
                texto = (w.get("text") or "").strip()
                try:
                    conf = float(w["conf"])
                except (TypeError, ValueError, KeyError):
                    continue
                if not texto or conf < 0:
                    continue
                confs.append(conf)
                k = (w["block_num"], w["par_num"], w["line_num"])
                x0, t = int(w["left"]) * esc, int(w["top"]) * esc
                x1, b = x0 + int(w["width"]) * esc, t + int(w["height"]) * esc
                d = linhas.setdefault(k, {"palavras": [], "x0": x0, "x1": x1, "top": t, "bottom": b})
                d["palavras"].append(texto)
                d["x0"], d["x1"], d["top"], d["bottom"] = min(d["x0"], x0), max(d["x1"], x1), min(d["top"], t), max(d["bottom"], b)
            lista = [{"text": " ".join(d.pop("palavras")), "gap": 0.0, **d} for d in linhas.values()]
            lista.sort(key=lambda l: (round(l["top"] / 4), l["x0"]))
            saida[n] = {"linhas": lista, "confianca": round(sum(confs) / len(confs), 1) if confs else 0.0}
    return saida
