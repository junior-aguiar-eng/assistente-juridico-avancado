# Identidade dos casos após a reconciliação

R07/R10 foram usados para documentos diferentes nas duas branches. A reconciliação conserva os casos públicos locais e dá identificadores próprios aos privados recuperados. Páginas, gabaritos e resultados não podem ser transferidos entre casos pelo apelido anterior.

| ID nesta cópia | Origem | Documento | Situação |
|---|---|---|---|
| R07 | Codex local | Agravo TJMG público, 12 páginas | Fixture pública e expectativas locais preservadas |
| R10 | Codex local | Ofício público de Picos, 1 página | Fixture pública e expectativas locais preservadas |
| ORG-R07-PRIVADO | R07 na branch recuperada | Sentença/acórdão TJAL, 38 páginas | PDF privado ausente; confirmação histórica limitada às fronteiras físicas |
| ORG-R10-PRIVADO | R10 na branch recuperada | Escaneado privado, 2 páginas | PDF privado ausente; seis expressões genéricas conferidas na origem, sem leitura integral |

O [manifesto público](../tests/casos/regressao/manifesto.json) mantém os 12 casos e seus bytes originais. O [manifesto privado ORG](../tests/casos/regressao/manifesto-privado-org.json) registra os dois casos recuperados em namespace separado. O runner combina os registros somente para executar os testes. Os hashes privados são distintos dos originais públicos; os testes verificam essa separação. Os metadados privados conservam `proveniencia_reconciliacao.id_na_origem`, sem renomear o arquivo original ou modificar referências antigas.

Gabaritos privados recuperados:

- [Fronteiras ORG-R07-PRIVADO](../tests/casos/pecas_contrato/ORG-R07-PRIVADO-fronteiras.json), SHA-256 do original `d5431d9144779f04f2d5e7d455332a5a640fc1f2bf413d75ea67bfa42597933b`.
- [Amostras ORG-R10-PRIVADO](../tests/casos/ocr_qualidade/ORG-R10-PRIVADO-amostras.json), SHA-256 do original `ac187d53278c1c860a3cd49ce9dcf2f398155faebfee775d4fdabe48b26b1dd6`.

Os PDFs, imagens e extrações privadas não foram recuperados nem versionados. O runner informa `skip` quando estão ausentes e confere o hash antes de qualquer processamento quando presentes. Sua ausência não é aprovação do corpus. O gabarito de fronteiras não migra a âncora técnica para novas extrações; a amostra OCR não confere nomes, números, mérito ou integralidade.

Reconciliar código não executa ORG-04/05. Os relatórios anteriores permanecem evidências históricas da branch de origem; resultados desta cópia ficam em [RC-01](reconciliacao-org-2026-10-22.md).
