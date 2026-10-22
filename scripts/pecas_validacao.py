"""Invariantes do grafo, partição e leitura do contrato v1."""


def validar_grafo(inv, doc, erro, avisos, *, anteriores=None, prefixo=0):
    anteriores = anteriores or set()
    total = inv['origem']['total_paginas']
    grupos = ['fragmentos', 'pecas', 'secoes', 'eventos', 'pendencias']
    ids = [inv['inventario_id']] + [x['id'] for g in grupos for x in inv[g]]
    if len(ids) != len(set(ids)) or any(x.startswith('pagina-') for x in ids):
        erro('id_invalido', '/inventario', 'IDs repetidos ou reservados.')
    conhecidos = set(ids) | {f"pagina-{p['numero']}" for p in inv['paginas']}
    blocos = {b['id']: b for b in doc['blocks']}
    if len(blocos) != len(doc['blocks']):
        erro('id_invalido', '/extracao/blocks', 'IDs de bloco repetidos na origem.')
    ordem_bloco = {b['id']: i for i, b in enumerate(doc['blocks'])}
    fs = {f['id']: f for f in inv['fragmentos']}
    ps = {p['id']: p for p in inv['pecas']}
    eventos = {e['id']: e for e in inv['eventos']}
    posicoes_evento = {e['id']: i for i, e in enumerate(inv['eventos'])}
    paginas = {p['numero']: p for p in inv['paginas']}
    numeros = sorted(p['numero'] for p in inv['paginas'])
    if len(numeros) != total or any(n != i for i, n in enumerate(numeros, 1)):
        erro('cobertura_invalida', '/paginas', 'Páginas ausentes, repetidas ou fora do total.')

    def ref(alvo, universo, onde):
        if alvo not in universo:
            erro('referencia_inexistente', onde, 'Referência não encontrada no conjunto esperado.')
            return False
        return True

    def pendencia(codigo, alvos, onde):
        if not any(p['codigo'] == codigo and set(p['referencias']) & set(alvos) for p in inv['pendencias']):
            erro('pendencia_ausente', onde, 'Condição incerta exige pendência específica e referenciada.')

    def chave(f):
        return f['paginas']['inicio'], ordem_bloco.get(f['block_id'], -1), f['inicio']

    por_bloco = {}
    por_peca = {pid: [] for pid in ps}
    for i, f in enumerate(inv['fragmentos']):
        onde = f'/fragmentos/{i}'
        if ref(f['block_id'], blocos, onde + '/block_id'):
            b = blocos[f['block_id']]
            por_bloco.setdefault(f['block_id'], []).append(f)
            pg = f['paginas']
            if (not 0 <= f['inicio'] < f['fim'] <= len(b['text'])
                    or not 1 <= pg['inicio'] <= pg['fim'] <= total
                    or not b['page'] <= pg['inicio'] <= pg['fim'] <= b.get('page_end', b['page'])
                    or (pg['precisao'] == 'pagina' and pg['inicio'] != pg['fim'])
                    or (pg['origem'] == 'extracao' and (pg['inicio'], pg['fim']) != (b['page'], b.get('page_end', b['page'])))):
                erro('intervalo_invalido', onde, 'Offsets, precisão ou envelope incompatíveis com a origem.')
        if f['paginas']['precisao'] == 'indeterminada' or f['paginas']['origem'] == 'indeterminada':
            pendencia('localizacao_indeterminada', [f['id']], onde)
        d = f['destino']
        if d['classe'] == 'peca':
            if ref(d['piece_id'], ps, onde + '/destino'):
                por_peca[d['piece_id']].append(f)
        elif d['classe'] == 'nao_atribuido':
            pendencia('fragmento_nao_atribuido', [f['id']], onde)
    for bid, b in blocos.items():
        cursor = 0
        for f in sorted(por_bloco.get(bid, []), key=lambda f: (f['inicio'], f['fim'])):
            if f['inicio'] != cursor:
                erro('cobertura_invalida', '/fragmentos', 'Partição contém lacuna ou sobreposição.')
            cursor = f['fim']
        if cursor != len(b['text']):
            erro('cobertura_invalida', '/fragmentos', 'Partição não conserva todo o texto de origem.')

    def conferencia(obj, dimensao, onde, fragmentos):
        estado = obj[dimensao]
        if estado['estado'] == 'proposto':
            return
        ev = eventos.get(estado['evento_id'])
        sufixo = 'secao' if dimensao == 'conferencia' else dimensao
        acao = ('conferir_' if estado['estado'] == 'conferido' else 'rejeitar_') + sufixo
        if (not ev or ev['ator']['tipo'] != 'humano' or ev['acao'] != acao or obj['id'] not in ev['alvos']):
            erro('conferencia_invalida', onde, 'Conferência sem evento humano correspondente à dimensão e ao alvo.')
        proposta = obj.get('proposta_evento_id')
        if not proposta and 'piece_id' in obj and obj['piece_id'] in ps:
            proposta = ps[obj['piece_id']]['proposta_evento_id']
        if (proposta and (prefixo == 0 or posicoes_evento.get(estado['evento_id'], -1) >= prefixo)
                and posicoes_evento.get(estado['evento_id'], -1) <= posicoes_evento.get(proposta, -1)):
            erro('conferencia_invalida', onde, 'Conferência deve suceder a proposta atual da peça.')
        if dimensao == 'limites' and estado['estado'] == 'conferido' and any(
                f['paginas']['precisao'] == 'indeterminada' or f['paginas']['origem'] == 'indeterminada' for f in fragmentos):
            erro('conferencia_invalida', onde, 'Limites de localização indeterminada não podem ser conferidos.')

    if sorted(p['ordem'] for p in ps.values()) != list(range(1, len(ps) + 1)):
        erro('limites_incoerentes', '/pecas', 'Ordem das peças deve ser única e consecutiva.')
    for i, p in enumerate(inv['pecas']):
        onde = f'/pecas/{i}'
        ligados = sorted(por_peca[p['id']], key=chave)
        ref(p['inicio'], fs, onde + '/inicio')
        ref(p['fim'], fs, onde + '/fim')
        if (not ligados or p['inicio'] != ligados[0]['id'] or p['fim'] != ligados[-1]['id']
                or any(f['paginas']['fim'] > ligados[-1]['paginas']['fim'] for f in ligados)):
            erro('limites_incoerentes', onde, 'Limites não delimitam os fragmentos da própria peça.')
        ev = eventos.get(p['proposta_evento_id'])
        if not ev or ev['acao'] not in ('propor', 'corrigir') or p['id'] not in ev['alvos']:
            erro('conferencia_invalida', onde + '/proposta_evento_id', 'Proposta sem evento correspondente.')
        for e in p['evidencias']:
            for fid in e['fragmentos']:
                ref(fid, fs, onde + '/evidencias')
        if p['tipo_proposto'] == 'nao_identificada':
            pendencia('tipo_nao_identificado', [p['id']], onde)
        for dimensao in ('limites', 'tipo'):
            conferencia(p, dimensao, onde + '/' + dimensao, ligados)
    corpo = [f for f in inv['fragmentos'] if f['destino']['classe'] == 'peca']
    # Ordem incompatível na fonte não deve ser reparada apenas ordenando o inventário.
    corpo_fonte = sorted(corpo, key=lambda f: (ordem_bloco.get(f['block_id'], -1), f['inicio']))
    if any(chave(a) > chave(b) for a, b in zip(corpo_fonte, corpo_fonte[1:])):
        erro('limites_incoerentes', '/fragmentos', 'Ordem de leitura da fonte incompatível com páginas físicas.')
    ordens = [ps[f['destino']['piece_id']]['ordem'] for f in sorted(corpo, key=chave) if f['destino']['piece_id'] in ps]
    if any(a > b for a, b in zip(ordens, ordens[1:])):
        erro('limites_incoerentes', '/pecas', 'Peças intercaladas ou em ordem física incompatível.')

    usados = set()
    for i, s in enumerate(inv['secoes']):
        onde = f'/secoes/{i}'
        ref(s['piece_id'], ps, onde + '/piece_id')
        for fid in s['fragmentos']:
            if ref(fid, fs, onde + '/fragmentos'):
                if fs[fid]['destino'] != {'classe': 'peca', 'piece_id': s['piece_id']} or fid in usados:
                    erro('secao_fora_da_peca', onde, 'Seção sobreposta ou sobre fragmento de outra peça.')
                usados.add(fid)
        conferencia(s, 'conferencia', onde + '/conferencia', [fs[f] for f in s['fragmentos'] if f in fs])
    for i, e in enumerate(inv['eventos']):
        if i < prefixo:
            continue  # alvos históricos preservados, comparados com a revisão anterior
        permitidos = conhecidos | (anteriores if e['acao'] == 'corrigir' else set())
        for alvo in e['alvos']:
            ref(alvo, permitidos, f'/eventos/{i}/alvos')
        dimensoes = {'limites': set(ps), 'tipo': set(ps), 'secao': {s['id'] for s in inv['secoes']}}
        if e['acao'].startswith(('conferir_', 'rejeitar_')):
            universo = dimensoes[e['acao'].split('_', 1)[1]]
            if any(alvo not in universo for alvo in e['alvos']):
                erro('conferencia_invalida', f'/eventos/{i}', 'Ação humana aponta classe de objeto incompatível.')
    for i, p in enumerate(inv['pendencias']):
        for alvo in p['referencias']:
            ref(alvo, conhecidos, f'/pendencias/{i}/referencias')
        avisos.append({'codigo': p['codigo'], 'onde': f'/pendencias/{i}', 'material': p['material']})
    if inv['origem']['configuracao_sha256'] is None:
        pendencia('configuracao_nao_registrada', [inv['inventario_id']], '/origem/configuracao_sha256')

    for n, pg in paginas.items():
        presentes = [f for f in inv['fragmentos'] if f['paginas']['inicio'] <= n <= f['paginas']['fim']]
        esperada = leitura_fonte(doc, n)
        leitura = pg['leitura']
        if leitura != esperada:
            erro('leitura_incoerente', '/paginas', 'Leitura declarada diverge da presença e dos avisos da fonte.')
        alvos = [f'pagina-{n}'] + [f['id'] for f in presentes]
        if leitura == 'ocr_parcial':
            pendencia('leitura_insuficiente', alvos, '/paginas')
        elif leitura == 'sem_texto':
            pendencia('pagina_sem_texto', [f'pagina-{n}'], '/paginas')
        elif leitura == 'nao_processada':
            pendencia('pagina_nao_processada', [f'pagina-{n}'], '/paginas')
    for i, _ in enumerate(doc.get('warnings', [])):
        avisos.append({'codigo': 'aviso_extracao', 'onde': f'/extracao/warnings/{i}', 'material': True})


def leitura_fonte(doc, n):
    """Envelope não prova presença em páginas intermediárias; avisos prevalecem.

    OCR aplicado pode suceder o aviso original de página sem texto. Um aviso
    sem localização é global, nunca simplesmente descartado.
    """
    bs = [b for b in doc['blocks'] if b['text'].strip() and n in (b['page'], b.get('page_end', b['page']))]
    wa = [a['codigo'] for a in doc.get('warnings', []) if a.get('page', a.get('pagina')) in (None, n)]
    ocr = any('ocr' in b.get('tags', []) for b in bs) or any(
        c.startswith('ocr_') and c not in ('ocr_indisponivel', 'ocr_sem_texto', 'ocr_idioma_degradado') for c in wa)
    if ocr:
        return 'ocr_parcial'
    if 'pagina_ilegivel' in wa:
        return 'nao_processada'
    if set(wa) & {'pagina_sem_texto', 'ocr_sem_texto', 'pagina_possivelmente_digitalizada'}:
        return 'sem_texto'
    if bs:
        return 'texto_nativo'
    if set(wa) & {'truncado', 'tempo_excedido'} or any(b['page'] < n < b.get('page_end', b['page']) for b in doc['blocks']):
        return 'nao_processada'
    return 'sem_texto'
