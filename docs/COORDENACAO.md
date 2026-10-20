# Coordenação entre Claude e Codex

Registro inicial: 18/10/2026. Esta preparação organiza o trabalho; não inicia as correções ou expansões listadas abaixo.

## Estado atual — revisão técnica, 20/10/2026

Esta seção atualiza as pendências R07/R10/DataJud dos resumos anteriores; os registros de execução abaixo são históricos.

- Base da entrega do Codex: fcbe5d2, branch codex/organizacao-colaboracao. As alterações da continuidade e reconciliação anteriores foram preservadas. Commit local dos 18 arquivos autorizado em 20/10/2026, conforme o registro abaixo; sem push, merge ou alterações no checkout do Claude.
- R07/R10 têm PDFs públicos, proveniência e gabaritos mecânicos. R07 usa publicação oficial do TJMG, sem afirmar cobertura de todos os layouts e-SAJ/PJe. R10 é uma imagem real, lida com Tesseract/por; OCR continua partial e sujeito a erros/omissões. Não são gabaritos jurídicos humanos.
- Extrator 0.4.2: além das correções R07/R10 anteriores, ementa aninhada com título isolado/espaçado também conserva contexto/texto e sinaliza ambiguidade, sem alterar a ementa principal. Zero páginas legíveis continua erro explícito; originais preservados, sem dependências ou mudanças de schema/estados.
- DataJud: consulta real em 20/10 encontrou o processo esperado (29,45 s), mas as duas repetições após a correção terminaram em timeout de leitura (42,65 s e 42,40 s). Há oscilação observada, sem causa remota/intermediária comprovada; não houve sucesso real após o patch. O leitor local agora rejeita corpo inválido, identificação incompatível e busca parcial, em vez de indicar ausência/sucesso indevidos. Endpoint, chave, timeout e teste real permanecem os mesmos. Testes de rede exigem JURIS_REDE=1.
- Verificação em 20/10: base focada 60 aprovados e 1 ignorado; 26 regressões novas aprovadas; oito skills PRONTA; pip check sem conflitos. Suíte integral offline: 624 aprovados e 3 ignorados em 742,40 s, sem falhas, JURIS_REDE ausente. R06/R07/R10 executados; ignorados dois testes de rede e o marcador vazio de casos aguardando. Detalhes atuais em docs/revisao-tecnica-2026-10-20.md; registro histórico em docs/validacao-r07-r10-datajud-2026-10-19.md.
- Continuam pendentes revisão jurídica humana e dos gabaritos, regras inativas, segunda avaliação das skills com documentos reais, fechamento formal CL-01/CL-02 pelo responsável e integração autorizada separadamente. O DataJud teve sucesso real, mas não demonstrou estabilidade. R07/R10 não dependem mais de o usuário fornecer PDFs para os casos mecânicos escolhidos. A fase de liberação não foi declarada concluída.

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
