# IG-01 — integração de ORG-01 a ORG-03 no worktree Codex

Data: 22/10/2026. Estado: concluída localmente, sem commit ou push.

Pedido: integrar a reconciliação RC-01 ao worktree Codex, preservando o checkout Claude, alterações locais, histórico e as 19 regras inativas; sem commit ou push.

Destino: `C:/Users/Boni Jr/.codex/worktrees/assistente-juridico-codex/Skill Legal`, branch `codex/organizacao-colaboracao`, HEAD-base `abbf85a779627a49ac38def046bbc142bacbacd1`. Fonte: cópia independente da [RC-01](reconciliacao-org-2026-10-22.md), validada com suíte integral 943 aprovados/5 ignorados e 304 focados em ambiente limpo. Esses números são históricos da fonte e não uma nova execução no destino.

## Implementação

- Preflight sem drift em relação aos 127 arquivos-base locais. O delta RC-01 continha 57 arquivos; seus hashes foram verificados antes de copiar. A transferência gerou 166 arquivos do snapshot reconciliado exatamente iguais em bytes aos da cópia isolada.
- Não houve merge de branches, checkout, cherry-pick, staging, commit, push, ativação de regras ou mudança em banco/serviço. O conteúdo foi integrado por arquivo sobre a base local preservada.
- Atribuição contextual, auditoria documental, G04/G05/G10, integridade e formatos locais permanecem. O extrator 0.5.1 inclui OCR, identidade/cache e curingas conciliados. UTF-8/LF explícito nas fixtures impede a falha de locale Windows reproduzida na origem.
- As 19 regras permanecem inativas. Regras, governança, `auditar.py`, `validate.py`, `auditoria_documental.py`, `contrato.py` e manifesto público não receberam alterações nesta transferência.
- R07/TJMG e R10/Picos continuam públicos e intactos. Os privados usam `ORG-R07-PRIVADO`/`ORG-R10-PRIVADO` no manifesto separado; PDFs privados continuam ausentes. [Mapa do corpus](corpus-reconciliado.md).
- Após a igualdade do snapshot, apenas COORDENACAO, o contexto do plano principal e este relatório recebem o registro da integração. A cópia isolada é preservada como fonte.

## Verificação

Executar regressões focadas no destino com o ambiente limpo próprio do Codex criado em RC-01, usando temporários/saídas novos desta integração e `JURIS_REDE=0`. Ambiente externo ao checkout, sem bibliotecas de sistema herdadas. Não instalar dependências no checkout Claude nem usar seus dados de execução.

A conferência final compara os hashes da fonte conciliada e dos arquivos locais que não participam do delta, além de HEAD, refs, índice e estado preservado do Claude. Resultados e limitações serão acrescentados após a execução.

Evidências: `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/integracao-org-codex-2026-10-22-4ywcc8qx`, com snapshot anterior, baseline, transferência, testes e conferência final. Regras e validação técnica não substituem revisão jurídica ou aprovação de entrega. ORG-04/05, rede, Docling opcional, CI remoto, instalação/distribuição e análise do texto privado não integram esta tarefa.

## Resultado final

- No worktree destino: **391 testes aprovados e 2 ignorados em 229,76 s**, com Python 3.14.6/Windows, ambiente limpo externo da RC-01, `JURIS_REDE=0`, bytecode desabilitado e temporários próprios. Os ignorados são exclusivamente `ORG-R07-PRIVADO` e `ORG-R10-PRIVADO`, cujos originais não estão disponíveis.
- Seleção executada: reconciliação/corpus, contrato do inventário, peças/propostas/histórico/CLI, OCR/diagnóstico, atribuição de citações, G04/G05/G10, auditoria documental, redline/issues, curingas PowerShell, versões Planalto, integridade do status e regressões com documentos públicos. Log: `testes-destino.txt`, nas evidências.
- Revisão mecânica: **8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL**. `git diff --check` sem erros; nenhum conteúdo staged. Links locais conferidos. O projeto não configura lint/build separados.
- A suíte integral 943/5 não foi repetida nesta integração: permanece evidência histórica da cópia isolada. Código, testes e fixtures transferidos foram conferidos por hash como idênticos à fonte já validada; somente três documentos receberam o registro desta integração. As 391 regressões acima são execução nova no destino.
- Preservação: os 109 arquivos locais anteriores que não participam do delta continuam idênticos; regras, governança, controles locais e manifesto público intactos. As 19 regras permanecem inativas. A cópia RC-01 original continua integralmente intacta.
- Claude: 106 arquivos acompanhados e 28 metadados Git preservados. Nenhum Git, teste, instalação ou edição foi executado no checkout do Claude. No Codex, branch `codex/organizacao-colaboracao`, HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`, refs e índice permanecem iguais à entrada. Não houve staging, commit, push ou troca de branch.

Conferência detalhada em `preservacao-final.json`; delta desta integração em `delta-integracao.json` e `delta-integracao.patch`, separados dos diffs locais que já existiam. A cópia integrada fica disponível no worktree Codex para revisão. PDFs privados, avaliação jurídica, ORG-04/05, CI remoto e publicação continuam fora desta entrega.
