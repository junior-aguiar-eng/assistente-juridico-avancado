---
name: br-preencher-minuta
description: Preenche um modelo DOCX com marcadores {{campo}} usando valores de procedência explícita: extraído de documento (o valor tem de aparecer literalmente no trecho citado), informado pelo usuário ou inferido. Campo sem prova fica marcado e destacado no documento, nunca preenchido de memória. Use quando o usuário pedir "preencher o modelo", "gerar a minuta a partir deste modelo e destes documentos" ou "completar a procuração com os dados do cliente". Não use para revisar contrato pronto (br-revisar-contrato), para redigir cláusulas novas nem para conferir citações.
version: 0.1.0
last_reviewed: 2026-10-17
owner: "pendente: mantenedor técnico e revisor jurídico a nomear"
---

# Preenchimento de minuta

Regras comuns: [garantias](../../shared/garantias.md), [formatos](../../shared/dados.md), [falhas jurídicas](../../shared/falhas-juridicas.md), [escalação](../../shared/escalacao.md).

## Público e natureza do trabalho

Para quem monta minutas a partir de modelos do escritório. A skill **transporta dados** de documentos e do usuário para o modelo; não redige cláusula nem decide o que o modelo deveria dizer. A escolha do modelo e a conferência final são do advogado.

## Entrada e saída

- **Entrada:** `modelo.docx` com marcadores `{{nome_do_campo}}` (minúsculas, dígitos e `_`), `derived/extracao.json` dos documentos de origem e `campos.json`.
- **Saída:** `outputs/minuta.docx` e o relatório de preenchimento (o que foi preenchido, o que ficou marcado). O modelo nunca é alterado.

## Estados do campo

| Estado | Exige | No documento |
|---|---|---|
| `extraido` | `valor` e `fonte` (`document_id`, `locator`, `trecho`); o valor aparece **literalmente** no trecho e o trecho no bloco extraído | valor |
| `informado` | `valor` e `informado_em` (data) | valor |
| `inferido` | `valor` e `razao` | só com `--aceitar-inferidos`, em amarelo, com `[INFERIDO: confirmar]` |
| `pendente` | `motivo`; sem `valor` | `[PENDENTE: campo]` em amarelo |
| `conflito` | 2+ `candidatos` de valores diferentes; sem `valor` | `[CONFLITO: campo]` em amarelo |
| `nao_se_aplica` | `motivo`; sem `valor` | `[NÃO SE APLICA: campo]` em amarelo |

## Roteiro

1. **Extraia** o modelo e as fontes. Confirme com o usuário **qual documento é a fonte de cada dado** quando houver mais de um candidato.
2. **Monte o `campos.json`** campo a campo. Para cada dado tirado de documento, copie do bloco extraído o trecho (a frase ou linha inteira) e o `locator`; o valor é um pedaço desse trecho, sem reescrever (CNPJ, nome e valores saem como estão). Dois documentos divergentes: `conflito`, não escolha. Dado ausente: `pendente`, não complete.
3. **Confira:** `python scripts/preencher.py lint campos.json --modelo modelo.docx --extracoes derived/extracao.json`. Os erros típicos: valor fora do trecho, marcador do modelo sem campo, campo `pendente` com valor, `informado` sem data.
4. **Gere:** `python scripts/preencher.py gerar campos.json modelo.docx outputs/minuta.docx --extracoes derived/extracao.json`. Sem `--aceitar-inferidos`, o inferido fica pendente.
5. **Entregue o relatório junto**: `completo: true` só quando nada ficou em amarelo. Liste ao advogado cada campo marcado e o motivo.

## O que não fazer

- **Não preencha por memória, por padrão do modelo nem por "o mais provável".** Sem prova, `pendente`.
- **Não reescreva o valor** para "limpar" (maiúsculas, pontuação, razão social abreviada): o que está no documento é o que vai.
- **Não resolva conflito** entre fontes; mostre os candidatos.
- **Não use dado de um caso em outro.** Cada `campos.json` pertence a um matter.
- **Não cole dado pessoal em consulta externa** nem em mensagem de commit; veja `confidentiality` no `matter.json`.

## Quando escalar

Além de [escalacao.md](../../shared/escalacao.md): modelo com marcador sem equivalente em nenhum documento; mais de um terço dos campos pendentes; dado do cliente que muda a natureza do instrumento (capacidade, representação, poderes); modelo com alteração rastreada ou comentário.

## Limites

Substitui só marcadores em texto simples de parágrafo (corpo e tabelas); marcador dentro de hiperlink, campo, caixa de texto, cabeçalho ou rodapé não é tratado e deve aparecer no relatório do lint como marcador sem campo, se estiver no corpo. Não faz cálculo, extenso de valor, nem concordância de gênero ou número. Sem OCR. Caso de referência: [tests/test_docx_edicao.py](../../tests/test_docx_edicao.py) (modelo com marcador dividido em runs e os seis estados).
