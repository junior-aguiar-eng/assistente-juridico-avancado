"""Experimento local opcional: extração atual versus Docling Parse, sem modelos ou OCR.

Este adaptador experimental não é importado pelos consumidores das skills.
A saída pública contém métricas e envelopes, nunca texto ou nomes do PDF.
"""
import argparse
from importlib.metadata import version
import json
from pathlib import Path
import time

from pecas import _sha, validar_inventario
from pecas_proposta import propor_inventario


def extrair_docling_parse(path: Path):
    # Importação tardia: pacote opcional, instalado somente no ambiente do piloto.
    from docling_parse.pdf_parser import ContentConfig, ContentLevel, DecodeConfig, DoclingPdfParser

    parser = DoclingPdfParser(loglevel='fatal')
    documento = parser.load(path_or_stream=str(path),
        decode_config=DecodeConfig(do_sanitization=True, keep_glyphs=False),
        content_config=ContentConfig(char_cells_content_level=ContentLevel.SKIP,
            word_cells_content_level=ContentLevel.SKIP,
            line_cells_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            shapes_content_level=ContentLevel.SKIP, bitmaps_content_level=ContentLevel.SKIP))
    sha = _sha(path.read_bytes())
    blocos, avisos = [], []
    for n, pagina in documento.iterate_pages():
        linhas = [c for c in pagina.textline_cells if c.text]
        if not linhas:
            avisos.append({'codigo': 'pagina_sem_texto', 'page': n})
        for c in linhas:
            blocos.append({'id': f'dp{len(blocos) + 1:06}', 'page': n, 'page_end': n,
                'text': c.text, 'tags': [], 'section': 'corpo', 'is_quote': False,
                'proveniencia': {'motor': 'docling-parse', 'rect': c.rect.model_dump(mode='json')}})
    avisos.append({'codigo': 'ordem_leitura_nao_conferida'})
    return {'schema_version': '1', 'run': {'params': {'motor': 'docling-parse', 'ocr': False,
        'sanitizacao': True, 'glyphs': False, 'linhas': True, 'palavras': False,
        'caracteres': False, 'formas': False, 'bitmaps': False}},
        'documents': [{'document_id': 'doc-' + sha[:12], 'sha256': sha,
            'extractor_versions': {'nome': 'docling-parse', 'extractor': version('docling-parse'), 'docling-core': version('docling-core')},
            'page_count': documento.number_of_pages(), 'status': 'partial', 'blocks': blocos, 'warnings': avisos}]}


def executar(path: Path, motor: str):
    inicio = time.perf_counter()
    sha = _sha(path.read_bytes())
    if motor == 'atual':
        import extract
        doc, _ = extract.extrair(path, ocr=False)
        pacote = {'schema_version': '1', 'run': {'params': {**extract.PARAMS, 'ocr': False}}, 'documents': [doc]}
    elif motor == 'docling-parse':
        pacote = extrair_docling_parse(path)
    else:
        raise ValueError('Motor desconhecido.')
    bruto = json.dumps(pacote, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    inv = propor_inventario(bruto, arquivo_sha256=sha)
    r = validar_inventario(inv, bruto, arquivo_sha256=sha)
    doc = pacote['documents'][0]
    fs = {f['id']: f for f in inv['fragmentos']}
    pecas = [{'tipo_proposto': p['tipo_proposto'], 'inicio': fs[p['inicio']]['paginas'], 'fim': fs[p['fim']]['paginas']} for p in inv['pecas']]
    return {'execucao': 'concluida', 'motor': motor, 'versoes': doc['extractor_versions'],
        'arquivo_sha256': sha, 'extracao_sha256': _sha(bruto), 'configuracao_sha256': inv['origem']['configuracao_sha256'],
        'paginas': doc['page_count'], 'blocos': len(doc['blocks']), 'caracteres': sum(len(b['text']) for b in doc['blocks']),
        'segundos': round(time.perf_counter() - inicio, 4), 'contrato_valido': r['valido'],
        'pecas': pecas, 'todas_conferencias_propostas': all(p['tipo']['estado'] == p['limites']['estado'] == 'proposto' for p in inv['pecas']),
        'pendencias': sorted({p['codigo'] for p in inv['pendencias']}), 'avisos_extracao': len(doc.get('warnings', [])),
        'limites': ['Sem OCR ou modelos de layout.', 'Título é sinal heurístico, sem confirmação de autoria ou natureza.',
                   'Corpus de desenvolvimento; não estima precisão em processos novos.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--motor', choices=('atual', 'docling-parse'), required=True)
    p.add_argument('--original', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.original.is_symlink() or not args.original.is_file() or args.original.stat().st_size > 60 * 1024 * 1024:
            raise ValueError('Original indisponível.')
        r = executar(args.original, args.motor)
    except ImportError:
        r = {'execucao': 'nao_executada', 'motor': args.motor, 'motivo': 'Dependência opcional ausente.'}
    except (OSError, ValueError, TypeError, AttributeError):
        r = {'execucao': 'falhou', 'motor': args.motor, 'motivo': 'Extração/proposta incompatível; consultar fonte local sem divulgar seu texto.'}
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r['execucao'] == 'concluida' and r['contrato_valido'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
