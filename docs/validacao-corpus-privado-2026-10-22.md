# Corpus privado recebido em 2026-10-22

> Proveniência: relatório recuperado da branch `ff225a7`; métricas e confirmações descrevem a execução de origem. Nesta cópia, os privados têm IDs próprios e os originais não foram transferidos. A validação atual e a manutenção das regras inativas estão em [RC-01](reconciliacao-org-2026-10-22.md).

Registro histórico da execução inicial. Evolução posterior: [ORG-02](piloto-org02-2026-10-22.md), [ORG-03](experimento-org03-2026-10-22.md) e [plano principal](plano-principal.md), fonte vigente das prioridades.

O titular forneceu dois PDFs para os casos ORG-R07-PRIVADO e ORG-R10-PRIVADO. Os arquivos e as extrações permanecem locais: os documentos contêm dados pessoais e conteúdo criminal sensível. Os PDFs em `tests/casos/regressao/pendentes/` estão excluídos pelo `.gitignore`; o commit contém apenas testes, hashes, expectativas estruturais e este registro, sem transcrições identificáveis. Não houve envio a serviço externo de OCR nem push.

| Caso | Material | Resultado observado | Limitação |
|---|---|---|---|
| ORG-R07-PRIVADO | PDF nativo com sentença e acórdão, 38 páginas | Extração `ok`, texto e localizadores presentes | Cabeçalhos do acórdão com letras espaçadas não mudam a seção; o texto segue agrupado como `sentenca`. O status de extração não garante classificação correta. |
| ORG-R10-PRIVADO | Documento escaneado, 2 páginas, sem texto nativo | OCR `partial`, blocos marcados `ocr`, aviso `ocr_baixa_confianca` | Texto reconhecido insuficiente para leitura jurídica confiável; exige melhoria de OCR e conferência no original. |

Os hashes SHA-256 e as expectativas estruturais estão no manifesto. O estado `privado_local` indica documento recebido que não acompanha o clone: os testes são ignorados se o arquivo não estiver presente. No ambiente atual ambos estão disponíveis. Receber o documento e passar nessas verificações não equivale a gabarito jurídico completo nem encerra a Fase 5.

Verificação na nuvem (Linux, Python 3.12, Tesseract com português): **505 testes passaram e 2 testes de rede foram ignorados** em 2026-10-22. Os casos privados ORG-R07-PRIVADO e ORG-R10-PRIVADO executaram. A validação das 19 regras contra os textos locais passou, com as pendências de fonte do pacote NDA preservadas; as oito skills passaram na revisão mecânica. A nova avaliação das skills por modelo com documentos reais ainda não foi realizada.

## Próximas correções

1. Reconhecer títulos espaçados de acórdão, relatório e voto, com testes sintéticos anônimos e conferência no ORG-R07-PRIVADO.
2. Investigar a baixa confiança do OCR do ORG-R10-PRIVADO; definir expectativas textuais apenas depois de conferir a leitura, sem reclassificar o resultado como completo.
3. Conferir gabaritos do corpus e repetir a avaliação das skills com documentos reais; registrar os resultados separadamente da aprovação jurídica declarada pelo titular.
