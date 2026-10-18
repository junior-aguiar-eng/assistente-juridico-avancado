"""Detecção heurística de texto dirigido ao modelo dentro de documentos (injeção de prompt).

Documentos, páginas e acórdãos são dados, nunca instruções. Estas regras só **avisam**: o texto continua
sendo tratado como dado e nenhuma ação é tomada por causa dele. Falsos positivos são esperados; falso
negativo é possível (a varredura é por frases conhecidas, não é garantia).
"""
from __future__ import annotations

import re

_B = chr(92) + "b"  # \b
_PADROES = [
    ("ignora_instrucoes", r"(?i)ignore (all |any )?(the )?(previous|above|prior|earlier) (instructions|rules|prompts)|disregard (the )?(above|previous|prior)"
                          r"|(ignore|desconsidere|esque[cç]a)( todas)?( as| os| o que)? (instru[cç][oõ]es|regras|ordens|comandos)( anteriores| acima| do sistema)?"),
    ("troca_de_papel", r"(?i)voc[eê] agora [ée] |you are now |seu novo papel|your new role|developer mode|modo desenvolvedor|priority override"),
    ("autoridade_falsa", r"(?i)as the administrator|como administrador do sistema|this is a system (prompt|message)|esta [ée] uma mensagem do sistema|system prompt|prompt do sistema"),
    ("dirigido_a_ia", r"(?i)" + _B + r"(ia|assistente|claude|chatgpt|gpt|llm|modelo de linguagem|ai assistant|assistant)" + _B +
                      r"[^.\n]{0,100}" + _B + r"(envie|encaminhe|ignore|aprove|execute|rode|revele|apague|classifique|marque|considere|trate|defina|"
                      r"send|forward|approve|run|reveal|delete|classify|mark|treat|set)" + _B),
    ("papel_no_texto", r"(?im)^\s*(assistente|assistant|claude|chatgpt)\s*:"),
    ("ordem_de_execucao", r"(?i)(execute|rode|run) (o seguinte comando|the following command)|(aprove|approve) (automaticamente|automatically)"),
]
PADROES = [(nome, re.compile(p)) for nome, p in _PADROES]


def detectar(texto: str) -> list[dict]:
    """Achados {padrao, trecho}: o trecho é a frase suspeita (até 90 caracteres), nunca o texto todo."""
    achados = []
    for nome, rx in PADROES:
        for m in rx.finditer(texto):
            achados.append({"padrao": nome, "trecho": " ".join(m.group(0).split())[:90]})
    return achados


def alguma(texto: str) -> bool:
    return any(rx.search(texto) for _, rx in PADROES)
