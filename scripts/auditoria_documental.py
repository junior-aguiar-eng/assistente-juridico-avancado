"""Checagens documentais do auditor, reutilizando os validadores de contrato e minuta.

Não confere aparência, mérito jurídico ou identidade de revisor. Não modifica os
documentos: a regeneração da minuta ocorre somente em diretório temporário próprio.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

from docx.opc.exceptions import PackageNotFoundError
from lxml.etree import XMLSyntaxError

import contrato
import preencher

FALHAS_DOCUMENTO = (OSError, ValueError, TypeError, KeyError, AttributeError, BadZipFile,
                   PackageNotFoundError, XMLSyntaxError)


def _relatorio_redline(obj):
    """O produtor referencia issues por caminho; não contém outro conjunto."""
    return (not {'schema_version','posicao_da_parte'} & obj.keys()
            and all(isinstance(obj.get(k),str) and obj[k] for k in ('issues','original','saida','autor_das_alteracoes','aviso'))
            and all(isinstance(obj.get(k),str) and len(obj[k]) == 64
                    and all(c in '0123456789abcdef' for c in obj[k])
                    for k in ('issues_sha256','original_sha256','saida_sha256'))
            and all(type(obj.get(k)) is int and obj[k] >= 0 for k in ('aplicadas','recusadas'))
            and isinstance(obj.get('edicoes'),list))


def identificar(issues, campos, extras):
    """Um conjunto por tipo; artefato JSON reconhecido pelo conteúdo, não pelo nome."""
    candidatos = {"issues": set(), "campos": set()}
    for nome, caminho in (("issues", issues), ("campos", campos)):
        if caminho:
            candidatos[nome].add(Path(caminho).resolve())
    for caminho in extras:
        p = Path(caminho).resolve()
        if p.suffix.lower() != ".json":
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # artefato genérico não declara ser entrada de um validador
        if isinstance(obj, dict):
            for nome in candidatos:
                resultado_do_validador = (
                    nome == "issues" and isinstance(obj.get(nome), int)
                    and isinstance(obj.get("erros"), list) and isinstance(obj.get("avisos"), list)
                    and isinstance(obj.get("rascunho"), bool) and isinstance(obj.get("entregavel"), bool)
                    and "schema_version" not in obj and "posicao_da_parte" not in obj)
                resultado_do_redline = nome == 'issues' and _relatorio_redline(obj)
                if nome in obj and not resultado_do_validador and not resultado_do_redline:
                    candidatos[nome].add(p)
    for nome, paths in candidatos.items():
        if len(paths) > 1:
            raise ValueError(f"Mais de um conjunto de {nome}: audite cada conjunto separadamente")
    return tuple(next(iter(candidatos[n]), None) for n in ("issues", "campos"))


def _ler_lista(caminho, chave):
    obj = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get(chave), list):
        raise ValueError(f"esperado objeto com lista '{chave}'")
    if not all(isinstance(item, dict) for item in obj[chave]):
        raise ValueError(f"cada item de '{chave}' deve ser objeto")
    return obj


def _erro(exc):
    return {"codigo": "documento_invalido", "onde": "entrada", "mensagem": f"{type(exc).__name__}: {exc}"}


def conferir(g, reg, idx, tem_extracoes, issues=None, campos=None, modelo=None, minuta=None,
             regras_dir=None, pacote="servicos_saas,lgpd"):
    documentos = {}
    extracao = {"documents": list(idx.values())} if tem_extracoes else None

    def registrar(caminho, tipo):
        p = Path(caminho).resolve()
        if not p.is_file():
            raise ValueError(f"{tipo} ausente: {p}")
        reg(p, tipo)
        return p

    if issues:
        try:
            ip = registrar(issues, "issues")
            obj = _ler_lista(ip, "issues")
            regras = Path(regras_dir) if regras_dir else Path(__file__).resolve().parent.parent / "rules" / "br"
            for nome in [n.strip() for n in pacote.split(",") if n.strip()]:
                registrar(regras / f"{nome}.json", "regras")
            r = contrato.validar_issues(obj, extracao, regras, pacote)
        except FALHAS_DOCUMENTO as e:
            r = {"erros": [_erro(e)], "avisos": [], "entregavel": False}
        documentos["apontamentos"] = r
        for fid in r.get("avaliacao_juridica_pendente", []):
            g.pend("avaliacao_juridica", fid, "nao_avaliada: requer revisão jurídica, não significa risco baixo")
        for a in r["avisos"]:
            if a["codigo"] != "avaliacao_juridica_pendente":
                g.pend("apontamento", a["onde"], a["mensagem"])
        resultado = "reprovado" if r["erros"] else ("alerta" if r["avisos"] or not r["entregavel"] else "aprovado")
        g.add("G14_apontamentos_contratuais", "apontamentos conferidos pelo validador contratual", resultado,
              "; ".join(e["codigo"] for e in r["erros"]) or "validação mecânica; mérito e avaliação jurídica permanecem distintos")

    if campos or modelo or minuta:
        try:
            if not campos or not modelo or not minuta:
                raise ValueError("a conferência da minuta exige --campos, --modelo e --minuta juntos")
            cp = registrar(campos, "campos")
            mp = registrar(modelo, "modelo")
            saida = registrar(minuta, "minuta")
            if mp == saida:
                raise ValueError("modelo e minuta devem ser arquivos distintos")
            obj = _ler_lista(cp, "campos")
            r = preencher.lint(obj, mp, extracao)
            resumo = {"lint": r, "completo": False, "conteudo_confere": False,
                      "marcados_no_documento": {}, "inspecao_visual": "nao_realizada"}
            if not r["erros"]:
                with TemporaryDirectory(prefix="juris-auditoria-minuta-") as tmp:
                    esperado = Path(tmp) / "minuta.docx"
                    gerado = preencher.gerar(obj, mp, esperado, extracao)
                    if not gerado.get("gerado"):
                        raise ValueError("o preenchimento não gerou a minuta de referência")
                    with ZipFile(esperado) as ze, ZipFile(saida) as zs:
                        partes = set(ze.namelist())
                        igual = partes == set(zs.namelist()) and all(ze.read(n) == zs.read(n) for n in partes)
                resumo.update({k: gerado[k] for k in ("completo", "marcados_no_documento", "escalar")})
                resumo["conteudo_confere"] = igual
                if not igual:
                    r["erros"].append({"codigo": "minuta_diverge", "onde": "minuta", "mensagem": "partes do DOCX diferem da geração com este modelo e estes campos"})
            for nome, estado in resumo["marcados_no_documento"].items():
                g.pend("campo", nome, f"estado {estado}: marcado na minuta, não concluído")
            for aviso in r["avisos"]:
                g.pend("minuta", aviso["onde"], aviso["mensagem"])
            for escalar in resumo.get("escalar", []):
                g.pend("escalar_minuta", "minuta", escalar)
        except FALHAS_DOCUMENTO as e:
            r = {"erros": [_erro(e)], "avisos": []}
            resumo = {"lint": r, "completo": False, "conteudo_confere": False,
                      "marcados_no_documento": {}, "inspecao_visual": "nao_realizada"}
        documentos["minuta"] = resumo
        resultado = "reprovado" if r["erros"] else ("alerta" if r["avisos"] or not resumo["completo"] else "aprovado")
        g.add("G15_minuta", "campos e conteúdo da minuta conferidos contra modelo e fontes", resultado,
              "; ".join(e["codigo"] for e in r["erros"]) or "partes do DOCX conferidas; não comprova aparência ou aprovação jurídica")
    return documentos
