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

sys.path.insert(0, str(Path(__file__).resolve().parent))  # injecao.py, mesmo com python -P
import injecao  # noqa: E402
import ocr  # noqa: E402

EXTRACTOR_VERSION = "0.4.0"
SCHEMA_VERSION = "1"
IDIOMA = "pt-BR"  # assumido, não detectado
EXTENSOES = {".pdf", ".docx", ".txt", ".md", ".eml", ".html", ".htm", ".csv", ".tsv", ".xlsx"}
MAX_PAGES = 2000
LIMIAR_PARAGRAFO = 30  # recuo de primeira linha (pt)
LIMIAR_CITACAO = 90  # recuo de citação em bloco (pt)
LIMIAR_IMAGEM = 0.5  # fração da página coberta por imagem
LIMIAR_CARACTERES = 300  # texto abaixo disso, numa página coberta por imagem, indica digitalização
MAX_SEGUNDOS = 300  # tempo máximo de leitura de um PDF (verificado entre páginas)
VAO_COLUNA = 36.0  # vão horizontal (pt) que separa colunas ou células
PROPORCAO_COLUNAS = 0.35  # fração de linhas com vão largo que caracteriza colunas ou tabela
MAX_DESCOMPRIMIDO = 200 * 1024 * 1024  # DOCX: soma dos tamanhos descomprimidos (proteção contra zip bomb)
PARAMS = {"idioma": IDIOMA, "lim_par": LIMIAR_PARAGRAFO, "lim_cit": LIMIAR_CITACAO, "max_pages": MAX_PAGES,
          "lim_img": LIMIAR_IMAGEM, "lim_chars": LIMIAR_CARACTERES, "vao": VAO_COLUNA, "cols": PROPORCAO_COLUNAS}


def _versoes_das_bibliotecas() -> dict:
    from importlib import metadata

    v = {}
    for nome in ("pdfplumber", "pdfminer.six", "python-docx", "lxml"):
        try:
            v[nome] = metadata.version(nome)
        except metadata.PackageNotFoundError:
            v[nome] = "ausente"
    return v


# a chave do cache muda com os parâmetros e com a versão das bibliotecas que leem o arquivo
PARAMS_HASH = hashlib.sha256(json.dumps({**PARAMS, "libs": _versoes_das_bibliotecas()}, sort_keys=True).encode()).hexdigest()[:8]

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


_INICIO_INLINE = re.compile(r"^(?:(EMENTA\b[^:]{0,60}:)|(Decis[ãa]o:))\s*\S")


def _secao_inline(txt: str) -> str | None:
    """Linha que abre a seção e já traz o texto dela ("EMENTA SOBRE REPERCUSSÃO GERAL: ...", "Decisão: O Tribunal...")."""
    m = _INICIO_INLINE.match(txt)
    if not m:
        return None
    return "ementa" if m.group(1) else "decisao"


def _maior_vao(chars) -> float:
    """Maior espaço horizontal entre caracteres consecutivos de uma linha (colunas e células deixam vãos grandes)."""
    pos = sorted((c for c in chars if str(c.get("text", "")).strip()), key=lambda c: c["x0"])
    return max((b["x0"] - a["x1"] for a, b in zip(pos, pos[1:])), default=0.0)


def _ler_pdf(path: Path):
    import time

    import pdfplumber

    paginas, avisos, cobertura, truncado = [], [], [], False
    duplicados: list[tuple[int, int]] = []
    estrutura = {"colunas": [], "tabelas": []}
    inicio = time.monotonic()
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages[:MAX_PAGES], 1):
            if i > 1 and time.monotonic() - inicio > MAX_SEGUNDOS:
                avisos.append(_aviso("tempo_excedido", f"leitura interrompida após {MAX_SEGUNDOS} s: lidas {i - 1} de {total} páginas"))
                break
            try:
                # PDFs que imprimem cada glifo duas vezes na mesma posição (negrito simulado, comum em documentos do STF)
                # saem com "SSuupprreemmoo": remove só o glifo repetido no mesmo ponto; "ss" e "rr" legítimos ficam
                antes = len(page.chars)
                pagina_limpa = page.dedupe_chars(tolerance=1)
                if antes - len(pagina_limpa.chars) >= 3:
                    duplicados.append((i, antes - len(pagina_limpa.chars)))
                page = pagina_limpa
                linhas = [ln for ln in page.extract_text_lines(strip=True, return_chars=True) if ln["text"].strip()]
            except Exception as e:  # noqa: BLE001
                linhas = []
                avisos.append(_aviso("pagina_ilegivel", f"{type(e).__name__}: {e}", i))
            for ln in linhas:
                ln["gap"] = _maior_vao(ln.pop("chars", []))
            w, h = float(page.width), float(page.height)
            paginas.append((w, h, linhas))
            if len(linhas) >= 8 and sum(1 for ln in linhas if ln["gap"] >= VAO_COLUNA) / len(linhas) >= PROPORCAO_COLUNAS:
                estrutura["colunas"].append(i)
            try:
                if (page.lines or page.rects) and any(len(t.rows) >= 2 and len(t.rows[0].cells) >= 2 for t in page.find_tables()):
                    estrutura["tabelas"].append(i)
            except Exception:  # noqa: BLE001 - detecção de tabela é auxiliar; falhar não pode derrubar a leitura
                pass
            area = 0.0
            for im in page.images:
                larg = max(0.0, min(im["x1"], w) - max(im["x0"], 0.0))
                alt = max(0.0, min(im["bottom"], h) - max(im["top"], 0.0))
                area += larg * alt
            cobertura.append(min(1.0, area / (w * h)) if w * h else 0.0)
        truncado = total > MAX_PAGES
    for pg, n in duplicados:
        avisos.append(_aviso("glifos_duplicados_removidos", f"{n} caracteres impressos em dobro na mesma posição foram colapsados "
                                                            "(negrito simulado); o texto lido é o que se vê na página", pg))
    if truncado:
        avisos.append(_aviso("truncado", f"lidas {MAX_PAGES} de {total} páginas"))
    return paginas, avisos, total, cobertura, estrutura


_VOCAB_RODAPE = re.compile(r"(?i)documento eletr[oô]nico|assinad[oa]|signat[aá]rio|c[oó]digo de controle|"
                           r"publica[cç][aã]o no dj|p[aá]gina \d+ de \d+|autenticidade|certificado digital")


def _remover_repetidas(paginas):
    """Remove cabeçalhos/rodapés das faixas superior e inferior, sem apagar texto legítimo.

    Só sai a linha repetida que (a) tem vocabulário de assinatura/paginação em 2+ páginas ou
    (b) se repete em metade ou mais das páginas. Texto duplicado em apenas 2 páginas (documento
    reproduzido duas vezes no mesmo PDF) permanece. As linhas removidas voltam como blocos da seção
    'rodape' (datas de publicação e de assinatura são evidência)."""
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
    removidas, novas, detalhes = 0, [], {}
    for n, (w, h, linhas) in enumerate(paginas, 1):
        mantidas = []
        for ln in linhas:
            k = _rodape_chave(ln["text"])
            if (ln["top"] < h * 0.06 or ln["top"] > h * 0.88) and k in repetidas:
                removidas += 1
                detalhes.setdefault(k, {"texto": ln["text"].strip(), "paginas": set()})["paginas"].add(n)
            else:
                mantidas.append(ln)
        novas.append((w, h, mantidas))
    lista = sorted(({"texto": d["texto"], "paginas": sorted(d["paginas"])} for d in detalhes.values()),
                   key=lambda d: (d["paginas"][0], d["texto"]))
    return novas, removidas, sorted({amostras[k] for k in repetidas})[:3], lista


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
            if (inline := _secao_inline(txt)):
                fechar()
                secao = inline
                ant = None
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


_OCR = False


def _aplicar_ocr(path: Path, paginas: list, alvo: list[int], avisos: list) -> set[int]:
    """OCR das páginas sem corpo de texto. Devolve as páginas lidas; falhas viram aviso, nunca silêncio."""
    exe = ocr.localizar_tesseract()
    if not exe:
        avisos.append(_aviso("ocr_indisponivel", "OCR pedido, mas o Tesseract não foi encontrado (PATH, JURIS_TESSERACT ou pasta padrão)"))
        return set()
    lang, aviso_lang = ocr.escolher_idioma(exe)
    if not lang:
        avisos.append(_aviso("ocr_indisponivel", aviso_lang))
        return set()
    if aviso_lang:
        avisos.append(_aviso("ocr_idioma_degradado", aviso_lang))
    try:
        lidas = ocr.ler_paginas(exe, path, alvo, lang)
    except Exception as e:  # noqa: BLE001 - OCR é auxiliar; a falha é relatada
        avisos.append(_aviso("ocr_indisponivel", f"{type(e).__name__}: {e}"))
        return set()
    feitas = set()
    for n, r in lidas.items():
        if not r["linhas"]:
            avisos.append(_aviso("ocr_sem_texto", "o OCR não reconheceu texto na página", n))
            continue
        w, h, existentes = paginas[n - 1]
        paginas[n - 1] = (w, h, sorted(r["linhas"] + existentes, key=lambda l: (round(l["top"] / 4), l["x0"])))
        feitas.add(n)
        avisos.append(_aviso("ocr_aplicado", f"texto reconhecido por OCR (idioma {lang}, confiança média {r['confianca']}): "
                                              "confira dígitos, acentos e nomes no original", n))
        if r["confianca"] < 60:
            avisos.append(_aviso("ocr_baixa_confianca", f"confiança média {r['confianca']} (< 60): o texto desta página não é confiável", n))
    return feitas


def extrair_pdf(path: Path) -> dict:
    paginas, avisos, total, cobertura, estrutura = _ler_pdf(path)
    texto_bruto = _hash_texto(ln["text"] for _, _, ls in paginas for ln in ls)
    sem_texto = [i for i, (_, _, ls) in enumerate(paginas, 1) if not ls]
    for i in sem_texto:
        avisos.append(_aviso("pagina_sem_texto", "possível digitalização; OCR indisponível", i))
    for i in estrutura["colunas"]:
        avisos.append(_aviso("layout_em_colunas_ou_tabela",
                             "muitas linhas com vãos largos: colunas ou tabela; a ordem de leitura e as células não são confiáveis", i))
    for i in estrutura["tabelas"]:
        avisos.append(_aviso("tabela_no_pdf", "tabela com linhas desenhadas: as células saem lidas linha a linha, sem separar colunas", i))
    paginas, removidas, exemplos, rodapes = _remover_repetidas(paginas)
    if removidas:
        avisos.append(_aviso("cabecalho_rodape_removido",
                             f"{removidas} linhas repetidas; voltam como blocos da seção 'rodape'; exemplos: {exemplos}"))
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
    ocr_paginas: set[int] = set()
    sem_corpo_antes = set(sem_texto) | set(digitalizadas)
    if _OCR and sem_corpo_antes:
        ocr_paginas = _aplicar_ocr(path, paginas, sorted(sem_corpo_antes), avisos)
        if ocr_paginas:
            texto_bruto = _hash_texto(ln["text"] for _, _, ls in paginas for ln in ls)
    blocos = _montar_blocos_pdf(paginas)
    for b in blocos:
        if ocr_paginas and b["page"] in ocr_paginas and (b.get("page_end") or b["page"]) in ocr_paginas:
            b["tags"] = sorted(set(b.get("tags", [])) | {"ocr"})
    chars = sum(len(b["text"]) for b in blocos)
    if chars and sum(b["text"].count("�") for b in blocos) / chars > 0.01:
        avisos.append(_aviso("codificacao_suspeita", "muitos caracteres de substituição (U+FFFD)"))
    for d in rodapes:
        pg = d["paginas"]
        blocos.append({"id": f"b{len(blocos) + 1:04d}", "locator": f"p.{pg[0]}" if pg[0] == pg[-1] else f"p.{pg[0]}-{pg[-1]}",
                       "text": _ws(d["texto"]), "tags": ["repetido"], "page": pg[0], "page_end": pg[-1], "section": "rodape",
                       "is_quote": False, "quote_basis": None})
    sem_corpo = (set(sem_texto) | set(digitalizadas)) - ocr_paginas
    codigos_parciais = ("truncado", "pagina_ilegivel", "codificacao_suspeita", "tempo_excedido", "layout_em_colunas_ou_tabela",
                        "ocr_aplicado")
    if len(sem_corpo) == len(paginas):
        status = "no_text"
    elif sem_corpo or any(a["codigo"] in codigos_parciais for a in avisos):
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
        _checar_zip(z)
        infos = z.infolist()
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


# --------------------------------------------------------------------------- ZIP (DOCX, XLSX)
MAX_RAZAO_COMPRESSAO = 1000  # membro grande com razão acima disso é assinatura de zip bomb
MAX_LINHAS = 100_000


def _checar_zip(z: zipfile.ZipFile) -> None:
    infos = z.infolist()
    if sum(i.file_size for i in infos) > MAX_DESCOMPRIMIDO:
        raise ArquivoSuspeito(f"tamanho descomprimido acima de {MAX_DESCOMPRIMIDO // (1024 * 1024)} MB")
    for i in infos:
        if i.file_size > 5 * 1024 * 1024 and i.compress_size and i.file_size / i.compress_size > MAX_RAZAO_COMPRESSAO:
            raise ArquivoSuspeito(f"membro '{i.filename}' com razão de compressão {i.file_size // i.compress_size}:1 (zip bomb)")


# --------------------------------------------------------------------------- HTML
_BLOCOS_HTML = ("p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "tr", "dt", "dd", "figcaption")
_OCULTO_XPATH = ("//*[@hidden or @aria-hidden='true' or contains(translate(@style,' ',''),'display:none') "
                 "or contains(translate(@style,' ',''),'visibility:hidden') or contains(translate(@style,' ',''),'font-size:0')]")


def extrair_html(path: Path) -> dict:
    """Página HTML salva: parágrafos, itens, títulos e linhas de tabela. Texto oculto é ignorado e avisado."""
    from lxml import html as lh

    bruto = path.read_bytes()
    avisos, blocos, brutos = [], [], []
    # sem <meta charset> o lxml assume latin-1 e estraga a acentuação: decodifica aqui (UTF-8 estrito, depois windows-1252)
    cab = bruto[:2048].decode("ascii", errors="ignore")
    m_cs = re.search(r"charset\s*=\s*[\"']?([\w-]+)", cab, re.I)
    try:
        texto_html = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        cs = m_cs.group(1) if m_cs else "windows-1252"
        try:
            texto_html = bruto.decode(cs)
        except (LookupError, UnicodeDecodeError):
            texto_html = bruto.decode("windows-1252", errors="replace")
        avisos.append(_aviso("codificacao_assumida", f"não era UTF-8; lido como {cs}"))
    texto_html = re.sub(r"^\s*<\?xml[^>]*\?>", "", texto_html)  # lxml recusa str com declaração de encoding
    raiz = lh.fromstring(texto_html, parser=lh.HTMLParser(no_network=True, remove_comments=True, remove_pis=True, huge_tree=False))
    for el in raiz.xpath("//script|//style|//noscript|//template"):
        el.drop_tree()
    ocultos = []
    for el in raiz.xpath(_OCULTO_XPATH):
        t = " ".join(el.text_content().split())
        if t:
            ocultos.append(t[:80])
        el.drop_tree()
    if ocultos:
        avisos.append(_aviso("texto_oculto_html", f"{len(ocultos)} trecho(s) invisível(is) ignorado(s) (possível injeção): {ocultos[:2]}"))
    n_img = len(raiz.xpath("//img"))
    if n_img:
        avisos.append(_aviso("parte_nao_extraida", f"{n_img} imagem(ns) não lida(s): texto em imagem não é extraído"))
    secao, npar, ntab, tabelas = "corpo", 0, 0, {}
    for el in raiz.iter():
        if not isinstance(el.tag, str) or el.tag not in _BLOCOS_HTML or el.xpath(".//*[self::" + " or self::".join(_BLOCOS_HTML) + "]"):
            continue
        if el.tag == "tr":
            tab = next((a for a in el.iterancestors("table")), None)
            if tab is not None and id(tab) not in tabelas:
                ntab += 1
                tabelas[id(tab)] = [ntab, 0]
            numero, linha = tabelas.get(id(tab), [0, 0]) if tab is not None else (0, 0)
            if tab is not None:
                tabelas[id(tab)][1] += 1
                linha = tabelas[id(tab)][1]
            texto = " | ".join(_ws(c.text_content()) for c in el.xpath("./td|./th"))
            loc = f"tab.{numero}.lin.{linha}"
            if not texto.strip(" |"):
                continue
        else:
            texto = _ws(el.text_content())
            if not texto:
                continue
            npar += 1
            loc = f"html.par.{npar}"
            if el.tag.startswith("h") and len(el.tag) == 2:
                secao = _slug(texto)
        citacao = el.tag == "blockquote" or any(True for _ in el.iterancestors("blockquote"))
        blocos.append({"page": None, "locator": loc, "section": secao, "texto": texto, "is_quote": citacao,
                       "quote_basis": "blockquote" if citacao else None, "tags": []})
        brutos.append(texto)
    return {"status": "ok" if blocos else "no_text", "page_count": None, "blocks": _finalizar_blocos(blocos),
            "warnings": avisos, "text_sha256": _hash_texto(brutos)}


# --------------------------------------------------------------------------- CSV, TSV
def extrair_csv(path: Path) -> dict:
    import csv
    import io

    avisos, bruto = [], path.read_bytes()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("windows-1252", errors="replace")
        avisos.append(_aviso("codificacao_assumida", "não era UTF-8; lido como windows-1252"))
    if path.suffix.lower() == ".tsv":
        delim = "\t"
    else:
        try:
            delim = csv.Sniffer().sniff(texto[:4096], delimiters=",;|\t").delimiter
        except csv.Error:
            delim = ","
    blocos, brutos, parcial = [], [], False
    for n, linha in enumerate(csv.reader(io.StringIO(texto), delimiter=delim), 1):
        if n > MAX_LINHAS:
            avisos.append(_aviso("truncado", f"lidas {MAX_LINHAS} linhas"))
            parcial = True
            break
        t = " | ".join(_ws(c) for c in linha)
        if t.strip(" |"):
            blocos.append({"page": None, "locator": f"tab.1.lin.{n}", "section": "planilha", "texto": t,
                           "is_quote": False, "quote_basis": None, "tags": ["cabecalho"] if n == 1 else []})
            brutos.append(t)
    return {"status": "no_text" if not blocos else ("partial" if parcial else "ok"), "page_count": None,
            "blocks": _finalizar_blocos(blocos), "warnings": avisos, "text_sha256": _hash_texto(brutos)}


# --------------------------------------------------------------------------- XLSX
_NS_X = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_FORMATOS_DATA = set(range(14, 23)) | {27, 30, 36, 45, 46, 47, 50, 57}


def _serial_para_iso(n: float) -> str:
    from datetime import datetime as _dt, timedelta

    base = _dt(1899, 12, 30)  # sistema 1900 com o erro do ano bissexto: vale para seriais acima de 60
    d = base + timedelta(days=n)
    return d.date().isoformat() if abs(n - int(n)) < 1e-9 else d.isoformat(timespec="minutes")


def _coluna(ref: str) -> int:
    letras = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letras:
        n = n * 26 + ord(ch) - 64
    return n - 1


def extrair_xlsx(path: Path) -> dict:
    """Planilha .xlsx lida direto do XML: valores em cache, datas convertidas, planilhas ocultas ignoradas e avisadas."""
    avisos, blocos, brutos, parcial = [], [], [], False
    with zipfile.ZipFile(path) as z:
        _checar_zip(z)
        nomes = set(z.namelist())

        def ler(n):
            return _xml_seguro(z.read(n))

        wb = ler("xl/workbook.xml")
        rels = {r.get("Id"): r.get("Target") for r in ler("xl/_rels/workbook.xml.rels")}
        folhas = [(s.get("name"), s.get("state", "visible"), rels.get(s.get(f"{{{_NS_R}}}id"))) for s in wb.iter(f"{{{_NS_X}}}sheet")]
        textos = []
        if "xl/sharedStrings.xml" in nomes:
            textos = ["".join(t.text or "" for t in si.iter(f"{{{_NS_X}}}t")) for si in ler("xl/sharedStrings.xml").iter(f"{{{_NS_X}}}si")]
        datas = set()
        if "xl/styles.xml" in nomes:
            est = ler("xl/styles.xml")
            custom = {int(n.get("numFmtId")): n.get("formatCode", "") for n in est.iter(f"{{{_NS_X}}}numFmt")}
            xfs = [x for cx in est.iter(f"{{{_NS_X}}}cellXfs") for x in cx]
            for k, x in enumerate(xfs):
                fid = int(x.get("numFmtId", 0))
                codigo = re.sub(r'"[^"]*"|\[[^\]]*\]', "", custom.get(fid, ""))
                if fid in _FORMATOS_DATA or re.search(r"(?i)[dmy]{2}|h{1,2}:", codigo):
                    datas.add(k)
        formulas_sem_valor = formulas = linhas_lidas = 0
        for nome, estado, alvo in folhas:
            if estado != "visible":
                parcial = True
                avisos.append(_aviso("planilha_oculta", f"planilha '{nome}' ({estado}) ignorada: conteúdo oculto não entra"))
                continue
            caminho = "xl/" + (alvo or "").lstrip("/").removeprefix("xl/")
            if caminho not in nomes:
                avisos.append(_aviso("planilha_nao_encontrada", f"'{nome}' aponta para {alvo}, que não existe no arquivo"))
                parcial = True
                continue
            for linha in ler(caminho).iter(f"{{{_NS_X}}}row"):
                linhas_lidas += 1
                if linhas_lidas > MAX_LINHAS:
                    avisos.append(_aviso("truncado", f"lidas {MAX_LINHAS} linhas"))
                    parcial = True
                    break
                celulas: dict[int, str] = {}
                for c in linha.iter(f"{{{_NS_X}}}c"):
                    tipo, v, f_, inl = c.get("t"), c.find(f"{{{_NS_X}}}v"), c.find(f"{{{_NS_X}}}f"), c.find(f"{{{_NS_X}}}is")
                    if f_ is not None:
                        formulas += 1
                        formulas_sem_valor += v is None
                    if tipo == "inlineStr" and inl is not None:
                        valor = "".join(t.text or "" for t in inl.iter(f"{{{_NS_X}}}t"))
                    elif v is None or v.text is None:
                        continue
                    elif tipo == "s":
                        valor = textos[int(v.text)]
                    elif tipo == "b":
                        valor = "VERDADEIRO" if v.text == "1" else "FALSO"
                    elif tipo == "e":
                        valor = f"#ERRO({v.text})"
                    elif tipo == "str":
                        valor = v.text
                    else:
                        valor = v.text
                        if int(c.get("s", 0)) in datas:
                            try:
                                valor = f"{_serial_para_iso(float(v.text))} (serial {v.text})"
                            except (ValueError, OverflowError):
                                pass
                    celulas[_coluna(c.get("r", "A1"))] = _ws(valor)
                if celulas:
                    texto = " | ".join(celulas.get(i, "") for i in range(max(celulas) + 1)).rstrip(" |")
                    if texto.strip():
                        blocos.append({"page": None, "locator": f"plan.{_slug(nome)}.lin.{linha.get('r', linhas_lidas)}",
                                       "section": _slug(nome), "texto": texto, "is_quote": False, "quote_basis": None, "tags": []})
                        brutos.append(texto)
        if formulas_sem_valor:
            parcial = True
            avisos.append(_aviso("formula_sem_valor", f"{formulas_sem_valor} fórmula(s) sem valor em cache: abra e salve a planilha no Excel"))
        elif formulas:
            avisos.append(_aviso("formulas_nao_recalculadas", f"{formulas} fórmula(s): o valor lido é o do último cálculo salvo"))
        if any(re.match(r"xl/(comments|threadedComments)", n) for n in nomes):
            parcial = True
            avisos.append(_aviso("parte_nao_extraida", "comentários da planilha não foram extraídos"))
    return {"status": "no_text" if not blocos else ("partial" if parcial else "ok"), "page_count": None,
            "blocks": _finalizar_blocos(blocos), "warnings": avisos, "text_sha256": _hash_texto(brutos)}


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


def extrair(caminho, cache_dir: str | None = None, max_mb: float = 60.0, ocr: bool = False):
    """Retorna (documento, cache_hit). Nunca levanta exceção por conteúdo do arquivo.

    ocr=True tenta o OCR (Tesseract) nas páginas de PDF sem texto ou cobertas por imagem."""
    global _OCR
    _OCR = bool(ocr)
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
                                ".eml": "message/rfc822", ".html": "text/html", ".htm": "text/html", ".csv": "text/csv",
                                ".tsv": "text/tab-separated-values",
                                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}[p.suffix.lower()]})
    arq_cache = Path(cache_dir) / f"{sha[:32]}-{EXTRACTOR_VERSION}-{PARAMS_HASH}{'-ocr' if ocr else ''}.json" if cache_dir else None
    if arq_cache and arq_cache.is_file():
        with contextlib.suppress(Exception):
            doc = json.loads(arq_cache.read_text(encoding="utf-8"))
            doc["path"] = str(caminho)
            return doc, True
    try:
        with warnings.catch_warnings(), contextlib.redirect_stdout(sys.stderr):
            warnings.simplefilter("ignore")
            r = {".pdf": extrair_pdf, ".docx": extrair_docx, ".eml": extrair_eml, ".html": extrair_html, ".htm": extrair_html,
                 ".csv": extrair_csv, ".tsv": extrair_csv, ".xlsx": extrair_xlsx}.get(p.suffix.lower(), extrair_texto)(p)
    except ArquivoSuspeito as e:
        return falha("arquivo_suspeito", str(e))
    except Exception as e:  # noqa: BLE001 - arquivo corrompido ou formato inesperado
        return falha("erro_de_leitura", f"{type(e).__name__}: {e}")
    # text_sha256 identifica o texto lido, independente do arquivo (o mesmo acórdão baixado duas vezes
    # pode ter bytes diferentes) e da segmentação em blocos; cada leitor o calcula sobre o texto bruto
    doc = {**base, "extractor_versions": _versoes(), **r}
    # texto que parece dirigido ao modelo: só avisa; o conteúdo continua sendo dado
    suspeitas = []
    for b in doc["blocks"]:
        for a in injecao.detectar(b["text"]):
            suspeitas.append({"locator": b.get("locator"), "block_id": b["id"], **a})
    if suspeitas:
        doc["instrucoes_suspeitas"] = suspeitas[:30]
        for x in suspeitas[:5]:
            doc["warnings"].append(_aviso("possivel_instrucao_embutida",
                                          f"{x['locator']}: {x['padrao']}: {x['trecho']!r} (tratado como dado, não como ordem)"))
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
    ap.add_argument("--ocr", action="store_true", help="OCR (Tesseract) nas páginas de PDF sem texto; blocos ficam com a tag 'ocr'")
    a = ap.parse_args(argv)
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    docs, hits = [], 0
    for arq in a.arquivos:
        d, hit = extrair(arq, None if a.no_cache else a.cache_dir, a.max_mb, a.ocr)
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
