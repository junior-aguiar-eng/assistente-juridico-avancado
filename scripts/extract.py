"""Extração de texto de documentos jurídicos (PDF textual, DOCX, TXT, MD, EML) em JSON.

Cada trecho (bloco) traz página, seção, localizador e marca de citação.
O stdout contém somente JSON válido; avisos de bibliotecas vão para o stderr.
Sem OCR: PDF sem camada de texto resulta em status "no_text".

Uso:  python scripts/extract.py ARQUIVO [ARQUIVO...] [--saida out.json]
                                [--cache-dir DIR | --no-cache] [--max-mb 60]

Status por documento: ok | partial | no_text | failed.
Marcação de citação é heurística (recuo à esquerda ou aspas): confira no original.
Geometria calibrada em página A4 (pontos PDF).
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
import hashlib
import io
import json
import logging
import os
import re
import sys
import unicodedata
import warnings
import zipfile
from pathlib import Path

EXTRACTOR_VERSION = "0.3.0"
SCHEMA_VERSION = "1"
IDIOMA = "pt-BR"  # assumido, não detectado
EXTENSOES = {".pdf", ".docx", ".txt", ".md", ".eml"}
MAX_PAGES = 2000
LIMIAR_PARAGRAFO = 30  # recuo de primeira linha (pt)
LIMIAR_CITACAO = 90  # recuo de citação em bloco (pt)
LIMIAR_IMAGEM = 0.5  # fração da página coberta por imagem
LIMIAR_CARACTERES = 300  # texto abaixo disso, numa página coberta por imagem, indica digitalização
MAX_DESCOMPRIMIDO = 200 * 1024 * 1024  # DOCX: soma dos tamanhos descomprimidos (proteção contra zip bomb)
PARAMS = {"idioma": IDIOMA, "lim_par": LIMIAR_PARAGRAFO, "lim_cit": LIMIAR_CITACAO, "max_pages": MAX_PAGES,
          "lim_img": LIMIAR_IMAGEM, "lim_chars": LIMIAR_CARACTERES}
PARAMS_HASH = hashlib.sha256(json.dumps(PARAMS, sort_keys=True).encode()).hexdigest()[:8]

TITULOS = {
    "EMENTA": "ementa", "RELATORIO": "relatorio", "VOTO": "voto", "ACORDAO": "acordao",
    "DECISAO": "decisao", "DESPACHO": "despacho", "SENTENCA": "sentenca", "PARECER": "parecer",
    "DISPOSITIVO": "dispositivo", "RELATORIO E VOTO": "relatorio_e_voto",
    "TERMO DE JULGAMENTO": "termo_de_julgamento", "CERTIDAO DE JULGAMENTO": "certidao_de_julgamento",
}
_DISPOSITIVO = re.compile(r"^(Ante o exposto|Diante do exposto|Pelo exposto|Nessas condições|"
                          r"Em face do exposto|Isso posto|Por tais razões)", re.I)
_FIM_FRASE = tuple(".;:!?”\"')")
# seções narrativas: só nelas o recuo à esquerda é lido como citação
SECOES_NARRATIVAS = {"relatorio", "voto", "relatorio_e_voto", "decisao", "sentenca", "despacho", "parecer", "dispositivo"}


# --------------------------------------------------------------------------- utilidades
def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def _hash_texto(partes) -> str:
    """Hash do texto bruto lido, sem depender de como ele foi dividido em blocos."""
    return hashlib.sha256(_ws(" ".join(partes)).encode("utf-8")).hexdigest()


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _sem_acento(s).lower()).strip("_")[:40] or "secao"


def _aviso(codigo, detalhe=None, pagina=None):
    return {"codigo": codigo, "detalhe": detalhe, "pagina": pagina}


def _fracao_entre_aspas(texto: str) -> float:
    dentro = total = 0
    aberto = False
    for ch in texto:
        if ch in "“\"":
            if ch == "“" or not aberto:
                aberto = True
            else:
                aberto = False
            continue
        if ch == "”":
            aberto = False
            continue
        total += 1
        dentro += aberto
    return dentro / total if total else 0.0


def _rodape_chave(s: str) -> str:
    s = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f-]{20,}", "uuid", s.lower())
    return re.sub(r"\d", "0", s)


def _finalizar_blocos(blocos: list[dict]) -> list[dict]:
    saida = []
    for i, b in enumerate(blocos, 1):
        texto = _ws(b.pop("texto"))
        if not texto:
            continue
        b.pop("_q", None)
        b.pop("_ux", None)
        b.pop("_d", None)
        if not b["is_quote"] and len(texto) > 40 and _fracao_entre_aspas(texto) >= 0.6:
            b["is_quote"], b["quote_basis"] = True, "aspas"
        tags = list(b.pop("tags", []))
        if b["section"] in ("voto", "relatorio_e_voto", "decisao", "dispositivo") and not b["is_quote"] \
                and _DISPOSITIVO.match(texto):
            tags.append("dispositivo")
        pg, pf = b["page"], b.get("page_end", b["page"])
        loc = ("p." + str(pg) if pg == pf else f"p.{pg}-{pf}") if pg else b.get("locator")
        saida.append({"id": f"b{len(saida) + 1:04d}", "locator": loc, "text": texto, "tags": tags, **b})
    return saida


# --------------------------------------------------------------------------- PDF
def _titulo(txt, ln, largura, margem):
    t = re.sub(r"[\s:.\-–]+$", "", txt).strip()
    if not t or t != t.upper():
        return None
    chave = _sem_acento(t)
    if chave not in TITULOS:
        return None
    centrado = abs((ln["x0"] + ln["x1"]) / 2 - largura / 2) < 30
    if centrado or abs(ln["x0"] - margem) < 15:
        return TITULOS[chave]
    return None


def _ler_pdf(path: Path):
    import pdfplumber

    paginas, avisos, cobertura, truncado = [], [], [], False
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages[:MAX_PAGES], 1):
            try:
                linhas = [ln for ln in page.extract_text_lines(strip=True) if ln["text"].strip()]
            except Exception as e:  # noqa: BLE001
                linhas = []
                avisos.append(_aviso("pagina_ilegivel", f"{type(e).__name__}: {e}", i))
            w, h = float(page.width), float(page.height)
            paginas.append((w, h, linhas))
            area = 0.0
            for im in page.images:
                larg = max(0.0, min(im["x1"], w) - max(im["x0"], 0.0))
                alt = max(0.0, min(im["bottom"], h) - max(im["top"], 0.0))
                area += larg * alt
            cobertura.append(min(1.0, area / (w * h)) if w * h else 0.0)
        truncado = total > MAX_PAGES
    if truncado:
        avisos.append(_aviso("truncado", f"lidas {MAX_PAGES} de {total} páginas"))
    return paginas, avisos, total, cobertura


_VOCAB_RODAPE = re.compile(r"(?i)documento eletr[oô]nico|assinad[oa]|signat[aá]rio|c[oó]digo de controle|"
                           r"publica[cç][aã]o no dj|p[aá]gina \d+ de \d+|autenticidade|certificado digital")


def _remover_repetidas(paginas):
    """Remove cabeçalhos/rodapés das faixas superior e inferior, sem apagar texto legítimo.

    Só sai a linha repetida que (a) tem vocabulário de assinatura/paginação em 2+ páginas ou
    (b) se repete em metade ou mais das páginas. Texto duplicado em apenas 2 páginas (documento
    reproduzido duas vezes no mesmo PDF) permanece."""
    contagem: dict[str, set[int]] = {}
    amostras: dict[str, str] = {}
    for n, (_, h, linhas) in enumerate(paginas):
        for ln in linhas:
            if ln["top"] < h * 0.06 or ln["top"] > h * 0.88:
                k = _rodape_chave(ln["text"])
                contagem.setdefault(k, set()).add(n)
                amostras.setdefault(k, ln["text"][:60])
    n_pag = len(paginas)
    repetidas = {k for k, v in contagem.items()
                 if (len(v) >= 2 and _VOCAB_RODAPE.search(amostras[k])) or (len(v) >= 3 and len(v) >= 0.5 * n_pag)}
    removidas, novas = 0, []
    for w, h, linhas in paginas:
        mantidas = []
        for ln in linhas:
            if (ln["top"] < h * 0.06 or ln["top"] > h * 0.88) and _rodape_chave(ln["text"]) in repetidas:
                removidas += 1
            else:
                mantidas.append(ln)
        novas.append((w, h, mantidas))
    return novas, removidas, sorted({amostras[k] for k in repetidas})[:3]


def _salto_de_paragrafo(ln, ant, passo_no_bloco) -> bool:
    """Espaço vertical maior que o passo das linhas do próprio bloco (ou 1,6 vez a altura da fonte)."""
    d = ln["top"] - ant["top"]
    if passo_no_bloco is not None:
        return d > 1.25 * passo_no_bloco
    return d > 1.6 * max(ln["bottom"] - ln["top"], 1.0)


def _montar_blocos_pdf(paginas):
    xs = sorted(ln["x0"] for _, _, ls in paginas for ln in ls)
    margem = xs[int(len(xs) * 0.15)] if xs else 0.0
    blocos, atual, secao = [], None, "cabecalho"

    def fechar():
        nonlocal atual
        if atual:
            blocos.append(atual)
            atual = None

    for pn, (w, _, linhas) in enumerate(paginas, 1):
        ant = None
        for ln in linhas:
            txt = ln["text"].strip()
            titulo = _titulo(txt, ln, w, margem)
            if titulo:
                fechar()
                secao, ant = titulo, ln
                continue
            recuo = ln["x0"] - margem
            quote = recuo >= LIMIAR_CITACAO and secao in SECOES_NARRATIVAS
            novo = atual is None or quote != atual["_q"]
            if not novo:
                fim = atual["texto"].rstrip().endswith(_FIM_FRASE)
                ref_x = ant["x0"] if ant is not None else atual["_ux"]
                if not quote and ln["x0"] - ref_x >= LIMIAR_PARAGRAFO:
                    novo = True  # recuo de primeira linha em relação à linha anterior
                elif ant is not None and _salto_de_paragrafo(ln, ant, atual["_d"]):
                    novo = True
                elif fim and re.match(r"^\d{1,2}\.\s", txt):
                    novo = True
                elif ant is None and fim:
                    novo = True  # início de página após frase concluída
            if novo:
                fechar()
                atual = {"page": pn, "page_end": pn, "section": secao, "texto": txt, "is_quote": quote,
                         "quote_basis": "recuo" if quote else None, "_q": quote, "_d": None}
            else:
                atual["texto"] += " " + txt
                atual["page_end"] = pn
                if ant is not None:
                    atual["_d"] = ln["top"] - ant["top"]
            atual["_ux"] = ln["x0"]
            ant = ln
    fechar()
    return _finalizar_blocos(blocos)


def extrair_pdf(path: Path) -> dict:
    paginas, avisos, total, cobertura = _ler_pdf(path)
    texto_bruto = _hash_texto(ln["text"] for _, _, ls in paginas for ln in ls)
    sem_texto = [i for i, (_, _, ls) in enumerate(paginas, 1) if not ls]
    for i in sem_texto:
        avisos.append(_aviso("pagina_sem_texto", "possível digitalização; OCR indisponível", i))
    paginas, removidas, exemplos = _remover_repetidas(paginas)
    if removidas:
        avisos.append(_aviso("cabecalho_rodape_removido", f"{removidas} linhas repetidas; exemplos: {exemplos}"))
    # página coberta por imagem com pouco texto: o corpo é imagem e o texto restante é carimbo ou rodapé
    digitalizadas = []
    for i, ((_, _, ls), cob) in enumerate(zip(paginas, cobertura), 1):
        if i in sem_texto:
            continue
        chars_pag = sum(len(ln["text"]) for ln in ls)
        if cob >= LIMIAR_IMAGEM and chars_pag < LIMIAR_CARACTERES:
            digitalizadas.append(i)
            avisos.append(_aviso("pagina_possivelmente_digitalizada",
                                 f"imagem cobre {cob:.0%} da página e há só {chars_pag} caracteres de texto; "
                                 "o corpo provavelmente é imagem (OCR indisponível)", i))
    blocos = _montar_blocos_pdf(paginas)
    chars = sum(len(b["text"]) for b in blocos)
    if chars and sum(b["text"].count("�") for b in blocos) / chars > 0.01:
        avisos.append(_aviso("codificacao_suspeita", "muitos caracteres de substituição (U+FFFD)"))
    sem_corpo = set(sem_texto) | set(digitalizadas)
    if len(sem_corpo) == len(paginas):
        status = "no_text"
    elif sem_corpo or any(a["codigo"] in ("truncado", "pagina_ilegivel", "codificacao_suspeita") for a in avisos):
        status = "partial"
    else:
        status = "ok"
    return {"status": status, "page_count": total, "blocks": blocos, "warnings": avisos,
            "text_sha256": texto_bruto}


# --------------------------------------------------------------------------- DOCX
class ArquivoSuspeito(Exception):
    """Arquivo que viola um limite de segurança (ex.: tamanho descomprimido)."""


_NS_W = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _xml_seguro(bruto: bytes):
    from lxml import etree

    return etree.fromstring(bruto, etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False))


def _xpaths():
    from lxml import etree

    f = lambda expr: etree.XPath(expr, namespaces=_NS_W)  # noqa: E731
    return {
        "runs": f(".//w:r[not(ancestor::w:txbxContent)]/*[self::w:t or self::w:tab or self::w:br or self::w:cr]"),
        "inserido": f("boolean(.//w:ins//w:r/w:t)"),
        "ins": f("count(//w:ins)"), "del": f("count(//w:del)"), "mov": f("count(//w:moveFrom | //w:moveTo)"),
        "caixas": f("//w:txbxContent//w:t"),
        "notas": f("//w:footnote[not(@w:type)] | //w:endnote[not(@w:type)]"),
        "pars": f(".//w:p"), "linhas": f("./w:tr"), "celulas": f("./w:tc"),
        "wt": f(".//w:t"), "id": f("string(@w:id)"),
    }


def _texto_runs(xp, el) -> str:
    """Texto das runs: inclui inserções rastreadas, exclui exclusões e caixas de texto."""
    partes = []
    for no in xp["runs"](el):
        tag = no.tag.rsplit("}", 1)[-1]
        partes.append((no.text or "") if tag == "t" else "\t" if tag == "tab" else "\n")
    return "".join(partes)


def _corpo(filhos):
    """Itera parágrafos e tabelas do corpo, entrando em controles de conteúdo (w:sdt)."""
    for f in filhos:
        tag = f.tag.rsplit("}", 1)[-1]
        if tag in ("p", "tbl"):
            yield tag, f
        elif tag == "sdt":
            conteudo = [c for c in f if c.tag.rsplit("}", 1)[-1] == "sdtContent"]
            for c in conteudo:
                yield from _corpo(list(c))


def extrair_docx(path: Path) -> dict:
    import docx
    from docx.text.paragraph import Paragraph

    avisos, xp = [], _xpaths()
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if sum(i.file_size for i in infos) > MAX_DESCOMPRIMIDO:
            raise ArquivoSuspeito(f"tamanho descomprimido acima de {MAX_DESCOMPRIMIDO // (1024 * 1024)} MB")
        partes = {i.filename: z.read(i.filename) for i in infos
                  if re.match(r"word/(document|footnotes|endnotes|header\d*|footer\d*|comments\w*)\.xml$", i.filename)}
    doc_xml = _xml_seguro(partes["word/document.xml"])
    n_ins, n_del, n_mov = int(xp["ins"](doc_xml)), int(xp["del"](doc_xml)), int(xp["mov"](doc_xml))
    parcial = False
    if n_ins or n_del or n_mov:
        parcial = True
        avisos.append(_aviso("alteracoes_rastreadas",
                             f"{n_ins} inserção(ões), {n_del} exclusão(ões) e {n_mov} movimentação(ões) rastreadas: "
                             "o texto lido é a versão com as alterações aceitas (blocos com inserção levam a tag "
                             "'inserido'); texto excluído foi omitido"))
    if [t for t in xp["caixas"](doc_xml) if (t.text or "").strip()]:
        parcial = True
        avisos.append(_aviso("parte_nao_extraida", "caixas de texto do corpo não foram extraídas"))
    for nome, bruto in sorted(partes.items()):
        if re.match(r"word/(header\d*|footer\d*|comments\w*)\.xml$", nome):
            texto = " ".join((t.text or "") for t in xp["wt"](_xml_seguro(bruto))).strip()
            if texto:
                parcial = True
                tipo = "cabeçalho/rodapé" if re.search(r"header|footer", nome) else "comentários"
                avisos.append(_aviso("parte_nao_extraida", f"{tipo} ({nome}) não extraído: {_ws(texto)[:80]!r}"))

    d = docx.Document(str(path))
    blocos, brutos, secao, npar, ntab = [], [], "corpo", 0, 0
    for tag, filho in _corpo(list(d.element.body)):
        if tag == "p":
            texto = _texto_runs(xp, filho)
            if not texto.strip():
                continue
            npar += 1
            p = Paragraph(filho, d)
            estilo = (p.style.name if p.style is not None else "") or ""
            if re.match(r"(?i)^(heading|título|titulo)", estilo):
                secao = _slug(texto)
            recuo = p.paragraph_format.left_indent
            quote = bool(re.search(r"(?i)quote|cita", estilo)) or (recuo is not None and recuo >= 540000)
            blocos.append({"page": None, "locator": f"par.{npar}", "section": secao, "texto": texto,
                           "is_quote": quote, "quote_basis": "estilo/recuo" if quote else None,
                           "tags": ["inserido"] if xp["inserido"](filho) else []})
            brutos.append(texto)
        else:
            ntab += 1
            for r, linha in enumerate(xp["linhas"](filho), 1):
                celulas = [_ws(" ".join(_texto_runs(xp, p) for p in xp["pars"](c))) for c in xp["celulas"](linha)]
                texto = " | ".join(celulas)
                if texto.strip(" |"):
                    blocos.append({"page": None, "locator": f"tab.{ntab}.lin.{r}", "section": secao,
                                   "texto": texto, "is_quote": False, "quote_basis": None,
                                   "tags": ["inserido"] if xp["inserido"](linha) else []})
                    brutos.append(texto)
    for nome, rot, secao_n in (("word/footnotes.xml", "nota", "notas_de_rodape"), ("word/endnotes.xml", "notafim", "notas_de_fim")):
        if nome not in partes:
            continue
        for nota in xp["notas"](_xml_seguro(partes[nome])):
            texto = _ws(" ".join(_texto_runs(xp, p) for p in xp["pars"](nota)))
            if texto:
                blocos.append({"page": None, "locator": f"{rot}.{xp['id'](nota)}", "section": secao_n, "texto": texto,
                               "is_quote": False, "quote_basis": None, "tags": []})
                brutos.append(texto)
    status = "no_text" if not blocos else ("partial" if parcial else "ok")
    return {"status": status, "page_count": None, "blocks": _finalizar_blocos(blocos), "warnings": avisos,
            "text_sha256": _hash_texto(brutos)}


# --------------------------------------------------------------------------- TXT / MD
def extrair_texto(path: Path) -> dict:
    avisos, bruto = [], path.read_bytes()
    try:
        texto = bruto.decode("utf-8")
    except UnicodeDecodeError:
        texto = bruto.decode("windows-1252", errors="replace")
        avisos.append(_aviso("codificacao_assumida", "não era UTF-8; lido como windows-1252"))
    md = path.suffix.lower() == ".md"
    blocos, secao = [], "corpo"
    for n, par in enumerate(re.split(r"\n\s*\n", texto.replace("\r\n", "\n")), 1):
        if not par.strip():
            continue
        if md and (m := re.match(r"^#{1,6}\s+(.*)$", par.strip().split("\n")[0])):
            secao = _slug(m.group(1))
        quote = md and all(l.lstrip().startswith(">") for l in par.strip().split("\n"))
        blocos.append({"page": None, "locator": f"par.{n}", "section": secao, "texto": par,
                       "is_quote": quote, "quote_basis": "marcador" if quote else None})
    return {"status": "ok" if blocos else "no_text", "page_count": None,
            "blocks": _finalizar_blocos(blocos), "warnings": avisos, "text_sha256": _hash_texto([texto])}


# --------------------------------------------------------------------------- E-MAIL (.eml)
def extrair_eml(path: Path) -> dict:
    """Mensagem de e-mail: cabeçalho (de, para, data, assunto) e corpo em parágrafos; anexos são só listados."""
    import html as _html
    from email import policy
    from email.parser import BytesParser
    from email.utils import parsedate_to_datetime

    msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    avisos, blocos, brutos = [], [], []
    cab = {k: _ws(str(msg.get(k, ""))) for k in ("From", "To", "Cc", "Date", "Subject")}
    partes_cab = [f"{rot}: {cab[k]}" for rot, k in (("De", "From"), ("Para", "To"), ("Cc", "Cc"), ("Data", "Date"),
                                                    ("Assunto", "Subject")) if cab[k]]
    if partes_cab:
        texto = " | ".join(partes_cab)
        blocos.append({"page": None, "locator": "email.cabecalho", "section": "cabecalho", "texto": texto,
                       "is_quote": False, "quote_basis": None, "tags": []})
        brutos.append(texto)
    data_iso = None
    if cab["Date"]:
        try:
            data_iso = parsedate_to_datetime(cab["Date"]).isoformat()
        except (TypeError, ValueError):
            avisos.append(_aviso("data_do_cabecalho_ilegivel", cab["Date"]))
    corpo = msg.get_body(preferencelist=("plain", "html"))
    texto_corpo = ""
    if corpo is not None:
        texto_corpo = corpo.get_content()
        if corpo.get_content_type() == "text/html":
            texto_corpo = re.sub(r"(?is)<(script|style).*?</\1>", " ", texto_corpo)
            texto_corpo = _html.unescape(re.sub(r"(?s)<br\s*/?>|</p>|</div>", "\n\n", texto_corpo))
            texto_corpo = re.sub(r"<[^>]+>", " ", texto_corpo)
            avisos.append(_aviso("corpo_html", "só havia HTML: o texto foi extraído sem formatação"))
    else:
        avisos.append(_aviso("sem_corpo", "a mensagem não tem corpo de texto legível"))
    for n, par in enumerate((p for p in re.split(r"\n\s*\n", texto_corpo.replace("\r\n", "\n")) if p.strip()), 1):
        linhas = [l for l in par.strip().split("\n") if l.strip()]
        citado = bool(linhas) and all(l.lstrip().startswith(">") for l in linhas)
        blocos.append({"page": None, "locator": f"email.corpo.par.{n}", "section": "corpo", "texto": par,
                       "is_quote": citado, "quote_basis": "marcador" if citado else None, "tags": []})
        brutos.append(par)
    anexos = [a.get_filename() or "(sem nome)" for a in msg.iter_attachments()]
    if anexos:
        avisos.append(_aviso("parte_nao_extraida", f"anexos não extraídos: {', '.join(anexos)}"))
    if corpo is not None and not texto_corpo.strip():
        avisos.append(_aviso("corpo_vazio", "o corpo da mensagem não tem texto"))
    parcial = bool(anexos) or corpo is None or not texto_corpo.strip()
    status = "no_text" if not blocos else ("partial" if parcial else "ok")
    return {"status": status, "page_count": None, "blocks": _finalizar_blocos(blocos), "warnings": avisos,
            "email": {"from": cab["From"], "to": cab["To"], "date": cab["Date"], "date_iso": data_iso,
                      "subject": cab["Subject"], "anexos": anexos},
            "text_sha256": _hash_texto(brutos)}


# --------------------------------------------------------------------------- orquestração
def _versoes():
    v = {"extractor": EXTRACTOR_VERSION}
    for nome in ("pdfplumber", "docx"):
        with contextlib.suppress(Exception):
            v[nome] = getattr(__import__(nome), "__version__", "?")
    return v


def extrair(caminho, cache_dir: str | None = None, max_mb: float = 60.0):
    """Retorna (documento, cache_hit). Nunca levanta exceção por conteúdo do arquivo."""
    p = Path(caminho)
    base = {"path": str(caminho), "idioma_assumido": IDIOMA}

    def falha(codigo, detalhe):
        return {**base, "document_id": None, "sha256": None, "status": "failed", "page_count": None,
                "blocks": [], "warnings": [_aviso(codigo, detalhe)]}, False

    if p.is_symlink():
        return falha("link_simbolico", "links simbólicos não são aceitos")
    if not p.is_file():
        return falha("arquivo_inexistente", str(p))
    if p.suffix.lower() not in EXTENSOES:
        return falha("extensao_nao_aceita", f"{p.suffix or '(sem extensão)'}; aceitas: {sorted(EXTENSOES)}")
    if p.stat().st_size > max_mb * 1024 * 1024:
        return falha("arquivo_grande", f"mais de {max_mb} MB")
    bruto = p.read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    base.update({"document_id": f"doc-{sha[:12]}", "sha256": sha, "size_bytes": len(bruto),
                 "media_type": {".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/markdown",
                                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                ".eml": "message/rfc822"}[p.suffix.lower()]})
    arq_cache = Path(cache_dir) / f"{sha[:32]}-{EXTRACTOR_VERSION}-{PARAMS_HASH}.json" if cache_dir else None
    if arq_cache and arq_cache.is_file():
        with contextlib.suppress(Exception):
            doc = json.loads(arq_cache.read_text(encoding="utf-8"))
            doc["path"] = str(caminho)
            return doc, True
    try:
        with warnings.catch_warnings(), contextlib.redirect_stdout(sys.stderr):
            warnings.simplefilter("ignore")
            r = {".pdf": extrair_pdf, ".docx": extrair_docx, ".eml": extrair_eml}.get(p.suffix.lower(), extrair_texto)(p)
    except ArquivoSuspeito as e:
        return falha("arquivo_suspeito", str(e))
    except Exception as e:  # noqa: BLE001 - arquivo corrompido ou formato inesperado
        return falha("erro_de_leitura", f"{type(e).__name__}: {e}")
    # text_sha256 identifica o texto lido, independente do arquivo (o mesmo acórdão baixado duas vezes
    # pode ter bytes diferentes) e da segmentação em blocos; cada leitor o calcula sobre o texto bruto
    doc = {**base, "extractor_versions": _versoes(), **r}
    if arq_cache and doc["status"] != "failed":
        arq_cache.parent.mkdir(parents=True, exist_ok=True)
        tmp = arq_cache.with_suffix(".tmp")
        tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, arq_cache)
    return doc, False


# --------------------------------------------------------------------------- ajudantes de análise
def texto_secao(doc: dict, secao: str, incluir_citacoes: bool = False) -> str:
    """Concatena os blocos de uma seção; por padrão exclui trechos marcados como citação."""
    return "\n".join(b["text"] for b in doc["blocks"]
                     if b["section"] == secao and (incluir_citacoes or not b["is_quote"]))


def segmentos(doc: dict) -> list[dict]:
    """Agrupa blocos consecutivos da mesma seção; separa cópias repetidas (ex.: ementa duplicada)."""
    saida: list[dict] = []
    for b in doc["blocks"]:
        if saida and saida[-1]["section"] == b["section"]:
            saida[-1]["text"] += "\n" + b["text"]
            saida[-1]["page_end"] = b.get("page_end") or saida[-1]["page_end"]
        else:
            saida.append({"section": b["section"], "page": b.get("page"),
                          "page_end": b.get("page_end") or b.get("page"), "text": b["text"]})
    return saida


def similaridade(a: str, b: str) -> float:
    """Razão (0 a 1) entre as sequências de palavras, ignorando caixa e pontuação."""
    ta, tb = re.findall(r"\w+", a.casefold()), re.findall(r"\w+", b.casefold())
    return difflib.SequenceMatcher(None, ta, tb, autojunk=False).ratio() if ta and tb else 0.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--saida")
    ap.add_argument("--cache-dir", default=".cache/extract")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--max-mb", type=float, default=60.0)
    a = ap.parse_args(argv)
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    docs, hits = [], 0
    for arq in a.arquivos:
        d, hit = extrair(arq, None if a.no_cache else a.cache_dir, a.max_mb)
        docs.append(d)
        hits += hit
    saida = {"schema_version": SCHEMA_VERSION, "run": {"extractor_version": EXTRACTOR_VERSION,
             "params": PARAMS, "cache_hits": hits}, "documents": docs}
    txt = json.dumps(saida, ensure_ascii=False, indent=2)
    if a.saida:
        Path(a.saida).write_text(txt, encoding="utf-8")
    sys.stdout.buffer.write((txt + "\n").encode("utf-8"))
    return 2 if any(d["status"] == "failed" for d in docs) else 0


if __name__ == "__main__":
    sys.exit(main())
