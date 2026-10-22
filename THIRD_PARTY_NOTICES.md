# Avisos de terceiros

Este repositório **não copia arquivos** de outros projetos de skills jurídicas. Os arquivos abaixo foram lidos nos commits indicados (17/10/2026) e **a estrutura ou a ideia** de cada um foi adaptada, com texto e código próprios. Se isso mudar, cada arquivo incorporado deve entrar aqui com repositório, commit, caminho, licença e a alteração feita (ver [governance/upstream-policy.md](governance/upstream-policy.md)). Comparação detalhada: [docs/comparacao-repositorios-modelo.md](docs/comparacao-repositorios-modelo.md).

## Projetos lidos e o que foi adaptado

| Projeto (commit) | Licença conferida nos arquivos | Arquivos lidos | O que foi adaptado |
|---|---|---|---|
| anthropics/claude-for-legal (`4a6c651`) | Apache-2.0 | `litigation-legal/skills/matter-intake`, `.../chronology`, `legal-builder-hub/skills/skills-qa` | intake uniforme e registro do resultado de conflitos; relevância, exposição de fatos, filtro de privilégio, versões; os 13 parâmetros e as 3 falhas jurídicas da revisão de skills |
| LegalQuants/lq-skills (`884cf40`) | Apache-2.0 na raiz e em `proposition-checking`; MIT em `adversarial-qc` (licença local) | `ACCESS-MODES.md`, `skills/proposition-checking`, `skills/adversarial-qc` e `references/checklist.md` | modos de acesso à fonte, `contradiz` e `nao_trata`, aplicabilidade, mapa de dependência, faixas de confiança, checklist de revisão crítica e profundidades |
| ma-serra/lex-intelligentia-skills (`21f5496`) | MIT | `docs/METODOLOGIA-FIRAC-JB.md`, `docs/GUIA-ANTI-ALUCINACAO.md`, `skills/core/peticao-analyzer` | estrutura FIRAC-JB, checklist do CPC art. 489 § 1º, roteiro CAPPD; lista do que nunca fazer. **Rejeitado:** os níveis CONFIRMADO e PROVÁVEL, que afirmam de memória |
| code-lawyer/Legal-Agent-Skills (`8916841`) | MIT | `legal-research/references/48-qc-gate.md`, `contract-review/references/06-output-and-severity.md`, `.../_templates/pack-template.md`, `document-fill/references/20-slot-and-fill.md` | rodapé de aviso obrigatório, limite de duas rodadas por verificação. Os demais ficam para a Fase 4 |
| chen-friedman/legal-skills (`18863f3`) | Apache-2.0 e NOTICE (o GitHub lista `NOASSERTION`) | `skills/mapping-legal-cases/references/output-templates.md`, `scripts/extract.py` | inventário com pendências, partes, relatório de privacidade com valores mascarados, leitura de e-mail, verificação de capacidades. NOTICE: "Copyright 2026 Chen Friedman / Lawcal AI" |
| evolsb/claude-legal-skill (`bca0d2e`) | MIT | `skill.md` | só leitura; a pré-checagem de contrato fica para a Fase 4, sem parâmetros de mercado dos EUA |
| autodevx/legal-skills, AlissonSantos1/brasil-legal-skills | MIT | não lidos nesta rodada | o validador CNJ do autodevx foi **reescrito do zero** (o original aceita dígito verificador errado, conforme a análise anterior) |

Nenhum desses projetos endossa este pacote.

## Dependências de execução (`requirements.txt`)

| Pacote | Versão | Licença |
|---|---|---|
| pdfplumber | 0.11.10 | MIT |
| Pillow | 13.0.0 | MIT-CMU; raster e filtro opcional de mediana do OCR |
| pdfminer.six | 20260107 | MIT |
| python-docx | 1.2.0 | MIT |
| lxml | 6.1.1 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT; esquema do inventário opcional de peças |
| rfc3339-validator | 0.1.4 | MIT; datas RFC 3339 dos eventos do inventário |

Dependências transitivas relevantes (instaladas com as acima): pypdfium2 (BSD-3-Clause e Apache-2.0), Pillow (MIT-CMU), charset-normalizer (MIT), cryptography (Apache-2.0 ou BSD-3-Clause), typing_extensions (PSF-2.0).

## Dependências de desenvolvimento (`requirements-dev.txt`)

| Pacote | Versão | Licença |
|---|---|---|
| pytest | 9.1.1 | MIT |
| pypdf | 6.19.0 | BSD-3-Clause |

O validador passou a dependência de execução em ORG-02. Dependências transitivas do validador de esquema nesta instalação: attrs, referencing, jsonschema-specifications e rpds-py, todas MIT conforme os metadados das distribuições instaladas. O rfc3339-validator usa ainda six (MIT). Nenhum modelo ou motor de extração foi adicionado por essa dependência de desenvolvimento.

PyMuPDF (AGPL-3.0) **não** é dependência e não deve ser adicionada sem decisão sobre a licença do pacote.

## Ferramentas externas usadas, fora do repositório

- `scripts/fetch_oficial.py` (conversão do Planalto em Markdown; arquivo do titular do projeto, incluído no repositório em 2026-10-18). Usa `requests` (Apache-2.0), `beautifulsoup4` (MIT) e `markdownify` (MIT).
- Tesseract OCR (Apache-2.0), instalado à parte e chamado como programa externo por `scripts/ocr.py`; o idioma `por` (tessdata) precisa ser instalado pelo usuário. Nada dele é redistribuído aqui.
- API Pública do DataJud (CNJ): chave pública publicada na wiki do CNJ, lida na hora da consulta e nunca gravada no repositório.
- ForgeLex (serviço de terceiro) e o navegador integrado do app: dependem da sessão e **enviam termos de consulta para fora da máquina**; a política de sigilo do caso decide se podem ser usados.

## Documentos de teste

`tests/casos/` traz o inteiro teor de acórdãos públicos do STJ (AREsp 2.432.194/SP e três do corpus em `stj_corpus`, baixados em 17/10/2026), as ementas dos conjuntos de dados abertos do STJ usadas como gabarito, e as versões compiladas do Código Civil e da Lei 13.709/2018 (LGPD) obtidas do Planalto, usados como fixtures. São atos e textos oficiais; a redistribuição não foi objeto de parecer.

## Piloto opcional de peças (`requirements-piloto-pecas.txt`)

Docling Parse 7.23.0 e Docling Core 2.104.0 são MIT, conforme documentação do projeto e metadados das distribuições instaladas. Usados somente em ambiente virtual separado para o [piloto ORG-02](docs/piloto-org02-2026-10-22.md); não houve instalação de modelos de layout/OCR, uso do pipeline completo Docling ou cópia de código/dados/pesos do VICTOR. O adaptador é código próprio, apoiado na API pública documentada.

Dependências adicionais relevantes instaladas no piloto: pydantic/pydantic-core/pydantic-settings (MIT), pandas (BSD-3-Clause), NumPy (BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0, expressão da distribuição), doclang (Apache-2.0), defusedxml (PSFL), jsonref e latex2mathml (MIT), rich/typer/tabulate (MIT). As ferramentas e seus dados não são redistribuídos neste repositório; fontes e versões diretas ficam fixadas no arquivo opcional. Licenças de modelos futuros exigem avaliação própria.
