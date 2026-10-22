# ORG-03 — diagnóstico e experimento de OCR

> Proveniência: relatório recuperado da branch `ff225a7`; métricas e confirmações descrevem a execução de origem. Nesta cópia, os privados têm IDs próprios e os originais não foram transferidos. A validação atual e a manutenção das regras inativas estão em [RC-01](reconciliacao-org-2026-10-22.md).

2026-10-22. [Plano principal](plano-principal.md) · [Uso](ocr-uso-e-limites.md) · [Métricas sem transcrições](experimento-org03-2026-10-22.json).

## Diagnóstico

O ORG-R10-PRIVADO contém duas imagens de páginas de um documento, sem texto nativo. As dimensões do PDF são 2.513×2.932 e 2.935×3.018 pontos; as imagens incorporadas têm esses mesmos números em pixels. A rasterização fixa anterior a 300 dpi ampliava artificialmente cada página para cerca de 128 e 154 milhões de pixels. Há ruído periódico vertical/moiré, inclinação e texto lateral.

O snapshot anterior do extrator 0.4.0 registra confiança média 41,7/37,9 e avisos de baixa confiança. Ele foi preservado localmente, sem reexecutar o raster excessivo. Não registra versão/hash do motor/modelo de OCR: não é baseline temporal comparável nem prova de exatidão textual.

A versão 0.5.0 limita o raster a 10 MP/4.000 pixels por lado, calcula coordenadas por eixo e oferece perfil de mediana/resolução explícitos. O limite inicial de 8 MP/3.500 foi rejeitado porque reduzia inclusive A4 usual a 300 dpi e a imagem nativa da segunda página. A correção é coberta por teste. Não há novas bibliotecas de OCR ou modelos; Pillow 13.0.0 já era instalado transitivamente e passou a dependência direta, com licença MIT-CMU.

## Amostra humana e método

O titular confirmou expressamente seis trechos e páginas nesta conversa: três na página física 1 e três na 2. O [gabarito mínimo](../tests/casos/ocr_qualidade/ORG-R10-PRIVADO-amostras.json) contém somente expressões genéricas, sem nomes, número do processo ou relato dos fatos. A confirmação **não** abrange a transcrição integral, dados pessoais, citações completas ou mérito.

O experimento foi local e sequencial, usando o mesmo original e Tesseract com português. Configuração, versão/hash do executável, hash do modelo, resolução efetiva e contagens ficam nas métricas. Textos reconhecidos, imagens e snapshots privados ficaram no workspace ignorado. O original manteve o SHA-256 do manifesto.

Foram comparados padrão e mediana (3×3 + autocontraste), com segmentação PSM 3, sem recortar/rotacionar páginas. A sondagem incluiu suavização gaussiana e PSM 6; não se adotaram essas variantes, que não superaram a amostra selecionada e misturavam mais texto lateral. Essa escolha foi ajustada no próprio ORG-R10-PRIVADO: ele é corpus de desenvolvimento, **não avaliação independente**.

## Resultados

| Configuração | Confiança p.1 / p.2 | Palavras com confiança <60 p.1 / p.2 | Amostras encontradas | Tempo |
|---|---|---|---|---|
| Padrão, 300 dpi solicitados, limitado | 75,2 / 61,1 | 45/192 / 111/242 | 1/6 | 7,1674 s |
| Mediana, 300 dpi solicitados, limitado | 73,8 / 70,0 | 120/418 / 99/306 | 5/6 | 11,4892 s |
| Mediana, 72 dpi solicitados | 83,8 / 73,0 | 49/376 / 82/279 | 6/6 | 8,3960 s |

A média de confiança não é precisão de transcrição. O melhor resultado ainda tem cerca de 29% das palavras abaixo de 60 na página 2. As amostras são comparadas apenas na página correta, ignorando caixa, espaços, acentos e pontuação; portanto seis acertos não demonstram fidelidade integral nem de números/acentos. Não se calculou CER/WER sem transcrição integral humana.

## Decisão e limite de uso

Adotar o limite de rasterização e a preservação de coordenadas como padrão técnico. Manter mediana/72 dpi como opção explícita para ORG-R10-PRIVADO, sem aplicá-la automaticamente a todos os escaneados. O extrator real oferece `--ocr --ocr-perfil mediana --ocr-dpi 72`; os resultados continuam `partial`, com tags e avisos.

O alerta também considera proporção de palavras de baixa confiança, além da média; TSV malformado é contabilizado e avisado. Motor, modelo, bibliotecas e parâmetros entram na identidade do cache; sem modelo identificável não se reutiliza cache. Snapshots antigos e originais não foram sobrescritos.

**Recusar uso material automático da transcrição do ORG-R10-PRIVADO.** Os seis trechos são expectativas locais conferidas, sem autorização para usar o restante como leitura fiel. Trecho que não possa ser conferido deve permanecer ilegível/não verificado. ORG-04 integrará esse limite aos consumidores; não foi implementado gate nesta entrega.

## Verificação

A revisão independente encontrou três falhas materiais, corrigidas com testes RED→GREEN: exceção do parser que podia divulgar conteúdo em traceback, coordenadas deformadas em CropBox com rotação e perda silenciosa de linhas TSV truncadas/excedentes. Os quatro ângulos e o retorno sanitizado foram exercitados com PDFs artificiais; 48 testes focados passaram após as correções. Não houve achados menores adiados. Suíte completa pós-correções em Linux/Python 3.12: **676 aprovados e 3 ignorados**, em 240,63 s, com `JURIS_TESSDATA=/workspace/.local/share/tessdata python -m pytest -q -ra` no ambiente virtual do projeto. Ignorados: dois testes de rede (`JURIS_REDE` ausente) e o Docling Parse opcional, fora do ambiente principal. Dependências compatíveis, originais preservados e verificações de links/diff sem erros. Os testes cobrem limite de raster, A4 preservado, escala por eixo, imagem original imutável, TSV inválido, confiança/proporção, identidade/cache, resolução, CLI real e separação entre gabarito proposto e humano. O andamento permanece exclusivamente no plano principal.

O experimento foi repetido após as correções, mantendo os resultados da amostra. A extração mediana/72 dpi foi preservada em arquivo novo na área privada local, identificada por SHA-256 nas métricas; não acompanha o Git. O PDF original e o snapshot 0.4.0 foram mantidos.
