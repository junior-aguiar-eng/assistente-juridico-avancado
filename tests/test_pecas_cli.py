import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize('modo', ['integro', 'original_trocado', 'inventario_invalido', 'extracao_invalida', 'arquivo_ausente'])
def test_cli_valida_sem_modificar_entradas_ou_expor_texto(tmp_path, modo):
    caso = json.loads((RAIZ / 'tests/casos/pecas_contrato/exemplos.json').read_text(encoding='utf-8'))['exemplos'][0]
    caminhos = {k: tmp_path / (k + '.json') for k in ('inventario', 'extracao', 'original')}
    caminhos['inventario'].write_text(json.dumps(caso['inventario']), encoding='utf-8', newline='\n')
    caminhos['extracao'].write_bytes(caso['extracao_json_utf8'].encode('utf-8'))
    caminhos['original'].write_bytes(caso['origem_simulada_utf8'].encode('utf-8'))
    if modo == 'original_trocado': caminhos['original'].write_text('SEGREDO-ARTIFICIAL')
    elif modo == 'inventario_invalido': caminhos['inventario'].write_text('{"schema_version":"SEGREDO-ARTIFICIAL"}')
    elif modo == 'extracao_invalida': caminhos['extracao'].write_text('SEGREDO-ARTIFICIAL')
    elif modo == 'arquivo_ausente': caminhos['original'].unlink()
    antes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in caminhos.items() if p.exists()}
    comando = [sys.executable, str(RAIZ / 'scripts/pecas.py'), 'validar']
    for k, p in caminhos.items(): comando += ['--' + k, str(p)]
    r = subprocess.run(comando, capture_output=True, text=True)
    assert r.returncode == (0 if modo == 'integro' else 1)
    obj = json.loads(r.stdout)
    assert obj['valido'] == (modo == 'integro')
    assert r.stderr == ''
    assert 'SEGREDO-ARTIFICIAL' not in r.stdout
    assert antes == {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in caminhos.items() if p.exists()}
