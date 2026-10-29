# Plano de aprimoramentos e correções (2026-10-29)

Base: HEAD `4e9989c`, branch `fix/fase2-correcoes`. Complementa `docs/planejamento-juris-skills-br-v2.md` (plano vigente) e `docs/COORDENACAO.md` (tarefas CL, CX e RV). Não amplia o escopo.

**Origem do diagnóstico.** README, `AGENTS.md`, `COORDENACAO.md`, `revisao-critica-fase2.md`, `avaliacao-skills-2026-10-18.md`, governança, `garantias.md`, `nda.json` e as `SKILL.md` de auditoria e verificação foram lidas. O código dos scripts e as demais skills não foram lidos. Itens marcados **[confirmar]** dependem de checagem no código antes de execução. A suíte de testes não foi confirmada nesta análise.

## 1. Limites de escopo (inalterados)

Permanecem: recorte documental cível; NDA, serviços/SaaS e preenchimento de modelos; skills em Markdown, scripts Python e revisão humana; regras contratuais inativas até revisão jurídica identificada; aprovação humana digitada em terminal.

Ficam fora deste plano, salvo autorização específica do titular: novos ramos do direito; novos frameworks, banco de dados, serviço persistente, API paga ou integração nova; cálculo de prazos, protocolo e envio a terceiros; interface gráfica; assinatura criptográfica dependente de serviço externo; ativação de regra por script ou modelo.

## 2. Diagnóstico em uma linha por eixo

| Eixo | Estado | Principal lacuna |
|---|---|---|
| Garantias e desenho | sólido | nenhuma estrutural |
| Integridade mecânica | boa, com backlog reconhecido | CX-01 a CX-04 e itens A/M abertos |
| Validação com material real | estreita | uma família de documentos (STJ); R07 e R10 pendentes; STF sem PDF automático |
| Avaliação das skills por modelo | uma rodada, um modelo | segunda rodada com documentos reais |
| Revisão jurídica | não realizada | regras inativas; `last_reviewed` desatualizado |
| Higiene do repositório e CI | fraca | 3 arquivos sem commit; CI nunca executado; worktree `prunable`; selo de testes divergente |

## 3. Plano por ondas

Cada onda tem critério de saída. A ordem respeita dependências; as ondas 1 e 2 podem correr em paralelo, cada uma no checkout do seu responsável.

### Onda 0. Higiene e linha de base (prioridade máxima)

| ID | Tarefa | Responsável | Critério de aceitação |
|---|---|---|---|
| H-01 | Commit único de `AGENTS.md`, `CLAUDE.md` e `docs/COORDENACAO.md` | Claude, com autorização | Um commit; sem duplicação de regras entre os arquivos |
| H-02 | Rodar `python -m pytest -q` (offline) e `revisar_skill.py` no Windows do titular e registrar contagem, tempo e versão do Python | Titular ou Claude | Resultado datado; README e `COORDENACAO.md` com números coerentes (463 + 4 opcionais = 467 coletados, conferem com o selo; os 390 da coordenação são fotografia antiga) |
| H-03 | Primeira execução real do CI (push de branch e PR) e correção do que falhar em Linux e em 3.12/3.13 | Claude | CI verde nas 4 combinações, ou falhas catalogadas com causa. Avaliar incluir 3.14 na matriz, pois o desenvolvimento ocorreu nela |
| H-04 | Confirmar que `.pytest_tmp`, `.pytest_cache` e `__pycache__` não estão rastreados (`git ls-files`) | Claude | **Executado**: nenhum artefato gerado no índice |
| H-05 | Tratar o worktree `prunable` do Codex: reconstituir o caminho ou, com autorização, `git worktree prune` | Titular decide | `git worktree list` sem entrada quebrada; `COORDENACAO.md` atualizado |
| H-06 | Confirmar se `fetch_oficial.py` está no repositório e se não resta dependência de `~/.claude/scripts` | Claude | **Executado**: o script está versionado e não há dependência de `~/.claude/scripts`; resta documentar o fallback de ForgeLex e navegador |
| H-07 | Reduzir o tempo da suíte (~164 s) com marcadores pytest para testes lentos, sem nova dependência | Claude | Execução rápida por padrão; execução completa documentada |
| H-08 | **Executado** em `docs/estado-backlog-2026-10-29.md`. Reconciliar o backlog: tabular o estado atual de cada item A1 a A9, C1 a C6 e M1 a M10 da revisão crítica (resolvido, parcial, aberto) contra o código atual | Claude (leitura) e Codex (revisão RV-01) | Tabela única em `docs/`, com teste ou commit de referência por item resolvido |

**Saída da onda 0:** repositório limpo, números verificados, CI executado.

### Onda 1. Integridade da verificação e da auditoria

Tarefas já reservadas, sob responsabilidade do Codex; mudanças em formatos JSON, enums e `shared/dados.md` exigem um único responsável e aviso prévio.

| ID | Tarefa | Critério de aceitação |
|---|---|---|
| CX-01 | Vínculo obrigatório entre fonte lida, `document_id` e extração no validador e no auditor | Trecho inventado ou documento ausente não passa como verificado; testes positivos e negativos |
| CX-02 | Integridade no `status` do auditor, inclusive entrega interna sem aprovação obrigatória | Artefato alterado ou ausente impede liberação; aprovação invalidada não libera |
| CX-03 | Preservar versões no download do Planalto | Download diferente preserva a versão anterior e os hashes; sem contornar bloqueios |
| CX-04 | Curingas compatíveis com PowerShell em comandos documentados e no CI | Comandos recebem arquivos reais no Windows |
| I-01 | A2 (`trecho_em_citacao`): estender o erro a `supported` de norma e doutrina quando o apoio está só em trecho transcrito, se for o caso | Já é erro para precedente, tema e súmula; avaliar os demais tipos e documentar a decisão |
| I-02 | Fonte secundária `lida` com hash de 64 caracteres não conferível: avisar quando não houver `local_file` nem `--reverificar` | Aviso testado; consta como aberto na avaliação de 18/10 |
| I-03 | Aviso para `documentado` apoiado em peça de parte (M1), com campo que identifique a natureza do documento | Exige mudança de formato em `shared/dados.md`: coordenação prévia e um único responsável |
| I-04 | Fechar M2, M3 e M6: guardar todas as linhas de rodapé removidas, definir timeout/limite de tempo na extração e reforçar o assert do mapeamento | Cada item verificado primeiro no código; testes que afirmem algo útil |
| I-05 | Teste de instrução embutida em PDF (além do já coberto em `test_extract_formatos.py`) e de DOCX com tamanho descomprimido excessivo | Cenários explícitos na suíte |

Itens do levantamento original **já resolvidos** e retirados desta lista: A3, A5, A6, M4, M7, M8, M9 e a parte principal de A2 (ver `docs/estado-backlog-2026-10-29.md`).

**Decisão do titular (I-08).** O modo padrão de `auditar.py` é `analise` (permissivo). Avaliar se o padrão passa a `fundamentada`, o que é mais seguro e quebra a compatibilidade de uso. Também decidir se a ausência de tese `central` vira exigência de declaração (A7).

**Limite aceito, não corrigir (documentar apenas):** `aprovacao.json` pode ser forjado por quem escreve no mesmo disco; o validador não julga a relação semântica entre trecho e proposição. Ambos já constam das skills e da avaliação, e a correção exigiria chave externa ou julgamento humano. Só se reabre por decisão expressa do titular.

**Saída da onda 1:** CX-01 a CX-04 integrados por PR, um por vez, revisados pelo outro agente em modo somente leitura.

### Onda 2. Contratos, minutas e fixtures (Claude)

| ID | Tarefa | Critério de aceitação |
|---|---|---|
| CL-01 | Consolidar o incremento de revisão contratual e preenchimento | Scripts, skills e documentação coerentes; regras não revisadas inativas; limitações explícitas |
| CL-02 | Organizar fixtures e documentação dos casos contratuais e do corpus STJ | Origem e gabarito de cada fixture identificados; separação entre testes de extração, mecânicos e de avaliação jurídica |
| C-01 | Ler a Lei 9.279/1996, art. 195, XI e XII, na versão compilada oficial (via `fontes.py`, com data e hash) e preparar o texto literal da regra de NDA **como rascunho inativo** | `nda.json` com texto literal e fonte; `pendencias_de_fonte` reduzida; permanece `inativa` até o revisor |
| C-02 | Ligar o redline ao `issues.json` (melhoria já listada como futura) | Cada alteração rastreada referencia o `issue_id` |
| C-03 | Corrigir o casamento do localizador por sufixo em `preencher.py` | **Executado em 2026-10-29**: dois testes novos; falhavam antes e passam depois; sem commit |
| C-04 | Revisar mensagens de erro e o relatório de `escalar` na minuta | Relatório legível pelo advogado, sem jargão de schema |

### Onda 3. Material real e segunda avaliação (depende de pessoas)

| ID | Tarefa | Responsável | Critério de aceitação |
|---|---|---|---|
| R-01 | Documento público de TJ para o caso R07 | Titular fornece | Sem dados pessoais nem segredo de justiça; gabarito escrito pelo revisor |
| R-02 | Documento escaneado real para o caso R10, com OCR | Titular fornece | Extração `partial` correta; sem perda silenciosa |
| R-03 | Fluxo do STF: PDF baixado pelo usuário e registrado com `fontes.py registrar`, com limite descrito na skill de pesquisa (A4) | Claude | Tese do STF verificada contra o PDF registrado, ou declarada `partial` de forma visível |
| R-04 | Ampliar o corpus com pelo menos um acórdão de outra turma/tribunal por família (STJ, STF, TJ) | Titular e Claude | Heurísticas de margem, recuo e rodapé testadas fora do acórdão de calibração |
| R-05 | Segunda avaliação das skills: mesmos cenários normal e armadilha, documentos reais e, se possível, outro modelo | Claude executa; titular lê os resultados | Relatório datado em `docs/`, com achados corrigidos ou declarados |

Regra de `AGENTS.md` mantida: originais e casos reais ficam fora do repositório; entram apenas fixtures públicas ou sintéticas autorizadas.

### Onda 4. Revisão jurídica (titular, revisor designado)

1. Ler cada `SKILL.md` com `governance/skill-review-checklist.md`, registrando resultado e data; `last_reviewed` só muda depois disso.
2. Ordem sugerida, pela sensibilidade: `br-auditar-entrega`, `br-verificar-citacoes`, `br-triagem`, `br-mapear-autos`, `br-pesquisa-juridica`, `br-cronologia`, `br-preencher-minuta`, `br-revisar-contrato`.
3. Ativar regras de `rules/br` uma a uma, com `revisao.revisor`, `revisao.data` e `revisao.observacao`; validar com `regras.py validar --dir rules/br`. Começar pelas de maior risco contratual em NDA e serviços/SaaS; LGPD por último, por extensão.
4. Registrar o que o pacote nunca deve fazer sozinho (`shared/escalacao.md`) e se os limites declarados bastam.

### Onda 5. Liberação para uso restrito

Critérios cumulativos para mudar a situação de "pré-lançamento": ondas 0, 1 e 4 concluídas; CI verde; 12 casos de regressão rodando; segunda avaliação realizada; README, selos e `COORDENACAO.md` coerentes com o estado real; `aviso-padrao` mantido em toda saída ao cliente. Mesmo assim, o pacote segue como apoio de organização e conferência, nunca como substituto do advogado.

## 4. Sequência e dependências

H-01 a H-08 → (CX-01 a CX-04 e I-01 a I-05) em paralelo com (CL-01, CL-02, C-01 a C-04) → R-01 a R-05 → Onda 4 → Onda 5. A Onda 4 pode começar logo após H-02 pelas skills de auditoria e verificação, porque o conteúdo normativo delas muda pouco; as demais esperam o fim das ondas 1 e 2 para não revisar texto que será alterado.

## 5. Riscos

| Risco | Mitigação |
|---|---|
| Concentração da revisão no titular | Cronograma por skill; priorizar as duas de maior risco |
| Autor e revisor coincidirem na revisão crítica | Usar o outro agente em RV-01 e revisão independente quando possível; concordância entre agentes não substitui revisão jurídica |
| Conflito lógico entre Claude e Codex em formatos JSON e enums | Um único responsável por mudança em `shared/dados.md`; registro na tarefa |
| Heurísticas de extração sobreajustadas ao STJ | R-02 e R-04 antes de qualquer afirmação de generalidade |
| Divulgar números de testes desatualizados | H-02 com data e comando no próprio README |
| Ampliação de escopo por conveniência técnica | Seção 1 como filtro; qualquer item novo exige autorização registrada |

## 6. Decisões pendentes do titular

1. Autorizar H-01 (commit) e o fluxo de PR para `main`, um incremento por vez.
2. H-05: reconstituir ou podar o worktree do Codex.
3. I-08: padrão do `auditar.py` (`analise` ou `fundamentada`).
4. Fornecer os documentos de R-01 e R-02 (públicos ou anonimizados) e o gabarito.
5. Calendário da Onda 4 e prioridade entre as skills.
6. Se a limitação da aprovação por terminal é aceitável para o uso pretendido, ou se justifica estudar assinatura com chave fora da máquina (fora do escopo atual).
