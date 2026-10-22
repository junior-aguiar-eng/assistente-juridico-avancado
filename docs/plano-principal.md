# Plano principal: juris-skills-br

Revisão 8 — 2026-10-22. **Este é o plano vigente e a fonte única de prioridades e andamento.** Substitui o [planejamento v2](planejamento-juris-skills-br-v2.md), preservado como histórico. Pesquisa, especificações e relatórios detalham decisões; não mantêm cronogramas ou listas de execução concorrentes.

**Objetivo:** manter as oito skills e o fluxo atual de evidências, acrescentando organização verificável de peças antes de liberar análise assistida de autos completos.

**Arquitetura:** conservar extração, validação, auditoria e formatos existentes. Acrescentar um inventário de peças que referencie a extração, distinguindo arquivo, peça, seção e bloco. Melhorias de OCR e eventual adaptador de extração têm avaliação própria e convergem para esse fluxo.

**Tecnologias:** Python >=3.12, ferramentas e dependências atuais. Docling Parse/Core foram avaliados em piloto local limitado e permanecem experimentais; não foram adotados como extrator padrão. O pipeline completo Docling não foi avaliado. VICTOR é referência metodológica, sem autorização presumida para copiar código, dados ou pesos.

**Especificação da nova etapa:** [inventário de peças](especificacao-inventario-pecas.md). Evidências: [pesquisa de referências](pesquisa-segmentacao-autos-2026-10-22.md) e [corpus privado](validacao-corpus-privado-2026-10-22.md).

## 1. Marco preservado

- Esta cópia concilia o snapshot Codex `abbf85a` com AF-01/CP-01/AC-01/GT-01 sem commit e os incrementos recuperados até `ff225a7`. Registro: [reconciliação RC-01](reconciliacao-org-2026-10-22.md).
- Oito skills existentes; as **19 regras de Código Civil/LGPD permanecem inativas**, conforme determinação do usuário nesta reconciliação. A ativação registrada na outra branch não foi aplicada. NDA permanece sem regras. Revisão jurídica, aprovação de entregas e validação técnica são etapas distintas.
- A base Codex registra 732 testes aprovados/3 ignorados na GT-01; as entregas ORG registram seus resultados históricos em Linux. RC-01 registra 943 aprovados/5 ignorados e 304 focados em ambiente limpo. **VT-01 repete a suíte completa no worktree Codex e no ambiente limpo: 943 aprovados/5 ignorados, sem falhas, em 859,31 s**; dois testes de rede, piloto opcional Docling e dois originais privados ausentes foram ignorados. Os 160 testes do snapshot intermediário também passaram; isso não constitui avaliação jurídica ou CI remoto.
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
| 2. Núcleo jurídico | Mapear, verificar citações e auditar | Entregue no escopo existente; integração com peças será incremental. |
| 3. Entorno | Triagem, cronologia e pesquisa | Entregue no escopo existente; não confundir inventário por arquivo com inventário de peças. |
| 4. Contratos e minuta | Pré-checagem, issues, redline e preenchimento | Parte mecânica entregue, com auditoria documental e avaliação jurídica pendente explícita; 19 regras inativas e NDA sem regras. |
| **4A. Organização dos autos** | Inventário de peças, fronteiras, seções internas, qualidade de leitura e integração | **ORG-01/02/03 recuperadas e conciliadas (contrato, validador, proposta assistida e diagnóstico OCR); integração e validação ampliada ainda pendentes. Obrigatória antes de encerrar a fase 5 no escopo de autos completos.** |
| 5. Liberação | Regressões, avaliação das skills, compatibilidade e limites publicados | Aberta; 12 casos executáveis não bastam como critério isolado de conclusão. |

OCR e DOCX/redline deixaram de ser itens futuros: já existem. A nova etapa aperfeiçoa e integra o que falta, sem apagar esse histórico.

## 4. Execução da fase 4A

IDs abaixo são estáveis. Dependências determinam a ordem; os detalhes de implementação de cada pacote serão escritos antes de executá-lo. Esta revisão não cria novos comandos nem altera o comportamento das skills.

| ID | Pacote e resultado verificável | Depende de | Critério de conclusão | Estado |
|---|---|---|---|---|
| ORG-01 | Contrato do inventário e gabarito inicial: arquivo, peça, seção, bloco; fronteiras; estados de conferência; exemplos anônimos | Marco preservado | [Contrato v1](contratos/pecas-v1.md), esquema estrutural e exemplos verificáveis; fronteira física do ORG-R07-PRIVADO conferida visualmente e confirmada pelo titular (1–24/25–38), sem promover âncora técnica a confirmação humana | Entregue; verificação final no [relatório ORG-01](entrega-org01-2026-10-22.md) |
| ORG-02 | Validador semântico do contrato, segmentação de referência e piloto comparativo: títulos espaçados, início/continuação, evidências de fronteira, revisão manual; comparar extração atual e candidato Docling | ORG-01 | Códigos de erro do contrato exercitados; casos adversariais, fusão/fragmentação, custo e licenças verificados; decisão de adotar ou rejeitar adaptador registrada com evidências | Entregue: [validação e piloto](piloto-org02-2026-10-22.md); 635 testes aprovados/3 ignorados na origem, resultado histórico; Docling Parse experimental, sem adoção no fluxo padrão |
| ORG-03 | Qualidade de OCR: diagnóstico do ORG-R10-PRIVADO, experimento local, comparação com transcrição conferida, preservação de originais e avisos | ORG-01 | Resultado e limitações reproduzíveis; expectativas textuais conferidas. Se continuar insuficiente, declarar trecho ilegível e manter bloqueio de uso material, sem forçar leitura | Entregue: [experimento OCR](experimento-org03-2026-10-22.md), seis amostras humanas; mediana/72 opcional, texto integral não conferido; 676 testes aprovados/3 ignorados na origem, resultado histórico |
| ORG-04 | Integração do inventário nas skills e nos gates, preservando fluxos anteriores | ORG-02; diagnóstico e decisão de uso do ORG-03 | Referências peça/bloco verificáveis; pendência material de fronteira, atribuição ou leitura aparece na entrega e impede aprovação técnica fundamentada daquele uso; testes legados preservados | Não iniciado |
| ORG-05 | Validação integrada e ampliação do corpus, separando resultados por processo e modalidade de leitura | ORG-04 | Gabaritos conferidos, avaliação com casos não usados no ajuste, métricas e falhas publicadas; segunda avaliação das skills realizada no escopo efetivamente disponível | Não iniciado |

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
| Testes | `tests/test_pecas*.py`, `tests/test_piloto_pecas.py`; futura integração e testes de extração/OCR/regressão existentes | Cenários de fronteiras e compatibilidade com fixtures anônimas; corpus privado opcional e explicitamente separado. |
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

- [ ] ORG-01 a ORG-05 concluídos com evidências e limitações registradas; escopo de liberação declarado como **assistido**, sem promessa de classificação universal automática.
- [ ] Fluxo completo liga arquivo → peça → seção/bloco → fato/proposição → auditoria, com conferência humana das fronteiras e tipos usados materialmente.
- [ ] Nenhuma fusão, atribuição errada ou leitura insuficiente conhecida é silenciosamente aceita como evidência conferida nos casos de aceitação.
- [ ] Suíte relevante e completa executada; passar, falhar, ignorar e não executar registrados separadamente. Corpus privado ausente não comprova sua validação.
- [ ] Avaliação das skills repetida com documentos reais; aprovação jurídica declarada não substitui essa avaliação nem a aprovação de entregas concretas.
- [ ] Compatibilidade com casos antigos demonstrada; migração explícita para novos artefatos, sem alteração dos originais.
- [ ] Licenças, modelos, custos e configuração reprodutível conferidos; documentação e avisos de terceiros atualizados somente para o que for efetivamente adotado.
- [ ] CI remota conferida quando houver autorização para publicar as mudanças. Enquanto permanecer a instrução de não fazer push, registrar essa verificação como pendente, sem simular sucesso remoto.

Testes podem passar verificando que uma falha é avisada; isso não converte a capacidade defeituosa em capacidade resolvida. A liberação deve distinguir uso que funciona, uso assistido e uso ainda recusado.

## 8. Pendências consolidadas após a reconciliação

O próximo incremento de implementação é **ORG-04**, seguido de **ORG-05**. O inventário possui contrato, validação e CLI próprios; ainda não é consumido pelos gates de `validate.py`/`auditar.py`, triagem e cronologia. Passar os testes desses módulos não demonstra a integração que falta. Nenhuma dessas duas tarefas é iniciada pelo versionamento local.

| Prioridade ou gate | Pendência confirmada | Evidência necessária para encerrar |
|---|---|---|
| Próxima implementação — ORG-04 | Integrar referências peça/bloco e restrições de leitura, fronteira e atribuição nos consumidores e nas skills | Fluxo integrado com testes positivos e negativos; pendência material impede aprovação técnica fundamentada daquele uso; interfaces legadas preservadas. |
| Depois de ORG-04 — ORG-05 | Validação integrada e ampliação do corpus; avaliação independente das skills | Casos não usados no ajuste, separação por processo/modalidade, gabaritos conferidos e métricas com denominadores. Rodada exploratória e testes sintéticos não encerram esse gate. |
| Insumos privados | Originais ORG-R07-PRIVADO e ORG-R10-PRIVADO ausentes nesta máquina | Recuperar arquivos autorizados fora do Git e conferir os hashes esperados antes de repetir o experimento. As fronteiras e seis amostras históricas não comprovam fidelidade integral. R07/TJMG e R10/Picos públicos continuam disponíveis e separados. |
| Revisão jurídica humana | Conferência das regras, gabaritos e entregas; 19 regras inativas e NDA vazio | Revisão identificada e decisão expressa para qualquer ativação futura. Testes, recuperação de aprovação de outra branch ou commit não autorizam ativação. |
| Validação contratual e encerramento pelo responsável | Contratos/NDA/modelos reais autorizados e fechamento formal de CL-01/CL-02 ainda não demonstrados | Avaliação documentada além dos controles sintéticos, revisão jurídica quando cabível e encerramento registrado pelo responsável. |
| Integração e fase 5 | Publicação da branch, PR/merge, CI das mudanças atuais e liberação do pacote pendentes | Autorizações próprias; CI da revisão publicada e critérios da seção 7. CIs históricos não validam estes commits; instalação/distribuição não foram verificadas nesta etapa. |
| Operação de rede | Estabilidade DataJud ainda não demonstrada | CP-01 registra sucesso real após o patch em 21/10, mas houve timeouts anteriores. Novas verificações de rede são separadas e opcionais; a suíte offline não demonstra estabilidade. |

As correções AF-01/AC-01/GT-01 e a recuperação/integração RC-01/IG-01 são entregas locais registradas, não novas pendências de implementação. Assinatura externa, prova semântica e revisão jurídica conservam os limites abaixo.

| Pendência | Tratamento no plano |
|---|---|
| Assinatura externa para aprovação resistente à escrita local | Decisão de arquitetura e custódia ainda aberta; manter limite do arquivo local explícito. Não misturar com o inventário. |
| Natureza da prova e relação semântica entre trecho e proposição | Inventário melhora atribuição, mas não prova o fato nem a tese. Continuam revisão jurídica e avaliação das skills; qualquer automação nova exige escopo próprio. |
| Hash de fonte sem arquivo disponível | Preservar limite de reverificação; não declarar conferência criptográfica sem acesso aos bytes. A reconciliação de c001/s2 e c005/s1 foi entregue em pacote externo novo; não recuperou a identidade dos bytes históricos nem o inteiro teor de c005, que permanece `partial`/ementa. Não reabrir a reconciliação já concluída nem promover esses limites a leitura integral. |
| Pacote NDA vazio | Frente de regras jurídicas, dependente de fontes e revisão próprias; não bloqueia o piloto de peças nem recebe regras improvisadas. |
| Novo corpus e gabaritos | ORG-05 solicita somente o que faltar para demonstrar o escopo; preservar privacidade e registrar ausência sem bloquear trabalho independente. |
| Docling Parse e troca de extrator | Piloto experimental, sem adoção como padrão. Uma eventual adoção exige decisão posterior sustentada por qualidade, recursos, licença e compatibilidade; não é pré-requisito presumido para ORG-04. |

## 9. Disciplina de engenharia

- Atualizar andamento e dependências **somente aqui**. Especificações explicam contratos; pesquisa registra evidência; relatórios registram execuções. Não criar um segundo roadmap.
- Cada pacote começa com plano executável proporcional, arquivos/interfaces definidos e testes de aceitação. Não implementar a fase inteira em uma mudança única.
- Aplicar teste que reproduz o problema antes da correção, revisão de código e verificações adequadas. Rodar pytest sequencialmente ou com diretórios `--basetemp` distintos.
- Commits pequenos, por entrega verificável; preservar alterações anteriores. Não criar worktree adicional automaticamente no ambiente de nuvem já isolado.
- Manter mudanças de documentação, piloto opcional e mudança do comportamento padrão distinguíveis. Nenhuma nova dependência/modelo entra só para preencher a arquitetura proposta.
- Registrar adoção/rejeição de tecnologia com evidências no relatório do piloto e resumir a decisão aqui. Sem licença clara, não copiar código/dados/pesos de terceiros.
- Alterações de regras, escopo jurídico e entregas continuam sujeitas às decisões humanas registradas; uma revisão do plano não aprova automaticamente essas alterações.

**Próxima entrega:** ORG-04, integrar referências ao inventário e restrições por uso nos consumidores/skills, preservando compatibilidade. OCR parcial ou pendência material deve permanecer visível e impedir a aprovação técnica fundamentada daquele uso. O diagnóstico ORG-03 permite avançar com leitura parcial explicitamente recusada; não declara o ORG-R10-PRIVADO integralmente legível.
