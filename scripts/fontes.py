"""Pontes de fontes: plano de consulta, download registrado e anotações de alteração de dispositivos.

  plano     --tipo TIPO [--matter matter.json]       pontes na ordem de tentativa, filtradas pela política do caso
  baixar    URL --destino DIR [--registro R.json]    baixa a fonte, grava hash e registra; não contorna desafio anti-robô
  anotacoes FONTE.md --artigo N [--paragrafo P] [--inciso I] [--data-fatos AAAA[-MM[-DD]]]
                                                      anotações de alteração do dispositivo na versão compilada

Uma ponte secundária localiza; a confirmação vem da fonte oficial lida (ver shared/fontes-br.md).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REGISTRO_PONTES = RAIZ / "shared" / "fontes.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
SUFIXOS_OFICIAIS = ("planalto.gov.br", "senado.leg.br", "camara.leg.br", "cnj.jus.br", ".jus.br", ".gov.br")
_REPO_FETCH = Path(__file__).resolve().parent / "fetch_oficial.py"
_HOME_FETCH = Path.home() / ".claude" / "scripts" / "fetch_oficial.py"
FETCH_OFICIAL = _REPO_FETCH if _REPO_FETCH.is_file() else _HOME_FETCH  # a cópia do repositório vale primeiro


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- plano
def plano(tipo: str, matter: dict | None = None, registro_pontes: Path = REGISTRO_PONTES, hoje: date | None = None) -> dict:
    reg = json.loads(registro_pontes.read_text(encoding="utf-8"))
    if tipo not in reg["tipos"]:
        raise ValueError(f"tipo desconhecido '{tipo}'; use: {', '.join(reg['tipos'])}")
    m = (matter or {}).get("matter", matter or {}) if matter else {}
    caps = m.get("capabilities") or {}
    consultas = (m.get("confidentiality") or {}).get("consultas_externas")
    definida = consultas is not None
    consultas = consultas or "permitidas"  # padrão: o usuário decide no próprio ambiente; sem política, nada é barrado
    saida = []
    for p in sorted((p for p in reg["pontes"] if tipo in p["tipos"]), key=lambda p: p["ordem"]):
        faltam = [r for r in p["requer"] if matter and not caps.get(r)]
        estado, motivo = "disponivel", None
        if p["envia_termos_do_caso"] and consultas == "proibidas":
            estado, motivo = "excluida", "a política do caso proíbe consultas externas com termos do caso"
        elif faltam:
            estado, motivo = "indisponivel", f"capacidade não registrada no matter.json: {', '.join(faltam)}"
        elif p["envia_termos_do_caso"] and consultas == "somente_termos_genericos":
            estado, motivo = "restrita", "use só termos genéricos (sem nomes, números de processo ou fatos do caso)"
        saida.append({"id": p["id"], "ordem": p["ordem"], "origem": p["origem"], "estado": estado, "motivo": motivo,
                      "como": p["como"], "envia_termos_do_caso": p["envia_termos_do_caso"], "limites": p["limites"]})
    uteis = [s for s in saida if s["estado"] in ("disponivel", "restrita")]
    oficiais = [s for s in uteis if s["origem"] == "oficial" and s["id"] != "usuario_fornece"]
    idade = ((hoje or date.today()) - date.fromisoformat(reg["last_verified"])).days
    desatualizado = idade > int(reg["freshness_window_days"])
    avisos = []
    if matter is None:
        avisos.append("sem matter.json: nenhuma política de confidencialidade foi aplicada a este plano")
    elif not definida:
        avisos.append("consultas_externas não definida: tratada como 'permitidas' (o usuário decide no próprio ambiente; "
                      "para restringir, registre a política no matter.json)")
    elif consultas in ("proibidas", "somente_termos_genericos"):
        avisos.append(f"consultas externas '{consultas}' (escolha do usuário): vale também para busca aberta na web; "
                      "para mudar, o usuário edita o matter.json")
    if not oficiais:
        avisos.append("nenhuma ponte oficial utilizável: o teto é 'partial' até o usuário fornecer o documento oficial")
    if desatualizado:
        avisos.append(f"o registro de pontes foi verificado há {idade} dias (janela de {reg['freshness_window_days']}): "
                      "refaça a sondagem (scripts/sonda_pontes.py) antes de confiar na ordem e nos limites")
    return {"tipo": tipo, "descricao": reg["tipos"][tipo], "pontes": saida,
            "tem_ponte_oficial": bool(oficiais), "desatualizado": desatualizado, "verificado_em": reg["last_verified"],
            "portais_para_o_usuario": reg.get("portais_para_o_usuario", {}).get(tipo, []),
            "aviso": " | ".join(avisos) or None}


# --------------------------------------------------------------------------- baixar
def classificar_origem(url: str) -> str:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return "oficial" if any(host == s.lstrip(".") or host.endswith(s if s.startswith(".") else "." + s)
                            for s in SUFIXOS_OFICIAIS) else "secundaria"


def _baixar_bytes(url: str, usar_ua: bool = True, timeout: int = 30):
    h = {"Accept": "*/*"}
    if usar_ua:
        h["User-Agent"] = UA
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(80_000_000)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), (e.read(200_000) if hasattr(e, "read") else b"")


def detectar_desafio(status: int, headers: dict, corpo: bytes) -> str | None:
    h = {k.lower(): str(v) for k, v in headers.items()}
    if "cf-mitigated" in h or h.get("x-amzn-waf-action", "").lower() == "challenge":
        return "desafio anti-robô do servidor (Cloudflare ou AWS WAF)"
    cabeca = corpo[:6000].lower()
    if status == 202 and not corpo:
        return "resposta 202 vazia, típica de desafio anti-robô"
    if b"verifica" in cabeca and b"seguran" in cabeca and b"<html" in cabeca[:500] + b"<html":
        return "página de verificação de segurança"
    return None


def _extensao(content_type: str, corpo: bytes) -> str:
    ct = (content_type or "").lower()
    if "pdf" in ct or corpo[:5] == b"%PDF-":
        return ".pdf"
    if "json" in ct:
        return ".json"
    if "html" in ct:
        return ".html"
    return ".bin"


def _nome_arquivo(url: str, nome: str | None) -> str:
    if nome:
        limpo = re.sub(r"[^\w.\- ]", "_", nome).lstrip(". ")
        return limpo or "fonte"  # '..' ou '.' nunca viram nome de arquivo
    p = urllib.parse.urlparse(url)
    base = Path(p.path).name or p.hostname or "fonte"
    return re.sub(r"[^\w.\-]", "_", (base + ("_" + p.query if p.query else ""))[:80]).lstrip(".") or "fonte"


def _registrar(registro: Path | None, entrada: dict):
    if registro is None:
        return
    obj = json.loads(registro.read_text(encoding="utf-8")) if registro.is_file() else {"schema_version": "1", "fontes": []}
    obj["fontes"].append(entrada)
    registro.parent.mkdir(parents=True, exist_ok=True)
    registro.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def baixar(url: str, destino: Path, registro: Path | None = None, nome: str | None = None,
           fetch_oficial: Path | None = None, exigir: str | None = None) -> dict:
    """exigir='pdf': a resposta tem de ser PDF de verdade. Vale por padrão para URL de inteiro teor do STJ,
    que devolve uma página HTML genérica (200) quando não entrega o documento."""
    destino = Path(destino)
    if exigir is None and "getinteiroteor" in url.lower():
        exigir = "pdf"
    base = {"url": url, "origem": classificar_origem(url), "retrieved_at": _agora(), "avisos": []}

    def falha(motivo, **extra):
        e = {**base, "status": "source_missing", "motivo": motivo, "source_id": "falha-" + _sha_bytes(url.encode())[:10], **extra}
        _registrar(registro, e)
        return e

    def sucesso(**extra):
        e = {**base, "status": "lida", **extra}
        _registrar(registro, e)
        return e

    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if host.endswith("planalto.gov.br"):
        if "compilad" not in url.lower():
            base["avisos"].append("nao_compilada: use a versão compilada quando existir; trecho tachado (~~) nunca é fonte de regra")
        script = Path(fetch_oficial) if fetch_oficial else FETCH_OFICIAL
        if not script.is_file():
            return falha(f"fetch_oficial.py ausente em {script}: ele converte o Planalto (windows-1252) em Markdown")
        destino.mkdir(parents=True, exist_ok=True)
        alvo = destino / (_nome_arquivo(url, nome).rsplit(".", 1)[0] + ".md")
        try:
            r = subprocess.run([sys.executable, str(script), url, str(alvo)], capture_output=True, timeout=180)
        except subprocess.TimeoutExpired:
            return falha("fetch_oficial.py excedeu 180 s")
        if r.returncode != 0 or not alvo.is_file():
            return falha("fetch_oficial.py falhou: " + (r.stdout + r.stderr).decode("utf-8", "replace")[-200:].strip())
        dados = alvo.read_bytes()
        tachados = dados.count(b"~~") // 2
        if tachados:
            base["avisos"].append(f"{tachados} trecho(s) tachado(s) (~~): revogado ou substituído; não é fonte de regra")
        return sucesso(source_id="src-" + _sha_bytes(dados)[:12], local_file=str(alvo), bytes=len(dados),
                       sha256=_sha_bytes(dados), content_type="text/markdown", via="fetch_oficial.py")

    ultimo = None
    for usar_ua, n in ((True, 1), (True, 2), (False, 3)):
        try:
            status, headers, corpo = _baixar_bytes(url, usar_ua)
        except Exception as e:  # noqa: BLE001 - registrar a exceção exata
            ultimo = f"{type(e).__name__}: {e}"
            continue
        desafio = detectar_desafio(status, headers, corpo)
        if desafio:
            return falha(f"{desafio}: não contornado", http=status)
        if status == 200 and corpo:
            ext = _extensao(headers.get("Content-Type", ""), corpo)
            if exigir == "pdf" and corpo[:5] != b"%PDF-":
                return falha("conteudo_inesperado: era esperado um PDF e veio " + str(headers.get("Content-Type")) +
                             " (página genérica ou aviso do portal); o documento não foi obtido", http=status,
                             content_type=headers.get("Content-Type"), bytes=len(corpo))
            if ext == ".pdf" and corpo[:5] != b"%PDF-":
                base["avisos"].append("conteudo_inesperado: Content-Type diz PDF mas os bytes não começam com %PDF-")
            destino.mkdir(parents=True, exist_ok=True)
            alvo = destino / _nome_arquivo(url, nome)
            if alvo.suffix.lower() != ext:
                alvo = alvo.with_name(alvo.name + ext)
            sha = _sha_bytes(corpo)
            if alvo.exists() and _sha_bytes(alvo.read_bytes()) != sha:
                alvo = alvo.with_name(f"{alvo.stem}-{sha[:8]}{alvo.suffix}")
            alvo.write_bytes(corpo)
            return sucesso(source_id="src-" + sha[:12], local_file=str(alvo), bytes=len(corpo), sha256=sha,
                           http=status, content_type=headers.get("Content-Type"))
        ultimo = f"HTTP {status}"
        if status in (401, 403, 404, 410):
            break
    return falha(f"sem resposta utilizável após 3 tentativas ({ultimo})")


# --------------------------------------------------------------------------- anotações
_ROMANO = r"[IVXLC]+"
_RE_ROTULO = re.compile(r"^(?:(?P<art>Art\. \d+(?:-[A-Z])?)\b|§ (?P<par>\d+)|(?P<unico>Parágrafo único)|"
                        rf"(?P<inc>{_ROMANO}) -|(?P<ali>[a-z])\))", re.M)
_RE_ANOTACAO = re.compile(r"\[\((?P<texto>[^\]]*?)\)\]\((?P<url>[^)]*)\)")


def registrar(arquivo: Path, registro: Path, origem: str, url: str | None = None) -> dict:
    """Registra um arquivo que o usuário forneceu (hash, origem declarada). Não lê nem verifica o conteúdo."""
    arquivo = Path(arquivo)
    if origem not in ("oficial", "secundaria"):
        raise ValueError("origem deve ser 'oficial' ou 'secundaria'")
    if not arquivo.is_file():
        raise ValueError(f"arquivo inexistente: {arquivo}")
    dados = arquivo.read_bytes()
    sha = _sha_bytes(dados)
    e = {"url": url, "origem": origem, "retrieved_at": _agora(), "avisos": [], "status": "lida", "obtained_via": "user_supplied_source",
         "source_id": "src-" + sha[:12], "local_file": str(arquivo), "bytes": len(dados), "sha256": sha,
         "nota": "origem declarada pelo usuário; o conteúdo ainda não foi lido nem verificado (use extract.py e br-verificar-citacoes)"}
    _registrar(registro, e)
    return e


def _tipo_anotacao(t: str) -> str:
    t = t.lower()
    for chave, nome in (("revogad", "revogado"), ("redação", "redacao"), ("incluíd", "incluido"),
                        ("vide", "vide"), ("vigência", "vigencia")):
        if t.startswith(chave):
            return nome
    return "outro"


def _rotulo(path) -> str:
    art, par, inc, ali = path
    partes = [f"art. {art}"] if art else []
    if par:
        partes.append("parágrafo único" if par == "unico" else f"§ {par}º")
    if inc:
        partes.append(f"inciso {inc}")
    if ali:
        partes.append(f"alínea {ali}")
    return ", ".join(partes)


def anotacoes(fonte_md: Path, artigo: str, paragrafo: str | None = None, inciso: str | None = None,
              data_fatos: str | None = None) -> dict:
    texto = Path(fonte_md).read_text(encoding="utf-8")
    inicio = re.search(rf"^Art\. {re.escape(artigo)}\.?(?=\s)", texto, re.M)
    if not inicio:
        raise ValueError(f"artigo {artigo} não encontrado em {fonte_md}")
    prox = re.search(r"^Art\. \d", texto[inicio.end():], re.M)
    bloco = texto[inicio.start(): inicio.end() + prox.start()] if prox else texto[inicio.start():]
    rotulos, atual = [], [artigo, None, None, None]
    for m in _RE_ROTULO.finditer(bloco):
        if m.group("art"):
            atual = [artigo, None, None, None]
        elif m.group("par") or m.group("unico"):
            atual = [artigo, m.group("par") or "unico", None, None]
        elif m.group("inc"):
            atual = [artigo, atual[1], m.group("inc"), None]
        elif m.group("ali"):
            atual = [artigo, atual[1], atual[2], m.group("ali")]
        rotulos.append((m.start(), tuple(atual)))
    consulta = (artigo, paragrafo, inciso, None)
    achadas = []
    for a in _RE_ANOTACAO.finditer(bloco):
        dono = next((p for pos, p in reversed(rotulos) if pos < a.start()), (artigo, None, None, None))
        t = " ".join(a.group("texto").split())
        ano = re.findall(r"(?:de|em)\s+(\d{4})\b", t)
        q = dono
        prefixo = lambda x, y: all(xi is None or xi == yi for xi, yi in zip(x, y))  # noqa: E731
        if q == consulta:
            relacao = "no_dispositivo"
        elif prefixo(q, consulta) and q != consulta:
            relacao = "em_dispositivo_superior"
        elif prefixo(consulta, q):
            relacao = "em_subdispositivo"
        else:
            continue
        item = {"dispositivo": _rotulo(q), "tipo": _tipo_anotacao(t), "texto": t, "ano": int(ano[-1]) if ano else None,
                "lei_url": a.group("url"), "relacao": relacao}
        if data_fatos and item["ano"]:
            ano_fatos = int(data_fatos[:4])
            item["posterior_aos_fatos"] = item["ano"] > ano_fatos
            item["mesmo_ano_dos_fatos"] = item["ano"] == ano_fatos
        achadas.append(item)
    rot_consulta = _rotulo(consulta)
    existe = (paragrafo is None and inciso is None) or any(p[:3] == consulta[:3] for _, p in rotulos)
    posteriores = [x for x in achadas if x.get("posterior_aos_fatos") or x.get("mesmo_ano_dos_fatos")]
    sugestao = None
    if data_fatos:
        if posteriores:
            sugestao = {"vigencia": "nao_verificada",
                        "motivo": "há alteração posterior (ou do mesmo ano) à data dos fatos: o texto lido pode não ser o da época"}
        elif not achadas:
            sugestao = {"vigencia": "nao_verificada",
                        "motivo": "sem anotação de alteração no dispositivo; isso não prova a redação à época (o texto compilado não traz o histórico completo)"}
    return {"artigo": artigo, "dispositivo_consultado": rot_consulta, "dispositivo_localizado": existe,
            "anotacoes": achadas, "data_fatos": data_fatos, "legal_time_sugerido": sugestao,
            "aviso": "A versão compilada mostra o texto em vigor. Trecho revogado desaparece e redação anterior não aparece: "
                     "para fato antigo, confira a redação à época em fonte própria."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plano")
    p.add_argument("--tipo", required=True)
    p.add_argument("--matter")
    b = sub.add_parser("baixar")
    b.add_argument("url")
    b.add_argument("--destino", required=True)
    b.add_argument("--registro")
    b.add_argument("--nome")
    b.add_argument("--exigir", choices=["pdf"], help="recusa a resposta se não for desse tipo")
    r = sub.add_parser("registrar")
    r.add_argument("arquivo")
    r.add_argument("--registro", required=True)
    r.add_argument("--origem", required=True, choices=["oficial", "secundaria"])
    r.add_argument("--url")
    a = sub.add_parser("anotacoes")
    a.add_argument("fonte")
    a.add_argument("--artigo", required=True)
    a.add_argument("--paragrafo")
    a.add_argument("--inciso")
    a.add_argument("--data-fatos")
    n = ap.parse_args(argv)
    try:
        if n.cmd == "plano":
            matter = json.loads(Path(n.matter).read_text(encoding="utf-8")) if n.matter else None
            res, cod = plano(n.tipo, matter), 0
        elif n.cmd == "baixar":
            res = baixar(n.url, Path(n.destino), Path(n.registro) if n.registro else None, n.nome, exigir=n.exigir)
            cod = 0 if res["status"] == "lida" else 1
        elif n.cmd == "registrar":
            res, cod = registrar(Path(n.arquivo), Path(n.registro), n.origem, n.url), 0
        else:
            res, cod = anotacoes(Path(n.fonte), n.artigo, n.paragrafo, n.inciso, n.data_fatos), 0
    except (ValueError, OSError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
