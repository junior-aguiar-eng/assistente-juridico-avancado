# Comparação com os repositórios de referência (17/10/2026)

Método: os arquivos mapeados no blueprint foram lidos nos **commits fixados** (todos existem; os caminhos conferem), e comparados com o que o pacote tem. Antes desta comparação, nada tinha sido lido por mim: o pacote incorporava só as ideias descritas no blueprint. Nenhum arquivo foi copiado. Licenças: ver `THIRD_PARTY_NOTICES.md`.

## O que o pacote já fazia de acordo com a referência

| Referência | Item confirmado na leitura |
|---|---|
| LegalQuants `ACCESS-MODES` | identificar o acesso real da sessão; preferir fonte oficial; registrar tipo, URL, data e localizador; sem fonte, só fila de verificação; parar e pedir ao usuário |
| LegalQuants `proposition-checking` | separar proposição de citação; existência, acerto e aplicabilidade são coisas distintas; `unverified` não é conclusão de mérito |
| Anthropic `chronology` | uma entrada por evento, conflitos entre documentos mantidos com marca, "não inventar eventos", lacunas explícitas, build incremental com diferenças |
| Anthropic `matter-intake` | intake uniforme (papel, jurisdição, datas), nunca supor a posição do cliente |
| Lex `GUIA-ANTI-ALUCINACAO` | lista do que nunca fazer (inventar número, relator, data; súmula sem número) |
| Chen `output-templates` | inventário com status por arquivo, pendências de OCR visíveis, localizador por arquivo e página |

## O que a leitura mostrou que faltava, e o que foi feito

Legenda: **feito** (nesta rodada), **Fase 4** (depende de skills ainda não escritas), **não adotado** (com motivo).

| Origem | Achado | Decisão |
|---|---|---|
| ACCESS-MODES | regra explícita "memória do modelo proibida"; distinção `live_source` / `user_supplied_source` | **feito**: garantia 5 e campo `obtained_via` |
| proposition-checking | `contradicted` separado de `unsupported`; `quote-inaccurate`; aplicabilidade; `suggested_fix`; mapa de dependência entre argumentos; escalação; faixas de confiança | **feito**: `source_relation`, `applicability`, `suggested_fix`, `depends_on`, `escalacao.md`; faixas de confiança no gate final |
| adversarial-qc | faixa do certificado (alta, mista, não entregar); entrega para cliente ou petição nunca fica em "alta"; assinante humano obrigatório; profundidade rápida/padrão/profunda; reverificação de fontes; trilha de QC é documento sensível | **feito**: `faixa`, `tipo_entrega`, `--reverificar`; profundidades descritas na skill. Dois agentes independentes: descritos como opção, não testados |
| adversarial-qc checklist | 17 itens (números, consistência, atribuição, metodologia da fonte, atualidade, hedging, teste do destinatário, escopo) | **feito**: checklist ampliado em `br-auditar-entrega` |
| skills-qa | 13 parâmetros, 3 falhas jurídicas, varredura de injeção, atualidade (`last_verified`), faixas de veredito | **feito**: `governance/skill-review-checklist.md`, `scripts/revisar_skill.py`, campos de versão e atualidade |
| matter-intake | gate de conflitos com status (`cleared`, `pending`, `not-run`, `waived`) e bypass registrado | **feito**: bloco `conflicts` no `matter.json` e gate no `auditar.py`. O pacote registra, não executa a checagem |
| chronology | marca de relevância por tese (🔴🟡⚪), disciplina "se tudo é vermelho nada é", variante para exposição de fatos, variante por testemunha, gate de privilégio com `priv: ok|flag|review`, tag `[user provided]` para fato sem documento, "nenhum suprimento silencioso" | **feito**: `relevancia`, `priv`, `informado`, `--formato fatos`, privilégio no `matter.json`. **Não adotado**: variante por testemunha (exige campo de participantes) e significância 🔴🟡⚪ em emoji |
| chronology | restrições ao uso de documentos obtidos em disclosure | **feito** na forma brasileira: `segredo_de_justica` no `matter.json` (CPC, art. 189, conferido) |
| FIRAC-JB | método de cinco etapas e checklist do CPC, art. 489, § 1º | **feito**: `references/analysis-method.md` na pesquisa e remissões; texto do dispositivo conferido no Planalto |
| peticao-analyzer | CAPPD (causas, argumentos, pedidos, provas, defesas), quadro de pontos controvertidos, fato não impugnado (CPC, art. 341) | **feito**: `references/pecas-cappd.md` na skill de mapear autos; art. 341 conferido |
| Anti-alucinação | níveis CONFIRMADO/PROVÁVEL/INCERTO baseados em memória | **não adotado**: contradiz a garantia 5. Aproveitado: portais para o usuário conferir à mão |
| Chen `output-templates` | `PARTIES.md`, `PRIVACY_FLAGS.md` com valores mascarados, glossário | **feito**: `partes` no `matter.json` e `triagem.py privacidade` (CPF e CNPJ com dígito, cartão, e-mail, telefone). **Não adotado**: glossário multilíngue |
| Chen `extract.py` | manipuladores de e-mail (`.eml`), planilha, HTML, imagem, áudio, vídeo; `preflight` de ferramentas | **feito**: `.eml` e `triagem.py capacidades`. **Não adotado** por ora: áudio, vídeo, imagem com OCR, planilha |
| code-lawyer `48-qc-gate` | sete verificações de saída, rótulo único de fonte por proposição, bloqueio quando nada foi verificado, **rodapé de aviso obrigatório**, no máximo 2 rodadas por verificação com declaração visível | **feito**: gate de aviso nos relatórios, regra das 2 rodadas, bloqueio sem extração (já existia) |
| code-lawyer `pack-template` | pacote por jurisdição (`_pack.md`, tabela de domínios, fontes recomendadas, metadados) | **feito (mecânico)**: `rules/br/*.json`, todas inativas até revisor jurídico |
| code-lawyer `06-output-and-severity` | duplo eixo de risco (jurídico e comercial), cartão de problema com texto completo da cláusula, "sinalize em excesso", comentário curto copiável | **feito**: `contrato.py validar-issues` (dois eixos, cláusula inteira) |
| code-lawyer `20-slot-and-fill` | cinco estados de preenchimento mais `pending_drafting`; `extracted` exige valor literal no trecho | **feito**: seis estados em `preencher.py` |
| evolsb `skill.md` | pré-checagem do contrato (campos em branco, anexos ausentes, assinatura, páginas), posição da parte, tabela de termos, sinais de alerta, cláusulas ausentes, inconsistências internas | **feito** em `contrato.py precheck`; sem os parâmetros de mercado dos EUA |

## O que continua fora

Áudio, vídeo e OCR; glossário multilíngue; pacote por jurisdição, duplo eixo de risco, preenchimento de modelo e revisão de contrato (Fase 4); dois agentes independentes testados; avaliação das skills com modelo.
