---
name: br-auditar-entrega
description: Gate final antes de entregar ou usar um pacote jurídico (matter.json, facts.json, claims.json, cronologia, extração e fontes): roda a checagem técnica, atribui a faixa de confiança (alta, mista, não entregar), faz a revisão crítica com objeções fundamentadas e prepara a aprovação humana ligada a hashes. Use quando o usuário pedir para "auditar", "revisar antes de entregar" ou "liberar" um trabalho feito com as outras skills do pacote. Não use para aprovar o mérito jurídico, assinar, protocolar ou enviar.
version: 0.2.0
last_reviewed: 2026-10-17
owner: "pendente: mantenedor técnico e revisor jurídico a nomear"
---

# Auditar entrega

Regras comuns: [garantias](../../shared/garantias.md), [estados](../../shared/estados.md), [formatos](../../shared/dados.md), [falhas jurídicas](../../shared/falhas-juridicas.md), [escalação](../../shared/escalacao.md). Esta skill **não aprova nada**. Ela diz se o pacote está pronto para a revisão de uma pessoa.

## Público e natureza do trabalho

Para o advogado responsável e para quem prepara o pacote para ele. Trabalho de revisão com padrão conhecido e itens de julgamento (o teste do destinatário, a leitura adversarial): o script cobre o mecânico e **o resultado sempre volta a uma pessoa**. Um resultado "alta" não é parecer nem sinal verde para assinar.

## Entrada e saída

- **Entrada:** o pacote reunido no diretório do caso: `matter.json`, `facts.json`, `claims.json`, `extracao.json`, fontes lidas (`fontes/`), cronologia e relatórios `.md`; o **tipo de entrega** (`interna`, `cliente`, `peticao`, `contrato`).
- **Saída:** `outputs/qc.json` (gates, pendências, hashes, faixa) e `outputs/revisao-final.md` com três blocos separados: resultado técnico, revisão crítica e aprovação humana. Salve dentro da pasta do caso: a trilha de QC também é documento sensível.

## Três coisas separadas

| Camada | Quem faz | Resultado |
|---|---|---|
| Checagem técnica | `scripts/auditar.py` | `revisao_pronta` ou `bloqueado`, com gates e pendências |
| Revisão crítica | você, pelo roteiro abaixo | objeções com localizador, ou "sem objeção" |
| Aprovação humana | revisor identificado | `aprovada`, `reprovada` ou `invalidada`, ligada a hashes |

**Faixa de confiança** (no `qc.json`): `nao_entregar` (algum gate reprovou), `mista` (alertas, pendências ou entrega externa) e `alta` (só entrega **interna**, sem alerta e sem pendência). Entrega para cliente, petição e contrato **nunca** fica em `alta` e exige aprovação humana.

## Roteiro

1. **Reúna o pacote** no diretório do caso.
2. **Rode a checagem técnica:** `python scripts/auditar.py auditar --facts derived/facts.json --claims derived/claims.json --extracoes derived/extracao.json --matter matter.json --timeline outputs/timeline.json --relatorio outputs/cronologia.md --relatorio outputs/verification.md --tipo-entrega cliente --saida outputs/qc.json`. Use `--modo fundamentada` quando a entrega apresentar a fundamentação como verificada. `--reverificar N` baixa de novo até N fontes oficiais (teses centrais primeiro) e compara o texto com o lido.
3. **Se vier `bloqueado`,** pare e relate o gate. Corrija na origem (skill anterior) e rode de novo; não edite o `qc.json`. No máximo **duas rodadas** de correção por gate: se não passar, declare o gate **não superado**, de forma visível.
4. **Faça a revisão crítica** (abaixo) sobre o pacote e as pendências do `qc.json`.
5. **Escreva `revisao-final.md`** com os três blocos, a faixa e o tipo de entrega.
6. **Peça a decisão a uma pessoa identificada.** Entregue ao revisor o `qc.json`, o `revisao-final.md` e o comando pronto e peça que ele rode `auditar.py aprovar` (ou `--decisao reprovada`) **no painel de terminal dele**, com `--revisor`, `--registro` e `--declaracao` em suas palavras. O comando mostra o que será registrado e só grava depois que o revisor digita a frase de confirmação (`APROVO` ou `REPROVO` mais 8 caracteres do hash do `qc.json`). Sem console interativo, o script recusa. **Você não aprova nem reprova por ele:** não rode `aprovar` por Bash e não use ferramentas de terminal para digitar a frase.
7. **Confira o estado antes de usar:** `python scripts/auditar.py status outputs/qc.json outputs/aprovacao.json`. Qualquer mudança no pacote, nas fontes ou no `qc.json` torna a aprovação `invalidada`. `liberado_para_uso` só é verdadeiro com `revisao_pronta` e, quando obrigatória, com aprovação `aprovada`.

## Gates da checagem técnica

| Gate | Reprova quando |
|---|---|
| G00 | sem extração: nada foi conferido contra o texto lido (em `fundamentada` ou entrega externa; em `analise` é alerta) |
| G01, G02 | `facts.json` ou `claims.json` violam as regras ou não batem com o texto extraído |
| G03 | documento `no_text`, `partial` ou `failed` sem fato `lacuna` que o nomeie |
| G04 | arquivo de origem mudou desde a extração |
| G05 | fonte lida não confere com o `content_hash`; em `fundamentada`, `supported` oficial sem `local_file` (leitura que não se refaz) |
| G06 | tese `central` sem `supported` (em `fundamentada`; em `analise` é alerta) |
| G07, G08 | alertas: proposição refutada (contraditas marcadas para escalar), argumentos que dependem de proposição sem apoio, avisos do validador |
| G09 | cronologia desatualizada em relação ao `facts.json` |
| G10 | relatório de entrega sem o aviso padrão (em `fundamentada` ou entrega externa) |
| G11 | conflito de interesses `pending` ou `not-run` sem bypass (em `fundamentada` ou entrega externa); sem `matter.json` em entrega externa |
| G12 | fontes `nao_triado` quanto a sigilo (em `fundamentada` ou entrega externa); triagem `misto` e segredo de justiça geram alerta |
| G13 | texto de fonte oficial relida diferente do lido (em `fundamentada` ou entrega externa); falha de acesso é alerta |

Alerta não bloqueia, mas vira pendência para o revisor.

## Revisão crítica

Profundidade: **rápida** (itens 1 a 5), **padrão** (1 a 12) e **profunda** (1 a 17, com `--reverificar`). Para entrega externa, use a profunda. Para cada tese central e cada proposição `supported`, procure o que a derrubaria e registre a objeção **com localizador**, ou escreva "sem objeção".

1. **Fatos com fonte:** toda afirmação material aponta documento e trecho; não há fato órfão.
2. **Números e datas conferidos** contra a fonte; se duas fontes divergem, mostre as duas.
3. **Lógica:** a conclusão decorre das premissas; sem salto nem non sequitur.
4. **Completude:** responde ao que foi pedido; omissão óbvia?
5. **Teste do especialista:** um advogado da área leria isto e assentiria, ou se encolheria?
6. **Linguagem vaga** ("diversos", "considerável") sem especificação.
7. **Consistência** de termos, números e classificações em todo o texto.
8. **Metodologia da fonte:** o tipo de fonte serve para o que se afirma (tabela publicada não é situação atual; agregador não é tribunal; ementa não é voto).
9. **Atribuição:** toda citação e dado emprestado tem origem; trecho de citação não é fundamento do órgão que cita.
10. **Formatação e remissões:** estrutura coerente, sem remissão quebrada.
11. **Acionável:** se recomenda ação, é específica o bastante para executar.
12. **Escopo:** ficou no que foi pedido, sem deriva.
13. **Reverificação:** releia ao menos 3 fontes-chave; a checagem original acertou?
14. **Leitura adversarial:** leia como quem quer provar que está errado; qual o ponto mais fraco?
15. **Atualidade:** algum dado pode ter mudado desde a coleta? Anote a data.
16. **Cautela calibrada:** a incerteza foi comunicada? Excesso de confiança é pior que incerteza honesta.
17. **Teste do destinatário:** o que o cliente, o juiz ou a parte contrária perguntaria primeiro?

Para **documento jurídico**, acrescente: jurisdição indicada e coerente; termos definidos usados de forma uniforme; remissões a cláusulas e artigos corretas; ausência de obrigações conflitantes; lei aplicável e foro presentes.

**Concordar consigo mesmo ou com outra passagem do modelo não prova nada:** a objeção precisa de trecho. Se o ambiente permitir subagentes, um segundo verificador adversarial, que não vê o resultado do primeiro, pode rodar os mesmos itens; discordância vira pendência, concordância não elimina nada (opção descrita, não testada).

## Quando escalar

Além de [escalacao.md](../../shared/escalacao.md): entrega para cliente, petição ou contrato (sempre leva a um advogado, qualquer que seja a faixa); concordância sobre afirmação sem fonte; tipo de entrega não identificado; `qc.json` que seria gravado fora da pasta do caso.

## Limites

O script confere forma, hashes e coerência; não julga a correção jurídica nem a vigência futura. A aprovação registra quem decidiu e sobre quais bytes; não substitui assinatura profissional. A confirmação por terminal barra agente e script sem console; não prova a identidade de quem digita, e um agente com ferramenta de digitação no terminal do usuário poderia contorná-la, por isso a regra de não usá-las vale. Casos de referência: [verificacao_stj](../../tests/casos/verificacao_stj/claims.json) e [mapeamento_stj](../../tests/casos/mapeamento_stj/facts.json).
