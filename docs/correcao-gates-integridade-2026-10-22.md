# Correção de integridade de G04/G05/G10 — 22/10/2026

Pedido autorizado: corrigir os três gates e o contorno por hash textual, com regressões,
preservando o checkout do Claude, alterações locais e históricos. Implementação no worktree
Codex, branch `codex/organizacao-colaboracao`, base `abbf85a779627a49ac38def046bbc142bacbacd1`.
Sem commit, push, PR, merge, instalação, ativação de regras ou aprovação jurídica.

## Causa e comportamento

- G04 e G05 aplicavam apenas alerta aos arquivos não localizados, inclusive em modo
  fundamentada ou entrega externa. A ausência passa a seguir o rigor já calculado pelo
  auditor: reprovação nesses usos, alerta na análise interna. Divergência de hash continua
  reprovada em qualquer modo.
- G05 comparava o hash textual do registro com a extração, sem exigir que o arquivo local
  fosse o documento extraído. Agora o arquivo precisa ter o SHA-256 bruto dessa extração;
  `content_hash` continua podendo conter o hash bruto ou textual correspondente. Cópia com
  bytes idênticos em outro caminho é aceita; arquivo divergente ou somente normalizado não.
  Sem extração vinculada, a comparação direta do hash do arquivo permanece, sujeita aos
  demais gates. Nenhuma regra do validador de claims foi relaxada.
- G10 dispensava o relatório quando `--relatorio` era omitido. Para `cliente`, `peticao` e
  `contrato`, a omissão passa a reprovar. Auditoria interna pode continuar sem relatório;
  um relatório informado continua sujeito à checagem existente do aviso padrão.

## Regressões e verificação

Novo `tests/test_gates_integridade.py`, com fontes e partes exclusivamente sintéticas.
Abrange modos/tipos de entrega, ausência independente de original/fonte, hash bruto e
textual legítimos, cópia idêntica, arquivo divergente, substituto normalizado, relatório
externo ausente, API/CLI, status e recusa de aprovação de pacote bloqueado. Também verifica
perda de fonte depois da auditoria. Os controles positivos de entrega externa existentes
passam a fornecer explicitamente o relatório exigido; não se removeu nenhuma asserção.

- Antes da correção: **22 falhas e 14 aprovações em 7,64 s**, pelas causas esperadas.
- Depois da correção: **36 aprovados em 6,81 s** na rodada focada.
- Suíte integral offline: **732 aprovados e 3 ignorados em 471,29 s** (7min51s),
  sem falhas, `JURIS_REDE=0`, Python 3.14.6/Windows e temporários próprios. Os ignorados
  são DataJud/rede, fontes/rede e o marcador vazio de casos pendentes. São 36 aprovações
  adicionais sobre a base local de 696, sem alterações no código durante a execução.
- Revisão mecânica: oito skills `PRONTA`, sem alertas materiais. `git diff --check` sem erros.
  Sem consultas externas de teste, CI remoto ou instalação nesta etapa.
- Revisão do diff pelo próprio implementador, sem revisão independente ou jurídica.
- Preservação final: 109 itens do Claude e 859 arquivos históricos sem diferenças por
  SHA-256; 120 dos 125 arquivos Codex anteriores intactos. As cinco alterações existentes
  previstas e os dois arquivos novos são o escopo deste incremento. Branch/HEAD mantidos,
  índice vazio e 19 regras inativas e intactas. Patch incremental separado de AF-01/CP-01/AC-01
  em `incremento-gt01-final.patch`; conferência em `preservacao-final.json` nas evidências.

## Preservação e limites

Baseline, snapshots pré-existentes, logs e patch incremental ficam fora do repositório em
`C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/gates-g04-g05-g10-2026-10-22-j_tcmexo`.
O baseline inclui 125 arquivos Codex, 109 itens Claude e 859 arquivos históricos.
AF-01/CP-01/AC-01 permanecem locais. Nenhuma migração dos QCs, fontes ou aprovações antigas:
as novas verificações exigem rodar `auditar` novamente sobre o pacote disponível.

Esta correção não modifica downloads nem autentica a autoria de `aprovacao.json`. Integridade
de bytes e relatório presente não demonstram apoio semântico, aplicabilidade ou revisão
jurídica humana. As 19 regras contratuais continuam inativas.
