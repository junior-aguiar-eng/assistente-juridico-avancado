---
name: br-cronologia
description: Gera a cronologia de um caso a partir do facts.json validado, ordenando sem inventar precisão e sem calcular prazos: datas parciais ficam parciais, fatos de ordem incerta são marcados, fatos sem data vão para seção própria e cada fato mostra se é documentado, alegação, inferência ou lacuna. Use depois de br-mapear-autos, quando o usuário pedir "cronologia", "linha do tempo" ou "o que aconteceu e quando". Não use para calcular prazo processual ou prescricional, nem para extrair fatos dos documentos.
---

# Cronologia

Regras comuns: [garantias](../../shared/garantias.md), [formatos](../../shared/dados.md). A cronologia é **derivada** do `facts.json`: ela não lê documentos nem acrescenta fatos.

## Entrada e saída

- **Entrada:** `facts.json` válido (o gerador recusa um inválido) e, se houver, `extracao.json` para conferir os trechos.
- **Saída:** `outputs/timeline.json` (dados) e `outputs/cronologia.md` (leitura), ambos reproduzíveis. A cronologia guarda o hash do `facts.json` de que veio.

## Roteiro

1. **Confirme que o `facts.json` está validado** (`validate.py`). Corrija os erros na origem (`br-mapear-autos`), nunca na cronologia.
2. **Gere:** `python scripts/cronologia.py gerar --facts derived/facts.json --extracoes derived/extracao.json --saida-json outputs/timeline.json --saida-md outputs/cronologia.md`. Em uma atualização, acrescente `--anterior outputs/timeline.json` para listar fatos novos, removidos, alterados e reordenados.
3. **Leia o resultado antes de entregar:**
   - fatos com ⚠ têm **ordem incerta** (os intervalos de data se sobrepõem: mês contra dia desse mês, dois fatos no mesmo dia, ano contra qualquer data dele). Não desempate por conta própria; se a ordem importar, volte aos documentos e procure data mais precisa;
   - **Sem data:** fatos sem data ou de data indefinida ficam fora da linha do tempo, com o motivo. Peça o documento que falta em vez de estimar;
   - **Conflitos:** pares que o `facts.json` marcou como incompatíveis são listados; a cronologia não decide qual vale;
   - **Lacunas:** repasse ao usuário.
4. **Entregue com o tipo de cada fato visível.** Alegação aparece como "alegação de X": não a apresente como ocorrência.
5. **Mantenha atualizada:** qualquer mudança no `facts.json` torna a cronologia desatualizada. `python scripts/cronologia.py conferir --facts derived/facts.json --timeline outputs/timeline.json` diz se ainda corresponde; a auditoria (`br-auditar-entrega --timeline`) bloqueia a entrega com cronologia velha.

## O que não fazer

- **Não calcule prazos** (processual, prescricional, decadencial) nem diferenças entre datas: o pacote só ordena. Se o usuário pedir, diga que está fora do escopo e sugira o cálculo por quem tem a regra do caso.
- **Não complete datas.** "Novembro de 2013" é mês; não vire dia 1º ou 15. Data ambígua continua ambígua.
- **Não misture fonte e inferência na mesma linha.** Inferência aparece com tipo próprio e só existe se o `facts.json` a registrou com base.

## Limites

Ordena datas ISO do Calendário Gregoriano em fatos já registrados; não reconhece datas dentro do texto livre dos fatos (o campo `date` é a fonte). A seção de conflitos reproduz o que foi registrado, sem análise. Caso de referência: [tests/casos/mapeamento_stj](../../tests/casos/mapeamento_stj/facts.json), com 4 fatos datados e 4 sem data.
