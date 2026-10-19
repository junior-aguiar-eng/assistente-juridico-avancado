"""Subconjuntos explícitos para testar fluxos válidos sem liberar o caso histórico."""
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def claims_stj_reconferiveis():
    """Somente c001–c004 e a fonte primária de c001; não é o pacote histórico completo.

    c001/s2 e c005/s1 continuam intactos no JSON original e bloqueados nos
    testes do caso histórico até recuperar os respectivos documentos reais.
    """
    path = Path(__file__).parent / "casos" / "verificacao_stj" / "claims.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["claims"] = [c for c in obj["claims"] if c["id"] in ("c001", "c002", "c003", "c004")]
    c1 = next(c for c in obj["claims"] if c["id"] == "c001")
    c1["sources"] = [s for s in c1["sources"] if s["source_id"] == "s1"]
    return obj
