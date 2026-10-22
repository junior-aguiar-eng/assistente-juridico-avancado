# ORG-05: validação integrada e ampliação do corpus

## Escopo e execução

Pedido de 22/10/2026: commitar ORG-04 e prosseguir com ORG-05. ORG-04 está no commit local `a3848b1c5443cc72d9a00346c5f661e69a52b558`. Codex permanece no worktree `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`. Sem push, instalação, ativação ou edição do checkout do Claude. A execução técnica inicial permaneceu sem commit; a autorização posterior do titular permite o fechamento da conferência P01/P02 e o commit local desta entrega. Prioridades e andamento somente no [plano principal](plano-principal.md).

Este é o plano executável e o registro da avaliação, subordinado aos critérios ORG-05 do plano principal. Arquitetura: reutilizar extração, proposta conservadora, validação do inventário e consumidores ORG-04; não ajustar o classificador aos casos de avaliação. Python e dependências existentes, sem APIs pagas ou novo modelo. As 19 regras continuam inativas.

## Etapas e arquivos

- [x] Registrar baseline externo de hashes, HEAD/branch/refs, 106 arquivos e seis metadados Claude. Congelar consumidores e proposta em `a3848b1` antes de observar os casos novos.
- [x] Acrescentar duas fixtures públicas oficiais em `tests/casos/org05/`, com manifesto, hashes, processo, coorte e modalidade de leitura. Processos de desenvolvimento e avaliação não podem coincidir; variações de leitura do mesmo processo permanecem na mesma coorte. Guardar metadados de coleta; PDF/HTML inesperado é falha, não caso avaliado.
- [x] Escrever testes RED em `tests/test_avaliar_pecas.py` para `scripts/avaliar_pecas.py`: separação de coortes, hashes, ausência, métricas de fronteiras/tipos/fusão/fragmentação/abstenção e leitura; comparar propostas a referências técnicas sem criar evento humano. Saídas por caso/processo/modalidade com denominadores; sem percentual jurídico ou média que esconda ausência.
- [x] Executar o fluxo real extração → proposta → integridade → triagem → facts/claims → cronologia → auditoria nos insumos disponíveis. Conferências propostas continuam propostas; a análise deve expor a pendência e o uso fundamentado deve recusá-la. Controle positivo de conferência permanece sintético e explicitamente separado dos casos reais.
- [x] Repetir a avaliação das oito skills com modelo, por revisão independente e evidência de comandos/artefatos, em diretórios externos próprios, com cenários normais e adversariais. Consumidores usam PDFs públicos reais; contratos/minutas usam os modelos sintéticos existentes e mantêm regras inativas. Não alegar validação contratual real.
- [x] Publicar resultados em `docs/avaliacao-skills-org05.md` e artefato de métricas sem texto pessoal. Executar testes pertinentes e suíte integral offline, revisão mecânica, dependências, diff e preservação por hashes; atualizar coordenação e plano. Não declarar encerrado critério que dependa de conferência humana ou corpus ausente.

## Interfaces e critérios

`scripts/avaliar_pecas.py` consome manifesto JSON e caminho explícito de raiz, retornando resultados por caso e métricas por coorte/modalidade. Cada caso fixa SHA-256, identificador de processo, modalidade e referência estrutural; a referência tem proveniência `modelo_tecnico`, `sintetico` ou `humano_identificado`. Referência do modelo não transforma limites/tipos em `conferido` e não habilita uso material. O diretório de saída precisa ser externo e novo; o avaliador não busca fontes nem sobrescreve resultados.

A comparação de fronteiras usará páginas físicas; fronteira dentro da página exige referência mais precisa ou fica sem avaliação fina, não será arredondada para produzir acerto. As métricas separam falsos cortes (fragmentação), cortes ausentes (fusão), tipo e abstenção. Zero denominador gera ausência de medição. Falha de extração ou arquivo ausente não conta como classificação correta. Métricas OCR são por trechos com referência textual disponível, sem tratar duas modalidades de um PDF como processos independentes.

Foco da revisão: vazamento entre coortes; gabarito gerado da própria previsão; OCR contado como nativo/aprovado; referências de peça perdidas na entrega; proposta ou saída do modelo promovida a evento humano. Gabaritos técnicos serão fixados por leitura do PDF e revisados independentemente antes da avaliação, sem copiar o resultado do detector.

## Evidências e limites

Diretório externo desta execução: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/org05-2026-10-22-ejd98q8d`. Os originais privados ORG-R07-PRIVADO/ORG-R10-PRIVADO continuam ausentes. Uma rodada com um modelo e poucos processos de um tribunal não demonstra generalização nem revisão jurídica. Corpus real completo de contratos, conferência humana dos inventários usados materialmente e eventual avaliação com segundo modelo exigem evidência própria. A confirmação estrutural P01/P02 está registrada separadamente ao final.

## Resultados observados

Os [dois PDFs novos e seus metadados](../tests/casos/org05/README.md) foram lidos por texto/PDFium e suas páginas de transição inspecionadas visualmente, antes da execução do detector. Outro agente conferiu independentemente a referência técnica: uma peça acórdão por PDF, embora o detector se abstenha do tipo. Naquela etapa o usuário respondeu **“Vou conferir depois; mantenha pendente”**; as referências e resultados históricos foram registrados como técnicos. Posteriormente, o titular confirmou **“P01/P02 revisados e aprovados”** e autorizou finalizar a pendência e commitar. O [registro de conferência](../tests/casos/org05/conferencia-humana.json) fixa PDFs/gabaritos e a declaração recebida; somente essas duas referências no manifesto atual passam a `humano_identificado`. Não foram criados eventos nos inventários propostos nem aprovada a aplicabilidade jurídica.

A [rodada congelada](resultado-org05-congelado.json) registra a base anterior às correções. O manifesto/avaliador exatos também estão preservados externamente. Os mesmos casos foram repetidos depois para regressão; esse resultado tem `fase=regressao_pos_avaliacao`, sem ser contado como novo holdout.

| Coorte/modalidade | Unidades/observações | Leitura e peças | Resultado e denominadores |
|---|---|---|---|
| Avaliação, nativo: P01/P02 | 2 processos, 2 observações | 16/14 páginas nativas; extração `ok`/`partial`; uma peça proposta em cada | Envelopes físicos correspondem em 2/2. Tipo identificado 0/2; abstenção 2/2. Nenhuma fronteira interna no gabarito: recall de cortes é 0/0, sem percentual. Nenhum corte extra observado |
| Desenvolvimento, nativo: R07 público | 1 processo, 1 observação | 12 páginas nativas, `partial`; uma peça proposta | Envelope 1/1; tipo identificado 0/1, abstenção 1/1. Fronteiras internas 0/0. Não é processo novo |
| Desenvolvimento, sem OCR: R10/Picos | 1 documento administrativo, 1 observação | `no_text`, uma página sem texto, nenhuma peça atribuída | Envelope 0/1; amostras 0/3. Integração por trecho não executada; não é classificação aprovada |
| Desenvolvimento, OCR: mesmo R10/Picos | Mesmo documento, outra observação | `partial`, `ocr_parcial`, nenhuma peça atribuída | Envelope 0/1; três expressões recuperadas em 3/3. Sem medida de fidelidade integral/CER; integração material não executada e nenhuma promoção da leitura |

São **quatro unidades, cinco observações: três processos judiciais e um ofício**, incluindo somente dois processos novos. A comparação de tipos é condicionada ao envelope exatamente correspondente; não estima precisão universal. Referências ou previsões com peças na mesma página sem offsets suficientes têm denominadores finos zerados. Ausência/falha de arquivo não entra como acerto, e dois nomes normalizados do mesmo processo não aumentam o número de processos.

Nos três casos nativos, integridade, triagem e análise foram exercitadas com pendências visíveis; cronologia de trabalho conserva o vínculo. Validação fundamentada e G16 fundamentado recusaram o uso proposto. Isso comprova a proteção de uso, não a classificação ou conferência humana. Nas skills, claims/exposição/status também foram exercitados; ver [segunda avaliação](avaliacao-skills-org05.md).

## Correções encontradas durante a avaliação

- **Colisão multidocumento:** ID de inventário passa a incluir o documento em pacotes com vários documentos; o caso único preserva a identidade anterior. RED reproduziu dois inventários com o mesmo ID; pós-correção, a revisão repetiu nativamente o pacote real, sem renomear IDs e sem eventos humanos.
- **Anexo redline:** relatório nativo com `issues` como caminho deixa de ser confundido com segundo conjunto de apontamentos; segue vinculado ao QC por hash. JSON malformado e regra inativa continuam reprovando. RED reproduziu o aborto com um relatório realmente produzido pelo script, e nova execução independente aceitou o pacote completo mantendo `entregavel=false`.
- **Métricas do avaliador:** revisão reproduziu propostas intrapágina contadas como 2/1 e grafias equivalentes do mesmo processo contadas duas vezes. Testes falharam antes da correção e passaram depois; sondas independentes confirmaram denominadores finos zerados e um processo/duas observações. Nenhum desses reparos ajustou o detector de tipos/fronteiras aos acórdãos.

## Verificações

- RED inicial do avaliador: 17 falhas por funcionalidade ausente; primeira implementação com 17 aprovados. Casos adicionais de cobertura/caminho/revisão foram reproduzidos e corrigidos.
- Rodada focada de auditoria documental, redline, proposta, ORG-04 e avaliador: **139 aprovados em 72,28 s**, antes dos dois testes adicionais finais de métricas. Avaliador final: **22 aprovados em 5,81 s**.
- Revisão final independente: dois P2 de métricas reproduzidos e corrigidos, sem achados materiais pendentes; controles positivos e negativos das correções de fluxo preservados.
- Portabilidade: dois testes reproduziram a dependência de caminhos Windows e de hashes CRLF/LF. Caminhos de unidade Windows são recusados também na semântica Posix; o manifesto atual normaliza somente código para LF, mantendo hashes exatos dos insumos. Testes de saída usam temporários externos mesmo quando a CI guarda o `tmp_path` no checkout. Avaliador final: **24 aprovados em 5,02 s**; isso não é execução da CI Linux.
- Controle final de caminhos: referência enraizada Windows reproduzida em RED e recusada após correção; junctions não permitem originais/código fora da raiz. Revisão independente confirmou oito caminhos inválidos recusados e três normais aceitos sob semânticas Windows/Posix, além das duas junctions. **27 testes do avaliador aprovados em 7,20 s**, sem achados materiais pendentes após as sondas.
- Oito skills PRONTA, sem alertas; `pip check` sem requisitos quebrados. Duas rodadas integrais foram interrompidas para fechar portabilidade e caminhos; não contam como aprovação. A rodada definitiva `integral-validada` terminou com **1014 aprovados, 5 ignorados, zero falhas/erros em 891,51 s**, saída zero e JUnit conferidos. Python 3.14.6/Windows, `PYTHONUTF8=1`, `JURIS_REDE=0`, temporários externos e código/testes preservados por hashes desde o início. Ignorados: duas operações de rede, Docling Parse opcional ausente e os dois originais privados ORG ausentes. Não é CI remoto ou execução Linux.

## Fechamento da conferência humana

Em 22/10/2026, o titular revisou e aprovou P01/P02 nesta conversa e pediu a finalização e commit local. O registro vinculado confirma uma peça acórdão por PDF (P01: páginas 1–16; P02: 1–14), com seções internas preservadas. Identifica o revisor pelo papel e origem da declaração, sem autenticação externa ou assinatura digital. Os gabaritos não foram ajustados após a previsão; somente a proveniência da conferência mudou. Os resultados congelados permanecem históricos.

A pendência de gabaritos está encerrada e a ORG-05 **concluída no escopo assistido medido**. Permanecem as abstenções do detector, inventários propostos e originais privados ausentes; não há liberação de autos completos, regras, instalação ou produção. Contratos reais, fidelidade integral de OCR, maior diversidade de processos e segundo modelo não foram validados nesta rodada. A fase 5 e os demais gates do plano principal permanecem abertos.

Preservação ao fim da execução técnica anterior: 106 arquivos e seis metadados Claude, 163 arquivos Codex preexistentes fora do escopo, HEAD/branch e outras branches/refs remotas preservados; índice vazio e 19 regras inativas. São sete arquivos modificados e dez novos. `preservacao-final.json` e `org05-final.patch` ficam no diretório externo: patch de texto/PDFs verificado sem aplicação ou staging (`--no-textconv` na geração dos PDFs). Naquele momento apenas ORG-04 havia recebido commit. O fechamento posterior inclui a entrega ORG-05 no commit que contém este registro, sem push; verificações próprias de fechamento são registradas abaixo.

Verificação do fechamento: **151 testes aprovados, zero ignorados/falhas em 54,44 s**, abrangendo avaliador, proposta, auditoria documental, redline e consumidores ORG-04. O controle com PDF real confirma que o gabarito humano não confere o inventário proposto nem libera uso material. Oito skills PRONTA na revisão mecânica. A primeira chamada usou nome incorreto do teste redline e não executou testes; foi corrigida antes desta rodada válida.

A suíte integral de 1014 aprovados/5 ignorados não foi repetida neste fechamento: saída/JUnit anteriores foram conferidos e todos os scripts permanecem byte a byte iguais aos daquela execução. Somente `tests/test_avaliar_pecas.py` mudou desde então, para o registro real de aprovação e controles de vínculo/revisor; foi executado integralmente na rodada de 151 testes. Hashes confirmam 163 arquivos Codex preexistentes fora do escopo, 106 arquivos/seis metadados Claude, resultados congelados e 19 regras inativas preservados. Escopo final: sete arquivos existentes modificados e onze novos. Logs, JUnit e conferências próprias ficam em `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/org05-fechamento-2026-10-22-1xcjbkis`. O commit local altera apenas a branch Codex; sem push ou liberação da fase 5.
