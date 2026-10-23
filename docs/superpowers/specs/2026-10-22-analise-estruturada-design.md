# Contrato da análise estruturada — analise-1

**Estado:** contrato e plano aprovados pelo titular em 22/10/2026; execução autorizada somente da EV-01. Este documento preserva o desenho aprovado; os detalhes executáveis estão no [contrato publicado](../../contratos/analise-v1.md). [Prioridades e estado canônicos](../../plano-principal.md). [Plano e piloto](../plans/2026-10-22-evolucao-analise-estruturada.md). Aprovação não inicia EV-02 a EV-06, APIs, modelos ou ativação de regras.

## 1. Objetivo e fronteira

Produzir uma análise estruturada dos documentos cíveis fornecidos, com profundidade argumentativa e fontes verificáveis, deixando ao profissional decisões jurídicas importantes e exceções materiais. O contrato descreve o produto desejado; não afirma capacidade já demonstrada.

A análise deve responder ao objetivo do caso e distinguir: o que foi pedido; o que cada interlocutor sustentou; o que os documentos registram; quais provas estão disponíveis; como os fundamentos se relacionam com a conclusão; o alcance do resultado; alternativas e lacunas relevantes. Inventário e resumo são insumos, não substitutos dessa entrega.

Escopo inicial: acórdão isolado e conjunto documental cível delimitado. “Autos fornecidos” nunca significa autos completos sem confirmação independente. Revisão contratual, biblioteca de minutas, cálculos, protocolo, monitoramento e novos ramos não integram este piloto. As oito skills continuam existentes; as 19 regras inativas e o NDA vazio permanecem como estão.

## 2. Entradas, artefatos e compatibilidade

Entradas possíveis: `matter.json`, extrações, inventários de peças e revisões anteriores, `facts.json`, `claims.json`, registro de fontes e QC existentes. Originais e casos reais permanecem fora do Git. Só fixtures públicas/sintéticas autorizadas entram em testes versionados.

A análise consumirá snapshots identificados por bytes/hash. A falta de um insumo não é suprida com ID fictício: registra limitação e restringe as conclusões dependentes. Acórdão que narra petição, perícia ou outro julgado não significa leitura do documento primário.

Saídas futuras: `derived/analise.json` e `derived/analise.md`, mais resultado de validação e manifesto da execução. São derivados novos; não sobrescrevem extrações nem alteram silenciosamente facts/claims. A versão publicada de cada saída é imutável; reexecução material cria outra revisão e aponta o hash anterior.

- Versão proposta: `schema_version: "analise-1"`, em artefato separado dos contratos legados.
- Preservar os enums/semântica de [dados](../../../shared/dados.md), [estados](../../../shared/estados.md) e [peças v1](../../contratos/pecas-v1.md). Não converter validação automática em `conferido` ou evento de ator humano.
- O fluxo legado, os modos `analise`/`fundamentada` e a aprovação de entregas conservam seus controles até uma futura mudança expressamente aprovada.
- A política técnica nova poderá emitir avaliação paralela para comparação. No piloto ela não libera o modo fundamentado recusado pelos gates atuais.
- Não publicar campos novos em `shared/dados.md` antes de implementar e validar a mudança aprovada.

## 3. Envelope e identidade

Campos obrigatórios propostos; listas e objetos têm as regras das seções seguintes:

| Campo | Forma e significado |
|---|---|
| `schema_version` | Constante `analise-1` |
| `analysis_id`, `matter_id` | IDs estáveis não vazios; `matter_id` corresponde à entrada de triagem |
| `revision`, `previous_sha256` | Inteiro ≥1; revisão 1 exige anterior nulo, revisão seguinte exige hash dos bytes anteriores e sequência +1 |
| `run_id`, `created_at`, `as_of` | Execução identificada; instante RFC3339 com fuso; data ISO de referência igual à triagem. Não substituem a data dos fatos |
| `objective`, `scope` | Objetivo específico; tipo `acordao_isolado` ou `conjunto_documental`; documentos incluídos, exclusões e limitações conhecidas |
| `inputs` | Manifesto: `artifact_id`, tipo, caminho relativo à raiz autorizada do caso, `sha256`; IDs únicos e hashes dos bytes efetivamente lidos |
| `execution_ref` | Caminho relativo e hash do manifesto de execução: versão do código/prompt, modelo quando usado, configuração e ferramentas. Sem segredos |
| `actors`, `references` | Interlocutores identificados e referências a fatos/proposições existentes, definidos abaixo |
| `overview`, `issues`, `requests`, `coverage` | Conteúdo analítico e cobertura |
| `research_tasks`, `findings`, `professional_decisions` | Pesquisa, achados técnicos/semânticos e decisões restantes |
| `technical_result` | Resultado calculável para revisão; não é aprovação de entrega |

IDs dos objetos novos seguem `[A-Za-z0-9_-]+` e são únicos dentro da análise. Referências ao legado carregam o namespace do artefato; `f001` de dois arquivos diferentes não é a mesma identidade. Caminhos absolutos, fuga por `..` e links simbólicos que escapem da raiz autorizada são recusados na futura implementação.

## 4. Referências e afirmações

`actors[]` contém `id`, `label`, `role` e referência à entrada de triagem ou à evidência que identifica o interlocutor. `role`: `parte`, `juizo`, `relator`, `colegiado`, `perito`, `testemunha` ou `outro`. Usar identificação mínima suficiente; `speaker.entity_ref` resolve um desses IDs. Interlocutor desconhecido permanece nulo, com motivo, sem associação por adivinhação.

Cada `references[]` contém exatamente `id`, `input_id`, `collection` (`facts` ou `claims`) e `item_id`. `input_id` resolve o `artifact_id` do manifesto de entradas. O artefato indicado tem hash válido, tipo correspondente e item existente. A resolução reaproveita a validação das fontes legadas, inclusive documento, trecho/localizador, peça/fragmentos quando exigidos e hashes externos disponíveis.

Observação documental ainda não representada exige primeiro um fato novo no formato legado, em derivado identificado; não inventar uma referência direta como substituto de fonte. Novas autoridades pesquisadas formam um `claims.json` derivado, com os estados existentes; o snapshot integra a revisão que o utiliza.

Toda afirmação analítica material usa a estrutura `Assertion`:

| Campo | Regra |
|---|---|
| `id`, `text` | Identificação e enunciado específico, passível de confronto |
| `nature` | `relato_documental`, `posicao_processual`, `inferencia_analitica` ou `limite`; não substitui `facts.kind` nem `claims.status` |
| `speaker` | `entity_ref` de parte/interlocutor identificado ou nulo com motivo; informa também se é fala própria, relato de terceiro ou transcrição |
| `basis_refs` | IDs de `references`; enunciado documental/posição exige 1+ apoio pertinente. Inferência exige premissas identificadas e justificativa sintética |
| `justification` | Obrigatória na inferência: síntese de como as referências sustentam a conclusão e suas ressalvas |
| `qualification` | `sustentada_no_escopo`, `parcial` ou `inconclusiva`; limita-se aos insumos analisados, sem equivalência com aprovação jurídica |
| `limitations` | Lista de restrições concretas. `parcial`/`inconclusiva` exigem motivo e efeito na conclusão |

Para `nature=limite`, ausência de documento é demonstrada pelo manifesto de entradas; registrar `missing_input` e não fabricar `basis_refs`. Não converter ausência no pacote em inexistência no processo.

A validação mecânica confere ligações e transcrições. Pertinência, suficiência e inferência exigem avaliação semântica separada. Números inventados de confiança são proibidos; não usar voto de modelos como certificação.

## 5. Conteúdo obrigatório da análise

### 5.1 Visão do caso e pedidos

`overview` contém contexto processual, objetivo, fase/posição do cliente, síntese do resultado e alcance. Cada componente material é uma `Assertion`. Sem informação suficiente, produzir limite específico; não preencher com generalidades.

`requests[]`: `id`, descrição, requerente, referências de origem, `issue_ids`, resposta localizada e efeito. Resposta usa `acolhido`, `rejeitado`, `parcial`, `nao_examinado` ou `nao_localizado`, com referências/motivo. Sentença narrada, decisão recorrida e acórdão atual ficam em registros distintos. Pedido subsidiário não desaparece em resumo do pedido principal.

### 5.2 Questões e encadeamento

Cada `issues[]` exige:

| Campo | Conteúdo |
|---|---|
| `id`, `question`, `importance`, `importance_reason` | Pergunta delimitada, importância `central`/`material`/`contextual` e efeito concreto no objetivo |
| `status` | `analisada`, `inconclusiva` ou `nao_examinada`; as duas últimas exigem motivo e próximo tratamento |
| `positions[]` | Interlocutor, argumento, referências e resposta/objeção. Quando a posição não estiver no pacote, registrar ausência em vez de inventá-la |
| `evidence[]` | Referências, papel favorável/contrário/contextual, origem primária/relatada e limitação. Relato de prova não vira a própria prova |
| `grounds[]` | Fundamentos do documento e autoridades, com distinção entre fundamento próprio e citação. Estado jurídico vem do claim resolvido |
| `assessment` | Justificativa verificável e sintética que conecta premissas, objeções, fundamentos e conclusão; não solicitar exposição de raciocínio interno do modelo |
| `preliminary_conclusion`, `alternatives[]` | Conclusão delimitada, consequências e alternativas relevantes. Não havendo alternativa pertinente, registrar motivo específico |
| `related_requests`, `research_ids`, `decision_ids` | Ligações existentes; listas vazias admitidas somente com motivo quando o componente for aplicável |

Todas as posições, fundamentos e conclusões são `Assertion` ou apontam uma `Assertion` existente. Referência inexistente e conclusão que usa somente a própria redação como fundamento são inválidos; o apoio deve resolver fatos/proposições dos insumos, não texto gerado pela própria análise.

### 5.3 Cobertura

`coverage[]` referencia `input_id`, `document_id`, `block_id` e, se houver, peça/seção e intervalo de caracteres. Cada bloco relevante do corpo fornecido tem tratamento `utilizado`, `contextual`, `excluido_com_motivo`, `ilegivel` ou `nao_examinado`; exclusão exige motivo e objeto analítico relacionado quando houver. Auxiliares/rodapés têm tratamento explícito, sem contagem falsa como análise de mérito.

Cobertura de blocos mede processamento, não suficiência jurídica. Cobertura de questões/pedidos/argumentos é medida contra o gabarito no piloto. `nao_examinado` e `ilegivel` não contam como lidos; excluir tudo com motivos genéricos não prova completude. Omissão relevante pode existir mesmo com 100% dos blocos contabilizados.

## 6. Pesquisa e revisão crítica

`research_tasks[]`: `id`, `issue_id`, pergunta, razão, termos permitidos, consultas/tentativas, fontes candidatas/examinadas, claim_refs, achados contrários, estado (`planejada`, `executada`, `limitada`, `dispensada`) e motivo/critério de parada. Fonte obtida depois do início da análise entra em novo snapshot identificado no manifesto.

Registrar separado: existência, acesso, fidelidade da transcrição, apoio à proposição e aplicabilidade. Autoridade não acessada continua não verificada; busca vazia não prova inexistência. Vigência atual e redação à época são dimensões distintas. Pesquisa remota depende de autorização/configuração; sem ela o relatório pode propor consultas e restringir conclusões.

Revisão crítica deve procurar omissões, atribuição indevida, objeções ignoradas e conclusões sem apoio. Cada achado indica alvo, motivo, fontes e tratamento. Apontamentos sem evidência não podem apagar conteúdo automaticamente. Conclusão revisada gera nova revisão; correções e divergências ficam rastreáveis.

## 7. Verificação técnica e intervenção profissional

`findings[]`: `id`, `code`, `category` (`integridade`, `leitura`, `atribuicao`, `cobertura`, `fundamentacao`), alvos, extensão, impacto, evidências e `action` (`registrar`, `reprocessar`, `restringir`, `decisao_profissional`). Impacto: `critico`, `material` ou `informativo`. Classificação precisa de motivo e regra/método versionados.

| Situação | Tratamento proposto |
|---|---|
| Hash/identidade incompatível ou referência quebrada | Bloquear a análise dependente e reprocessar; não pedir ao advogado que resolva falha de arquivo |
| Aviso de rodapé repetido, sem perda no trecho usado | Registrar automaticamente, sem impor conferência humana de todo o documento |
| OCR com valor ou dispositivo não legível | Tentar recuperação técnica limitada; persistindo, restringir a conclusão e formular exceção material |
| Autoria ambígua que altera a conclusão | Confrontar contexto/alternativas; encaminhar pergunta com trechos e impacto se persistir |
| Estratégia, tese controvertida ou suficiência probatória | Entregar análise e opções; destacar decisão jurídica profissional |

`professional_decisions[]`: `id`, `issue_id`, pergunta, razão jurídica/material, opções, recomendação preliminar quando possível, referências e consequência. Não incluir pedidos triviais solucionáveis pelos insumos legíveis. Não pedir aprovação de todas as seções como substituto de trabalho analítico.

`technical_result`: `integrity` (`valida`, `invalida`, `nao_verificada`), `review_readiness` (`apta`, `com_restricoes`, `reprocessar`, `bloqueada`), achados impeditivos e restrições. Integridade inválida prevalece sobre os demais resultados; falta material restringe as conclusões dependentes; não transferir falha técnica para mera “decisão profissional”. Regras propostas serão aprovadas antes de codificação.

O artefato não contém campo de aprovação profissional automática. Decisão/aprovação real continua no mecanismo separado existente, vinculada aos insumos aplicáveis. O relatório deve informar que está pronto para revisão, com restrições ou bloqueado, sem se anunciar como entrega liberada.

## 8. Apresentação ao profissional

Ordem obrigatória do Markdown: (1) síntese e alcance; (2) questões centrais, posições e conclusão preliminar; (3) pedidos e resultado; (4) provas, fundamentos e contraposições por questão; (5) limitações/pesquisa pendente; (6) decisões profissionais priorizadas; (7) fontes e cobertura técnica em apêndice.

Cada afirmação material permite abrir sua referência. Alertas operacionais resolvidos ficam no apêndice; impedimentos permanecem visíveis junto à conclusão afetada. JSON e Markdown usam os mesmos IDs e qualificações; não remover limitações no renderizador.

## 9. Exemplos de aceitação P01/P02

Exemplos derivados do pacote-03, sem nova aprovação material, novo parecer ou confirmação das peças primárias ausentes:

- **P01:** articular a alegação de ausência de comprometimento/habitabilidade (F05), o relato pericial e os danos descritos (F08–F09), os fundamentos e a indenização (F10), delimitando o alcance do parcial provimento (F12–F13). Separar condições de continuidade das obras, tutela e capítulos de indenização; não inferir reforma integral.
- **P02:** criar questões distintas para competência e má-fé (F04–F06, F12–F15); distinguir o resultado do processo dos precedentes transcritos (F07–F11). Não concluir procedência da cobrança a partir da decisão de competência; fontes citadas continuam transcrições até exame autônomo.

IDs Fxx são rótulos do pacote de revisão e precisam ser resolvidos ao snapshot real na futura fixture; não são aceitos como IDs globais fictícios.

## 10. Aceitação do contrato e decisões de desenho

Antes da implementação, revisar esta proposta e aprovar: campos/qualificações; contrato aditivo e preservação do legado; classificação técnica por finalidade; rubrica do piloto; limites de dados/custos da etapa agêntica. Aprovar o documento não ativa regras nem autoriza APIs, persistência ou publicação.

O contrato está suficientemente especificado quando: nenhum campo confunde fonte/apoio/aplicabilidade/aprovação; todos os vínculos e estados têm regra; dois exemplos positivos e cinco contraexemplos cobrem referências incompatíveis, fonte secundária, autoria ambígua, conteúdo parcial e falta de documento; a rubrica exige análise e não só preenchimento. Esses exemplos serão fixtures apenas na futura execução autorizada.

### Casos de contrato para revisão agora

São exemplos conceituais; fixtures e testes executáveis serão criados apenas na execução autorizada.

| ID | Entrada/comportamento | Resultado esperado |
|---|---|---|
| POS-01 | Acórdão e fatos/proposições identificados, pedidos e resultado relacionados aos trechos, conclusão preliminar limitada ao julgamento | Análise apta à revisão se sem achados impeditivos; nenhuma aprovação de entrega |
| POS-02 | Acórdão relata perícia ausente; análise distingue o relato, examina o argumento possível e explicita o limite da prova | Contrato íntegro, revisão com restrições nas conclusões dependentes; sem pedido para conferir todos os outros trechos |
| NEG-01 | Fato/claim aponta snapshot com hash incompatível | Integridade inválida; reprocessar, não pedir aprovação jurídica do hash |
| NEG-02 | Fonte secundária ou ementa isolada apresentada como confirmação plena do inteiro teor | Validação legada/semântica recusa a promoção; corrigir qualificação e restringir conclusão |
| NEG-03 | Ementa transcrita atribuída ao colegiado atual sem resolver a ambiguidade | Achado material de autoria; análise irrestrita não aceita. Resolver tecnicamente ou apresentar exceção delimitada |
| NEG-04 | Dispositivo ilegível ou questão central não examinada, com relatório anunciado como completo | Reprovar suficiência/aptidão irrestrita; preservar análise possível, marcar limitação e recuperar entrada quando viável |
| NEG-05 | Peça não fornecida declarada como lida ou conclusão sem base inventa seu conteúdo | Reprovar; distinguir documento ausente de inexistente e remover a afirmação não sustentada |
