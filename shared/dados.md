# Formatos de dados: `matter.json`, `facts.json` e `claims.json`

Validados por [scripts/validate.py](../scripts/validate.py). O validador confere **forma e coerência com as regras** de [estados.md](estados.md) e [garantias.md](garantias.md). Ele não decide se a fonte apoia a proposição: isso é revisão jurídica.

```bash
python scripts/validate.py matter.json --extracoes extract.json
python scripts/validate.py facts.json --extracoes extract.json
python scripts/validate.py claims.json --extracoes extract.json --estrito
```

Com `--extracoes` (saída de `extract.py`), cada `document_id`, `block_id`, `excerpt` e `content_hash` é conferido contra o texto realmente extraído. Código de saída: 0 válido, 1 inválido. Avisos não reprovam, exceto com `--estrito`. Trecho citado com CPF, CNPJ, cartão, e-mail ou telefone gera `dado_pessoal_no_trecho` (o valor não é repetido): troque o número por `[...]`.

## matter.json

Produzido pela `br-triagem`. Estrutura `{"schema_version": "1", "matter": {...}}`.

| Campo | Regra |
|---|---|
| `matter_id`, `objective` | obrigatórios |
| `client_role` | posição que o cliente defende: `autor`, `reu`, `recorrente`, `recorrido`, `terceiro`, `interessado` (processo); `contratante`, `contratada`, `divulgadora`, `receptora` (contrato); `nao_aplicavel`; `nao_informado` (gera aviso). Use a posição real: papel invertido muda toda a análise |
| `jurisdiction` | objeto: `ramo` (`civel`, `consumidor`, `empresarial`, `administrativo`, `familia`, `outro`, `nao_informado`), opcionais `tribunal` e `uf` (duas letras maiúsculas) |
| `as_of` | data de referência, AAAA-MM-DD, não futura. `facts_date` opcional (AAAA, AAAA-MM ou AAAA-MM-DD), não posterior a `as_of` |
| `fato_chave` | opcional: o fato que a tese precisa provar; orienta a relevância |
| `confidentiality` | `nivel` (`publico`, `restrito`, `sigiloso`) e `consultas_externas` (`permitidas`, `somente_termos_genericos`, `proibidas`) obrigatórios; `politica_modelo` obrigatória se restrito ou sigiloso; `privilegio` (`triado`, `misto`, `nao_triado`, `nao_aplicavel`); `segredo_de_justica` (verdadeiro ou falso; CPC, art. 189) |
| `conflicts` | resultado da checagem de conflito de interesses, **registrada, não executada**: `status` `cleared` (exige `method`, `cleared_by`, `cleared_date`, `checked_against`), `pending` (exige `owner`), `waived` (exige `waiver_rationale`), `nao_aplicavel` (exige `motivo`) ou `not-run` (só passa sem aviso com `override` completo: `by`, `date`, `rationale`). Ausente: aviso |
| `partes` | lista de `{nome, papel, representada_por?, source?}`; `papel`: `autor`, `reu`, `terceiro`, `advogado`, `juizo`, `perito`, `testemunha`, `outro`. `source` (documento, localizador, trecho) é conferida contra a extração; sem fonte, aviso |
| `processos` | números CNJ (com dígito verificador conferido) |
| `capabilities` | verdadeiro ou falso por capacidade; OCR é sempre falso |
| `documentos`, `lacunas_iniciais` | listas de texto |

## facts.json

```json
{
  "schema_version": "1",
  "matter_id": "caso-2026-001",
  "facts": [
    {"id": "f001", "kind": "documentado", "text": "Sessão virtual de 10/03/2026 a 16/03/2026.",
     "date": {"original": "10/03/2026", "iso": "2026-03-10", "precision": "dia"},
     "relevancia": "media", "priv": "ok",
     "source": {"document_id": "doc-1a2b3c4d5e6f", "block_id": "b0187", "locator": "p.15",
                "excerpt": "Sessão Virtual de 10/03/2026 a 16/03/2026"}}
  ]
}
```

| Campo | Regra |
|---|---|
| `id` | obrigatório, único, `[A-Za-z0-9_-]+` |
| `kind` | `documentado` (o documento registra o ato), `alegacao` (a parte, a decisão ou o parecer afirma), `inferencia`, `lacuna`, `informado` (o usuário contou e não há documento: aviso) |
| `text` | obrigatório |
| `source` | obrigatório em `documentado` e `alegacao`: `document_id`, `locator`, `excerpt` (opcional `block_id`) |
| `other_sources` | opcional: outras fontes do mesmo fato, validadas como `source` (um fato, várias fontes) |
| `alleged_by` | obrigatório em `alegacao` |
| `basis` | obrigatório em `inferencia`: lista de `id` de outros fatos existentes |
| `date` | opcional: `original`, `precision` (`dia`, `mes`, `ano`, `indefinida`), `iso`. Precisão e `iso` devem combinar (`dia`=AAAA-MM-DD, `mes`=AAAA-MM, `ano`=AAAA, `indefinida`=null). Data ambígua continua ambígua |
| `conflicts_with` | opcional: ids existentes; aviso se o conflito não for recíproco |
| `relevancia` | opcional: `alta` (exige `relevancia_motivo`), `media`, `baixa`; `relevancia_incerta` (verdadeiro ou falso) marca a dúvida. Mais da metade `alta` num conjunto de 6 ou mais gera aviso |
| `priv` | opcional: `ok` (sem sigilo), `flag` (provável sigilo ou dúvida), `review` (não foi possível julgar). Em triagem `misto`, só `ok` circula |
| coerência com a evidência | `date.original` precisa estar dentro de `source.excerpt` (`data_fora_do_trecho`). Com `--extracoes`, o `locator` (`p.N`, `par.N`, `tab.T.lin.R`, `nota.N`, `email.corpo.par.N`) precisa coincidir com onde o trecho foi achado (`localizador_incoerente`); texto livre sem marcador não é verificável e passa. Fato `documentado` apoiado só em trecho transcrito gera `documentado_em_citacao` |

Alegação não vira fato: o documento que mostra a alegação a sustenta como alegação, não como ocorrência.

## claims.json

```json
{
  "schema_version": "1",
  "claims": [
    {"id": "c001", "tipo": "precedente", "central": true,
     "proposition": "O STJ aplica o prazo quinquenal do art. 206, § 5º, I, do CC à cobrança de dívida líquida em instrumento particular.",
     "proposition_scope": "ementa", "draft_locator": "seção II, parágrafo 3",
     "applicability": "STJ, 3ª Turma, AREsp em recuperação judicial; vale como indicação para dívida líquida em instrumento particular.",
     "status": "supported", "existence": "confirmada", "quote_status": "conferida",
     "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida", "obtained_via": "live_source",
                  "url": "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202302535191",
                  "retrieved_at": "2026-10-17", "content_hash": "<sha256 do arquivo lido>",
                  "text_scope": "inteiro_teor", "document_id": "doc-1a2b3c4d5e6f", "block_id": "b0033",
                  "pinpoint": {"locator": "p.2", "excerpt": "se submete ao prazo quinquenal específico do art. 206"}}]}
  ]
}
```

| Campo | Regra |
|---|---|
| `id`, `proposition`, `status`, `existence` | obrigatórios. `status`: `unverified`, `partial`, `supported`, `unsupported`. `existence`: `confirmada`, `nao_confirmada`, `indisponivel` (não existe "inexistente") |
| `tipo` | opcional: `norma`, `precedente`, `sumula`, `tema`, `doutrina`, `outro` |
| `central` | opcional; tese central não verificada ou sem apoio pleno gera aviso |
| `proposition_scope` | `ementa` ou `inteiro_teor`. Padrão: `inteiro_teor` para `precedente` e `tema` |
| `quote_status` | `conferida`, `divergente`, `nao_conferida`; obrigatório fora de `unverified` |
| `source_relation` | só em `unsupported`: `contradiz` (a fonte diz o contrário: escalar) ou `nao_trata` (não trata do ponto). Sem ele, aviso |
| `applicability` | texto: órgão, classe, fatos e fase que tornam o apoio aplicável ao caso. `supported` de `precedente` ou `tema` sem ele gera aviso |
| `suggested_fix`, `draft_locator` | opcionais: o que fazer com a proposição (restringir, trocar a citação, acrescentar fonte, remover) e onde ela aparece na peça |
| `depends_on` | opcional: ids de outras proposições de que esta depende (existem, sem ciclo consigo mesma); a auditoria aponta dependência de proposição sem apoio |
| `reason`, `missing` | `reason` obrigatório em `partial` e `unsupported`; `missing` obrigatório em `partial` |
| `sources[]` | `source_id` único, `origin` (`oficial` ou `secundaria`), `access` (`lida`, `nao_acessada`, `source_missing`), `obtained_via` opcional (`live_source`, `user_supplied_source`) |
| `content_hash` | sha256 do arquivo lido. Com `--extracoes`, também vale o `text_sha256` da extração: hash do texto bruto lido (espaços normalizados), que não depende da divisão em blocos nem dos bytes do arquivo; o mesmo acórdão baixado duas vezes pode ter bytes diferentes e texto idêntico |
| fonte `lida` | exige `url` ou `local_file`, `retrieved_at` (data ISO), `content_hash` (sha256, 64 hex), `text_scope` (`ementa`, `inteiro_teor`, `texto_legal`, `outro`) e `pinpoint` com `locator` e `excerpt` |
| fonte não lida | pode trazer `error`; não leva `pinpoint` |
| `legal_time` | opcional na fonte: `as_of` (data) e `vigencia` (`vigente`, `revogada`, `nao_verificada`) |
| `cited_text` | opcional na proposição, booleano: `true` declara que a proposição é sobre o que a decisão transcreve. Precedente, tema ou súmula `supported` cujo trecho só aparece em passagem transcrita (acórdão que cita outro) é erro sem `cited_text=true` |
| `tipo` `sumula` e `tema` | o escopo é livre, mas a regra de revisão é: `supported` só com fonte oficial `lida` que traga o enunciado ou a tese literal. O validador não confere isso sozinho (confere oficial, `lida` e trecho no texto); quem revisa confere que o trecho é o enunciado |

### Regras de coerência por estado

| Estado | O validador exige |
|---|---|
| `unverified` | nenhuma fonte `lida` (se houve leitura, reavalie o estado) |
| `partial` | 1+ fonte `lida` (pode ser secundária), `existence=confirmada`, `reason`, `missing` |
| `supported` | 1+ fonte **oficial** `lida`; `existence=confirmada`; `quote_status=conferida`; se o escopo é `inteiro_teor`, uma fonte oficial com `text_scope=inteiro_teor`. Só fonte secundária: teto `partial` |
| `unsupported` | 1+ fonte oficial `lida` com `pinpoint`; `existence=confirmada`; `reason` |

`existence` diferente de `confirmada` só combina com `unverified`: busca vazia ou fonte inacessível nunca prova que a autoridade não existe. Em `supported` de `tipo=norma` sem `legal_time`, o aviso lembra que apoio ao texto não prova vigência.
