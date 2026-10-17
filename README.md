# juris-skills-br

Pacote de 8 skills para trabalho jurídico brasileiro com disciplina de prova: toda afirmação aponta uma fonte lida ou aparece como não verificada.

Planejamento: [docs/planejamento-juris-skills-br-v2.md](docs/planejamento-juris-skills-br-v2.md) · Revisão crítica da Fase 2: [docs/revisao-critica-fase2.md](docs/revisao-critica-fase2.md) · Sondagem das fontes: [docs/sondagem-pontes.md](docs/sondagem-pontes.md)

## Instalação

```bash
pip install -r requirements-dev.txt   # versões testadas em Python 3.14.6
python -m pytest                      # JURIS_REDE=1 liga o teste que baixa um acórdão do STJ
```

## Skills

| Skill | Situação | Script de apoio |
|---|---|---|
| [br-triagem](skills/br-triagem/SKILL.md) | escrita e testada | `triagem.py`, `validate.py` (matter.json) |
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
| 0 a 2 | concluídas (base, scripts, núcleo) e corrigidas pela revisão crítica |
| 3 | concluída: triagem, cronologia e pesquisa, com casos reais do STJ |
| 4 | contratos e minuta: aguardam revisor jurídico |
| 5 | liberação: 12 casos de regressão, incluindo outros tribunais e documentos escaneados |

Testes: 181 (mais 1 de rede opcional). Tudo foi testado em **um acórdão do STJ e no Código Civil compilado**; outros tipos de documento não foram avaliados. As skills (prompts) ainda não passaram por avaliação com modelo.

## Scripts

| Comando | Para quê |
|---|---|
| `python scripts/triagem.py init CASO --id ID` | cria a pasta do caso; `inventario` (hash dos originais, `--travar`) e `processos` (números CNJ com dígito conferido) |
| `python scripts/extract.py ARQ... --saida extracao.json` | PDF, DOCX, TXT e MD em blocos com página, seção, localizador e marca de citação; sem OCR |
| `python scripts/validate.py ARQ.json --extracoes extracao.json` | valida `matter.json`, `facts.json` e `claims.json` contra as regras e o texto extraído ([formatos](shared/dados.md)) |
| `python scripts/cronologia.py gerar --facts F --saida-json T --saida-md C` | ordena sem inventar precisão e sem calcular prazos; `conferir` diz se está desatualizada |
| `python scripts/fontes.py plano\|baixar\|anotacoes` | pontes de fontes por política do caso; download com hash e registro; alterações de um dispositivo à data dos fatos |
| `python scripts/auditar.py auditar\|aprovar\|status` | gate final; a aprovação exige terminal interativo e a frase digitada pelo revisor |

## Regras comuns

[shared/garantias.md](shared/garantias.md) · [shared/estados.md](shared/estados.md) · [shared/dados.md](shared/dados.md) · [shared/fontes-br.md](shared/fontes-br.md)
