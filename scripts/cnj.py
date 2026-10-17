"""Validador e gerador do número único de processo (Resolução CNJ 65/2008, Anexo VIII).

Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
  NNNNNNN número sequencial, DD dígito verificador, AAAA ano de ajuizamento,
  J segmento do Poder Judiciário, TR tribunal/região, OOOO unidade de origem.

DV = 98 - (NNNNNNN AAAA J TR OOOO 00  mod 97).  Válido quando
(NNNNNNN AAAA J TR OOOO DD) mod 97 == 1.

Este módulo valida a estrutura e o dígito verificador. Não confere se o
tribunal ou a unidade existem (tabelas do CNJ), nem se o processo existe.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass

_FORMATADO = re.compile(r"^(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$")
_CORRIDO = re.compile(r"^\d{20}$")


@dataclass(frozen=True)
class NumeroCNJ:
    sequencial: str
    dv: str
    ano: str
    segmento: str
    tribunal: str
    origem: str

    @property
    def formatado(self) -> str:
        return f"{self.sequencial}-{self.dv}.{self.ano}.{self.segmento}.{self.tribunal}.{self.origem}"


def _base(sequencial: str, ano: str, segmento: str, tribunal: str, origem: str) -> str:
    return f"{sequencial}{ano}{segmento}{tribunal}{origem}"


def calcular_dv(sequencial: str, ano: str, segmento: str, tribunal: str, origem: str) -> str:
    base = _base(sequencial, ano, segmento, tribunal, origem)
    return f"{98 - (int(base + '00') % 97):02d}"


def parse(texto: str) -> NumeroCNJ | None:
    """Divide o número em campos; None se a estrutura for inválida."""
    t = texto.strip()
    m = _FORMATADO.match(t)
    if m:
        seq, dv, ano, seg, tr, org = m.groups()
    elif _CORRIDO.match(t):
        seq, dv, ano, seg, tr, org = t[0:7], t[7:9], t[9:13], t[13], t[14:16], t[16:20]
    else:
        return None
    return NumeroCNJ(seq, dv, ano, seg, tr, org)


def validar(texto: str) -> tuple[bool, str]:
    """Retorna (válido, motivo). Motivo é 'ok' quando válido."""
    n = parse(texto)
    if n is None:
        return False, "estrutura inválida (esperado NNNNNNN-DD.AAAA.J.TR.OOOO ou 20 dígitos)"
    if n.segmento == "0":
        return False, "segmento J=0 não existe"
    esperado = calcular_dv(n.sequencial, n.ano, n.segmento, n.tribunal, n.origem)
    if esperado != n.dv:
        return False, f"dígito verificador incorreto (informado {n.dv}, esperado {esperado})"
    return True, "ok"


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        ok, motivo = validar(arg)
        print(f"{arg}\t{'VÁLIDO' if ok else 'INVÁLIDO'}\t{motivo}")
