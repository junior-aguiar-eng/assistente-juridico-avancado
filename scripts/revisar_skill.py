"""Revisão mecânica de SKILL.md contra governance/skill-review-checklist.md.

  python scripts/revisar_skill.py skills/*/SKILL.md [--hoje AAAA-MM-DD]

Confere estrutura, atualidade do conteúdo de regra em references/, sobreposição de gatilhos e a
superfície de confiança (hooks, ferramentas, URLs, texto oculto, frases de injeção, execução de código,
pedido de credenciais, autoridade jurídica afirmada). É uma varredura heurística, não uma auditoria
de segurança: leia o SKILL.md você mesmo. Código de saída 1 se alguma skill tiver PREOCUPACAO_MATERIAL.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

RECOMENDADOS = ("version", "last_reviewed", "owner")
CHAVES_DE_SUPERFICIE = ("hooks", "allowed-tools", "tools", "mcp", "mcpServers")
OCULTOS = re.compile("[​-‏⁠﻿‪-‮⁦-⁩]")
FRASES_DE_INJECAO = re.compile(
    r"(?i)ignore (all )?(the )?(previous|above|prior) instructions|disregard (the )?(above|previous)|"
    r"ignore (as )?instru[cç][oõ]es (anteriores|acima)|desconsidere (as )?instru[cç][oõ]es|esque[cç]a (o que|as instru)|"
    r"as the administrator|como administrador do sistema|this is a system (prompt|message)|esta [ée] uma mensagem do sistema|"
    r"voc[eê] agora [ée]|you are now|your new role|seu novo papel|developer mode|modo desenvolvedor|priority override")
EXECUCAO = re.compile(r"(?i)\b(curl|wget)\s+\S|\beval\s*\(|\|\s*(ba)?sh\b|Invoke-Expression|\bsudo\b|rm\s+-rf|chmod\s+\+x")
CREDENCIAL = re.compile(r"(?i)(cole|informe|envie|forne[cç]a|digite|passe)\b.{0,40}(senha|chave de api|api key|token de acesso|segredo)")
AUTORIDADE = re.compile(r"(?i)sou (seu )?advogad|atuo como advogad|dispensa a revis[aã]o|n[aã]o precisa de revis[aã]o|"
                        r"cria (o )?privil[eé]gio|garante a corre[cç][aã]o jur[ií]dica")
URL = re.compile(r"https?://[^\s)>\]\"']+")
URL_COM_DADOS = re.compile(r"(?i)[?&](data|token|payload|key|secret|senha)=")
BASE64 = re.compile(r"[A-Za-z0-9+/]{120,}={0,2}")


def _negado(linha: str, m) -> bool:
    """A frase de autoridade vem negada ('não cria privilégio', 'nunca dispensa a revisão')."""
    return bool(re.search(r"(?i)\b(n[aã]o|nunca|jamais)\s+(\w+\s+){0,2}$", linha[: m.start()]))


def _frontmatter(texto: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texto, re.S)
    if not m:
        return None, texto
    fm = {}
    for linha in m.group(1).splitlines():
        if ":" in linha and not linha.startswith((" ", "\t", "-")):
            k, _, v = linha.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, texto[m.end():]


def _achado(lista, parametro, gravidade, mensagem, linha=None):
    lista.append({"parametro": parametro, "gravidade": gravidade, "mensagem": mensagem, "linha": linha})


def _tem_secao(corpo: str, *palavras) -> bool:
    return any(re.search(rf"(?im)^#{{2,3}}\s+.*{p}", corpo) for p in palavras)


def revisar(caminho: Path, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    achados: list[dict] = []
    texto = Path(caminho).read_text(encoding="utf-8")
    fm, corpo = _frontmatter(texto)
    pasta = Path(caminho).parent
    nome = None
    # 12 Estrutura
    if fm is None:
        _achado(achados, "12_estrutura", "material", "sem frontmatter (name e description)")
        fm = {}
    for k in ("name", "description"):
        if not fm.get(k):
            _achado(achados, "12_estrutura", "material", f"frontmatter sem '{k}'")
    nome = fm.get("name")
    if nome and nome != pasta.name:
        _achado(achados, "12_estrutura", "atencao", f"name '{nome}' difere da pasta '{pasta.name}'")
    for rotulo, palavras, gravidade in (("entrada e saída", ("entrada",), "material"), ("roteiro", ("roteiro",), "material")):
        if not _tem_secao(corpo, *palavras):
            _achado(achados, "12_estrutura", gravidade, f"falta a seção de {rotulo}")
    if not re.search(r"(?i)casos? de refer[eê]ncia|exemplo", corpo):
        _achado(achados, "12_estrutura", "atencao", "sem exemplo ou caso de referência")
    if "garantias.md" not in corpo:
        _achado(achados, "12_estrutura", "atencao", "sem remissão às garantias comuns (shared/garantias.md)")
    # 1 Público, 8 Escopo, 9 Escalação, 7 Falhas jurídicas
    if not _tem_secao(corpo, "p[uú]blico"):
        _achado(achados, "1_publico", "atencao", "sem seção sobre público e natureza do trabalho")
    if not _tem_secao(corpo, "limites", "n[aã]o fazer"):
        _achado(achados, "8_escopo", "material", "sem seção de limites (o que a skill não faz)")
    if not (_tem_secao(corpo, "escalar", "escala[cç][aã]o") or "escalacao.md" in corpo):
        _achado(achados, "9_escalacao", "material", "sem gatilhos de escalação (nem remissão a shared/escalacao.md)")
    if not (_tem_secao(corpo, "falhas") or "falhas-juridicas.md" in corpo):
        _achado(achados, "7_falhas_juridicas", "material", "as três falhas jurídicas não estão tratadas (apoio, sigilo, responsabilidade)")
    # 5 Versão e responsável
    for k in RECOMENDADOS:
        if not fm.get(k):
            _achado(achados, "5_versao_responsavel", "atencao", f"frontmatter sem '{k}'")
    # 11 Atualidade
    refs = list((pasta / "references").glob("*.md")) if (pasta / "references").is_dir() else []
    if refs:
        faltam = [k for k in ("last_verified", "freshness_window_days", "freshness_category", "verified_against") if not fm.get(k)]
        if faltam:
            _achado(achados, "11_atualidade", "atencao", f"traz references/ com texto de regra, mas falta no frontmatter: {', '.join(faltam)}")
        else:
            try:
                limite = date.fromisoformat(fm["last_verified"]).toordinal() + int(fm["freshness_window_days"])
                if hoje.toordinal() > limite:
                    _achado(achados, "11_atualidade", "material", "a janela de atualidade declarada pelo autor venceu: reverificar o texto de regra")
            except ValueError:
                _achado(achados, "11_atualidade", "atencao", "last_verified ou freshness_window_days em formato inválido")
            if fm.get("freshness_category", "").lower() == "stable":
                _achado(achados, "11_atualidade", "atencao", "'stable' em texto de regra: use 'rule_text'")
    # 10 Superfície de confiança
    for k in CHAVES_DE_SUPERFICIE:
        if k in fm:
            _achado(achados, "10_superficie", "material", f"frontmatter declara '{k}': execução ou ferramentas fora do escopo da skill")
    if (pasta / "hooks").exists() or (pasta / ".mcp.json").exists():
        _achado(achados, "10_superficie", "material", "a pasta da skill traz hooks ou .mcp.json")
    linhas = texto.splitlines()
    fim_fm = next((i for i, l in enumerate(linhas[1:], 1) if l.strip() == "---"), 0) if fm else 0
    for i, linha in enumerate(linhas, 1):
        if len(linha) > (900 if i <= fim_fm else 800):
            _achado(achados, "10_superficie", "atencao", f"linha com {len(linha)} caracteres (conteúdo possivelmente codificado)", i)
        if OCULTOS.search(linha):
            _achado(achados, "10_superficie", "material", "caractere invisível ou de inversão de texto", i)
        if "<!--" in linha:
            _achado(achados, "10_superficie", "material", "comentário HTML (pode esconder instrução)", i)
        if BASE64.search(linha):
            _achado(achados, "10_superficie", "material", "bloco longo que parece base64", i)
        for padrao, msg in ((FRASES_DE_INJECAO, "frase de injeção de prompt"), (EXECUCAO, "execução de código ou download de script"),
                            (CREDENCIAL, "pede senha, chave ou token"), (AUTORIDADE, "afirma autoridade jurídica ou dispensa revisão")):
            m = padrao.search(linha)
            if m and not (padrao is AUTORIDADE and _negado(linha, m)):
                _achado(achados, "10_superficie", "material", f"{msg}: '{m.group(0)[:60]}'", i)
        for u in URL.findall(linha):
            if URL_COM_DADOS.search(u):
                _achado(achados, "10_superficie", "material", f"URL com parâmetro que pode carregar dados: {u}", i)
    urls = sorted(set(URL.findall(texto)))
    if urls:
        _achado(achados, "10_superficie", "info", f"{len(urls)} URL(s) citadas (confira o propósito de cada uma): " + ", ".join(urls[:6]))
    if re.search(r"python (-P )?scripts/", texto):
        _achado(achados, "10_superficie", "info", "manda rodar scripts do próprio repositório (propósito claro e limitado)")
    gravidades = {a["gravidade"] for a in achados}
    veredito = "PREOCUPACAO_MATERIAL" if "material" in gravidades else ("ATENCAO" if "atencao" in gravidades else "PRONTA")
    return {"caminho": str(caminho), "nome": nome, "veredito": veredito, "achados": achados,
            "gatilhos": sorted(set(re.findall(r"[\"“]([^\"”]{4,60})[\"”]", fm.get("description", ""))))}


def revisar_todas(caminhos, hoje=None) -> dict:
    res = [revisar(Path(c), hoje) for c in caminhos]
    donos: dict[str, list[str]] = {}
    for r in res:
        for g in r["gatilhos"]:
            donos.setdefault(g.lower(), []).append(r["nome"] or r["caminho"])
    for g, quem in donos.items():
        if len(quem) > 1:
            for r in res:
                if (r["nome"] or r["caminho"]) in quem:
                    _achado(r["achados"], "13_conflitos", "atencao", f"o gatilho '{g}' também aparece em: {', '.join(q for q in quem if q != (r['nome'] or r['caminho']))}")
                    if r["veredito"] == "PRONTA":
                        r["veredito"] = "ATENCAO"
    resumo = {v: sum(1 for r in res if r["veredito"] == v) for v in ("PRONTA", "ATENCAO", "PREOCUPACAO_MATERIAL")}
    return {"skills": res, "resumo": resumo,
            "aviso": "varredura heurística: não é auditoria de segurança; leia os SKILL.md"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("skills", nargs="+")
    ap.add_argument("--hoje")
    a = ap.parse_args(argv)
    r = revisar_todas(a.skills, date.fromisoformat(a.hoje) if a.hoje else None)
    sys.stdout.buffer.write((json.dumps(r, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return 1 if r["resumo"]["PREOCUPACAO_MATERIAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
