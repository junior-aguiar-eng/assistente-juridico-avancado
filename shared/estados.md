# Estados de verificação

Toda citação ou proposição jurídica carrega **um** destes estados. O padrão é `unverified`.

| Estado | Significa | Exige |
|---|---|---|
| `unverified` | A fonte não foi lida | nada (é o padrão) |
| `partial` | Fonte lida só em parte, ou apoia só parte da proposição, ou só há fonte secundária | indicar o que falta |
| `supported` | Fonte oficial lida, trecho localizado, o trecho apoia a proposição | fonte, data da leitura, hash, trecho exato |
| `unsupported` | Fonte lida e não apoia (ou contradiz) a proposição | fonte, trecho, motivo |

## Regras

1. **Existir não é apoiar.** Confirmar que o acórdão existe não autoriza `supported`.
2. **Indisponível nunca vira inexistente.** Falha de acesso grava `access: source_missing` e mantém `unverified`.
3. **Fonte secundária** (agregadores, informativo comentado, ForgeLex) localiza; não confirma. Teto: `partial`.
4. **Vigência é evidência à parte.** `supported` não afirma que a norma está vigente hoje; vigência exige versão compilada lida, com data.
5. Trecho tachado (`~~`) de página anotada nunca é fonte de regra.

## `unsupported`: contradiz ou não trata

`unsupported` se divide em duas situações com gravidades diferentes. Registre em `source_relation`: `contradiz` (a fonte oficial lida diz o contrário; se a proposição for central, **escale** a um advogado) ou `nao_trata` (a fonte não trata do ponto; costuma bastar trocar a citação). Não confunda com `quote_status: divergente`, que diz que a transcrição da citação não confere com o texto.
