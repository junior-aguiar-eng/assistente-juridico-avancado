"""Expansão de argumentos de arquivo independente do shell, sem resolver links."""
import glob
from pathlib import Path


def expandir_argumentos(entradas: list[str]) -> list[str]:
    """Prefere caminhos literais existentes e preserva padrões sem correspondência.

    Cada CLI decide como relatar entradas ausentes. Repetições lexicais são
    removidas mantendo a ordem, sem transformar links em seus destinos.
    """
    caminhos, vistos = [], set()
    for entrada in entradas:
        p = Path(entrada)
        if p.exists() or p.is_symlink() or not glob.has_magic(entrada):
            candidatos = [entrada]
        else:
            candidatos = sorted(glob.glob(entrada)) or [entrada]
        for candidato in candidatos:
            chave = Path(candidato).absolute()
            if chave not in vistos:
                vistos.add(chave)
                caminhos.append(candidato)
    return caminhos
