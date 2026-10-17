"""Detecção de dados pessoais em texto (CPF, CNPJ, cartão, e-mail, telefone) com valores mascarados.

CPF, CNPJ e cartão só contam se o dígito verificador (ou Luhn) fecha, para reduzir falso positivo.
Nenhuma função devolve o valor completo: só o tipo, a posição e uma máscara.
"""
from __future__ import annotations

import re

_CPF = re.compile(r"(?<![\d.\-/])(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})(?![\d\-/])")
_CNPJ = re.compile(r"(?<![\d.\-/])(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})(?![\d\-/])")
_CARTAO = re.compile(r"(?<![\d.\-/])(\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{1,7}|\d{13,19})(?![\d\-/])")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_FONE = re.compile(r"(?<!\d)(?:\+55\s?)?(?:\(\d{2}\)\s?|\d{2}\s)9?\d{4}-\d{4}(?!\d)")

TIPOS = ("cpf", "cnpj", "cartao", "email", "telefone")


def _digitos(s: str) -> str:
    return re.sub(r"\D", "", s)


def cpf_valido(s: str) -> bool:
    d = _digitos(s)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != int(d[n]):
            return False
    return True


def cnpj_valido(s: str) -> bool:
    d = _digitos(s)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for n in (12, 13):
        soma = sum(int(d[i]) * pesos[i + (13 - n)] for i in range(n))
        resto = soma % 11
        if int(d[n]) != (0 if resto < 2 else 11 - resto):
            return False
    return True


def luhn_valido(s: str) -> bool:
    d = _digitos(s)
    if not 13 <= len(d) <= 19 or len(set(d)) == 1:
        return False
    total = 0
    for i, ch in enumerate(reversed(d)):
        n = int(ch)
        if i % 2:
            n *= 2
            n -= 9 if n > 9 else 0
        total += n
    return total % 10 == 0


def mascara(tipo: str, valor: str) -> str:
    d = _digitos(valor)
    if tipo == "cpf":
        return f"***.***.***-{d[-2:]}"
    if tipo == "cnpj":
        return f"**.***.***/****-{d[-2:]}"
    if tipo == "cartao":
        return f"****-****-****-{d[-4:]}"
    if tipo == "telefone":
        return f"(**) *****-{d[-4:]}"
    nome, _, dominio = valor.partition("@")
    return f"{nome[:1]}***@{dominio}"


def detectar(texto: str) -> list[dict]:
    """Lista de achados {tipo, inicio, fim, mascara}, sem sobreposição, em ordem de posição."""
    achados: list[dict] = []
    ocupado: list[tuple[int, int]] = []

    def livre(a, b):
        return all(b <= x or a >= y for x, y in ocupado)

    for tipo, padrao, ok in (("cnpj", _CNPJ, cnpj_valido), ("cpf", _CPF, cpf_valido), ("cartao", _CARTAO, luhn_valido),
                             ("email", _EMAIL, lambda v: True), ("telefone", _FONE, lambda v: True)):
        for m in padrao.finditer(texto):
            a, b = m.span()
            if ok(m.group()) and livre(a, b):
                ocupado.append((a, b))
                achados.append({"tipo": tipo, "inicio": a, "fim": b, "mascara": mascara(tipo, m.group())})
    return sorted(achados, key=lambda x: x["inicio"])


def tipos_presentes(texto: str) -> list[str]:
    return sorted({a["tipo"] for a in detectar(texto)})
