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

SCHEMA_VERSION = "1"
ESTADOS = ("unverified", "partial", "supported", "unsupported")
KIND_FATO = ("documentado", "alegacao", "inferencia", "lacuna")
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
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", s)).casefold()


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
    marcadores = re.findall(r"\b(?:par\.\d+|tab\.\d+\.lin\.\d+|nota(?:fim)?\.[\w-]+)", locator or "")
    if marcadores and not any(b.get("locator") in marcadores for b in ach):
        achado = ", ".join(sorted({str(b.get("locator")) for b in ach}))
        return f"o localizador informa '{locator}', mas o trecho está em {achado}"
    return None


def _conferir_trecho(r, caminho, ref, locator, excerpt, idx, kind=None):
    """Confere document_id/block_id/excerpt contra a extração. ref é o dict com os campos."""
    did = ref.get("document_id")
    if idx is None or not did:
        return
    doc = idx.get(did)
    if doc is None:
        r.erro("documento_nao_extraido", f"{caminho}.document_id", f"'{did}' não consta nas extrações fornecidas")
        return
    blocos = doc["blocks"]
    bid = ref.get("block_id")
    if bid:
        bloco = next((b for b in blocos if b["id"] == bid), None)
        if bloco is None:
            r.erro("bloco_inexistente", f"{caminho}.block_id", f"bloco '{bid}' não existe em {did}")
            return
        candidatos = [bloco]
    else:
        candidatos = blocos
    ach = [b for b in candidatos if excerpt and _contem(b["text"], excerpt)]
    if not ach:
        r.erro("trecho_nao_encontrado", f"{caminho}.excerpt",
               f"o trecho não está no texto extraído de {did}" + (f" (bloco {bid})" if bid else ""))
    elif (msg := _localizador_incoerente(locator, ach)):
        r.erro("localizador_incoerente", f"{caminho}.locator", msg)
    elif all(b.get("is_quote") for b in ach):
        if kind == "documentado":
            r.aviso("documentado_em_citacao", f"{caminho}.excerpt",
                    "fato 'documentado' apoiado só em trecho transcrito: quem narra é outro texto; considere 'alegacao'")
        else:
            r.aviso("trecho_em_citacao", f"{caminho}.excerpt",
                    "o trecho está em passagem marcada como citação: confirme quem fala (o órgão julgador ou o texto transcrito)")


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
    return r


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
    if not isinstance(iso, str) or not _ISO_PARCIAL.match(iso) or len(iso) != PRECISOES[prec]:
        r.erro("data_incoerente", f"{c}.iso", f"precisão '{prec}' exige formato com {PRECISOES[prec]} caracteres (AAAA[-MM[-DD]])")
    elif len(iso) == 10 and not _data_valida(iso):
        r.erro("data_invalida", f"{c}.iso", f"'{iso}' não é data de calendário válida")
    elif len(iso) == 7 and not 1 <= int(iso[5:]) <= 12:
        r.erro("data_invalida", f"{c}.iso", f"mês inválido em '{iso}'")


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
        fontes = _validar_fontes(r, cl, c, idx)
        if status is None:
            continue
        lidas = [s for s in fontes if s.get("access") == "lida"]
        oficiais = [s for s in lidas if s.get("origin") == "oficial"]
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
        acesso = _enum(r, s, "access", p, ACESSOS)
        if acesso == "lida":
            if not (isinstance(s.get("url"), str) and s["url"].strip()) and not (
                    isinstance(s.get("local_file"), str) and s["local_file"].strip()):
                r.erro("campo_obrigatorio", f"{p}.url", "fonte lida exige 'url' ou 'local_file'")
            if not _data_valida(s.get("retrieved_at")):
                r.erro("data_invalida", f"{p}.retrieved_at", "fonte lida exige 'retrieved_at' em ISO 8601")
            if not isinstance(s.get("content_hash"), str) or not _HASH.match(s["content_hash"]):
                r.erro("hash_invalido", f"{p}.content_hash", "fonte lida exige sha256 em 64 caracteres hexadecimais minúsculos")
            _enum(r, s, "text_scope", p, ESCOPOS_TEXTO)
            pin = s.get("pinpoint")
            if not isinstance(pin, dict):
                r.erro("campo_obrigatorio", f"{p}.pinpoint", "fonte lida exige 'pinpoint' (locator e excerpt)")
            else:
                _texto(r, pin, "locator", f"{p}.pinpoint")
                if _texto(r, pin, "excerpt", f"{p}.pinpoint"):
                    _conferir_trecho(r, f"{p}.pinpoint", s, pin.get("locator"), pin["excerpt"], idx)
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
    if idx is None or not s.get("document_id") or s["document_id"] not in idx:
        return
    d = idx[s["document_id"]]
    aceitos = {h for h in (d.get("sha256"), d.get("text_sha256")) if h}
    if aceitos and s.get("content_hash") not in aceitos:
        r.erro("hash_diverge", f"{p}.content_hash",
               "o hash informado não é o do arquivo (sha256) nem o do texto extraído (text_sha256): a fonte lida não é a registrada")


# --------------------------------------------------------------------------- matter.json
RAMOS = ("civel", "consumidor", "empresarial", "administrativo", "familia", "outro", "nao_informado")
PAPEIS = ("autor", "reu", "terceiro", "interessado", "nao_aplicavel", "nao_informado")
NIVEIS = ("publico", "restrito", "sigiloso")
CONSULTAS = ("permitidas", "somente_termos_genericos", "proibidas")


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
        r.erro("campo_obrigatorio", f"{c}.confidentiality", "'confidentiality' é obrigatório (nivel e consultas_externas)")
    else:
        nivel = _enum(r, conf, "nivel", f"{c}.confidentiality", NIVEIS)
        consultas = _enum(r, conf, "consultas_externas", f"{c}.confidentiality", CONSULTAS)
        if nivel in ("restrito", "sigiloso"):
            _texto(r, conf, "politica_modelo", f"{c}.confidentiality")
            if consultas == "permitidas":
                r.aviso("sigilo_com_consultas_externas", f"{c}.confidentiality.consultas_externas",
                        f"nível '{nivel}' com consultas externas permitidas: termos do caso podem sair da máquina")
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
                                       if c.get("central") is True and c.get("status") != "supported"]}
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
