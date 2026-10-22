# Inventário de peças: comandos e limites

[Plano principal](plano-principal.md) · [Contrato v1](contratos/pecas-v1.md) · [Resultados do piloto](piloto-org02-2026-10-22.md).

Instalar `requirements.txt` em Python >=3.12. ORG-04 acrescenta consumo opcional por triagem, validador, cronologia e auditor; o fluxo legado continua disponível. Para organização assistida de autos, usar o modo explícito e registrar as referências de peça conforme [shared/dados.md](../shared/dados.md).

## Consumir inventários nas entregas

```sh
python scripts/triagem.py pecas --extracoes caso/derived/extracao.json \
  --pecas caso/derived/pecas.json caso/input/original.pdf
python scripts/validate.py caso/derived/facts.json --extracoes caso/derived/extracao.json \
  --pecas caso/derived/pecas.json caso/input/original.pdf --exigir-pecas --modo fundamentada
```

O resumo de triagem distingue integridade, propostas, leitura e pendências, sem transcrever o documento. `valido` indica integridade dos inventários fornecidos; não é conferência humana ou autorização de uso. Referências `source.peca`/`sources[].peca` fixam o hash da revisão corrente, a peça e os fragmentos usados. `--pecas` é repetível; revisão posterior exige `--pecas-anterior ARQUIVO` com os bytes exatos da revisão imediatamente anterior. Originais e extrações são entradas explícitas, somente leitura.

Os mesmos parâmetros são aceitos por `cronologia.py gerar`, `cronologia.py conferir` e `auditar.py auditar`. A cronologia de trabalho preserva as referências e mostra pendências; `--modo fundamentada` e `--formato fatos` recusam o uso material pendente antes de gravar saídas. Para conferir uma cronologia com peças, fornecer novamente extração, inventário, original e revisão anterior quando houver; não basta o hash de facts. No auditor, `G16_inventario_pecas` aplica as restrições do uso e os insumos ficam ligados ao QC por hash.

`--exigir-pecas` exige referência nas fontes de documentos paginados; não inventa páginas para DOCX/TXT. Sem essa flag, uma referência explícita ou um uso de documento com inventário fornecido também precisa conferir. Limites/tipo propostos, OCR e atribuição incerta continuam pendentes na análise e bloqueiam o uso fundamentado; `supported`/`unsupported` não podem usar fonte pendente nem em análise. Pendência localizada em outra peça não bloqueia automaticamente um trecho nativo conferido. Não remover flags/referências para apresentar o fluxo legado como análise integrada de autos.

## Validar um inventário

```sh
python scripts/pecas.py validar --inventario caso/derived/pecas.json \
  --extracao caso/derived/extracao.json --original caso/original.pdf
```

Para revisão posterior à inicial, fornecer também `--anterior caso/derived/pecas.rev-0001.json`. A revisão imediatamente anterior deve estar disponível em bytes exatos; o histórico anterior é preservado como prefixo. O comando calcula o SHA-256 lendo o original, sem confiar no hash declarado pelo inventário.

A saída é JSON `{valido, erros, avisos}`; código de saída 0 indica integridade, 1 indica falha. Erros usam os códigos do contrato. As mensagens não transcrevem valores ou trechos privados. Entradas são somente leitura; o comando não modifica o original nem grava inventários. Arquivos ausentes, links simbólicos e JSON incompatível são recusados.

**Um contrato válido pode conter OCR ilegível, tipo desconhecido e limites propostos.** Pendências permanecem em `avisos`, com sua relevância material. Validade não confirma identidade humana, natureza jurídica, texto ou mérito, nem libera automaticamente evidência para uso material.

## Propor e revisar fronteiras

API opcional em `scripts/pecas_proposta.py`:

```python
from pecas_proposta import propor_inventario

inv = propor_inventario(extracao_bytes, arquivo_sha256=hash_calculado_do_original)
```

Se o pacote tem vários documentos, selecionar `document_id` explicitamente. Títulos portugueses ancorados, inclusive com letras espaçadas, são sinais heurísticos. Menções no meio de parágrafos e blocos marcados como citação não iniciam automaticamente outra peça; essa cautela também perde títulos verdadeiros quando a marcação de citação do extrator está errada. O tipo `section` antigo não define a natureza da peça. Continuidade sem título pode permanecer `nao_identificada`.

O parâmetro opcional `fronteiras` **substitui todos os detectores automáticos**, permitindo retirar falsos inícios e separar peças consecutivas do mesmo tipo. Cada entrada usa `block_id`, `offset` Unicode e `tipo`. Duas entradas na mesma posição são recusadas. Exemplo artificial, com um bloco que atravessa duas páginas:

```python
inv = propor_inventario(extracao_bytes, arquivo_sha256=hash_calculado_do_original,
    fronteiras=[
        {"block_id": "b0001", "offset": 0, "tipo": "sentenca"},
        {"block_id": "b0001", "offset": 17, "tipo": "acordao",
         "pagina_anterior": 1, "pagina_inicio": 2},
    ])
```

Não reutilizar esses valores em outro documento. Páginas do corte exigem inspeção do original e devem caber no envelope do bloco. Essa localização técnica é proposta, sem conferência humana automática. O método preserva todos os caracteres por fragmentos e só retorna uma proposta se ela passa pelo validador.

A API cria um **novo inventário de revisão 1**; não a usar para substituir silenciosamente uma revisão já conferida. Para editar um inventário existente, preservar o snapshot anterior e seguir o contrato de revisões/eventos: alteração material exige correção e invalidação das dimensões afetadas, ou nova conferência humana posterior. Cada ID removido deve constar explicitamente nos alvos de `corrigir`, mesmo quando a peça também é alvo; o histórico impede reutilizar essa identidade depois. Não existe editor de revisões publicado nesta etapa.

## Executar o piloto opcional

Criar ambiente virtual separado e instalar `requirements-piloto-pecas.txt`. Depois:

```sh
python scripts/piloto_pecas.py --motor atual --original original.pdf
python scripts/piloto_pecas.py --motor docling-parse --original original.pdf
```

A saída contém hashes, versões, parâmetros identificados por hash, tempo, contagens, envelopes de propostas e pendências; não transcreve texto do documento. Não grava originais/extrações nem envia PDFs a serviços de inferência. O motor opcional sem a dependência instalada retorna `nao_executada`, sem fingir um resultado.

Docling Parse extrai linhas nativas com página e coordenadas. Este adaptador experimental não usa OCR, modelos de layout, classificação jurídica ou o pipeline completo Docling. Sua ordem de leitura não está conferida e gera aviso material. Não resolve páginas escaneadas e não foi adotado como extrator das skills.
