"""Validador de facts.json e claims.json (regras de shared/estados.md e shared/dados.md).

Confere forma e coerência entre estado, fontes e evidências. Não julga se a fonte
apoia a proposição. Com --extracoes (saída de extract.py) confere também documento,
bloco, trecho e hash contra o texto realmente extraído.

Uso:  python scripts/validate.py ARQUIVO.json [--extracoes extract.json ...] [--estrito]
Saída: JSON no stdout. Código 0 = válido, 1 = inválido (com --estrito, aviso também reprova).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # cnj.py, mesmo com python -P
import privacidade  # noqa: E402

SCHEMA_VERSION = "1"
ESTADOS = ("unverified", "partial", "supported", "unsupported")
KIND_FATO = ("documentado", "alegacao", "inferencia", "lacuna", "informado")
RELEVANCIA = ("alta", "media", "baixa")
PRIV = ("ok", "flag", "review")
SOURCE_REL = ("contradiz", "nao_trata")
OBTIDO = ("live_source", "user_supplied_source")
CONFLITOS = ("cleared", "pending", "not-run", "waived", "nao_aplicavel")
PRIVILEGIO = ("triado", "misto", "nao_triado", "nao_aplicavel")
PAPEIS_PARTE = ("autor", "reu", "terceiro", "advogado", "juizo", "perito", "testemunha", "outro")
PRECISOES = {"dia": 10, "mes": 7, "ano": 4, "indefinida": None}
TIPOS = ("norma", "precedente", "sumula", "tema", "doutrina", "outro")
EXISTENCIA = ("confirmada", "nao_confirmada", "indisponivel")
QUOTE = ("conferida", "divergente", "nao_conferida")
ORIGENS = ("oficial", "secundaria")
ACESSOS = ("lida", "nao_acessada", "source_missing")
ESCOPOS_TEXTO = ("ementa", "inteiro_teor", "texto_legal", "outro")
ESCOPOS_PROPOSICAO = ("ementa", "inteiro_teor")
VIGENCIA = ("vigente", "revogada", "nao_verificada")
_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_ISO_PARCIAL = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


class Resultado:
    def __init__(self):
        self.erros: list[dict] = []
        self.avisos: list[dict] = []

    def erro(self, codigo, caminho, mensagem):
        self.erros.append({"codigo": codigo, "caminho": caminho, "mensagem": mensagem})

    def aviso(self, codigo, caminho, mensagem):
        self.avisos.append({"codigo": codigo, "caminho": caminho, "mensagem": mensagem})


# --------------------------------------------------------------------------- utilidades
def _texto(r, obj, chave, caminho, obrigatorio=True):
    v = obj.get(chave)
    if v is None:
        if obrigatorio:
            r.erro("campo_obrigatorio", f"{caminho}.{chave}", f"'{chave}' é obrigatório")
        return None
    if not isinstance(v, str) or not v.strip():
        r.erro("tipo_invalido", f"{caminho}.{chave}", f"'{chave}' deve ser texto não vazio")
        return None
    return v


def _enum(r, obj, chave, caminho, valores, obrigatorio=True):
    v = obj.get(chave)
    if v is None:
        if obrigatorio:
            r.erro("campo_obrigatorio", f"{caminho}.{chave}", f"'{chave}' é obrigatório ({'|'.join(valores)})")
        return None
    if v not in valores:
        r.erro("valor_invalido", f"{caminho}.{chave}", f"'{v}' não é válido; use: {', '.join(valores)}")
        return None
    return v


def _data_valida(s) -> bool:
    if not isinstance(s, str):
        return False
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _norm(s: str) -> str:
    """Compara sem espaços, caixa nem hífen (a quebra de linha com hífen no PDF não pode reprovar um trecho certo)."""
    return re.sub(r"[\s\-­]+", "", unicodedata.normalize("NFC", s)).casefold()


def _contem(texto: str, trecho: str) -> bool:
    """O trecho está no texto, ignorando espaços e caixa; '[...]' e '…' separam fragmentos em ordem."""
    t, pos = _norm(texto), 0
    for parte in re.split(r"\[\.\.\.\]|…", trecho):
        parte = _norm(parte)
        if not parte:
            continue
        i = t.find(parte, pos)
        if i < 0:
            return False
        pos = i + len(parte)
    return True


def carregar_extracoes(caminhos) -> dict:
    """Índice document_id -> documento a partir de saídas do extract.py."""
    idx = {}
    for c in caminhos:
        obj = json.loads(Path(c).read_text(encoding="utf-8"))
        for d in obj.get("documents", [obj] if "blocks" in obj else []):
            if d.get("document_id"):
                idx[d["document_id"]] = d
    return idx


def _paginas_do_localizador(locator):
    return [(int(a), int(b or a)) for a, b in re.findall(r"\bp\.\s*(\d+)(?:\s*[-–]\s*(\d+))?", locator or "")]


def _localizador_incoerente(locator, ach):
    """Mensagem se o localizador informado não bate com onde o trecho foi de fato achado."""
    pgs = _paginas_do_localizador(locator)
    com_pagina = [b for b in ach if b.get("page")]
    if pgs and com_pagina:
        for b in com_pagina:
            fim = b.get("page_end") or b["page"]
            if any(a <= fim and b["page"] <= z for a, z in pgs):
                return None
        achado = ", ".join(sorted({b["locator"] for b in com_pagina}))
        return f"o localizador informa '{locator}', mas o trecho está em {achado}"
    marcadores = re.findall(r"\b(?:par\.\d+|tab\.\d+\.lin\.\d+|nota(?:fim)?\.[\w-]+|email\.cabecalho)", locator or "")

    def casa(loc):  # 'par.2' casa com 'par.2' e com 'email.corpo.par.2'
        return any(loc == m or str(loc).endswith("." + m) for m in marcadores)

    if marcadores and not any(casa(b.get("locator")) for b in ach):
        achado = ", ".join(sorted({str(b.get("locator")) for b in ach}))
        return f"o localizador informa '{locator}', mas o trecho está em {achado}"
    return None


def _avisar_dados_pessoais(r, caminho, excerpt):
    """Avisa (sem repetir o valor) quando o trecho citado traz CPF, CNPJ, cartão, e-mail ou telefone."""
    if isinstance(excerpt, str):
        tipos = privacidade.tipos_presentes(excerpt)
        if tipos:
            r.aviso("dado_pessoal_no_trecho", f"{caminho}.excerpt",
                    f"o trecho contém {', '.join(tipos)}: troque o número por [...] para não repetir o dado nos relatórios")


SECOES_NARRATIVAS = ("relatorio", "voto", "relatorio_e_voto", "decisao", "sentenca", "despacho", "parecer")


def _avaliar_trecho(r, caminho, excerpt):
    """Avisos sobre o próprio trecho citado: dado pessoal e trecho curto demais para servir de prova."""
    if not isinstance(excerpt, str):
        return
    _avisar_dados_pessoais(r, caminho, excerpt)
    if len(re.findall(r"\w+", re.sub(r"\[\.\.\.\]|…", " ", excerpt))) < 4:
        r.aviso("trecho_curto", f"{caminho}.excerpt",
                "trecho com menos de 4 palavras é prova fraca (pode estar em vários lugares): cite a frase inteira")


def _blocos_do_trecho(doc, bid, excerpt):
    """Blocos em que o trecho aparece. Sem block_id, aceita trecho que atravessa dois blocos consecutivos."""
    blocos = doc["blocks"]
    if bid:
        bloco = next((b for b in blocos if b["id"] == bid), None)
        if bloco is None:
            return None
        candidatos = [bloco]
    else:
        candidatos = blocos
    ach = [b for b in candidatos if excerpt and _contem(b["text"], excerpt)]
    if not ach and not bid and excerpt:
        for a, b in zip(blocos, blocos[1:]):
            if _contem(a["text"] + " " + b["text"], excerpt):
                fim = max(x for x in (a.get("page_end"), b.get("page_end"), a.get("page"), b.get("page")) if x) \
                    if (a.get("page") or b.get("page")) else None
                tags = set(a.get("tags", [])) | set(b.get("tags", []))
                if bool(a.get("is_quote")) != bool(b.get("is_quote")):
                    tags.add("atribuicao_ambigua")
                ach.append({**a, "text": a["text"] + " " + b["text"], "page_end": fim,
                            "is_quote": bool(a.get("is_quote") and b.get("is_quote")),
                            "tags": sorted(tags)})
    return ach


def _conferir_trecho(r, caminho, ref, locator, excerpt, idx, kind=None):
    """Confere document_id/block_id/excerpt contra a extração. ref é o dict com os campos.

    kind: 'documentado', 'alegacao' (fatos), 'claim' (a proposição decide o aviso) ou None."""
    did = ref.get("document_id")
    if idx is None or not isinstance(did, str) or not did.strip():
        return
    doc = idx.get(did)
    if doc is None:
        r.erro("documento_nao_extraido", f"{caminho}.document_id", f"'{did}' não consta nas extrações fornecidas")
        return
    bid = ref.get("block_id")
    ach = _blocos_do_trecho(doc, bid, excerpt)
    if ach is None:
        r.erro("bloco_inexistente", f"{caminho}.block_id", f"bloco '{bid}' não existe em {did}")
        return
    if ach and any("ocr" in b.get("tags", []) for b in ach):
        r.aviso("trecho_de_ocr", f"{caminho}.excerpt",
                "o trecho vem de OCR: dígitos, acentos e nomes podem estar errados; confira no original antes de tratar como prova")
    if not ach:
        r.erro("trecho_nao_encontrado", f"{caminho}.excerpt",
               f"o trecho não está no texto extraído de {did}" + (f" (bloco {bid})" if bid else ""))
    elif (msg := _localizador_incoerente(locator, ach)):
        r.erro("localizador_incoerente", f"{caminho}.locator", msg)
    elif all(b.get("is_quote") for b in ach):
        if kind == "documentado":
            r.aviso("documentado_em_citacao", f"{caminho}.excerpt",
                    "fato 'documentado' apoiado só em trecho transcrito: quem narra é outro texto; considere 'alegacao'")
        elif kind != "claim":
            r.aviso("trecho_em_citacao", f"{caminho}.excerpt",
                    "o trecho está em passagem marcada como citação: confirme quem fala (o órgão julgador ou o texto transcrito)")
    elif kind == "documentado" and all(b.get("section") in SECOES_NARRATIVAS and "dispositivo" not in b.get("tags", [])
                                       for b in ach):
        r.aviso("documentado_em_narrativa", f"{caminho}.excerpt",
                "decisões e peças narram fatos que não provam: confirme que o fato 'documentado' é o próprio ato (decisão, "
                "protocolo, assinatura) e não um fato material narrado")


def _contexto_do_pinpoint(idx, s):
    """Atribuição no local citado, sem aproveitar outra ocorrência do texto."""
    pin = s.get("pinpoint") or {}
    if (not isinstance(pin, dict) or idx is None or not isinstance(s.get("document_id"), str)
            or s["document_id"] not in idx or not isinstance(pin.get("excerpt"), str)):
        return []
    ach = _blocos_do_trecho(idx[s["document_id"]], s.get("block_id"), pin["excerpt"])
    return [b for b in (ach or []) if not _localizador_incoerente(pin.get("locator"), [b])]


def _so_em_citacao(idx, s):
    """True se o pinpoint só existe em passagem transcrita; None se não dá para saber."""
    ach = _contexto_do_pinpoint(idx, s)
    return bool(ach) and all(b.get("is_quote") for b in ach) if ach else None


# --------------------------------------------------------------------------- facts.json
def validar_facts(obj, idx=None) -> Resultado:
    r = Resultado()
    if not isinstance(obj, dict) or not isinstance(obj.get("facts"), list):
        r.erro("estrutura", "$", "esperado objeto com a lista 'facts'")
        return r
    if obj.get("schema_version") != SCHEMA_VERSION:
        r.erro("schema_version", "$.schema_version", f"esperado '{SCHEMA_VERSION}'")
    if not obj["facts"]:
        r.aviso("lista_vazia", "$.facts", "nenhum fato registrado")
    ids = [f.get("id") for f in obj["facts"] if isinstance(f, dict)]
    existentes = set(ids)
    vistos: set = set()
    por_id = {f["id"]: f for f in obj["facts"] if isinstance(f, dict) and isinstance(f.get("id"), str)}
    for i, f in enumerate(obj["facts"]):
        c = f"$.facts[{i}]"
        if not isinstance(f, dict):
            r.erro("tipo_invalido", c, "cada fato deve ser um objeto")
            continue
        fid = _texto(r, f, "id", c)
        if fid:
            if not _ID.match(fid):
                r.erro("id_invalido", f"{c}.id", "use apenas letras, números, '_' e '-'")
            if fid in vistos:
                r.erro("id_duplicado", f"{c}.id", f"id '{fid}' repetido")
            vistos.add(fid)
        kind = _enum(r, f, "kind", c, KIND_FATO)
        _texto(r, f, "text", c)
        if kind in ("documentado", "alegacao"):
            s = f.get("source")
            if not isinstance(s, dict):
                r.erro("campo_obrigatorio", f"{c}.source", f"fato '{kind}' exige 'source' (documento, localizador, trecho)")
            else:
                for k in ("document_id", "locator", "excerpt"):
                    _texto(r, s, k, f"{c}.source")
                if isinstance(s.get("excerpt"), str):
                    _conferir_trecho(r, f"{c}.source", s, s.get("locator"), s["excerpt"], idx, kind)
                    _avaliar_trecho(r, f"{c}.source", s["excerpt"])
        if kind == "lacuna":
            _texto(r, f, "document_id", c, obrigatorio=False)
        if kind == "informado":
            r.aviso("fato_informado_sem_documento", c,
                    f"fato '{fid}' foi informado pelo usuário e não tem documento: obtenha o documento ou mantenha a marca")
        outras = f.get("other_sources")
        if outras is not None:
            if not isinstance(outras, list):
                r.erro("tipo_invalido", f"{c}.other_sources", "'other_sources' deve ser lista de fontes")
            else:
                for j, o in enumerate(outras):
                    cj = f"{c}.other_sources[{j}]"
                    if not isinstance(o, dict):
                        r.erro("tipo_invalido", cj, "cada fonte deve ser objeto")
                        continue
                    for k in ("document_id", "locator", "excerpt"):
                        _texto(r, o, k, cj)
                    if isinstance(o.get("excerpt"), str):
                        _conferir_trecho(r, cj, o, o.get("locator"), o["excerpt"], idx, kind)
                        _avaliar_trecho(r, cj, o["excerpt"])
        rel = _enum(r, f, "relevancia", c, RELEVANCIA, obrigatorio=False)
        if rel == "alta":
            _texto(r, f, "relevancia_motivo", c)
        if f.get("relevancia_incerta") is not None and not isinstance(f["relevancia_incerta"], bool):
            r.erro("tipo_invalido", f"{c}.relevancia_incerta", "'relevancia_incerta' deve ser verdadeiro ou falso")
        _enum(r, f, "priv", c, PRIV, obrigatorio=False)
        if kind in ("documentado", "alegacao") and isinstance(f.get("date"), dict) and isinstance(f.get("source"), dict):
            exc, orig = f["source"].get("excerpt"), f["date"].get("original")
            if isinstance(exc, str) and isinstance(orig, str) and orig.strip() and not _contem(exc, orig):
                r.erro("data_fora_do_trecho", f"{c}.date.original",
                       f"a data '{orig}' não aparece no trecho citado: a data precisa estar na evidência")
        if kind == "alegacao":
            _texto(r, f, "alleged_by", c)
        if kind == "inferencia":
            b = f.get("basis")
            if not isinstance(b, list) or not b:
                r.erro("campo_obrigatorio", f"{c}.basis", "inferência exige 'basis' (ids de fatos de apoio)")
            else:
                for x in b:
                    if x not in existentes:
                        r.erro("referencia_inexistente", f"{c}.basis", f"fato '{x}' não existe")
                    elif x == fid:
                        r.erro("referencia_circular", f"{c}.basis", "a inferência não pode se apoiar em si mesma")
        if (d := f.get("date")) is not None:
            _validar_data(r, d, f"{c}.date")
        for x in f.get("conflicts_with") or []:
            if x not in existentes:
                r.erro("referencia_inexistente", f"{c}.conflicts_with", f"fato '{x}' não existe")
            elif fid and fid not in (por_id[x].get("conflicts_with") or []):
                r.aviso("conflito_nao_reciproco", f"{c}.conflicts_with", f"'{x}' não aponta de volta para '{fid}'")
    avaliados = [f for f in obj["facts"] if isinstance(f, dict) and f.get("relevancia") in RELEVANCIA]
    if len(avaliados) >= 6 and sum(1 for f in avaliados if f["relevancia"] == "alta") / len(avaliados) > 0.5:
        r.aviso("relevancia_excessiva", "$.facts", "mais da metade dos fatos avaliados é 'alta': se tudo é central, a marca perde o sentido")
    return r


_MESES = {"janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7,
          "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
_DATA_NUM = re.compile(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{4}|\d{2})(?!\d)")
_MES_ANO = re.compile(r"(?<![\d/.\-])(\d{1,2})\s*[/.\-]\s*((?:19|20)\d{2})(?!\d)")
_ANO4 = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")


def _componentes_da_data(original: str) -> dict:
    """Ano, mês e dia que o texto da data realmente contém (não o que alguém deduziu dele)."""
    anos, meses, dias = set(), set(), set()
    for m in _DATA_NUM.finditer(original):
        d, mes, a = int(m.group(1)), int(m.group(2)), m.group(3)
        dias.add(d)
        meses.add(mes)
        anos.add(int(a) if len(a) == 4 else 2000 + int(a))
    for m in _MES_ANO.finditer(original):  # 03/2026
        if 1 <= int(m.group(1)) <= 12:
            meses.add(int(m.group(1)))
    anos |= {int(a) for a in _ANO4.findall(original)}
    baixo = original.lower()
    for nome, n in _MESES.items():
        for m in re.finditer(r"(?<![a-zçã])" + nome + r"(?![a-zçã])", baixo):
            meses.add(n)
            ant = re.search(r"(\d{1,2})\s*[º°o]?\s*(?:de\s+)?$", baixo[:m.start()])
            if ant:
                dias.add(int(ant.group(1)))
    for m in re.finditer(r"\bdia\s+(\d{1,2})\b", baixo):
        dias.add(int(m.group(1)))
    return {"anos": anos, "meses": meses, "dias": dias}


def _validar_data(r, d, c):
    if not isinstance(d, dict):
        r.erro("tipo_invalido", c, "'date' deve ser objeto")
        return
    _texto(r, d, "original", c)
    prec = _enum(r, d, "precision", c, tuple(PRECISOES))
    iso = d.get("iso", "__ausente__")
    if iso == "__ausente__":
        r.erro("campo_obrigatorio", f"{c}.iso", "'iso' é obrigatório (use null se indefinida)")
        return
    if prec is None:
        return
    if PRECISOES[prec] is None:
        if iso is not None:
            r.erro("data_incoerente", f"{c}.iso", "precisão 'indefinida' exige iso=null: não invente precisão")
        return
    n_erros = len(r.erros)
    if not isinstance(iso, str) or not _ISO_PARCIAL.match(iso) or len(iso) != PRECISOES[prec]:
        r.erro("data_incoerente", f"{c}.iso", f"precisão '{prec}' exige formato com {PRECISOES[prec]} caracteres (AAAA[-MM[-DD]])")
    elif len(iso) == 10 and not _data_valida(iso):
        r.erro("data_invalida", f"{c}.iso", f"'{iso}' não é data de calendário válida")
    elif len(iso) == 7 and not 1 <= int(iso[5:]) <= 12:
        r.erro("data_invalida", f"{c}.iso", f"mês inválido em '{iso}'")
    if len(r.erros) == n_erros and isinstance(iso, str) and isinstance(d.get("original"), str):
        comp = _componentes_da_data(d["original"])
        ano = int(iso[:4])
        if ano not in comp["anos"]:
            r.erro("data_inventada", f"{c}.iso", f"o ano {ano} não aparece em '{d['original']}': ano deduzido do contexto não vira data; "
                                                   "use precisão 'indefinida' (iso=null) e registre a lacuna")
        elif len(iso) >= 7 and int(iso[5:7]) not in comp["meses"]:
            r.erro("data_inventada", f"{c}.iso", f"o mês {iso[5:7]} não aparece em '{d['original']}'")
        elif len(iso) == 10 and int(iso[8:]) not in comp["dias"]:
            r.erro("data_inventada", f"{c}.iso", f"o dia {iso[8:]} não aparece em '{d['original']}': use precisão 'mes' ou 'ano'")


# --------------------------------------------------------------------------- claims.json
def validar_claims(obj, idx=None) -> Resultado:
    r = Resultado()
    if not isinstance(obj, dict) or not isinstance(obj.get("claims"), list):
        r.erro("estrutura", "$", "esperado objeto com a lista 'claims'")
        return r
    if obj.get("schema_version") != SCHEMA_VERSION:
        r.erro("schema_version", "$.schema_version", f"esperado '{SCHEMA_VERSION}'")
    if not obj["claims"]:
        r.aviso("lista_vazia", "$.claims", "nenhuma proposição registrada")
    vistos: set = set()
    dependencias: list[tuple] = []
    for i, cl in enumerate(obj["claims"]):
        c = f"$.claims[{i}]"
        if not isinstance(cl, dict):
            r.erro("tipo_invalido", c, "cada proposição deve ser um objeto")
            continue
        cid = _texto(r, cl, "id", c)
        if cid:
            if not _ID.match(cid):
                r.erro("id_invalido", f"{c}.id", "use apenas letras, números, '_' e '-'")
            if cid in vistos:
                r.erro("id_duplicado", f"{c}.id", f"id '{cid}' repetido")
            vistos.add(cid)
        _texto(r, cl, "proposition", c)
        tipo = _enum(r, cl, "tipo", c, TIPOS, obrigatorio=False)
        status = _enum(r, cl, "status", c, ESTADOS)
        exist = _enum(r, cl, "existence", c, EXISTENCIA)
        escopo = _enum(r, cl, "proposition_scope", c, ESCOPOS_PROPOSICAO, obrigatorio=False)
        if escopo is None and tipo in ("precedente", "tema"):
            escopo = "inteiro_teor"
        quote = _enum(r, cl, "quote_status", c, QUOTE, obrigatorio=status not in (None, "unverified"))
        rel = _enum(r, cl, "source_relation", c, SOURCE_REL, obrigatorio=False)
        _texto(r, cl, "applicability", c, obrigatorio=False)
        _texto(r, cl, "suggested_fix", c, obrigatorio=False)
        _texto(r, cl, "draft_locator", c, obrigatorio=False)
        dep = cl.get("depends_on")
        if dep is not None:
            if not isinstance(dep, list) or not all(isinstance(x, str) for x in dep):
                r.erro("tipo_invalido", f"{c}.depends_on", "'depends_on' deve ser lista de ids de proposições")
            else:
                dependencias.append((c, cid, dep))
        fontes = _validar_fontes(r, cl, c, idx)
        if status is None:
            continue
        if status == "unsupported" and rel is None:
            r.aviso("relacao_nao_informada", f"{c}.source_relation",
                    "diga se a fonte contradiz a proposição ('contradiz') ou não trata dela ('nao_trata'): muda a gravidade")
        elif status != "unsupported" and rel is not None:
            r.erro("relacao_incompativel", f"{c}.source_relation", "'source_relation' só se aplica ao estado 'unsupported'")
        if status == "supported" and tipo in ("precedente", "tema") and not cl.get("applicability"):
            r.aviso("aplicabilidade_nao_registrada", f"{c}.applicability",
                    "registre a aplicabilidade (órgão, classe, fatos e fase) ao caso: apoio à tese não é aplicabilidade")
        lidas = [s for s in fontes if s.get("access") == "lida"]
        oficiais = [s for s in lidas if s.get("origin") == "oficial"]
        if cl.get("cited_text") is not None and not isinstance(cl["cited_text"], bool):
            r.erro("tipo_invalido", f"{c}.cited_text", "'cited_text' deve ser verdadeiro ou falso")
        contextos = [_contexto_do_pinpoint(idx, s) for s in lidas]
        if any(any("atribuicao_ambigua" in b.get("tags", []) for b in ach)
               or len({bool(b.get("is_quote")) for b in ach}) > 1 for ach in contextos):
            registrar = r.erro if status == "supported" else r.aviso
            registrar("atribuicao_ambigua", f"{c}.sources",
                      "o trecho tem fronteira incerta ou autorias distintas no local citado: confira a atribuição "
                      "no original e restrinja o registro; cited_text=true não resolve uma fronteira incerta")
        # Uma fonte secundária não substitui fundamento próprio da fonte oficial.
        em_citacao = [_so_em_citacao(idx, s) for s in (oficiais if status == "supported" else lidas)]
        if em_citacao and all(x is True for x in em_citacao):
            if status == "supported" and tipo in ("precedente", "tema", "sumula") and cl.get("cited_text") is not True:
                r.erro("trecho_so_em_citacao", f"{c}.sources",
                       "o apoio está só em texto transcrito de outra decisão, não no fundamento do órgão julgador: cite o fundamento "
                       "do próprio órgão ou declare cited_text=true se a proposição é sobre o que a decisão transcreve")
            elif status in ("partial", "unsupported", "supported") and cl.get("cited_text") is not True:
                r.aviso("trecho_em_citacao", f"{c}.sources",
                        "os trechos estão em passagem transcrita: confirme quem fala (o órgão julgador ou o texto transcrito)")
        if status != "unverified" and exist is not None and exist != "confirmada":
            r.erro("existencia_incompativel", f"{c}.existence",
                   f"existence='{exist}' só combina com 'unverified': busca vazia ou fonte inacessível não prova inexistência")
        if status == "unverified" and lidas:
            r.erro("unverified_com_fonte_lida", f"{c}.status", "há fonte 'lida': reavalie o estado (partial, supported ou unsupported)")
        if status in ("partial", "supported", "unsupported") and not lidas:
            r.erro("estado_sem_fonte_lida", f"{c}.status", f"'{status}' exige ao menos uma fonte com access='lida'; sem leitura o estado é 'unverified'")
        if status in ("partial", "unsupported"):
            _texto(r, cl, "reason", c)
        if status == "partial":
            _texto(r, cl, "missing", c)
        if status == "supported" and lidas:
            if not oficiais:
                r.erro("teto_partial_sem_fonte_oficial", f"{c}.status",
                       "só há fonte secundária lida: o estado máximo é 'partial' até a fonte oficial ser lida")
            if quote is not None and quote != "conferida":
                r.erro("citacao_nao_conferida", f"{c}.quote_status", "'supported' exige quote_status='conferida'")
            if escopo == "inteiro_teor" and oficiais and not any(s.get("text_scope") == "inteiro_teor" for s in oficiais):
                r.erro("ementa_nao_equivale_a_inteiro_teor", f"{c}.sources",
                       "a proposição exige inteiro teor (ou declare proposition_scope='ementa'); a fonte oficial lida é só ementa/outro escopo")
            if tipo == "norma" and not any(isinstance(s.get("legal_time"), dict) for s in oficiais):
                r.aviso("vigencia_nao_verificada", f"{c}.sources", "apoio ao texto não prova vigência: registre legal_time")
        if status == "unsupported" and lidas and not oficiais:
            r.erro("unsupported_exige_fonte_oficial", f"{c}.status", "concluir que a fonte não apoia exige fonte oficial lida")
        if cl.get("central") is True and status == "unverified":
            r.aviso("tese_central_nao_verificada", f"{c}.status", f"tese central '{cid}' sem verificação")
        elif cl.get("central") is True and status in ("partial", "unsupported"):
            r.aviso("tese_central_sem_apoio_pleno", f"{c}.status", f"tese central '{cid}' está '{status}'")
    for c, cid, dep in dependencias:
        for x in dep:
            if x not in vistos:
                r.erro("referencia_inexistente", f"{c}.depends_on", f"proposição '{x}' não existe")
            elif x == cid:
                r.erro("referencia_circular", f"{c}.depends_on", "a proposição não pode depender de si mesma")
    return r


def _validar_fontes(r, cl, c, idx):
    fontes = cl.get("sources")
    if fontes is None:
        fontes = []
    if not isinstance(fontes, list):
        r.erro("tipo_invalido", f"{c}.sources", "'sources' deve ser lista")
        return []
    validas, vistos = [], set()
    for j, s in enumerate(fontes):
        p = f"{c}.sources[{j}]"
        if not isinstance(s, dict):
            r.erro("tipo_invalido", p, "cada fonte deve ser objeto")
            continue
        sid = _texto(r, s, "source_id", p)
        if sid in vistos:
            r.erro("id_duplicado", f"{p}.source_id", f"source_id '{sid}' repetido")
        vistos.add(sid)
        _enum(r, s, "origin", p, ORIGENS)
        _enum(r, s, "obtained_via", p, OBTIDO, obrigatorio=False)
        acesso = _enum(r, s, "access", p, ACESSOS)
        if acesso == "lida":
            did = _texto(r, s, "document_id", p)
            if not (isinstance(s.get("url"), str) and s["url"].strip()) and not (
                    isinstance(s.get("local_file"), str) and s["local_file"].strip()):
                r.erro("campo_obrigatorio", f"{p}.url", "fonte lida exige 'url' ou 'local_file'")
            if not _data_valida(s.get("retrieved_at")):
                r.erro("data_invalida", f"{p}.retrieved_at", "fonte lida exige 'retrieved_at' em ISO 8601")
            if not isinstance(s.get("content_hash"), str) or not _HASH.match(s["content_hash"]):
                r.erro("hash_invalido", f"{p}.content_hash", "fonte lida exige sha256 em 64 caracteres hexadecimais minúsculos")
            _enum(r, s, "text_scope", p, ESCOPOS_TEXTO)
            if s.get("text_scope") == "inteiro_teor" and idx is not None and did in idx:
                d = idx[did]
                if d.get("media_type") == "application/pdf" and not any(b.get("section") in SECOES_NARRATIVAS for b in d["blocks"]):
                    r.erro("inteiro_teor_sem_voto", f"{p}.text_scope",
                           "o documento extraído não tem relatório, voto ou decisão: é só ementa ou parte do acórdão, não inteiro teor")
            pin = s.get("pinpoint")
            if not isinstance(pin, dict):
                r.erro("campo_obrigatorio", f"{p}.pinpoint", "fonte lida exige 'pinpoint' (locator e excerpt)")
            else:
                _texto(r, pin, "locator", f"{p}.pinpoint")
                if _texto(r, pin, "excerpt", f"{p}.pinpoint"):
                    _conferir_trecho(r, f"{p}.pinpoint", s, pin.get("locator"), pin["excerpt"], idx, "claim")
                    _avaliar_trecho(r, f"{p}.pinpoint", pin["excerpt"])
                    _conferir_hash(r, p, s, idx)
        elif acesso is not None and s.get("pinpoint") is not None:
            r.erro("pinpoint_sem_leitura", f"{p}.pinpoint", "fonte não lida não pode trazer pinpoint")
        if (lt := s.get("legal_time")) is not None:
            if not isinstance(lt, dict) or not _data_valida(lt.get("as_of")):
                r.erro("data_invalida", f"{p}.legal_time.as_of", "legal_time exige 'as_of' em ISO 8601")
            else:
                _enum(r, lt, "vigencia", f"{p}.legal_time", VIGENCIA)
        validas.append(s)
    return validas


def _conferir_hash(r, p, s, idx):
    if idx is None or not isinstance(s.get("document_id"), str) or s["document_id"] not in idx:
        return
    d = idx[s["document_id"]]
    aceitos = {h for h in (d.get("sha256"), d.get("text_sha256")) if h}
    if aceitos and s.get("content_hash") not in aceitos:
        r.erro("hash_diverge", f"{p}.content_hash",
               "o hash informado não é o do arquivo (sha256) nem o do texto extraído (text_sha256): a fonte lida não é a registrada")


# --------------------------------------------------------------------------- matter.json
RAMOS = ("civel", "consumidor", "empresarial", "administrativo", "familia", "outro", "nao_informado")
PAPEIS = ("autor", "reu", "recorrente", "recorrido", "terceiro", "interessado", "contratante", "contratada", "divulgadora",
          "receptora", "nao_aplicavel", "nao_informado")
NIVEIS = ("publico", "restrito", "sigiloso")
CONSULTAS = ("permitidas", "somente_termos_genericos", "proibidas")


def _validar_conflitos(r, cf, c):
    """Registro do resultado da checagem de conflito de interesses. O pacote registra; não executa a checagem."""
    if cf is None:
        r.aviso("conflitos_nao_registrados", c, "registre o resultado da checagem de conflito de interesses")
        return
    if not isinstance(cf, dict):
        r.erro("tipo_invalido", c, "'conflicts' deve ser objeto")
        return
    st = _enum(r, cf, "status", c, CONFLITOS)
    if st == "cleared":
        for k in ("method", "cleared_by"):
            _texto(r, cf, k, c)
        if not _data_valida(cf.get("cleared_date")):
            r.erro("data_invalida", f"{c}.cleared_date", "'cleared_date' é obrigatório (AAAA-MM-DD)")
        ca = cf.get("checked_against")
        if not (isinstance(ca, list) and ca and all(isinstance(x, str) and x.strip() for x in ca)):
            r.erro("campo_obrigatorio", f"{c}.checked_against", "liste contra quem a checagem foi feita (partes, afiliadas, advogados)")
    elif st == "waived":
        _texto(r, cf, "waiver_rationale", c)
    elif st == "nao_aplicavel":
        _texto(r, cf, "motivo", c)
    elif st == "pending":
        _texto(r, cf, "owner", c)
        r.aviso("conflitos_pendentes", c, "checagem de conflito pendente: resolva antes de entregar o trabalho ao cliente")
    elif st == "not-run":
        ov = cf.get("override")
        if ov is None:
            r.aviso("conflitos_nao_verificados", c, "a checagem de conflito não foi feita: faça, marque como pendente com responsável ou registre o bypass")
        elif not isinstance(ov, dict) or not all(isinstance(ov.get(k), str) and ov[k].strip() for k in ("by", "date", "rationale")):
            r.erro("campo_obrigatorio", f"{c}.override", "o bypass exige 'by', 'date' e 'rationale'")
        else:
            r.aviso("conflitos_com_bypass_registrado", c, "checagem de conflito dispensada por bypass registrado: visível em toda auditoria")


def _validar_partes(r, partes, c, idx):
    if partes is None:
        return
    if not isinstance(partes, list):
        r.erro("tipo_invalido", c, "'partes' deve ser lista")
        return
    for i, p in enumerate(partes):
        cp = f"{c}[{i}]"
        if not isinstance(p, dict):
            r.erro("tipo_invalido", cp, "cada parte deve ser objeto")
            continue
        _texto(r, p, "nome", cp)
        _enum(r, p, "papel", cp, PAPEIS_PARTE)
        _texto(r, p, "representada_por", cp, obrigatorio=False)
        s = p.get("source")
        if s is None:
            r.aviso("parte_sem_fonte", cp, "parte sem fonte: aponte documento, localizador e trecho onde ela aparece")
        elif not isinstance(s, dict):
            r.erro("tipo_invalido", f"{cp}.source", "'source' deve ser objeto")
        else:
            for k in ("document_id", "locator", "excerpt"):
                _texto(r, s, k, f"{cp}.source")
            if isinstance(s.get("excerpt"), str):
                _conferir_trecho(r, f"{cp}.source", s, s.get("locator"), s["excerpt"], idx)
                _avaliar_trecho(r, f"{cp}.source", s["excerpt"])


def validar_matter(obj, idx=None) -> Resultado:
    r = Resultado()
    m = obj.get("matter") if isinstance(obj, dict) else None
    if not isinstance(m, dict):
        r.erro("estrutura", "$", "esperado objeto com 'matter'")
        return r
    if obj.get("schema_version") != SCHEMA_VERSION:
        r.erro("schema_version", "$.schema_version", f"esperado '{SCHEMA_VERSION}'")
    c = "$.matter"
    mid = _texto(r, m, "matter_id", c)
    if mid and not _ID.match(mid):
        r.erro("id_invalido", f"{c}.matter_id", "use apenas letras, números, '_' e '-'")
    _texto(r, m, "objective", c)
    papel = _enum(r, m, "client_role", c, PAPEIS)
    if papel == "nao_informado":
        r.aviso("papel_nao_informado", f"{c}.client_role", "sem o papel do cliente a análise não tem posição a defender")
    j = m.get("jurisdiction")
    if not isinstance(j, dict):
        r.erro("campo_obrigatorio", f"{c}.jurisdiction", "'jurisdiction' é obrigatório (objeto com 'ramo')")
    else:
        ramo = _enum(r, j, "ramo", f"{c}.jurisdiction", RAMOS)
        if ramo == "nao_informado":
            r.aviso("jurisdicao_nao_informada", f"{c}.jurisdiction.ramo",
                    "sem jurisdição não há conclusão localizada; o inventário documental pode seguir")
        uf = j.get("uf")
        if uf is not None and not (isinstance(uf, str) and re.fullmatch(r"[A-Z]{2}", uf)):
            r.erro("valor_invalido", f"{c}.jurisdiction.uf", "use a sigla com duas letras maiúsculas (ex.: AL)")
        _texto(r, j, "tribunal", f"{c}.jurisdiction", obrigatorio=False)
    as_of = m.get("as_of")
    hoje = datetime.now().date().isoformat()
    if not _data_valida(as_of) or not isinstance(as_of, str) or len(as_of) < 10:
        r.erro("data_invalida", f"{c}.as_of", "'as_of' (data de referência) é obrigatório, em AAAA-MM-DD")
    elif as_of[:10] > hoje:
        r.erro("data_futura", f"{c}.as_of", "a data de referência não pode estar no futuro")
    fd = m.get("facts_date")
    if fd is not None:
        if not isinstance(fd, str) or not _ISO_PARCIAL.match(fd) or (len(fd) == 7 and not 1 <= int(fd[5:]) <= 12) \
                or (len(fd) == 10 and not _data_valida(fd)):
            r.erro("data_invalida", f"{c}.facts_date", "use AAAA, AAAA-MM ou AAAA-MM-DD válidos; omita se for desconhecida")
        elif isinstance(as_of, str) and fd > as_of[: len(fd)]:
            r.erro("data_incoerente", f"{c}.facts_date", "a data dos fatos não pode ser posterior à data de referência")
    conf = m.get("confidentiality")
    if not isinstance(conf, dict):
        r.erro("campo_obrigatorio", f"{c}.confidentiality", "'confidentiality' é obrigatório (ao menos nivel; consultas_externas é opcional e o padrão é 'permitidas')")
    else:
        nivel = _enum(r, conf, "nivel", f"{c}.confidentiality", NIVEIS)
        # a política é escolha do usuário no próprio ambiente: sem ela, vale 'permitidas'
        consultas = _enum(r, conf, "consultas_externas", f"{c}.confidentiality", CONSULTAS, obrigatorio=False) or "permitidas"
        if nivel in ("restrito", "sigiloso"):
            if not (isinstance(conf.get("politica_modelo"), str) and conf["politica_modelo"].strip()):
                r.aviso("politica_modelo_nao_registrada", f"{c}.confidentiality.politica_modelo",
                        "nível restrito ou sigiloso sem registro do que pode ir ao modelo: opcional, mas ajuda quem revisar depois")
            if consultas == "permitidas" and conf.get("consultas_externas") is not None:
                r.aviso("sigilo_com_consultas_externas", f"{c}.confidentiality.consultas_externas",
                        f"nível '{nivel}' com consultas externas permitidas: termos do caso podem sair da máquina")
        priv = _enum(r, conf, "privilegio", f"{c}.confidentiality", PRIVILEGIO, obrigatorio=False)
        if priv is None and nivel in ("restrito", "sigiloso"):
            r.aviso("privilegio_nao_registrado", f"{c}.confidentiality.privilegio",
                    "registre se as fontes passaram por triagem de sigilo profissional (triado, misto, nao_triado)")
        if priv == "nao_triado":
            r.aviso("fontes_sem_triagem_de_sigilo", f"{c}.confidentiality.privilegio",
                    "as fontes não foram triadas quanto a sigilo: triar antes de extrair para relatórios que circulem")
        sj = conf.get("segredo_de_justica")
        if sj is not None and not isinstance(sj, bool):
            r.erro("tipo_invalido", f"{c}.confidentiality.segredo_de_justica", "use verdadeiro ou falso (CPC, art. 189)")
        elif sj is True and consultas == "permitidas":
            r.aviso("segredo_com_consultas_externas", f"{c}.confidentiality.segredo_de_justica",
                    "processo em segredo de justiça com consultas externas permitidas: restrinja a termos genéricos")
    _texto(r, m, "fato_chave", c, obrigatorio=False)
    _validar_conflitos(r, m.get("conflicts"), f"{c}.conflicts")
    _validar_partes(r, m.get("partes"), f"{c}.partes", idx)
    caps = m.get("capabilities")
    if caps is not None:
        if not isinstance(caps, dict) or not all(isinstance(v, bool) for v in caps.values()):
            r.erro("tipo_invalido", f"{c}.capabilities", "'capabilities' deve ser objeto de valores verdadeiro/falso")
    procs = m.get("processos")
    if procs is not None:
        if not isinstance(procs, list):
            r.erro("tipo_invalido", f"{c}.processos", "'processos' deve ser lista")
        else:
            import cnj

            for i, p in enumerate(procs):
                num = p.get("numero") if isinstance(p, dict) else p
                ok, motivo = cnj.validar(num) if isinstance(num, str) else (False, "número ausente")
                if not ok:
                    r.erro("cnj_invalido", f"{c}.processos[{i}]", f"número '{num}' recusado: {motivo}")
    for chave in ("documentos", "lacunas_iniciais"):
        v = m.get(chave)
        if v is not None and not (isinstance(v, list) and all(isinstance(x, (str, dict)) and x for x in v)):
            r.erro("tipo_invalido", f"{c}.{chave}", f"'{chave}' deve ser lista de textos ou objetos não vazios")
    return r


# --------------------------------------------------------------------------- orquestração
def validar(obj, idx=None) -> tuple[str, Resultado]:
    chaves = [k for k in ("facts", "claims", "matter") if isinstance(obj, dict) and k in obj]
    if len(chaves) > 1:
        r = Resultado()
        r.erro("estrutura", "$", f"o arquivo traz {' e '.join(repr(k) for k in chaves)}; use um arquivo para cada formato")
        return "indefinido", r
    if chaves == ["facts"]:
        return "facts", validar_facts(obj, idx)
    if chaves == ["claims"]:
        return "claims", validar_claims(obj, idx)
    if chaves == ["matter"]:
        return "matter", validar_matter(obj, idx)
    r = Resultado()
    r.erro("estrutura", "$", "não encontrei 'facts', 'claims' nem 'matter' no objeto raiz")
    return "indefinido", r


def resumo(tipo, obj, r) -> dict:
    if tipo == "facts":
        itens = [f for f in obj.get("facts", []) if isinstance(f, dict)]
        return {"total": len(itens), **{k: sum(1 for f in itens if f.get("kind") == k) for k in KIND_FATO}}
    if tipo == "claims":
        itens = [c for c in obj.get("claims", []) if isinstance(c, dict)]
        return {"total": len(itens), **{k: sum(1 for c in itens if c.get("status") == k) for k in ESTADOS},
                "centrais_pendentes": [c.get("id") for c in itens
                                       if c.get("central") is True and c.get("status") != "supported"],
                "contraditas": [c.get("id") for c in itens
                                if c.get("status") == "unsupported" and c.get("source_relation") == "contradiz"]}
    if tipo == "matter":
        m = obj.get("matter", {}) if isinstance(obj.get("matter"), dict) else {}
        return {"matter_id": m.get("matter_id"), "ramo": (m.get("jurisdiction") or {}).get("ramo"),
                "nivel": (m.get("confidentiality") or {}).get("nivel"), "processos": len(m.get("processos") or [])}
    return {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("arquivo")
    ap.add_argument("--extracoes", action="append", default=[], help="saída do extract.py (repetível)")
    ap.add_argument("--estrito", action="store_true", help="avisos também reprovam")
    a = ap.parse_args(argv)
    try:
        obj = json.loads(Path(a.arquivo).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        tipo, r, obj = "indefinido", Resultado(), {}
        r.erro("arquivo_ilegivel", "$", f"{type(e).__name__}: {e}")
    else:
        try:
            idx = carregar_extracoes(a.extracoes) if a.extracoes else None
        except (OSError, ValueError) as e:
            idx = None
            tipo, r = "indefinido", Resultado()
            r.erro("extracoes_ilegiveis", "--extracoes", f"{type(e).__name__}: {e}")
            obj = {}
        else:
            tipo, r = validar(obj, idx)
    valido = not r.erros and not (a.estrito and r.avisos)
    saida = {"arquivo": a.arquivo, "tipo": tipo, "valido": valido, "erros": r.erros, "avisos": r.avisos,
             "resumo": resumo(tipo, obj, r)}
    sys.stdout.buffer.write((json.dumps(saida, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return 0 if valido else 1


if __name__ == "__main__":
    sys.exit(main())
