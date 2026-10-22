# Exemplos e gabaritos de ORG-01

Contrato normativo: [pecas-v1](../../../docs/contratos/pecas-v1.md). Os exemplos em `exemplos.json` são inteiramente artificiais: `origem_simulada_utf8` representa bytes simulados, e `extracao_json_utf8` contém bytes UTF-8 exatos de uma extração fabricada para exercitar o contrato. Não são PDFs reais nem resultados de um segmentador. Data, ator e textos dos exemplos não representam aprovação humana.

| Caso | Situação especificada |
|---|---|
| CT01 | Sentença e acórdão em páginas distintas; tipo de peça independente da seção antiga incorreta; relatório/voto dentro do acórdão |
| CT02 | Duas peças do mesmo tipo dentro de um único bloco e página, com offsets Unicode |
| CT03 | Duas peças consecutivas do mesmo tipo em páginas diferentes |
| CT04 | Menção a SENTENÇA em citação não abre peça; rodapé repetido permanece auxiliar fora do corpo |
| CT05 | OCR insuficiente, texto não atribuído e nenhuma peça artificialmente confirmada |
| CT06 | Um bloco cruza a fronteira de páginas; fragmentos explicitam o corte e a localização visual proposta |
| RH01 | Duas revisões: fusão remove uma peça, preserva alvos históricos e invalida conferências fictícias da peça ampliada |
| CT07 | Capa/índice auxiliares, página vazia e continuação de tipo não identificado |

Reprodução determinística: `python tests/casos/pecas_contrato/gerar_exemplos.py`. Validação: `python -m pytest -q tests/test_contrato_inventario_pecas.py`. JSON Schema usa as dependências de execução `jsonschema` e `rfc3339-validator` (promovidas de desenvolvimento em ORG-02), com `FormatChecker` ativo; elas são consumidas pelo validador opcional, sem mudar o extrator atual.

Os testes validam o esquema, rejeitam estruturas incompatíveis e conferem hashes, referências e partição dos textos **destes exemplos**. O arquivo `test_contrato_inventario_pecas.py` não executa o validador semântico, não mede classificação e não valida OCR de documentos reais. ORG-02 acrescenta os testes semânticos gerais em `tests/test_pecas.py` e os testes da proposta/CLI/piloto, separados destes gabaritos.

## ORG-R07-PRIVADO: gabarito físico confirmado

`ORG-R07-PRIVADO-fronteiras.json` contém hash e intervalos físicos, sem nomes, número de processo ou transcrições. A confirmação humana é a declaração do titular em 2026-10-22 nesta conversa, restrita aos intervalos e à natureza sentença/acórdão. O original, as imagens de conferência e a extração permanecem privados e não são distribuídos.

A âncora técnica de offsets é vinculada ao hash de **um snapshot**. Outra extração pode produzir blocos diferentes; a confirmação dos intervalos físicos não autoriza reutilizar esses offsets automaticamente nem representa conferência humana de cada caractere. O gabarito de páginas não é uma instância completa de `pecas.json`.
