# ORG-03 — leitura de PDF escaneado

Execução nativa com TDD e uma revisão independente final. Subordinado ao [plano principal](plano-principal.md); não define prioridades concorrentes.

**Objetivo:** diagnosticar ORG-R10-PRIVADO, executar experimento local reproduzível, melhorar o tratamento técnico seguro e comparar somente com expectativas textuais conferidas.

**Limites:** original imutável e SHA-256 verificado; sem OCR remoto ou publicação de transcrições pessoais; OCR permanece `partial`, com tags e avisos. Confiança do Tesseract não certifica texto. Gabarito humano abrange apenas os trechos expressamente confirmados. Sem integração de gates (ORG-04).

## Tarefas e verificações

1. Inspecionar geometria, imagem e resultado anterior. Comparar resolução próxima à imagem fonte e suavização/segmentação controladas. Guardar texto e imagens apenas no workspace ignorado; relatório público contém métricas.
2. Acrescentar testes antes do código para limitar megapixels/lado da rasterização e conservar coordenadas X/Y em pontos PDF. Comparar configuração padrão e perfil opcional de suavização, sem recorte nem rotação que invalide localizadores. Comando: `python -m pytest -q tests/test_ocr.py tests/test_ocr_qualidade.py`; esperado: testes passam após RED observado.
3. Acrescentar diagnóstico reproduzível com parâmetros/versões/hashes, contagens e correspondência com gabarito mínimo. Estados proposto/conferido separados; ausência de gabarito não pode virar aprovação. Casos artificiais não contam como benchmark de documentos reais.
4. Versionar mudanças de extração/configuração para invalidar cache antigo e preservar seus artefatos. Registrar adoção/rejeição do perfil; médias e amostra de trechos não liberam nomes, datas, dispositivo ou integralidade.
5. Revisão independente do conjunto, correções materiais RED→GREEN, suíte completa `JURIS_TESSDATA=... python -m pytest -q -ra`, conferência de dependências/links/diff e commit local sem push.

## Foco de revisão

Rasterização excessiva; escala X/Y errada após limite de resolução; TSV parcial/malformado ou falha do motor; confiança alta escondendo erros/ilegibilidade; gabarito inexistente/promovido indevidamente; cache incompatível com perfil/idioma/configuração. Testes e relatório devem distinguir experimento, melhoria técnica e conferência humana.
