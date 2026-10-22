# Fase 5 — evidências para liberação assistida

Base `910b11e87e92e153610463fdc6e5cd167f5d3968`, branch `codex/organizacao-colaboracao`, 22/10/2026. O pedido autoriza executar a fase 5 do [plano principal](plano-principal.md); não autoriza ativar regras, publicar, instalar ou aprovar entregas em nome de pessoa. Este documento registra verificações; prioridades e andamento permanecem no plano principal.

## Escopo de aceitação

Organização assistida de documentos cíveis fornecidos: inventário, leitura com cobertura explícita, referências de peça/bloco/trecho, mapa de fatos, cronologia de trabalho e auditoria. A pesquisa preserva a separação entre localizar, ler, verificar apoio e avaliar aplicabilidade. Contratos e minutas permanecem com validação mecânica e controles sintéticos; 19 regras inativas e pacote NDA vazio.

P01/P02 possuem gabaritos estruturais humanos registrados, uma peça acórdão nas páginas 1–16 e 1–14. A geração de inventário continua proposta; a confirmação do gabarito não resolve automaticamente atribuição, offsets, seções, leitura ou aprovação de uso material. A aceitação não criará eventos humanos para obter um resultado positivo.

## Execução prevista

1. Conferir baseline, regras, ambiente e integridade dos insumos.
2. Reexecutar o manifesto atual de avaliação em saída externa nova, conservando abstenções e verificando bloqueios reais. Conferir compatibilidade e casos antigos com a suíte existente.
3. Reexecutar a suíte integral offline, revisão mecânica das oito skills e integridade de dependências. Conferir versões/licenças nos metadados locais; não instalar ou adotar novos motores/modelos.
4. Documentar fluxo reproduzível e atualização explícita dos artefatos, sem alterar históricos. Corrigir descrições atuais desatualizadas no README e completar avisos das dependências existentes.
5. Submeter o diff e as evidências a revisão independente e conferir preservação final.

Evidências externas: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/fase5-2026-10-22-a7bu7lxi`. A validação técnica local foi concluída, com resultados abaixo. CI remoto, Linux/outras versões Python, inspeção no Word, contratos reais e originais privados ausentes não foram executados.

## Resultados de aceitação local

O manifesto ORG-05 foi repetido em destino externo novo, com verificação dos hashes do produto e dos insumos. As cinco observações terminaram com integridade dos inventários, sem promover propostas ou criar eventos humanos. São quatro unidades: três processos judiciais (somente dois novos) e um ofício em duas modalidades. Repetição do mesmo corpus é regressão, não nova avaliação independente.

| Casos | Resultado | Restrição preservada |
|---|---|---|
| P01/P02 | Envelopes 2/2; identificação de tipo 0/2, abstenções 2/2; P01 `ok`, P02 `partial` | Referências humanas estruturais, inventários ainda propostos; análise com avisos, uso fundamentado/G16 recusados |
| R07/TJMG público | Envelope 1/1, identificação de tipo 0/1; `partial` | Mesmo bloqueio de uso; não é o ORG-R07-PRIVADO |
| R10/Picos sem OCR | `no_text`, amostras 0/3, nenhuma peça atribuída | Integração por trecho não executada; não é classificação correta |
| Mesmo R10/Picos com OCR | `partial`, amostras 3/3, nenhuma peça atribuída | Sem fidelidade integral/CER ou uso material; não é o ORG-R10-PRIVADO |

O fluxo CLI foi também exercitado com P01: triagem de peças → validação da análise → cronologia → auditoria → status. Oito comandos conferidos, incluindo duas recusas esperadas no modo fundamentado e a detecção de alteração posterior em cópia própria do inventário. Originais e evidências de aceitação não foram alterados. `liberado_para_uso=false` em todos os estados observados. Na primeira sonda, esperou-se incorretamente saída 1 de `status` após alteração; o contrato existente retorna 0, lista `alterados` e mantém a recusa de uso. A sonda foi corrigida e repetida em nova pasta, sem mudar o produto. Esse detalhe consta do roteiro para evitar interpretar saída zero como aprovação.

Os controles positivos de uso conferido são sintéticos e estão identificados como tais em `tests/test_org04.py`; não representam conferência de documentos reais. O fluxo legado e a integração com inventários são separados. A suíte cobre recusa de referência incompatível, alteração de extração/inventário/original, revisão sem bytes anteriores, atribuição ambígua, OCR e alteração posterior do pacote; esses testes foram aprovados na rodada integral abaixo.

## Cobertura efetiva e capacidades recusadas

| Área | Cobertura disponível | O que não está demonstrado |
|---|---|---|
| Acórdãos nativos | Casos públicos STJ/STF/TJMG; dois novos gabaritos humanos na ORG-05 | Reconhecimento automático universal de tipos ou generalização para autos completos |
| Sentença, peças consecutivas e cortes intrapágina | Controles sintéticos; evidência histórica privada separada | Reexecução dos dois originais privados ausentes nesta máquina |
| Petições e demais classes do contrato v1 | Petição sintética e controles do contrato/inventário; taxonomia de organização | Corpus real suficiente por classe; enumeração de um tipo não comprova seu detector |
| OCR | Ofício público e controles sintéticos; seis amostras privadas históricas registradas | Transcrição integral conferida, fidelidade de nomes/datas/dispositivo ou aprovação da leitura |
| Contratos e preenchimento | Pré-checagem, dados, redline e auditoria mecânicos em controles sintéticos | Validação contratual real ou liberação jurídica; 19 regras inativas e NDA vazio |
| Pesquisa/verificação | Pontes existentes e documentos fornecidos, com fontes/pendências rastreadas | Nova estabilidade de rede, inexistência por busca vazia, fonte oficial integral por mero link |

Transcrições dos casos novos ainda podem chegar com `is_quote=false`; a leitura contextual do modelo foi necessária na ORG-05. Alertas e controles não provam verdade do fato, autoria de todo trecho nem relação semântica entre fonte e proposição. Ausência de inventário e parâmetros mantém o fluxo legado por compatibilidade; não o apresentar como aceitação de autos completos. Não houve nova avaliação entre modelos nesta fase; a segunda avaliação das oito skills é a da ORG-05, com repetições nativas dos defeitos encontrados. Os scripts e as skills permanecem idênticos aos da base.

## Ambiente, licenças e custo

Python 3.14.6/Windows, UTF-8, `JURIS_REDE=0`, bytecode/cache desativados e temporários externos próprios. `pip check` retornou sem requisitos quebrados; as dez dependências diretas de execução e duas de desenvolvimento coincidem com os arquivos fixados. Licenças declaradas conferidas nos metadados locais, sem instalação nova ou parecer de redistribuição. Oito skills PRONTA, zero ATENCAO/PREOCUPACAO_MATERIAL na revisão mecânica, sem equivaler a revisão jurídica ou avaliação de segurança.

Tesseract com `por` disponível; Docling Parse continua opcional/experimental fora do ambiente principal. Nenhum motor, modelo, API paga ou infraestrutura foi adotado. Os scripts locais não fazem chamadas de geração por API; modelo, dados e custos da conversa são próprios da sessão e não foram homologados para inferência local ou comparados entre famílias. [Roteiro de configuração, migração e uso](uso-assistido.md). As instruções de migração não alteram arquivos automaticamente.

## Critérios e decisão de liberação

Esta matriz aplica os critérios existentes, sem reduzir o escopo por declaração:

| Critério da seção 7 do plano | Evidência e limite |
|---|---|
| ORG-01 a ORG-05 | Concluídos no recorte assistido medido; confirmação dos gabaritos P01/P02 preservada |
| Fluxo completo com conferência humana material | Cadeia técnica exercitada; positivo conferido somente sintético. Inventários reais continuam propostos. **Não encerrado para uso material** |
| Falhas conhecidas não aceitas silenciosamente | Casos de proposta/OCR/atribuição expõem avisos ou bloqueios. A verificação semântica continua assistida e não é certificada pelo script |
| Suíte relevante e completa | **1019 aprovados, 5 ignorados, zero falhas/erros**, saída zero e JUnit conferidos; privados ausentes não contados como validados |
| Segunda avaliação das skills com documentos reais | Executada na ORG-05, em oito skills/16 cenários, documentos públicos reais nas skills de autos/pesquisa/auditoria e sintéticos nas contratuais; não é validação jurídica integral |
| Compatibilidade e migração | Controles legados/integrados na suíte; atualização explícita documentada, sem migrador geral ou mudança de originais |
| Licenças, modelos, custos e configuração | Distribuições existentes conferidas; sem nova adoção, custo de API ou promessa de inferência local; avisos atualizados |
| CI da revisão publicada | **Não executado:** sem autorização de publicação/push. CI histórico não valida esta revisão |

A fase 5 **não está encerrada como liberação material ou publicada**. Concluir a validação técnica local não autoriza marcar o fluxo real conferido por pessoa ou CI remoto como aprovados. A confirmação estrutural de P01/P02 não será solicitada novamente; a pendência é a conferência dos inventários/trechos realmente utilizados e a aprovação da entrega correspondente, além da etapa remota quando autorizada. Não criar aprovação pelo agente, ativar regras, publicar ou instalar para contornar esses gates.

## Suíte integral e preservação

Rodada completa `integral`: **1019 aprovados, 5 ignorados, zero falhas/erros em 766,98 s** (770,20 s do runner). Código de saída zero e 1024 casos no JUnit XML conferidos. Ignorados: dois testes de rede desativados por `JURIS_REDE=0`, Docling Parse opcional ausente no ambiente principal e os dois originais privados ORG-R07/ORG-R10 ausentes. Os 12 casos locais de regressão, os controles positivos/negativos de inventário e a compatibilidade legada foram exercitados; isso não confere juridicamente os gabaritos. A configuração efetiva de pytest é `pytest.ini`, com `--basetemp` externo explícito nesta execução.

Hashes confirmam scripts e testes idênticos desde o início da suíte e nenhum arquivo de produto/skill/regra/fixture modificado. Permanecem 177 arquivos Codex preexistentes fora do escopo, 106 arquivos e seis metadados Claude, HEAD/branch/refs e índice vazio intactos; 19 regras inativas. Escopo final: quatro documentos existentes modificados e dois novos. UTF-8, whitespace e destinos dos links locais conferidos; diff sem erros e patch completo verificado por `git apply --reverse --check`, sem aplicar ou stagear. Nenhum commit, push, instalação ou publicação.

Revisão independente somente leitura não encontrou P1/P2 no escopo documental. Encontrou um P3: o exemplo pós-aprovação precisava fornecer também o caminho de `aprovacao.json` ao `status`; o código existente foi conferido e o roteiro corrigido. Não foi criada aprovação para testar esse exemplo. Os comportamentos excluídos da revisão foram mantidos como limites: nova auditoria histórica integral, correção jurídica/semântica, contratos reais, OCR integral, privados ausentes, Word, outros ambientes, rede e operações externas.

Logs/JUnit/saída do runner, aceitação, oito CLIs, metadados de licenças, revisão e preservação ficam no diretório externo. `pacote-revisao-material.md` liga PDFs, extrações, inventários e QCs por hash para uma eventual conferência específica; não contém aprovação, não corrige inventários e não reabre a confirmação estrutural humana já recebida.

## Autorização posterior de integração

Após a validação local, o titular autorizou “commit, push, pr e merge após”. A integração da branch Codex será destinada explicitamente a `main`, com merge condicionado à revisão da proposta e à CI da revisão publicada. A conferência humana de uso material e as 19 regras inativas continuam inalteradas. [Registro F5-I01](COORDENACAO.md) e evidências de integração em `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/integracao-fase5-2026-10-22-gr45seb6`; os resultados de ausência de publicação acima descrevem a etapa local anterior.
