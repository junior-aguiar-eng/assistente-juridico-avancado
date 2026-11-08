"""EV-02: contagens e vínculos técnicos não substituem o julgamento jurídico."""
import copy
import importlib
from pathlib import Path
import sys

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'scripts'))


def modulo():
    assert (RAIZ / 'scripts/avaliar_analise.py').is_file(), 'Falta avaliador EV-02'
    return importlib.import_module('avaliar_analise')


def dados():
    p = dict(schema_version='1', execucao_id='run-1', caso_id='c1',
             processo_id='TJ:0001-23', familia_id='f1', grupo='desenvolvimento',
             serie_id='luna-high', modelo_id='modelo-sintetico', config_sha256='a'*64,
             prompt_sha256='b'*64, produto_sha256='c'*64,
             experimento='semantico', variante='A', repeticao=1, condicao='nativa',
             estado='concluida', saida_sha256='d'*64, entradas_sha256={'e1': 'e'*64},
             itens=[{'id': 'p1', 'tipo': 'afirmacao', 'texto': 'Questão sintética'}],
             operacao={'custo_usd': 0.01, 'latencia_segundos': 2, 'chamadas': 1})
    g = dict(schema_version='1', caso_id='c1', processo_id='TJ:0001-23', familia_id='f1',
             grupo='desenvolvimento', entradas_sha256={'e1': 'e'*64},
             revisao={'status': 'conferido', 'revisor': 'Revisor sintético', 'data': '2026-10-22'},
             itens=[{'id': 'g1', 'classe': 'questao', 'central': True, 'respondivel': True,
                     'descricao': 'Questão sintética',
                     'fontes': [{'artifact_id': 'e1', 'localizador': 'p.1'}]}],
             rubrica={d: {'aplicavel': True, 'motivo': ''} for d in
                      ('conexao', 'contraposicoes', 'consequencias', 'limites')})
    j = dict(schema_version='1', execucao_id='run-1', status='conferido',
             revisor='Revisor sintético', data='2026-10-22',
             correspondencias=[{'predicao_id': 'p1', 'gabarito_id': 'g1', 'resultado': 'correto'}],
             profundidade={d: 3 for d in g['rubrica']}, erros=[],
             revisao_ativa_segundos=60, perguntas_triviais=2,
             referencias={'resolvidas': 1, 'total': 1})
    return p, g, j


def avaliar(p=None, g=None, j=None):
    pp, gg, jj = dados()
    p, g, j = p or pp, g or gg, j or jj
    j = copy.deepcopy(j)
    j['predicao_sha256'] = modulo().sha_objeto(p)
    j['gabarito_sha256'] = modulo().sha_objeto(g)
    return modulo().avaliar_caso(p, g, j)


def test_contagem_conhecida_e_pureza():
    p, g, j = dados(); antes = copy.deepcopy((p, g, j))
    r = avaliar(p, g, j)
    assert r['avaliacao'] == 'julgada'
    assert r['metricas']['recall'] == {'numerador': 1, 'denominador': 1, 'valor': 1}
    assert r['metricas']['precisao']['valor'] == 1
    assert r['metricas']['centrais_tratados']['valor'] == 1
    assert (p, g, j) == antes


def test_nao_conta_paginas_como_processos():
    p, g, j = dados(); resultados = [avaliar(p, g, j)]
    p['execucao_id'] = j['execucao_id'] = 'run-2'; p['repeticao'] = 2
    resultados.append(avaliar(p, g, j))
    a = modulo().agregar_resultados(resultados)[0]
    assert a['execucoes'] == 2 and a['processos'] == 1 and a['familias'] == 1
    assert a['recall_macro']['valor'] == 1


@pytest.mark.parametrize('estado', ['abstencao', 'falha', 'timeout', 'invalida', 'limite', 'nao_executada'])
def test_abstencao_e_falha_entram_no_denominador(estado):
    p, g, j = dados(); rs = [avaliar(p, g, j)]
    p.update(execucao_id='run-2', repeticao=2, estado=estado, itens=[])
    j.update(execucao_id='run-2', correspondencias=[])
    rs.append(avaliar(p, g, j))
    a = modulo().agregar_resultados(rs)[0]
    assert a['execucoes'] == 2
    assert a['estados'][estado] == 1
    assert a['recall_micro']['valor'] == 0.5
    assert a['recall_macro']['valor'] == 0.5
    assert a['cobertura_avaliacao']['denominador'] == 2


def test_media_macro_e_por_processo_nao_por_repeticao():
    p, g, j = dados(); rs = [avaliar(p, g, j)]
    p.update(execucao_id='run-2', repeticao=2); j['execucao_id'] = 'run-2'
    rs.append(avaliar(p, g, j))
    p.update(execucao_id='run-3', caso_id='c2', processo_id='outro', familia_id='f2', repeticao=1, itens=[], estado='falha')
    g.update(caso_id='c2', processo_id='outro', familia_id='f2')
    j.update(execucao_id='run-3', correspondencias=[])
    rs.append(avaliar(p, g, j))
    a = modulo().agregar_resultados(rs)[0]
    assert a['recall_macro']['valor'] == 0.5
    assert a['recall_micro']['valor'] == pytest.approx(2/3)


def test_gabarito_pendente_nao_vira_nota_ou_aprovacao():
    p, g, j = dados(); g['revisao'] = {'status': 'pendente', 'revisor': '', 'data': None}
    r = avaliar(p, g, j)
    assert r['avaliacao'] == 'pendente' and r['metricas'] is None
    a = modulo().agregar_resultados([r])[0]
    assert a['cobertura_avaliacao']['valor'] == 0
    assert a['recall_macro']['valor'] is None
    assert a['execucoes'] == 1


def test_julgamento_pendente_nao_vira_nota():
    p, g, j = dados(); j = {'status': 'pendente'}
    assert avaliar(p, g, j)['avaliacao'] == 'pendente'


@pytest.mark.parametrize('campo', ['predicao_sha256', 'gabarito_sha256'])
def test_julgamento_antigo_nao_avalia_bytes_logicos_novos(campo):
    p, g, j = dados()
    j.update(predicao_sha256=modulo().sha_objeto(p), gabarito_sha256=modulo().sha_objeto(g))
    j[campo] = 'f'*64
    with pytest.raises(ValueError, match='julgamento_desatualizado'):
        modulo().avaliar_caso(p, g, j)


@pytest.mark.parametrize('campo', ['processo_id', 'familia_id', 'caso_id', 'grupo', 'entradas_sha256'])
def test_identidade_ou_entradas_divergentes_recusadas(campo):
    p, g, j = dados(); g[campo] = {'e1': 'f'*64} if campo == 'entradas_sha256' else 'outro'
    with pytest.raises(ValueError): avaliar(p, g, j)


def test_na_exige_motivo_e_nao_remove_execucao():
    p, g, j = dados(); g['rubrica']['consequencias'] = {'aplicavel': False, 'motivo': 'Não há alternativa no insumo sintético'}
    j['profundidade']['consequencias'] = None
    r = avaliar(p, g, j); a = modulo().agregar_resultados([r])[0]
    assert a['profundidade']['consequencias']['denominador'] == 0
    assert a['execucoes'] == 1
    g['rubrica']['consequencias']['motivo'] = ''
    with pytest.raises(ValueError): avaliar(p, g, j)


def test_abstencao_correta_separa_resposta_de_tratamento():
    p, g, j = dados(); g['itens'][0]['respondivel'] = False
    p['itens'][0]['tipo'] = 'limitacao'
    j['correspondencias'][0]['resultado'] = 'abstencao_correta'
    r = avaliar(p, g, j)
    assert r['metricas']['recall']['valor'] == 0
    assert r['metricas']['centrais_tratados']['valor'] == 1
    assert r['metricas']['abstencoes_corretas'] == 1
    assert r['metricas']['precisao']['valor'] is None
    g['itens'][0]['respondivel'] = True
    with pytest.raises(ValueError): avaliar(p, g, j)


@pytest.mark.parametrize('mudanca', ['duplicada', 'desconhecida', 'omitida', 'nota', 'nan', 'booleano', 'referencias'])
def test_julgamento_incoerente_recusado(mudanca):
    p, g, j = dados()
    if mudanca == 'duplicada': j['correspondencias'] *= 2
    if mudanca == 'desconhecida': j['correspondencias'][0]['gabarito_id'] = 'fantasma'
    if mudanca == 'omitida': j['correspondencias'] = []
    if mudanca == 'nota': j['profundidade']['conexao'] = 5
    if mudanca == 'nan': j['revisao_ativa_segundos'] = float('nan')
    if mudanca == 'booleano': j['profundidade']['conexao'] = True
    if mudanca == 'referencias': j['referencias']['resolvidas'] = 2
    with pytest.raises(ValueError): avaliar(p, g, j)


def test_item_extra_penaliza_precisao():
    p, g, j = dados(); p['itens'].append({'id': 'p2', 'tipo': 'afirmacao', 'texto': 'Excesso'})
    j['correspondencias'].append({'predicao_id': 'p2', 'gabarito_id': None, 'resultado': 'incorreto'})
    assert avaliar(p, g, j)['metricas']['precisao']['valor'] == 0.5


def test_erro_critico_visivel_reprova_criterio_tambem():
    p, g, j = dados(); j['erros'] = [{'id': 'erro-1', 'critico': True, 'silencioso': False, 'motivo': 'Resultado invertido'}]
    r = avaliar(p, g, j)
    assert not r['criterios']['sem_erro_critico']
    assert r['criterios']['sem_erro_critico_silencioso']


@pytest.mark.parametrize('campo,valor', [('modelo_id','outro'), ('config_sha256','f'*64), ('experimento','ponta_a_ponta'), ('condicao','assistida')])
def test_nao_mistura_modelos_experimentos_ou_recuperacao(campo, valor):
    p, g, j = dados(); rs = [avaliar(p, g, j)]
    p.update(execucao_id='run-2'); j['execucao_id'] = 'run-2'; p[campo] = valor
    if campo in ('modelo_id','config_sha256'): p['serie_id'] = 'serie2'
    rs.append(avaliar(p, g, j))
    assert len(modulo().agregar_resultados(rs)) == 2


def test_recusa_execucao_repetida_e_serie_instavel():
    r = avaliar()
    with pytest.raises(ValueError): modulo().agregar_resultados([r, r])
    p, g, j = dados(); p.update(execucao_id='run-2', modelo_id='outro'); j['execucao_id'] = 'run-2'
    with pytest.raises(ValueError, match='serie_instavel'):
        modulo().agregar_resultados([r, avaliar(p, g, j)])


@pytest.mark.parametrize('mudanca', ['prompt', 'entradas', 'gabarito'])
def test_comparacao_semantica_recusa_contexto_variavel(mudanca):
    p, g, j = dados(); rs = [avaliar(p, g, j)]
    p.update(execucao_id='run-b', variante='B'); j['execucao_id'] = 'run-b'
    if mudanca == 'prompt': p['prompt_sha256'] = 'f'*64
    if mudanca == 'entradas': p['entradas_sha256'] = g['entradas_sha256'] = {'e1':'f'*64}
    if mudanca == 'gabarito': g['itens'][0]['descricao'] = 'Referência revisada depois de A'
    rs.append(avaliar(p, g, j))
    with pytest.raises(ValueError): modulo().agregar_resultados(rs)


@pytest.mark.parametrize('objeto,campo,valor', [('p','itens',[None]), ('j','profundidade',None), ('g','rubrica',[])])
def test_dado_malformado_recusado_com_erro_de_dominio(objeto,campo,valor):
    p,g,j=dados(); {'p':p,'g':g,'j':j}[objeto][campo]=valor
    with pytest.raises(ValueError): avaliar(p,g,j)


def caso(id='c1', grupo='desenvolvimento'):
    return dict(id=id, processo_id=id, familia_id=id, duplicata_id=id, grupo=grupo,
                tribunal='TJ-SINTETICO', modalidade='nativo', origem='origem1', paginas=16, pecas=1,
                artefatos=[{'id': id+'-o', 'tipo': 'original', 'sha256': modulo().sha_bytes(id.encode())},
                           {'id': id+'-e', 'tipo': 'extracao', 'sha256': modulo().sha_bytes((id+'-e').encode())}])


def corpus(cs):
    entradas = {a['id']: (c['id'] + ('-e' if a['tipo'] == 'extracao' else '')).encode() for c in cs for a in c['artefatos']}
    return {'schema_version': '1', 'casos': cs}, entradas


@pytest.mark.parametrize('campo', ['processo_id','familia_id','duplicata_id'])
def test_detecta_vazamento_de_processo(campo):
    a, b = caso(), caso('c2', 'reservado'); b[campo] = a[campo]
    m, e = corpus([a,b])
    with pytest.raises(ValueError, match='vazamento'): modulo().validar_corpus(m,e)


def test_detecta_processo_normalizado_e_bytes_iguais():
    a, b = caso(), caso('c2','reservado'); a['processo_id']='TJ:0001-23'; b['processo_id']='tj000123'
    m,e=corpus([a,b])
    with pytest.raises(ValueError,match='vazamento'): modulo().validar_corpus(m,e)
    b['processo_id']='diferente'; b['artefatos'][0]['sha256']=a['artefatos'][0]['sha256']; e['c2-o']=e['c1-o']
    with pytest.raises(ValueError,match='vazamento'): modulo().validar_corpus(m,e)


def test_hash_nao_confere_e_snapshot_ausente_falham():
    m,e=corpus([caso()]);e['c1-o']=b'alterado'
    with pytest.raises(ValueError,match='snapshot'): modulo().validar_corpus(m,e)
    del e['c1-o']
    with pytest.raises(ValueError,match='snapshot'): modulo().validar_corpus(m,e)


def test_corpus_insuficiente_expõe_estratos_sem_inventar_casos():
    m,e=corpus([caso()]);r=modulo().validar_corpus(m,e)
    assert r['processos']['desenvolvimento'] == 1
    assert r['processos']['reservado'] == 0
    assert not r['cobertura_planejada'] and r['lacunas']


@pytest.mark.parametrize('campo,valor', [('paginas',True),('pecas',0),('grupo','teste'),('modalidade','inventada'),('processo_id','---')])
def test_corpus_metadados_invalidos(campo,valor):
    c=caso();c[campo]=valor;m,e=corpus([c])
    with pytest.raises(ValueError): modulo().validar_corpus(m,e)


def corpus_completo():
    cs=[caso('d'+str(i)) for i in range(6)]
    for i in range(12):
        c=caso('r'+str(i),'reservado');c['pecas']=(1,5,15)[i//4]
        c['modalidade']='nativo' if i<6 else 'digitalizado' if i<9 else 'misto'
        c['tribunal']='TJ'+str(i%3);c['origem']='origem'+str(i%2)
        cs.append(c)
    return corpus(cs)


def test_cobertura_completa_e_controle_positivo():
    m,e=corpus_completo();r=modulo().validar_corpus(m,e)
    assert r['cobertura_planejada'] and not r['lacunas']


@pytest.mark.parametrize('tipo',['curada','bytes'])
def test_duplicatas_internas_nao_completam_corpus(tipo):
    m,e=corpus_completo()
    if tipo=='curada':
        for c in m['casos'][6:]: c['duplicata_id']='mesmo-conteudo'
    else:
        a,b=m['casos'][6:8]
        b['artefatos'][0]['sha256']=a['artefatos'][0]['sha256']
        e[b['artefatos'][0]['id']]=e[a['artefatos'][0]['id']]
    r=modulo().validar_corpus(m,e)
    assert not r['cobertura_planejada'] and r['lacunas']
