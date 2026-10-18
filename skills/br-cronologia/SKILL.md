---
name: br-cronologia
description: Gera a cronologia de um caso a partir do facts.json validado, ordenando sem inventar precisão: datas parciais ficam parciais, fatos de ordem incerta são marcados, fatos sem data vão para seção própria, cada fato mostra se é documentado, alegação, inferência ou informado, e a relevância fica marcada. Tem variante de exposição de fatos. Use quando já houver fatos registrados e o usuário pedir "cronologia", "linha do tempo", "o que aconteceu e quando" ou "exposição de fatos". Não use para calcular prazo processual ou prescricional, nem para extrair fatos dos documentos.
version: 0.2.0
last_reviewed: 2026-10-17
owner: "pendente: mantenedor técnico e revisor jurídico a nomear"
---

# Cronologia

Regras comuns: [garantias](../../shared/garantias.md), [formatos](../../shared/dados.md), [falhas jurídicas](../../shared/falhas-juridicas.md), [escalação](../../shared/escalacao.md). A cronologia é **derivada** do `facts.json`: ela não lê documentos nem acrescenta fatos.

## Público e natureza do trabalho

Para quem monta a narrativa do caso (petição, parecer, preparação de audiência). Trabalho de ordenação e apresentação sobre fatos já registrados: a skill executa; a leitura de relevância e a escolha do que entra numa peça são do advogado.

## Entrada e saída

- **Entrada:** `facts.json` válido (o gerador recusa um inválido), `matter.json` (papel, fato-chave, sigilo; obrigatório na exposição de fatos) e, se houver, `extracao.json`.
- **Saída:** `outputs/timeline.json` e `outputs/cronologia.md` (ou exposição de fatos), reproduzíveis, com o hash do `facts.json`, número de versão e o [aviso padrão](../../shared/aviso-padrao.md).

## Roteiro

1. **Confirme que o `facts.json` está validado.** Corrija os erros na origem (`br-mapear-autos`), nunca na cronologia.
2. **Gere:** `python scripts/cronologia.py gerar --facts derived/facts.json --matter matter.json --extracoes derived/extracao.json --saida-json outputs/timeline.json --saida-md outputs/cronologia.md`. Em atualização, acrescente `--anterior outputs/timeline.json` (versão +1 e lista de fatos novos, removidos, alterados e reordenados). `--janela-meses N` lista períodos sem fato registrado, como possível lacuna de documentos.
3. **Leia o resultado antes de entregar:**
   - ⚠ **ordem incerta**: intervalos de data que se sobrepõem. Não desempate; se importar, procure data mais precisa;
   - **relevância** aplicada do papel registrado, com a seção de eventos de relevância alta e o motivo de cada um;
   - **Sem data**, **Conflitos** (a cronologia não decide qual vale) e **Lacunas**;
   - tipo de cada fato visível: alegação aparece como "alegação de X"; fato `informado` aparece como tal, sem documento.
4. **Exposição de fatos** (`--formato fatos`, exige `--matter`): prosa em ordem, só fatos de relevância alta ou média, com o tipo e a fonte de cada um. Em triagem `misto` de sigilo, **só entra o que está `priv: ok`**; o restante fica de fora e o relatório diz quantos. `--incluir-sinalizados` só com a confirmação do advogado, e o cabeçalho registra isso. Com fontes `nao_triado`, a skill se recusa.
5. **Mantenha atualizada:** `python scripts/cronologia.py conferir --facts derived/facts.json --timeline outputs/timeline.json`. A auditoria (`br-auditar-entrega --timeline`) bloqueia a entrega com cronologia velha.

## O que não fazer

- **Não calcule prazos** (processual, prescricional, decadencial) nem diferenças entre datas.
- **Não complete datas.** "Novembro de 2013" é mês; não vire dia 1º ou 15.
- **Não misture fonte e inferência na mesma linha** nem apresente alegação como ocorrência.
- **Não supra janelas sem eventos com memória ou busca**: relate a janela e pergunte por documentos.

## Quando escalar

Além de [escalacao.md](../../shared/escalacao.md): processo em segredo de justiça (o cabeçalho avisa: confirmar que a circulação é permitida); pedido de exposição de fatos com fontes sem triagem de sigilo; fato central só `informado`; muitos fatos de ordem incerta num ponto decisivo.

## Limites

Ordena datas de calendário gregoriano de fatos já registrados; não reconhece datas dentro do texto livre (o campo `date` é a fonte). Relevância é marca do revisor, não cálculo. Não há variante por testemunha (falta campo de participantes). Caso de referência: [tests/casos/mapeamento_stj](../../tests/casos/mapeamento_stj/facts.json), com 4 fatos datados e 4 sem data.
