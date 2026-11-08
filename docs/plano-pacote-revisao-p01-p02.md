# Pacote de revisão material P01/P02

> Execução: Codex, nesta sessão, conforme `superpowers:executing-plans`. Pedido de preparar e corrigir já autorizado; sem commit ou push.

**Objetivo:** apresentar documentos, trechos literais, atribuições, afirmações e referências lado a lado para conferência humana real.

**Arquitetura:** pacote externo novo, com PDFs públicos intactos, snapshots anteriores preservados e novas extrações derivadas com correções técnicas explícitas. Reutilizar validadores, proposta de inventário, cronologia e auditoria existentes; nenhuma mudança de contrato, detector, dependência ou política de aprovação.

**Tecnologias:** Python >=3.12 e bibliotecas já instaladas; JSON, Markdown e HTML estático.

**Especificação:** pedido do titular; `docs/plano-principal.md`, seção 7; `docs/contratos/pecas-v1.md`; `skills/br-mapear-autos/SKILL.md`; `skills/br-auditar-entrega/SKILL.md`.

## Restrições

- Worktree Codex `codex/organizacao-colaboracao`, base `3ab28e211641acb8fe75da5152fa0235e25fbd4d`; Claude e índice preservados.
- Manter as 19 regras inativas, originais e evidências anteriores intactos.
- Não criar eventos humanos nem arquivo de aprovação; gabaritos estruturais já aprovados não confirmam offsets, atribuição ou entrega.
- Correção de extração implica novo artefato e nova identidade de inventário, sem remapeamento silencioso.
- Pacote de revisão interna de documentos públicos, sem aconselhamento para caso de cliente, pesquisa externa ou certificação de vigência.

## Foco de revisão

- Transcrições não podem virar conclusão própria do órgão julgador.
- Alegações relatadas não podem virar prova primária de fatos materiais.
- Cabeçalhos/rodapés continuam disponíveis; avisos tratados ficam identificados com motivo, fonte e limites.
- Referência deve conter documento, página física, bloco, offsets e fragmentos compatíveis.
- Leitura técnica pelo modelo não deve se passar por conferência humana nem liberar uso material.

## Tarefas

- [x] Preservar baseline e ler visualmente os PDFs e as extrações completas; identificar correções por bloco e trechos centrais.
- [x] Gerar pacote externo por script de preparação da rodada, com proveniência e testes de integridade próprios, sem alterar scripts do produto se não houver defeito reproduzido.
- [x] Elaborar fatos, cronologias, mapas e relatório lado a lado; registrar lacunas e limites de cada afirmação.
- [x] Validar extrações/inventários/fontes, executar auditorias nos dois modos, conferir bloqueio material somente pelas dimensões humanas ainda pendentes e aprovação final ausente.
- [x] Executar suíte offline e revisão mecânica, inspecionar apresentação, revisar diff e hashes; atualizar coordenação e situação da fase 5 sem encerrá-la. Resultado: 1019/5 no ambiente isolado, 14 testes do pacote, 16 passos CLI e oito skills PRONTA. Prévia HTML bloqueada por política; estrutura/links e imagens verificadas. Revisão independente sem achados P1/P2/P3; detalhes em `docs/revisao-material-p01-p02.md`.

## Resultado esperado

Análise `revisao_pronta` para ambos, referências íntegras, sem fatos meramente mecânicos, com material de revisão completo. Uso fundamentado continua recusado enquanto fronteiras/tipos/seções não forem conferidos pela pessoa. Entregar lista precisa dessas decisões; nenhuma aprovação fictícia para obter resultado positivo.
