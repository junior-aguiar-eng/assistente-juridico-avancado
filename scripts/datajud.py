"""Consulta de metadados de processo na API Pública do DataJud (CNJ).

  python scripts/datajud.py consultar NUMERO_CNJ

A chave é pública e fica publicada na wiki do CNJ (https://datajud-wiki.cnj.jus.br/api-publica/acesso); o CNJ pode trocá-la
a qualquer momento. Ordem: variável DATAJUD_API_KEY; senão, leitura da wiki no momento da consulta. A chave nunca é gravada.

O DataJud devolve **metadados** (classe, órgão, assuntos, movimentos). Não devolve inteiro teor nem prova que uma decisão
diz o que se alega: o resultado serve para confirmar que o processo existe e para dados de identificação, nunca como
fonte de tese. Dados pessoais de partes podem estar ausentes; o que vem é público, mas siga a política do caso.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cnj  # noqa: E402

WIKI = "https://datajud-wiki.cnj.jus.br/api-publica/acesso"
BASE = "https://api-publica.datajud.cnj.jus.br"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
_UF = "ac al ap am ba ce dft es go ma mt ms mg pa pb pr pe pi rj rn rs ro rr sc se sp to".split()
_UF_ALIAS = {"dft": "tjdft"}


def alias(num: "cnj.NumeroCNJ") -> str | None:
    """Índice da API pública para o número (justiça estadual, federal, do trabalho e STJ)."""
    j, tr = str(num.segmento), int(num.tribunal)
    if j == "8" and 1 <= tr <= 27:
        uf = _UF[tr - 1]
        return _UF_ALIAS.get(uf, f"tj{uf}")
    if j == "4" and 1 <= tr <= 6:
        return f"trf{tr}"
    if j == "5" and 1 <= tr <= 24:
        return f"trt{tr}"
    if j == "3" and tr == 0:
        return "stj"
    return None


def chave_publica() -> str:
    env = os.environ.get("DATAJUD_API_KEY")
    if env:
        return env.strip()
    script = Path(__file__).resolve().parent / "fetch_oficial.py"
    r = subprocess.run([sys.executable, str(script), WIKI], capture_output=True, timeout=120)
    m = re.search(r"APIKey\s+\*\*([A-Za-z0-9+/=_-]{20,})\*\*", r.stdout.decode("utf-8", "replace"))
    if not m:
        raise RuntimeError("não encontrei a chave pública na wiki do CNJ (a página mudou?); defina DATAJUD_API_KEY")
    return m.group(1)


def _post(url: str, chave: str, corpo: dict, timeout: int = 40):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), method="POST",
                                 headers={"Authorization": f"APIKey {chave}", "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def consultar(numero: str, chave: str | None = None) -> dict:
    n = cnj.parse(numero)
    if n is None:
        return {"status": "numero_invalido", "numero": numero}
    ok, motivo = cnj.validar(numero)
    if not ok:
        return {"status": "numero_invalido", "numero": n.formatado, "motivo": motivo}
    idx = alias(n)
    if idx is None:
        return {"status": "tribunal_nao_coberto", "numero": n.formatado,
                "motivo": "o segmento/tribunal deste número não tem índice mapeado neste script"}
    try:
        status, obj = _post(f"{BASE}/api_publica_{idx}/_search", chave or chave_publica(),
                            {"query": {"match": {"numeroProcesso": re.sub(r"\D", "", n.formatado)}}, "size": 5})
    except urllib.error.HTTPError as e:
        return {"status": "erro_http", "numero": n.formatado, "http": e.code,
                "motivo": "401 costuma indicar chave trocada pelo CNJ: confira a wiki" if e.code == 401 else str(e)}
    except Exception as e:  # noqa: BLE001 - relato exato da falha
        return {"status": "erro_de_acesso", "numero": n.formatado, "motivo": f"{type(e).__name__}: {e}"}
    hits = obj.get("hits", {}).get("hits", [])
    if not hits:
        return {"status": "nao_encontrado", "numero": n.formatado, "indice": idx,
                "aviso": "ausência no DataJud não prova que o processo não existe (sigilo, atraso de envio, outro tribunal)"}
    saida = []
    for h in hits:
        s = h.get("_source", {})
        saida.append({"numeroProcesso": s.get("numeroProcesso"), "classe": (s.get("classe") or {}).get("nome"),
                      "tribunal": s.get("tribunal"), "grau": s.get("grau"), "orgaoJulgador": (s.get("orgaoJulgador") or {}).get("nome"),
                      "dataAjuizamento": s.get("dataAjuizamento"), "assuntos": [a.get("nome") for a in s.get("assuntos", []) if isinstance(a, dict)],
                      "nivelSigilo": s.get("nivelSigilo"), "movimentos": len(s.get("movimentos", [])),
                      "dataHoraUltimaAtualizacao": s.get("dataHoraUltimaAtualizacao")})
    return {"status": "encontrado", "numero": n.formatado, "indice": idx, "resultados": saida,
            "aviso": "metadados do DataJud: não é inteiro teor nem fonte de tese"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("consultar")
    c.add_argument("numero")
    n = ap.parse_args(argv)
    try:
        res = consultar(n.numero)
    except (RuntimeError, OSError) as e:
        res = {"status": "erro", "motivo": f"{type(e).__name__}: {e}"}
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return 0 if res.get("status") in ("encontrado", "nao_encontrado") else 1


if __name__ == "__main__":
    sys.exit(main())
