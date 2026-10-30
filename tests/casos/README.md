# Casos de teste (`tests/casos`)

Índice das fixtures: de onde vem cada uma, qual é o gabarito e que tipo de teste a usa. Atualizado em 2026-10-29 (tarefa CL-02). O que nenhum teste aqui faz é avaliar a **correção jurídica**: os gabaritos são objetivos (ementa oficial, contagem de páginas, hash, texto presente ou ausente) e a revisão jurídica continua com o revisor designado (`governance/revisor-juridico.md`).

## Três tipos de teste

| Tipo | O que prova | Onde |
|---|---|---|
| Extração | o texto sai inteiro, com seção, localizador e status honesto (`ok`, `partial`, `failed`) | `test_extract*.py`, `test_regressao.py`, `test_corpus_stj.py`, `test_ocr.py` |
| Mecânico | os scripts validam, bloqueiam e registram como a skill descreve (formato, hash, estado, aprovação) | `test_validate*.py`, `test_auditar*.py`, `test_triagem.py`, `test_cronologia*.py`, `test_pesquisa.py`, `test_fontes.py`, `test_contrato.py`, `test_docx_edicao.py`, `test_rigor.py`, `test_gatilhos.py` |
| Avaliação jurídica | o conteúdo jurídico está certo | **nenhum**; pendente (revisor jurídico e segunda avaliação das skills) |

## Fixtures

| Pasta ou arquivo | Origem | Gabarito | Usada por | Tipo |
|---|---|---|---|---|
| `stj_aresp_2432194.pdf` e `stj_aresp_2432194_ementa_ref.txt` | Inteiro teor do AREsp 2.432.194/SP, portal do STJ | ementa de referência (texto) | `test_extract`, `test_validate`, `test_caso_stj` | extração |
| `verificacao_stj/` (`fontes/stj_inteiro_teor.pdf`, `fontes/cc_compilado.md`, `claims.json`) | Mesmo acórdão baixado de novo (bytes diferentes, texto igual) e Código Civil compilado do Planalto | `claims.json` com os quatro estados de apoio, escrito pelo mantenedor técnico, **sem revisão jurídica** | `test_auditar*`, `test_rigor`, `test_caso_stj`, `test_contrato`, `test_validate_extras` e outros | mecânico |
| `mapeamento_stj/facts.json` | Fatos do AREsp 2.432.194 escritos pelo mantenedor técnico | validador (trecho, localizador, data); sem revisão jurídica | `test_caso_mapeamento`, `test_auditar*`, `test_cronologia*` | mecânico |
| `pesquisa_stj/claims_inicial.json` | Proposições iniciais do caso, escritas pelo mantenedor técnico | validador; sem revisão jurídica | `test_pesquisa` | mecânico |
| `triagem_stj/matter.json` | `matter.json` do caso AREsp 2.432.194 | validador | `test_triagem`, `test_fontes`, `test_pesquisa` e outros | mecânico |
| `stj_corpus/` (`pdf/`, `gabarito.json`, `registro.json`) | Três acórdãos do STJ baixados do portal (Corte Especial e Sexta Turma), com hash e data no `registro.json` | **ementa oficial dos dados abertos do STJ**, independente da extração do PDF | `test_corpus_stj`, R02 a R05 da regressão | extração |
| `regressao/` (`manifesto.json`, `R06_stf_are_1563128_rg.pdf`, `pendentes/`) | 12 casos de regressão; R06 é o inteiro teor do STF (Tema 1473) baixado em 2026-10-18 pelo navegador do app | esperado por caso no manifesto (status, páginas, seções, avisos, texto presente ou ausente) | `test_regressao` | extração |
| `regras_fontes/` (`lgpd_compilado.md`, `l9279_compilado.md`, `registro.json`) | LGPD (lida em 2026-10-18) e Lei 9.279/1996 (lida em 2026-10-29), versões compiladas do Planalto, com hash | texto literal das regras de `rules/br` conferido contra a fonte | `test_contrato` | mecânico |
| `_download/` | baixado em tempo de teste; **não versionado** (`.gitignore`) | hash e texto idênticos entre downloads | `test_fontes` (rede só com `JURIS_REDE=1`), `test_regressao` | extração |

## Casos de regressão (manifesto)

R01 a R06 usam PDFs reais públicos (STJ e STF). R05 é o caso em que o portal do STJ devolve uma página genérica no lugar do PDF (`source_missing`). R08, R09, R11 e R12 (DOCX com alteração rastreada, página digitalizada sintética, planilha XLSX, e-mail `.eml`) são **gerados em código**, sem arquivo versionado. R07 (decisão de TJ) e R10 (escaneado real) estão **aguardando** documento: ver `regressao/pendentes/LEIAME.txt` (documento público ou do próprio titular, sem dado de cliente).

## Regras

- Originais e casos reais de cliente ficam fora do repositório; entram só documentos públicos ou sintéticos autorizados.
- Os documentos públicos mantêm o regime de origem; o restante segue a licença do projeto.
- `tests/casos/**` não tem conversão de fim de linha (`.gitattributes`), para os hashes registrados não mudarem.
- Fixture nova entra com origem, data e gabarito registrados aqui, e indicando a qual dos três tipos de teste serve.
