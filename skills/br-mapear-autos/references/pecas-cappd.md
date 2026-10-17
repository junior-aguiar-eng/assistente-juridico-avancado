# Mapear peças processuais: CAPPD

Roteiro para extrair o conteúdo de petições e decisões, adaptado do `peticao-analyzer` do repositório ma-serra/lex-intelligentia-skills (MIT; só a estrutura foi adaptada, ver `THIRD_PARTY_NOTICES.md`). **Causas de pedir, Argumentos, Pedidos, Provas, Defesas.** Cada item vira fatos em `facts.json` (com `source`) ou entra no `mapa.md`; nada é valorado.

## Por tipo de peça

| Peça | Extrair | Tipo de fato |
|---|---|---|
| Petição inicial | partes e qualificação; natureza da ação e valor da causa; fatos narrados (causa de pedir fática); normas invocadas (causa de pedir jurídica); pedidos principal, subsidiários, tutela de urgência, honorários; provas juntadas e requeridas | fatos narrados: `alegacao` de autor; pedidos: `documentado` (o que a peça pede) |
| Contestação | preliminares; fatos impugnados e fatos admitidos; teses defensivas; documentos juntados; reconvenção | fatos narrados: `alegacao` de réu; "não impugnou": `lacuna` ou nota, ver abaixo |
| Réplica e recursos | o que mudou na tese, novos documentos, pedidos de reforma, pontos de omissão ou contradição apontados | `alegacao` e `documentado` |
| Decisão (sentença, acórdão) | relatório, questões, fundamentos, dispositivo | ato e dispositivo: `documentado`; fatos narrados: `alegacao` da decisão; trecho transcrito: citação |
| Laudo pericial | quesitos, metodologia, conclusões, impugnações | conclusões: `alegacao` do perito |

## Pontos controvertidos

Monte, no `mapa.md`, o quadro **alegação do autor x posição do réu x prova disponível**, com o id de cada fato. O pacote lista; quem decide qual ponto é controvertido para o saneamento é o advogado (ou o juiz).

## Fato não impugnado (CPC, art. 341)

O texto conferido no Planalto (versão compilada lida em 17/10/2026) diz que incumbe ao réu manifestar-se precisamente sobre as alegações de fato da inicial, **presumindo-se verdadeiras as não impugnadas**, salvo se: não for admissível a confissão; a inicial não vier com instrumento que a lei considere da substância do ato; ou o fato contradisser a defesa em seu conjunto. O ônus não se aplica ao defensor público, ao advogado dativo e ao curador especial.

Uso aqui: ao ver um fato da inicial sem resposta na contestação, **anote a observação** (`mapa.md`, coluna "impugnação") com o trecho da contestação examinado. Não grave como `documentado` nem declare o fato provado: a presunção é consequência jurídica, com exceções, e fica com o advogado. Se a contestação não foi fornecida, isso é `lacuna`.

## Armadilhas

- Qualificação das partes e número do processo vêm do cabeçalho: confira o dígito do CNJ com `triagem.py processos`.
- Valor da causa e valores pedidos são `documentado` (o que a peça afirma pedir), não valor devido.
- Peça com pedido ambíguo: registre o trecho e a ambiguidade; não escolha a leitura mais favorável.
