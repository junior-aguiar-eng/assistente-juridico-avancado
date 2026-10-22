"""Diagnóstico local de OCR: métricas e amostras, sem divulgar transcrição do original."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import unicodedata

import ocr


def _normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD',texto).casefold() if c.isalnum() and not unicodedata.combining(c))


def avaliar_amostras(resultados: dict, gabarito: dict | None, *, arquivo_sha256: str) -> dict:
    r={'total':0,'acertos':0,'conferencia_humana_da_amostra':False,'uso_material_liberado':False,'correspondencias':[]}
    if gabarito is None:
        return r
    if not isinstance(gabarito,dict) or gabarito.get('arquivo_sha256') != arquivo_sha256:
        raise ValueError('Gabarito incompatível com original.')
    amostras=gabarito.get('amostras')
    conf=gabarito.get('conferencia',{})
    if (not isinstance(amostras,list) or not amostras or not isinstance(conf,dict)
            or conf.get('estado') not in ('proposto','conferido')):
        raise ValueError('Gabarito sem amostras/estado compatíveis.')
    ids=set()
    for a in amostras:
        if (not isinstance(a,dict) or not isinstance(a.get('id'),str) or not a['id'] or a['id'] in ids
                or type(a.get('pagina')) is not int or a['pagina'] < 1
                or not isinstance(a.get('trecho'),str) or not _normalizar(a['trecho'])):
            raise ValueError('Amostra incompatível.')
        ids.add(a['id'])
        texto=' '.join(l['text'] for l in resultados.get(a['pagina'],{}).get('linhas',[]))
        presente=_normalizar(a['trecho']) in _normalizar(texto)
        r['correspondencias'].append({'id':a['id'],'pagina':a['pagina'],'presente':presente})
        r['total']+=1; r['acertos']+=int(presente)
    r['conferencia_humana_da_amostra']=conf.get('estado')=='conferido' and conf.get('ator_tipo')=='humano'
    return r


def diagnosticar(original: Path, *, perfil='padrao', dpi=ocr.DPI, gabarito=None):
    import pdfplumber
    inicio=time.perf_counter()
    if original.is_symlink() or not original.is_file() or original.stat().st_size > 60*1024*1024:
        raise ValueError('Original indisponível.')
    sha=hashlib.sha256(original.read_bytes()).hexdigest()
    cfg=ocr.configuracao(perfil); cfg['dpi']=dpi
    exe=ocr.localizar_tesseract()
    if not exe: return {'execucao':'nao_executada','motivo':'Tesseract ausente.'}
    lang,aviso=ocr.escolher_idioma(exe)
    if not lang: return {'execucao':'nao_executada','motivo':'Idioma utilizável ausente.'}
    with pdfplumber.open(original) as pdf: total=len(pdf.pages)
    if gabarito and any(a.get('pagina',0)>total for a in gabarito.get('amostras',[])):
        raise ValueError('Página do gabarito fora do original.')
    resultados=ocr.ler_paginas(exe,original,list(range(1,total+1)),lang,perfil=perfil,dpi=dpi)
    amostra=avaliar_amostras(resultados,gabarito,arquivo_sha256=sha)
    if sha != hashlib.sha256(original.read_bytes()).hexdigest():
        raise ValueError('Original mudou durante o diagnóstico.')
    return {'execucao':'concluida','arquivo_sha256':sha,'configuracao':cfg,
        'idioma_degradado':bool(aviso),'segundos':round(time.perf_counter()-inicio,4),
        'status_leitura':'partial' if any(r['linhas'] for r in resultados.values()) else 'no_text',
        'paginas':[{'pagina':n,'confianca':r['confianca'],'palavras':r['palavras'],
                    'palavras_baixa_confianca':r['palavras_baixa_confianca'],'palavras_descartadas':r['palavras_descartadas'],
                    'linhas':len(r['linhas']),'raster':r['raster']} for n,r in resultados.items()],
        'amostra':amostra,'limites':['Correspondência normalizada de trechos curtos não mede exatidão integral, acentos ou pontuação.',
            'Confiança do motor não é probabilidade de acerto nem aprovação humana.',
            'Nomes, números, datas e mérito exigem conferência própria.']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,required=True)
    parser.add_argument('--gabarito',type=Path)
    parser.add_argument('--perfil',choices=ocr.PERFIS,default='padrao')
    parser.add_argument('--dpi',type=float,default=ocr.DPI)
    args=parser.parse_args(argv)
    try:
        gabarito=json.loads(args.gabarito.read_text(encoding='utf-8')) if args.gabarito else None
        resultado=diagnosticar(args.original,perfil=args.perfil,dpi=args.dpi,gabarito=gabarito)
    except Exception:  # fronteira pública: exceções de parsers podem conter dados do PDF
        resultado={'execucao':'falhou','motivo':'Entradas, gabarito ou OCR incompatíveis; conteúdo privado não divulgado.'}
    print(json.dumps(resultado,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if resultado['execucao']=='concluida' else 1


if __name__=='__main__':
    raise SystemExit(main())
