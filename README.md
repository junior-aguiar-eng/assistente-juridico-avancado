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
| br-revisar-contrato | **não iniciada** (Fase 4; exige revisor jurídico) | |
| br-preencher-minuta | **não iniciada** (Fase 4) | |

Fluxos: mapear um caso (triagem, mapear-autos, cronologia, auditar); pesquisar e verificar (triagem, pesquisa, verificar-citacoes, auditar).

## Estado

| Fase | Situação |
|---|---|
| 0 a 3 | concluídas, corrigidas pela revisão crítica e ajustadas pela comparação com os repositórios de referência |
| 4 | contratos e minuta: aguardam revisor jurídico |
| 5 | liberação: 12 casos de regressão, incluindo outros tribunais e documentos escaneados |

Testes: 273 (mais 1 de rede opcional). Tudo foi testado em **um acórdão do STJ e no Código Civil compilado**; outros tipos de documento não foram avaliados. As skills (prompts) passam na revisão mecânica (`revisar_skill.py`), mas **não foram avaliadas com modelo**. Nenhum revisor jurídico foi nomeado: o pacote não substitui revisão por advogado.

## Scripts

| Comando | Para quê |
|---|---|
| `python scripts/triagem.py init\|inventario\|processos\|privacidade\|capacidades` | pasta do caso, hash dos originais (`--travar`), números CNJ com dígito conferido, dados pessoais mascarados, capacidades do ambiente |
| `python scripts/extract.py ARQ... --saida extracao.json` | PDF, DOCX, TXT, MD, e-mail (.eml), HTML salvo, CSV/TSV e XLSX em blocos com página, seção, localizador e marca de citação; rodapés repetidos voltam como seção `rodape`; sem OCR; perda de texto, colunas/tabelas em PDF, planilha oculta ou limite de tempo viram `partial`; arquivo com razão de compressão absurda é recusado; frase dirigida ao modelo dentro do documento gera `possivel_instrucao_embutida` (aviso, o texto segue como dado) |
| `python scripts/validate.py ARQ.json --extracoes extracao.json` | valida `matter.json`, `facts.json` e `claims.json` contra as regras e o texto extraído ([formatos](shared/dados.md)) |
| `python scripts/cronologia.py gerar\|conferir` | ordena sem inventar precisão e sem calcular prazos; relevância, exposição de fatos com filtro de sigilo, versões |
| `python scripts/fontes.py plano\|baixar\|anotacoes` | pontes de fontes por política do caso; download com hash e registro; alterações de um dispositivo à data dos fatos |
| `python scripts/auditar.py auditar\|aprovar\|status` | gate final com faixa de confiança; a aprovação exige terminal interativo e a frase digitada pelo revisor |
| `python scripts/revisar_skill.py skills/*/SKILL.md` | revisão mecânica das skills (estrutura, atualidade, superfície de confiança) |

## Regras comuns

[shared/garantias.md](shared/garantias.md) · [shared/estados.md](shared/estados.md) · [shared/dados.md](shared/dados.md) · [shared/fontes-br.md](shared/fontes-br.md) · [shared/falhas-juridicas.md](shared/falhas-juridicas.md) · [shared/escalacao.md](shared/escalacao.md) · [shared/aviso-padrao.md](shared/aviso-padrao.md)
