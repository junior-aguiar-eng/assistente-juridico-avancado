# Revisor jurídico

**Designado:** José Bonifácio de Aguiar Santos Júnior, em 2026-10-18 (indicação feita pelo titular do projeto, em conversa).

**Situação da revisão:** em 30/10/2026 o revisor designado ativou 8 regras do Código Civil (`civ-412`, `413`, `421a`, `422`, `423`, `424`, `473` e `478`), com nome, data e observação em `revisao`. `civ-598`, as 10 da LGPD e as 2 de NDA continuam `inativa`. A designação em si não ativa nada: skills continuam "escritas e testadas mecanicamente".

## O que cabe ao revisor

1. **Ler cada skill** (`skills/*/SKILL.md`) com a [checklist](skill-review-checklist.md) e registrar o resultado e a data (`last_reviewed` só muda depois disso).
2. **Ativar regras de revisão contratual**, uma a uma, em `rules/br/*.json`: conferir a pergunta de revisão e o texto literal, trocar `"status": "inativa"` por `"ativa"` e preencher `revisao.revisor`, `revisao.data` e `revisao.observacao`. O código só usa regra com os três campos preenchidos; a ativação é um ato do revisor e não é feita por script nem por modelo.
3. **Decidir** o que o pacote nunca deve fazer sozinho (escalações em `shared/escalacao.md`) e se os limites declarados nas skills bastam.
4. **Aprovar entregas**: o comando `auditar.py aprovar` exige terminal interativo e a frase digitada pelo próprio revisor; nenhuma aprovação automática existe.

## Como o revisor trabalha com o código

- `python scripts/regras.py listar --incluir-inativas` mostra os rascunhos com o artigo literal.
- `python scripts/regras.py validar --dir rules/br` recusa regra ativa sem revisor e data.
- Alterar o texto literal de uma regra faz `validar --fonte` apontar divergência com a versão compilada lida.
