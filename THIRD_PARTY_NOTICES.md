# Avisos de terceiros

Este repositório não copia arquivos de outros projetos de skills jurídicas. O desenho foi informado por leitura de repositórios públicos (listados abaixo); nenhum texto ou código deles foi incorporado. Se isso mudar, cada arquivo incorporado deve entrar aqui com repositório, commit, caminho, licença e a alteração feita.

## Projetos que informaram o desenho (ideias, sem cópia de arquivos)

| Projeto | Licença observada | O que informou |
|---|---|---|
| anthropics/claude-for-legal | Apache-2.0 | organização por assunto; triagem e cronologia |
| LegalQuants/lq-skills | Apache-2.0 na raiz; licenças locais por componente | separação entre acesso, existência e apoio à proposição |
| code-lawyer/Legal-Agent-Skills | MIT | pacotes por jurisdição; gate de preenchimento |
| chen-friedman/legal-skills | Apache-2.0 + NOTICE | inventário e mapa de casos |
| ma-serra/lex-intelligentia-skills | MIT | estrutura de análise (FIRAC) |

## Dependências de execução (`requirements.txt`)

| Pacote | Versão | Licença |
|---|---|---|
| pdfplumber | 0.11.10 | MIT |
| pdfminer.six | 20260107 | MIT |
| python-docx | 1.2.0 | MIT |
| lxml | 6.1.1 | BSD-3-Clause |

Dependências transitivas relevantes (instaladas com as acima): pypdfium2 (BSD-3-Clause e Apache-2.0), Pillow (MIT-CMU), charset-normalizer (MIT), cryptography (Apache-2.0 ou BSD-3-Clause), typing_extensions (PSF-2.0).

## Dependências de desenvolvimento (`requirements-dev.txt`)

| Pacote | Versão | Licença |
|---|---|---|
| pytest | 9.1.1 | MIT |
| pypdf | 6.19.0 | BSD-3-Clause |

PyMuPDF (AGPL-3.0) **não** é dependência e não deve ser adicionada sem decisão sobre a licença do pacote.

## Documentos de teste

`tests/casos/` traz o inteiro teor de um acórdão público do STJ (AREsp 2.432.194/SP) e a versão compilada do Código Civil obtida do Planalto, usados como fixtures. São atos e textos oficiais; a redistribuição não foi objeto de parecer. Os arquivos foram baixados em 17/10/2026.
