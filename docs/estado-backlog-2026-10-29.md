# Estado do backlog da revisão crítica (2026-10-29)

Base: HEAD `4e9989c`, branch `fix/fase2-correcoes`. Reconcilia os itens de `docs/revisao-critica-fase2.md` e `docs/avaliacao-skills-2026-10-18.md` com o código atual (tarefa H-08 do plano de aprimoramentos).

**Método e limite.** Leitura dirigida por busca textual em `scripts/` e `tests/`, com os trechos relevantes lidos. Não houve execução da suíte completa neste levantamento; "resolvido" significa que o mecanismo existe no código e há teste correspondente localizado, não que a correção foi reproduzida. Itens sem evidência ficam como **não verificado**.

Contagem de testes: `pytest --collect-only` coleta **467** (463 offline + 4 opcionais), o que confere com o selo do README. Os "390 aprovados e 1 ignorado" da `COORDENACAO.md` são a fotografia anterior às Fases 4 e 5 e não precisam de correção, apenas de data.

## Críticos (C) e altos (A)

| Item | Estado | Evidência |
|---|---|---|
| C1 gate sem extração | resolvido | G00 em `auditar.py`, documentado na skill |
| C2 aprovação por agente | resolvido, com limite aceito | terminal interativo e frase digitada; arquivo forjável à mão segue como limite declarado |
| C3 perda silenciosa de texto | resolvido | DOCX rastreado, cabeçalho/rodapé com aviso e `partial`; PDF digitalizado marcado |
| C4 localizador e data | resolvido | `localizador_incoerente`, `data_fora_do_trecho` |
| C5 uma só família de documento | **aberto** | STJ + STF real (R06); R07 (TJ) e R10 (escaneado real) pendentes |
| C6 skills sem avaliação por modelo | **parcial** | uma rodada, um modelo (18/10); segunda rodada pendente |
| A1 hash dependente de blocos | resolvido | `text_sha256` do texto bruto (extrator 0.3.0) |
| A2 `trecho_em_citacao` | resolvido para `supported` | erro `trecho_so_em_citacao` em precedente, tema e súmula (`validate.py` ~460); permanece aviso nos demais estados e tipos |
| A3 `inteiro_teor` autodeclarado | resolvido | erros `ementa_nao_equivale_a_inteiro_teor` e `inteiro_teor_sem_voto` |
| A4 STF sem PDF no disco | **parcial** | caso real R06 em regressão; fluxo continua manual (PDF baixado pelo usuário) |
| A5 trecho curto ou entre parágrafos | resolvido | aviso `trecho_curto`; janela de dois blocos consecutivos; teste de hifenização em `test_rigor.py` |
| A6 lacuna por substring | resolvido | vínculo por `document_id`; o antigo casamento por nome só avisa |
| A7 modo padrão permissivo | **aberto, decisão do titular** | `--modo` default `analise` em `auditar.py` |
| A8 dependências fora do repositório | **parcial** | `fetch_oficial.py` está versionado e só usa `~/.claude/downloads` como saída padrão; ForgeLex e o navegador do app seguem externos, descritos em `shared/fontes-br.md` |
| A9 git, requirements, notices | resolvido | git, requirements, `THIRD_PARTY_NOTICES.md` presentes |

## Médios (M)

| Item | Estado | Evidência / observação |
|---|---|---|
| M1 `documentado` em narrativa | resolvido em parte | aviso `documentado_em_narrativa`; peça de parte como prova de fato segue sem aviso (validador não conhece a natureza do documento) |
| M2 rodapés removidos | não verificado | `_remover_repetidas` devolve `rodapes`; conferir se guardam todas as linhas |
| M3 tempo e limite de páginas | parcial | `MAX_PAGES=2000` com aviso `truncado`; sem timeout; suíte lenta |
| M4 chave de cache | resolvido | chave inclui versão das bibliotecas |
| M5 segurança da extração | resolvido em parte | limites de zip bomb em `extract.py`; teste de instrução embutida em `test_extract_formatos.py`; cobertura de injeção em PDF específico não verificada |
| M6 testes frouxos | não verificado | teste de PDF truncado agora afirma falha explícita (`test_extract.py`); o assert do mapeamento não foi relido |
| M7 `cnj.py` órfão | resolvido | usado por `triagem.py processos` |
| M8 pastas do caso | resolvido | `triagem.py init` |
| M9 escopo de proposição | resolvido | súmula incluída nas regras de citação; tese de repercussão geral tratada como `tema` |
| M10 gatilhos das skills | resolvido em parte | `tests/test_gatilhos.py`, aproximação lexical; não testa o modelo |

## Achados da avaliação de 18/10 deixados em aberto

| Achado | Estado |
|---|---|
| `aprovacao.json` forjável à mão | limite aceito e documentado |
| `documentado` apoiado em peça de parte | aberto (ver M1) |
| Validador não confere relação semântica trecho–proposição | limite aceito e documentado |
| Fonte secundária `lida` aceita qualquer hash de 64 caracteres | aberto; só `--reverificar` confere |
| Redline não ligado ao `issues.json` | aberto (C-02) |
| Localizador por sufixo em `preencher.py` casava o bloco errado | **corrigido nesta rodada** (ver abaixo) |

## Alterações desta rodada

- `scripts/preencher.py`: `_bloco` passa a preferir o localizador exato e, quando só há correspondência por sufixo com mais de um bloco, escolhe o que contém o trecho. Chamada em `lint` passa o trecho.
- `tests/test_docx_edicao.py`: dois testes novos (`test_localizador_por_sufixo_escolhe_o_bloco_que_contem_o_trecho` e `test_localizador_exato_tem_prioridade_sobre_o_sufixo`). Falhavam antes da correção e passam depois. Executados `test_docx_edicao.py` e `test_contrato.py`: 62 passam. Suíte completa não executada.
- Observação de ambiente: os arquivos de trabalho têm fim de linha CRLF (checkout Windows) e o índice guarda LF; o diff real é de 37 linhas, apesar de uma visão Linux mostrar o arquivo inteiro como alterado.

## Efeito sobre o plano de aprimoramentos

I-01 a I-04, I-07 e boa parte de I-06 estão resolvidos ou parcialmente resolvidos; I-05 é o único item de validação ainda aberto com mudança de formato; C-03 foi executado. O plano foi ajustado de acordo.
