# Uso assistido e atualização de artefatos

Este roteiro descreve o fluxo existente na base `910b11e`, sem instalação ou publicação automática. O recorte é documental cível. [Evidências da fase 5](validacao-fase5.md) · [Formatos](../shared/dados.md) · [Inventário de peças](inventario-pecas-uso.md).

## Ambiente e sigilo

Use Python >=3.12 e as versões de `requirements.txt`/`requirements-dev.txt` em um ambiente próprio. A rodada local foi executada em Windows/Python 3.14.6; outras combinações precisam de validação própria. Para repetir os testes offline, use UTF-8, `JURIS_REDE=0` e temporários fora dos checkouts. Não reutilize ambiente, índice Git ou pasta de testes de outro agente.

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:JURIS_REDE = '0'
python -m pip check
python -m pytest -q --basetemp 'C:/evidencias/nova-rodada/tmp'
python scripts/revisar_skill.py 'skills/br-*/SKILL.md'
```

Escolha um diretório de temporários próprio e ainda não usado: o pytest administra e pode remover o conteúdo desse diretório. Não use originais, evidências históricas ou checkout como `--basetemp`.

Tesseract e idioma português são opcionais, instalados à parte; `triagem.py capacidades` informa a disponibilidade. OCR gera leitura parcial, não aprovação. Docling Parse é piloto opcional em ambiente separado, sem adoção como padrão. Não há motor de IA embutido ou API adicional de geração no pacote; análise e redação usam o modelo da sessão. A rodada das oito skills não compara famílias de modelos. Custos e política de dados dessa sessão são separados dos scripts locais.

Extração local não torna a inferência local: texto lido pelo modelo entra no ambiente da conversa. Registre sigilo, triagem de privilégio e política de consultas externas antes de fornecer conteúdo. ForgeLex, navegador e DataJud dependem do acesso efetivo da sessão e da política do caso. Não contornar bloqueios de portais ou declarar fonte lida por ter localizado um link.

## Do documento ao pacote de trabalho

1. **Triagem.** Defina objetivo, papel do cliente, jurisdição, datas e sigilo. Crie pasta própria com `triagem.py init`; complete `matter.json` apenas com informações fornecidas. A checagem de conflitos é do responsável; a skill registra método, data e resultado, sem inventá-los.
2. **Originais.** Copie os arquivos autorizados para `input/`, preserve os originais e registre o inventário com `triagem.py inventario --travar`. Não copie casos privados para o Git.
3. **Leitura.** Execute `extract.py`, relate cobertura e classifique ausências/falhas como lacunas. PDF, DOCX, TXT/MD, EML, HTML salvo, CSV/TSV e XLSX têm limites próprios. Planilhas não são recalculadas; imagens/áudio/vídeo não são análise multimodal deste pacote. Confira OCR, tabelas, colunas e DOCX com alterações no original.
4. **Peças.** Gere proposta pela API documentada em [inventario-pecas-uso.md](inventario-pecas-uso.md). Proposta heurística pode se abster; tipo desconhecido não é tipo confirmado. Uma seção ACÓRDÃO/VOTO ou precedente transcrito não define, por si, uma peça nova. Preserve documento, bloco, fragmentos e páginas. Conferir integridade com `pecas.py validar` não confere autoria, leitura ou natureza jurídica.
5. **Fatos e tempo.** O modelo prepara `facts.json` e o mapa, separando ato documentado, alegação, inferência, informado e lacuna. A cronologia deriva desses fatos, sem completar datas nem calcular prazos. Use inventários e `--exigir-pecas` no fluxo integrado; mostre pendências da análise.
6. **Fontes e teses.** A pesquisa localiza candidatos e registra tentativas. A verificação lê a fonte oficial necessária, localiza trecho e distingue apoio, apoio parcial, contradição e ausência de verificação. Vigência e aplicabilidade são avaliações separadas. Citação dentro de voto exige atribuição contextual; o script não prova que o trecho sustenta a tese.
7. **Auditoria.** Informe todos os insumos, tipo de entrega, modo e relatórios. Confira os campos do QC e o estado do pacote, não só o código de saída. No `status`, examine `alterados`, `ausentes`, `revisao_humana` e `liberado_para_uso`: o comando pode retornar zero mesmo com arquivos alterados e revisão pendente. Análise pode conter avisos; uso fundamentado, exposição de fatos e entrega externa recusam pendências materiais conhecidas do uso.
8. **Revisão humana.** O profissional confere fronteiras, tipos, leitura, atribuição e mérito pertinentes. Inventários têm eventos próprios; a aprovação final do pacote usa `auditar.py aprovar`, digitada pela pessoa em terminal interativo conforme a skill. O agente não executa essa confirmação nem cria `aprovacao.json`. Depois, `status` deve reler os artefatos e informar o estado atual. Arquivo local de aprovação não é autenticação externa ou assinatura profissional.

Contratos e minutas seguem ramos próprios e convergem para a auditoria: pré-checagem/apontamentos/redline ou preenchimento de DOCX fornecido com `{{marcadores}}`. Das 21 regras contratuais, 20 estão ativadas pelo revisor (30/10/2026) e só a `civ-598` segue inativa; sem regra ativa, a avaliação jurídica fica ausente como `nao_avaliada` e `entregavel=false`. Modelos sintéticos não comprovam validação contratual real. Não há biblioteca de minutas juridicamente homologadas neste repositório; integrar JurisExpert é uma frente separada.

## Comandos de análise com inventário fornecido

O exemplo pressupõe `extracao.json`, `pecas.json` e `facts.json` efetivamente produzidos e validados; não os cria nem confere automaticamente. Defina uma pasta própria do caso e execute na raiz do projeto.

```powershell
$caso = 'C:/casos/meu-caso'
python scripts/triagem.py pecas --extracoes "$caso/derived/extracao.json" --pecas "$caso/derived/pecas.json" "$caso/input/original.pdf"
python scripts/validate.py "$caso/derived/facts.json" --extracoes "$caso/derived/extracao.json" --pecas "$caso/derived/pecas.json" "$caso/input/original.pdf" --exigir-pecas --modo analise
python scripts/cronologia.py gerar --facts "$caso/derived/facts.json" --extracoes "$caso/derived/extracao.json" --pecas "$caso/derived/pecas.json" "$caso/input/original.pdf" --exigir-pecas --modo analise --saida-json "$caso/outputs/timeline.json" --saida-md "$caso/outputs/cronologia.md"
python scripts/auditar.py auditar --facts "$caso/derived/facts.json" --matter "$caso/matter.json" --extracoes "$caso/derived/extracao.json" --pecas "$caso/derived/pecas.json" "$caso/input/original.pdf" --exigir-pecas --timeline "$caso/outputs/timeline.json" --tipo-entrega interna --modo analise --saida "$caso/outputs/qc.json"
python scripts/auditar.py status "$caso/outputs/qc.json"
```

Para uso fundamentado, altere o modo somente depois de resolver as pendências e rode novamente os consumidores e a auditoria. Entregas externas exigem também relatório com aviso padrão e verificações específicas. A aprovação anterior do QC não é transferível ao novo pacote.

Após a aprovação efetivamente registrada pela pessoa, forneça também o arquivo correspondente ao consultar o estado:

```powershell
python scripts/auditar.py status "$caso/outputs/qc.json" "$caso/outputs/aprovacao.json"
```

Sem esse segundo argumento, `status` informa revisão humana pendente, mesmo que exista um arquivo de aprovação na pasta. Este comando só consulta; não cria nem valida uma aprovação por inferência, e alterações nos artefatos continuam impedindo o uso.

## Compatibilidade e migração explícita

| Situação | Procedimento | O que não transportar |
|---|---|---|
| Caso antigo sem inventário | Preservar arquivos e executar o fluxo legado no seu escopo; se incorporar peças, criar novos artefatos e ligações verificáveis | Não apresentar ausência de inventário como análise integrada de autos completos |
| Mesma extração, primeira proposta | Criar inventário v1 e registrar fontes com `peca`, documento/bloco/trecho/localizador | Não conferir limites/tipos pelo simples sucesso do validador |
| Revisão do inventário | Preservar snapshot exato anterior, incrementar revisão, vincular hash anterior e eventos de correção; usar `--pecas-anterior` | Não manter conferência da dimensão alterada nem reutilizar IDs removidos |
| Nova extração, extrator ou configuração | Guardar nova extração e inventário próprios; reler fontes e reconstruir referências dos fatos/proposições em novos artefatos | Não remapear IDs, offsets, localizadores ou aprovação antigos silenciosamente |
| Alteração em fatos, fontes, original, inventário, DOCX ou QC | Regenerar derivados afetados, auditar novamente e conferir `status` | Não editar pacote aprovado conservando sua aprovação |

Não existe editor/migrador geral de revisões publicado. A revisão assistida segue o contrato e deve ser executada e conferida explicitamente; esta tabela não migra nada. Referência incompatível falha em vez de ser corrigida por adivinhação.

## Repetir a aceitação sem aprovar material

```powershell
python scripts/avaliar_pecas.py --manifesto tests/casos/org05/manifesto.json --saida 'C:/evidencias/nova-aceitacao-fase5'
```

O destino deve ser externo e novo. O comando verifica produto/insumos, não baixa PDFs ou modifica originais; produz cinco observações de quatro unidades, com dois processos novos. Confirmação humana dos gabaritos P01/P02 permanece separada dos inventários propostos. Resultados devem conservar abstenções e bloqueios, sem promover a referência humana a aprovação de uso. Registros antigos continuam históricos; repetir os mesmos casos não cria nova coorte independente.

## Fora da liberação atual

Sem protocolo, envio externo, cálculo de prazo/valor, prognóstico de êxito, acesso automático aos autos completos em PJe/eSAJ ou parecer final. DataJud fornece metadados, não inteiro teor. Nem cobertura universal de tribunais/classes, OCR integralmente fiel, todos os casos contratuais reais, Word, Linux/CI da revisão atual ou instalação foram comprovados pela validação local. Regras e entregas exigem suas decisões próprias; documento, hash, schema e teste não substituem revisão jurídica.
