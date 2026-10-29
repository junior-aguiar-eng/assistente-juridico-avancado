# Coordenação entre Claude e Codex

Registro inicial: 18/10/2026. Esta preparação organiza o trabalho; não inicia as correções ou expansões listadas abaixo.

## Base e locais

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
