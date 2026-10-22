# Contrato de inventário de peças — versão 1

Entrega ORG-01, 2026-10-22. [Especificação](../especificacao-inventario-pecas.md) · [Plano principal](../plano-principal.md) · [JSON Schema](pecas-v1.schema.json) · [Exemplos e gabaritos](../../tests/casos/pecas_contrato/README.md).

**Estado:** contrato definido e exemplos verificáveis. ORG-02 acrescenta [validador semântico e proposta conservadora opcionais](../inventario-pecas-uso.md). Não existe ainda gate consumidor desse formato. A validação estrutural por JSON Schema não certifica as referências ou a classificação. A validação semântica é implementada/testada em ORG-02; a integração nos consumidores pertence a ORG-04.

## 1. Artefato e identidade

Um `derived/pecas.json` descreve **um documento de origem** da extração. São obrigatórios os campos do esquema, sem propriedades extras. O documento de origem pode ser selecionado de um pacote com `documents` ou de uma extração avulsa; `origem.document_id` deve identificar exatamente um documento. IDs não são inferidos de nomes de arquivos.

| Campo | Semântica exata |
|---|---|
| `schema_version` | String `"1"`. Versão desconhecida é incompatível; não ignorar campos para aceitá-la. |
| `inventario_id` | Identidade estável desta linha de revisões. Trocar a extração exige outro inventário, sem migrar evidências antigas silenciosamente. |
| `revisao`, `anterior_sha256` | Revisão inicial: `1` e `null`. Depois, contador anterior + 1 e SHA-256 dos bytes exatos da revisão anterior. |
| `origem.document_id` | ID existente no documento extraído. O SHA completo continua obrigatório; o prefixo do ID não substitui o hash. |
| `origem.arquivo_sha256` | SHA-256, 64 hex minúsculos, dos bytes imutáveis do original. Deve coincidir com a extração e com a verificação externa do original. |
| `origem.extracao_sha256` | SHA-256 dos **bytes exatos do JSON de extração inteiro**. Em pacote, inclui o pacote completo, não a serialização isolada do documento. Mudança de espaços, caminho ou metadados também muda essa identidade; deve ser tratada explicitamente. |
| `origem.total_paginas` | Quantidade física do PDF, >= 1. A primeira versão cobre documentos com páginas físicas conhecidas; não fabrica páginas de DOCX/TXT. |
| `origem.extrator` | `{nome, versao}`, a partir do registro da extração. `"desconhecido"` registra ausência, nunca supõe a versão instalada hoje. |
| `origem.configuracao_sha256` | Se há `run.params`, hash da codificação UTF-8 de `json.dumps(params, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)`. Se ausente, `null` e pendência `configuracao_nao_registrada`; não reconstruir configuração por adivinhação. Esse hash não substitui a identidade dos bytes da extração. |
| `metodo` | `{nome, versao}` do método que propôs o inventário, separado do extrator. Não há probabilidade de acerto neste contrato. |

`text_sha256`, SHA-256 de arquivo, SHA-256 de extração e IDs de bloco têm papéis diferentes. Nenhum é substituído pelo hash de 64 bits de um fornecedor. Desconhecimento de configuração não impede registrar uma proposta manual sobre um artefato identificado, mas permanece visível.

## 2. Páginas e fragmentos

`paginas` contém exatamente uma entrada para cada número físico de 1 a `total_paginas`, sem duplicatas. `leitura` é `texto_nativo`, `ocr_parcial`, `sem_texto` ou `nao_processada`; sua `origem` é extração ou conferência visual. Não se promove OCR a texto nativo pela classificação de uma peça. Avisos e tags da extração continuam válidos; divergências de leitura precisam ser resolvidas, não ocultadas.

`fragmentos` particiona o texto dos blocos, sem duplicá-lo:

- `id` é o ID do fragmento no inventário; `block_id` aponta o bloco original. Não renomear o bloco.
- `inicio` e `fim` usam **índices de code points Unicode do `block.text` decodificado**, como `texto[inicio:fim]` em Python. Início inclusivo, fim exclusivo, base zero. Não são bytes UTF-8, unidades UTF-16 nem posições no texto normalizado.
- Deve valer `0 <= inicio < fim <= len(block.text)`. Nenhuma normalização, corte de espaços ou hifenização é feita antes da contagem.
- Para cada bloco não vazio do documento selecionado, os intervalos ordenados devem cobrir `[0, len(texto))` exatamente, sem sobreposição ou lacuna. Bloco vazio não recebe fragmento. Um bloco pode ser dividido entre peças ou seções.
- `destino` é **uma** das alternativas: `{classe: "peca", piece_id}`, `{classe: "auxiliar", motivo}` ou `{classe: "nao_atribuido", motivo}`. Capas, rodapés e texto ilegível não precisam ser forçados a peças jurídicas.
- Rodapé condensado que ocorre em várias páginas fica auxiliar e pode ser consultado por sua localização; não é copiado para o corpo de várias peças. Se uma evidência depender desse trecho, sua ocorrência física precisa ser localizada antes do uso material.

`paginas` de cada fragmento contém `inicio`, `fim`, `precisao` e `origem`. Os números são físicos e inclusivos, entre 1 e o total. `precisao: "pagina"` exige início = fim. `"intervalo"` dá um envelope, **não prova presença em todas as páginas intermediárias**. `"indeterminada"` registra que a posição exata não está estabelecida, com pendência obrigatória.

Origem da localização: `extracao`, `conferencia_visual` ou `indeterminada`. Uma inspeção técnica visual não é automaticamente confirmação humana. Um bloco entre várias páginas não tem mapa de caracteres por página só por possuir `page` e `page_end`: para estreitar sua localização, é preciso inspeção rastreável ou nova extração. Limite que dependa de localização indeterminada não pode ser marcado conferido.

O intervalo de um fragmento deve ficar dentro do envelope do bloco fonte. Se o próprio envelope fonte estiver errado, corrigir a extração em novo artefato; não fabricar uma localização incompatível no inventário. Fronteira entre páginas dentro de um bloco exige dividi-lo em fragmentos, preservando seus bytes/texto e ID de origem.

## 3. Peças e seções

`pecas[].id` é o `piece_id`. `ordem` é única e consecutiva, base 1. `inicio` e `fim` são **IDs de fragmentos**, delimitando o primeiro e o último trecho de corpo da peça; não são números de página. Os fragmentos destinados à peça formam seu conteúdo. Página da fronteira vem da localização do fragmento, sem alterar a paginação original.

Para comparar posições, usar página física e, dentro dela, índice do bloco na extração selecionada e offset. Não ordenar por texto do ID nem tratar rodapés auxiliares anexados ao fim como corpo. Se o extrator tem ordem de leitura incompatível com o original, registrar a pendência e corrigir a extração: não corrigir a ordem reescrevendo os blocos antigos. Fragmentos de corpo de peças distintas não podem se intercalar; auxiliares e regiões explicitamente não atribuídas podem ocorrer entre eles.

Os limites precisam apontar fragmentos destinados à própria peça, e suas localizações devem conter o envelope de todos os seus fragmentos. Duas peças podem ocupar uma página; duas peças consecutivas podem ter o mesmo tipo. A mudança de tipo não é condição necessária ou suficiente para começar uma peça.

Taxonomia fechada da v1: `peticao_inicial`, `contestacao`, `peticao`, `recurso`, `manifestacao_mp`, `decisao_interlocutoria`, `despacho`, `sentenca`, `acordao`, `certidao`, `anexo`, `nao_identificada`. São categorias de organização, sem promessa de que o classificador já saiba reconhecê-las. Incerteza usa `nao_identificada` e pendência `tipo_nao_identificado`.

`evidencias` lista sinais (`titulo`, `autoria`, `numeracao`, `continuidade`, `indice`, `conferencia_visual`, `outro`), fragmentos de origem e observação. Citação a outra peça não prova fronteira; menção ao MP não prova autoria. Não duplicar texto pessoal apenas para justificar um rótulo.

`secoes` é uma lista plana, separada de `pecas`. Cada seção informa ID, `piece_id`, tipo proposto, fragmentos e conferência. Tipos: `relatorio`, `fundamentacao`, `voto`, `dispositivo`, `ementa`, `outro`, `nao_identificada`. Seus fragmentos devem pertencer à mesma peça e não integrar outra seção. Para dividir um bloco entre seções, dividir os fragmentos. Texto sem seção é permitido; não significa seção conferida. O `section` antigo não é alterado nem tratado como gabarito do inventário.

## 4. Conferência e histórico

Peças têm conferência de `limites` e de `tipo` independentes. Seções têm `conferencia`. Cada objeto contém `{estado, evento_id}`:

- `proposto`: `evento_id: null`. Não é confirmação humana.
- `conferido` ou `rejeitado`: evento existente, ação correspondente e alvo correto, com ator `humano` e motivo. Exigir o evento não autentica sua autoria criptograficamente; o arquivo local permanece editável.

Cada peça também aponta `proposta_evento_id`, um evento `propor` ou `corrigir` que a inclui nos alvos e identifica sua proposta atual. `eventos` é a sequência cronológica, com IDs únicos, `instante` RFC 3339 com fuso, ator `{tipo, identificador}`, ação, alvos e motivo. Atores `modelo` e `sistema` podem propor/corrigir; não podem registrar as ações de conferência/rejeição humana. Ações permitidas e formato constam do esquema.

Correção material gera outra revisão: mesmo inventário/origem, contador + 1, hash anterior correto e histórico anterior como prefixo inalterado. Append de evento `corrigir` identifica o objeto alterado. Tipo, fronteira ou seção alterados voltam a propostos; a dimensão não alterada pode manter conferência. Isso inclui alterar conteúdo/localização dos fragmentos e sinais em que a dimensão se apoiava, mesmo mantendo seus IDs. A revisão pode registrar correção e nova conferência humana em sequência, com eventos distintos. Não carregar aprovação antiga sobre conteúdo modificado. Preservar snapshots anteriores imutáveis como `derived/pecas.rev-0001.json`, etc.; `pecas.json` é a cópia da revisão corrente, não o único registro.

IDs de inventário, fragmentos, peças, seções, eventos e pendências são globalmente únicos entre esses objetos; IDs de blocos pertencem ao namespace externo da extração. `pagina-N` é referência virtual reservada às páginas e não pode ser ID de objeto. `pendencias.referencias` aponta esses IDs ou páginas virtuais existentes. Referências ativas e alvos de novos eventos devem resolver na revisão atual. Exceção: um novo evento `corrigir` pode apontar um objeto removido que exista na revisão imediatamente anterior, fornecida em `anterior_bytes`, para registrar exclusão ou fusão. Essa exceção não vale na revisão inicial nem para ações de conferência; não autoriza referências a objetos ausentes de ambas as revisões. Eventos no prefixo histórico preservado podem apontar objetos que já não existem: seus alvos são referências históricas, verificadas pela comparação com a revisão anterior, sem exigir recriar peças removidas. Todo objeto removido deve aparecer pelo próprio ID nos alvos de um novo evento `corrigir`, inclusive fragmentos cuja peça também seja alvo; isso mantém o registro persistente da identidade removida nas revisões posteriores. Não reutilizar identidades removidas para representar outro objeto. `material` informa relevância e não declara o gate superado. `pecas: []` e `fragmentos: []` são permitidos quando não existe texto; as páginas e suas pendências continuam obrigatórias.

## 5. Validação e códigos estáveis

O JSON Schema valida forma, campos, enums, hashes, revisões e restrições locais; não verifica somas de cobertura, igualdade de hashes externos, identidade humana ou referências entre objetos. ORG-01 verificou essas invariantes nos exemplos; ORG-02 acrescenta o validador geral opcional e testes adversariais. Com `jsonschema`, usar `Draft202012Validator(schema, format_checker=FormatChecker())` e instalar `rfc3339-validator`: sem esse verificador opcional, o formato `date-time` pode ser silenciosamente ignorado.

Interface implementada em ORG-02, em `scripts/pecas.py`:

```python
def validar_inventario(inventario: dict, extracao_bytes: bytes, *,
                       arquivo_sha256: str,
                       anterior_bytes: bytes | None = None) -> dict:
    # {"valido": bool, "erros": [{"codigo", "onde", "mensagem"}], "avisos": [...]}
    ...
```

O chamador calcula `arquivo_sha256` lendo o original autorizado; não o obtém do inventário que será validado. O validador calcula o hash dos bytes da extração, seleciona o documento de origem e confere o hash nela registrado. O retorno `valido` significa contrato íntegro, não classificação correta, texto conferido, decisão jurídica ou entrega aprovada. A CLI opcional `validar` está descrita no guia de uso; ORG-01, isoladamente, não a publicou.

| Código | Condição recusada pelo validador semântico |
|---|---|
| `estrutura_invalida` | JSON/esquema incompatível, inclusive versão desconhecida |
| `arquivo_divergente` | Hash de original não coincide com inventário/extração |
| `extracao_divergente` | Bytes da extração não coincidem com o hash do inventário |
| `origem_invalida` | Documento ausente/ambíguo ou configuração declarada incompatível com a registrada |
| `id_invalido` | Duplicidade de IDs ou uso de prefixo virtual reservado |
| `referencia_inexistente` | Bloco, fragmento, peça, evento, alvo ou página inexistentes |
| `intervalo_invalido` | Offset fora do texto, início >= fim, envelope impossível |
| `cobertura_invalida` | Lacuna/sobreposição de caracteres; página ausente/duplicada no inventário |
| `limites_incoerentes` | Fronteiras fora da peça, intercalamento ou ordem incompatível |
| `secao_fora_da_peca` | Seção sobre fragmento de outra peça ou sobreposição de seções |
| `conferencia_invalida` | Evento/ator/ação/alvo incompatível; localização indeterminada apresentada como conferida |
| `historico_incompativel` | Cadeia/revisão/origem/prefixo divergente ou conferência antiga mantida após alteração material |
| `leitura_incoerente` | OCR/ilegibilidade ocultos ou leitura declarada incompatível com a evidência disponível |
| `pendencia_ausente` | Ausência de pendência obrigatória para posição/tipo/leitura/configuração desconhecidos ou fragmento não atribuído |

Recusar integridade não é rejeitar juridicamente a peça. Pendências declaradas e propostas incertas podem formar um contrato válido, mas não liberam automaticamente seu uso material; a aplicação desse limite aos consumidores é ORG-04.

## 6. Gabaritos de aceitação

Os exemplos CT01–CT07 e a fusão entre revisões RH01 são simulações de dados, não resultados de parser/modelo. As conferências de RH01 são fictícias e servem somente para verificar sua invalidação após mudança material. O gabarito ORG-R07-PRIVADO registra apenas intervalos físicos e natureza das duas peças, confirmados pelo titular: sentença 1–24 e acórdão 25–38. A âncora de caracteres do snapshot foi inspecionada tecnicamente e permanece **proposta**, separada dessa confirmação humana. Não se confirmou mérito, conteúdo integral, seções ou qualidade de OCR por esse ato.

Casos negativos de ORG-02 exercitam os códigos da tabela, incluindo: extrato com um byte alterado; bloco removido/reordenado; dois objetos com mesmo ID; fragmento que perde um caractere; peça que usa trecho de outra; falsa conferência por modelo; revisão que altera conteúdo mas preserva aprovação; leitura de OCR apresentada como nativa. A implementação é verificada por testes; apenas especificar um caso não comprova seu tratamento.
