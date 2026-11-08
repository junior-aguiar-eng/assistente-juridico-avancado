# F5-R01 — pacote de revisão material P01/P02

Preparação autorizada pelo titular após a integração da PR #5. Base local `3ab28e211641acb8fe75da5152fa0235e25fbd4d`, worktree Codex e branch `codex/organizacao-colaboracao`. Não é encerramento da fase 5 nem aprovação de entrega.

## Acesso à versão revisável

Pasta externa da rodada: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx`. Pacote corrente: `pacote-03`.

- [Guia de revisão](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx/pacote-03/LEIA-ME.md>) e [HTML](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx/pacote-03/LEIA-ME.html>).
- [P01 — trecho, afirmação e referência](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx/pacote-03/ORG05-P01/revisao.html>): 13 afirmações, 11 grupos de atribuição, 16 páginas.
- [P02 — trecho, afirmação e referência](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx/pacote-03/ORG05-P02/revisao.html>): 15 afirmações, 10 grupos de atribuição, 14 páginas.
- [Formulário em branco](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx/pacote-03/respostas-revisao.md>) e [manifesto de integridade](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx/pacote-03/MANIFESTO.json>).
- [ZIP completo](<C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/p01-p02-revisao-uxiaaesx/P01-P02-revisao.zip>): 89 arquivos, manifesto/CRC conferidos, SHA-256 `373c61aa861897816b8928729f9adcc476c076963f037501b7a0e90c7fe868df`.

Cada caso contém cópia íntegra do PDF público, extração derivada, inventário e snapshot, fatos, matriz de revisão, atribuições, cronologia, mapa Markdown, revisão crítica e QC nos dois modos. As 30 páginas renderizadas permitem conferir contexto, cabeçalhos e transcrições, inclusive passagens não selecionadas. Cópias anteriores ficam em `historico/`, com os mesmos bytes. O script específico `preparar.py`, as seleções e os testes da rodada ficam na pasta externa; não integram o detector do produto.

## Correções e proveniência

Não houve alteração nos scripts, detectores, contratos, regras, fixtures ou dependências do projeto. As correções são propostas técnicas específicas de dados, não ajustes ao detector sobre o corpus de avaliação.

1. **Tipo e organização:** nova proposta de uma peça `acordao`, coerente com o gabarito estrutural já aprovado, e seis seções por caso. Limites, tipo e seções continuam `proposto`; nenhum evento humano foi criado.
2. **Atribuição:** marcas de citação corrigidas na extração derivada após inspeção contextual. No P01, sentença, tutela, perícia e doutrina não são conclusões próprias do relator. No P02, as ementas internas são precedentes transcritos; o voto próprio retoma em `b0089`, página 12. Súmula e dispositivo do processo atual não são precedentes externos.
3. **Avisos anteriores:** os dois códigos conhecidos foram tratados individualmente, não removidos dos registros históricos. `cabecalho_rodape_removido`: texto condensado permanece auxiliar e não sustenta as afirmações selecionadas. `secao_aninhada_ambigua`: limites das três transcrições do P02 identificados tecnicamente e apresentados ao humano. O registro completo de antes/depois e dos avisos permanece em `correcoes-tecnicas.json` e `run.revisao_tecnica`; nenhuma nova remoção textual.
4. **Cobertura:** P02 conserva `partial`, com lacuna ligada ao `document_id`, corrigindo a falha de cobertura silenciosa da aceitação mecânica. Peças/provas primárias e precedentes autônomos ausentes continuam lacunas; a leitura secundária não passa por leitura dos originais.
5. **Fatos e datas:** as observações mecânicas foram substituídas por afirmações efetivas sobre o conteúdo dos acórdãos, separando ato documentado, alegação relatada e citação. Datas de julgamento/publicação são distintas; a fiscalização narrada do P01 é alegação. Não há cálculo de prazos nem datas de precedentes misturadas à cronologia do processo atual.

Texto de todos os blocos, IDs, páginas, localizadores e `text_sha256` permanecem idênticos à extração anterior. Mudança dos metadados/caminho/proveniência implica novos bytes de extração e **nova identidade de inventário**, conforme o contrato v1; nenhuma referência antiga foi remapeada silenciosamente e nenhuma aprovação foi transportada.

## Estado dos gates

| Caso | Análise | Fundamentada | Uso liberado |
|---|---|---|---|
| P01 | `revisao_pronta`, faixa `mista` | `bloqueado`, faixa `nao_entregar` | `false` |
| P02 | `revisao_pronta`, faixa `mista` | `bloqueado`, faixa `nao_entregar` | `false` |

Erros materiais restantes: `pecas_limites_nao_conferido`, `pecas_tipo_nao_conferido`, `pecas_secao_nao_conferida` e `pecas_limite_incerto`, todos ligados à conferência humana ainda pendente. Os alertas de `trecho_em_citacao` permanecem visíveis. Integridade do inventário, presença dos trechos, cobertura com lacunas, originais, cronologia e aviso dos relatórios foram conferidos. Isso não certifica semântica, autoria humana, vigência ou aplicabilidade jurídica.

## Conferência a receber

O responsável deve revisar os recortes/atribuições desta versão, os IDs P01-F01–F13 e P02-F01–F15 com suas fontes adicionais, os 21 grupos de atribuição e as ressalvas. O formulário aceita respostas parciais, correções e exclusões. Não se pede nova aprovação do gabarito estrutural de uma peça por PDF.

Somente após receber conferência real: registrar a revisão correspondente conforme o contrato, atualizar referências e repetir auditoria fundamentada. A aprovação final da entrega continua sendo ato pessoal posterior no terminal. Não apresentar aprovação do QC de análise como solução para o bloqueio material; não criar `aprovacao.json` ou confirmar pelo responsável.

## Verificações desta rodada

- 14 testes próprios do pacote aprovados: PDFs/snapshots intactos, conteúdo dos blocos preservado, referências/offsets/páginas, comparação dos trechos com o texto ordenado visualmente do PDF, datas, atribuições, 30 imagens e links locais, ausência de aprovação/eventos humanos, recusas de referências erradas e detecção de alteração em cópia temporária própria.
- 16 passos CLI conferidos no ambiente isolado já utilizado pelo projeto, incluindo validação dos dois inventários, fatos, cronologias, auditorias e status; recusas esperadas registradas separadamente. Oito skills `PRONTA`, sem alertas materiais na revisão mecânica.
- A primeira tentativa da suíte usou Python global sem `rfc3339-validator`, reproduziu falha de ambiente no caso de instante sem fuso e apresentou outras falhas de decodificação/CLI. A tentativa de interrupção da sessão não encerrou o subprocesso: o resultado final real foi 945 aprovados, 70 falhas, 7 ignorados e 2 erros, saída 1. Logs/JUnit completos preservados em `tentativa-python-global/`; não é contado como validação aprovada. Nenhum requisito ou teste foi alterado para ocultá-la. A rodada correta usa o ambiente isolado anterior, UTF-8, `JURIS_REDE=0`, sem instalação.
- Revisão independente somente leitura: sem achados P1/P2/P3 no escopo; 28 afirmações/fontes e 88 hashes do manifesto conferidos, 111 links locais válidos. Inspeção visual focada P01 pp.12–15 e P02 pp.9–13, sem aprovação humana ou validação jurídica externa.
- Suíte integral no ambiente isolado: **1019 aprovados, 5 ignorados, zero falhas/erros em 846,08 s** (848,15 s do runner), código zero e 1024 casos no JUnit conferidos. Ignorados: duas consultas de rede desativadas, Docling Parse opcional ausente e dois originais privados ausentes. Os scripts/testes permanecem idênticos desde o início dessa rodada. Logs e JUnit em `suite-ambiente-isolado/`.
- As quatro auditorias foram repetidas por CLI no ambiente isolado e comparadas com as do pacote: resultados, gates, pendências e hashes idênticos, exceto o horário de geração. Validação mecânica não é aprovação humana.
- Preservação final: 181 arquivos Codex preexistentes fora do escopo, 107 arquivos e seis metadados Claude, HEAD/branch, índice vazio e 19 regras inativas intactos. Somente dois documentos existentes e dois novos no worktree; nenhum arquivo do produto, teste, fixture ou skill modificado. Diff sem erros de whitespace.
- A prévia HTML no navegador não foi executada: a política da ferramenta bloqueou URLs `file:`. Estrutura/links/âncoras/imagens foram verificados sem navegador; imagens dos PDFs inspecionadas. A versão Markdown permanece disponível para leitura no Codex.

Sem consultas externas, commit, push, instalação ou ativação. Os dados de casos e saídas ficam fora do Git; as alterações locais versionáveis são somente documentais. A fase 5 permanece aberta para a conferência material e aprovação humana correspondentes.
