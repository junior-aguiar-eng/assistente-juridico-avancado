# Checklist de revisão de uma skill

Adaptado da estrutura do `skills-qa` do repositório anthropics/claude-for-legal (Apache-2.0; só a estrutura foi adaptada, ver `THIRD_PARTY_NOTICES.md`). Parte dos itens é verificada por [scripts/revisar_skill.py](../scripts/revisar_skill.py); o resto é revisão humana. Rode o script antes de qualquer mudança ser aceita e a cada release.

```bash
python scripts/revisar_skill.py skills/*/SKILL.md
```

Resultado por skill: `PRONTA`, `ATENCAO` ou `PREOCUPACAO_MATERIAL`.

## Treze parâmetros

| # | Parâmetro | Pergunta | Mecânico? |
|---|---|---|---|
| 1 | Público | Para quem é a skill (papel, familiaridade com IA)? | sim: seção `Público` |
| 2 | Natureza do trabalho | Qual o formato dominante (verificação pontual, transacional, acumulativo)? O comportamento condiz? | sim: presença; coerência é humana |
| 3 | Limiar de delegação | Onde acaba o papel do modelo e começa o do advogado? A passagem é estrutural (estados, pendências, aprovação) ou só um aviso? | parcial |
| 4 | Entradas mínimas | O que fazer quando faltam? (pedir, parar ou seguir com premissa declarada; nunca seguir calado) | sim: seção de entrada |
| 5 | Versão e responsável | Há `version`, `last_reviewed` e `owner` no frontmatter? | sim |
| 6 | Bandas de confiança | Os estados (`unverified`, `partial`, `supported`, `unsupported`) mudam o comportamento? | humana |
| 7 | Modos de falha | As três falhas jurídicas estão tratadas ([falhas-juridicas.md](../shared/falhas-juridicas.md))? | sim: remissão ou seção |
| 8 | Escopo | Há "o que não faz" e o que acontece quando o pedido sai do escopo? | sim: seção `Limites` |
| 9 | Escalação | Há gatilhos para parar e levar a uma pessoa ([escalacao.md](../shared/escalacao.md))? | sim |
| 10 | Superfície de confiança | O que a skill pode fazer no ambiente: hooks, MCP, ferramentas, URLs, escritas, injeção, autoridade jurídica? | sim: varredura |
| 11 | Atualidade | Se traz texto de regra em `references/`, declara `last_verified`, `freshness_window_days`, `freshness_category` e `verified_against`, e a janela está em dia? | sim |
| 12 | Estrutura | Frontmatter com `name` e `description`; seções de entrada e saída, roteiro e limites; exemplo ou caso de referência; salvaguardas? | sim |
| 13 | Conflitos | Os gatilhos se sobrepõem aos de outra skill do pacote? | parcial: descrições comparadas por palavras |

## Três falhas jurídicas (todas precisam estar tratadas)

1. Apoio, não conselho.
2. Sigilo e privilégio.
3. Responsabilidade e decisão humana.

Falha não tratada força `PREOCUPACAO_MATERIAL`, qualquer que seja o resto.

## Veredito

- **PRONTA:** treze parâmetros tratados, três falhas tratadas, varredura limpa.
- **ATENCAO:** um ou dois parâmetros parciais, falhas jurídicas tratadas. Usável sabendo das lacunas.
- **PREOCUPACAO_MATERIAL:** falha jurídica não tratada; escopo ou escalação ausentes; entrada insuficiente tratada em silêncio; saída que funciona como conclusão; achado de injeção ou de execução de código.

A varredura de superfície é heurística: não é auditoria de segurança. Leia o `SKILL.md` você mesmo.

## Revisor

Mudança em limiar de delegação, gatilhos de escalação ou escopo precisa de **dois responsáveis**: mantenedor técnico e revisor jurídico identificado (a nomear; sem ele, as skills de contrato e minuta não são liberadas). Um prompt com nome de advogado não conta como revisor.
