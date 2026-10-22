# Especificação: inventário de peças

Versão 1 — 2026-10-22. Documento técnico de **ORG-01**, subordinado ao [plano principal](plano-principal.md). O [contrato exato](contratos/pecas-v1.md), seu [JSON Schema](contratos/pecas-v1.schema.json) e os [gabaritos](../tests/casos/pecas_contrato/README.md) fecham esta etapa. O andamento fica somente no plano principal; um contrato definido não é um segmentador ou gate implementado.

## 1. Problema e objetivo

Um arquivo PDF pode reunir várias peças jurídicas. O extrator atual reconhece alguns títulos como seções e pode carregar a classificação anterior para outra peça. No ORG-R07-PRIVADO, títulos espaçados do acórdão não encerraram a classificação de sentença. A leitura parcial do ORG-R10-PRIVADO é outro problema: classificar a peça não torna seu texto confiável.

Objetivo: representar e conferir peças separadamente das seções internas, preservando a ligação com o arquivo e os blocos usados como evidência. O primeiro escopo é análise **assistida**, com revisão humana; não prometer identificação automática de toda peça em qualquer tribunal.

## 2. Conceitos e saída

| Conceito | Significado |
|---|---|
| Arquivo | Original imutável, identificado por SHA-256; pode conter uma ou várias peças. |
| Extração | Artefato versionado de texto/blocos, associado ao arquivo, extrator e configuração. |
| Peça | Unidade documental com início e fim próprios, como sentença ou acórdão. Não é um chunk por tamanho. |
| Seção | Parte interna da peça, como relatório, fundamentos, voto ou dispositivo. |
| Bloco | Unidade da extração atual, com identificador e localizador preservados. |

Saída proposta: `derived/pecas.json`, separado de `facts.json` e `claims.json`. O inventário referencia os blocos; não precisa duplicar seu texto. Nenhuma alteração imediata nos formatos atuais é autorizada por este documento.

## 3. Contrato mínimo definido em ORG-01

| Grupo | Informação obrigatória e regra |
|---|---|
| Versão e identidade | Versão do inventário; identificador/document_id da extração; SHA-256 do original e do artefato de extração; extrator/versão/configuração identificáveis. |
| Peça | `piece_id` único no inventário; origem; tipo proposto; início/fim; sinais e referências usados na proposta; método e versão. |
| Fronteira | IDs dos fragmentos inicial e final; cada fragmento referencia `block_id` e offsets Unicode `[inicio, fim)`, com posição física e precisão explícita. Não se presume mapa de caracteres por página em bloco multipágina. |
| Conferência dos limites | Estado independente `proposto`, `conferido` ou `rejeitado`; autor/data e origem da decisão quando conferido/rejeitado. O modelo pode propor; não registrar confirmação humana que não ocorreu. |
| Conferência do tipo | Estado separado dos limites, com a mesma disciplina de registro. Limites conferidos não confirmam automaticamente o tipo. |
| Seções | Cada seção pertence a uma peça e aponta blocos/intervalos. Não reutilizar `section` como campo de tipo da peça. |
| Qualidade e pendências | Referenciar status/avisos da extração e trechos ilegíveis; registrar dúvida de fronteira, tipo ou leitura. Não transformar `partial` em texto conferido. |

Nomes de campos, interface futura do validador, convenção de intervalos, códigos de erro e exemplos estão definidos no contrato normativo. O JSON Schema cobre a estrutura; as referências entre objetos, partição, histórico e comparação com originais exigem a validação semântica especificada, implementada em ORG-02 e documentada no [guia de uso](inventario-pecas-uso.md). Não duplicar essas decisões nos consumidores.

### Taxonomia da versão 1

`peticao_inicial`, `contestacao`, `peticao`, `recurso`, `manifestacao_mp`, `decisao_interlocutoria`, `despacho`, `sentenca`, `acordao`, `certidao`, `anexo`, `nao_identificada`.

A taxonomia organiza os dados, sem declarar cobertura automática dos tipos. Capa, índice, página vazia e trecho ilegível têm cobertura explícita, sem serem forçados a uma classe jurídica. Não distinguir decisão de despacho por mera palavra isolada; autoria do MP exige sinais de origem, não uma citação ao órgão.

Classificação sem suporte suficiente usa `nao_identificada` e conserva a pendência. Escore de modelo, se houver, deve indicar método e calibração; não é certificado de acerto nem critério único de conferência.

## 4. Invariantes de integridade

1. Toda posição resolve para o arquivo/extração indicados; hash divergente ou bloco inexistente invalida a ligação. Mudança de parser não remapeia evidências antigas automaticamente.
2. Início precede fim, dentro dos limites da extração. Convenção de posições será única e testável para não duplicar ou perder caracteres nas fronteiras.
3. A cobertura explicita regiões não atribuídas, ilegíveis e não jurídicas. Sobreposição entre peças ou lacunas não justificadas é erro; não se deve escondê-las criando uma peça genérica que aparenta estar conferida.
4. Duas peças podem começar na mesma página e duas peças consecutivas podem ter o mesmo tipo. Fim/início são decisões independentes da troca de classe.
5. Cada seção se mantém dentro de sua peça. Texto que cita uma sentença dentro de um acórdão não se torna outra peça automaticamente.
6. O número impresso na folha e a página física do PDF são campos distintos. Reproduzir decisões ou anexos com numeração própria não altera o localizador físico do original.
7. Classificação e conferência não alteram texto, hashes, originais nem os estados jurídicos `unverified`, `partial`, `supported` e `unsupported`.
8. Uma correção humana gera registro de mudança, sem apagar a proposta anterior necessária para explicar a decisão. Não copiar o mecanismo de aprovação de entregas nem criar `aprovacao.json` por essa via.

## 5. Processamento e integração

1. Receber extração e identidade do original, preservando o inventário por arquivo da triagem.
2. Propor fronteiras com sinais rastreáveis; considerar início/continuação, ordem, títulos, autoria, numeração e estrutura, com abstenção quando necessário.
3. Associar proposta de tipo e seções internas sem carregar a última classe por padrão para todas as páginas seguintes.
4. Apresentar inventário e pendências para conferência; limites e tipos podem ser corrigidos independentemente.
5. Validar a integridade das referências antes de consumir o inventário no mapeamento, cronologia, citações e auditoria.

No fluxo de autos completos, evidência material com limite, atribuição ou leitura não resolvidos deve permanecer pendente e impedir a aprovação técnica fundamentada desse uso. Isso não elimina o fluxo anterior de documentos individuais nem dispensa a verificação de fontes e mérito. O comportamento exato dos gates e sua compatibilidade serão implementados em ORG-04, depois dos testes de integração.

## 6. Limites tecnológicos

- Docling Core é referência para hierarquia/proveniência; a implementação pode começar com os blocos existentes. Docling completo é candidato opcional, condicionado ao piloto.
- Preservar SHA-256 próprio: `DocumentOrigin.binary_hash` do Docling não é equivalente a esse contrato de integridade.
- A abordagem início/continuação do VICTOR é referência metodológica. Não copiar código, pesos ou dataset sem licença/permissão adequada; suas seis classes não definem a taxonomia do projeto.
- OCR é uma dimensão de qualidade independente. Saída de fornecedor não elimina os avisos e limites do projeto. Processamento privado deve permanecer local, conforme a política do caso.
- Não exigir treinamento de modelo, GPU, banco, frontend ou serviço externo para fechar o contrato e construir o primeiro inventário assistido.

## 7. Aceitação e casos obrigatórios

Os exemplos CT01–CT07 e o gabarito físico do ORG-R07-PRIVADO materializam os cenários abaixo. Sua verificação é de contrato, não execução de um classificador. Os casos negativos estruturais são executados; os negativos semânticos estão exercitados pelos testes de ORG-02.

| Cenário | Resultado a conferir |
|---|---|
| ORG-R07-PRIVADO: sentença seguida de acórdão com títulos espaçados | Duas peças com fronteira conferida no original; relatório/voto do acórdão não continuam como seções da sentença. |
| Duas petições consecutivas | Dois inícios mesmo que o tipo seja igual; não fundir só por igualdade de classe. |
| Duas peças na mesma página | Separação por bloco/região e referências físicas corretas. |
| Título de sentença/acórdão dentro de citação | Sem fronteira automática baseada apenas na ocorrência textual. |
| Capa, índice, anexo, continuação sem título, folha vazia | Cobertura e pendências explícitas; sem classificação jurídica forçada. |
| Arquivo/extração alterados ou bloco removido/reordenado | Ligação incompatível recusada; facts/claims antigos não são atualizados silenciosamente. |
| ORG-R10-PRIVADO com leitura insuficiente | Texto não confiável segue parcial e pendente; identificação da peça não promove o OCR. |
| Fluxo antigo sem inventário de peças | Compatibilidade demonstrada no escopo anterior; sem migrar casos implicitamente para análise de autos completos. |

Os PDFs privados não acompanham o repositório. Os testes distribuídos devem usar exemplos anônimos próprios. A ausência do corpus local é informada como não execução; a aprovação jurídica já declarada não funciona como gabarito textual ou de fronteiras desses PDFs.

## 8. Estado da especificação

O contrato está definido, com exemplos anônimos verificáveis e confirmação humana dos intervalos físicos sentença 1–24/acórdão 25–38 do ORG-R07-PRIVADO. A âncora de caracteres do snapshot continua proposta técnica; a confirmação não abrange texto, seções ou mérito. Nenhum classificador, motor de OCR ou migração para Docling foi escolhido por esta entrega. ORG-02 acrescentou validador semântico, proposta de referência e [piloto limitado](piloto-org02-2026-10-22.md), sem adotar outro extrator padrão. O andamento das próximas etapas permanece no plano principal.
