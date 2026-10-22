# Correção da atribuição contextual de citações

Incremento AC-01, autorizado em 21/10/2026, no worktree do Codex, branch
`codex/organizacao-colaboracao`, HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`.
As alterações locais AF-01 e CP-01 foram preservadas. Sem commit ou push.

## Causa e comportamento corrigido

A sonda da CP-01 usou como resultado de R07 o **“Recurso desprovido”** da página
11, que pertence a um precedente transcrito. O resultado próprio do acórdão é
provimento, nas páginas 1 e 12. O PDF preserva os dois resultados; a falha estava
na atribuição dos blocos extraídos, não na existência do texto.

O extrator reconhecia o título da ementa aninhada e avisava sobre a ambiguidade,
mas decidia `is_quote` pelo recuo de cada linha. Como a transcrição usa a mesma
margem do voto e atravessa páginas, seu dispositivo voltava a parecer texto próprio.

O extrator `0.4.3` acompanha a sequência de uma ementa dentro de seção narrativa
até uma referência bibliográfica fechada, com metadados de relatoria e
julgamento/publicação. O intervalo identificado recebe `is_quote: true` e
`quote_basis: contexto_ementa`. A regra não depende de tribunal, processo,
página ou resultado específico. Ementas isoladas, espaçadas e com caixa mista
seguem o mesmo contexto. A ementa principal continua sendo seção própria.

Uma nova ementa não resolve automaticamente o fim de uma anterior. Referência
incompleta ou fronteira dentro de bloco que também contém texto posterior
conserva a incerteza pela tag `atribuicao_ambigua`, em vez de inventar autoria.
Não se apaga ou substitui o texto extraído. O documento pode continuar `partial`.

O validador agora considera a ocorrência no localizador informado. Outra
ocorrência do mesmo texto em página distinta não serve para trocar sua autoria.
Autorias diferentes no mesmo localizador exigem desambiguação, por exemplo com
o `block_id` conferido. A junção de dois blocos de origens distintas também não
apaga a incerteza. Uma fonte secundária não substitui o fundamento próprio da
fonte oficial exigida para `supported`.

`atribuicao_ambigua` gera erro em `supported` e aviso em registros de leitura
parcial. `cited_text=true` continua permitindo uma proposição explicitamente
sobre transcrição delimitada, mas não resolve uma fronteira incerta. O auditor
reutiliza essa validação e bloqueia a atribuição indevida em G02, por API e CLI.
Não houve mudança de schema, dos quatro estados de claims ou da aprovação humana.

## Regressões e verificação

- Rodada anterior à implementação: **18 falhas e 5 passagens**, incluindo a
  atribuição indevida no PDF real e a aceitação pelo auditor/CLI.
- Um defeito no gerador mínimo da fixture sintética removia parênteses PDF não
  escapados. O gerador do novo teste foi corrigido sem relaxar as expectativas;
  a falha de atribuição também foi reproduzida com esse PDF válido usando o
  código original preservado no snapshot externo.
- Três sondas adicionais reproduziram a ambiguidade de ocorrências na mesma
  página e o contorno por fonte secundária antes da correção correspondente.
- A revisão adicional reproduziu duas falhas de fechamento prematuro por referência interna com continuação. A rodada integral intermediária foi interrompida para corrigir essas falhas e não conta como aprovação.
- Rodada focada final: **28 aprovados em 6,81 s**. Inclui o PDF R07, variantes
  sintéticas de caixa, margem, recuo e quantidade de páginas anteriores,
  fechamento multipágina, ausência de fechamento, controle positivo do texto
  próprio, transcrição explícita, validador, auditor e CLI.
- A nova extração de R07 preserva SHA-256 do arquivo, `text_sha256` e a sequência
  do texto. A proposta indevida falha; o resultado próprio e a proposição
  explicitamente sobre o precedente transcrito passam na validação mecânica.
- Suíte integral final offline: **696 aprovados e 3 ignorados em 806,63 s** (13min26s), sem falhas. `JURIS_REDE=0`, `PYTHONDONTWRITEBYTECODE=1`, Python 3.14.6 e temporários próprios. Ignorados os dois testes de rede (DataJud e fontes) e o marcador vazio de casos pendentes. São 28 aprovações adicionais sobre a base local AF-01 de 668.
- Revisão mecânica: **8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL**. `git diff --check` sem erros. A suíte comprova execução local, sem equivaler a revisão jurídica, CI remoto ou instalação.
- Rede, CI remoto, instalação e revisão jurídica humana não executados.

Evidências, snapshots, diff de entrada e reextração nova:
`C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/correcao-atribuicao-citacoes-2026-10-21`.

## Preservação e limites

A versão do extrator muda a chave do cache. O cache `0.4.2`, os QCs, as sondas
e os relatórios anteriores permanecem intactos; não recebem a correção
retroativamente. Para usar a nova atribuição é necessário **reextrair e
reauditar em novos derivados**. Os IDs dos blocos podem mudar; localizadores e
trechos devem ser conferidos na nova extração, sem migrar referências às cegas.

A regra delimita contextos reconhecíveis de transcrição em PDF. Referências em
outros formatos podem continuar ambíguas e exigir conferência no original.
Não prova que uma proposição corresponde semanticamente ao texto, que a regra
se aplica a outro caso ou que o revisor humano aprovou o mérito. A leitura do
contexto, a aplicabilidade e a revisão jurídica continuam necessárias.

A conferência final confirmou **109 itens do Claude e 797 arquivos históricos intactos**, por SHA-256; as **19 regras permanecem inativas e com os mesmos bytes**. Os demais arquivos preexistentes do Codex foram preservados, incluindo o diff funcional AF-01. HEAD/branch mantidos e índice vazio. Nenhuma operação Git, instalação ou teste foi executada no checkout do Claude.

O incremento altera somente `scripts/extract.py`, `scripts/validate.py`, a instrução de atribuição da skill de citações, README e coordenação; acrescenta este relatório e `tests/test_atribuicao_citacoes.py`. O patch específico está nas evidências em `incremento-ac01-final.patch`, separado do diff anterior. A revisão do código foi feita pelo próprio implementador, sem revisão independente ou jurídica.
