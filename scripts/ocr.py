"""OCR opcional (Tesseract) para páginas de PDF sem texto ou cobertas por imagem.

O resultado é sempre menos confiável que texto nativo: o extrator marca os blocos com a tag "ocr", o documento sai
`partial` e o validador avisa quando um trecho citado vem de OCR. Nada aqui baixa arquivo ou instala ferramenta.

  JURIS_TESSERACT   caminho do executável (senão: PATH e pastas padrão do Windows)
  JURIS_TESSDATA    pasta com os idiomas (.traineddata); padrão: ~/.juris-skills/tessdata, se existir
"""
from __future__ import annotations

import csv
import hashlib
import re
import io
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

DPI = 300
MAX_PIXELS = 10_000_000
MAX_LADO = 4000
PERFIS = ("padrao", "mediana")
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


def configuracao(perfil: str = "padrao") -> dict:
    """Identifica política, motor e modelo; sem modelo identificado não reutiliza cache."""
    if perfil not in PERFIS:
        raise ValueError("Perfil de OCR desconhecido.")
    from importlib import metadata
    bibliotecas = {}
    for nome in ("Pillow", "pypdfium2"):
        try:
            bibliotecas[nome] = metadata.version(nome)
        except metadata.PackageNotFoundError:
            bibliotecas[nome] = "ausente"
    cfg = {"bibliotecas": bibliotecas, "perfil": perfil, "dpi": DPI, "max_pixels": MAX_PIXELS, "max_lado": MAX_LADO,
           "psm": 3, "motor_versao": None, "motor_sha256": None, "idioma": None,
           "modelo_sha256": None, "cache_verificavel": False}
    exe = localizar_tesseract()
    if not exe:
        return cfg
    try:
        lang, _ = escolher_idioma(exe)
        cfg["idioma"] = lang or None
        r = subprocess.run(_cmd(exe, "--list-langs"), capture_output=True, timeout=30)
        linhas = (r.stdout+r.stderr).decode("utf-8","replace").splitlines()
        pasta = _pasta_tessdata()
        if not pasta and linhas:
            match = re.search(r'in "([^"]+)"', linhas[0])
            pasta = match.group(1) if match else None
        v = subprocess.run([exe,"--version"],capture_output=True,timeout=30)
        versao = (v.stdout+v.stderr).decode("utf-8","replace").splitlines()
        cfg["motor_versao"] = versao[0] if v.returncode == 0 and versao else None
        with Path(exe).open("rb") as f:
            cfg["motor_sha256"] = hashlib.file_digest(f,"sha256").hexdigest()
        if pasta and lang:
            with (Path(pasta)/(lang+".traineddata")).open("rb") as f:
                cfg["modelo_sha256"] = hashlib.file_digest(f,"sha256").hexdigest()
        cfg["cache_verificavel"] = bool(cfg["modelo_sha256"] and cfg["motor_versao"] and cfg["motor_sha256"])
    except (OSError, ValueError, subprocess.SubprocessError):
        cfg["cache_verificavel"] = False
    return cfg


def resolucao_limitada(largura: float, altura: float, dpi: float = DPI) -> float:
    if not all(math.isfinite(v) and v > 0 for v in (largura, altura, dpi)):
        raise ValueError("Dimensões e resolução devem ser positivas e finitas.")
    # Margem para o arredondamento a pixels do renderizador.
    return min(dpi, 72 * (MAX_LADO - 2) / max(largura, altura),
               72 * math.sqrt((MAX_PIXELS * .999) / (largura * altura)))


def preparar_imagem(img, perfil: str):
    from PIL import ImageFilter, ImageOps
    if perfil not in PERFIS:
        raise ValueError("Perfil de OCR desconhecido.")
    derivada = img.convert("L")
    if perfil == "mediana":
        derivada = ImageOps.autocontrast(derivada.filter(ImageFilter.MedianFilter(3)))
    return derivada


def ler_tsv(texto: str, *, largura_pdf: float, altura_pdf: float, largura_img: int, altura_img: int) -> dict:
    """Escalas por eixo derivam do raster real, não de um DPI nominal."""
    linhas, confs = {}, []
    descartadas = 0
    sx, sy = largura_pdf / largura_img, altura_pdf / altura_img
    leitor = csv.DictReader(io.StringIO(texto), delimiter="\t", quoting=csv.QUOTE_NONE)
    esperado = {"level", "page_num", "block_num", "par_num", "line_num", "word_num", "left", "top", "width", "height", "conf", "text"}
    if not leitor.fieldnames or len(leitor.fieldnames) != len(esperado) or set(leitor.fieldnames) != esperado:
        raise ValueError("Cabeçalho TSV incompatível.")
    for w in leitor:
        if None in w or any(v is None for v in w.values()):
            descartadas += 1
            continue
        palavra = (w.get("text") or "").strip()
        if not palavra:
            continue
        try:
            conf = float(w["conf"])
            x, y, largura, altura = (int(w[k]) for k in ("left", "top", "width", "height"))
            k = tuple(int(w[c]) for c in ("block_num", "par_num", "line_num"))
            if (not math.isfinite(conf) or not 0 <= conf <= 100 or min(k) < 1
                    or x < 0 or y < 0 or largura <= 0 or altura <= 0
                    or x + largura > largura_img or y + altura > altura_img):
                raise ValueError("Palavra/caixa incompatível.")
        except (TypeError, ValueError, KeyError):
            descartadas += 1
            continue
        confs.append(conf)
        x0, t, x1, b = x*sx, y*sy, (x+largura)*sx, (y+altura)*sy
        d = linhas.setdefault(k, {"palavras": [], "x0": x0, "x1": x1, "top": t, "bottom": b})
        d["palavras"].append(palavra)
        d["x0"], d["x1"], d["top"], d["bottom"] = min(d["x0"], x0), max(d["x1"], x1), min(d["top"], t), max(d["bottom"], b)
    lista = [{"text": " ".join(d.pop("palavras")), "gap": 0.0, **d} for d in linhas.values()]
    lista.sort(key=lambda l: (round(l["top"] / 4), l["x0"]))
    return {"linhas": lista, "confianca": round(sum(confs)/len(confs),1) if confs else 0.0,
            "palavras": len(confs), "palavras_baixa_confianca": sum(c < 60 for c in confs),
            "palavras_descartadas": descartadas}


def ler_paginas(exe: str, pdf_path: Path, paginas: list[int], lang: str, *, perfil: str = "padrao", dpi: float = DPI) -> dict[int, dict]:
    """Resultados por página com raster limitado e coordenadas em pontos PDF.

    O perfil mediana é opcional e não representa conferência da transcrição.
    """
    import pdfplumber
    if perfil not in PERFIS:
        raise ValueError("Perfil de OCR desconhecido.")
    saida = {}
    with pdfplumber.open(pdf_path) as pdf, tempfile.TemporaryDirectory() as tmp:
        for n in paginas:
            pg = pdf.pages[n-1]
            # Renderizar a área visível e preservar sua origem no referencial PDF.
            quadro = pg.bbox if pg.bbox != pg.mediabox else pg.cropbox
            resolucao = resolucao_limitada(quadro[2]-quadro[0], quadro[3]-quadro[1], dpi)
            render = pg.to_image(resolution=resolucao)
            quadro = render.bbox
            img = preparar_imagem(render.original, perfil)
            png = Path(tmp) / f"p{n}.png"
            img.save(png)
            r = subprocess.run(_cmd(exe, str(png), "stdout", "-l", lang, "--psm", "3", "-c", "tessedit_create_tsv=1"),
                               capture_output=True, timeout=TIMEOUT_PAGINA)
            if r.returncode != 0:
                raise RuntimeError("Falha do motor OCR; conteúdo e caminhos do stderr não são divulgados.")
            resultado = ler_tsv(r.stdout.decode("utf-8", "replace"), largura_pdf=quadro[2]-quadro[0], altura_pdf=quadro[3]-quadro[1],
                                largura_img=img.width, altura_img=img.height)
            for linha in resultado["linhas"]:
                linha["x0"] += quadro[0]; linha["x1"] += quadro[0]
                linha["top"] += quadro[1]; linha["bottom"] += quadro[1]
            resultado["raster"] = {"bbox_pdf": list(quadro), "largura": img.width, "altura": img.height, "dpi_efetivo": resolucao, "perfil": perfil}
            saida[n] = resultado
    return saida
