# Plano principal: juris-skills-br

Revisão 16 — 2026-10-22. **Este é o plano vigente e a fonte única de prioridades e andamento.** Substitui o [planejamento v2](planejamento-juris-skills-br-v2.md), preservado como histórico. Pesquisa, especificações e relatórios detalham decisões; não mantêm cronogramas ou listas de execução concorrentes.

**Objetivo:** manter as oito skills e o fluxo atual de evidências, acrescentando organização verificável de peças antes de liberar análise assistida de autos completos.

**Arquitetura:** conservar extração, validação, auditoria e formatos existentes. Acrescentar um inventário de peças que referencie a extração, distinguindo arquivo, peça, seção e bloco. Melhorias de OCR e eventual adaptador de extração têm avaliação própria e convergem para esse fluxo.

**Tecnologias:** Python >=3.12, ferramentas e dependências atuais. Docling Parse/Core foram avaliados em piloto local limitado e permanecem experimentais; não foram adotados como extrator padrão. O pipeline completo Docling não foi avaliado. VICTOR é referência metodológica, sem autorização presumida para copiar código, dados ou pesos.

**Especificação da nova etapa:** [inventário de peças](especificacao-inventario-pecas.md). Evidências: [pesquisa de referências](pesquisa-segmentacao-autos-2026-10-22.md) e [corpus privado](validacao-corpus-privado-2026-10-22.md).

## 1. Marco preservado

- Esta cópia concilia o snapshot Codex `abbf85a` com AF-01/CP-01/AC-01/GT-01 sem commit e os incrementos recuperados até `ff225a7`. Registro: [reconciliação RC-01](reconciliacao-org-2026-10-22.md).
- Oito skills existentes; as **19 regras de Código Civil/LGPD permanecem inativas**, conforme determinação do usuário nesta reconciliação. A ativação registrada na outra branch não foi aplicada. NDA permanece sem regras. Revisão jurídica, aprovação de entregas e validação técnica são etapas distintas.
- A base Codex registra 732 testes aprovados/3 ignorados na GT-01; as entregas ORG registram seus resultados históricos em Linux. RC-01 registra 943 aprovados/5 ignorados e 304 focados em ambiente limpo. **VT-01 repete a suíte completa no worktree Codex e no ambiente limpo: 943 aprovados/5 ignorados, sem falhas, em 859,31 s**; dois testes de rede, piloto opcional Docling e dois originais privados ausentes foram ignorados. Os 160 testes do snapshot intermediário também passaram; isso não constitui avaliação jurídica ou CI remoto.
- **ORG-04 implementada e validada localmente:** 41 testes novos, 283 aprovações focadas e **984 aprovados/5 ignorados na suíte integral offline**, sem falhas, em 815,17 s. A primeira execução teve uma falha de decodificação no ambiente; a repetição com UTF-8 consistente passou sem alterar produto/teste para essa falha. Oito skills PRONTA; referências opcionais e restrições por uso integradas. Ver [relatório](integracao-org04.md). ORG-04 no commit local `a3848b1`, sem push. ORG-05 concluída no escopo assistido medido após a confirmação humana dos gabaritos P01/P02, sem liberação da fase 5.
- **ORG-05 — verificação técnica:** dois processos públicos novos, avaliação inicial congelada separada das regressões posteriores e oito skills em 16 cenários. Suíte integral offline: **1014 aprovados/5 ignorados, zero falhas/erros em 891,51 s**. Oito skills PRONTA; dependências sem conflitos. Correções de identidade multidocumento, relatório redline e métricas verificadas; classificação se absteve nos dois processos novos. [Evidências e limites](validacao-org05.md). Gabaritos estruturais P01/P02 revisados e aprovados pelo titular em 22/10/2026 ([registro](../tests/casos/org05/conferencia-humana.json)); fechamento e commit local autorizados, sem push. O commit que contém este registro identifica a entrega ORG-05.
- **Fase 5 — validação técnica local e CI publicadas:** base local `910b11e`, sem mudanças funcionais na fase 5. Aceitação em cinco observações/quatro unidades e oito CLIs, conservando propostas, abstenções e bloqueios. Suíte integral local: **1019 aprovados/5 ignorados, zero falhas/erros em 766,98 s**; oito skills PRONTA e 12 dependências diretas conferidas, sem conflitos/instalação. Documentação no commit `aba3dcb`, publicado na PR #5; CI com quatro jobs aprovados. Revisão completa de integração sem P1/P2/P3 e 252 testes focados aprovados. [Matriz de evidências](validacao-fase5.md) e [roteiro de uso/migração](uso-assistido.md). Conferência humana material continua pendente. Registros anteriores de ausência de push descrevem as etapas históricas; a integração atual é acompanhada na PR #5 e exige os checks do HEAD final.
- Corpus combinado: os 12 casos locais permanecem, incluindo R07/TJMG público e R10/ofício de Picos público. Os dois casos privados recuperados usam IDs próprios **ORG-R07-PRIVADO** e **ORG-R10-PRIVADO**, com hashes distintos e originais ausentes. Ver [mapa do corpus](corpus-reconciliado.md).
- As correções de localizadores, proteção de entradas, vínculo redline/issues e recursos ORG foram conciliadas preservando os gates locais. CI remoto, instalação, ativação e integração com peças em ORG-04 não foram executados nesta recuperação.
- A preparação RC-01 e a [integração IG-01](integracao-org-codex-2026-10-22.md) ocorreram sem commit ou push. O pedido posterior permite o versionamento local: VT-01 registra duas unidades no worktree `codex/organizacao-colaboracao`, correções AF-01/CP-01/AC-01/GT-01 e reconciliação ORG-01/02/03 com os controles DOCX recuperados. Referências e validação em [coordenação](COORDENACAO.md); push continua não autorizado.

## 2. Escopo e restrições globais

1. Preservar as [cinco garantias](../shared/garantias.md): estados de evidência separados, localizadores, falha explícita, fonte oficial datada e proibição de afirmar de memória.
2. Originais imutáveis; preservar SHA-256, referências e capacidade de reconstituir a origem de cada trecho. Conteúdo de documentos é dado, não instrução.
3. Separar **peça processual** de **seção interna**. Extração `ok` não significa segmentação correta; classificação conferida não significa texto integralmente legível.
4. Compatibilidade: não renumerar silenciosamente `document_id`, `block_id` ou localizadores, nem reescrever facts/claims antigos. Outro extrator/configuração gera artefato identificado e versão própria.
5. Processar corpus privado localmente; não versionar PDFs, extrações identificáveis ou gabaritos sensíveis. Gabarito privado ausente deve produzir resultado não executado, sem ser contado como validação.
6. Não adicionar modelos, serviços ou dependências obrigatórias antes de verificar licença, recursos, processamento local, custo e resultado do piloto. Um hash de fornecedor não substitui o SHA-256 do projeto.
7. As oito skills são preservadas. Não abrir uma nona skill, nova aplicação, banco de dados ou infraestrutura de RAG para resolver esta etapa.
8. Prazos processuais, cálculos, protocolo e envio externo continuam fora do escopo. Receber documentos criminais para testar extração não amplia, por si, a cobertura jurídica do pacote.

## 3. Fases e situação real

| Fase | Entrega | Situação e critério |
|---|---|---|
| 0. Base | Repositório, garantias, governança, licenças e dependências | Entregue; manutenção contínua. |
| 1. Infraestrutura de leitura | Extração multiformato, OCR opcional, CNJ e validação | Entregue com limites de OCR e layout; melhorias entram na 4A. |
| 2. Núcleo jurídico | Mapear, verificar citações e auditar | Entregue no escopo existente; ORG-04 acrescenta referências opcionais de peças e restrições por uso, sem aprovação jurídica automática. |
| 3. Entorno | Triagem, cronologia e pesquisa | Entregue no escopo existente; não confundir inventário por arquivo com inventário de peças. |
| 4. Contratos e minuta | Pré-checagem, issues, redline e preenchimento | Parte mecânica entregue, com auditoria documental e avaliação jurídica pendente explícita; 19 regras inativas e NDA sem regras. |
| **4A. Organização dos autos** | Inventário de peças, fronteiras, seções internas, qualidade de leitura e integração | **ORG-01/02/03 recuperadas e conciliadas; ORG-04 no commit local `a3848b1`. ORG-05 concluída no escopo assistido medido, com gabaritos P01/P02 conferidos pelo titular. A fase 5 e a liberação de autos completos permanecem abertas.** |
| 5. Liberação | Regressões, avaliação das skills, compatibilidade e limites publicados | Validação técnica local e CI da proposta publicadas; integração pela [PR #5](https://github.com/junior-aguiar-eng/assistente-juridico-avancado/pull/5), condicionada aos checks do HEAD final. Gates humanos de uso material abertos. [Resultados e limites](validacao-fase5.md). |

OCR e DOCX/redline deixaram de ser itens futuros: já existem. A nova etapa aperfeiçoa e integra o que falta, sem apagar esse histórico.

## 4. Execução da fase 4A

IDs abaixo são estáveis. Dependências determinam a ordem; os detalhes de implementação de cada pacote são registrados antes de executá-lo. A ORG-04 acrescenta parâmetros opcionais e orientações às skills consumidoras; as interfaces legadas são preservadas.

| ID | Pacote e resultado verificável | Depende de | Critério de conclusão | Estado |
|---|---|---|---|---|
| ORG-01 | Contrato do inventário e gabarito inicial: arquivo, peça, seção, bloco; fronteiras; estados de conferência; exemplos anônimos | Marco preservado | [Contrato v1](contratos/pecas-v1.md), esquema estrutural e exemplos verificáveis; fronteira física do ORG-R07-PRIVADO conferida visualmente e confirmada pelo titular (1–24/25–38), sem promover âncora técnica a confirmação humana | Entregue; verificação final no [relatório ORG-01](entrega-org01-2026-10-22.md) |
| ORG-02 | Validador semântico do contrato, segmentação de referência e piloto comparativo: títulos espaçados, início/continuação, evidências de fronteira, revisão manual; comparar extração atual e candidato Docling | ORG-01 | Códigos de erro do contrato exercitados; casos adversariais, fusão/fragmentação, custo e licenças verificados; decisão de adotar ou rejeitar adaptador registrada com evidências | Entregue: [validação e piloto](piloto-org02-2026-10-22.md); 635 testes aprovados/3 ignorados na origem, resultado histórico; Docling Parse experimental, sem adoção no fluxo padrão |
| ORG-03 | Qualidade de OCR: diagnóstico do ORG-R10-PRIVADO, experimento local, comparação com transcrição conferida, preservação de originais e avisos | ORG-01 | Resultado e limitações reproduzíveis; expectativas textuais conferidas. Se continuar insuficiente, declarar trecho ilegível e manter bloqueio de uso material, sem forçar leitura | Entregue: [experimento OCR](experimento-org03-2026-10-22.md), seis amostras humanas; mediana/72 opcional, texto integral não conferido; 676 testes aprovados/3 ignorados na origem, resultado histórico |
| ORG-04 | Integração do inventário nas skills e nos gates, preservando fluxos anteriores | ORG-02; diagnóstico e decisão de uso do ORG-03 | Referências peça/bloco verificáveis; pendência material de fronteira, atribuição ou leitura aparece na entrega e impede aprovação técnica fundamentada daquele uso; testes legados preservados | Entregue localmente: [implementação e evidências](integracao-org04.md), 984 aprovados/5 ignorados; commit local `a3848b1`, sem push |
| ORG-05 | Validação integrada e ampliação do corpus, separando resultados por processo e modalidade de leitura | ORG-04 | Gabaritos conferidos, avaliação com casos não usados no ajuste, métricas e falhas publicadas; segunda avaliação das skills realizada no escopo efetivamente disponível | Concluída no escopo assistido medido: [corpus e métricas](validacao-org05.md), [segunda avaliação](avaliacao-skills-org05.md), [gabaritos P01/P02 conferidos](../tests/casos/org05/conferencia-humana.json); sem liberação material ou push |

ORG-02 e ORG-03 podem avançar independentemente depois do contrato comum. Compartilham o mesmo plano, formatos e registro de decisão; não são projetos paralelos. ORG-04 pode integrar leitura parcial explicitamente recusada: não exige prometer OCR perfeito, mas exige impedir que sua falha seja tratada como evidência legível.

### Ordem de trabalho

```text
marco atual → ORG-01 → ORG-02 ─┐
                     ORG-03 ─┴→ ORG-04 → ORG-05 → fase 5
```

O fluxo de uso pretendido é: triagem → inventário de arquivos → extração → inventário de peças e conferência de leitura → mapeamento/pesquisa/cronologia → auditoria → aprovação humana. O inventário de peças não substitui nenhuma verificação de fonte ou de mérito jurídico.

## 5. Limites de módulos e arquivos

Destinos abaixo orientam o detalhamento; arquivos propostos não devem ser criados como estruturas vazias antes de sua tarefa.

| Área | Destino | Responsabilidade e limite |
|---|---|---|
| Extração | `scripts/extract.py` | Texto, blocos, seções e proveniência. Não concentrar nele toda a classificação de peças. |
| Inventário de peças | `scripts/pecas.py`, `pecas_validacao.py`, `pecas_historico.py` e proposta opcional em `pecas_proposta.py`; artefato `derived/pecas.json` | Validar ligações e revisões; propor fronteiras sem conferir automaticamente. O contrato exato precedeu a implementação; integração em consumidores permanece separada. |
| OCR | `scripts/ocr.py` e testes existentes | Qualidade de leitura e diagnósticos. Não decidir natureza jurídica da peça. |
| Adaptador de extração | `scripts/piloto_pecas.py`, experimental; integração depende de decisão posterior | Comparar extrações e adaptar linhas com proveniência, mantendo fornecedor fora das dependências obrigatórias das oito skills. |
| Consumidores | `scripts/triagem.py`, `validate.py`, `cronologia.py`, `auditar.py` e skills afetadas | Consumir referências ao inventário e aplicar restrições por uso; não duplicar o classificador em cada módulo. |
| Testes | `tests/test_pecas*.py`, `tests/test_org04.py`, `tests/test_avaliar_pecas.py`, `tests/test_piloto_pecas.py` e regressões existentes | Cenários de fronteiras e compatibilidade com fixtures anônimas; corpus privado opcional e explicitamente separado. |
| Contrato publicado | `shared/dados.md`, depois da implementação validada | Documentar o novo artefato e eventual extensão aditiva. O contrato está definido em `docs/contratos/pecas-v1.md`; sua publicação em `shared/dados.md` depende da implementação validada. |

Nenhuma troca de extrator é presumida. Se o piloto não justificar Docling, o inventário pode continuar usando a extração atual com a mesma interface.

## 6. Validação e pontos de atenção

As condições abaixo devem aparecer nos testes do pacote responsável, não apenas em uma checklist de revisão:

| Condição de risco | Comportamento esperado | Responsável |
|---|---|---|
| Título de outra peça dentro de citação, ementa ou transcrição | Não abrir nova peça só pela palavra; registrar sinais e permitir revisão | ORG-02 |
| Duas peças consecutivas do mesmo tipo; duas peças na mesma página | Inícios distintos e fronteiras por bloco/região, sem fusão automática | ORG-01/02 |
| Anexo, capa, página vazia, continuação sem título ou tipo desconhecido | Cobertura explícita; não herdar tipo anterior como certeza; incerteza e leitura ausente preservadas | ORG-01/02/03 |
| Troca de extrator, configuração, hash ou ordem dos blocos | Rejeitar referência incompatível; nunca remapear evidências silenciosamente | ORG-01/04 |
| OCR com nomes, datas, números ou dispositivo ilegíveis | Aviso e abstenção de uso material; `partial` não é aprovação da leitura | ORG-03/04 |

Métricas separadas: fronteiras corretas, fusões, fragmentações, tipo da peça, abstenções e qualidade do OCR em trechos relevantes. Informar denominadores e condições; não criar percentuais de precisão a partir dos testes atuais. Separar ajuste e avaliação por processo, evitando colocar páginas do mesmo processo nos dois grupos. Variações de leitura do mesmo documento não contam como processos independentes.

A matriz precisa cobrir as classes prometidas; tipo sem corpus suficiente deve ser declarado sem cobertura validada. ORG-R07-PRIVADO/ORG-R10-PRIVADO são regressões úteis, não prova de generalização para todos os tribunais e autos.

## 7. Critérios da fase 5

- [x] ORG-01 a ORG-05 concluídos com evidências e limitações registradas; escopo de liberação declarado como **assistido**, sem promessa de classificação universal automática.
- [ ] Fluxo completo liga arquivo → peça → seção/bloco → fato/proposição → auditoria, com conferência humana das fronteiras e tipos usados materialmente. Cadeia técnica exercitada; inventários reais continuam propostos. Aprovação estrutural dos gabaritos P01/P02 preservada, sem convertê-la em conferência de fragmentos/atribuição ou aprovação de entrega.
- [ ] Nenhuma fusão, atribuição errada ou leitura insuficiente conhecida é silenciosamente aceita como evidência conferida nos casos de aceitação. Controles técnicos de avisos/bloqueio exercitados; conferência semântica material permanece humana, inclusive transcrições com `is_quote=false` nos casos novos.
- [x] Suíte relevante e completa executada; passar, falhar, ignorar e não executar registrados separadamente. Corpus privado ausente não comprova sua validação. Fase 5: 1019 aprovados/5 ignorados, zero falhas/erros; Windows/Python 3.14.6 offline, saída/JUnit e hashes conferidos.
- [x] Avaliação das skills repetida com documentos reais; aprovação jurídica declarada não substitui essa avaliação nem a aprovação de entregas concretas. ORG-05: oito skills/16 cenários, corpus público real nas skills de autos/pesquisa/auditoria e controles sintéticos nas contratuais; validação contratual real continua pendente.
- [x] Compatibilidade com casos antigos demonstrada; migração explícita para novos artefatos, sem alteração dos originais. Suíte legada/integrada aprovada e roteiro de atualização documentado; nenhuma migração automática ou editor geral de revisões é declarado.
- [x] Licenças, modelos, custos e configuração reprodutível conferidos; documentação e avisos de terceiros atualizados somente para o que for efetivamente adotado. Versões/licenças das 12 dependências diretas nos metadados locais, ambiente e limites da sessão documentados; sem nova adoção ou API de geração. Não é parecer de redistribuição ou certificação de inferência local.
- [x] CI remota conferida quando houver autorização para publicar as mudanças. Publicação autorizada: commit, push, PR e merge após revisão/CI. [PR #5 / CI 39865227437](https://github.com/junior-aguiar-eng/assistente-juridico-avancado/actions/runs/39865227437), head `aba3dcb`: quatro jobs Ubuntu/Windows Python 3.12/3.13 aprovados e oito skills PRONTA em todos. O registro é documental; conferir também a CI do HEAD final antes do merge. Detalhes e contagens em [fase 5](validacao-fase5.md).

Testes podem passar verificando que uma falha é avisada; isso não converte a capacidade defeituosa em capacidade resolvida. A liberação deve distinguir uso que funciona, uso assistido e uso ainda recusado.

## 8. Pendências consolidadas após a reconciliação

A **ORG-04 foi entregue e validada localmente** e recebeu o commit local `a3848b1` por autorização posterior, sem push. Integra referências opcionais e restrições por uso em `validate.py`/`auditar.py`, triagem e cronologia, com as instruções das skills consumidoras. **ORG-05 com entrega técnica verificada**: dois processos públicos novos, métricas separadas e segunda avaliação das oito skills. Após o adiamento inicial, o titular confirmou a revisão e aprovação dos gabaritos estruturais P01/P02 em 22/10/2026; a ORG-05 está concluída no escopo assistido medido e a fase 5 permanece aberta. As correções encontradas na avaliação são regressões posteriores, sem nova coorte independente.

| Prioridade ou gate | Pendência confirmada | Evidência necessária para encerrar |
|---|---|---|
| Insumos privados | Originais ORG-R07-PRIVADO e ORG-R10-PRIVADO ausentes nesta máquina | Recuperar arquivos autorizados fora do Git e conferir os hashes esperados antes de repetir o experimento. As fronteiras e seis amostras históricas não comprovam fidelidade integral. R07/TJMG e R10/Picos públicos continuam disponíveis e separados. |
| Revisão jurídica humana | Conferência das regras, gabaritos e entregas; 19 regras inativas e NDA vazio | Revisão identificada e decisão expressa para qualquer ativação futura. Testes, recuperação de aprovação de outra branch ou commit não autorizam ativação. |
| Validação contratual e encerramento pelo responsável | Contratos/NDA/modelos reais autorizados e fechamento formal de CL-01/CL-02 ainda não demonstrados | Avaliação documentada além dos controles sintéticos, revisão jurídica quando cabível e encerramento registrado pelo responsável. |
| Integração e fase 5 | Conferência humana dos inventários/trechos usados materialmente e aprovação da entrega pendentes | Critérios da seção 7 e [evidências de fase 5](validacao-fase5.md). Não reabrir os gabaritos estruturais P01/P02 já aprovados. Publicação/integração autorizadas e acompanhadas na [PR #5](https://github.com/junior-aguiar-eng/assistente-juridico-avancado/pull/5), com checks do HEAD final exigidos antes do merge. Instalação continua separada. |
| Operação de rede | Estabilidade DataJud ainda não demonstrada | CP-01 registra sucesso real após o patch em 21/10, mas houve timeouts anteriores. Novas verificações de rede são separadas e opcionais; a suíte offline não demonstra estabilidade. |

As correções AF-01/AC-01/GT-01 e a recuperação/integração RC-01/IG-01 são entregas locais registradas, não novas pendências de implementação. Assinatura externa, prova semântica e revisão jurídica conservam os limites abaixo.

| Pendência | Tratamento no plano |
|---|---|
| Assinatura externa para aprovação resistente à escrita local | Decisão de arquitetura e custódia ainda aberta; manter limite do arquivo local explícito. Não misturar com o inventário. |
| Natureza da prova e relação semântica entre trecho e proposição | Inventário melhora atribuição, mas não prova o fato nem a tese. Continuam revisão jurídica e avaliação das skills; qualquer automação nova exige escopo próprio. |
| Hash de fonte sem arquivo disponível | Preservar limite de reverificação; não declarar conferência criptográfica sem acesso aos bytes. A reconciliação de c001/s2 e c005/s1 foi entregue em pacote externo novo; não recuperou a identidade dos bytes históricos nem o inteiro teor de c005, que permanece `partial`/ementa. Não reabrir a reconciliação já concluída nem promover esses limites a leitura integral. |
| Pacote NDA vazio | Frente de regras jurídicas, dependente de fontes e revisão próprias; não bloqueia o piloto de peças nem recebe regras improvisadas. |
| Ampliação futura do corpus | ORG-05 encerrada no escopo medido; diversidade adicional de processos/modalidades exige escopo e evidências próprios. Preservar privacidade e registrar ausência. |
| Docling Parse e troca de extrator | Piloto experimental, sem adoção como padrão. Uma eventual adoção exige decisão posterior sustentada por qualidade, recursos, licença e compatibilidade; não é pré-requisito presumido para ORG-04. |

## 9. Disciplina de engenharia

- Atualizar andamento e dependências **somente aqui**. Especificações explicam contratos; pesquisa registra evidência; relatórios registram execuções. Não criar um segundo roadmap.
- Cada pacote começa com plano executável proporcional, arquivos/interfaces definidos e testes de aceitação. Não implementar a fase inteira em uma mudança única.
- Aplicar teste que reproduz o problema antes da correção, revisão de código e verificações adequadas. Rodar pytest sequencialmente ou com diretórios `--basetemp` distintos.
- Commits pequenos, por entrega verificável; preservar alterações anteriores. Não criar worktree adicional automaticamente no ambiente de nuvem já isolado.
- Manter mudanças de documentação, piloto opcional e mudança do comportamento padrão distinguíveis. Nenhuma nova dependência/modelo entra só para preencher a arquitetura proposta.
- Registrar adoção/rejeição de tecnologia com evidências no relatório do piloto e resumir a decisão aqui. Sem licença clara, não copiar código/dados/pesos de terceiros.
- Alterações de regras, escopo jurídico e entregas continuam sujeitas às decisões humanas registradas; uma revisão do plano não aprova automaticamente essas alterações.

**Próximo gate de liberação material:** conferência humana dos inventários/trechos efetivamente usados e aprovação da entrega correspondente. A integração técnica autorizada é acompanhada na PR #5, com merge condicionado à CI do HEAD final. A validação local e a CI identificada estão concluídas e não devem ser refeitas sem mudança ou falha nova. P01/P02 já foram conferidos estruturalmente pelo titular; não reabrir essa pendência. A integração não ativa regras. Classificação automática se absteve nos dois processos novos; o uso continua assistido. O diagnóstico ORG-03 não declara o ORG-R10-PRIVADO integralmente legível.

## 10. Evolução analítica aprovada — execução por etapa

**Contrato e plano aprovados pelo titular em 22/10/2026; somente EV-01 autorizada.** O pedido inicial foi documental; a instrução posterior “Aprovo o contrato e o plano. Prossiga com a EV-01” autoriza o contrato executável, validador/renderização, exemplos e testes dessa etapa. Objetivo preservado: análise por questão com posições, provas, fundamentos, conclusões preliminares e limites, automatizando verificações técnicas e destacando decisões jurídicas importantes. A EV-01, isoladamente, não gera essa análise nem demonstra profundidade jurídica.

- [Desenho analise-1 aprovado](superpowers/specs/2026-10-22-analise-estruturada-design.md) e [contrato executável EV-01](contratos/analise-v1.md): schema aditivo, snapshots, cobertura, atribuição, pesquisa, resultados técnicos e decisões profissionais; não modifica peças v1 ou estados legados.
- [Decomposição técnica e piloto](superpowers/plans/2026-10-22-evolucao-analise-estruturada.md): **EV-01 concluída e validada localmente**, sem commit/push. Contrato/schema aditivos, APIs puras de validação/renderização, dois exemplos sintéticos positivos/cinco contraexemplos; 117 aprovações focadas (76 EV-01/41 ORG-04) e **1095 aprovados/5 ignorados na integral offline**, zero falhas/erros em 632,45 s. Código/testes/schema congelados por hash; oito skills PRONTA, ambiente sem conflitos, revisão independente reconferida após correções. EV-02 corpus/protocolo; EV-03 automação técnica; EV-04 fluxo agêntico; EV-05 comparação; EV-06 integração permanecem **não iniciadas, sem autorização de execução**. Este é o registro canônico de andamento.
- Próxima etapa prevista, ainda não iniciada: EV-02, corpus/protocolo. A/B/C mantêm o mesmo modelo na comparação principal; P01/P02 são desenvolvimento/regressão, com processos novos reservados à avaliação. Metas são critérios de projeto aprovados para o desenho, a congelar com o protocolo antes do holdout, não resultados ou garantias. Modelo, revisor do benchmark, insumos e tetos ainda precisam ser definidos.
- Novas dependências, modelos/APIs, persistência, dados transmitidos, orçamento e execução das demais etapas precisam de decisões próprias. Sem adoção de LangGraph/SDK/Docling, mudança dos gates da fase 5, aprovação material, ativação de regras, commit ou push.

A evolução não substitui os gates anteriores nem altera suas evidências. Aprovar o contrato não aprova os casos concretos ou as 19 regras, que continuam inativas. Registro, resultados e preservação: EV-P01/EV-01 em [coordenação](COORDENACAO.md).
