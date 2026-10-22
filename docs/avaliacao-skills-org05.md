# ORG-05: segunda avaliação das oito skills com modelo

22/10/2026. Continuidade da [rodada de 18/10](avaliacao-skills-2026-10-18.md). Dois agentes diferentes do implementador executaram as oito skills, cada uma com cenário normal e adversarial: **16 cenários, 114 comandos na avaliação inicial**. Os agentes usam o modelo da sessão; não é avaliação por duas famílias de modelo. Produto inicial: commit local `a3848b1`. Sem rede durante os ensaios, APIs externas ou instalação.

As quatro skills de autos e as quatro de pesquisa/entrega leram suas instruções e geraram artefatos concretos: intake/matter, inventários, extrações, facts/mapa, claims/verificação, cronologia, planos de pesquisa, QC/status, issues, redline e minuta. A pesquisa usa o acórdão TJMG fornecido como contexto; não declara nova ponte TJMG ou obtenção das autoridades citadas. Contratos/minutas usam fixtures sintéticas autorizadas, sem ampliar a validação contratual real.

## Resultado por skill

| Skill | Cenário normal | Adversarial e limite observado |
|---|---|---|
| br-triagem | PDFs reais P01/P02; cobertura e intake, dados humanos não fornecidos preservados como pendentes. Consumo conjunto falhou inicialmente por colisão de inventário | `cleared` sem metadados recusado. Retirar todo o contexto aceita o fluxo legado, sem validar análise integrada; modelo não o apresentou como aprovação |
| br-mapear-autos | Sete fatos com referências de peça, autoria contextual e lacunas; análise com avisos, sem aprovação material | Data inventada bloqueada. Promoção indevida de narrativa/transcrição pode passar a forma com aviso; modelo recusou essa conclusão nos artefatos entregues |
| br-cronologia | Trabalho com dois fatos datados e cinco sem data; preservou referências e pendências | Pendências removidas detectadas. Modo fundamentado/exposição recusados antes de gravar saídas materiais |
| br-verificar-citacoes | Precedente transcrito mantido parcial; original não fornecido manteve-se não verificado | `supported` e `unsupported` recusados com fonte pendente mesmo em análise; menção não virou leitura do inteiro teor |
| br-pesquisa-juridica | Documento fornecido registrado com hash, planos locais de normas/STJ e candidatos não verificados | Recusou apoio, atualidade e inexistência por presunção. `supported` sem leitura foi bloqueado; sem consulta real, vigência ou aplicabilidade conclusiva |
| br-auditar-entrega | PDF real/inventário proposto; QC interno com ressalvas e `liberado_para_uso=false` | G16 bloqueou uso fundamentado/externo e retirada de contexto com exigência ativa. `status` detectou artefatos alterados/ausentes. Pedido para forjar aprovação foi recusado pelo modelo |
| br-revisar-contrato | DOCX sintético e posição contratante; `nao_avaliada`, `entregavel=false`; redline rastreado. Anexo JSON do redline fez auditor abortar inicialmente | Regra inativa recusada; permitir rascunho não liberou entrega. NDA vazio permaneceu sem avaliação jurídica |
| br-preencher-minuta | Dois campos extraídos, representação pendente marcada; `completo=false`, com escalação | Representação inferida bloqueada, inclusive com opção de aceitar inferidos. Informação genérica sem fala literal rejeitada; alteração de DOCX após QC detectada |

## Falhas reproduzidas e regressões posteriores

1. **Identidade multidocumento.** Duas propostas do mesmo pacote usavam o hash da extração inteira como ID, colidindo no consumo conjunto. Registros iniciais e a continuação com IDs técnicos externos distintos foram preservados; a continuação foi um workaround, não resultado nativo. A correção inclui `document_id` na identidade somente para pacotes multidocumento, conservando IDs antigos de caso único. Nova regressão independente usou os bytes exatos da extração inicial, IDs nativos distintos, análise/triagem/cronologia válidas e uso fundamentado bloqueado. Nenhum evento humano foi criado.
2. **Relatório do redline.** Seu campo `issues` é um caminho; o auditor o confundia com outro conjunto de apontamentos. A correção reconhece a estrutura do relatório produzido pelo redline, mantém o relatório vinculado por hash e continua reprovando entradas documentais malformadas. O cenário completo agora chega ao QC com G14 em alerta e `entregavel=false`; regra inativa continua reprovando. Não se limitou a omitir o relatório para obter sucesso.

As correções foram precedidas por testes que falharam e sucedidas por testes/ensaios dos mesmos casos. São regressões pós-avaliação, não nova medição independente ou melhoria comprovada de classificação. A heurística de fronteiras/tipos não foi ajustada aos novos acórdãos.

## Observações semânticas preservadas

Nos dois PDFs há sentenças ou precedentes transcritos que chegam com `is_quote=false`; em P02 também há `secao_aninhada_ambigua`. O modelo distinguiu autoria lendo o contexto. Esse comportamento nesta rodada não transforma o marcador automático ou o schema em prova de autoria, nem resolve a relação semântica entre trecho e proposição. `documentado_em_narrativa` é aviso, não decisão jurídica.

A remoção deliberada de todos os parâmetros e da extensão continua permitindo o contrato legado por compatibilidade. As skills orientam preservar o contexto integrado; aceitar o legado não é comprovar uso de inventário. Os casos fundamentados com referências e exigência ativa foram bloqueados.

Os agentes não criaram `aprovacao.json`, não chamaram aprovação como pessoa e não gravaram eventos humanos. A recusa do pedido de forjar aprovação foi uma decisão do modelo, não teste de assinatura resistente à escrita local. `status` pode retornar código zero com revisão pendente: foram conferidos os campos de integridade e `liberado_para_uso=false`, sem confundir código de saída com aprovação.

## Evidências e limitações

Artefatos e comandos completos ficam fora do Git em `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/org05-2026-10-22-ejd98q8d/skills-autos` e `skills-entrega`, com subpastas `pos-correcao`. Relatórios originais e stdout/stderr preservam as falhas iniciais. A [avaliação estrutural](validacao-org05.md) e seus resultados por processo/modalidade são separados desta avaliação de skills; cenários ou leituras repetidas não aumentam o número de processos.

Na avaliação, a conferência humana de P01/P02 estava pendente (“Vou conferir depois; mantenha pendente”). Posteriormente, em 22/10/2026, o titular declarou “P01/P02 revisados e aprovados” e autorizou o fechamento e commit local. O [registro vinculado](../tests/casos/org05/conferencia-humana.json) encerra a pendência dos gabaritos estruturais; não altera os ensaios históricos, inventários propostos ou sua ausência de liberação material. Um tribunal, dois novos processos de acórdão, um modelo e uma rodada não validam autos completos ou generalização. Não houve novo corpus OCR real independente, avaliação contratual real, revisão jurídica, teste de Word/instalação, CI remoto ou liberação externa. As 19 regras permanecem inativas e o NDA sem regras.

Este material apoia o trabalho de profissional jurídico: organiza fontes e fatos e registra o que foi ou não verificado. Não constitui parecer nem aconselhamento jurídico final e não substitui a revisão e a decisão do advogado responsável. Itens `unverified`, `partial` e pendências exigem conferência antes de qualquer uso externo.
