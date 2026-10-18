"""Higiene dos fontes: caractere de controle (ex.: \b virando backspace ao gerar código) quebra regex em silêncio."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def test_nenhum_fonte_tem_caractere_de_controle():
    arquivos = [*RAIZ.glob("scripts/*.py"), *RAIZ.glob("tests/*.py"), *RAIZ.glob("skills/*/SKILL.md"), *RAIZ.glob("shared/*.md")]
    assert len(arquivos) > 30
    ruins = [str(a.relative_to(RAIZ)) for a in arquivos if CONTROLE.search(a.read_text(encoding="utf-8"))]
    assert ruins == []
