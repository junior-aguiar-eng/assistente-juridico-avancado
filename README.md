# juris-skills-br

Pacote de 8 skills para trabalho jurídico brasileiro com disciplina de prova: toda afirmação aponta uma fonte lida ou aparece como não verificada.

Planejamento: [docs/planejamento-juris-skills-br-v2.md](docs/planejamento-juris-skills-br-v2.md) · Revisão crítica da Fase 2: [docs/revisao-critica-fase2.md](docs/revisao-critica-fase2.md) · Comparação com os repositórios de referência: [docs/comparacao-repositorios-modelo.md](docs/comparacao-repositorios-modelo.md) · Sondagem das fontes: [docs/sondagem-pontes.md](docs/sondagem-pontes.md) · Governança: [governance/](governance/skill-review-checklist.md)

## Instalação

```bash
pip install -r requirements-dev.txt   # versões testadas em Python 3.14.6
python -m pytest                      # JURIS_REDE=1 liga o teste que baixa um acórdão do STJ
python scripts/revisar_skill.py skills/*/SKILL.md   # revisão mecânica das skills
```

## Skills

| Skill | Situação | Scripts de apoio |
|---|---|---|
| [br-triagem](skills/br-triagem/SKILL.md) | escrita e testada | `triagem.py`, `privacidade.py`, `validate.py` (matter.json) |
| [br-mapear-autos](skills/br-mapear-autos/SKILL.md) | escrita e testada | `extract.py`, `validate.py` (facts.json) |
| [br-cronologia](skills/br-cronologia/SKILL.md) | escrita e testada | `cronologia.py` |
| [br-pesquisa-juridica](skills/br-pesquisa-juridica/SKILL.md) | escrita e testada | `fontes.py`, `shared/fontes.json` |
| [br-verificar-citacoes](skills/br-verificar-citacoes/SKILL.md) | escrita e testada | `validate.py` (claims.json) |
| [br-auditar-entrega](skills/br-auditar-entrega/SKILL.md) | escrita e testada | `auditar.py` |
| br-revisar-contrato | **rascunho mecânico** (Fase 4): pré-checagem, `issues.json` validado, redline; regras `rules/br` **inativas até revisor jurídico** | [tests/test_contrato.py](tests/test_contrato.py) |
| br-preencher-minuta | **escrita** (Fase 4): seis estados de campo, valor extraído tem de estar literalmente no trecho | [tests/test_docx_edicao.py](tests/test_docx_edicao.py) |

Fluxos: mapear um caso (triagem, mapear-autos, cronologia, auditar); pesquisar e verificar (triagem, pesquisa, verificar-citacoes, auditar).

## Estado

| Fase | Situação |
|---|---|
| 0 a 3 | concluídas, corrigidas pela revisão crítica e ajustadas pela comparação com os repositórios de referência |
| 4 | contratos e minuta: aguardam revisor jurídico |
| 5 | liberação: 12 casos de regressão, incluindo outros tribunais e documentos escaneados |

Testes: 390 (mais 1 de rede opcional). Os acórdãos reais testados são **quatro do STJ** (Corte Especial e Sexta Turma, com a ementa dos dados abertos como gabarito objetivo; um quinto veio como página HTML e foi recusado) e o Código Civil compilado; contratos, petições e planilhas só têm casos sintéticos. As skills (prompts) passam na revisão mecânica (`revisar_skill.py`), mas **não foram avaliadas com modelo**. Nenhum revisor jurídico foi nomeado: o pacote não substitui revisão por advogado.

## Scripts

| Comando | Para quê |
|---|---|
| `python scripts/triagem.py init\|inventario\|processos\|privacidade\|capacidades` | pasta do caso, hash dos originais (`--travar`), números CNJ com dígito conferido, dados pessoais mascarados, capacidades do ambiente |
| `python scripts/extract.py ARQ... --saida extracao.json` | PDF, DOCX, TXT, MD, e-mail (.eml), HTML salvo, CSV/TSV e XLSX em blocos com página, seção, localizador e marca de citação; rodapés repetidos voltam como seção `rodape`; sem OCR; perda de texto, colunas/tabelas em PDF, planilha oculta ou limite de tempo viram `partial`; arquivo com razão de compressão absurda é recusado; frase dirigida ao modelo dentro do documento gera `possivel_instrucao_embutida` (aviso, o texto segue como dado) |
| `python scripts/validate.py ARQ.json --extracoes extracao.json` | valida `matter.json`, `facts.json` e `claims.json` contra as regras e o texto extraído ([formatos](shared/dados.md)) |
| `python scripts/cronologia.py gerar\|conferir` | ordena sem inventar precisão e sem calcular prazos; relevância, exposição de fatos com filtro de sigilo, versões |
| `python scripts/fontes.py plano\|baixar\|anotacoes` | pontes de fontes por política do caso; download com hash e registro; alterações de um dispositivo à data dos fatos |
| `python scripts/auditar.py auditar\|aprovar\|status` | gate final com faixa de confiança; a aprovação exige terminal interativo e a frase digitada pelo revisor |
| `python scripts/contrato.py precheck\|validar-issues` | pré-checagem do contrato (campo em branco, anexo ausente, remissão quebrada, assinatura) e validação do `issues.json` (cláusula inteira, dois eixos de severidade, base verificável) |
| `python scripts/redline_docx.py ORIG.docx EDICOES.json SAIDA.docx` | cópia do DOCX com alterações rastreadas; edição ambígua ou fora do texto simples é recusada; o original não muda |
| `python scripts/preencher.py lint\|gerar` | preenche modelo com `{{campo}}`; campo sem prova vira marcador amarelo |
| `python scripts/regras.py gerar\|validar\|listar` | pacotes `rules/br` com o texto literal do Código Civil; todos **inativos** até um revisor jurídico ativar |
| `python scripts/revisar_skill.py skills/*/SKILL.md` | revisão mecânica das skills (estrutura, atualidade, superfície de confiança) |

## Regras comuns

[shared/garantias.md](shared/garantias.md) · [shared/estados.md](shared/estados.md) · [shared/dados.md](shared/dados.md) · [shared/fontes-br.md](shared/fontes-br.md) · [shared/falhas-juridicas.md](shared/falhas-juridicas.md) · [shared/escalacao.md](shared/escalacao.md) · [shared/aviso-padrao.md](shared/aviso-padrao.md)
