"""Sondagem das pontes HTTP de fontes oficiais.

Para cada alvo: tentativa com User-Agent de navegador (2 vezes, timeout 25 s);
se falhar, uma tentativa sem o cabeçalho. Registra status, tamanho, tempo e se o
conteúdo esperado apareceu. Uso:  python scripts/sonda_pontes.py [saida.json]
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 25

ALVOS = [
    {"id": "planalto_cc", "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
     "esperado": "Art. 206", "charset": "windows-1252"},
    {"id": "planalto_cpc", "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm",
     "esperado": "Art. 85", "charset": "windows-1252"},
    {"id": "senado_lista", "accept": "application/json",
     "url": "https://legis.senado.leg.br/dadosabertos/legislacao/lista?tipo=LEI&numero=10406&ano=2002",
     "esperado": "10406"},
    {"id": "senado_apidocs", "accept": "application/json",
     "url": "https://legis.senado.leg.br/dadosabertos/v3/api-docs", "esperado": "openapi"},
    {"id": "stf_portal", "url": "https://portal.stf.jus.br/", "esperado": "Supremo"},
    {"id": "stf_jurisprudencia", "url": "https://jurisprudencia.stf.jus.br/pages/search", "esperado": None},
    {"id": "stj_dadosabertos", "url": "https://dadosabertos.web.stj.jus.br/", "esperado": "dados"},
    {"id": "stj_scon", "url": "https://scon.stj.jus.br/SCON/", "esperado": "SCON"},
    {"id": "lexml_sru", "accept": "application/xml",
     "url": "https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&version=1.1&maximumRecords=1"
            "&query=urn%20any%20%22urn%3Alex%3Abr%3Afederal%3Alei%3A2002-01-10%3B10406%22",
     "esperado": "searchRetrieveResponse"},
    {"id": "datajud_tjsp", "accept": "application/json",
     "url": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search", "esperado": None,
     "obs": "sem credencial; só mede alcance (401/403 = host alcançável)"},
    {"id": "camara_api", "accept": "application/json",
     "url": "https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&ano=2020&itens=1",
     "esperado": "dados"},
]


def _get(url, accept, usar_ua):
    h = {"Accept": accept or "*/*"}
    if usar_ua:
        h["User-Agent"] = UA
    req = urllib.request.Request(url, headers=h)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            corpo = r.read(2_000_000)
            return {"http": r.status, "bytes": len(corpo), "seg": round(time.time() - t0, 2),
                    "ctype": r.headers.get("Content-Type"), "corpo": corpo}
    except urllib.error.HTTPError as e:
        return {"http": e.code, "bytes": 0, "seg": round(time.time() - t0, 2), "erro": f"HTTP {e.code}"}
    except Exception as e:  # noqa: BLE001 - registrar a exceção exata
        return {"http": None, "bytes": 0, "seg": round(time.time() - t0, 2),
                "erro": f"{type(e).__name__}: {e}"}


def sondar(alvo):
    tentativas = []
    for usar_ua, n in ((True, 1), (True, 2), (False, 1)):
        r = _get(alvo["url"], alvo.get("accept"), usar_ua)
        corpo = r.pop("corpo", b"")
        r["user_agent_navegador"] = usar_ua
        r["tentativa"] = n
        if corpo and alvo.get("esperado"):
            texto = corpo.decode(alvo.get("charset", "utf-8"), errors="replace")
            r["esperado_encontrado"] = alvo["esperado"].lower() in texto.lower()
        if corpo:
            r["sha256"] = hashlib.sha256(corpo).hexdigest()[:16]
        tentativas.append(r)
        if r.get("http") == 200 or (r.get("http") in (401, 403) and alvo["id"].startswith("datajud")):
            break
    return {"id": alvo["id"], "url": alvo["url"], "obs": alvo.get("obs"), "tentativas": tentativas}


if __name__ == "__main__":
    saida = {"consultado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "resultados": [sondar(a) for a in ALVOS]}
    txt = json.dumps(saida, ensure_ascii=False, indent=2)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(txt)
    print(txt)
