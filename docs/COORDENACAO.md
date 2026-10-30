# Coordenação entre Claude e Codex

Registro inicial: 18/10/2026. Esta preparação organiza o trabalho; não inicia as correções ou expansões listadas abaixo.

## CL-CODEX — push do `785d4ce` pelo Codex e conflito pendente, 30/10/2026

- O titular informou que o Codex enviou o commit `785d4ce` ("feat: validar e renderizar análise estruturada"). Conferido pelo Claude no GitHub: `origin/codex/organizacao-colaboracao` está em `785d4ce`, sobre a base `3ab28e2` (PR #5); é o único commit da branch que o `main` não tem. Isso substitui a pendência de CL-FECH ("só no worktree do Codex"). Não há PR aberto para ele.
- Conteúdo, por `git show --stat`: 9 arquivos, 3.882 linhas: `scripts/analise_estruturada.py`, `docs/contratos/analise-v1.md` e `.schema.json`, `tests/casos/analise_contrato/exemplos.json`, `tests/test_analise_estruturada.py`, documentos de especificação e alterações em `docs/COORDENACAO.md` e `docs/plano-principal.md`. O Claude não revisou nem executou esse código.
- Merge simulado contra o `main` (`d81f8b4`, `git merge-tree`, sem alterar nada): **um conflito**, em `docs/plano-principal.md` (o `main` passou para a revisão 15 em 30/10/2026: 21 regras inativas e NDA com 2 regras). `docs/COORDENACAO.md` mescla sem conflito; não há conflito em código.
- Responsável pela resolução e pelo PR: Codex, no worktree dele; o Claude não tocou na branch. A resolução deve preservar o texto do `main` sobre as 21 regras (19 de Código Civil/LGPD e 2 de NDA, todas inativas) e acrescentar o que o commit do Codex introduz. Merge só com CI verde e revisão, por decisão do titular.

## CL-PERGUNTAS — perguntas de revisão reescritas como rascunho, 30/10/2026

- Pedido autorizado pelo titular, opção "reescrever perguntas, inativas", sobre o parecer registrado em CL-PARECER. Responsável: Claude; branch `claude/perguntas-regras-rascunho`.
- Alterado: `pergunta_de_revisao` de 17 regras (7 do Código Civil e as 10 da LGPD); `civ-473`, `civ-598` e as 2 de NDA não foram alteradas, em `scripts/regras.py` e nos JSON de `rules/br/`; `pendencias_de_fonte` dos pacotes `lgpd` e `servicos_saas`, antes vazias, passam a registrar o que ficou de fora (resoluções da ANPD não lidas na fonte oficial, art. 19 como fonte de `lgpd-18`, escopo B2B/CDC, texto do Código Civil ausente do repositório, marcação de link no texto literal de `lgpd-7` e `lgpd-11`).
- Não alterado: `status` (todas as 21 **inativas**), `revisao` (vazia), `nota` ("rascunho do mantenedor técnico") e texto literal das fontes. Nenhuma regra foi ativada. As perguntas seguem o parecer, que não tem autor identificado, e continuam sujeitas à revisão do titular; o Claude não as validou juridicamente.
- Limite: a limpeza do texto literal de `lgpd-7` e `lgpd-11` (marcação de link) exige alterar a extração em `regras.py` e regerar o pacote; ficou como pendência, não feita aqui.
- Verificação: `gerar` reproduz byte a byte `lgpd.json` e `nda.json` a partir das fontes do repositório; `validar` sem erros (21 regras); 82 testes aprovados nos módulos que tocam regras. O pacote do Código Civil não pôde ser regerado (compilado ausente): as perguntas dele foram editadas no JSON e em `regras.py` em paralelo. Suíte integral não executada localmente.

## CL-PARECER — decisões propostas para as 21 regras, 30/10/2026

- Entrada: o titular anexou um "parecer jurídico objetivo" sobre as 21 regras. O arquivo **não identifica o autor** e traz resíduos de rascunho; é registrado como **insumo externo**, não como revisão: nenhuma regra recebeu `revisor`, `data` ou `observacao`, e **nenhuma foi ativada ou alterada**. A ativação continua exigindo o revisor identificado pelo titular (nome completo, data, observação), por PR. Responsável por este registro: Claude, só documentação.
- Contagem corrigida: o parecer traz três totais incompatíveis ("15/4/2" no início, "15/2/1" na seção 4 e uma tabela final). Somando as decisões regra a regra: **1** ativar como está, **17** ajustar e ativar, **2** manter inativas, **1** descartar (total 21). Valem estes números.
- Decisões propostas pelo parecer, por regra (proposta; não é ativação):

| Decisão proposta | Regras |
|---|---|
| Ativar como está | `civ-473` |
| Ajustar a pergunta e ativar | `civ-412`, `civ-413`, `civ-421a`, `civ-422`, `civ-423`, `civ-424`, `civ-478`, `lgpd-7`, `lgpd-11`, `lgpd-18`, `lgpd-33`, `lgpd-37`, `lgpd-39`, `lgpd-41`, `lgpd-42`, `lgpd-46`, `lgpd-48` |
| Manter inativa | `civ-598` (enquadramento de SaaS no regime típico de serviços), `pi-195-xi` |
| Descartar | `pi-195-xii` (a tipificação legal subsiste sem previsão contratual) |

- Escopo proposto: pacote `servicos_saas` prioritariamente B2B, com alerta de incidência do CDC em B2C; LGPD em B2B e B2C quando houver tratamento de dados pessoais; arts. 207 e 209 da Lei 9.279/1996 como fundamento civil complementar, sem exigência automática de cláusula; sem prazo universal de sigilo; foro fora do pacote de NDA.
- Conferido pelo Claude nesta data: o art. 19 da LGPD (resposta simplificada imediata ou declaração completa em até 15 dias) consta do texto compilado já guardado em `tests/casos/regras_fontes/lgpd_compilado.md`. A Resolução CD/ANPD nº 15/2024 (24/04/2024) fixa 3 dias úteis para comunicar incidente, segundo fonte secundária (escritório de advocacia), não o texto oficial. Existência das Resoluções CD/ANPD nº 18/2024 (encarregado) e nº 19/2024 (transferência internacional) apareceu em resultados de busca; o texto oficial não foi aberto. A Resolução CD/ANPD nº 2/2022 não foi verificada.
- O que bloqueia a ativação das 17 "ajustar e ativar": reescrever cada pergunta de revisão; decidir se o art. 19 e as resoluções da ANPD entram como fonte do pacote (ampliação de escopo que exige leitura da fonte oficial, data e hash); validar o texto literal do Código Civil, cujo compilado **não está** no repositório (sem `--fonte-cc`, `regras.py validar` não confere as 9 regras do CC); limpar artefatos de conversão no texto literal de `lgpd-7` e `lgpd-11` (marcação de link e quebras de linha). Só `civ-473` está pronta para ativar sem alteração de pergunta.
- Orientação do parecer preservada como diretriz, sem implementação: as regras devem sinalizar pontos de revisão, sem declarar nulidade ou ilegalidade pela mera ausência de cláusula.
- Correções de documentação desta entrada: `docs/plano-principal.md` (revisão 15), `docs/uso-assistido.md`, `shared/dados.md` e `skills/br-revisar-contrato/SKILL.md` passam a dizer 21 regras inativas (19 de Código Civil/LGPD e 2 de NDA) e que o pacote NDA tem 2 regras-rascunho, em vez de "NDA vazio". Registros datados anteriores (por exemplo, `docs/validacao-fase5.md`) preservam a contagem da época e não foram alterados.
- Verificação: ver o PR; a suíte integral não foi executada localmente.

## CL-FECH — fechamento da reconciliação do repositório, 30/10/2026

- Pedido autorizado pelo titular, passo a passo. Responsável: Claude; apenas Git/GitHub e este registro, sem alteração de código, de regras ou de skills. O worktree do Codex não foi tocado.
- Integrado no `main`: PR #7 (pacote NDA, H-07 e correção da skill `br-preencher-minuta`; CI verde nos quatro jobs) e PR #9 (`pypdf` 6.19.0 → 6.21.2 em `requirements-dev.txt`, mesmo diff do PR #6 do Dependabot; CI verde). Os merges foram feitos pelo titular.
- Causa do PR #9: o PR #6 do Dependabot havia entrado em `fix/fase2-correcoes`, que era a branch padrão do GitHub, e não chegou ao `main`.
- Branch padrão do GitHub trocada para `main` pelo titular (Settings → Default branch). Depois disso o Dependabot passa a abrir PRs contra `main`.
- `fix/fase2-correcoes`: obsoleta. Os 7 commits que existiam só no checkout local do Claude foram preservados e integrados nela pelo PR #8 (merge do titular, antes da troca da branch padrão); não passam para o `main` e conflitam com ele em 7 arquivos. As branches `arquivo/fase2-local-2026-10-29` e `claude/pypdf-6-21-2` foram apagadas pelo titular. Restam no GitHub, sem uso corrente: `fix/fase2-correcoes` e `claude/porte-sobre-main` (integrada pelo PR #7).
- Documentos de plano e backlog do Claude de 29/10/2026 (`docs/plano-aprimoramentos-2026-10-29.md`, `docs/estado-backlog-2026-10-29.md`) e `tests/casos/README.md`: escritos sobre base obsoleta, **não** portados ao `main`; só existem em `fix/fase2-correcoes`. Se forem retomados, devem ser reescritos sobre o `main`.
- Checkout local do titular alinhado ao `origin/main` (`5561813`), com árvore limpa. O checkout de origem foi atualizado por bundle, porque a VM da ponte não tem credenciais do GitHub.
- Pendente do Codex: no worktree dele, a branch `codex/organizacao-colaboracao` tem o commit `785d4ce` ("feat: validar e renderizar análise estruturada") que não está no GitHub nem no `main`. Não foi verificado nem enviado pelo Claude. Cabe ao Codex abrir o PR ou dizer se ele ainda vale sobre o `main` atual.
- Pendentes do titular, sem prazo técnico: revisão jurídica das 21 regras contratuais, todas **inativas** (nenhuma ativação ocorreu); decisão sobre o modo padrão de `auditar.py` (`analise` ou `fundamentada`).
- Verificação: `git status` limpo após o alinhamento; CI dos PRs #7 e #9 verde. Suíte integral não executada no ambiente do Claude.

## CL-NDA / H-07 — porte do trabalho do Claude sobre o `main`, 29/10/2026

- Pedido autorizado pelo titular: “commit e push e pr”. Responsável: Claude, em cópia própria (clone novo de `main`, `3ab28e2`), branch `claude/porte-sobre-main`; o worktree do Codex e o checkout original do Claude não foram tocados. PR para `main`, sem merge.
- Contexto: o checkout original do Claude estava em `fix/fase2-correcoes`, base `4e9989c`, e divergia do `main` em 16 commits (CX-01 a CX-04, R07/R10, peças, redline por issue). Do trabalho local foram portados somente os itens que o `main` ainda não tem; C-02 (redline por `issue_id`) e C-03 (localizador por sufixo em `preencher.py`) foram **descartados** por já existirem, de forma mais estrita, no `main`.
- Portado: (1) pacote NDA com o art. 195 da Lei 9.279/1996 (texto literal da versão compilada lida em 2026-10-29, hash em `tests/casos/regras_fontes/registro.json`), duas regras **inativas** e sem revisor, `--fonte-lpi` em `regras.py`, com pendências do revisor mantidas (via civil, arts. 207 e 209; prazo do sigilo e foro); (2) H-07: a fixture `caso` de `tests/test_auditar.py` extrai o PDF uma vez por módulo, com cópia por teste; (3) `br-preencher-minuta`: o estado `informado` exige também `fala`.
- Verificação: 207 testes aprovados e 2 falhas em `test_contrato_inventario_pecas.py` (`instante_invalido`, `instante_sem_fuso`), **idênticas no `main` limpo** neste ambiente por faltar `rfc3339-validator`; a suíte integral não foi executada. Antes da integração com o `main`, a mudança de H-07 reduziu a suíte de 483,6 s para 353,3 s no Windows do titular (mesmos 465 aprovados e 4 ignorados); o efeito sobre a base atual não foi medido.
- Limites: as regras contratuais continuam inativas (21 no total, 2 delas novas); nenhuma ativação, revisão jurídica ou liberação. Conflitos antecipados com a branch antiga `fix/fase2-correcoes` (7 arquivos) tornam essa branch obsoleta para integração.

## F5-I01 — versionamento e integração autorizados, 22/10/2026

- Autorização posterior do titular: “commit, push, pr e merge após”. Abrange os seis documentos da fase 5 e os commits locais anteriores da branch Codex. Executar commit, push e PR para `main`; merge somente depois de conferir revisão, head exato e CI. Não ativa regras, não aprova usos materiais e não autoriza instalação ou edição do checkout Claude.
- Preflight: worktree Codex e branch `codex/organizacao-colaboracao`, HEAD `910b11e87e92e153610463fdc6e5cd167f5d3968`; quatro documentos modificados/dois novos e índice vazio. Fetch de `origin` realizado sem trocar branches. Base explícita da PR: `main`, `7394606a7097dfa8430e2acea15ff7561b50bcba`; não usar o default remoto `fix/fase2-correcoes`, reservado ao checkout Claude.
- Escopo: registrar esta autorização e o estado da integração nos documentos já previstos, conferir diff staged e diff final contra `main`, reutilizar a suíte local de 1019 aprovados/5 ignorados mediante conferência dos hashes, revisar a proposta completa e verificar os quatro jobs remotos. Nenhuma nova implementação funcional prevista. Manter os dois casos públicos R07/R10 separados dos privados e 19 regras inativas.
- Evidências próprias: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/integracao-fase5-2026-10-22-gr45seb6`. Baseline anterior ao commit, hashes e estado de Claude preservados; logs/saídas e refs da integração serão registrados sem sobrescrever as evidências locais da fase 5. Registros anteriores de ausência de autorização/commit/push são históricos.
- Publicação: commit documental da fase 5 `aba3dcb56359cab6a7846ef915c41491c84eb74f`, branch publicada e [PR #5](https://github.com/junior-aguiar-eng/assistente-juridico-avancado/pull/5) aberta explicitamente para `main`. Proposta completa com 94 arquivos; revisão independente de integração sem P1/P2/P3, com **252 testes focados aprovados em 45,26 s** e JUnit conferido. Sem nova mudança funcional.
- CI da proposta `aba3dcb`: [execução 39865227437](https://github.com/junior-aguiar-eng/assistente-juridico-avancado/actions/runs/39865227437), quatro jobs aprovados. Ubuntu/Python 3.12: 1015 aprovados/5 ignorados; Ubuntu/3.13: 1015/5; Windows/3.12: 1008/16; Windows/3.13: 1008/16. Oito skills PRONTA em todos. Logs vinculam o merge de teste `d976360e81123aede70d9a34fa9abc94070cf3b6` ao head e à base corretos. As contagens variam por ambiente; ignorados não comprovam cobertura. A CI deste registro documental é uma execução separada e será conferida no HEAD final antes do merge, sem contornar checks.
- Estado da integração acompanhado pela PR #5; este registro confirma a CI já executada, sem antecipar o merge. Conferência humana dos inventários/trechos e aprovação de entregas permanecem pendentes, P01/P02 estruturalmente aprovados, 19 regras inativas e Claude preservado. A integração não instala nem libera material juridicamente.

## Fase 5 — validação para liberação assistida, 22/10/2026

- Pedido: concluir primeiro o plano vigente, prosseguindo com a fase 5. Responsável: Codex, no worktree separado `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`, base `910b11e87e92e153610463fdc6e5cd167f5d3968`; remoto e worktrees conferidos, árvore limpa e índice vazio. Claude permanece no checkout original, sem Git, testes ou alterações nele.
- Escopo antes da execução: reconciliar cada critério da seção 7 do plano com evidências; repetir a aceitação dos PDFs públicos e os controles de bloqueio, suíte integral offline, revisão mecânica, compatibilidade, ambiente e licenças das dependências já adotadas. Atualizar README, avisos de terceiros, plano, este registro e criar `docs/validacao-fase5.md` e `docs/uso-assistido.md`. Nenhuma mudança funcional, dependência, integração JurisExpert, ativação de regras ou migração de arquivos prevista; defeito reproduzido terá escopo e regressão próprios.
- Critério: publicar no repositório a matriz de evidências e os limites reais, preparar roteiro de uso/migração, registrar separadamente testes aprovados, ignorados e não executados; manter 19 regras inativas, originais e aprovações históricas. Aprovação dos gabaritos P01/P02 não vira evento humano dos inventários ou aprovação de entrega. Gates humanos e CI da revisão publicada não serão marcados como concluídos por testes locais.
- Evidências e ledger próprios: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/fase5-2026-10-22-a7bu7lxi`. Baseline de 181 arquivos Codex e conferência de 106 arquivos/seis metadados Claude. Executar a preparação e validação local até o limite autorizado, sem novo commit, push, PR, merge, instalação ou publicação externa nesta etapa.
- Resultado local: **1019 testes aprovados, 5 ignorados, zero falhas/erros em 766,98 s**, saída zero/JUnit conferidos; dois de rede, Docling opcional e dois privados ausentes ignorados. Cinco observações de aceitação e oito CLIs conferidos, incluindo recusas materiais e detecção de alteração. Oito skills PRONTA; 12 dependências fixadas e licenças locais conferidas, sem conflitos. Scripts/testes/skills/regras/fixtures intactos; 177 arquivos Codex fora do escopo e 106 arquivos/seis metadados Claude, índice vazio, HEAD/branch/refs e 19 regras inativas preservados. Quatro documentos modificados/dois novos; patch reverso verificado sem aplicar. Revisão independente sem P1/P2, P3 do exemplo de status corrigido. Fase 5 continua aberta para conferência humana material e CI da revisão publicada; sem commit/push ou ativação. [Evidências e limites](validacao-fase5.md).

## ORG-05 — fechamento da conferência humana e commit local, 22/10/2026

- Autorização posterior do titular nesta conversa: “P01/P02 revisados e aprovados. proceda com a finalização da pendência, commit as alterações”. Substitui o adiamento abaixo somente quanto aos gabaritos estruturais de P01/P02; não aprova mérito jurídico, inventários de uso material, OCR integral ou ativação de regras.
- Preflight: worktree Codex `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`, HEAD `a3848b1c5443cc72d9a00346c5f661e69a52b558`, origin e worktrees conferidos; sete arquivos modificados/dez novos da ORG-05 e índice vazio. Claude preservado, sem executar Git/testes nele.
- Escopo antes da edição: registrar a confirmação real do titular em `tests/casos/org05/conferencia-humana.json`, vinculada aos hashes dos PDFs e aos gabaritos de uma peça acórdão (P01: 1–16; P02: 1–14); atualizar proveniência somente dessas duas referências no manifesto, testes de integridade/proveniência e estado atual no README, corpus, plano e relatórios. Resultados congelados e evidências anteriores permanecem históricos. Nenhuma mudança adicional no código do produto.
- Critério: verificar vínculo da confirmação e seu escopo, repetir os testes pertinentes e revisão mecânica; comparar código com a suíte integral definitiva já executada; conferir diff staged e preservação de Claude, arquivos fora do escopo e 19 regras inativas. Fazer um commit local da entrega ORG-05, sem push, PR, merge, instalação ou liberação da fase 5.
- Evidências próprias do fechamento: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/org05-fechamento-2026-10-22-1xcjbkis`. O commit que contém este registro identifica a entrega final; os registros de adiamento/ausência de commit abaixo descrevem a execução anterior.
- Verificação de fechamento: **151 aprovados, zero ignorados/falhas em 54,44 s**, oito skills PRONTA. JUnit/saída da integral anterior (1014/5) reconferidos; todos os scripts idênticos por hash, somente o teste de manifesto/conferência atualizado e repetido. Integral não reexecutada. Preservados 163 arquivos Codex fora do escopo, 106 arquivos/seis metadados Claude, resultados congelados, demais refs e 19 regras inativas. Escopo final de sete arquivos modificados/onze novos; diff final e staged conferidos para commit local, sem push.

## ORG-05 — validação integrada, 22/10/2026 (registro anterior ao fechamento)

- Autorização: commit local da ORG-04 e prosseguimento com ORG-05. ORG-04 registrada em `a3848b1c5443cc72d9a00346c5f661e69a52b558`, com 41 regressões repetidas antes do commit e a suíte integral de 984 aprovados/5 ignorados conferida. Árvore limpa na entrada da ORG-05, índice vazio, mesma branch/remoto/worktree. Sem push.
- Plano, arquivos previstos, critérios e limites: [validação ORG-05](validacao-org05.md). Consumidores/classificador congelados na base; novos processos públicos separados do desenvolvimento, métricas por processo/modalidade, integração e segunda avaliação das oito skills. Sem promover propostas técnicas a conferências humanas, sem mudar regras ou checkout Claude. Prioridades somente no plano principal.
- Baseline externo: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/org05-2026-10-22-ejd98q8d`; hashes dos arquivos Codex e referências, 106 arquivos e seis metadados Claude. ORG-05 será entregue como diff local, sem novo commit nesta execução.
- Execução técnica: duas fixtures públicas oficiais novas do TJMG (16/14 páginas), referências técnicas independentes por dois agentes, manifesto por processo/coorte/modalidade e avaliador offline. Rodada inicial `a3848b1` preservada em [resultado congelado](resultado-org05-congelado.json); duas leituras do ofício R10 não viram processos distintos. Detector manteve um envelope por PDF novo, mas se absteve do tipo nos dois.
- Segunda avaliação: oito skills, 16 cenários, 114 comandos iniciais, com documentos públicos reais nas skills de autos/pesquisa/auditoria e contratos/minutas sintéticos. Achados reais de colisão de inventários multidocumento e identificação incorreta do relatório redline reproduzidos em RED, corrigidos e repetidos independentemente sem workaround. Só identidade/identificação foram reparadas; detector não ajustado ao holdout. Testes/documentos respectivos passam a integrar o escopo. [Relatório das skills](avaliacao-skills-org05.md).
- Revisão do avaliador encontrou contagem duplicada de processo e precisão falsa intrapágina; RED confirmado, correções verificadas por sondas independentes e 22 testes do avaliador aprovados nessa rodada parcial. Focada anterior: 139 aprovados/72,28 s. Oito skills PRONTA e `pip check` sem conflitos; suíte integral definitiva com código congelado por hashes no início, resultado abaixo.
- Decisão humana posterior: “Vou conferir depois; mantenha pendente” para os gabaritos P01/P02. Preservar `modelo_tecnico` e ausência de eventos humanos. A concordância entre agentes não encerra ORG-05 nem a fase 5; nenhuma avaliação jurídica ou liberação externa foi feita.

- Verificação definitiva: **1014 aprovados, 5 ignorados, zero falhas/erros em 891,51 s**, saída zero/JUnit conferidos, Python 3.14.6/Windows, `PYTHONUTF8=1`, `JURIS_REDE=0`. Duas execuções anteriores interrompidas para corrigir portabilidade/caminhos não contam como aprovadas. Avaliador final com 27 testes aprovados; caminhos e junctions conferidos por revisão independente, sem achados materiais pendentes. Oito skills PRONTA, sem alertas; `pip check` sem conflitos.
- Preservação final em `preservacao-final.json`: sete arquivos modificados/dez novos; 163 arquivos Codex preexistentes fora do escopo, 106 arquivos/seis metadados Claude, índice vazio, HEAD/branch/refs e 19 regras inativas preservados. Código/testes inalterados desde o início da rodada definitiva. Patch externo completo de texto/PDFs verificado sem aplicar ou stagear. ORG-05 permanece sem commit/push; conferência humana e fase 5 continuam abertas.

## ORG-04 — integração do inventário nos consumidores, 22/10/2026

- Autorização posterior: usuário solicitou commit local da ORG-04 e prosseguimento com ORG-05. O versionamento não autoriza push, instalação, ativação de regras ou aprovação jurídica; ORG-05 terá escopo e resultados próprios, posteriores a este commit.
- Pedido expresso: implementar ORG-04 no worktree Codex, executar testes, preservar Claude e 19 regras inativas, sem commit ou push. Responsável: Codex; diretório `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`, HEAD `9100c8fb709a10d4eb50fc9f41128c34debc8da1`, árvore inicialmente limpa; remoto e worktrees conferidos.
- Coordenação de formato: extensão opcional `peca` nas fontes de facts/claims, com inventário identificado por hash, peça e fragmentos; nenhum estado jurídico ou campo legado é migrado. Parâmetros opcionais ligam inventários, originais e revisões anteriores às extrações fornecidas. O modo de exigência explícita cobre documentos paginados; comandos antigos sem inventário e sem referências novas conservam o fluxo anterior.
- Escopo previsto: novo módulo compartilhado `scripts/pecas_uso.py`; integração em `validate.py`, `auditar.py`, `cronologia.py` e `triagem.py`; regressões sintéticas em `tests/test_org04.py`; instruções das skills consumidoras, `shared/dados.md`, guia do inventário, contrato, README, plano principal e relatório `docs/integracao-org04.md`. Sem extrator novo, dependências novas, editor de conferências, ORG-05, regras ou governança jurídica.
- Aceitação e desenho: [integração ORG-04](integracao-org04.md). Primeiro reproduzir usos indevidos e controles positivos; depois compartilhar validação de identidade/fragmentos e pendências por uso. Análise pode registrar proposta/OCR com ressalvas; uso fundamentado ou exposição de fatos recusa pendências materiais do trecho. Inventário de outra extração, peça ou revisão não pode validar uma referência. QC vincula todos os insumos por hash; cronologia preserva referências e detecta mudança do inventário. Não criar confirmação humana automaticamente.
- Baseline externo: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/org04-2026-10-22-u94_hf_s`, com 167 arquivos Codex, 106 arquivos Claude, metadados próprios dos checkouts, refs e índice. Testes no ambiente limpo já existente, temporários/logs externos exclusivos.
- Entrega local: 41 regressões novas; rodada focada final com **283 aprovados em 44,78 s**. Revisão independente somente leitura encontrou falhas de referência, atribuição, localização, seção e proveniência; reproduzidas e corrigidas, com nova revisão sem achados pendentes no escopo. Oito skills PRONTA, sem alertas; `pip check` sem requisitos quebrados. Relatório e limites em [ORG-04](integracao-org04.md).
- Suíte integral: primeira execução com 983 aprovados/5 ignorados/uma falha de decodificação no teste existente de resolução `NaN`; corrigida somente a configuração da execução com `PYTHONUTF8=1`, sem editar produto/teste. Repetição: **984 aprovados, 5 ignorados, zero falhas/erros em 815,17 s**, `JURIS_REDE=0`, Python 3.14.6/Windows; saída zero/JUnit conferidos. Ignorados: duas operações de rede, Docling Parse opcional e dois originais privados ausentes. Código/testes congelados desde antes da primeira suíte; mudanças posteriores somente documentais.
- Preservação por hashes: 106 arquivos e seis metadados do Claude, 152 arquivos Codex preexistentes fora do escopo, índice vazio e intacto, HEAD/branch e outras branches/refs remotas preservados; 19 regras inativas. Escopo final: 15 arquivos modificados e três novos; patch externo completo e conferência em `preservacao-final.json`. Sem commit, push, PR, merge, instalação, ativação ou aprovação jurídica. ORG-05 permanece não iniciada; prioridades somente no plano principal.

## VT-01 — versionamento local e pendências consolidadas, 22/10/2026

- Pedido expresso posterior a IG-01: fazer commit das alterações e identificar as pendências, sem push. Responsável: Codex, no worktree `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`, base `abbf85a779627a49ac38def046bbc142bacbacd1`. Claude permanece no checkout original; não executar Git ou testes nele.
- Escopo previsto em duas unidades lógicas: (1) auditoria documental, atribuição contextual e gates de integridade, com seus testes/documentos AF-01/CP-01/AC-01/GT-01; (2) reconciliação ORG-01/02/03 e controles DOCX recuperados, testes, separação do corpus, correção UTF-8 e documentação RC-01/IG-01. Apenas este registro e a seção de pendências do plano principal recebem atualização adicional; nenhuma nova implementação funcional.
- Preservação: conteúdo funcional dos arquivos de produto mantido; primeiro índice montado a partir de cópia própria do snapshot anterior a IG-01, sem trocar os arquivos do worktree. Removida somente linha vazia excedente no fim de `tests/test_atribuicao_citacoes.py`, no snapshot e na versão final, para a conferência de whitespace. Nenhuma regra ou arquivo do Claude é incluído como mudança; 19 regras inativas e casos públicos/privados separados.
- Critério: revisar cada diff staged, testar a unidade intermediária e a suíte integral offline final em ambiente limpo, conferir as oito skills, dependências, hashes de preservação e árvore limpa após os commits. Pendências consolidadas somente em [plano-principal.md](plano-principal.md), mantendo ORG-04/05 não iniciadas. Push, PR, merge, CI remoto, instalação, ativação e liberação continuam fora desta autorização.
- Evidências e snapshot: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/versionamento-org-2026-10-22-t_dz92rv`. A referência da segunda unidade é o commit que contém este registro, informada também na entrega, evitando hash autorreferente. Os registros anteriores de ausência de commit são históricos e não restringem este pedido posterior.
- Primeira unidade: commit `f3e3c2b8ea2024717fc9529c43a1aaf6547b8159`, com 20 arquivos. Regressões do snapshot intermediário: **160 aprovados em 133,66 s**, no ambiente limpo e com temporários próprios. A primeira tentativa da suíte integral encerrou sem resumo final e não conta como aprovação; log parcial preservado e execução retomada com registro persistente de conclusão.
- Suíte integral retomada: **943 aprovados, 5 ignorados, zero falhas/erros em 859,31 s**, Python 3.14.6/Windows, ambiente próprio `.venv-limpo`, `JURIS_REDE=0`, bytecode/cache desativados e temporários externos exclusivos. Resultado confirmado pelo código de saída zero e JUnit XML. Ignorados: dois testes de rede, Docling Parse opcional ausente e os originais ORG-R07-PRIVADO/ORG-R10-PRIVADO ausentes. R07/R10 públicos executados com aprovação. Oito skills PRONTA; `pip check` sem requisitos quebrados; diffs staged sem erros de whitespace.
- Estado: as duas unidades recebem commits locais nesta etapa; nenhum push, PR, merge, CI remoto, instalação, ativação ou aprovação jurídica. O conteúdo funcional reconciliado e as correções locais permanecem preservados. A conferência final registra hashes dos 106 arquivos do Claude e seis metadados próprios de seu checkout, 19 regras inativas, outras branches/refs remotas intactas e árvore Codex limpa em `preservacao-final.json`. ORG-04 é a próxima implementação; demais pendências e decisões estão somente no plano principal.

## IG-01 — integração da reconciliação no worktree Codex, 22/10/2026

- Autorização expressa: integrar RC-01 ao worktree Codex preservando Claude, alterações locais e 19 regras inativas, sem commit ou push.
- Diretório: `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`; branch `codex/organizacao-colaboracao`, HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`. Remoto e worktrees conferidos. Nenhuma mudança em branch, refs ou índice prevista.
- Preflight: os 127 arquivos locais eram idênticos ao snapshot-base de RC-01; nenhum drift ou conflito posterior. Snapshot externo dos arquivos e baseline Git antes de escrever. Claude conferido por hashes de arquivos/metadados, sem executar Git, testes ou instalação nele.
- Transferência: delta de 57 arquivos da cópia reconciliada, com conferência dos 166 arquivos resultantes byte a byte antes dos ajustes documentais de integração. AF-01/CP-01/AC-01/GT-01 permanecem preservados; regras e governança locais não são substituídas por ativações da branch recuperada. R07/R10 públicos e privados conservam manifestos/IDs separados.
- Escopo adicional: somente este registro, contexto do plano principal e relatório `docs/integracao-org-codex-2026-10-22.md`. Nenhuma alteração de código em relação à RC-01 validada; ORG-04/05 não iniciadas.
- Critério: conteúdo de código/testes/fixtures idêntico à RC-01, controles locais e regras intactos, testes focados no destino e revisão mecânica, diff sem erros, preservação final de Claude e do índice/refs/HEAD Codex. Os 943/5 e 304 testes anteriores permanecem resultados da cópia isolada.
- Evidências: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/integracao-org-codex-2026-10-22-4ywcc8qx`. Estado: integração e validação local concluídas; 391 testes aprovados/2 ignorados (privados ausentes), oito skills PRONTA, diff sem erros. Hashes de 106 arquivos Claude e 28 metadados intactos; 109 arquivos locais fora do delta preservados; código/testes/fixtures iguais à RC-01. Branch/HEAD/refs/índice mantidos, 19 regras inativas. Sem commit/push, aprovação ou ativação. Relatório: [integracao-org-codex-2026-10-22.md](integracao-org-codex-2026-10-22.md).

## RC-01 — reconciliação isolada de ORG-01 a ORG-03, 22/10/2026

- Autorizada pelo usuário em cópia independente: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/reconciliacao-org-2026-10-22-ijrtytf6/Skill Legal`, branch `codex/reconciliacao-org01-org03`, HEAD `abbf85a`.
- Baseia-se no snapshot do worktree Codex com AF-01/CP-01/AC-01/GT-01 e na branch recuperada `ff225a7`; ambos os checkouts anteriores permanecem preservados.
- Escopo, arquivos e aceitação em [reconciliacao-org-2026-10-22.md](reconciliacao-org-2026-10-22.md). Regras inativas, casos privados separados; sem commit/push, ORG-04/05 ou ativação. Estado: concluída localmente para revisão; 943 testes offline aprovados/5 ignorados, 304 focados aprovados em ambiente limpo, oito skills PRONTA e revisão estática independente sem achados materiais pendentes. Regras/manifesto público/controles preservados; relatório e evidências de preservação conferidos. Sem commit/push ou integração nos checkouts anteriores.

## GT-01 — integridade de G04/G05 e relatório de G10, 22/10/2026

- Pedido expresso: corrigir primeiro G04, G05 e G10, incluindo o contorno por hash textual, com testes de regressão. Responsável: Codex, worktree `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`, HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`, remoto confirmado. AF-01/CP-01/AC-01 e índice preservados; Claude fora de Git/testes/edição.
- Diagnóstico reproduzido na análise anterior: originais/fontes ausentes ficam apenas em alerta em modo fundamentada; G05 aceita arquivo divergente usando hash textual de outra extração; G10 dispensa relatório em entrega externa.
- Escopo/arquivos previstos: `scripts/auditar.py` somente G04/G05/G10, novo `tests/test_gates_integridade.py`, ajuste das entradas positivas em `tests/test_auditar_extras.py`, instruções delimitadas em `skills/br-auditar-entrega/SKILL.md`, README, este registro e novo `docs/correcao-gates-integridade-2026-10-22.md`. Sem alterar formatos/estados, aprovação humana, downloader, regras, dependências ou históricos.
- Critério: fontes/originais ausentes bloqueiam em modo fundamentada ou entrega externa; análise interna mantém alerta. G05 aceita hash bruto ou textual no registro somente com arquivo local vinculado aos bytes da extração. Relatório é obrigatório para entrega externa; auditoria interna sem relatório mantém o comportamento anterior. Alterações de hash continuam reprovadas em qualquer modo. Entradas legíveis/intactas e relatórios com aviso preservam os controles positivos.
- Validação: reproduzir falhas com fixtures sintéticas e API/CLI antes da correção, incluindo hash textual legítimo, arquivo substituto normalizado, ausência e perda posterior de fonte. Executar regressões, suíte integral offline e revisão mecânica das skills; conferir diff e preservação por hashes. Sem commit/push, PR, merge, instalação ou ativação.
- Evidências: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/gates-g04-g05-g10-2026-10-22-j_tcmexo`; snapshots anteriores à implementação e baseline de 125 arquivos Codex, 109 itens Claude e históricos, incluindo AC-01. Estado: concluído localmente para revisão.
- Resultado: G04/G05 aplicam rigor à ausência, G05 exige os bytes da extração mesmo quando o registro usa hash textual, e G10 reprova entrega externa sem relatório. Aprovação, formatos/estados, downloader e regras não modificados. As novas verificações exigem nova auditoria; QCs históricos não são migrados.
- Testes: 22 falhas/14 controles positivos antes da correção; rodada focada final com 36 aprovados em 6,81 s. Suíte integral offline: **732 aprovados, 3 ignorados em 471,29 s**, sem falhas, Python 3.14.6/Windows, `JURIS_REDE=0`. Ignorados os dois testes de rede e o marcador vazio de casos pendentes. Oito skills PRONTA; `git diff --check` sem erros. CI remoto/rede/instalação não executados.
- Preservação: 109 itens do Claude e 859 arquivos históricos intactos por SHA-256; 120 demais arquivos Codex anteriores intactos. Cinco arquivos existentes alterados no escopo e dois novos, preservando os diffs anteriores. Branch/HEAD mantidos, índice vazio, 19 regras inativas. Patch incremental e conferência final nas evidências. Sem commit/push/PR/merge ou revisão jurídica. Revisão do próprio implementador, sem revisão independente.
- Relatório: [correcao-gates-integridade-2026-10-22.md](correcao-gates-integridade-2026-10-22.md).

## AC-01 — atribuição contextual de citações, 21/10/2026

- Pedido expresso: corrigir a atribuição indevida reproduzida em R07, com regressões e sem exceções por página, processo ou frase do caso. Responsável: Codex; worktree `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`, HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`, remoto confirmado. AF-01/CP-01 locais preservadas, índice vazio; checkout do Claude fora de edição/Git/testes.
- Diagnóstico: ementa aninhada dentro de voto gera aviso, mas a atribuição depende do recuo de cada linha; a transcrição de mesma margem e multipágina volta a ser tratada como texto próprio. O desprovimento citado passa como resultado do órgão principal.
- Escopo/arquivos previstos: `scripts/extract.py` (contexto de transcrição e invalidação de cache pela versão), `scripts/validate.py` (ambiguidade de atribuição e correspondência do localizador), `tests/test_atribuicao_citacoes.py` (novo), este registro, `docs/correcao-atribuicao-citacoes-2026-10-21.md` (novo), README e a instrução delimitada de `skills/br-verificar-citacoes/SKILL.md` sobre atribuição ambígua. Sem alterar os formatos/estados de claims, política humana, dependências, regras jurídicas, fixtures ou históricos.
- Desenho: início de ementa dentro de seção narrativa abre candidato a transcrição; fechamento bibliográfico com metadados de relatoria/data delimita o intervalo, independentemente de margem e página. Fronteira não resolvida recebe tag de atribuição ambígua, sem inventar autoria; `supported` não passa com essa ambiguidade. Textos próprios após referência fechada preservados; transcrição explícita e segura continua representável com `cited_text=true`.
- Aceitação: primeiro reproduzir a falha no PDF real e em variantes sintéticas (margem, caixa, título, quebra de página, mais de uma referência e retorno ao voto); observar falhas antes da correção. Depois bloquear atribuição indevida no validador/auditor/CLI, preservar controles positivos e todo o texto/hash bruto. Executar suíte integral offline e revisão mecânica; rede/CI remotos não necessários.
- Evidências/baseline: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/correcao-atribuicao-citacoes-2026-10-21`. Originais, relatórios, QCs e sondas anteriores ficam intactos; reextrações novas ficam nesta pasta. Sem commit, push, PR, merge, instalação ou ativação.
- Implementação: extrator `0.4.3` delimita ementas transcritas pelo contexto até referência bibliográfica fechada no fim do bloco; referência interna com continuação não encerra a transcrição. Fronteira não resolvida fica `atribuicao_ambigua`. O validador rejeita `supported` ambíguo, considera a ocorrência no localizador informado, não aceita contorno por fonte secundária e mantém o controle positivo de texto próprio/`cited_text=true` delimitado. Schema, estados e política humana preservados.
- Regressões: 18 falhas/5 passagens iniciais; gerador de fixture corrigido para escapar parênteses PDF, com falha também reproduzida na base original e PDF válido. Três sondas adicionais e duas de referência interna reproduzidas antes das respectivas correções. Rodada focada final: 28 aprovados em 6,81 s. A rodada integral intermediária foi interrompida para incluir/corrigir as duas regressões de fronteira; não conta como aprovação.
- Suíte integral final: **696 aprovados, 3 ignorados em 806,63 s**, sem falhas, offline (`JURIS_REDE=0`, Python 3.14.6, temporários próprios). Ignorados DataJud/rede, fontes/rede e marcador vazio de casos pendentes. Revisão mecânica: oito skills PRONTA. `git diff --check` sem erros. Rede, CI remoto e instalação não executados.
- Reextração nova de R07 preserva hash do arquivo, hash textual e sequência do texto. A sonda histórica, copiada byte a byte e confrontada com a extração nova, é recusada com `trecho_so_em_citacao`; auditor reprova G02 por API/CLI e não libera uso. Texto próprio e proposição explícita sobre o precedente transcrito continuam válidos. Históricos não foram reescritos: a correção exige nova extração e nova auditoria.
- Preservação final: 109 itens do Claude e 797 arquivos históricos sem diferenças por SHA-256; 19 regras inativas e intactas; demais arquivos preexistentes do Codex preservados. Branch/HEAD mantidos, índice vazio. O patch do incremento, separado de AF-01/CP-01, e a conferência final ficam nas evidências. Relatório: [correcao-atribuicao-citacoes-2026-10-21.md](correcao-atribuicao-citacoes-2026-10-21.md).
- Estado: implementação e validação local concluídas, disponíveis para revisão; sem commit, push, PR, merge, ativação ou aprovação jurídica. Revisão do próprio implementador, sem revisão independente. A correção não substitui julgamento semântico, atribuição/aplicabilidade humana ou resolve automaticamente todos os formatos de referência.

## CP-01 — retomada das pendências, 21/10/2026

- Pedido: continuar as pendências. Responsável: Codex; worktree e remoto reconfirmados, branch `codex/organizacao-colaboracao`, HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`, com o diff AF-01 preservado e índice vazio.
- Escopo inicial: inspeção visual das quatro cópias DOCX da simulação (modelo, minuta, contrato original e redline), renderização local sem editar originais e identificação das pendências restantes. Avaliação das skills com R06/R07/R10 poderá prosseguir offline, distinguindo documento real de contrato sintético. Sem revisão jurídica ou ativação de regras.
- Arquivos previstos: este registro e `docs/continuidade-pendencias-2026-10-21.md`; saídas, logs e baseline fora do repositório em `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/continuacao-pendencias-2026-10-21`. Nenhuma mudança funcional prevista.
- Aceitação: inspecionar todas as páginas efetivamente renderizadas; registrar achados com página e fonte, sem confundir XML com inspeção visual. Preservar hashes do Claude, regras, fontes históricas e diff funcional AF-01. Sem commit, push, PR, merge, instalação ou uso externo.
- Atualização de escopo: README.md receberá somente os novos resultados de avaliação/DataJud e a ligação para o relatório; arquivo compartilhado sob responsabilidade deste incremento. Correção editorial limitada a novos derivados do modelo/minuta da simulação, com regeneração e reauditoria. Nenhum código de produto previsto.
- Resultado: inspeção visual de modelo/minuta/contrato/redline concluída por renderização local Word→PDF→PNG. Corrigida duplicação editorial apenas em novo modelo derivado; minuta regenerada, inspecionada e reauditada, sem sobrescrever simulações anteriores. QC com evidência visual vinculada por hash em `reconciliacao-visual-r2/outputs/qc-com-inspecao.json`: revisão pronta/faixa mista, `completo=false`, `liberado_para_uso=false`; duas marcações e avaliação jurídica pendente preservadas.
- Avaliação: segunda rodada exploratória nesta conversa, sem cegamento, independência ou segundo modelo; seis skills com R06/R07/R10 e duas contratuais com controles sintéticos. Sonda real R07/p.11 atribuiu resultado de precedente citado ao processo principal e passou no validador sem aviso; a leitura do modelo recusou a atribuição, com conferência de p.1/11/12. Limitação semântica permanece aberta; não houve correção funcional por frase/página/processo.
- Verificações: 77 testes focados offline aprovados em 29,33 s; teste real DataJud separado aprovado em 38,57 s (primeiro sucesso após o patch demonstrado neste registro, sem provar estabilidade); oito skills PRONTA. Suíte integral e CI remoto não repetidos. Uma rodada de correção de entrada no ensaio real (IDs das lacunas e declaração explícita sem teses centrais), preservando a tentativa bloqueada.
- Relatório: [continuidade-pendencias-2026-10-21.md](continuidade-pendencias-2026-10-21.md). Baseline, logs, cenários, respostas, sondas negativas e derivados fora do repositório na pasta registrada acima. A inspeção externa não altera o campo automático de inspeção visual do auditor nem constitui revisão humana.
- Estado: execução local concluída, conferência final de preservação registrada nas evidências; sem commit/push/PR/merge. A revisão jurídica, avaliação independente com contratos reais, fechamento CL-01/CL-02 e integração continuam pendentes. O diff funcional AF-01 não recebeu alterações nesta rodada.

## AF-01 — auditoria documental e classificação jurídica, 20/10/2026

- Pedido: consolidar a auditoria final e corrigir a classificação jurídica dos apontamentos após a simulação completa. Responsável por esta implementação: Codex, inclusive a alteração delimitada em contrato.py e nas instruções contratuais. Atribuição expressa do usuário substitui a reserva anterior somente neste escopo; CL-01/CL-02 não são declaradas encerradas.
- Base confirmada: worktree C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal, branch codex/organizacao-colaboracao, HEAD abbf85a779627a49ac38def046bbc142bacbacd1; árvore inicialmente limpa. Remoto junior-aguiar-eng/assistente-juridico-avancado. Checkout do Claude permanece separado e não recebe Git, testes ou edições.
- Coordenação prévia de formato: acrescentar severidade_juridica=nao_avaliada e motivo_nao_avaliada em issues.json; manter os estados de facts/claims e a política de aprovação humana. Apontamento sustentado apenas em prática comercial não pode receber graduação jurídica. Não migrar ou sobrescrever registros históricos automaticamente.
- Plano: primeiro regressões negativas/positivas; depois reutilizar contrato.validar_issues e preencher.lint/gerar na auditoria, com entradas explícitas e reconhecimento de JSONs de campos/apontamentos recebidos como artefatos; distinguir campos marcados/avaliação jurídica pendente de erro técnico. Conferir o conteúdo da minuta gerada sem alegar inspeção visual.
- Arquivos previstos: scripts/auditar.py, scripts/auditoria_documental.py (novo), scripts/contrato.py; tests/test_auditoria_documental.py (novo) e tests/test_contrato.py; README.md, shared/dados.md, skills/br-auditar-entrega/SKILL.md, skills/br-revisar-contrato/SKILL.md, este registro e plano local em docs/plano-auditoria-final-2026-10-20.md.
- Aceitação: apontamento comercial usa nao_avaliada com motivo e permanece pendente de revisão jurídica; erros de lint, cláusula/valor sem fonte, modelo/minuta ausente ou minuta divergente bloqueiam a checagem; pendências legítimas aparecem em qc/status sem virar documento completo; modelos, minutas, campos, apontamentos e regras usadas ficam vinculados por hash. Comandos antigos sem documentos adicionais continuam compatíveis.
- Verificação prevista: regressões antes/depois, suíte integral offline, revisão mecânica das oito skills, reexecução em novos derivados da simulação sem alterar o pacote original, diff final e hashes do Claude/regras. Sem nova dependência, consulta externa, renderizador, instalação, ativação, aprovação humana, commit ou push.
- Implementação: validador contratual aceita nao_avaliada com motivo, informa IDs pendentes e não libera graduação apoiada só em prática comercial. Regra citada sem conferência também mantém entregavel=false. Auditor reutiliza os validadores, confere as partes da minuta com geração temporária e registra documentos/pendências no QC/status. G14/G15 são acrescentados somente quando há entradas documentais; aprovação humana preservada.
- Testes antes da implementação: 23 cenários novos falharam. Revisão independente estática encontrou duas brechas, reproduzidas com nove falhas e uma passagem: reconhecimento de JSON mal tipado e regra sem conferência que mantinha entregavel=true. Corrigidas e reconferidas pelo revisor sem outros bloqueadores diretos. Rodada focada final: 77 aprovados em 15,08 s. Rodadas ampliadas iniciais foram interrompidas para aplicar a revisão, sem contar como aprovação.
- Suíte integral final offline: python -B -m pytest -q -rs --durations=8, com JURIS_REDE=0, PYTHONDONTWRITEBYTECODE=1 e basetemp próprio no diretório de evidências: **668 aprovados e 3 ignorados em 901,83 s**, sem falhas. São 44 regressões adicionais em relação à base de 624 aprovações. Ignorados: rede DataJud, rede fontes e marcador vazio de casos aguardando. Rede e CI remoto não executados nesta etapa.
- Reauditoria derivada em C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/simulacao-auditoria-final-2026-10-20-r2: classificação antiga bloqueada em G14; cópia com dois apontamentos nao_avaliada passa mecanicamente com alerta, 15 gates e faixa mista; minuta continua completo=false com conflito de data e chamado pendente, conteudo_confere=true. Status sem aprovação e liberado_para_uso=false. Simulação original intacta (184 arquivos comparados ao ZIP).
- Preservação: 109 itens do Claude sem alteração; 19 regras inativas e intactas; HEAD abbf85a e índice vazio. Revisão mecânica: oito skills PRONTA, sem alertas materiais; git diff --check sem erros. CLI com --regras/--pacote explícitos também executada na reauditoria. Logs, baseline e conferência final em C:/Users/BONIJR~1/AppData/Local/Temp/juris-auditoria-final-20261020-5rtki14_.
- Estado: implementação e verificações locais concluídas, diff disponível para revisão; sem commit, push ou liberação jurídica. São oito arquivos preexistentes alterados e três novos, todos no escopo registrado. A comparação das partes do DOCX é estrita e não valida aparência. Inspeção visual, avaliação com documentos reais e fechamento CL-01/CL-02 continuam pendentes.

## Estado atual — pós-merge do PR #4, 20/10/2026

Esta seção atualiza as pendências R07/R10/DataJud e a integração dos PRs #3 e #4; os registros de execução abaixo são históricos. Os CIs específicos dos dois merges foram concluídos com sucesso nos quatro jobs de cada execução.

- Entrega dos 18 arquivos: e3dff29282c108645b498eac74396c3e791d8dc4, publicada e integrada em main pelo usuário no PR #3. Merge 9363524651e13d98493ccd2d623299785d419486, em 20/10/2026 às 12:48:10 UTC. Oito checks de push/PR e os quatro jobs do CI desse merge passaram.
- Atualização documental posterior: ac12882cf061261cdfd742c0e176c21b966a973c integrada pelo PR #4, merge 7394606a7097dfa8430e2acea15ff7561b50bcba, em 20/10/2026 às 13:10:53 UTC, após oito checks aprovados. O Codex foi sincronizado por fast-forward nessa base, na branch codex/organizacao-colaboracao; checkout do Claude preservado. O CI específico desse merge também passou, conforme o registro abaixo.
- R07/R10 têm PDFs públicos, proveniência e gabaritos mecânicos. R07 usa publicação oficial do TJMG, sem afirmar cobertura de todos os layouts e-SAJ/PJe. R10 é uma imagem real, lida com Tesseract/por; OCR continua partial e sujeito a erros/omissões. Não são gabaritos jurídicos humanos.
- Extrator 0.4.2: além das correções R07/R10 anteriores, ementa aninhada com título isolado/espaçado também conserva contexto/texto e sinaliza ambiguidade, sem alterar a ementa principal. Zero páginas legíveis continua erro explícito; originais preservados, sem dependências ou mudanças de schema/estados.
- DataJud: consulta real em 20/10 encontrou o processo esperado (29,45 s), mas as duas repetições após a correção terminaram em timeout de leitura (42,65 s e 42,40 s). Há oscilação observada, sem causa remota/intermediária comprovada; não houve sucesso real após o patch. O leitor local agora rejeita corpo inválido, identificação incompatível e busca parcial, em vez de indicar ausência/sucesso indevidos. Endpoint, chave, timeout e teste real permanecem os mesmos. Testes de rede exigem JURIS_REDE=1.
- Verificação em 20/10: base focada 60 aprovados e 1 ignorado; 26 regressões novas aprovadas; oito skills PRONTA; pip check sem conflitos. Suíte integral offline: 624 aprovados e 3 ignorados em 742,40 s, sem falhas, JURIS_REDE ausente. R06/R07/R10 executados; ignorados dois testes de rede e o marcador vazio de casos aguardando. Detalhes atuais em docs/revisao-tecnica-2026-10-20.md; registro histórico em docs/validacao-r07-r10-datajud-2026-10-19.md.
- Continuam pendentes revisão jurídica humana e dos gabaritos, segunda avaliação das skills com documentos reais e fechamento formal CL-01/CL-02 pelo responsável. As 19 regras permanecem inativas. O DataJud teve sucesso real, mas não demonstrou estabilidade. R07/R10 não dependem mais de o usuário fornecer PDFs para os casos mecânicos escolhidos. A entrega técnica está integrada e o CI do merge aprovado; a fase de liberação não foi declarada concluída.

## Conferência do CI do merge do PR #4 — 20/10/2026

- Pedido autorizado: conferir o CI, registrar o resultado e fazer commit/push somente desta atualização documental na branch codex/organizacao-colaboracao, preservando o checkout/índice do Claude e as regras inativas. Base da etapa: 7394606a7097dfa8430e2acea15ff7561b50bcba; nenhum outro arquivo modificado.
- PR #4 confirmada como MERGED em main: https://github.com/junior-aguiar-eng/assistente-juridico-avancado/pull/4. Commit documental integrado ac12882; merge 7394606a7097dfa8430e2acea15ff7561b50bcba. A aprovação do CI deste merge é separada dos oito checks anteriores de push/PR.
- CI específico: https://github.com/junior-aguiar-eng/assistente-juridico-avancado/actions/runs/39428218263, evento push, headSha 7394606a7097dfa8430e2acea15ff7561b50bcba. Conferido em **2026-10-20 13:18:29 UTC**: execução **completed**, conclusão **success**. Os quatro jobs de Ubuntu/Windows com Python 3.12/3.13 passaram; em cada job, pytest e revisão mecânica das skills terminaram com sucesso. Último job concluído em **2026-10-20 13:17:24 UTC**.
- O log contém anotações não bloqueantes do GitHub Actions sobre Node.js e a imagem ubuntu-latest. Nenhuma mudança incidental no workflow foi feita. O sucesso do CI não equivale a revisão jurídica nem comprova disponibilidade real do DataJud.
- Verificação documental: diff restrito a docs/COORDENACAO.md e git diff --check sem erros. Testes locais e consultas DataJud não foram repetidos, pois não houve mudança funcional. As 19 regras permanecem inativas; arquivos do Claude, seu índice/HEAD, skills e corpus preservados por hashes. A atualização terá commit próprio e push na branch do Codex, sem outra integração nesta etapa.
- Baseline e evidência: C:/Users/Boni Jr/AppData/Local/Temp/juris-ci-pr4-commit-push-wqe0neq3 (baseline.json, ci-final.json e ci-watch.txt). A referência exata do commit é entregue na conversa, evitando hash autorreferente neste registro.

## Conferência do CI do merge do PR #3 — 20/10/2026

- Pedido autorizado: conferir o CI e atualizar somente este registro no worktree do Codex; preservar checkout/índice do Claude e regras inativas; sem novo commit ou push. Nenhuma nova tarefa funcional, sincronização do Claude ou alteração de branch.
- PR #3 confirmada como MERGED em main: https://github.com/junior-aguiar-eng/assistente-juridico-avancado/pull/3. Commit integrado e3dff29; SHA do merge 9363524651e13d98493ccd2d623299785d419486, igual ao HEAD atual do Codex e à main remota na conferência. A árvore de arquivos do merge é idêntica à entrega local validada.
- CI específico do merge: https://github.com/junior-aguiar-eng/assistente-juridico-avancado/actions/runs/39425121479, evento push, headSha 9363524651e13d98493ccd2d623299785d419486. Primeira conferência em **2026-10-20 12:51:07 UTC**: **in_progress**, sem conclusão; os quatro jobs estavam em execução, com pytest em andamento e revisão mecânica pendente. Naquela conferência, o sucesso dos oito checks anteriores não comprovava o resultado desta execução.
- Nova conferência autorizada em **2026-10-20 12:59:18 UTC**: execução **completed**, conclusão **success**. Os quatro jobs de Ubuntu e Windows, Python 3.12 e 3.13, terminaram com sucesso; em cada job, tanto pytest quanto a revisão mecânica das skills foram concluídos com sucesso. Último job concluído em **2026-10-20 12:54:38 UTC**. O SHA validado é o merge 9363524651e13d98493ccd2d623299785d419486, não apenas a entrega anterior e3dff29.
- Verificação local limitada ao diff documental e à preservação por hashes; não foram repetidos testes locais nem consultas DataJud, pois não houve mudança funcional. Permanecem válidos os resultados locais anteriores com seus limites, sem nova aprovação jurídica.
- Baseline e evidência consultada: C:/Users/Boni Jr/AppData/Local/Temp/juris-registro-ci-pr3-71m704op (baseline.json e ci.json). Escopo de preservação: 106 arquivos acompanhados do Claude, seu índice/HEAD e o PDF ignorado, totalizando 109 itens; todos os arquivos preexistentes do Codex, inclusive rules/br, skills e corpus. Esta atualização fica local e fora do índice; HEAD 9363524 e demais refs não são movimentados. Sem novo commit ou push.
- Conferência final: 109 itens do Claude sem diferenças por SHA-256; somente docs/COORDENACAO.md alterado no Codex, índice vazio e HEAD/refs inalterados. As 19 regras continuam inativas e com bytes preservados; skills e corpus intactos. Resultado em preservacao-final.json no diretório de evidências; git diff --check sem erros.
- Evidência da nova conferência: C:/Users/Boni Jr/AppData/Local/Temp/juris-ci-pr3-aprovado-zvvngx1i (baseline.json e ci-aprovado.json). Alteração limitada a este registro, preservando a observação inicial e as alterações documentais já pendentes. Sem nova execução local de testes, consulta DataJud, ativação de regras, commit ou push. O sucesso do CI não substitui revisão jurídica nem comprova disponibilidade do DataJud real.

## Estado consolidado após o PR #1 — 19/10/2026

Este resumo prevalece sobre os estados históricos das etapas registradas abaixo.

- CX-01, CX-02, CX-03 e CX-04: concluídas, revisadas na RV-01 e integradas em main pelo usuário no PR #1: https://github.com/junior-aguiar-eng/assistente-juridico-avancado/pull/1.
- Commit da entrega: fd2a136f42c118c72de81640a2f4a08d59bb2145. Merge: 39998ba4141d48f6df7c427d43396f0cfeed3e2a, em 19/10/2026 às 19:33:02 UTC. Os oito checks de push/PR da entrega passaram.
- Pós-merge autorizado: confirmar CI de main, sincronizar somente o worktree do Codex e atualizar este registro; nenhuma nova tarefa funcional iniciada.
- Worktree do Codex: branch codex/organizacao-colaboracao avançada por fast-forward para 39998ba, igual a origin/main. A árvore de arquivos desse merge é idêntica à entrega fd2a136; nenhum novo merge local foi criado. A branch local main não foi movimentada.
- CI específico do merge: execução 39311926077 concluída com sucesso nos quatro jobs (Ubuntu e Windows, Python 3.12 e 3.13), incluindo pytest e revisão mecânica das skills: https://github.com/junior-aguiar-eng/assistente-juridico-avancado/actions/runs/39311926077. O SHA validado é o merge 39998ba4141d48f6df7c427d43396f0cfeed3e2a.
- Checkout do Claude permanece na branch fix/fase2-correcoes, HEAD 4e9989c6ede8e6b9c3d6932310a9768a668d49ca. Arquivos pendentes e documentos locais não foram sobrescritos; sua sincronização não faz parte deste pós-merge. Nenhum Git ou teste foi executado no checkout do Claude.
- Ao concluir a sincronização, esta atualização ficou local e fora do índice, sem novo commit ou push. Em seguida, o usuário autorizou seu commit local, exclusivamente em docs/COORDENACAO.md; push permanece não autorizado. Nenhuma alteração de branch do Claude.
- Verificação final: hashes dos 106 arquivos presentes no checkout do Claude e correspondentes aos caminhos versionados do Codex (incluindo os três documentos comuns pendentes no Claude) idênticos à entrada; git diff --check sem erros. Somente docs/COORDENACAO.md alterado no worktree do Codex. Sem nova execução local de testes: árvore integrada idêntica à entrega revisada e CI do merge aprovado.
- Pendências preservadas: fechamento formal de CL-01/CL-02 a confirmar com o responsável; fontes c001/s2 e c005/s1; documentos reais R07/R10; testes de rede; revisão jurídica identificada e segunda avaliação das skills com documentos reais. Regras jurídicas permanecem inativas. Nenhuma dessas tarefas foi iniciada.

## Base e locais

### Commit local dos 18 arquivos — autorizado em 20/10/2026

- Pedido: registrar em um commit local os 18 arquivos pendentes do Codex, preservando o checkout do Claude e as regras inativas. Sem push ou merge.
- Responsável: Codex; branch codex/organizacao-colaboracao, base fcbe5d2ddc1a70c6327abd6a95bfea0631b18bdf. Escopo fechado: os 11 arquivos modificados e os sete novos presentes na entrada. Somente este registro recebe a atualização de autorização; nenhuma implementação adicional.
- Critério: conteúdo staged restrito aos 18 caminhos autorizados, revisão do diff e regressões pertinentes, nenhum arquivo de rules/br alterado, checkout/índice do Claude preservados por hashes e demais branches/refs intactas. A referência exata do commit será entregue na conversa, sem inserir um hash autorreferente neste arquivo.
- Evidência integral anterior: 624 aprovados e 3 ignorados, já registrada na revisão técnica; sem alteração de código desde essa verificação. Nesta etapa: 49 testes focados de DataJud/ementa/proveniência aprovados, 1 de rede ignorado e 38 não selecionados, em 1,65 s, com JURIS_REDE=0. Revisão mecânica: 8 PRONTA, 0 ATENCAO e 0 PREOCUPACAO_MATERIAL. Suíte integral não repetida; nenhuma nova consulta externa. A autorização de commit substitui somente a restrição histórica de não versionar esta entrega; não autoriza integração ou liberação jurídica.
- Baseline e logs próprios: C:/Users/Boni Jr/AppData/Local/Temp/juris-commit-local-20261020-9gnxnnbe. Entrada: índice do Codex vazio; hashes de 106 arquivos acompanhados do Claude, do seu índice/HEAD e do PDF ignorado registrados, somente por leitura.

### Revisão do diff e continuidade técnica — autorizada em 20/10/2026

- Responsável: Codex; worktree C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal, branch codex/organizacao-colaboracao, HEAD fcbe5d2ddc1a70c6327abd6a95bfea0631b18bdf. Pedido: revisar diff local e avançar pendências técnicas; preservar Claude, regras inativas, sem commit ou push.
- Escopo: revisar todos os arquivos modificados/novos da entrega R07/R10/DataJud e preservar as alterações anteriores. Reproduzir dois riscos encontrados: título EMENTA isolado/espaçado dentro de narrativa contorna o aviso inline; resposta DataJud sem hits válidos ou com busca incompleta pode virar nao_encontrado. Correções somente se reproduzidas, em scripts/extract.py, scripts/datajud.py e respectivos testes. Atualizar este registro, relatório de revisão e documentação comprovadamente desatualizada. Contratos/minutas e tarefas CL-01/CL-02 não serão alterados.
- Critérios: contexto e texto da ementa aninhada preservados com aviso/partial, sem alterar ementas principais; resposta incompleta/inválida da API gera falha explícita e saída CLI 1, nunca ausência; resposta válida continua aceita. Testes primeiro, suíte offline integral e revisão mecânica; consulta pública DataJud separada, sem flexibilizar seu teste. Sem dependências, novos estados/schema ou alteração de originais/corpus/regras.
- Baseline de entrada e logs próprios em C:/Users/Boni Jr/AppData/Local/Temp/juris-revisao-20261020-mvoshh6b. Hashes de 106 arquivos do checkout Claude registrados sem executar Git ou testes nele. Índice vazio.
- Entrega: dois achados reproduzidos e corrigidos, em revisão local. Extrator 0.4.2 preserva ementa aninhada isolada/espaçada; DataJud normaliza somente resposta válida e trata falhas de formato/completude/identificação explicitamente. Base focada 60 aprovados/1 ignorado; 26 regressões novas aprovadas; suíte integral 624 aprovados/3 ignorados em 742,40 s. Nenhum gabarito mecânico anterior relaxado. Rede: uma aprovação antes do patch e dois timeouts depois; o patch não tem sucesso real posterior confirmado. Não se alterou timeout/endpoint/teste para obter aprovação. Documentação de pendências corrigida sem declarar nova avaliação com modelo, aprovação humana ou fechamento de CL-01/CL-02.
- Preservação final: 106 arquivos acompanhados do Claude sem diferenças por SHA-256; regras, skills, fixtures/corpus e shared/escalacao.md preexistente intactos. Índice vazio, branch/HEAD iguais à entrada, whitespace sem erros com cr-at-eol. Sem commit, push, PR ou instalação. Relatório revisável em docs/revisao-tecnica-2026-10-20.md; evidência preservacao-final.json no diretório temporário acima.

### R07/R10 e diagnóstico DataJud — autorizado em 19/10/2026

- Responsável: Codex; branch codex/organizacao-colaboracao; base fcbe5d2ddc1a70c6327abd6a95bfea0631b18bdf. Estado: em execução. Pedido: avançar pendências técnicas, começando pelos casos R07/R10 e DataJud; preservar checkout do Claude, regras jurídicas inativas, sem commit ou push.
- Escopo/arquivos previstos: buscar PDFs públicos oficiais para R07 (decisão cível de TJ) e R10 (digitalização real); conferir visualmente páginas, proveniência e extração; ajustar manifesto e testes de regressão apenas com gabarito mecânico verificável. Diagnosticar a cadeia wiki/chave/transporte/resposta do DataJud; eventual correção mínima em scripts/datajud.py acompanhada de regressões em tests/test_datajud.py. README e este registro serão atualizados conforme evidências. Não alterar dependências, regras, corpus histórico STJ, contratos/minutas ou checkout do Claude.
- Critérios: PDFs autênticos e não sintetizados, URL/data/SHA-256 registrados; R10 exige imagem real e avaliação com/sem OCR, sem promover OCR a texto nativo confiável; R07/R10 só serão prontos com verificações objetivas. DataJud: causa delimitada por reprodução, falhas permanecem explícitas, testes de rede separados dos offline; indisponibilidade não será aceita como processo ausente ou sucesso.
- Entrada: README.md, docs/COORDENACAO.md e shared/escalacao.md já modificados localmente, índice vazio. Baseline SHA-256 de 218 arquivos nas duas cópias e backup documental em C:/Users/Boni Jr/AppData/Local/Temp/juris-r07-r10-datajud-5d92525c8edc406b9f22b0095f8a081e. Todos os comandos de execução usam o worktree do Codex explicitamente.
- Investigação: R07 será acórdão cível público em relatório oficial do TJMG (publicação do tribunal, sem afirmar formato e-SAJ/PJe); R10 será ofício público de Picos, PDF original com uma imagem e zero caracteres nativos. Outro ofício de Taquaral tem xref deslocado: pypdf/PDFium enxergam duas páginas, mas pdfminer devolve catálogo vazio. O arquivo não será reparado nem substituído silenciosamente. Dois defeitos de extração reproduzidos justificam incluir scripts/extract.py e tests/test_extract.py: títulos conhecidos com letras espaçadas não delimitam seções; leitura com zero páginas retorna no_text silencioso. Critério adicional: títulos reconhecidos preservam geometria e texto; catálogo sem páginas legíveis vira falha explícita, inclusive na CLI e no cache. Fixtures novas serão somente públicas e datadas, com proveniência; não há ampliação de área jurídica.
- Suíte integral inicial: 596 aprovados, 3 ignorados, 1 falha em R06 (691,27 s). A página 9 do STF foi reconferida visualmente: o título inline pertence à ementa de outro julgado transcrita no contexto decisao. O código atual preserva esse contexto e sinaliza partial, em vez de iniciar ementa principal até o fim do PDF; a expectativa anterior de ok não refletia essa incerteza. Gabarito mecânico R06 atualizado somente em status/aviso e nova regressão de página, seção e citação. PDF original e demais expectativas preservados. Sem ajuste adicional no código de produção; repetir a verificação com os gabaritos coerentes.
- Entrega final: verificação técnica local concluída e pronta para revisão; consulta real DataJud ainda pendente de sucesso. Rodada focada após R06: 30 aprovados, 1 ignorado. Segunda suíte integral: 598 aprovados, 3 ignorados em 557,23 s, sem falhas, JURIS_REDE ausente. R06/R07/R10 executados. Oito skills PRONTA; pip check sem conflitos; whitespace conferido com cr-at-eol para preservar o manifesto CRLF. Conferência final: 106 arquivos acompanhados do Claude sem diferenças, regras e corpus histórico STJ intactos, alterações anteriores em shared/escalacao.md preservadas, índice vazio e HEAD fcbe5d2 inalterado. Nenhum commit, push, instalação, aprovação humana ou ativação de regra. Detalhes, fontes e limites em docs/validacao-r07-r10-datajud-2026-10-19.md; logs e baseline no diretório temporário próprio acima.

### Reconciliação das fontes c001/s2 e c005/s1 — 19/10/2026

- Autorizada pelo usuário: criar pacote novo, validar vínculos e hashes, preservar histórico e checkout do Claude, sem commit ou push. Base fcbe5d2; branch codex/organizacao-colaboracao; três alterações documentais anteriores preservadas.
- Escopo: pacote autossuficiente fora do repositório, com cópias das fontes primárias existentes e dos datasets recuperados, registros selecionados, ementas derivadas, nova extração, claims reconciliados e manifesto de proveniência. Somente este registro será atualizado no repositório; não alterar scripts, fixtures históricas, estados jurídicos ou regras.
- Critério: hashes recalculados de todos os artefatos; registros selecionados iguais aos encontrados nos datasets; textos derivados reproduzíveis; fontes lidas vinculadas às extrações corretas; validador existente sem erros; sondagens negativas de hash/vínculo rejeitadas. c005 permanece partial/ementa, sem afirmar leitura de inteiro teor ou aprovação humana.
- Entrega local: C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/reconciliacao-stj-2026-10-19. Pacote externo autossuficiente com README, claims.json, extracao.json, histórico copiado, fontes, datasets/seleções, manifesto de hashes e verificar.py reutilizável com --repo. Dados públicos reais não foram acrescentados ao repositório.
- Resultado: quatro documentos com hashes e vínculos conferidos; 15 artefatos identificados no manifesto; seleção de registros e derivação das ementas reproduzidas byte a byte (UTF-8/CRLF). Nova coleta vinculada aos textos derivados, sem afirmar identidade dos bytes históricos; classificação conservadora secundária preservada. Estados das cinco proposições mantidos.
- Validação: CLI validate.py --estrito com nova extração, zero erros e avisos; verificar.py confirma pacote e bloqueio do histórico. Dez mutações em memória rejeitadas (sem ID, ID ausente, documento trocado, hash alterado e trecho inventado, em ambas as referências); índice vazio rejeitado. Duas cópias temporárias com adulteração de texto/dataset também recusadas. Resultados em validacao.json e negativos_arquivos.json no pacote.
- Regressões CX-01 repetidas: 43 aprovadas em 3,76 s. Não repetida suíte integral: scripts e fixtures do repositório não foram modificados por esta reconciliação. Nenhuma aprovação humana emitida ou liberação jurídica avaliada; c005 segue sem inteiro teor.
- Preservação final por hashes: somente este registro mudou entre os arquivos preexistentes do Codex; README.md e shared/escalacao.md mantêm as alterações da etapa anterior, sem mudanças nesta tarefa. Checkout do Claude e corpus histórico intactos. git diff --check sem erros; índice vazio; sem commit ou push.

### Continuidade por prioridade — autorizada em 19/10/2026

- Escopo: confirmar CI do PR #2, sincronizar o worktree do Codex, conferir evidências existentes de CL-01/CL-02, tentar recuperar fontes públicas e executar os dois testes de rede existentes; corrigir divergências documentais verificáveis. Sem ativar regras, assumir revisão humana, modificar corpus histórico ou executar tarefas no checkout do Claude.
- Codex sincronizado por fast-forward para fcbe5d2ddc1a70c6327abd6a95bfea0631b18bdf, merge do PR #2. Arquivos previstos para documentação: este registro, README.md e shared/escalacao.md. Critério: manifesto, política de consultas já autorizada e descrição do CI coerentes; resultados de rede identificados sem converter indisponibilidade em sucesso.
- CI do merge do PR #2 confirmado: execução 39332752818 concluída com sucesso nos quatro jobs de Ubuntu/Windows e Python 3.12/3.13, no SHA fcbe5d2: https://github.com/junior-aguiar-eng/assistente-juridico-avancado/actions/runs/39332752818.
- CL-01/CL-02: código, testes e corpus presentes; fechamento formal pelo responsável não demonstrado. governance/revisor-juridico.md declara revisão jurídica não realizada; não marcar tais tarefas como juridicamente aprovadas.
- Fontes públicas recuperadas em nova coleta: registros STJ 953016 (AREsp 2432194, registro 202302535191) e 942828 (AREsp 2789755, registro 202404234365), com os trechos das referências c001/s2 e c005/s1 encontrados nas ementas. Os hashes dos datasets atuais diferem dos content_hash históricos; não se demonstrou equivalência dos bytes antigos nem recuperação do inteiro teor de c005. Nenhum vínculo foi inserido no claims.json histórico.
- Evidências da coleta fora do repositório: C:/Users/BONIJR~1/AppData/Local/Temp/juris-recuperacao-qbvqum87 (datasets brutos, registros individuais, ementas derivadas, extracao.json e manifest.json com hashes/URL/data). Documentos derivados extraídos com status ok: doc-26a20429567a e doc-6f0b48cb5a7e. A primeira tentativa de c001 expirou; a segunda recuperou o dataset. A reconciliação em pacote novo permanece pendente; o pacote histórico continua bloqueado.
- Rede executada explicitamente com JURIS_REDE=1: 1 aprovado (download real do STJ com texto igual ao caso de teste) e 1 falhou (DataJud/TJSP retornou erro_de_acesso, em vez de encontrado), em 68,47 s. Falha externa observada, sem causa raiz estabelecida; não alterar o teste para aceitar indisponibilidade nem inferir inexistência do processo. Variável removida após execução.
- Documentação corrigida: manifesto tem dez casos prontos, incluindo R06/STF, e dois pendentes; README reconhece CI já executado; shared/escalacao.md respeita o padrão de consultas permitidas já autorizado, sem novo bloqueio por política ausente. Teste existente dessa política: 1 aprovado em 0,23 s. Corpus histórico, regras e scripts preservados.
- Conferência mecânica de CL-01: tests/test_contrato.py com 33 aprovações em 3,93 s. Não equivale a fechamento pelo Claude ou revisão jurídica. Alterações documentais desta continuidade permanecem locais, sem commit ou push; checkout do Claude sem diferenças nos hashes conferidos.

Repositório: `https://github.com/junior-aguiar-eng/assistente-juridico-avancado.git`.
Base da preparação: `e3f03f84171648da955922f63ac3989eac7b15b1`.

| Responsável | Diretório local | Branch inicial |
|---|---|---|
| Claude | `C:/Users/Boni Jr/Desktop/Skill Legal` | `fix/fase2-correcoes` |
| Codex | `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal` | `codex/organizacao-colaboracao` |

São duas cópias de arquivos com branches distintas, compartilhando o histórico Git. O worktree do Codex está anexado a este chat. A pasta padrão do chat pode continuar sendo a original: comandos de implementação do Codex devem informar o diretório acima explicitamente.

Os caminhos são desta máquina; em outra máquina, confirmar `git worktree list` e registrar os locais antes de escrever. Não inferir o estado atual a partir desta fotografia: verificar Git novamente em cada tarefa.

## Estado desta preparação

- Checkout original limpo na entrada; implementação preservada.
- Somente AGENTS.md, CLAUDE.md e este documento são adicionados por esta preparação.
- Documentos disponibilizados de forma idêntica nos dois checkouts para leitura imediata pelos agentes.
- Os três documentos ficam pendentes de commit. Não houve push, merge ou mudança de branch do checkout original.
- Para versionar, fazer um único commit de organização na branch escolhida e integrar/sincronizar no outro checkout, conferindo primeiro as cópias locais. Não criar dois commits independentes dos mesmos documentos.
- A preparação não envia instruções ao Claude nem inicia tarefas em seu nome. O usuário deve encaminhar a tarefa ao agente escolhido.

## Divisão inicial das tarefas

Todas as tarefas abaixo estão **reservadas, não iniciadas nesta preparação**. A atribuição organiza responsabilidade; execução depende de pedido específico. Antes de implementar, reconfirmar se a implementação já mudou.

| ID | Responsável por implementar | Escopo proposto | Critério de aceitação |
|---|---|---|---|
| CL-01 | Claude | Consolidar o incremento atual de revisão contratual e preenchimento, preservando o escopo NDA/serviços/SaaS/modelos | Scripts, skills e documentação coerentes; limitações explícitas; testes pertinentes registrados; regras não revisadas permanecem inativas |
| CL-02 | Claude | Organizar fixtures e documentação dos casos contratuais e do corpus STJ já acrescentados | Origem e gabarito identificados; distinguir testes de extração, mecânicos e avaliação jurídica; sem ampliar áreas do produto |
| CX-01 | Codex | Conferência obrigatória de vínculo entre fonte lida, document_id e extração no validador/auditor | Trecho inventado ou documento ausente não passa como verificado; regressões positivas e negativas; preservar casos válidos |
| CX-02 | Codex | Integridade no comando de status do auditor, inclusive entrega interna sem aprovação obrigatória | Artefato alterado/ausente impede liberação; aprovação invalidada ou reprovação não libera uso; regressões pertinentes |
| CX-03 | Codex | Preservação de versões no download Planalto | Download diferente preserva versão anterior e a rastreabilidade dos hashes; sem contornar bloqueios de fontes |
| CX-04 | Codex | Compatibilidade de curingas dos comandos no PowerShell | Comandos documentados e de CI recebem arquivos reais no Windows; regressões e exemplos compatíveis com o shell |
| RV-01 | Agente diferente do implementador | Revisão somente leitura de cada entrega | Achados vinculados ao diff e à fonte; testes confirmados; concordância entre agentes não substitui revisão jurídica |

CL-01 e CL-02 têm prioridade de continuidade para o Claude. CX-01 e CX-02 são os primeiros candidatos de robustecimento para o Codex. CX-03 só começa após confirmar que `scripts/fontes.py` não está sendo alterado pelo Claude.

## Limites de responsabilidade

- Claude: skills e scripts de contratos/minutas, regras inativas e fixtures desses módulos.
- Codex: correções delimitadas de validação, auditoria, integridade e compatibilidade operacional.
- `shared/dados.md`, enums, formatos JSON, estados, AGENTS.md, README, dependências e CI são áreas compartilhadas: um único responsável por mudança, com aviso no registro da tarefa e revisão do outro agente quando solicitada pelo usuário.
- Se uma tarefa exigir arquivo do outro responsável, coordenar a dependência antes de editar. Nenhum responsável implica exclusividade permanente ou autorização para alterações fora da tarefa.
- Não alterar a política de aprovação humana, ativar regras jurídicas ou ampliar o escopo para resolver uma dificuldade técnica.

## Roteiro por incremento

1. O usuário atribui a tarefa a um agente, delimitando o resultado esperado.
2. O implementador confirma checkout, base e alterações locais e registra ID, estado, arquivos previstos e critério de aceitação.
3. Trabalha apenas na sua cópia e executa as verificações apropriadas.
4. Entrega diff, verificações e limitações; commit e push somente quando autorizados.
5. O revisor examina a referência exata, sem editar a implementação durante a revisão. Comunicação entre chats só quando autorizada pelo usuário.
6. Correções ficam com o implementador; integração em `main` ocorre uma alteração por vez, após autorização.
7. O próximo incremento parte da base integrada; sincronização nunca descarta trabalho pendente.

## Modelo curto para atualizar uma tarefa

```text
ID:
Responsável / branch / commit-base:
Estado: reservada | em execução | em revisão | concluída | bloqueada
Escopo e arquivos previstos:
Critério de aceitação:
Verificações executadas e resultados:
Limitações / dependências:
Referência da entrega, se houver:
```

## O que fica fora desta preparação

Correções funcionais do backlog, avaliação com modelo, novos serviços ou dependências, revisão jurídica, instalação/distribuição do pacote, envio de mensagens ao Claude, commits, push, PR e merge.

## Verificação desta preparação

- Suíte offline no worktree do Codex: **390 aprovados e 1 ignorado**, em 163,92 s; `JURIS_REDE=0`. O teste de rede não foi executado.
- Revisão mecânica das skills com caminhos explícitos no PowerShell: **8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL**.
- AGENTS.md, CLAUDE.md e este documento iguais nas duas cópias; remissões locais conferidas.
- Nenhum arquivo previamente versionado foi modificado por esta preparação. HEAD de ambos permanece na base acima; apenas a branch do novo worktree foi criada.
- Essas verificações registram a base inicial. Não comprovam correção jurídica, avaliação com modelo, CI remoto nem resolução das tarefas reservadas.

## CX-01 — execução autorizada em 18/10/2026

- Responsável: Codex; branch `codex/organizacao-colaboracao`; base `e3f03f84171648da955922f63ac3989eac7b15b1`.
- Estado: em execução.
- Escopo: exigir document_id nas fontes declaradas lidas; conferir o vínculo quando houver extração, inclusive índice vazio; preservar fontes não lidas e casos válidos.
- Arquivos previstos: scripts/validate.py, scripts/auditar.py, testes de validação/auditoria e shared/dados.md. A alteração de documentação comum apenas explicita a exigência desta tarefa; nenhum enum ou formato novo.
- Critério: regressão reproduz falha antes da correção; fonte sem id ou fora da extração bloqueia a validação e a auditoria; fonte válida passa e trecho/hash divergentes continuam recusados.
- Fora de escopo: CX-02 a CX-04, contratos, minutas, ativação de regras, dependências e checkout do Claude.

### CX-01 — compatibilidade identificada na validação

- As 29 regressões novas passam com a exigência estrita; os testes anteriores de validação/pesquisa, após completar suas fixtures sintéticas, tiveram 89 aprovações na rodada focada.
- A suíte integral encontrou referências secundárias históricas sem document_id em `tests/casos/verificacao_stj/claims.json`: c001/s2 e c005/s1. Possuem URL, hash e trecho, mas não uma cópia extraída arquivada no caso.
- A nova exigência estrita invalida essas referências e os testes positivos que dependem delas. Não é falha preexistente; a base anterior tinha 390 aprovações e 1 teste de rede ignorado.
- Nenhuma fonte real, hash ou extração foi fabricada ou alterada. Está pendente a decisão do usuário entre exigir vínculo em todas as fontes lidas ou preservar referências secundárias sem vínculo apenas fora da verificação plena.
- Estado: aguardando definição dessa política; não integrar nem declarar a tarefa concluída antes de resolver a compatibilidade e executar novamente as verificações necessárias.

- Resultado da suíte integral nesta versão estrita: **398 aprovados, 21 falharam e 1 de rede ignorado**, em 189,77 s. As 21 falhas decorrem da incompatibilidade documentada com as duas referências secundárias sem vínculo. `git diff --check` sem erros.

### CX-01 — decisão do usuário confirmada

- Política escolhida: exigir document_id de toda fonte lida, inclusive secundária; manter registros sem vínculo bloqueados até recuperar as fontes reais.
- O pacote histórico `tests/casos/verificacao_stj/claims.json` e seus arquivos de origem foram preservados. Os testes agora exigem os dois erros exatos e o bloqueio pela auditoria/CLI.
- Os testes positivos de aprovação usam um subconjunto explícito de c001 a c004, mantendo somente a fonte primária arquivada de c001. Essa fixture é exclusiva dos testes e não representa recuperação ou liberação do pacote histórico completo.
- Primeira rodada focada após adequação à política: 68 testes aprovados. Nova execução integral em andamento, incluindo regressões oficiais/secundárias e CLI.
- A pendência de decisão da rodada anterior está resolvida. A recuperação das referências c001/s2 e c005/s1 permanece pendência de dados, fora desta correção.

### CX-01 — entrega local pronta para revisão

- Estado atual: em revisão; implementação e verificações concluídas no worktree do Codex. Revisão por outro responsável, commit e integração não executados.
- Toda fonte declarada lida exige document_id textual não vazio. Extração fornecida mas vazia não é tratada como ausência de extração. IDs malformados são rejeitados sem exceção nos caminhos cobertos.
- Regressões novas: 43 cenários cobrindo fontes oficiais e secundárias, campo ausente/nulo/vazio/tipo inválido, documento ausente, trecho/hash divergentes, índices vazios, fontes não lidas, pacotes válidos e bloqueio do caso histórico pela CLI.
- Verificação final: `python -B -m pytest -q`, com `JURIS_REDE=0`: **433 aprovados, 1 de rede ignorado**, em 205,43 s.
- Revisão mecânica das skills: **8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL**. `git diff --check` sem erros.
- Os testes integrais aprovados incluem a recusa esperada do pacote histórico; não significam que c001/s2 e c005/s1 foram recuperados ou liberados. Seus registros e fontes permanecem intactos e bloqueados.
- Sem mudança em contratos/minutas, regras, dependências, skills ou checkout do Claude. Sem commit, push, PR ou merge.

### CX-01 — compatibilização com a nova base do Claude

- Autorizada pelo usuário em 18/10/2026; estado: em execução.
- Branch do Codex avançada por fast-forward de e3f03f8 para 4e9989c6ede8e6b9c3d6932310a9768a668d49ca, sem criar commit. Checkout e branch do Claude preservados.
- Cópia de segurança dos arquivos pendentes e patch original fora dos checkouts, em C:/Users/BONIJR~1/AppData/Local/Temp/cx01-compat-3f23tqnr.
- Plano: reproduzir as regressões de vínculo na base nova; reaplicar a CX-01; compatibilizar os testes com --tipo-entrega obrigatório; executar suíte offline, revisão mecânica e conferência do diff.
- Critério: toda fonte lida continua exigindo document_id; referências históricas sem extração permanecem bloqueadas; mudanças do Claude preservadas.
- Decisão: usar este registro existente como roteiro e evidência, sem criar estrutura adicional de planejamento para a compatibilização.
- CX-02 e demais tarefas fora desta etapa; sem commit, push, instalação ou consultas externas.

- Regressões na base nova, antes de reaplicar o patch: 33 falharam e 10 passaram (3,97 s), reproduzindo a ausência da CX-01; a CLI já incluía --tipo-entrega interna para testar o bloqueio pelo vínculo, não erro de argumentos.
- Patch CX-01 reaplicado sem conflitos; único ajuste novo de teste: --tipo-entrega interna em tests/test_fontes_vinculo.py.
- Conferência de preservação: nove arquivos versionados de CX-01 diferem da base; status() idêntico à base nova; corpus versionado intacto; hashes dos arquivos versionados e documentos comuns no checkout do Claude sem alteração.
- Revisão independente somente leitura do diff: nenhum bloqueador encontrado; sem execução de testes pelo revisor.
- Revisão mecânica: 8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL; git diff --check sem erros.
- Suíte integral será executada com JURIS_REDE ausente: o teste novo do DataJud verifica presença/valor verdadeiro da variável e seria ativado até por "0". Nenhum teste ou script do DataJud será alterado nesta tarefa.

- Rodada focada após reaplicar CX-01: 156 aprovados em 451,18 s, abrangendo tests/test_fontes_vinculo.py, test_validate.py, test_validate_extras.py, test_auditar.py, test_auditar_extras.py, test_caso_stj.py e test_pesquisa.py (nomes reais em tests/).
- Suíte integral offline iniciada: python -B -m pytest -q -rs --durations=10, com JURIS_REDE ausente. Resultado pendente até a conclusão da execução.

### CX-01 — compatibilização verificada e pronta para revisão

- Estado atual: em revisão. Compatibilização e verificação local concluídas sobre 4e9989c6ede8e6b9c3d6932310a9768a668d49ca, na branch codex/organizacao-colaboracao.
- Suíte integral: python -B -m pytest -q -rs --durations=10, JURIS_REDE ausente, PYTHONDONTWRITEBYTECODE=1: **506 aprovados e 4 ignorados em 515,62 s**, sem falhas.
- Ignorados: consulta real do DataJud; download real de fontes; R07 (decisão real de TJ ausente); R10 (escaneado real ausente). Os testes locais de OCR foram executados.
- Revisão mecânica: oito skills PRONTA; git diff --check sem erros. Revisão independente estática sem bloqueadores. Isso não equivale a revisão jurídica, CI remoto ou testes das APIs reais.
- Política preservada: toda fonte lida exige document_id; c001/s2 e c005/s1 continuam bloqueados até recuperar seus documentos reais. Nenhum arquivo do corpus histórico foi alterado.
- Alterações do Claude preservadas na nova base; status() permanece idêntico à base. CX-02 não foi implementada e continua pendente em etapa separada.
- As alterações de CX-01 e os documentos locais continuam pendentes, fora do índice; nenhum commit novo, push, PR, instalação ou alteração do checkout do Claude. O fast-forward reutilizou apenas os commits existentes do Claude.
- Logs e cópia de segurança preservados fora do repositório em C:/Users/BONIJR~1/AppData/Local/Temp/cx01-compat-3f23tqnr (red.log, focused.log, full.log e cx01.patch).

## CX-02 — execução autorizada em 18/10/2026

- Responsável: Codex; branch codex/organizacao-colaboracao; base 4e9989c6ede8e6b9c3d6932310a9768a668d49ca, com CX-01 local preservada. Estado: em execução.
- Escopo e arquivos previstos: decisão e diagnóstico de integridade em status() de scripts/auditar.py, regressões em tests/test_status_integridade.py e este registro.
- Hipótese: a condição `aprovada or not obrig` libera uso interno apesar de revisão reprovada/invalidada; o resultado da segunda conferência também substitui os alertas da primeira, ocultando artefatos presentes somente no QC atual.
- Plano: testes com arquivos reais temporários para reproduzir as falhas; correção mínima; regressões novas e CX-01; suíte integral offline; revisão final e conferência de preservação.
- Critério: artefato alterado/ausente, aprovação invalidada e revisão reprovada impedem liberação, inclusive interna. Pacote íntegro sem aprovação continua liberado somente quando esta é dispensada; aprovação válida mantém uso liberado se tecnicamente pronto.
- Preservar estados, formatos, política de aprovação, implementação da CX-01 e checkout do Claude. Sem assinatura de registros, novas dependências, outras tarefas, commit ou push.

- Regressões antes da correção: 8 falharam e 20 passaram em 2,74 s, demonstrando liberação indevida interna e perda de diagnóstico de artefatos do QC atual.
- Correção: combinar os diagnósticos do QC e da aprovação sem duplicação; se uma decisão é fornecida, somente aprovação válida e pacote íntegro/tecnicamente pronto liberam uso. Dispensa interna sem decisão permanece como antes.
- Verificação focada após correção: **71 aprovados em 3,75 s** (28 cenários novos da CX-02 e 43 da CX-01).
- Suíte integral offline iniciada, com JURIS_REDE ausente para não ativar testes de rede; resultado ainda pendente.

- Revisão independente somente leitura: nenhum bloqueador; alteração isolada em status(), preservando CX-01, formatos e política. Não executou testes nem alterou arquivos.
- Conferência por hashes: somente scripts/auditar.py e este registro diferem entre os arquivos preexistentes; nenhum arquivo do checkout do Claude mudou. Alterações fora de status() em auditar.py são idênticas à entrada desta etapa.
- Revisão mecânica das skills: 8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL. git diff --check sem erros.
- Cópia de segurança e logs desta etapa: C:/Users/BONIJR~1/AppData/Local/Temp/cx02-19x8rvh0.

### CX-02 — entrega local verificada

- Estado: em revisão; implementação e verificações locais concluídas, sem integração ou commit.
- Função status() impede liberação com artefatos alterados/ausentes, aprovação invalidada ou revisão reprovada, inclusive para uso interno dispensado de aprovação. Diagnósticos do QC atual e do registro são preservados sem duplicação.
- Contrato mantido: o comando confere o QC e o registro de aprovação indicado; não passa a descobrir registros automaticamente nem a autenticar sua autoria. Sem decisão fornecida, a dispensa só libera pacote tecnicamente pronto e íntegro.
- Regressões: 28 cenários novos com arquivos temporários reais e chamadas de função/CLI. Antes: 8 falhas e 20 aprovações; após: 71 aprovações somando as 43 regressões CX-01.
- Suíte integral offline: python -B -m pytest -q -rs --durations=10, JURIS_REDE ausente, PYTHONDONTWRITEBYTECODE=1: **534 aprovados, 4 ignorados em 702,60 s**, sem falhas.
- Ignorados: dois testes de rede (DataJud e fontes), R07 (decisão real de TJ ausente) e R10 (escaneado real ausente). Nenhuma consulta externa foi executada.
- Revisão mecânica: 8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL. Revisão independente somente leitura sem bloqueadores. git diff --check sem erros.
- Preservação: CX-01 e demais arquivos preexistentes intactos, exceto o trecho status() do auditor e este registro; checkout do Claude sem alteração. Fontes secundárias históricas continuam bloqueadas até recuperar os documentos reais.
- Arquivos desta etapa: scripts/auditar.py (somente status), tests/test_status_integridade.py (novo), docs/COORDENACAO.md. Sem novas dependências, mudança de CLI, autenticação de aprovações ou outras tarefas.
- Branch codex/organizacao-colaboracao; HEAD 4e9989c6ede8e6b9c3d6932310a9768a668d49ca preservado. Sem commit, push, PR ou arquivos no índice. Logs e backup em C:/Users/BONIJR~1/AppData/Local/Temp/cx02-19x8rvh0.

## CX-03 — execução autorizada em 19/10/2026

- Responsável: Codex; branch codex/organizacao-colaboracao; HEAD 4e9989c6ede8e6b9c3d6932310a9768a668d49ca; CX-01 e CX-02 locais preservadas. Estado: em execução.
- Escopo: ramo de download do Planalto em scripts/fontes.py, regressões em tests/test_planalto_versoes.py e este registro. scripts/fontes.py estava sem alteração local na entrada; checkout do Claude permanece na mesma base.
- Causa: o conversor recebe o caminho definitivo e sobrescreve o Markdown anterior antes de verificar sucesso; uma saída ausente pode reutilizar erroneamente o arquivo antigo.
- Plano: reproduzir com conversor local controlado; converter em temporário isolado; armazenar resultado sem substituir arquivos existentes, reutilizando conteúdo idêntico e escolhendo outro nome se houver colisão; validar regressões e suíte integral offline.
- Critério: versões e registros anteriores continuam apontando aos mesmos bytes; conteúdo diferente ganha arquivo próprio; conteúdo igual é reutilizado; falha, saída ausente e timeout não alteram versões anteriores. Hash e local_file do registro correspondem à versão entregue.
- Premissa: preservar o primeiro nome solicitado e usar sufixo de hash para novas versões, como o fluxo binário existente. Colisões no nome recebem contador, sem sobrescrita. Nenhuma mudança em estados, formatos, downloads não Planalto, fetch_oficial.py, dependências ou política de acesso.
- Sem commit, push, integração ou consultas externas.

- Regressões antes da correção: **12 falharam e 2 passaram em 6,06 s**, reproduzindo sobrescrita, reescrita de conteúdo idêntico, falsa reutilização de saída antiga e dano por falha/timeout.
- Implementação: conversão em TemporaryDirectory isolado no destino; após sucesso, _salvar_versao reutiliza bytes idênticos ou cria arquivo com abertura exclusiva, sufixo hash e contador em colisões. Nenhum arquivo existente é aberto para escrita.
- Verificação focada: **123 aprovados e 1 teste de rede ignorado em 17,72 s**, incluindo as 14 regressões novas, testes de fontes, CX-01 e CX-02.
- Suíte integral offline iniciada com JURIS_REDE ausente; resultado ainda pendente.
- Logs e backup desta etapa: C:/Users/BONIJR~1/AppData/Local/Temp/cx03-04w_bjp9.

- Revisão independente somente leitura: nenhum bloqueador, mudança limitada ao import tempfile, helper de armazenamento e ramo Planalto; não executou testes ou edições.
- Conferência por hashes: CX-01, CX-02 e todos os arquivos preexistentes preservados, exceto scripts/fontes.py e este registro. Checkout do Claude sem alterações. Índice vazio.

### CX-03 — entrega local verificada

- Estado: em revisão; implementação e verificações locais concluídas em 19/10/2026, sem commit ou integração.
- Downloads do Planalto são convertidos em pasta temporária isolada; após sucesso, conteúdo diferente é armazenado em arquivo próprio, sem abrir arquivos anteriores para escrita. Conteúdo idêntico reutiliza o arquivo existente sem reescrever; colisões de nome recebem sufixo adicional.
- Os registros anteriores mantêm os caminhos e hashes dos respectivos bytes. Erro, timeout ou saída ausente do conversor não substituem versões anteriores nem reutilizam saída antiga como novo sucesso.
- Regressões: 14 cenários novos (versões distintas, repetição, retorno à versão antiga, arquivo pré-existente sem registro, colisões, falhas, timeout, ausência de saída, erro de execução e CLI). Antes: 12 falhas e 2 aprovações; rodada focada após correção: 123 aprovações e 1 teste de rede ignorado.
- Suíte integral offline: python -B -m pytest -q -rs --durations=10, JURIS_REDE ausente, PYTHONDONTWRITEBYTECODE=1: **548 aprovados e 4 ignorados em 851,97 s**, sem falhas.
- Ignorados: consulta real do DataJud, download real de fontes, R07 (decisão real de TJ ausente) e R10 (escaneado real ausente). A conversão nos testes novos usa processo Python local controlado; não houve consulta externa ao Planalto.
- Revisão mecânica: 8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL. Revisão independente somente leitura sem bloqueadores. git diff --check sem erros.
- Arquivos desta etapa: scripts/fontes.py (import tempfile, helper _salvar_versao e ramo Planalto), tests/test_planalto_versoes.py (novo) e este registro. Sem alteração de fetch_oficial.py, demais downloads, dependências, regras jurídicas ou outras tarefas.
- CX-01, CX-02, arquivos preexistentes fora do escopo e checkout do Claude preservados por conferência de hashes. HEAD 4e9989c6ede8e6b9c3d6932310a9768a668d49ca na branch codex/organizacao-colaboracao; índice vazio. Sem commit, push, PR ou instalação.
- Logs e backup preservados em C:/Users/BONIJR~1/AppData/Local/Temp/cx03-04w_bjp9.

## CX-04 — execução autorizada em 19/10/2026

- Responsável: Codex; branch codex/organizacao-colaboracao; HEAD 4e9989c6ede8e6b9c3d6932310a9768a668d49ca. Estado: em execução. CX-01, CX-02 e CX-03 locais preservadas.
- Diagnóstico: o revisor já expande globs, mas pode descartar padrão sem correspondência se outro argumento produzir arquivos; duplicação gera revisões repetidas; caminhos literais com colchetes podem ser interpretados como padrão. O comando de extração input/* da triagem ainda depende da expansão pelo shell.
- Escopo/arquivos previstos: helper pequeno compartilhado de expansão em scripts/cli_caminhos.py; somente adaptação da entrada CLI em scripts/revisar_skill.py e scripts/extract.py; regressões em tests/test_curingas_cli.py; exemplos README e comando de CI; este registro. Não alterar skills, extratores, OCR, schemas, regras jurídicas ou políticas.
- Plano: reproduzir falhas; expandir padrões no Python, com preferência por caminho literal existente e sem descartar entradas sem correspondência; deduplicar caminhos lexicais; documentar padrões entre aspas; executar comandos em PowerShell 5.1 e PowerShell 7 disponíveis, regressões anteriores e suíte integral offline.
- Critério: comandos do README/CI e input/* funcionam sem expansão do shell; revisor recusa entrada sem arquivo real antes de revisar qualquer subconjunto; extrator mantém relatório failed e saída 2 para arquivo/padrão ausente; deduplicação não resolve links simbólicos para não enfraquecer a recusa existente.
- Premissa: suporte aos padrões glob não recursivos já usados (*, ?, colchetes), sem adicionar opção de recursão ou expandir outras CLIs.
- Sem instalação, consulta externa, commit, push ou alteração do checkout do Claude.

- Regressões antes da correção: **13 falharam e 12 passaram em 22,91 s**, incluindo input/* recebido literalmente no Windows PowerShell e no PowerShell 7.
- Implementação: helper CLI compartilhado de expansão; prioridade ao caminho literal existente, ordenação das correspondências e deduplicação lexical sem resolver links. Padrões ausentes são preservados para relato de erro. O revisor valida todas as entradas antes de revisar; o extrator mantém seu relatório failed/saída 2.
- README e CI usam padrões entre aspas; o próprio Python os expande em PowerShell/Bash. Nenhum SKILL.md alterado.
- Rodada focada: **168 aprovados em 49,52 s**, incluindo 25 cenários CX-04, revisão/gatilhos e regressões CX-01/CX-02/CX-03. Foram executados comandos reais nos dois PowerShells disponíveis, inclusive os exemplos README/CI.
- Suíte integral offline iniciada com JURIS_REDE ausente; resultado ainda pendente. Logs e backup em C:/Users/BONIJR~1/AppData/Local/Temp/cx04-i9dv6xe7.

- Revisão independente somente leitura sem bloqueadores no código. Apontou um exemplo de extract.py ainda sem aspas no README; exemplo padronizado, sem mudança de código ou testes.
- Exemplo literal de extração do README executado adicionalmente em cópia temporária controlada: Windows PowerShell e PowerShell 7 extraíram dois TXT com status ok. Não houve mudança de scripts após a rodada focada.

- Ambientes PowerShell verificados em execução: powershell 5.1.26100.9711; pwsh 7.6.5. Sem alteração de política de execução ou perfis.
- Revisão mecânica pelo comando com curinga entre aspas: 8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL. git diff --check sem erros.
- Hashes dos arquivos preexistentes confirmam alterações somente nos cinco arquivos previstos da CX-04; CX-01, CX-02, CX-03 e checkout do Claude preservados. Nas funções dos scripts, apenas main() foi alterada. Índice vazio.

### CX-04 — entrega local verificada

- Estado: em revisão; implementação e verificações locais concluídas em 19/10/2026, sem commit ou integração.
- revisar_skill.py e extract.py expandem padrões no próprio Python, aceitam caminhos literais com espaços/colchetes e removem repetições mantendo ordem, sem resolver links. Cada CLI mantém seu contrato de erro: revisor recusa entrada que não é arquivo antes de revisar qualquer subconjunto; extrator registra failed e sai com código 2.
- Helper compartilhado pequeno em scripts/cli_caminhos.py. Nos scripts preexistentes, somente importação e entrada main() mudaram; lógica de revisão, extração, OCR, cache e formatos foram preservados.
- README (revisor e extrator) e comando do CI usam padrões entre aspas, sem depender de expansão do shell. Nenhum SKILL.md alterado.
- Regressões novas: 25 cenários. Antes: 13 falhas e 12 aprovações em 22,91 s. Rodada focada após correção: **168 aprovados em 49,52 s**, abrangendo as regressões das CX-01/02/03.
- Comandos reais testados em Windows PowerShell 5.1.26100.9711 e PowerShell 7.6.5, com perfis desativados e sem alterar políticas. Comandos README/CI do revisor revisaram as oito skills; exemplo literal de extração README, verificado adicionalmente em ambos os shells, extraiu dois TXT controlados. CI remoto não executado.
- Suíte integral offline: python -B -m pytest -q -rs --durations=10, JURIS_REDE ausente, PYTHONDONTWRITEBYTECODE=1: **573 aprovados e 4 ignorados em 905,30 s**, sem falhas.
- Ignorados: dois testes de rede (DataJud e fontes), R07 (decisão real de TJ ausente) e R10 (escaneado real ausente). Nenhuma consulta externa, instalação ou serviço adicionado.
- Revisão independente estática sem bloqueadores no código; única omissão apontada foi o exemplo sem aspas de extração no README, corrigido e conferido nos dois shells. Revisão mecânica: 8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL. git diff --check sem erros.
- Arquivos desta etapa: scripts/cli_caminhos.py (novo), scripts/extract.py (somente entrada CLI/importação), scripts/revisar_skill.py (somente CLI/importação/docstring), tests/test_curingas_cli.py (novo), README.md, .github/workflows/ci.yml e este registro.
- CX-01, CX-02, CX-03, demais arquivos preexistentes e checkout do Claude preservados por hashes. HEAD 4e9989c6ede8e6b9c3d6932310a9768a668d49ca, branch codex/organizacao-colaboracao, índice vazio. Sem commit, push, PR ou alteração do checkout original.
- Logs e backup preservados em C:/Users/BONIJR~1/AppData/Local/Temp/cx04-i9dv6xe7.

## RV-01 — revisão conjunta concluída em 19/10/2026

- Escopo: revisão somente leitura das CX-01 a CX-04 sobre a base 4e9989c6ede8e6b9c3d6932310a9768a668d49ca, incluindo diff, arquivos novos, testes e evidências de execução. Revisão independente por agente diferente do implementador, sem bloqueadores encontrados.
- Resultado: não foram identificadas regressões ou incompatibilidades entre vínculo documental obrigatório, gate de integridade, preservação das versões do Planalto e expansão de curingas. Sondagens em memória confirmaram o vínculo da versão correta, a preservação da versão anterior e o bloqueio por alteração ou reprovação.
- Preservação: hashes dos arquivos dos dois checkouts não mudaram durante a revisão. Os 103 arquivos versionados do checkout do Claude foram comparados à base Git sem diferenças de conteúdo; diferenças de terminação CRLF/LF foram consideradas nessa comparação. Skills, regras jurídicas, dependências e corpus histórico preservados.
- Evidências conferidas: suíte integral previamente executada com 573 aprovações e 4 testes ignorados; rodada focada com 168 aprovações; revisão mecânica das oito skills sem alertas. A RV-01 não repetiu pytest nem escreveu arquivos; este registro é posterior, autorizado separadamente pelo usuário.
- Limitações: não comprova correção jurídica, autoria de aprovação humana, CI remoto ou APIs reais. Fontes históricas c001/s2 e c005/s1 continuam bloqueadas até recuperar os documentos. Permanecem ignorados os dois testes de rede e os casos reais R07/R10 ausentes.
- Estado atual das CX-01 a CX-04: implementação local revisada, sem bloqueadores identificados para versionamento local. Integração continua pendente de autorização.

## Versionamento local — autorizado em 19/10/2026

- Pedido: registrar RV-01 e fazer um commit local conjunto das CX-01 a CX-04, incluindo arquivos novos e regras de coordenação, somente na branch codex/organizacao-colaboracao. Sem push ou merge; checkout do Claude preservado.
- Escopo: os 14 arquivos versionados alterados e os nove arquivos novos listados no status de entrada, incluindo AGENTS.md, CLAUDE.md, este registro, helper CLI e regressões. Nenhuma implementação adicional.
- Os registros anteriores descrevem as respectivas etapas; as restrições históricas de não fazer commit foram substituídas exclusivamente pela autorização deste versionamento local. A cópia de coordenação no checkout do Claude permanece intacta; sincronização posterior exige conferir os documentos locais antes de incorporar a versão canônica.
- Verificação anterior ao commit: rodada focada repetida com 168 aprovações em 30,71 s (CX-01 a CX-04, revisão e gatilhos), JURIS_REDE ausente; revisão mecânica repetida com 8 PRONTA, 0 ATENCAO e 0 PREOCUPACAO_MATERIAL; git diff --check sem erros. A suíte integral não foi repetida nesta etapa: o último resultado integral é o registrado na CX-04, 573 aprovações e 4 ignorados.
- A referência exata do commit será entregue na conversa, evitando autorreferência do hash neste documento. O commit registra a entrega local revisada; não representa integração em main, publicação, instalação ou revisão jurídica.
