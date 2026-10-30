"""Pacotes de regras de revisão contratual: rascunhos com o texto literal da lei, sempre INATIVOS até revisão jurídica.

  gerar  --fonte-cc CC.md --fonte-lgpd LGPD.md --fonte-lpi LPI.md --saida-dir rules/br [--lido-em AAAA-MM-DD]   escreve os pacotes-rascunho
  validar [--dir rules/br] [--fonte-cc CC.md] [--fonte-lgpd LGPD.md] [--fonte-lpi LPI.md]   confere estrutura, ativação e texto literal
  listar [--dir rules/br] [--incluir-inativas]                                  regras que podem ser usadas

Uma regra só é usada se `status` for "ativa" **e** houver `revisao.revisor` e `revisao.data`. Este script nunca ativa
regra: a ativação é um ato do revisor jurídico, editando o arquivo. O texto literal vem da versão compilada do Planalto;
parâmetro de mercado ou regra de outra jurisdição não vira regra brasileira.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

NORMAS = {
    "cc": {"nome": "Lei nº 10.406/2002 (Código Civil)", "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"},
    "lgpd": {"nome": "Lei nº 13.709/2018 (LGPD)",
             "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm"},
    "lpi": {"nome": "Lei nº 9.279/1996 (Lei da Propriedade Industrial)",
            "url": "https://www.planalto.gov.br/ccivil_03/leis/l9279.htm"},
}
RASCUNHO = "Rascunho do mantenedor técnico: pergunta de revisão não revisada por profissional do Direito."

# (id, pacote, artigo, tópico, pergunta de revisão, norma)
CODIGO_CIVIL = [
    ("civ-412", "servicos_saas", "412", "cláusula penal: teto", "Alguma cláusula penal, inclusive por inadimplemento ou rescisão antecipada conforme sua natureza jurídica, pode exceder o valor da obrigação principal concretamente identificada, sem presumir que ela corresponda à mensalidade ou ao valor integral do contrato?", "cc"),
    ("civ-413", "servicos_saas", "413", "cláusula penal: redução", "Há indícios de cumprimento parcial da obrigação principal ou de penalidade manifestamente excessiva, considerada a natureza e a finalidade do negócio, que justifiquem alertar para eventual redução equitativa judicial?", "cc"),
    ("civ-421a", "servicos_saas", "421-A", "paridade e alocação de riscos", "Em contrato civil ou empresarial, como foram alocados os riscos e existem elementos concretos que possam afastar a presunção de paridade e simetria, ressalvados os regimes especiais? Há possível relação de consumo a exigir análise do CDC, inclusive entre empresas?", "cc"),
    ("civ-422", "servicos_saas", "422", "boa-fé", "Há cláusula concretamente incompatível com os deveres de cooperação, lealdade e boa-fé objetiva na conclusão ou na execução do contrato?", "cc"),
    ("civ-423", "servicos_saas", "423", "adesão: ambiguidade", "Há cláusulas predispostas unilateralmente, sem possibilidade substancial de negociação, que indiquem contrato de adesão? Em caso afirmativo, há cláusulas ambíguas ou contraditórias cuja interpretação mais favorável ao aderente deva ser examinada?", "cc"),
    ("civ-424", "servicos_saas", "424", "adesão: renúncia antecipada", "Em contrato de adesão, alguma cláusula estipula renúncia antecipada do aderente a direito resultante da natureza do negócio, indicando possível nulidade a ser examinada?", "cc"),
    ("civ-473", "servicos_saas", "473", "resilição unilateral", "Quando admitida a resilição unilateral, há previsão de denúncia notificada à outra parte e, havendo investimentos consideráveis para a execução, de prazo compatível com a natureza e o vulto dos investimentos?", "cc"),
    ("civ-478", "servicos_saas", "478", "onerosidade excessiva", "Em contrato de execução continuada ou diferida, há cláusula que exclua a resolução por onerosidade excessiva? Se houver, quais são os requisitos legais, a alocação de riscos e as circunstâncias relevantes para avaliar sua validade, sem presumir sua invalidade?", "cc"),
    ("civ-598", "servicos_saas", "598", "prestação de serviço: prazo máximo", "O contrato pode ser enquadrado no regime típico de prestação de serviços do Código Civil e, em caso afirmativo, prevê prazo superior a quatro anos? Não presumir esse enquadramento para contratos SaaS, de licenciamento ou mistos.", "cc"),
]
LGPD = [
    ("lgpd-7", "lgpd", "7", "base legal do tratamento", "Cada operação de tratamento identificada no contrato tem uma hipótese legal do art. 7 que a sustente?", "lgpd"),
    ("lgpd-11", "lgpd", "11", "dado sensível", "O contrato prevê tratamento de dado pessoal sensível? Em caso positivo, a hipótese específica do art. 11 está identificada?", "lgpd"),
    ("lgpd-18", "lgpd", "18", "direitos do titular", "O contrato prevê mecanismos para o controlador atender os pedidos do titular (acesso, correção, eliminação, portabilidade) e, quanto à confirmação de existência e ao acesso, os prazos do art. 19 (resposta simplificada imediata ou declaração completa em até 15 dias)?", "lgpd"),
    ("lgpd-33", "lgpd", "33", "transferência internacional", "Há armazenamento, suporte ou subprocessador fora do Brasil? Em caso positivo, a hipótese do art. 33 está identificada?", "lgpd"),
    ("lgpd-37", "lgpd", "37", "registro das operações", "O contrato prevê a manutenção do registro das operações de tratamento por controlador e operador? A ausência de cláusula específica não configura, por si só, infração ao art. 37.", "lgpd"),
    ("lgpd-39", "lgpd", "39", "operador e instruções", "O contrato define os papéis de controlador e operador e as instruções ao operador, ressalvado que a qualificação jurídica depende das atividades efetivamente desempenhadas?", "lgpd"),
    ("lgpd-41", "lgpd", "41", "encarregado", "O contrato indica o encarregado (ou o canal) de cada parte, observadas as dispensas regulamentares e a distinção entre controlador e operador?", "lgpd"),
    ("lgpd-42", "lgpd", "42", "responsabilidade e ressarcimento", "A cláusula de limitação de responsabilidade distingue a responsabilidade entre as partes da responsabilidade legal perante o titular, ou aparenta restringir a reparação devida a este por dano de tratamento irregular?", "lgpd"),
    ("lgpd-46", "lgpd", "46", "segurança", "O contrato prevê medidas de segurança técnicas e administrativas? A adequação efetiva ao risco dos dados exige análise material, não apenas textual.", "lgpd"),
    ("lgpd-48", "lgpd", "48", "incidente de segurança", "O contrato fixa prazo e procedimento para comunicar incidente de segurança à outra parte, de modo compatível com a obrigação do controlador de comunicar a ANPD e o titular?", "lgpd"),
]
# O art. 195 da Lei 9.279/1996 é o texto literal inteiro; as duas regras separam as perguntas de revisão (incisos XI e XII).
NDA = [
    ("pi-195-xi", "nda", "195", "sigilo: informação confidencial obtida por relação contratual (art. 195, XI)",
     "A definição de informação confidencial exclui o que é de conhecimento público ou evidente para um técnico no assunto, "
     "e o fim do contrato é tratado de modo compatível com a ressalva 'mesmo após o término do contrato'?", "lpi"),
    ("pi-195-xii", "nda", "195", "sigilo: informação obtida por meio ilícito ou fraude (art. 195, XII)",
     "O contrato trata expressamente do uso de informação confidencial obtida por meio ilícito ou mediante fraude, "
     "ou deixa essa hipótese apenas à lei?", "lpi"),
]
PENDENCIAS_LGPD = [
    "Regulamentos da ANPD apontados em parecer anexado pelo titular e ainda não incorporados como fonte (texto oficial não lido, data e hash a registrar): Resolução CD/ANPD nº 19/2024 (transferência internacional e cláusulas-padrão), nº 18/2024 (encarregado), nº 15/2024 (comunicação de incidente; prazo de 3 dias úteis informado só por fonte secundária) e nº 2/2022 (agentes de pequeno porte): decisão do revisor jurídico se entram no pacote",
    "lgpd-18: a pergunta remete ao art. 19 da Lei 13.709/2018, que consta do compilado guardado no repositório, mas ainda não é fonte própria da regra: decisão do revisor jurídico",
]
PENDENCIAS_SERVICOS_SAAS = [
    "Escopo proposto em parecer anexado pelo titular: aplicação prioritária a contratos civis e empresariais, com alerta de possível incidência do CDC em contrato de consumo; decisão do revisor jurídico",
]
PENDENCIAS = {"lgpd": PENDENCIAS_LGPD, "servicos_saas": PENDENCIAS_SERVICOS_SAAS}
PENDENCIAS_NDA = [
    "Lei nº 9.279/1996, art. 195 tipifica crime de concorrência desleal; a via civil está nos arts. 207 e 209 da mesma lei "
    "(lidos na versão compilada, sem virar regra): decisão do revisor jurídico se entram no pacote",
    "Prazo de vigência do dever de sigilo e foro: sem regra legal específica; decisão do revisor jurídico",
]
_CABECALHO = re.compile(r"^(Art\.\s*\d|LIVRO|T[ÍI]TULO|CAP[ÍI]TULO|Se[cç][aã]o|Subse[cç][aã]o|\*\*)")
_DISP_REVOGADO = re.compile(r"^((?:§\s*\d+[º°o]?|[IVXLC]+|[a-z]\)|Parágrafo único)[^()]{0,12})\((?:Revogad[oa]|VETAD[OA])[^)]*\)\.?$", re.I)
_REDACAO = re.compile(r"\[\((?P<n>[^\]]*?)\)\]\([^)]*\)", re.S)
_LINK_MD = re.compile(r"\[([^\]\n]+)\]\([^)\s]*\)")  # [texto](url) da conversão da página: fica só o texto


def _ns(s: str) -> str:
    return " ".join(s.split())


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def extrair_artigo(texto: str, numero: str) -> dict:
    """Texto literal do artigo no Markdown compilado. Recusa artigo revogado, tachado ou não encontrado."""
    linhas = texto.splitlines()
    rx = re.compile(r"^Art\.\s*" + re.escape(numero).replace(r"\-", "-") + r"(?![\d\-A-Za-z])")
    ini = next((i for i, l in enumerate(linhas) if rx.match(l)), None)
    if ini is None:
        raise ValueError(f"art. {numero} não encontrado no texto compilado")
    fim = ini + 1
    while fim < len(linhas) and not _CABECALHO.match(linhas[fim]):
        fim += 1
    junto = "\n".join(linhas[ini:fim])
    # "§ 4º" numa linha e "[(VETADO)](link)" na seguinte: junta para o dispositivo ser reconhecido como um só
    junto = re.sub(r"((?:§\s*\d+[º°o]?|[IVXLC]+\s*[-–]?))\s*\n\s*\[\((VETADO|Revogad[oa])[^\]]*\)\]\([^)]*\)", r"\1 (\2)", junto)
    junto = re.sub(r"\[Vig[êe]ncia\]\([^)]*\)", "", junto)
    bloco = junto.splitlines()
    if re.search(r"\((?:Revogad|VETAD)", bloco[0], re.I):
        raise ValueError(f"art. {numero} revogado ou vetado: não é fonte de regra")
    revogados, mantidas, pular = [], [], False
    for l in bloco:
        if pular:  # notas de redação que pertencem ao dispositivo revogado/vetado vão junto com ele
            pular = bool(l.strip())
            if pular:
                continue
        m = _DISP_REVOGADO.match(l.strip())
        if m:
            revogados.append(_ns(m.group(1)))  # dispositivo isolado revogado ou vetado: sai do texto e fica registrado
            pular = True
        else:
            mantidas.append(l)
    bruto = "\n".join(mantidas)
    if "~~" in bruto or re.search(r"\((?:Revogad|VETAD)", bruto, re.I):
        raise ValueError(f"art. {numero} tem trecho tachado ou revogado fora de um dispositivo isolado: não é fonte de regra")
    redacao = list(dict.fromkeys(_ns(m.group("n")) for m in _REDACAO.finditer(bruto)))
    limpo = _LINK_MD.sub(r"\1", _REDACAO.sub("", bruto))
    paragrafos = [_ns(p) for p in re.split(r"\n\s*\n", limpo) if _ns(p)]
    # a fonte grafa "caput" em itálico, sozinho num parágrafo, o que quebra a frase em três: cola ao anterior e ao seguinte
    colados, colar = [], False
    for p in paragrafos:
        if colar:
            colados[-1] += " " + p
            colar = False
        elif p == "caput" and colados:
            colados[-1] += " " + p
            colar = True
        else:
            colados.append(p)
    paragrafos = colados
    return {"texto_literal": "\n".join(paragrafos), "redacao": redacao, "dispositivos_revogados": revogados}


def gerar(fontes: dict[str, Path], saida_dir: Path, lido_em: str | None = None) -> dict:
    """fontes: {'cc': caminho do Markdown compilado, 'lgpd': ..., 'lpi': ...}. Cada regra guarda o hash do arquivo de onde foi lida."""
    lido_em = lido_em or date.today().isoformat()
    date.fromisoformat(lido_em)
    brutos = {k: Path(v).read_bytes() for k, v in fontes.items()}
    pacotes: dict[str, list] = {}
    for rid, pacote, art, topico, pergunta, norma in CODIGO_CIVIL + LGPD + NDA:
        if norma not in brutos:
            continue
        art_ = extrair_artigo(brutos[norma].decode("utf-8"), art)
        pacotes.setdefault(pacote, []).append({
            "id": rid, "topico": topico, "pergunta_de_revisao": pergunta, "status": "inativa",
            "revisao": {"revisor": None, "data": None, "observacao": None}, "nota": RASCUNHO,
            "fonte": {"norma_id": norma, "norma": NORMAS[norma]["nome"], "artigo": art, "url": NORMAS[norma]["url"],
                      "arquivo_sha256": _sha(brutos[norma]), "lido_em": lido_em, "versao": "compilada", **art_}})
    pacotes.setdefault("nda", [])
    saida_dir = Path(saida_dir)
    saida_dir.mkdir(parents=True, exist_ok=True)
    escritos = []
    for nome, regras in pacotes.items():
        obj = {"schema_version": "1", "pacote": nome, "jurisdicao": "BR", "regras": regras,
               "pendencias_de_fonte": PENDENCIAS_NDA if nome == "nda" else PENDENCIAS.get(nome, [])}
        (saida_dir / f"{nome}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        escritos.append({"pacote": nome, "regras": len(regras)})
    return {"escritos": escritos, "status": "todas inativas e sem revisão", "lido_em": lido_em}


def _ativa(r: dict) -> bool:
    rev = r.get("revisao") or {}
    return r.get("status") == "ativa" and bool(rev.get("revisor")) and bool(rev.get("data"))


def validar(dir_: Path, fonte: Path | None = None, fontes: dict[str, Path] | None = None) -> dict:
    """`fonte` (compat.) é o Código Civil; `fontes` mapeia norma_id -> arquivo. Só regras com fonte fornecida têm o texto conferido."""
    erros, avisos = [], []
    textos = {k: Path(v).read_text(encoding="utf-8") for k, v in (fontes or {}).items()}
    if fonte:
        textos.setdefault("cc", Path(fonte).read_text(encoding="utf-8"))
    ids = set()
    for arq in sorted(Path(dir_).glob("*.json")):
        obj = json.loads(arq.read_text(encoding="utf-8"))
        for r in obj.get("regras", []):
            w = f"{arq.name}:{r.get('id')}"
            if r.get("id") in ids:
                erros.append({"codigo": "id_duplicado", "onde": w})
            ids.add(r.get("id"))
            if r.get("status") not in ("inativa", "ativa"):
                erros.append({"codigo": "status_invalido", "onde": w})
            if r.get("status") == "ativa" and not _ativa(r):
                erros.append({"codigo": "ativa_sem_revisor", "onde": w,
                              "mensagem": "regra ativa exige revisao.revisor e revisao.data"})
            f = r.get("fonte") or {}
            if not (f.get("norma") and f.get("artigo") and f.get("texto_literal") and f.get("url") and f.get("lido_em")):
                erros.append({"codigo": "fonte_incompleta", "onde": w})
            elif (texto := textos.get(f.get("norma_id", "cc"))) is not None:
                try:
                    atual = extrair_artigo(texto, f["artigo"])["texto_literal"]
                    if atual != f["texto_literal"]:
                        erros.append({"codigo": "texto_diverge_da_fonte", "onde": w,
                                      "mensagem": "o texto da regra não é o da versão compilada lida"})
                except ValueError as e:
                    erros.append({"codigo": "artigo_indisponivel", "onde": w, "mensagem": str(e)})
        for p in obj.get("pendencias_de_fonte", []):
            avisos.append({"codigo": "pendencia_de_fonte", "onde": arq.name, "mensagem": p})
    return {"erros": erros, "avisos": avisos, "regras": len(ids)}


def carregar(dir_: Path, pacote: str, incluir_inativas: bool = False) -> dict:
    """Regras do pacote que podem ser usadas; as demais voltam em `excluidas` com o motivo."""
    arq = Path(dir_) / f"{pacote}.json"
    if not arq.is_file():
        raise ValueError(f"pacote '{pacote}' não existe em {dir_}")
    obj = json.loads(arq.read_text(encoding="utf-8"))
    usadas, excluidas = [], []
    for r in obj.get("regras", []):
        if _ativa(r) or incluir_inativas:
            usadas.append({**r, "uso": "revisada" if _ativa(r) else "RASCUNHO_NAO_REVISADO"})
        else:
            excluidas.append({"id": r["id"], "motivo": "inativa ou sem revisor jurídico"})
    return {"pacote": pacote, "regras": usadas, "excluidas": excluidas, "pendencias_de_fonte": obj.get("pendencias_de_fonte", [])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--fonte-cc")
    g.add_argument("--fonte-lgpd")
    g.add_argument("--fonte-lpi")
    g.add_argument("--saida-dir", required=True)
    g.add_argument("--lido-em")
    v = sub.add_parser("validar")
    v.add_argument("--dir", default="rules/br")
    v.add_argument("--fonte-cc")
    v.add_argument("--fonte-lgpd")
    v.add_argument("--fonte-lpi")
    l = sub.add_parser("listar")
    l.add_argument("--dir", default="rules/br")
    l.add_argument("--pacote", default="servicos_saas")
    l.add_argument("--incluir-inativas", action="store_true")
    n = ap.parse_args(argv)
    try:
        if n.cmd == "gerar":
            fs = {k: Path(v) for k, v in (("cc", n.fonte_cc), ("lgpd", n.fonte_lgpd), ("lpi", n.fonte_lpi)) if v}
            if not fs:
                raise ValueError("informe --fonte-cc, --fonte-lgpd e/ou --fonte-lpi")
            res, cod = gerar(fs, Path(n.saida_dir), n.lido_em), 0
        elif n.cmd == "validar":
            res = validar(Path(n.dir), fontes={k: Path(v) for k, v in (("cc", n.fonte_cc), ("lgpd", n.fonte_lgpd), ("lpi", n.fonte_lpi)) if v})
            cod = 1 if res["erros"] else 0
        else:
            res, cod = carregar(Path(n.dir), n.pacote, n.incluir_inativas), 0
    except (ValueError, OSError, KeyError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
