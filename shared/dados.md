# Formatos de dados: `facts.json` e `claims.json`

Validados por [scripts/validate.py](../scripts/validate.py). O validador confere **forma e coerência com as regras** de [estados.md](estados.md) e [garantias.md](garantias.md). Ele não decide se a fonte apoia a proposição: isso é revisão jurídica.

```bash
python scripts/validate.py facts.json --extracoes extract.json
python scripts/validate.py claims.json --extracoes extract.json --estrito
```

Com `--extracoes` (saída de `extract.py`), cada `document_id`, `block_id`, `excerpt` e `content_hash` é conferido contra o texto realmente extraído. Código de saída: 0 válido, 1 inválido. Avisos não reprovam, exceto com `--estrito`.

## facts.json

```json
{
  "schema_version": "1",
  "matter_id": "caso-2026-001",
  "facts": [
    {"id": "f001", "kind": "documentado", "text": "Sessão virtual de 10/03/2026 a 16/03/2026.",
     "date": {"original": "10/03/2026", "iso": "2026-03-10", "precision": "dia"},
     "source": {"document_id": "doc-1a2b3c4d5e6f", "block_id": "b0187", "locator": "p.15",
                "excerpt": "Sessão Virtual de 10/03/2026 a 16/03/2026"}}
  ]
}
```

| Campo | Regra |
|---|---|
| `id` | obrigatório, único, `[A-Za-z0-9_-]+` |
| `kind` | `documentado` (o documento registra o fato), `alegacao` (a parte afirma), `inferencia`, `lacuna` |
| `text` | obrigatório |
| `source` | obrigatório em `documentado` e `alegacao`: `document_id`, `locator`, `excerpt` (opcional `block_id`) |
| `alleged_by` | obrigatório em `alegacao` |
| `basis` | obrigatório em `inferencia`: lista de `id` de outros fatos existentes |
| `date` | opcional: `original`, `precision` (`dia`, `mes`, `ano`, `indefinida`), `iso`. Precisão e `iso` devem combinar (`dia`=AAAA-MM-DD, `mes`=AAAA-MM, `ano`=AAAA, `indefinida`=null). Data ambígua continua ambígua |
| `conflicts_with` | opcional: ids existentes; aviso se o conflito não for recíproco |
| coerência com a evidência | `date.original` precisa estar dentro de `source.excerpt` (`data_fora_do_trecho`). Com `--extracoes`, o `locator` (`p.N`, `par.N`, `tab.T.lin.R`, `nota.N`) precisa coincidir com onde o trecho foi achado (`localizador_incoerente`); texto livre sem marcador não é verificável e passa |

Alegação não vira fato: o documento que mostra a alegação a sustenta como alegação, não como ocorrência.

## claims.json

```json
{
  "schema_version": "1",
  "claims": [
    {"id": "c001", "tipo": "precedente", "central": true,
     "proposition": "O STJ aplica o prazo quinquenal do art. 206, § 5º, I, do CC à cobrança de dívida líquida em instrumento particular.",
     "proposition_scope": "ementa",
     "status": "supported", "existence": "confirmada", "quote_status": "conferida",
     "sources": [{"source_id": "s1", "origin": "oficial", "access": "lida",
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
| `reason`, `missing` | `reason` obrigatório em `partial` e `unsupported`; `missing` obrigatório em `partial` |
| `sources[]` | `source_id` único, `origin` (`oficial` ou `secundaria`), `access` (`lida`, `nao_acessada`, `source_missing`) |
| `content_hash` | sha256 do arquivo lido. Com `--extracoes`, também vale o `text_sha256` da extração: hash do texto bruto lido (espaços normalizados), que não depende da divisão em blocos nem dos bytes do arquivo; o mesmo acórdão baixado duas vezes pode ter bytes diferentes e texto idêntico |
| fonte `lida` | exige `url` ou `local_file`, `retrieved_at` (data ISO), `content_hash` (sha256, 64 hex), `text_scope` (`ementa`, `inteiro_teor`, `texto_legal`, `outro`) e `pinpoint` com `locator` e `excerpt` |
| fonte não lida | pode trazer `error`; não leva `pinpoint` |
| `legal_time` | opcional na fonte: `as_of` (data) e `vigencia` (`vigente`, `revogada`, `nao_verificada`) |

### Regras de coerência por estado

| Estado | O validador exige |
|---|---|
| `unverified` | nenhuma fonte `lida` (se houve leitura, reavalie o estado) |
| `partial` | 1+ fonte `lida` (pode ser secundária), `existence=confirmada`, `reason`, `missing` |
| `supported` | 1+ fonte **oficial** `lida`; `existence=confirmada`; `quote_status=conferida`; se o escopo é `inteiro_teor`, uma fonte oficial com `text_scope=inteiro_teor`. Só fonte secundária: teto `partial` |
| `unsupported` | 1+ fonte oficial `lida` com `pinpoint`; `existence=confirmada`; `reason` |

`existence` diferente de `confirmada` só combina com `unverified`: busca vazia ou fonte inacessível nunca prova que a autoridade não existe. Em `supported` de `tipo=norma` sem `legal_time`, o aviso lembra que apoio ao texto não prova vigência.
