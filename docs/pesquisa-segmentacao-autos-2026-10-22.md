# Pesquisa: identificação de peças em autos completos

Data: 2026-10-22. Pesquisa de repositórios públicos, com leitura de documentação, licenças e trechos de código nos commits abaixo. Não houve instalação de modelos, benchmark, alteração do extrator nem envio de documentos privados a serviços externos. A recomendação é uma proposta técnica, ainda não uma implementação validada.

Integração no planejamento: [plano principal](plano-principal.md), fase 4A. Esta pesquisa é evidência para as decisões dessa etapa e não mantém uma frente ou ordem de execução independente.

## Conclusão

Há referências consistentes para aproveitar, mas os projetos examinados não fornecem uma solução pronta e validada para todas as peças de autos brasileiros. A combinação recomendada é:

1. **Docling / Docling Core:** estrutura técnica para representar páginas, hierarquia, texto e proveniência; avaliar um adaptador opcional antes de substituir a extração atual.
2. **Método do VICTOR:** classificação sequencial e distinção explícita entre início e continuação de peça. Implementar a adaptação com código próprio e taxonomia adequada ao projeto; não copiar o código sem esclarecer sua licença.
3. **Inventário jurídico próprio:** documento/peça separado de seção interna, incerteza explícita e confirmação humana das fronteiras e dos tipos.

O problema não se resolve apenas com outra biblioteca de PDF, com divisão por tamanho de texto ou com um modelo que classifique uma decisão isolada.

## Projetos examinados

| Projeto | Evidência observada | Aproveitamento e limites | Licença do código |
|---|---|---|---|
| [Docling](https://github.com/docling-project/docling/tree/7d5fc2a51e563d7938731e8c0d61fb6324a1ae52) e [Docling Core](https://github.com/docling-project/docling-core/tree/b501ec8011181db4a08a45b27a47fe7f66814cbe) | Modelo Pydantic `DoclingDocument`, hierarquia de itens e grupos, páginas e `ProvenanceItem` com página, caixa geométrica e intervalo de caracteres; testes do modelo presentes no repositório. Pipeline com opções de OCR e controle de serviços remotos. | Melhor candidato estrutural. Seus rótulos de layout, como título e cabeçalho de seção, não são classes jurídicas como sentença ou manifestação do MP. Precisará de camada própria para delimitar peças. | MIT; licenças dos modelos devem ser verificadas separadamente. |
| [VICTOR — repositório dos autores](https://github.com/peluz/VICTOR-dataset/tree/e13e65a90477074d94c3434a5f0e576c655f2a7b) | Experimentos brasileiros de classificação com seis tipos e pós-processamento por CRF; o notebook constrói rótulos `B-` e `I-` e agrupa sequências por `process_id`. | Referência mais diretamente ligada ao problema de tipos e fronteiras de peças. Classes e domínio do STF são restritos; não equivalem à taxonomia geral de autos. O código consultado depende de arquivos de dados e modelos externos e usa APIs antigas: não é componente pronto para instalar. | Não encontrei arquivo de licença nem declaração explícita na árvore consultada. Referência metodológica, sem incorporar código, dados ou pesos. |
| [Unstructured](https://github.com/Unstructured-IO/unstructured/tree/5618dcaa7d146cddf1a0cf23117d5740d5e579ef) | Elementos com `page_number`, `parent_id` e `category_depth`; `chunk_by_title` cria divisões por títulos, metadados e limites de tamanho. | Alternativa para extração e representação. Chunk não equivale a peça processual: a divisão pode ser por tamanho e a classificação jurídica precisa de outra camada. | Apache-2.0 na biblioteca; componentes e modelos adicionais precisam de conferência própria. |
| [LegalSeg](https://github.com/ShubhamKumarNigam/LegalSeg/tree/af1b45c52cab22a71ddea0bf13c987741b16f042) | Dataset e experimentos para papéis retóricos de sentenças em decisões judiciais indianas; documentação de modelos contextuais. | Útil para estudar seções e funções argumentativas. Não é segmentador pronto de peças de autos brasileiros e exige adaptação de língua, domínio e dados. | Apache-2.0 no código; não inferir a licença de datasets e pesos a partir dela. |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | Documentação de OCR local com Tesseract, rotação, alinhamento e limpeza opcional. | Candidato complementar para investigar ORG-R10-PRIVADO. Não classifica peças e não há evidência nesta pesquisa de que resolverá a baixa confiança do documento recebido. | MPL-2.0 no núcleo; há outras licenças em componentes e dependências. |

Também consultei `chen-friedman/legal-skills`, já citado no projeto, no commit `18863f361f91eb2ecc85b13d021bbfdd9e1997df`. A skill de mapeamento e seus handlers organizam arquivos heterogêneos e um inventário por arquivo; não encontrei ali um segmentador automático demonstrado para várias peças dentro do mesmo PDF. O vocabulário português é referência auxiliar, não classificador validado.

## Por que VICTOR é pertinente

No código consultado, os seis rótulos são `acordao_de_2_instancia`, `agravo_em_recurso_extraordinario`, `despacho_de_admissibilidade`, `outros`, `peticao_do_RE` e `sentenca`. A saída não contempla diretamente petição inicial, manifestação do MP, contestação ou todas as decisões interlocutórias.

O notebook de CRF marca `B-<tipo>` quando `pages == 1` e `I-<tipo>` nas demais páginas, agrupando os dados por processo. Isso mostra uma representação explícita de início/continuação de documento; é diferente de manter a última seção reconhecida pelo título. A estratégia também permite representar duas peças consecutivas do mesmo tipo como dois inícios distintos. O uso de `pages` no treinamento pressupõe informação anotada; não devemos tratar essa coluna de gabarito como informação disponível na inferência.

Código lido e referência bibliográfica:

- [Artigo citado pelos autores: VICTOR, LREC 2020](https://aclanthology.org/2020.lrec-1.181/) — localizado pelo README, sem leitura integral nesta rodada; a análise técnica acima se baseia no código, não em reprodução dos resultados do artigo.
- [Código dos rótulos e predições](https://github.com/peluz/VICTOR-dataset/blob/e13e65a90477074d94c3434a5f0e576c655f2a7b/get_preds.py).
- [Notebook de sequências e CRF](https://github.com/peluz/VICTOR-dataset/blob/e13e65a90477074d94c3434a5f0e576c655f2a7b/crf_experiments.ipynb).

## Estrutura proposta para o projeto

```text
PDF original imutável — SHA-256
  └── páginas físicas e blocos com coordenadas/localizadores
       └── peças identificadas, cada uma com início/fim e estado de conferência
            └── seções internas e evidências vinculadas aos blocos originais
```

Uma peça precisa de identificador próprio, tipo proposto, localização inicial e final, sinais que fundamentam a classificação, método/versão e estado de conferência. O tipo pode ser `nao_identificada`; não se deve forçar o rótulo da peça anterior nem apresentar um escore não calibrado como probabilidade de acerto.

Página física do PDF, número impresso e numeração interna da peça são referências distintas. Se duas peças compartilham uma página, somente intervalos de páginas não bastam: precisam ser suportadas fronteiras por bloco ou região.

As classes de peça devem distinguir, entre outras, petição inicial, contestação, petição/manifestação, manifestação do MP, decisão interlocutória, despacho, sentença, acórdão, certidão e anexo. Dentro de cada uma, relatório, fundamentos, voto e dispositivo são seções; esses nomes não substituem o tipo da peça. A taxonomia final e os critérios precisam ser especificados antes da implementação.

## Integração e verificação recomendadas

- Criar uma camada de inventário que referencie os blocos atuais, preservando os identificadores e localizadores já usados por facts e claims. A adoção de outro extrator deve ter versão própria e migração explícita: normalização diferente pode alterar hashes de texto e invalidar evidências anteriores.
- Avaliar primeiro o modelo de dados do Docling Core. Sua estrutura de proveniência tem página, `bbox` e `charspan`; seu `DocumentOrigin.binary_hash` é `Uint64` no commit consultado e **não substitui o SHA-256 de integridade do projeto**.
- Comparar a extração atual e um adaptador Docling em corpus local, mantendo ambos como alternativas durante a avaliação. Não adicionar toda a pilha de modelos como dependência obrigatória antes de medir custo e resultado.
- Para processamento privado, usar pipeline local e desabilitar serviços remotos; o download inicial de modelos é uma etapa distinta do envio de conteúdo a um serviço de inferência. Conferir licenças e requisitos de cada motor/modelo escolhido.
- Usar ORG-R07-PRIVADO como regressão do limite sentença/acórdão e dos títulos espaçados. Acrescentar casos anotados com outras peças e casos de mesmo tipo em sequência, títulos mencionados em citações, anexos, capas e fronteiras dentro da mesma página. Um único processo não demonstra generalização.
- Medir separadamente fronteiras corretas, fusões indevidas de peças, fragmentações indevidas, acerto do tipo, taxa de abstenção e erros de OCR em conteúdo relevante. As fronteiras devem ser conferidas no original.

## Decisão recomendada

**Aproveitar Docling Core como referência estrutural e VICTOR como referência metodológica**, mantendo a classificação jurídica e a trilha de conferência como camada do projeto. Unstructured é uma alternativa a comparar, não uma segunda dependência obrigatória. LegalSeg serve para estudo de funções internas da decisão. OCRmyPDF merece ensaio separado para a qualidade de imagem/OCR.

A pesquisa não demonstra precisão em nossos PDFs e não autoriza anunciar identificação automática confiável de todas as peças. O próximo trabalho é especificar um inventário de peças compatível com a evidência atual e realizar um piloto local com gabarito de fronteiras.
