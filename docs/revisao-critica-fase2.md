# Revisão crítica da Fase 2 (17/10/2026)

Escopo: `extract.py`, `validate.py`, `auditar.py`, `cnj.py` e as skills `br-mapear-autos`, `br-verificar-citacoes` e `br-auditar-entrega`. Método: releitura do código e **sondas reais** sobre os furos suspeitos. Os itens marcados **[confirmado]** foram reproduzidos; os demais são inferência do código ou do desenho. Revisor: o mesmo autor do código, portanto não é uma revisão independente.

## O que está sólido

- 91 testes passam. Fontes reais (acórdão do STJ e CC compilado) atravessam extração, validação e auditoria.
- A extração falha de forma explícita em PDF em branco, corrompido, extensão recusada e arquivo grande.
- O validador recusa trecho inventado, hash trocado, ementa usada como inteiro teor, inexistência concluída por busca vazia e teto de fonte secundária.
- Alterar um byte de qualquer artefato ou fonte derruba a aprovação.

## Crítico: viola uma das quatro garantias

| # | Furo | Evidência | Correção proposta |
|---|---|---|---|
| C1 | `auditar` libera `revisao_pronta` **sem extração**: G02 sai "aprovado" sem conferir nenhum trecho. Fonte oficial lida sem `local_file` passa em G05 com "0 fontes conferidas" | [confirmado] sondas P3 e P4 | Em `fundamentada`, exigir extração e reprovar; em qualquer modo, `supported` sem `local_file` vira alerta de "não reconferível" |
| C2 | Qualquer processo pode **aprovar em nome do revisor**: `aprovar` rodou com stdin nulo, como um agente rodaria. A regra é só de procedimento | [confirmado] P5 | Exigir confirmação digitada em terminal real (TTY); sem TTY, recusar. O revisor roda no painel de terminal do app |
| C3 | **Perda silenciosa de texto com status `ok`**: DOCX com inserção rastreada perde o texto inserido (só aviso, status segue `ok`); cabeçalho, rodapé, notas e caixas de texto do DOCX são ignorados sem aviso; página digitalizada com carimbo de texto vira `ok` com uma linha | [confirmado] P1, P1b, P6 | Alteração rastreada vira `partial`; avisar parte do DOCX ignorada; detectar página com imagem grande e pouco texto e marcá-la `partial` |
| C4 | **Localizador e data não são conferidos.** Sem `block_id`, o trecho é buscado no documento inteiro: localizador `p.2` para trecho da p.16 passa sem aviso. `date.original` pode não ter relação com o trecho | [confirmado] P2 e P9 | Calcular onde o trecho foi achado e comparar com `locator`; exigir `date.original` dentro do `excerpt` |

## Crítico para a validade do conjunto

| # | Furo | Observação |
|---|---|---|
| C5 | **Uma só família de documento.** Todas as heurísticas (margem, recuo como citação, títulos de seção, rodapés) foram calibradas em um acórdão do STJ. Os dois casos "reais" derivam do mesmo PDF e foram escritos por mim. STF, TJs, petições e contratos escaneados não foram testados | O plano pedia 12 casos com gabarito de revisor jurídico; há 2, de uma fonte |
| C6 | **Nenhuma skill foi executada por um modelo com avaliação.** Os testes cobrem scripts. Não se sabe se o modelo segue o roteiro, classifica `alegacao` corretamente ou resiste a instrução embutida em PDF | Skills são prompts: sem eval, a qualidade é suposição |

## Alto

| # | Furo | Observação |
|---|---|---|
| A1 | `text_sha256` depende da **segmentação em blocos**. Mudar uma heurística muda o hash e quebra qualquer `claims.json` que o use | [confirmado] P11. Corrigir antes de haver claims reais: hash do texto normalizado, sem fronteira de bloco |
| A2 | `trecho_em_citacao` é só aviso, inclusive em `supported` de precedente com escopo `inteiro_teor`: a prova pode estar em texto transcrito de outro órgão | Tornar erro, salvo declaração explícita de que se prova o que a decisão transcreve |
| A3 | `text_scope: inteiro_teor` é autodeclarado. Um PDF só com ementa passaria | Conferir se a extração tem seção de voto ou relatório |
| A4 | **STF sem caminho até arquivo e hash.** O navegador do app lê a página, mas o PDF não chegou ao disco. Na prática teses do STF ficam em `partial`, e a skill não diz isso | Registrar como limite explícito; ou definir fluxo com PDF baixado pelo usuário |
| A5 | Trecho que atravessa dois parágrafos, ou que tenha hifenização de fim de linha, dá falso erro. Não há tamanho mínimo: `excerpt` de três palavras vale como prova | [confirmado] P7 (falso erro). Aviso para `excerpt` curto; casar por janela de blocos |
| A6 | G03 casa a lacuna por **substring do nome do arquivo** no texto livre | Campo `document_id` na lacuna |
| A7 | Padrão é `--modo analise` (permissivo) e "nenhuma tese central" é só alerta, então esquecer de marcar `central` esvazia o gate G06 | Padrão seguro (`fundamentada`); exigir declaração quando não há central |
| A8 | **Dependências fora do repositório:** `fetch_oficial.py` fica em `~/.claude/scripts`; ForgeLex é serviço de terceiro (créditos, sessão OAuth) para onde vão os termos da consulta; o navegador do app é manual. As skills não descrevem o fallback nem avisam que consultas saem da máquina | Documentar fallback e política de dados por caso |
| A9 | **Sem git, sem `requirements`/`pyproject`, sem `THIRD_PARTY_NOTICES.md`.** Nada está versionado, as versões das bibliotecas não estão fixadas e pypdf (usado só em testes) não é declarado | [confirmado] `git status` e `ls`. Fazer antes de qualquer outra coisa: `git init`, requirements, notices |

## Médio

| # | Furo |
|---|---|
| M1 | Fato `documentado` apoiado na **narrativa** do relatório ou do voto (não em citação) não é sinalizado; decisões narram fatos que não provam |
| M2 | Rodapés removidos guardam só a contagem e 3 exemplos: data de publicação e de assinatura se perdem. Guardar todas as linhas removidas em campo à parte |
| M3 | Layout: duas colunas e tabelas são lidas linha a linha; geometria calibrada em A4; sem timeout (até 2000 páginas no pdfplumber, que é lento); suíte leva ~74 s |
| M4 | A chave de cache não inclui a versão das bibliotecas (só a do extrator) |
| M5 | Segurança da extração não testada: DOCX é zip e `z.read` não limita tamanho (zip bomb); só há teste de link simbólico no nível do arquivo; nenhum teste de prompt injection embutida em PDF, como o plano exigia |
| M6 | Testes frouxos: o do PDF truncado aceita qualquer status, e um `assert` do mapeamento compara duas listas de avisos sem afirmar nada útil |
| M7 | `cnj.py` não é usado por nenhuma skill e não confere tabela de tribunais |
| M8 | As skills supõem pastas `derived/` e `outputs/` que nenhum script cria; a triagem (que criaria o `matter.md`) ainda não existe |
| M9 | `proposition_scope` por padrão só cobre `precedente` e `tema`; súmula e tese de repercussão geral ficam sem regra |
| M10 | Gatilhos das skills (`description`) não foram testados: risco de sobreposição entre `br-mapear-autos`, `br-verificar-citacoes` e a futura `br-pesquisa-juridica` |

## Ordem sugerida

1. **Antes da Fase 3 (cerca de 1 a 2 dias):** A9 (git, requirements, notices), C1, C2, C3, C4, A1.
2. **Junto com a Fase 3:** A2, A3, A5, A6, A7, M1, M2, M4, M6 e o fluxo de pasta do caso (M8, na `br-triagem`).
3. **Depende de você, não de código:** corpus com outros tribunais e documentos escaneados (C5), revisor jurídico que escreva os gabaritos, e uma rodada de avaliação das skills em modelo (C6). Sem isso, o pacote tem scripts testados e prompts não testados.

## Status das correções (17/10/2026, branch `fix/fase2-correcoes`)

| # | Situação | O que mudou | Verificação |
|---|---|---|---|
| A9 | corrigido | `git init`; `requirements.txt` e `requirements-dev.txt` com versões fixadas; `THIRD_PARTY_NOTICES.md` | `pip check` sem conflito; **nada foi commitado ainda** |
| A1 | corrigido | `text_sha256` agora é o hash do texto bruto lido, sem depender de blocos (extrator 0.3.0) | teste: segmentação diferente, mesmo hash; dois downloads do mesmo acórdão têm o mesmo hash |
| C1 | corrigido | Gate G00: sem extração, alerta (`analise`) ou reprovação (`fundamentada`). Em G05, `supported` com fonte oficial sem `local_file` vira alerta ou reprovação | testes com o caso real |
| C2 | corrigido, com limite | `aprovar` exige console interativo e a frase digitada (`APROVO` ou `REPROVO` + 8 caracteres do hash do `qc.json`). Achado no caminho: no Windows `isatty()` é verdadeiro para o stdin nulo (NUL), então a checagem também usa `GetConsoleMode` | recusa por subprocesso sem terminal testada; **console real** confirmado uma vez no painel de terminal do app; a digitação da frase só foi testada por simulação. Um agente com ferramenta que digita no terminal do usuário ainda poderia contornar |
| C3 | corrigido | DOCX: inserções rastreadas entram (tag `inserido`), exclusões saem, resultado `partial`; notas de rodapé, de fim e controles de conteúdo são extraídos; cabeçalho, rodapé, comentários e caixas de texto geram aviso e `partial`; células mescladas não duplicam; limite de tamanho descomprimido. PDF: página coberta por imagem com pouco texto vira `pagina_possivelmente_digitalizada` | testes com DOCX e PDF construídos à mão. O limiar (imagem ≥ 50% da página, menos de 300 caracteres) é heurístico |
| C4 | corrigido | `localizador_incoerente` é erro quando o trecho está em outra página ou parágrafo; `data_fora_do_trecho` é erro | testes, incluindo arquivo sem páginas |

Casos de teste adaptados: as datas dos testes de `facts.json` passaram a vir de dentro do trecho. Um teste de auditoria dependia do segundo do relógio e foi corrigido.

Continuam abertos: C5 (um só tipo de documento), C6 (skills sem avaliação por modelo), A2 a A8, M1 a M10.
