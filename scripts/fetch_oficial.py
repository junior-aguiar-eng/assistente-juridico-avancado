#!/usr/bin/env python3
"""
fetch_oficial.py: baixa uma página de site oficial (.gov.br, .jus.br) e entrega Markdown limpo.

Uso:
    python fetch_oficial.py URL [SAIDA.md]

Sem SAIDA, o Markdown vai para o stdout. Se a resposta for PDF, o arquivo é salvo (em SAIDA, se
informada; senão em ~/.claude/downloads) e o caminho é informado, sem conversão.

Decodificação (nunca a automática do requests):
    1. charset do cabeçalho Content-Type
    2. charset da tag <meta>
    3. UTF-8 estrito
    4. windows-1252 (páginas do Planalto não declaram charset)

Em erro: imprime host, código HTTP ou exceção exata e as tentativas feitas, e sai com código 1.
Não tenta contornar bloqueios de política (por exemplo 403 do proxy do ambiente).

Dependências: requests, beautifulsoup4, lxml, markdownify
"""
import codecs
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT_S = 30
TENTATIVAS = 2
PAUSA_ENTRE_TENTATIVAS_S = 2

# Segundo a especificação HTML, estes rótulos significam windows-1252 na prática.
ALIAS_CHARSET = {"iso-8859-1": "windows-1252", "latin1": "windows-1252", "latin-1": "windows-1252",
                 "l1": "windows-1252", "us-ascii": "windows-1252", "ascii": "windows-1252"}


def _cp1252_tolerante(erro):
    """Bytes que o windows-1252 deixa indefinidos (0x81, 0x8D, 0x8F, 0x90, 0x9D) viram o ponto de
    código equivalente do Latin-1, em vez de U+FFFD."""
    if isinstance(erro, UnicodeDecodeError):
        return "".join(chr(b) for b in erro.object[erro.start:erro.end]), erro.end
    raise erro


codecs.register_error("cp1252_tolerante", _cp1252_tolerante)


class FalhaDeAcesso(Exception):
    pass


def baixar(url):
    """Retorna (resposta, tentativas). Levanta FalhaDeAcesso com o relato completo."""
    tentativas = []
    for n in range(1, TENTATIVAS + 1):
        try:
            r = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
                         "Accept-Language": "pt-BR,pt;q=0.9"},
                timeout=TIMEOUT_S,
                allow_redirects=True,
            )
        except Exception as e:  # relato exato da exceção
            tentativas.append(f"tentativa {n}: {type(e).__name__}: {e}")
        else:
            if r.status_code < 400:
                tentativas.append(f"tentativa {n}: HTTP {r.status_code}")
                return r, tentativas
            tentativas.append(f"tentativa {n}: HTTP {r.status_code} {r.reason or ''}".rstrip())
        if n < TENTATIVAS:
            time.sleep(PAUSA_ENTRE_TENTATIVAS_S)
    raise FalhaDeAcesso(tentativas)


def charset_do_cabecalho(content_type):
    m = re.search(r"charset\s*=\s*[\"']?([\w.:-]+)", content_type or "", re.I)
    return m.group(1).lower() if m else None


def charset_do_meta(dados):
    # O trecho inicial é ASCII em qualquer codificação ASCII-compatível; basta buscar em bytes.
    cabeca = dados[:8192]
    m = re.search(rb"<meta[^>]+charset\s*=\s*[\"']?\s*([\w.:-]+)", cabeca, re.I)
    if not m:
        m = re.search(rb"<meta[^>]+content\s*=\s*[\"'][^\"']*charset\s*=\s*([\w.:-]+)", cabeca, re.I)
    return m.group(1).decode("ascii", "ignore").lower() if m else None


def decodificar(dados, content_type):
    """Retorna (texto, charset_usado, origem)."""
    for origem, rotulo in (("cabeçalho", charset_do_cabecalho(content_type)), ("meta", charset_do_meta(dados))):
        if not rotulo:
            continue
        rotulo = ALIAS_CHARSET.get(rotulo, rotulo)
        try:
            codecs.lookup(rotulo)
        except LookupError:
            continue
        erros = "cp1252_tolerante" if rotulo == "windows-1252" else "strict"
        try:
            return dados.decode(rotulo, errors=erros), rotulo, origem
        except UnicodeDecodeError:
            continue  # o charset declarado não confere com os bytes: segue a cadeia
    try:
        return dados.decode("utf-8", errors="strict"), "utf-8", "UTF-8 estrito"
    except UnicodeDecodeError:
        return dados.decode("windows-1252", errors="cp1252_tolerante"), "windows-1252", "fallback"


def eh_pdf(r):
    tipo = (r.headers.get("Content-Type") or "").lower()
    return "application/pdf" in tipo or r.content[:5] == b"%PDF-"


def nome_de_arquivo(url):
    nome = Path(unquote(urlparse(url).path)).name or "documento"
    return nome if nome.lower().endswith(".pdf") else nome + ".pdf"


def _soup(html):
    """lxml encerra a análise em páginas grandes e malformadas (o Código Civil do Planalto sai com 750 caracteres).
    Se o resultado perder muito texto frente ao html.parser, usa o html.parser."""
    soup = BeautifulSoup(html, "lxml")
    texto_lxml = len(soup.get_text())
    alternativa = BeautifulSoup(html, "html.parser")
    if len(alternativa.get_text()) > 2 * texto_lxml + 1000:
        return alternativa
    return soup


def html_para_markdown(html):
    soup = _soup(html)
    for tag in soup(["script", "style", "noscript", "template", "iframe", "svg", "link", "meta"]):
        tag.decompose()
    # O Planalto marca o texto revogado ou substituído como tachado; o markdownify descarta isso.
    # Marca com ~~ para que redação antiga nunca seja lida como vigente.
    for tag in soup.find_all(["strike", "s", "del"]):
        if tag.get_text(strip=True):
            tag.insert_before("~~")
            tag.insert_after("~~")
    # Páginas com </body> ou </html> prematuros (Código Civil do Planalto): o texto fica fora do <body>.
    base = soup.body if soup.body and len(soup.body.get_text()) * 2 >= len(soup.get_text()) else soup
    md = markdownify(str(base), heading_style="ATX", strip=["img"])
    md = md.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    if len(argv) not in (2, 3) or argv[1] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    url = argv[1]
    saida = Path(argv[2]).expanduser() if len(argv) == 3 else None
    host = urlparse(url).hostname or url

    try:
        r, tentativas = baixar(url)
    except FalhaDeAcesso as e:
        print(f"ERRO ao acessar {url}\nhost: {host}", file=sys.stderr)
        for t in e.args[0]:
            print(f"  {t}", file=sys.stderr)
        print("Nenhum contorno foi tentado; se for bloqueio de política (403), peça a liberação do host.", file=sys.stderr)
        return 1

    if eh_pdf(r):
        destino = saida or (Path.home() / ".claude" / "downloads" / nome_de_arquivo(r.url))
        if destino.suffix.lower() != ".pdf":
            destino = destino.with_name(destino.name + ".pdf")  # nunca deixar um PDF com extensão de texto
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(r.content)
        print(f"PDF salvo em: {destino} ({len(r.content)} bytes). Conteúdo não convertido.")
        return 0

    tipo = r.headers.get("Content-Type", "")
    texto, charset, origem = decodificar(r.content, tipo)
    if re.search(r"html|xml", tipo, re.I) or re.search(r"<html|<!doctype html|<body", texto[:2000], re.I):
        saida_texto = html_para_markdown(texto)
    else:
        saida_texto = texto

    tachados = saida_texto.count("~~") // 2
    print(f"[fetch_oficial] {r.url} | HTTP {r.status_code} | charset {charset} ({origem}) | {len(r.content)} bytes | {'; '.join(tentativas)}"
          + (f" | {tachados} trechos tachados (revogados/substituídos) marcados com ~~" if tachados else ""),
          file=sys.stderr)
    if saida:
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(saida_texto, encoding="utf-8", newline="\n")
        print(f"Markdown salvo em: {saida} ({len(saida_texto)} caracteres)")
    else:
        sys.stdout.write(saida_texto)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
