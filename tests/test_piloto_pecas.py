"""Piloto real opcional; saída contém somente métricas e referências, sem transcrições."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize('motor', ['atual', 'docling-parse'])
def test_piloto_publico_produz_metricas_e_contrato_integro(motor):
    if motor == 'docling-parse' and importlib.util.find_spec('docling_parse') is None:
        pytest.skip('docling-parse opcional não instalado neste ambiente')
    script = RAIZ / 'scripts/piloto_pecas.py'
    assert script.exists(), 'Falta o piloto local reproduzível'
    r = subprocess.run([sys.executable, str(script), '--motor', motor, '--original',
                        str(RAIZ / 'tests/casos/stj_aresp_2432194.pdf')], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    obj = json.loads(r.stdout)
    assert obj['execucao'] == 'concluida'
    assert obj['contrato_valido']
    assert obj['paginas'] == 16
    assert obj['blocos'] > 0 and obj['caracteres'] > 0
    assert obj['segundos'] >= 0
    assert obj['motor'] == motor
    assert 'text' not in obj and 'documents' not in obj
    assert all(set(p) == {'tipo_proposto', 'inicio', 'fim'} for p in obj['pecas'])
