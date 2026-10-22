"""ORG-04: usos de inventários artificiais, sem documentos ou revisores reais."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))
import auditar
import cronologia
import validate


def gravar(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    return p


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def conferir_simulado(inv):
    for p in inv['pecas']:
        for dim in ('limites', 'tipo'):
            eid = 'sim-' + p['id'] + '-' + dim
            inv['eventos'].append({'id': eid, 'instante': '2026-10-22T01:00:00Z',
                'ator': {'tipo': 'humano', 'identificador': 'Fixture ficticia, sem revisao real'},
                'acao': 'conferir_' + dim, 'alvos': [p['id']], 'motivo': 'Simulacao de teste'})
            p[dim] = {'estado': 'conferido', 'evento_id': eid}


def caso(tmp, cid='CT01'):
    c = next(c for c in json.loads((RAIZ / 'tests/casos/pecas_contrato/exemplos.json').read_text(encoding='utf-8'))['exemplos'] if c['id'] == cid)
    inv, ext = copy.deepcopy(c['inventario']), json.loads(c['extracao_json_utf8'])
    original = tmp / 'original.pdf'
    original.write_bytes(c['origem_simulada_utf8'].encode('utf-8'))
    ext['documents'][0]['path'] = str(original)
    conferir_simulado(inv)
    p = SimpleNamespace(inv=inv, ext=ext, original=original, ip=tmp/'pecas.json', ep=tmp/'extracao.json', fp=tmp/'facts.json')
    salvar(p)
    p.facts = fatos(p)
    gravar(p.fp, p.facts)
    return p


def salvar(p):
    gravar(p.ep, p.ext)
    p.inv['origem']['extracao_sha256'] = sha(p.ep)
    gravar(p.ip, p.inv)


def fonte(p, fid='f001'):
    f = next(f for f in p.inv['fragmentos'] if f['id'] == fid)
    b = next(b for b in p.ext['documents'][0]['blocks'] if b['id'] == f['block_id'])
    return {'document_id': p.inv['origem']['document_id'], 'block_id': b['id'], 'locator': b['locator'],
        'excerpt': b['text'][f['inicio']:f['fim']],
        'peca': {'inventario_id': p.inv['inventario_id'], 'inventario_sha256': sha(p.ip),
                 'piece_id': f['destino'].get('piece_id'), 'fragmentos': [fid]}}


def fatos(p, fid='f001'):
    return {'schema_version': '1', 'facts': [{'id': 'fato-1', 'kind': 'alegacao',
        'text': 'A parte apresenta a narrativa.', 'alleged_by': 'parte simulada', 'source': fonte(p, fid)}]}


def contexto(p, **kw):
    assert (RAIZ/'scripts/pecas_uso.py').is_file(), 'Falta integracao de inventario por uso'
    return importlib.import_module('pecas_uso').carregar_contexto([p.ep], [(p.ip, p.original)], **kw)


def validar(p, obj=None, modo='fundamentada', **kw):
    return validate.validar_facts(obj or p.facts, validate.carregar_extracoes([p.ep]), pecas=contexto(p, **kw), modo=modo)


def codigos(r):
    return {e['codigo'] for e in r.erros}


def test_referencia_explicita_sem_contexto_nao_e_ignorada(tmp_path):
    p = caso(tmp_path)
    r = validate.validar_facts(p.facts, validate.carregar_extracoes([p.ep]))
    assert 'pecas_inventario_ausente' in codigos(r)


def test_uso_conferido_preserva_controle_positivo(tmp_path):
    p = caso(tmp_path)
    assert not validar(p).erros


@pytest.mark.parametrize('alteracao', ['inventario', 'hash', 'peca', 'fragmento', 'bloco', 'trecho', 'pagina', 'secao', 'tipo_campo'])
def test_rejeita_referencia_incompativel_em_qualquer_modo(tmp_path, alteracao):
    p = caso(tmp_path)
    s = p.facts['facts'][0]['source']; ref = s['peca']
    if alteracao == 'inventario': ref['inventario_id'] = 'inexistente'
    elif alteracao == 'hash': ref['inventario_sha256'] = '0'*64
    elif alteracao == 'peca': ref['piece_id'] = 'p002'
    elif alteracao == 'fragmento': ref['fragmentos'] = ['f002']
    elif alteracao == 'bloco': s['block_id'] = 'b0002'
    elif alteracao == 'trecho': s['excerpt'] = 'Texto artificial inexistente no fragmento'
    elif alteracao == 'pagina': s['locator'] = 'p.99'
    elif alteracao == 'secao': ref['secao_id'] = 'ausente'
    else: ref['fragmentos'] = 'f001'
    assert validar(p, modo='analise').erros


def test_duas_pecas_no_mesmo_bloco_nao_compartilham_o_trecho(tmp_path):
    p = caso(tmp_path, 'CT02')
    assert not validar(p).erros
    p.facts['facts'][0]['source']['excerpt'] = fonte(p, 'f002')['excerpt']
    assert 'pecas_trecho_incompativel' in codigos(validar(p))


@pytest.mark.parametrize('dim', ['limites', 'tipo'])
def test_proposta_aparece_na_analise_e_bloqueia_uso_fundamentado(tmp_path, dim):
    p = caso(tmp_path)
    p.inv['pecas'][0][dim] = {'estado': 'proposto', 'evento_id': None}
    salvar(p); p.facts = fatos(p)
    r = validar(p, modo='analise')
    assert not r.erros and any(a['codigo'].startswith('pecas_') for a in r.avisos)
    assert validar(p).erros


def test_pendencia_material_de_outra_peca_nao_bloqueia_o_uso_conferido(tmp_path):
    p = caso(tmp_path)
    p.inv['pendencias'].append({'id':'pend-outra', 'codigo':'outro', 'referencias':['p002'],
                               'mensagem':'Pendencia artificial em outra peca', 'material':True})
    salvar(p); p.facts = fatos(p)
    assert not validar(p).erros
    assert validar(p, fatos(p, 'f002')).erros


def test_ocr_nao_e_promovido_por_conferencia_de_limites_ou_material_false(tmp_path):
    p = caso(tmp_path)
    p.ext['documents'][0]['status'] = 'partial'
    p.ext['documents'][0]['blocks'][0]['tags'] = ['ocr']
    p.ext['documents'][0]['warnings'] = [{'codigo':'ocr_aplicado', 'page':1}]
    p.inv['paginas'][0]['leitura'] = 'ocr_parcial'
    p.inv['pendencias'].append({'id':'pend-ocr', 'codigo':'leitura_insuficiente','referencias':['f001'],
                               'mensagem':'OCR artificial', 'material':False})
    salvar(p); p.facts = fatos(p)
    assert not validar(p, modo='analise').erros
    assert 'pecas_leitura_insuficiente' in codigos(validar(p))
    assert not validar(p, fatos(p, 'f002')).erros


def test_atribuicao_ambigua_nao_e_resolvida_pelo_inventario(tmp_path):
    p = caso(tmp_path)
    p.ext['documents'][0]['blocks'][0]['tags'] = ['atribuicao_ambigua']
    salvar(p); p.facts = fatos(p)
    assert validar(p).erros


def test_nao_aceita_original_ou_extracao_adulterados(tmp_path):
    p = caso(tmp_path)
    p.original.write_bytes(b'outro original')
    assert contexto(p).erros
    p = caso(tmp_path)
    p.ep.write_bytes(p.ep.read_bytes()+b' ')
    assert contexto(p).erros


def test_troca_de_revisao_nao_remapeia_referencia_antiga(tmp_path):
    p = caso(tmp_path)
    p.ip.write_bytes(p.ip.read_bytes()+b'\n')
    assert 'pecas_referencia_incompativel' in codigos(validar(p))


def test_exigencia_explicita_recusa_omissao_da_referencia(tmp_path):
    p = caso(tmp_path); del p.facts['facts'][0]['source']['peca']
    assert validar(p, exigir=True).erros


def test_fontes_adicionais_tambem_passam_pelo_gate(tmp_path):
    p = caso(tmp_path)
    p.facts['facts'][0]['other_sources'] = [fonte(p,'f002')]
    p.facts['facts'][0]['other_sources'][0]['peca']['piece_id'] = 'p001'
    assert validar(p).erros


def test_claim_supported_nao_passa_com_peca_proposta(tmp_path):
    p = caso(tmp_path)
    p.inv['pecas'][0]['limites'] = {'estado':'proposto','evento_id':None}
    salvar(p)
    s = fonte(p); pin = {k:s.pop(k) for k in ('locator','excerpt')}
    s.update(source_id='s1', origin='oficial',access='lida',url='https://example.invalid/fonte',
             retrieved_at='2026-10-22',content_hash=sha(p.original),text_scope='outro',pinpoint=pin)
    cl = {'schema_version':'1','claims':[{'id':'c1','proposition':'Proposicao artificial',
          'tipo':'outro','status':'supported','existence':'confirmada','quote_status':'conferida','sources':[s]}]}
    r = validate.validar_claims(cl, validate.carregar_extracoes([p.ep]), pecas=contexto(p))
    assert any(e['codigo'].startswith('pecas_') for e in r.erros)


def test_cronologia_preserva_referencia_e_recusa_perda_do_contexto(tmp_path):
    p = caso(tmp_path); tj, md = tmp_path/'timeline.json', tmp_path/'cronologia.md'
    cronologia.gerar(p.fp,tj,md,extracoes=[p.ep],pecas=[(p.ip,p.original)])
    t = json.loads(tj.read_text(encoding='utf-8'))
    assert t['sem_data'][0]['fonte']['peca'] == p.facts['facts'][0]['source']['peca']
    assert t['inventarios_pecas'][0]['sha256'] == sha(p.ip)
    assert not cronologia.conferir(p.fp,tj)['atualizada']
    assert cronologia.conferir(p.fp,tj,pecas_contexto=contexto(p))['atualizada']
    p.ip.write_bytes(p.ip.read_bytes()+b'\n')
    assert not cronologia.conferir(p.fp,tj,pecas_contexto=contexto(p))['atualizada']


def test_auditoria_vincula_insumos_e_detecta_adulteracao_posterior(tmp_path):
    p = caso(tmp_path)
    q = auditar.auditar(p.fp,None,[p.ep],base=tmp_path,pecas=[(p.ip,p.original)])
    gate = next(g for g in q['gates'] if g['id']=='G16_inventario_pecas')
    assert gate['resultado']=='aprovado'
    qp = gravar(tmp_path/'qc.json',q)
    p.ip.write_bytes(p.ip.read_bytes()+b'\n')
    assert 'pecas.json' in auditar.status(qp)['alterados']


@pytest.mark.parametrize('modo,esperado',[('analise','alerta'),('fundamentada','reprovado')])
def test_auditoria_recusa_uso_pendente_sem_mudar_gates_legados(tmp_path,modo,esperado):
    p=caso(tmp_path); p.inv['pecas'][0]['limites']={'estado':'proposto','evento_id':None}
    salvar(p); p.facts=fatos(p); gravar(p.fp,p.facts)
    q=auditar.auditar(p.fp,None,[p.ep],modo,base=tmp_path,pecas=[(p.ip,p.original)])
    assert next(g for g in q['gates'] if g['id']=='G16_inventario_pecas')['resultado']==esperado
    assert any(x['origem']=='pecas' for x in q['pendencias'])


def test_legacy_sem_referencia_ou_inventario_continua_valido(tmp_path):
    p=caso(tmp_path); del p.facts['facts'][0]['source']['peca']; gravar(p.fp,p.facts)
    assert not validate.validar_facts(p.facts,validate.carregar_extracoes([p.ep])).erros
    q=auditar.auditar(p.fp,None,[p.ep],base=tmp_path)
    assert not any(g['id']=='G16_inventario_pecas' for g in q['gates'])


def test_clis_e_fluxo_integrado_sem_editar_originais(tmp_path):
    p=caso(tmp_path); antes={x:sha(x) for x in (p.ip,p.ep,p.original,p.fp)}
    def cli(script,*args):
        r=subprocess.run([sys.executable,'-B',str(RAIZ/'scripts'/script),*map(str,args)],cwd=tmp_path,capture_output=True)
        assert r.returncode==0,r.stderr.decode('utf-8',errors='replace')+r.stdout.decode('utf-8',errors='replace')
        return json.loads(r.stdout.decode('utf-8'))
    flags=['--extracoes',p.ep,'--pecas',p.ip,p.original,'--exigir-pecas']
    tri=cli('triagem.py','pecas',*flags)
    assert tri['valido'] and tri['inventarios']
    assert cli('validate.py',p.fp,*flags,'--modo','fundamentada')['valido']
    tj,md,qp=tmp_path/'timeline.json',tmp_path/'timeline.md',tmp_path/'qc.json'
    cli('cronologia.py','gerar','--facts',p.fp,*flags,'--saida-json',tj,'--saida-md',md)
    cli('auditar.py','auditar','--facts',p.fp,*flags,'--timeline',tj,'--tipo-entrega','interna','--saida',qp)
    assert cli('auditar.py','status',qp)['estado_tecnico']=='revisao_pronta'
    assert {x:sha(x) for x in antes}==antes


def test_reticencias_sozinhas_nao_sao_trecho_conferivel(tmp_path):
    p=caso(tmp_path); p.facts['facts'][0]['source']['excerpt']='[...]'
    assert 'pecas_trecho_incompativel' in codigos(validar(p))


def test_revisao_posterior_exige_bytes_anteriores_e_entra_no_qc(tmp_path):
    p=caso(tmp_path); anterior=tmp_path/'pecas.rev-0001.json'
    anterior.write_bytes(p.ip.read_bytes())
    p.inv.update(revisao=2,anterior_sha256=sha(anterior))
    p.inv['eventos'].append({'id':'ev-rev2','instante':'2026-10-22T02:00:00Z',
        'ator':{'tipo':'sistema','identificador':'fixture'},'acao':'corrigir',
        'alvos':[p.inv['inventario_id']],'motivo':'Revisao artificial sem alteracao material'})
    salvar(p); p.facts=fatos(p); gravar(p.fp,p.facts)
    assert contexto(p).erros
    assert not validar(p,anteriores=[anterior]).erros
    q=auditar.auditar(p.fp,None,[p.ep],base=tmp_path,pecas=[(p.ip,p.original)],pecas_anteriores=[anterior])
    assert any(a['caminho']=='pecas.rev-0001.json' for a in q['artefatos'])


def test_secao_precisa_pertencer_a_peca_e_estar_conferida(tmp_path):
    p=caso(tmp_path)
    p.inv['secoes']=[{'id':'sec-1','piece_id':'p001','tipo_proposto':'fundamentacao',
                     'fragmentos':['f001'],'conferencia':{'estado':'proposto','evento_id':None}}]
    salvar(p); p.facts=fatos(p); p.facts['facts'][0]['source']['peca']['secao_id']='sec-1'
    assert validar(p).erros
    assert not validar(p,modo='analise').erros
    p.inv['eventos'].append({'id':'ev-sec','instante':'2026-10-22T03:00:00Z',
        'ator':{'tipo':'humano','identificador':'Fixture ficticia'},'acao':'conferir_secao',
        'alvos':['sec-1'],'motivo':'Conferencia simulada, sem valor humano real'})
    p.inv['secoes'][0]['conferencia']={'estado':'conferido','evento_id':'ev-sec'}
    salvar(p); p.facts=fatos(p); p.facts['facts'][0]['source']['peca']['secao_id']='sec-1'
    assert not validar(p).erros


def test_cronologia_de_trabalho_exibe_pendencias_e_fundamentada_nao_grava(tmp_path):
    p=caso(tmp_path); p.inv['pecas'][0]['limites']={'estado':'proposto','evento_id':None}
    salvar(p); p.facts=fatos(p); gravar(p.fp,p.facts)
    tj,md=tmp_path/'t.json',tmp_path/'t.md'
    cronologia.gerar(p.fp,tj,md,extracoes=[p.ep],pecas=[(p.ip,p.original)])
    assert json.loads(tj.read_text(encoding='utf-8'))['pendencias_pecas']
    assert 'Pendências das peças utilizadas' in md.read_text(encoding='utf-8')
    assert cronologia.conferir(p.fp,tj,pecas_contexto=contexto(p))['atualizada']
    with pytest.raises(ValueError):
        cronologia.gerar(p.fp,tmp_path/'bloqueado.json',tmp_path/'bloqueado.md',extracoes=[p.ep],
                         pecas=[(p.ip,p.original)],modo='fundamentada')
    assert not (tmp_path/'bloqueado.json').exists()


def test_extracoes_com_document_id_ambiguo_sao_recusadas(tmp_path):
    p=caso(tmp_path); outro=copy.deepcopy(p.ext); outro['run']['params']['outro']=True
    ep2=gravar(tmp_path/'outra-extracao.json',outro)
    mod=importlib.import_module('pecas_uso')
    assert mod.carregar_contexto([p.ep,ep2],[(p.ip,p.original)]).erros


def test_fonte_nao_lida_nao_pode_declarar_vinculo_de_peca_ignorado(tmp_path):
    p=caso(tmp_path)
    obj={'schema_version':'1','claims':[{'id':'c1','proposition':'Ainda nao conferida',
        'status':'unverified','existence':'nao_confirmada','sources':[{
        'source_id':'s1','origin':'oficial','access':'nao_acessada','peca':{'incorreta':True}}]}]}
    for ctx in (None,contexto(p)):
        r=validate.validar_claims(obj,validate.carregar_extracoes([p.ep]),pecas=ctx)
        assert 'pecas_sem_leitura' in codigos(r)


def test_pendencia_material_de_secao_segue_os_fragmentos_sem_secao_id(tmp_path):
    p=caso(tmp_path)
    p.inv['secoes']=[{'id':'sec-1','piece_id':'p001','tipo_proposto':'fundamentacao',
                     'fragmentos':['f001'],'conferencia':{'estado':'proposto','evento_id':None}}]
    p.inv['pendencias'].append({'id':'pend-secao','codigo':'outro','referencias':['sec-1'],
                               'mensagem':'Pendencia artificial no trecho','material':True})
    salvar(p); p.facts=fatos(p)
    assert 'pecas_outro' in codigos(validar(p))


def test_blocos_com_autorias_distintas_nao_sao_fundamento_sem_ressalva(tmp_path):
    p=caso(tmp_path); p.ext['documents'][0]['blocks'][1]['is_quote']=True
    salvar(p); p.facts=fatos(p,'f002')
    s=p.facts['facts'][0]['source']; s.pop('block_id')
    s['peca']['fragmentos']=['f002','f003']
    s['excerpt']=' '.join(b['text'] for b in p.ext['documents'][0]['blocks'][1:3])
    assert 'pecas_atribuicao_ambigua' in codigos(validar(p))


def test_fronteira_incerta_em_outro_fragmento_afeta_toda_a_peca(tmp_path):
    p=caso(tmp_path)
    p.inv['pendencias'].append({'id':'pend-fim','codigo':'limite_incerto','referencias':['f004'],
                               'mensagem':'Fim da peca ainda incerto','material':True})
    salvar(p); p.facts=fatos(p,'f002')
    assert 'pecas_limite_incerto' in codigos(validar(p))


def test_pagina_e_trecho_devem_coincidir_na_mesma_ocorrencia_da_peca(tmp_path):
    p=caso(tmp_path)
    texto='Texto repetido comum da decisao.'
    bs=p.ext['documents'][0]['blocks']
    bs[0]['text']=bs[2]['text']=texto
    bs[1].update(page=1,page_end=1,locator='p.1')
    for f in p.inv['fragmentos']:
        f['fim']=len(next(b['text'] for b in bs if b['id']==f['block_id']))
    p.inv['fragmentos'][1]['paginas'].update(inicio=1,fim=1)
    salvar(p); p.facts=fatos(p,'f002')
    s=p.facts['facts'][0]['source']; s.pop('block_id')
    s['peca']['fragmentos']=['f002','f003']; s.update(excerpt=texto,locator='p.1')
    assert 'pecas_localizador_incompativel' in codigos(validar(p))
    s['locator']='p.2'
    assert not validar(p).erros


def test_markdown_sem_data_preserva_outras_fontes_com_peca(tmp_path):
    p=caso(tmp_path)
    p.facts['facts'][0].update(kind='lacuna',other_sources=[fonte(p)])
    p.facts['facts'][0].pop('source'); gravar(p.fp,p.facts)
    tj,md=tmp_path/'t.json',tmp_path/'t.md'
    cronologia.gerar(p.fp,tj,md,extracoes=[p.ep],pecas=[(p.ip,p.original)])
    assert 'peça p001' in md.read_text(encoding='utf-8')


def test_reticencias_podem_terminar_na_ocorrencia_posterior_da_pagina_citada(tmp_path):
    p=caso(tmp_path); bs=p.ext['documents'][0]['blocks']
    bs[1].update(text='Comeco aqui final aqui.',page=1,page_end=1,locator='p.1')
    bs[2]['text']='final aqui.'
    for f in p.inv['fragmentos']:
        f['fim']=len(next(b['text'] for b in bs if b['id']==f['block_id']))
    p.inv['fragmentos'][1]['paginas'].update(inicio=1,fim=1)
    salvar(p); p.facts=fatos(p,'f002')
    s=p.facts['facts'][0]['source']; s.pop('block_id')
    s['peca']['fragmentos']=['f002','f003']
    s.update(excerpt='Comeco aqui [...] final aqui.',locator='p.1-2')
    assert not validar(p).erros


def test_fronteira_referenciada_por_secao_afeta_a_peca_inteira(tmp_path):
    p=caso(tmp_path)
    p.inv['secoes']=[{'id':'sec-fim','piece_id':'p002','tipo_proposto':'dispositivo',
                     'fragmentos':['f004'],'conferencia':{'estado':'proposto','evento_id':None}}]
    p.inv['pendencias'].append({'id':'pend-fim','codigo':'limite_incerto','referencias':['sec-fim'],
                               'mensagem':'Fim ainda incerto','material':True})
    salvar(p); p.facts=fatos(p,'f002')
    assert 'pecas_limite_incerto' in codigos(validar(p))
