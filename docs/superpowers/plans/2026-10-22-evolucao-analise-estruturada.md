# Evolução da análise estruturada — plano de execução aprovado

> **Autorização de 22/10/2026:** “Aprovo o contrato e o plano. Prossiga com a EV-01”. Usar `superpowers:executing-plans` apenas nessa etapa, com revisão final somente leitura. EV-02 a EV-06, implementação delegada, APIs, modelos e novos serviços não foram iniciados nem autorizados por este pedido. Sem commit ou push.

**Goal:** entregar análise documental cível estruturada, mais profunda e verificável, reduzindo conferências técnicas triviais e reservando ao profissional decisões jurídicas relevantes.

**Architecture:** preservar skills, scripts e contratos existentes; acrescentar contrato aditivo de análise e política técnica avaliada em paralelo. Comparar melhorias técnicas com um fluxo agêntico delimitado antes de adotar runtime, modelos ou infraestrutura.

**Tech Stack:** Python >=3.12 e dependências fixadas atuais; ambiente de referência existente Windows/Python 3.14.6. SDK, modelos, persistência e ferramentas externas são candidatos, sem adoção neste plano.

**Spec:** [contrato analise-1 aprovado](../specs/2026-10-22-analise-estruturada-design.md). **Andamento/prioridades:** exclusivamente [plano principal](../../plano-principal.md). Os pacotes abaixo descrevem a decomposição aprovada; somente EV-01 recebeu autorização de execução.

## 1. Restrições globais

- Trabalhar somente no worktree Codex `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`; Claude permanece no checkout original, sem Git, instalação, testes ou escrita nele.
- Reconfirmar remoto, branch, HEAD, estado, índice e worktrees antes da futura execução; este planejamento partiu de `codex/organizacao-colaboracao`, HEAD `3ab28e211641acb8fe75da5152fa0235e25fbd4d`, com alterações documentais preexistentes.
- Preservar originais, alterações locais e evidências históricas; 19 regras continuam inativas, NDA vazio. Não presumir aprovação material/encerramento da fase 5.
- Autorização atual: somente schema, contrato, validação/renderização e fixtures/testes da EV-01. Não iniciar os demais pacotes, chamadas de inferência, dependências, credenciais ou estado persistente.
- Cada adoção futura de framework, API/serviço, modelo externo, persistência, instalação, commit, push e publicação depende de autorização própria.
- Reaproveitar invariantes existentes e manter os modos legados. Política técnica experimental não ignora os bloqueios atuais nem registra eventos humanos.
- Não duplicar cronograma: esta é decomposição técnica proposta; andamento, reserva e prioridade de execução ficam no plano principal.
- Arquivos citados como futuros não existem por força deste plano. Assinaturas são interfaces propostas, sujeitas à aprovação do contrato.

## 2. Foco da revisão e testes que deverão demonstrá-lo

| Entrada/falha | Comportamento obrigatório | Pacote responsável |
|---|---|---|
| Resultado de precedente transcrito misturado ao acórdão atual | Atribuir corretamente e não alterar o resultado atual; teste `test_precedente_nao_substitui_dispositivo_atual` | EV-03/EV-05 |
| Acórdão relata prova ou peça não fornecida | Distinguir relato de exame primário; teste `test_relato_nao_vira_prova_primaria` | EV-01/EV-05 |
| Aviso genérico junto a trecho legível e aviso grave no dispositivo | Resolver o primeiro tecnicamente e restringir o segundo; `test_politica_diferencia_rodape_e_dispositivo` | EV-03 |
| Alteração de fonte após QC, referência incompatível ou retomada | Invalidar dependentes, preservar histórico e não duplicar efeito externo; `test_retomada_invalida_dependentes_sem_duplicar_efeito` | EV-01/EV-04 |
| Fonte externa inacessível ou instrução maliciosa em documento | Registrar limite/abster conclusão dependente e não executar instruções do documento; `test_fonte_indisponivel_e_documento_nao_da_ordens` | EV-04/EV-05 |

Na preparação documental EV-P01 nenhuma dessas verificações havia sido executada. Resultados posteriores da EV-01 ficam na coordenação/plano principal, sem antecipar os testes atribuídos às etapas futuras.

## 3. Entregas, arquivos e interfaces futuras

Caminhos relativos ao worktree Codex. Confirmar responsabilidades antes de criar módulo; reutilizar o que já existe sem refatoração paralela.

| Pacote | Arquivos previstos | Interface proposta / responsabilidade |
|---|---|---|
| EV-01 contrato executável, depois de aprovado | `docs/contratos/analise-v1.md`, `docs/contratos/analise-v1.schema.json`, `scripts/analise_estruturada.py`, `tests/test_analise_estruturada.py` | `validar_analise(obj: dict, entradas: dict[str, bytes]) -> dict`; `renderizar_analise(obj: dict) -> str`. Resultado com `valido`, `erros`, `avisos`; sem certificar mérito |
| EV-02 corpus/avaliação | `scripts/avaliar_analise.py`, `tests/test_avaliar_analise.py`, `docs/avaliacao-analise-protocolo.md`; casos/gabaritos reais fora do Git | `avaliar_caso(predicao: dict, gabarito: dict, julgamento: dict) -> dict`; `agregar_resultados(resultados: list[dict]) -> dict` |
| EV-03 automação técnica | `scripts/extract.py`, `scripts/pecas_proposta.py` quando justificado; novo `scripts/politica_uso.py`; `tests/test_politica_uso.py`, `tests/test_atribuicao_contextual.py` | `avaliar_uso_tecnico(achados: list[dict], contexto: dict) -> dict`, produz ações/limites do contrato. `pecas_uso.py` permanece com o contrato atual durante o piloto |
| EV-04 fluxo agêntico isolado | `scripts/fluxo_analise.py`, `tests/test_fluxo_analise.py`; configuração e resultados por caso fora do Git | `executar_fluxo(entradas: dict[str, bytes], configuracao: dict, ferramentas: dict) -> dict`; coordenar etapas limitadas, com adaptador do runtime escolhido |
| EV-05 piloto comparativo | `docs/resultado-piloto-analise.md`; manifestos, saídas, avaliações cegas e logs externos | Tabela por caso/variante/repetição, métricas agregadas e decisão de adoção, inclusive rejeição |
| EV-06 eventual integração | `scripts/validate.py`, `scripts/auditar.py`, skills de autos/pesquisa/auditoria, `shared/dados.md`, README/avisos de terceiros somente no escopo aprovado | Integração aditiva e opt-in, após aprovação do piloto e de qualquer mudança de política. Sem migração silenciosa |

A futura `validar_analise` reutiliza `validate.validar_facts`, `validate.validar_claims` e `pecas_uso.carregar_contexto` onde seus contratos se aplicarem. Não sobrecarregar `extract.py` com raciocínio jurídico. O avaliador não usa o próprio modelo avaliado como única fonte de gabarito.

## 4. EV-01 — aprovar e tornar verificável o contrato

**Entrada:** especificação analise-1 e formatos legados. **Saída:** contrato aceito; em futura execução, schema/validação/renderização com exemplos e regressões.

- [ ] Revisar campos, qualificações, referência a fatos/claims, atores, cobertura e política de intervenção. Resolver ambiguidades no documento antes de código.
- [ ] Após autorização de implementação, escrever primeiro os testes `test_referencia_resolve_snapshot_exato`, `test_referencia_incompativel_reprova`, `test_relato_nao_vira_prova_primaria`, `test_resultado_tecnico_nao_aprova_entrega` e `test_markdown_preserva_limites_do_json`.
- [ ] Confirmar falha pelos comportamentos ainda ausentes; implementar o mínimo das duas funções propostas; repetir os testes.
- [ ] Construir dois exemplos positivos sintéticos e cinco contraexemplos do contrato, sem copiar eventos humanos reais nem dar aprovação a P01/P02.
- [ ] Revisar o diff/compatibilidade e registrar limitações no plano principal. Versionamento somente se autorizado separadamente.

**Aceitação:** 100% das referências de exemplos resolvem os bytes corretos; referências quebradas/mismatches reprovam; afirmação material sem base/motivo não passa; fontes secundárias/parciais conservam limites; JSON e Markdown concordam em IDs, qualificações e restrições; nenhum evento humano/estado legado é promovido automaticamente.

**Validação futura:** `python -m pytest -q tests/test_analise_estruturada.py`. Isso não avalia profundidade jurídica; a rubrica é EV-02/EV-05.

## 5. EV-02 — congelar protocolo, corpus e baseline

**Entrada:** contrato aceito. **Saída:** protocolo registrado, corpus dividido por processo, gabarito/rubrica revisados e baseline A preservado.

- [ ] Identificar seis processos de desenvolvimento: P01/P02 mais quatro novos públicos/autorizados. R07/R10 já utilizados podem ser regressões adicionais; não entram como holdout.
- [ ] Reservar doze processos novos: quatro acórdãos isolados, quatro conjuntos de 3–10 peças e quatro conjuntos maiores de 11–30 peças. Limites propostos do piloto: até 40 páginas por acórdão isolado, 120 por conjunto menor e 250 por conjunto maior; não representam capacidade já validada. No total reservado: seis nativos, três digitalizados e três mistos; pelo menos três tribunais e duas origens no grupo OCR/misto. Se não houver insumos autorizados suficientes, reduzir a promessa e registrar estratos sem cobertura antes de executar.
- [ ] Separar por processo/família recursal e duplicata substancial. Páginas, versões, peças e decisões do mesmo processo não atravessam desenvolvimento/holdout. Citações naturais comuns entre julgados são registradas, sem tratar cada citação como novo processo. O conjunto reservado não entra em exemplos, prompts, ajuste de regras ou consultas de desenvolvimento; depois de aberto para avaliação, seus resultados permanecem congelados.
- [ ] Preparar gabarito profissional mínimo: questões/pedidos/argumentos materiais, resultado/alcance, evidências e erros críticos. Registrar revisor, data, fontes e divergências. Gabaritos e textos reais permanecem externos.
- [ ] Preparar dois níveis de entradas: originais para avaliação ponta a ponta; extrações congeladas comuns para avaliação semântica controlada. Hashes separam os resultados.
- [ ] Definir prompt/tarefa comum, versão exata do modelo/configuração, ferramentas permitidas, tetos financeiros e política de dados. Medir baseline A no desenvolvimento, congelar metas e protocolo antes de abrir o holdout.
- [ ] Após autorização, testar o avaliador com denominadores conhecidos, abstenção, dado ausente e vazamento; implementar as duas interfaces propostas e executar baseline A.

**Aceitação:** manifesto sem sobreposição indevida; hash de cada snapshot; gabarito com responsável real e limites; rubric e tetos fechados antes das execuções pagas; baseline nativo imutável, sem correções manuais ocultas. Falta de revisor, fontes ou orçamento deixa esta etapa pendente — não vira gabarito de modelo ou autorização presumida.

**Validação futura:** `python -m pytest -q tests/test_avaliar_analise.py`, incluindo `test_nao_conta_paginas_como_processos`, `test_abstencao_e_falha_entram_no_denominador` e `test_detecta_vazamento_de_processo`.

## 6. Piloto comparativo: desenho comum a EV-03/04/05

### 6.1 Variantes

| Variante | Conteúdo | Efeito isolado |
|---|---|---|
| A — atual | Código/skills congelados da base, execução no host, objetivo e formato de avaliação comuns | Baseline; preenchimento ausente conta como lacuna, sem completar manualmente |
| B — técnica | A mais melhorias técnicas selecionadas, mesma tarefa e mesmo modelo/configuração | Efeito da extração/atribuição/validação técnica |
| C — agêntica | B mais etapas de análise, pesquisa e revisão com um runtime congelado | Efeito do fluxo controlado, com custo adicional explicitado |

Não comparar A com um modelo fraco e C com outro mais forte. O primeiro comparativo mantém um mesmo modelo e versão nas três variantes; disponibilidade real precisa ser confirmada antes do protocolo final. Se não for possível, declarar comparação de sistemas completos e não atribuir o ganho apenas à arquitetura.

Na avaliação semântica controlada, todas recebem as mesmas extrações/fontes congeladas; B conserva apenas suas verificações/organização aplicáveis, sem reextrair. Na ponta a ponta, todas partem dos mesmos originais; A usa a base e B/C a extração melhorada. Relatar os dois experimentos separadamente.

**Pesquisa:** primeiro usar o mesmo conjunto congelado de fontes em A/B/C, sem rede. Pesquisa remota será ensaio separado, após autorização: mesmas perguntas, fontes/ferramentas e tetos, sem dar a C autoridades selecionadas manualmente e negá-las a A/B. Medir localização, leitura e pertinência separadamente; resultado online não se mistura ao ganho semântico offline.

Adapter de comparação só reorganiza campos existentes. Não cria argumentos, preenche omissões ou corrige a resposta de A. Registrar o prompt comum, tempo do operador e tudo que dependeu de intervenção.

### 6.2 Repetições, cegamento e intervenção

Proposta de execução principal: 12 casos reservados × 3 variantes × 2 repetições = **72 execuções por experimento**. Experimento semântico e ponta a ponta somam até 144 execuções; autorizar o teto de cada um separadamente, começando pelo semântico. Se o teto não permitir, revisar o desenho antes de executar, sem coletar parcialmente e selecionar só acertos.

Randomizar ordem por caso, registrar versão/configuração e apresentar as saídas com rótulos cegos ao avaliador. Repetições não viram novos processos independentes. Relatar resultado por caso, pior repetição, distribuição e macro/microagregação; amostra pequena é exploratória, sem promessa de precisão populacional.

Uma mesma pessoa pode revisar, com ordem randomizada, intervalo e registro dessa limitação; segundo revisor é recomendado para erros críticos e divergências, sem assumir contratação/custo autorizados. A equipe/modelo que ajustou o sistema não escreve sozinho o gabarito final.

Intervenção manual de recuperação, reclassificação ou escolha de trecho invalida a condição “nativa” daquela execução; preservar a falha e avaliar uma continuação assistida separada. Falha, timeout e saída inválida permanecem no denominador.

### 6.3 Métricas e rubrica profissional

| Dimensão | Medida |
|---|---|
| Integridade | Referências resolvidas, identidade/hash, divergência JSON/Markdown, preservação do original |
| Cobertura | Recall/precisão de questões, pedidos, argumentos e fatos materiais; omissão crítica por caso |
| Atribuição/prova | Interlocutor correto, fala própria/transcrição, relato/prova primária, resultado atual/precedente |
| Fundamentação | Afirmações apoiadas em fontes pertinentes, inferências qualificadas, autoridades efetivamente lidas e limitações temporais |
| Profundidade | Pontuação 0–4 em conexão entre fatos/provas/fundamentos, confronto de posições, consequências/alternativas e tratamento das lacunas |
| Utilidade | Tempo ativo de revisão até corrigir/decidir, correções materiais, perguntas técnicas triviais e decisões jurídicas relevantes |
| Operação | Custo/tokens/chamadas por execução, latência, memória quando observável, falhas, retomadas e efeitos repetidos |

Escala comum de profundidade: **0** ausente/errada; **1** lista ou paráfrase sem conexão; **2** conecta parcialmente, com lacuna material; **3** conecta os elementos materiais e enfrenta objeções/limites; **4** cumpre 3 e explica alternativas/consequências relevantes com precisão. Aplicar às quatro dimensões; “não aplicável” exige motivo do gabarito e sai apenas do denominador daquela dimensão, nunca do total de execuções.

Tempo humano mede trabalho ativo por protocolo comum, incluindo correções e decisões para chegar à mesma finalidade de revisão, sem contar espera do modelo. Classificar pergunta trivial por possibilidade de resolução com insumo legível/ferramenta disponível. Ausência de pergunta não é ganho se vier acompanhada de omissão ou erro oculto.

### 6.4 Metas de aceitação propostas, a congelar antes do holdout

Estas são **metas de projeto para aprovação**, não taxas já obtidas nem garantia de qualidade jurídica:

- **Integridade/segurança:** 100% das referências utilizadas resolvidas; zero aprovação/evento humano forjado, envio não autorizado, alteração do original ou erro crítico silencioso.
- **Conteúdo:** todas as questões/pedidos classificados como centrais no gabarito tratados corretamente ou explicitamente limitados por insumo ausente; recall macro de itens materiais ≥90% e precisão macro ≥95%. Uma limitação não justifica omissão de item respondível; medir abstenções corretas e indevidas separadamente.
- **Profundidade:** pelo menos 3/4 em cada dimensão aplicável de cada caso com insumos suficientes; nos insuficientes, limitações e análise possível recebem rubrica própria, sem dispensar o caso.
- **Ganho de C:** melhora média de profundidade ≥0,5 ponto versus A e mediana, por processo, de `(T_A - T_C) / T_A` ≥30%, usando a mediana das repetições como T de cada variante; T_A deve ser positivo. Se A já atingir média ≥3,5/4, exigir manutenção dessa qualidade e o ganho de tempo, registrando o efeito de teto. Não admitir piora de erros críticos; relatar também C versus B para justificar a complexidade agêntica.
- **Carga trivial:** zero exigência indiscriminada de conferência humana de hash, referência existente ou aviso benigno resolvido. Meta adicional de redução ≥50% das perguntas triviais versus A quando A tiver contagem não nula; se A já for zero, exigir zero em C.
- **B:** nenhuma nova falha crítica e nenhum caso com queda de 1 ponto ou mais em dimensão de profundidade; redução demonstrada de pelo menos uma classe técnica problemática do desenvolvimento, confirmada na avaliação. Sem ganho técnico observado, não adotar o componente por aparência.
- **Operação:** todas as execuções dentro dos tetos financeiros/tempo/chamadas pré-aprovados ou encerradas com falha/limite explícito. Tetos não definidos bloqueiam chamadas pagas, não o planejamento.

Erro crítico inclui atribuir decisão ao processo errado, inverter parte/resultado com efeito na conclusão, omitir pedido/questão central respondível, inventar autoridade/apoio, esconder leitura materialmente insuficiente ou simular aprovação humana. Restrição correta por documento realmente ausente não é erro crítico, mas não conta como solução da questão.

Qualquer falha crítica reprova a variante para adoção no escopo afetado, mesmo com média boa. A descoberta no holdout não autoriza ajustar e reclassificar a mesma amostra como teste independente: preservar resultado, voltar ao desenvolvimento e obter novo holdout para nova alegação de ganho.

## 7. EV-03 — automação técnica selecionada

**Entrada:** contrato/protocolo aceitos; falhas e baseline preservados. **Saída:** B reproduzível e relatório da política paralela.

- [ ] Priorizar retenção de geometria/proveniência, contexto de transcrições e classificação dos avisos por trecho/finalidade. Não criar exceções por título, página ou frase de P01/P02.
- [ ] Escrever primeiro os testes de atribuição e da distinção entre aviso benigno e dispositivo ilegível; confirmar RED.
- [ ] Implementar menor mudança coerente e `avaliar_uso_tecnico`; resultado somente paralelo, sem modificar a liberação legada ou eventos v1.
- [ ] Repetir controles positivos/negativos e medir no desenvolvimento. Piloto opcional Docling/OCRmyPDF somente após autorização específica de instalação/modelos/licenças; não é pré-requisito de B.
- [ ] Congelar B, hashes e configurações antes do holdout.

**Aceitação:** aviso benigno resolvido não gera tarefa humana; problema material continua visível e restringe conclusão; identidade/fragmentos íntegros; atribuição melhora sem generalização presumida; regras e contratos legados preservados.

**Validação futura:** `python -m pytest -q tests/test_politica_uso.py tests/test_atribuicao_contextual.py tests/test_org04.py`; depois suíte integral offline.

## 8. EV-04 — piloto agêntico delimitado

**Entrada:** B congelada, contrato e orçamento/política de dados aprovados. **Saída:** C e manifesto de execução, sem integração padrão.

- [ ] Registrar decisão de runtime em spike técnico usando só desenvolvimento/sintéticos: fluxo Python simples versus **um** candidato, LangGraph ou SDK tipado. Exigir retomada, limites e rastreabilidade; adotar solução menor se cumprir. Não empilhar LangGraph, OpenAI Agents SDK e PydanticAI.
- [ ] Definir um modelo/configuração comuns para A/B/C e o mecanismo real de acesso. Comparação adicional OpenAI/Anthropic/local é ensaio separado, posterior e condicionado a orçamento/hardware.
- [ ] Definir números antes de executar: custo máximo por caso e rodada, timeout de ferramenta e execução, chamadas, tentativas e ciclos de revisão. Sem definição/aprovação, não chamar API.
- [ ] Testar primeiro com ferramentas falsas offline: leitura autorizada, resolução de referências, busca em fontes congeladas, timeout, repetição, falha parcial e retomada.
- [ ] Implementar coordenador → mapeamento/análise → pesquisa dirigida quando necessária → revisão crítica → validação/renderização. Começar por papéis como etapas; separar agentes somente com ganho demonstrado.
- [ ] Restringir ferramentas; sem shell genérico, escrita no original, ativação de regras ou autorização por conteúdo de documento. Persistência/traces locais somente no escopo aprovado; nenhuma exportação externa de texto/traços por padrão.
- [ ] Congelar C; executar desenvolvimento e falhas adversariais antes do holdout. Pesquisa ao vivo fica fora do experimento principal até autorização própria.

**Aceitação:** resultado cumpre o contrato; falha não vira sucesso; fonte indisponível conserva estado correto; arquivo alterado invalida dependentes; retomada preserva IDs/histórico e não duplica efeitos; custo/limites são reportados; revisor aponta fonte e alvo, sem certificar consenso como verdade.

**Validação futura:** `python -m pytest -q tests/test_fluxo_analise.py`; falhas do foco de revisão obrigatórias; suíte integral offline e revisão mecânica das skills se forem alteradas.

## 9. EV-05 — executar, avaliar e decidir

**Entrada:** A/B/C congeladas e holdout ainda reservado. **Saída:** evidências comparativas, decisão justificada e limites.

- [ ] Executar primeiro o comparativo semântico controlado autorizado; preservar todos os resultados nativos e intervenção/custo.
- [ ] Avaliar às cegas, conferir erros críticos/divergências e agregar por processo/repetição/modalidade, sem inflar amostra com páginas.
- [ ] Aplicar as metas congeladas, relatar A/B/C inclusive falhas/abstenções e decidir se a ponta a ponta e a pesquisa online merecem execução autorizada.
- [ ] Executar etapas adicionais somente dentro dos tetos/escopos aprovados e publicar relatório separando seus efeitos.
- [ ] Recomendar adotar, restringir, refazer ou rejeitar cada componente; registrar a decisão no plano principal, sem promover toda a arquitetura pelo ganho de uma parte.

**Aceitação:** resultados rastreáveis e reprodutíveis quanto a entradas/configuração; julgamentos humanos reais identificados; erros/denominadores/custos disponíveis; zero seleção oculta de melhores saídas. Se C não justificar ganho sobre B, manter B e rejeitar a complexidade adicional.

## 10. EV-06 — integração somente após decisão favorável

**Entrada:** decisão expressa de adoção com escopo e política de uso aprovados. **Saída futura:** incremento opt-in revisável; migração explícita apenas se necessária.

- [ ] Registrar arquivos/interfaces e compatibilidade antes da mudança; escrever regressões que cubram modo legado e novo.
- [ ] Integrar apenas componentes aprovados, conservar gates legados até decisão própria e incluir regressões de conteúdo parcial, autoria, mudança de fonte e efeito da política.
- [ ] Executar testes focados, suíte completa offline, revisão mecânica pertinente e revisão do diff. Atualizar documentação/avisos de terceiros para dependências realmente adotadas.
- [ ] Pedir decisão separada sobre publicação/instalação e eventuais mudanças de gates humanos. Nenhuma regra contratual é ativada neste pacote.

**Aceitação:** compatibilidade demonstrada; saída nova opt-in, limites visíveis, originais/histórico intactos e 19 regras inativas. Teste local não comprova CI, instalação, qualidade jurídica ou uso profissional aprovado.

## 11. Verificação e pontos de parada

Comandos futuros sempre no worktree Codex, no ambiente próprio já adotado; conferir o intérprete antes. Para suíte offline: `JURIS_REDE=0` no ambiente do processo e `python -m pytest -q`. UTF-8 consistente, temporários próprios e nenhuma instalação incidental. Não rodar variantes em paralelo no mesmo `--basetemp`.

Parar a variante afetada e registrar: origem/hash incompatível; transmissão fora da política; custo no teto; documento com instrução que provoque ação; aprovação falsa; erro crítico silencioso. Corrigir no desenvolvimento, não apagar a tentativa. Falha de fonte externa pode permitir análise limitada das demais questões, nunca conclusão dependente sem apoio.

Cada pacote é unidade revisável, mas este documento não autoriza commit entre passos. Sem dependência de prazo/calendário inventado; avanço ocorre por aceitação e autorização, não por tempo decorrido.

## 12. Decisões que o titular precisa revisar antes da execução

1. Aprovar/ajustar o contrato analise-1 e o nível de análise esperado, incluindo os exemplos P01/P02.
2. Aprovar desenho do corpus, gabarito profissional, metas e experimento inicial; indicar quem fará a avaliação jurídica do benchmark.
3. Autorizar quais pacotes poderão ser implementados. Para EV-04 em diante: autorizar separadamente runtime/persistência, modelo, ferramentas, dados transmitidos e tetos de gasto.
4. Manter ou alterar expressamente os gates de uso material em incremento próprio; aprovação do plano não equivale a aprovação jurídica dos casos ou ativação das regras.

**Autorização posterior à preparação:** contrato/plano aprovados e EV-01 autorizada. Coleta de novo corpus, implementação de EV-02 e execução do piloto continuam pendentes de autorização; ver estado canônico no plano principal.

## Referências de desenho

[Avaliação técnica anterior](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/avaliacao-evolucao-2026-10-22/avaliacao.md>) e [snapshots de dez repositórios](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/avaliacao-evolucao-2026-10-22/repositorios.json>). Tecnologias ali descritas são candidatas e não dependências aprovadas. Para referências portáveis, ver [pdfplumber](https://github.com/jsvine/pdfplumber/tree/4c64b92d5caccd71c645e98e0fabb0c4dba7ff45), [Docling](https://github.com/docling-project/docling/tree/1ee1db0f648c4bd2d25146f5dd100d1b75d94d7d), [LangGraph](https://github.com/langchain-ai/langgraph/tree/9d68e5b3eb1a63027b05e9f0152149ea0284dcdb), [OpenAI Agents SDK](https://github.com/openai/openai-agents-python/tree/0dc4cf152bff1f50bdc0e41f28808563406545b2) e [Promptfoo](https://github.com/promptfoo/promptfoo/tree/c50f045172b983cbe2173666936e62e96bb506f7). Antes de futura adoção, reverificar compatibilidade, licença de componentes/modelos e disponibilidade.
