import importlib
import json
from pathlib import Path

import pytest

from test_pecas import RAIZ, caso, codigos, validar


def propor(ext, sha, **kw):
    assert (RAIZ / 'scripts/pecas_proposta.py').exists(), 'Falta a proposta conservadora de peças'
    return importlib.import_module('pecas_proposta').propor_inventario(ext, arquivo_sha256=sha, **kw)


@pytest.mark.parametrize('cid,tipos', [('CT01', ['sentenca', 'acordao']), ('CT03', ['nao_identificada']), ('CT04', ['nao_identificada']), ('CT05', [])])
def test_proposta_nao_confunde_secao_com_tipo_nem_citacao_com_fronteira(cid, tipos):
    _, ext, sha = caso(cid)
    inv = propor(ext, sha)
    assert [p['tipo_proposto'] for p in inv['pecas']] == tipos
    assert validar(inv, ext, sha)['valido']
    assert all(p['tipo']['estado'] == p['limites']['estado'] == 'proposto' for p in inv['pecas'])
    assert all(e['ator']['tipo'] == 'sistema' for e in inv['eventos'])


def test_revisao_manual_divide_duas_pecas_do_mesmo_tipo_no_mesmo_bloco():
    _, ext, sha = caso('CT02')
    inv = propor(ext, sha, fronteiras=[{'block_id': 'b0001', 'offset': 0, 'tipo': 'peticao'},
                                      {'block_id': 'b0001', 'offset': 11, 'tipo': 'peticao'}])
    assert len(inv['pecas']) == 2
    assert [(f['inicio'], f['fim']) for f in inv['fragmentos']] == [(0, 11), (11, 21)]
    assert validar(inv, ext, sha)['valido']
    assert all(p['limites']['estado'] == 'proposto' for p in inv['pecas'])


def test_fronteira_manual_multipagina_preserva_offsets_e_nao_confirma_localizacao():
    _, ext, sha = caso('CT06')
    inv = propor(ext, sha, fronteiras=[{'block_id': 'b0001', 'offset': 0, 'tipo': 'sentenca'},
                                      {'block_id': 'b0001', 'offset': 17, 'tipo': 'acordao', 'pagina_anterior': 1, 'pagina_inicio': 2}])
    assert [f['paginas']['inicio'] for f in inv['fragmentos']] == [1, 2]
    assert [f['paginas']['fim'] for f in inv['fragmentos']] == [1, 2]
    assert all(f['paginas']['origem'] == 'conferencia_visual' for f in inv['fragmentos'])
    assert validar(inv, ext, sha)['valido']


def test_titulo_em_bloco_marcado_como_citacao_nao_inicia_peca():
    _, ext, sha = caso('CT01')
    obj = json.loads(ext)
    obj['documents'][0]['blocks'][1]['is_quote'] = True
    ext = json.dumps(obj).encode()
    inv = propor(ext, sha)
    assert len(inv['pecas']) == 1
    assert validar(inv, ext, sha)['valido']


@pytest.mark.parametrize('fronteira', [
    {'block_id': 'ausente', 'offset': 0, 'tipo': 'sentenca'},
    {'block_id': 'b0001', 'offset': 999, 'tipo': 'sentenca'},
    {'block_id': 'b0001', 'offset': 0, 'tipo': 'inventado'},
    {'block_id': 'b0001', 'offset': 0, 'tipo': 'sentenca', 'pagina_inicio': 99},
])
def test_recusa_fronteira_manual_incompativel(fronteira):
    _, ext, sha = caso()
    with pytest.raises(ValueError): propor(ext, sha, fronteiras=[fronteira])


def test_fronteiras_manuais_substituem_detectores_para_remover_falso_inicio():
    _, ext, sha = caso('CT01')
    inv = propor(ext, sha, fronteiras=[{'block_id': 'b0001', 'offset': 0, 'tipo': 'acordao'}])
    assert len(inv['pecas']) == 1
    assert inv['pecas'][0]['tipo_proposto'] == 'acordao'
    assert inv['pecas'][0]['evidencias'][0]['sinal'] == 'outro'
    assert validar(inv, ext, sha)['valido']


def test_recusa_duas_fronteiras_manuais_na_mesma_posicao():
    _, ext, sha = caso()
    corte = {'block_id': 'b0001', 'offset': 0, 'tipo': 'sentenca'}
    with pytest.raises(ValueError): propor(ext, sha, fronteiras=[corte, corte])


def test_limite_manual_com_tipo_desconhecido_nao_e_absorvido_pela_peca_seguinte():
    _, ext, sha = caso('CT02')
    inv = propor(ext, sha, fronteiras=[{'block_id': 'b0001', 'offset': 0, 'tipo': 'nao_identificada'},
                                      {'block_id': 'b0001', 'offset': 11, 'tipo': 'peticao'}])
    assert [p['tipo_proposto'] for p in inv['pecas']] == ['nao_identificada', 'peticao']
    assert validar(inv, ext, sha)['valido']
