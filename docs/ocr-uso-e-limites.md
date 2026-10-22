# OCR local: uso, diagnóstico e limites

[Plano principal](plano-principal.md) · [Experimento ORG-03](experimento-org03-2026-10-22.md).

Instalar `requirements.txt` e, à parte, Tesseract com português. `JURIS_TESSERACT` seleciona o executável; `JURIS_TESSDATA` seleciona os modelos locais. Não há OCR remoto, download automático de modelos ou alteração do PDF original.

## Extrair

```sh
python scripts/extract.py original.pdf --ocr --no-cache > extracao.json
python scripts/extract.py original.pdf --ocr --ocr-perfil mediana --ocr-dpi 72 --no-cache > derivado.json
```

O primeiro comando usa perfil `padrao`, 300 dpi solicitados e teto de **10 milhões de pixels / 4.000 pixels por lado**. O teto reduz a resolução efetiva de páginas fisicamente enormes; preserva a rasterização A4 usual a 300 dpi. As coordenadas de cada eixo são calculadas pelo tamanho real do raster e voltam a pontos PDF.

O segundo é a configuração experimental escolhida para o ORG-R10-PRIVADO: mediana 3×3 e autocontraste numa cópia em cinza, com 72 dpi solicitados. **Não é recomendação geral para outros PDFs.** Numa página A4 comum, 72 dpi pode perder caracteres pequenos. O filtro não introduz recorte ou rotação. O render respeita a área visível (CropBox), quando existente, e as caixas retornam ao referencial da página, incluindo origem e rotação pré-existentes; não se amplia a área visível para revelar conteúdo fora dela. Os arquivos de saída são derivados, nunca substitutos do original.

A API `extract.extrair(..., ocr=True, ocr_perfil="mediana", ocr_dpi=72)` oferece as mesmas opções. Perfil/resolução, limites, idioma, hashes do modelo e executável e versões das bibliotecas identificam a configuração e o cache. Se o modelo não puder ser identificado, o OCR não reutiliza nem grava cache. A versão conciliada do extrator é `0.5.1` (ORG-03 original: `0.5.0`; inclui os controles locais de atribuição); caches anteriores não são reaproveitados. Novas extrações têm identidade própria: referências e offsets de snapshots antigos não são migrados automaticamente.

## Diagnosticar

```sh
python scripts/diagnostico_ocr.py --original original.pdf \
  --perfil mediana --dpi 72 --gabarito gabarito.json
```

O gabarito deve corresponder ao SHA-256 do original e listar amostras por página física. Sem gabarito, o diagnóstico registra ausência de conferência; um gabarito `proposto` não é promovido a humano. O ORG-R10-PRIVADO tem seis trechos genéricos confirmados pelo titular, disponíveis em [ORG-R10-PRIVADO-amostras.json](../tests/casos/ocr_qualidade/ORG-R10-PRIVADO-amostras.json); não reutilizar esse arquivo com outro original.

O stdout contém somente métricas, versões, hashes e resultados por ID de amostra, sem transcrição do PDF. O comando não grava imagens ou texto reconhecido. Código de saída 0 significa experimento executado, **não texto aprovado**. Falta do motor/modelo ou falha de leitura não é contada como validação bem-sucedida.

A correspondência de amostras ignora caixa, espaços, acentos e pontuação, para admitir títulos com letras espaçadas. Não mede fidelidade de acentos/pontuação, taxa de erro da transcrição completa ou preservação de todos os dados. Uma ocorrência noutra página não atende à amostra.

## Alertas

OCR mantém `status: partial`, tags `ocr` e aviso `ocr_aplicado`; ausência de texto permanece explícita. `ocr_baixa_confianca` aparece se a média do motor é menor que 60 **ou se pelo menos 20% das palavras têm confiança abaixo de 60**. Esses limiares são heurísticos, não probabilidades de acerto ou critérios de aprovação jurídica.

Cabeçalho TSV incompatível causa falha explícita; linhas truncadas ou com campos excedentes são contabilizadas antes de ignorar linhas vazias. Dados TSV malformados, caixas impossíveis e confiança não finita são descartados com contagem e aviso `ocr_dados_descartados`. Palavras de baixa confiança válidas continuam no texto e continuam incertas; não são apagadas para melhorar a média.

Mesmo com seis acertos em seis amostras, `uso_material_liberado` permanece falso. Nomes, datas, números, citações e dispositivo exigem conferência específica no original. ORG-04 integrará as restrições de uso aos consumidores; esta etapa não publica esse gate.
