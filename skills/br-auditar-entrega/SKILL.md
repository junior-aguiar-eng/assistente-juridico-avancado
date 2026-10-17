---
name: br-auditar-entrega
description: Gate final antes de entregar ou usar um pacote jurídico (facts.json, claims.json, extração e fontes): roda a checagem técnica, faz a revisão crítica com objeções fundamentadas e prepara a aprovação humana ligada a hashes. Use quando o usuário pedir para "auditar", "revisar antes de entregar" ou "liberar" um trabalho feito com br-mapear-autos ou br-verificar-citacoes. Não use para aprovar o mérito jurídico, assinar, protocolar ou enviar.
---

# Auditar entrega

Regras comuns: [garantias](../../shared/garantias.md), [estados](../../shared/estados.md), [formatos](../../shared/dados.md). Esta skill **não aprova nada**. Ela diz se o pacote está pronto para a revisão de uma pessoa.

## Três coisas separadas

| Camada | Quem faz | Resultado |
|---|---|---|
| Checagem técnica | `scripts/auditar.py` | `revisao_pronta` ou `bloqueado`, com gates e pendências |
| Revisão crítica | você, pelo roteiro abaixo | objeções com localizador, ou "sem objeção" |
| Aprovação humana | revisor identificado | `aprovada`, `reprovada` ou `invalidada`, ligada a hashes |

`revisao_pronta` libera a revisão. Não libera assinatura, protocolo nem envio.

## Roteiro

1. **Reúna o pacote** num mesmo diretório do caso: `facts.json`, `claims.json`, `extracao.json`, fontes lidas (`fontes/`) e os relatórios (`mapa.md`, `verification.md`).
2. **Rode a checagem técnica:**
   `python scripts/auditar.py auditar --facts derived/facts.json --claims derived/claims.json --extracoes derived/extracao.json --artefato outputs/mapa.md --saida outputs/qc.json`
   Use `--modo fundamentada` quando a entrega apresentar a fundamentação como verificada: tese central sem `supported` passa a bloquear. Em `analise` ela só gera alerta.
3. **Se vier `bloqueado`,** pare e relate o gate que reprovou. Corrija na origem (skill anterior) e rode de novo; não edite o `qc.json`.
4. **Faça a revisão crítica** (abaixo) sobre o pacote e as pendências do `qc.json`.
5. **Escreva `revisao-final.md`** com três blocos separados: resultado técnico (gates e pendências), revisão crítica (objeções) e aprovação humana (pendente).
6. **Peça a decisão a uma pessoa identificada.** Entregue ao revisor o `qc.json`, o `revisao-final.md` e o comando pronto, e peça que ele rode `auditar.py aprovar` (ou `--decisao reprovada`) **no painel de terminal dele**, com `--revisor`, `--registro` e `--declaracao` em suas palavras. O comando mostra o que será registrado e só grava depois que o revisor digita a frase de confirmação (`APROVO` ou `REPROVO` mais 8 caracteres do hash do `qc.json`). Sem console interativo, o script recusa. **Você não aprova nem reprova por ele:** não rode `aprovar` por Bash e não use ferramentas de terminal para digitar a frase.
7. **Confira o estado antes de usar:** `python scripts/auditar.py status outputs/qc.json outputs/aprovacao.json`. Qualquer mudança no pacote, nas fontes ou no `qc.json` torna a aprovação `invalidada`: rode de novo a auditoria.

## Gates da checagem técnica

| Gate | Reprova quando |
|---|---|
| G00 | sem extração informada: nada foi conferido contra o texto lido (só em `--modo fundamentada`; em `analise` é alerta) |
| G01, G02 | `facts.json` ou `claims.json` violam as regras ou não batem com o texto extraído |
| G03 | documento `no_text`, `partial` ou `failed` sem fato `lacuna` que o nomeie (falha silenciosa) |
| G04 | arquivo de origem mudou desde a extração |
| G05 | arquivo de fonte lida não confere com o `content_hash` do claim; em `fundamentada`, também `supported` com fonte oficial sem `local_file` (leitura que não pode ser refeita; em `analise` é alerta) |
| G06 | tese `central` sem `supported` (só em `--modo fundamentada`; em `analise` é alerta) |
| G07, G08 | alertas: proposição refutada, avisos do validador (ex.: `trecho_em_citacao`) |

Alerta não bloqueia, mas vira pendência para o revisor ver.

## Revisão crítica

Para cada tese central e para cada proposição `supported`, procure ativamente o que a derrubaria e registre a objeção com localizador, ou escreva "sem objeção":

- O trecho citado diz o que a proposição afirma, ou só trata do mesmo tema?
- O trecho é fundamento do órgão julgador ou texto transcrito (`is_quote`)?
- Há fonte oficial lida que contradiga, restrinja ou altere (outro acórdão, revogação, tema afetado)?
- Data, órgão, número e tese conferem com o texto da fonte, não com o resumo?
- Alguma alegação foi promovida a fato? Alguma lacuna relevante ficou escondida?
- Valores e datas dos fatos batem com o trecho?

Concordar consigo mesmo ou com outra passagem do modelo não prova nada: a objeção precisa de trecho. Não elimine a pendência por convicção.

## Limites

O script confere forma, hashes e coerência; não julga a correção jurídica nem a vigência futura. A aprovação registra quem decidiu e sobre quais bytes; não substitui assinatura profissional. A confirmação por terminal barra agente e script sem console; não é assinatura nem prova a identidade de quem digita, e um agente com acesso a ferramentas de digitação no terminal do usuário poderia contorná-la, por isso a regra de não usá-las vale. Casos de referência: [verificacao_stj](../../tests/casos/verificacao_stj/claims.json) e [mapeamento_stj](../../tests/casos/mapeamento_stj/facts.json).
