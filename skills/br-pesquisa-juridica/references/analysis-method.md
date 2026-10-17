# Organização do raciocínio: FIRAC-JB

Estrutura de raciocínio jurídico adaptada ao direito brasileiro (fatos, questões, regras, aplicação, conclusão), baseada na descrição do método FIRAC-JB do repositório ma-serra/lex-intelligentia-skills (MIT; só a estrutura foi adaptada, ver `THIRD_PARTY_NOTICES.md`). Serve para **organizar o que a pesquisa achou**, não para decidir.

## As cinco etapas e de onde vem cada uma aqui

| Etapa | Pergunta | De onde vem no pacote | Estado esperado |
|---|---|---|---|
| **F**atos | Quem, o quê, quando; o que é incontroverso e o que é disputado | `facts.json` (documentado, alegação, inferência, lacuna) e `cronologia.md` | cada fato com fonte e tipo |
| **I**ssues (questões) | O que precisa ser decidido: preliminares, mérito, pedidos subsidiários | questões da pesquisa, uma proposição por linha | texto do advogado |
| **R**egras | Normas, súmulas, temas e precedentes aplicáveis | `claims.json` | só `supported` conta como regra verificada |
| **A**plicação | Como os fatos se enquadram nas regras | rascunho do advogado | **sempre marcada como não verificada** |
| **C**onclusão | Resultado e consequências | decisão do advogado | fora do pacote |

Regra de ouro: as etapas F e R vêm de fontes lidas; **A e C são do advogado**. O pacote pode listar o que cada regra exigiria dos fatos, mas não escreve a subsunção como se estivesse provada.

## Checklist de fundamentação (CPC, art. 489, § 1º)

O texto do dispositivo foi conferido no Planalto, versão compilada lida em 17/10/2026. Uma decisão judicial (interlocutória, sentença ou acórdão) **não se considera fundamentada** quando:

1. se limita à indicação, à reprodução ou à paráfrase de ato normativo, sem explicar sua relação com a causa ou a questão decidida;
2. emprega conceitos jurídicos indeterminados sem explicar o motivo concreto de sua incidência;
3. invoca motivos que se prestariam a justificar qualquer outra decisão;
4. não enfrenta todos os argumentos deduzidos no processo capazes, em tese, de infirmar a conclusão;
5. se limita a invocar precedente ou súmula, sem identificar seus fundamentos determinantes nem demonstrar que o caso se ajusta a eles;
6. deixa de seguir súmula, jurisprudência ou precedente invocado pela parte, sem demonstrar distinção ou superação.

Uso aqui: ao organizar F-I-R-A-C para uma **peça ou análise de apoio**, o mesmo teste serve de espelho. Para cada precedente da etapa R, registre os **fundamentos determinantes** (o que, no voto, sustenta a tese) e por que o caso se ajusta ou se distingue; isso é o que impede a citação decorativa. Item 4 vira pergunta de revisão: que argumento da parte contrária a análise não enfrentou?

## Como entregar

No `pesquisa.md`, uma seção por etapa, com remissões aos ids de fatos e de proposições. Em A e C, escrever apenas: "a cargo do advogado" e, se útil, as perguntas que ele precisa responder. Itens da etapa R fora de `supported` aparecem com o estado e o que falta.

## O que não fazer

- Não escrever a Conclusão como dispositivo nem como "o tribunal decidirá que...".
- Não converter precedente persuasivo em regra sem registrar órgão, classe e efeito.
- Não usar o FIRAC para cobrir lacuna de fonte: a etapa em que falta fonte fica com a lacuna declarada.
