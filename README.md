# juris-skills-br

Pacote de 8 skills para trabalho jurídico brasileiro com disciplina de prova: toda afirmação aponta uma fonte lida ou aparece como não verificada.

Planejamento: [docs/planejamento-juris-skills-br-v2.md](docs/planejamento-juris-skills-br-v2.md)

## Instalação

```bash
pip install -r requirements-dev.txt   # versões testadas em Python 3.14.6
python -m pytest
```

## Estado

| Fase | Situação |
|---|---|
| 0. Base | estrutura e `shared/` criados |
| 1. Scripts | `cnj.py` + testes feitos; sondagem de fontes feita ([resultado](docs/sondagem-pontes.md)); `extract.py` feito (pdfplumber); `validate.py` feito (109 testes no total) |
| 2. Núcleo | `br-verificar-citacoes` ([caso](tests/casos/verificacao_stj/claims.json)) e `br-mapear-autos` ([caso](tests/casos/mapeamento_stj/facts.json)) e `br-auditar-entrega` (`scripts/auditar.py`) escritas e testadas em caso real do STJ; **Fase 2 concluída** |
| 3 a 5 | não iniciadas |

## Extração

```bash
python scripts/extract.py caminho/arquivo.pdf   # JSON no stdout; cache em .cache/extract
```

Cada trecho sai com página, seção, localizador e marca de citação (heurística: recuo ou aspas). Limites: sem OCR; geometria calibrada em A4 e em um tipo de documento (acórdão do STJ); STF e peças de outros tribunais ainda sem teste.

## Validação dos dados

```bash
python scripts/validate.py claims.json --extracoes extract.json
```

Formatos e regras em [shared/dados.md](shared/dados.md). Com `--extracoes`, documento, bloco, trecho e hash são conferidos contra o texto extraído. O validador não julga se a fonte apoia a tese.

## Auditoria e aprovação

```bash
python scripts/auditar.py auditar --facts facts.json --claims claims.json --extracoes extracao.json --saida qc.json
python scripts/auditar.py status qc.json aprovacao.json
```

O script diz `revisao_pronta` ou `bloqueado`. A aprovação é registrada por revisor identificado e cai se qualquer artefato ou fonte mudar. Ver [skills/br-auditar-entrega](skills/br-auditar-entrega/SKILL.md).

## Testes

```bash
python -m pytest tests
```

## Regras comuns

[shared/garantias.md](shared/garantias.md) · [shared/estados.md](shared/estados.md)
