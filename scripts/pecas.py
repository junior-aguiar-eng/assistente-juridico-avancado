"""Integridade do inventário v1; validade não é aprovação jurídica ou de leitura."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from pecas_validacao import validar_grafo
from pecas_historico import validar_historico

_SCHEMA = json.loads((Path(__file__).resolve().parent.parent / 'docs/contratos/pecas-v1.schema.json').read_text(encoding='utf-8'))
_VALIDATOR = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())
_SHA = re.compile(r'[0-9a-f]{64}\Z')
_ID = re.compile(r'[A-Za-z0-9_-]+\Z')


def _sha(bruto):
    return hashlib.sha256(bruto).hexdigest()


def _json(bruto):
    """JSON estrito: não aceitar chaves duplicadas nem números não finitos."""
    def pares(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise ValueError('chave duplicada')
            obj[k] = v
        return obj

    def nao_finito(_):
        raise ValueError('número não finito')

    return json.loads(bruto.decode('utf-8'), object_pairs_hook=pares, parse_constant=nao_finito)


def _inteiro(n):
    return type(n) is int


def _documento(pacote, origem):
    if not isinstance(pacote, dict):
        raise ValueError('extração deve ser objeto')
    docs = pacote.get('documents', [pacote])
    if not isinstance(docs, list) or not all(isinstance(d, dict) for d in docs):
        raise ValueError('documentos inválidos')
    encontrados = [d for d in docs if d.get('document_id') == origem['document_id']]
    if len(encontrados) != 1:
        raise ValueError('documento ausente/ambíguo')
    doc = encontrados[0]
    total = doc.get('page_count')
    if not _inteiro(total) or total < 1:
        raise ValueError('paginação física ausente')
    if doc.get('status') not in ('ok', 'partial', 'no_text'):
        raise ValueError('extração indisponível')
    blocos = doc.get('blocks')
    if not isinstance(blocos, list):
        raise ValueError('blocos ausentes')
    for b in blocos:
        if (not isinstance(b, dict) or not isinstance(b.get('id'), str) or not _ID.fullmatch(b['id'])
                or not isinstance(b.get('text'), str)
                or not _inteiro(b.get('page')) or not _inteiro(b.get('page_end', b.get('page')))
                or not 1 <= b['page'] <= b.get('page_end', b['page']) <= total
                or not isinstance(b.get('tags', []), list)
                or not all(isinstance(t, str) for t in b.get('tags', []))):
            raise ValueError('bloco incompatível')
    avisos = doc.get('warnings', [])
    if not isinstance(avisos, list) or not all(isinstance(a, dict) and isinstance(a.get('codigo'), str) for a in avisos):
        raise ValueError('avisos incompatíveis')
    for a in avisos:
        for campo in ('page', 'pagina'):
            if campo in a and a[campo] is not None and (not _inteiro(a[campo]) or not 1 <= a[campo] <= total):
                raise ValueError('localização de aviso inválida')
        if 'page' in a and 'pagina' in a and a['page'] != a['pagina']:
            raise ValueError('localizações conflitantes no aviso')
    versoes = doc.get('extractor_versions', {})
    if not isinstance(versoes, dict):
        raise ValueError('versões incompatíveis')
    return doc


def validar_inventario(inventario: dict, extracao_bytes: bytes, *, arquivo_sha256: str,
                       anterior_bytes: bytes | None = None) -> dict:
    """Compara contrato e fontes externas. Não modifica entradas nem confirma peças."""
    erros = []
    avisos = []

    def erro(codigo, onde, mensagem):
        item = {'codigo': codigo, 'onde': onde, 'mensagem': mensagem}
        if item not in erros:
            erros.append(item)

    def resultado():
        return {'valido': not erros, 'erros': erros, 'avisos': avisos}

    if not _VALIDATOR.is_valid(inventario):
        erro('estrutura_invalida', '/inventario', 'Inventário incompatível com o esquema v1.')
        return resultado()
    # JSON Schema admite 2.0 como integer. Normalizar só campos estruturais
    # numa cópia; bytes da fonte e configuração permanecem intocados.
    inventario = copy.deepcopy(inventario)
    inventario['revisao'] = int(inventario['revisao'])
    inventario['origem']['total_paginas'] = int(inventario['origem']['total_paginas'])
    for pagina in inventario['paginas']:
        pagina['numero'] = int(pagina['numero'])
    for f in inventario['fragmentos']:
        for campo in ('inicio', 'fim'):
            f[campo] = int(f[campo])
            f['paginas'][campo] = int(f['paginas'][campo])
    for peca in inventario['pecas']:
        peca['ordem'] = int(peca['ordem'])
    o = inventario['origem']
    if not isinstance(arquivo_sha256, str) or not _SHA.fullmatch(arquivo_sha256) or o['arquivo_sha256'] != arquivo_sha256:
        erro('arquivo_divergente', '/origem/arquivo_sha256', 'Hash do original externo não coincide.')
    if not isinstance(extracao_bytes, bytes):
        erro('origem_invalida', '/extracao', 'Fornecer bytes UTF-8 exatos da extração.')
        return resultado()
    if o['extracao_sha256'] != _sha(extracao_bytes):
        erro('extracao_divergente', '/origem/extracao_sha256', 'Bytes da extração não coincidem.')
    try:
        pacote = _json(extracao_bytes)
        doc = _documento(pacote, o)
        params = pacote.get('run', {}).get('params')
        config = None if 'params' not in pacote.get('run', {}) else _sha(json.dumps(params, ensure_ascii=False, sort_keys=True,
                                                            separators=(',', ':'), allow_nan=False).encode('utf-8'))
    except (ValueError, TypeError, AttributeError, UnicodeError, RecursionError):
        erro('origem_invalida', '/extracao', 'Extração inválida, sem documento único ou paginação verificável.')
        return resultado()
    if doc.get('sha256') != o['arquivo_sha256']:
        erro('arquivo_divergente', '/extracao/sha256', 'Hash registrado na extração não coincide com o original.')
    versoes = doc.get('extractor_versions', {})
    if (doc['page_count'] != o['total_paginas'] or config != o['configuracao_sha256']
            or o['extrator']['versao'] != versoes.get('extractor', 'desconhecido')
            or o['extrator']['nome'] != versoes.get('nome', 'extract')):
        erro('origem_invalida', '/origem', 'Paginação, configuração ou extrator divergem da extração.')
    anteriores, prefixo = validar_historico(inventario, anterior_bytes, erro, _json, _sha, _VALIDATOR)
    validar_grafo(inventario, doc, erro, avisos, anteriores=anteriores, prefixo=prefixo)
    return resultado()


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='comando', required=True)
    v = sub.add_parser('validar', help='Verificar integridade; não aprova classificação ou leitura.')
    for campo in ('inventario', 'extracao', 'original'):
        v.add_argument('--' + campo, required=True, type=Path)
    v.add_argument('--anterior', type=Path)
    args = parser.parse_args(argv)
    try:
        caminhos = [args.inventario, args.extracao, args.original] + ([args.anterior] if args.anterior else [])
        if any(p.is_symlink() or not p.is_file() for p in caminhos):
            raise OSError('entrada indisponível')
        with args.original.open('rb') as entrada:
            sha = hashlib.file_digest(entrada, 'sha256').hexdigest()
        inv = _json(args.inventario.read_bytes())
        r = validar_inventario(inv, args.extracao.read_bytes(), arquivo_sha256=sha,
                               anterior_bytes=args.anterior.read_bytes() if args.anterior else None)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        r = {'valido': False, 'erros': [{'codigo': 'estrutura_invalida', 'onde': '/entrada',
             'mensagem': 'Não foi possível ler entradas regulares e JSON válido.'}], 'avisos': []}
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r['valido'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
