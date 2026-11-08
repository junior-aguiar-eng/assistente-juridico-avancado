# EV-02 — protocolo da avaliação analítica

Versão 1, 22/10/2026. Implementação offline do avaliador; **baseline ainda não executada**. Andamento e pendências ficam no [plano principal](plano-principal.md). Este protocolo detalha o [piloto aprovado](superpowers/plans/2026-10-22-evolucao-analise-estruturada.md), sem autorizar EV-03 a EV-06.

## Decisões e gates

- Revisor jurídico: titular do projeto, conforme resposta nesta conversa. Designar o revisor não confere os novos gabaritos. A aprovação estrutural anterior de P01/P02 continua válida e não abrange sua avaliação jurídica EV-02.
- Modelos escolhidos: `gpt-6-luna`, `reasoning.effort=high`, e `claude-haiku-5-5`. Duas séries independentes, cada uma mantendo modelo e configuração em A/B/C. Para Haiku, proposta técnica: esforço `medium` padrão, sem equipará-lo a `high` da OpenAI; congelar configuração efetiva antes de executar. Confirmar modelo retornado e disponibilidade da conta; alias sem snapshot imutável exige registrar essa limitação.
- Teto autorizado: **US$ 5 no total**, somando provedores, tentativas, repetições e recuperação. Gasto nesta preparação: zero. Titular configurará o acesso local depois; links dos painéis não fornecem credenciais ao processo. Nenhuma chave foi lida/criada e nenhuma chamada de inferência foi feita.
- Só transmitir fontes públicas selecionadas para o corpus. Dados privados, originais R07/R10, segredos e documentos do checkout Claude ficam fora. A seleção das fontes não libera uso material da análise nem ativa regras.
- Antes da primeira chamada: gabaritos de desenvolvimento conferidos, tarefa/configuração/entradas congeladas, acesso confirmado e estimativa conservadora dentro do saldo. Antes do reservado: corpus completo ou desenho reduzido expressamente registrado, metas congeladas e anotação profissional preservada sem exposição ao fluxo de desenvolvimento.

Os IDs e parâmetros foram conferidos nas documentações oficiais de [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) e [Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview), em 22/10/2026. Tarifas precisam ser reconferidas na [OpenAI](https://developers.openai.com/api/docs/pricing) e na [Anthropic](https://platform.claude.com/docs/en/about-claude/pricing) ao congelar a execução. Não estimar custo de raciocínio como zero nem prometer que o teto comporta todo o piloto.

## Corpus e isolamento

Desenvolvimento: seis processos, P01/P02 e quatro novos públicos. Reservado: doze processos novos, quatro acórdãos isolados (até 40 páginas), quatro conjuntos de 3–10 peças (até 120 páginas) e quatro de 11–30 peças (até 250 páginas); seis nativos, três digitalizados e três mistos, pelo menos três tribunais e duas origens no grupo OCR/misto. Não fabricar digitalização de um PDF nativo para preencher um estrato.

Uma página, peça, versão ou repetição não é um processo novo. Separar a família recursal e duplicatas substanciais; R07/R10 e processos já usados não entram no reservado. Partes/advogados/teses semelhantes não demonstram identidade; metadados de família e duplicata exigem curadoria. Hash detecta igualdade dos bytes, sem comprovar independência semântica. Citações naturais comuns não são duplicatas de processo.

Originais, extrações congeladas, referências, anotações e respostas reais ficam **externos ao Git**, em pasta nova. Preservar origens/URLs, data de obtenção, SHA-256 de bytes e limitações de leitura. Nenhuma coleta autenticada, contorno de restrição, instalação ou download de modelo é necessário ao avaliador.

`validar_corpus(manifesto, entradas)` recebe objetos e bytes já obtidos pelo chamador; não abre caminhos. Manifesto `schema_version="1"`, `casos` (lista), cada caso com:

| Campo | Contrato |
|---|---|
| `id`, `processo_id`, `familia_id`, `duplicata_id` | Identidades explícitas; família/duplicata curadas antes da separação |
| `grupo` | `desenvolvimento` ou `reservado` |
| `tribunal`, `origem` | Origem identificada, sem contar nomes cosmeticamente diferentes como novas fontes |
| `modalidade` | `nativo`, `digitalizado` ou `misto` |
| `paginas`, `pecas` | Inteiros positivos; seções internas não viram peças |
| `artefatos` | Lista de `id`, `tipo` (`original`/`extracao`) e `sha256`; ao menos um de cada tipo |

`entradas` é `dict[artifact_id, bytes]`, todos os snapshots não vazios. Caminhos podem constar no manifesto externo como localização auxiliar, nunca são seguidos pela função. IDs de artefatos são únicos; mesmo processo duplicado é recusado. Identidades são normalizadas para detectar diferenças de pontuação/caixa; IDs devem conservar prefixo do tribunal para evitar colisões. Família, duplicata ou bytes cruzando coortes reprovam. Repetições de família, duplicata curada ou bytes entre processos da mesma coorte geram lacuna de independência, mesmo quando as contagens nominais atingem a meta. Metadados válidos com corpus insuficiente retornam `valido=true`, **`cobertura_planejada=false` e lacunas explícitas**. Isso não libera avaliação reservada. Metadados não garantem que um documento de uma página seja realmente acórdão nem que as peças estejam completas.

## Tarefa comum e congelamento

Texto proposto para a baseline de desenvolvimento, a congelar com as skills da base:

> Analise somente o processo e as fontes fornecidos. Entregue análise documental cível estruturada por questão: pedidos, posições e argumentos materiais, fatos e provas com atribuição, fundamentos efetivamente lidos, confronto das posições, resultado e alcance, conclusões preliminares, alternativas e limites. Distinga fala própria, relato e transcrição, decisão atual e precedente, prova primária e narrativa secundária. Vincule afirmações ao documento, página e trecho; registre ausência/ilegibilidade sem inventar conclusão. Automatize verificações técnicas possíveis com os insumos disponíveis; destaque ao profissional decisões jurídicas importantes. Não presuma leitura de peça ausente, não simule revisão humana e não ative regras. Preserve explicitamente o que não conseguiu analisar.

A usa o código/skills congelados de `785d4ce39124a4077e49ef438b91f4ed15259f03`, sem melhoria EV-03. A ausência de saída no formato `analise-1` conta como limitação; um adaptador apenas mapeia campos existentes, sem criar argumentos ou completar omissões. Preservar resposta bruta e registrar hash/versão/tempo da adaptação. Não confundir o `sha256` do conteúdo adaptado com o da resposta bruta.

Semântico: mesmas extrações e fontes congeladas em A/B/C; sem rede, reextração ou descoberta de autoridades durante a execução. Ponta a ponta: mesmos originais, extração de cada variante; relatório separado. Pesquisa remota é ensaio separado, não liberado pela escolha de modelos. Referências jurídicas citadas dentro de um acórdão são referências secundárias até leitura autônoma, não autoridades automaticamente fornecidas.

Antes de executar, gravar manifesto externo com hash de produto/skills, prompt comum, ferramentas permitidas (leitura dos snapshots e scripts offline selecionados; sem escrita de originais), configuração completa, hashes dos insumos, coorte, número de repetições e ordem randomizada. O sorteio deve ter seed registrada; saídas para revisão recebem rótulos cegos. Gabarito não entra no prompt. Guardar resposta nativa, erro/timeout/uso/tokens/modelo retornado e intervenções. Não alterar uma execução histórica para corrigir seu resultado.

Proposta principal: 12 processos × A/B/C × 2 repetições = 72 execuções por experimento **por modelo**, até 288 para dois modelos e dois experimentos. EV-02 prepara/executa somente A no desenvolvimento quando seus gates fecharem; B/C dependem das etapas seguintes. Não iniciar todas as execuções sob um orçamento insuficiente. Redução da amostra/repetições/experimentos deve ser definida antes de coletar, sem seleção posterior dos acertos. Amostra exploratória não permite promessa populacional.

Reserva de custo antes de cada chamada: somar gasto confirmado, custos ainda desconhecidos das chamadas iniciadas e pior custo da próxima (entrada, saída/raciocínio máximo, faixas longas, cache e ferramentas). Não conceder desconto de cache sem comprovação. Limite financeiro compartilhado US$ 5; proposta operacional de parar em US$ 4,50 para margem, sem tratar margem como verba adicional. Custo desconhecido bloqueia a chamada seguinte até reconciliação. Usar execução sequencial, sem retry automático, ferramentas pagas ou chamadas simultâneas. Registrar posições interrompidas como `limite`/`nao_executada` e as tentativas falhas separadamente. Este módulo **não executa nem impõe** esse controle; o executor futuro deverá aplicá-lo. Tetos de tempo, saída e chamadas por execução permanecem a congelar após medir tamanho dos insumos, antes de chamar API.

## Gabarito e julgamento

Interfaces puras em [avaliar_analise.py](../scripts/avaliar_analise.py):

```python
avaliar_caso(predicao: dict, gabarito: dict, julgamento: dict) -> dict
agregar_resultados(resultados: list[dict]) -> list[dict]
validar_corpus(manifesto: dict, entradas: dict[str, bytes]) -> dict
```

Formato v1 dos objetos e exemplo sintético executável: [testes](../tests/test_avaliar_analise.py), função `dados`. Nada nesses exemplos é caso real ou aprovação do titular.

`predicao`: versão, `execucao_id`, `caso_id`, processo/família/grupo, `serie_id`, modelo/configuração, hashes do prompt/produto/entradas/saída, experimento, variante, repetição, condição `nativa`/`assistida`, estado e itens `{id,tipo,texto}`. `tipo` é `afirmacao` ou `limitacao`. Operação guarda custo USD e latência (números não negativos ou `null` desconhecido) e chamadas (inteiro). Estado é `concluida`, `abstencao`, `falha`, `timeout`, `invalida`, `limite` ou `nao_executada`. Resposta disponível exige hash; falha sem resposta pode ter hash nulo. A lista de itens é a saída adaptada, não a prova de fidelidade da adaptação.

`gabarito`: versão, caso/processo/família/grupo/entradas correspondentes, `revisao` (`status`, `revisor`, `data`), itens materiais `{id,classe,descricao,central,respondivel,fontes}` e rubrica. Classes: `questao`, `pedido`, `argumento`, `fato`, `resultado`, `alcance`. Fontes `{artifact_id,localizador}` têm que pertencer às entradas. `respondivel=false` requer justificativa jurídica no texto do item, apontando qual insumo falta. O revisor deve completar questões/pedidos/argumentos, resultado/alcance, evidências e erros críticos esperados; candidatos técnicos não são gabaritos jurídicos completos. Divergências/correções permanecem no registro externo. Rubrica contém as quatro dimensões, cada uma com `aplicavel` e motivo para não aplicável.

`julgamento`: `status=conferido`, versão, execução, revisor/data, hashes lógicos `predicao_sha256`/`gabarito_sha256`, correspondências, notas, erros, revisão ativa em segundos, perguntas triviais e referências resolvidas/total. `sha_objeto` usa JSON UTF-8 ordenado e compacto; não é o hash bruto de arquivo. Gravar também os hashes dos arquivos no manifesto externo. Alterar uma entrada após conferência invalida o julgamento vinculado. Nome/data declarados não autenticam uma pessoa e não viram evento dos gates legados.

Cada item proposto recebe exatamente uma correspondência: `{predicao_id,gabarito_id,resultado}`, com resultado `correto`, `incorreto`, `abstencao_correta` ou `abstencao_indevida`. Alvo pode ser nulo apenas para excesso incorreto. Um item de gabarito não recebe crédito duplo. Acerto exige afirmação e insumo suficiente; abstenção exige limitação explícita, sendo correta apenas se o item não for respondível. Item material omitido não recebe crédito. Isso contabiliza julgamento; não faz matching semântico, não verifica automaticamente apoio/pertinência e não detecta omissões jurídicas fora do gabarito.

As quatro notas 0–4 são `conexao` (fato/prova/fundamento), `contraposicoes`, `consequencias` e `limites`: 0 ausente/errada, 1 lista/paráfrase, 2 conexão parcial com lacuna material, 3 conexão dos elementos materiais e objeções/limites, 4 também explica alternativas/consequências com precisão. Não aplicável exige motivo do gabarito e nota nula; não elimina a execução.

Erros têm `id`, `critico`, `silencioso`, `motivo`. Qualquer erro crítico impede adoção no escopo, inclusive quando explicitado. Erro crítico silencioso recebe critério booleano separado. Exemplos: processo/parte/resultado invertidos, pedido central respondível omitido, apoio/autoridade inventado, leitura insuficiente escondida ou aprovação humana simulada. Testes/esquema/hash não estabelecem inexistência desses erros.

Tempo humano é trabalho ativo até corrigir/decidir com a mesma finalidade, incluindo correções; espera do modelo é latência, não tempo humano. Pergunta trivial é resolvível do insumo legível/ferramenta permitida; deixar de perguntar omitindo o tema não é ganho. Uma pessoa fará a revisão: registrar o risco de memória mesmo com cegamento/ordem aleatória; segunda revisão é recomendada para divergências sem pressupor contratação.

## Métricas e leitura dos resultados

- Recall: itens materiais corretamente respondidos / todos os itens do gabarito, por classe e total. Limitação correta não conta como solução. `centrais_tratados`: central corretamente respondido ou explicitamente limitado por falta real de insumo / centrais. Abstenções corretas/indevidas ficam separadas.
- Precisão: respostas corretas / afirmações propostas. Limitações não entram nesse denominador; correspondências extras incorretas penalizam precisão. Razão com denominador zero retorna `valor=null`, nunca 100% por ausência de saída.
- Falha técnica, timeout, saída inválida, limite e não execução: com gabarito conferido, recall/tratamento e notas aplicáveis zero, mantendo a execução no total. Sem gabarito conferido, nota fica pendente. Gabarito ou julgamento jurídico pendente não é aprovação, nota automática ou exclusão silenciosa.
- Agregação: separada por série/modelo/configuração, experimento, condição, coorte e variante. Repetições não viram processos. Micro soma numeradores/denominadores; macro calcula média das repetições por processo e depois média dos processos. Reportar famílias também; parentesco repetido não estabelece independência. Cobertura de avaliação é execuções medidas / todas as registradas, incluindo pendentes. Média com cobertura incompleta não sustenta aceitação.
- O agregador informa pior recall, profundidade macro por dimensão, mediana de tempo por processo, custo conhecido, custos desconhecidos, chamadas, perguntas triviais conhecidas, erros críticos conhecidos e execuções sem julgamento crítico. Não infere que custo desconhecido é zero ou que erro não julgado inexiste. Preservar os resultados individuais para pior repetição e distribuição; não descartar falhas por média boa.
- Registrar **todas** as posições planejadas, inclusive não executadas. A função não conhece posições ausentes da lista. Tentativas e recuperação assistida possuem IDs distintos; não substituem a posição nativa. Uma série com modelo/configuração/prompt variável ou posição repetida é recusada. No experimento semântico, entradas e gabarito também precisam permanecer idênticos por processo entre modelos e variantes. O agregador não é um atestador contra adulteração de resultados construídos manualmente.

Metas congeladas para a comparação futura: referências usadas 100% resolvidas; nenhum erro crítico, envio não autorizado, alteração de original ou evento humano forjado; centrais corretamente tratados; recall macro ≥90%, precisão ≥95%; notas ≥3 por dimensão aplicável/caso; C melhora média ≥0,5 versus A e mediana de redução de tempo ≥30% por processo. Se A≥3,5, manutenção da qualidade e ganho de tempo. Trivialidades reduzem ≥50% quando A>0, senão permanecem zero. B não introduz erro crítico nem queda ≥1 em dimensão e demonstra ganho técnico. Todas as execuções devem estar dentro dos tetos ou interrompidas explicitamente.

Ganho de tempo utiliza mediana das repetições de A/C por processo e `(T_A-T_C)/T_A`, somente com T_A positivo; faltas são relatadas, não preenchidas. O módulo fornece os componentes, **não declara comparação A/B/C aprovada** nem implementa testes estatísticos ou política de liberação. Um holdout aberto fica congelado; correções voltam ao desenvolvimento e uma nova alegação independente exige nova amostra.

## Verificação e limitações da etapa

Rodar `python -m pytest -q tests/test_avaliar_analise.py`, depois suíte offline integral no ambiente próprio. Os testes usam apenas dados sintéticos; as anotações reais externas precisam de conferência do titular. Preservar snapshot do código no início da integral e conferir hashes ao fim. Revisão mecânica das skills e diff final são verificações técnicas adicionais, sem comprovar qualidade jurídica ou execução de modelos.

Enquanto faltarem gabaritos conferidos/acesso/protocolo de execução fechado, não produzir relatório de baseline, pontuação comparativa ou declaração de conclusão EV-02. Se faltar corpus reservado, relatar estratos ausentes e manter o gate da comparação reservado pendente, sem converter P01/P02 em casos novos.
