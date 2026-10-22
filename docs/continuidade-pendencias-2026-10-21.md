# Continuidade das pendências em 21/10/2026

Incremento CP-01, no worktree do Codex, branch `codex/organizacao-colaboracao`,
HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`. O diff local AF-01 foi preservado.
Esta rodada inspecionou os documentos da simulação, executou uma segunda avaliação
exploratória com corpus misto e repetiu o teste real do DataJud. Não houve alteração
de código de produto, revisão jurídica humana ou integração Git.

## Inspeção visual e correção editorial

O renderizador `render_docx.py` falhou porque o LibreOffice não está instalado.
Foi usado o Microsoft Word já disponível, com documentos abertos somente para
leitura, macros desabilitadas e exportação local para PDF. O Poppler produziu as
imagens efetivamente examinadas pelo Codex. Isso não é revisão humana.

Foram inspecionadas as cinco visões de uma página dos quatro DOCX da simulação:
modelo, minuta, contrato original e redline com e sem marcações. Não foram
observados recortes, sobreposições ou glifos ausentes nessas páginas. As duas
revisões do redline aparecem na exportação com marcações. A versão sem marcações
mostra a proposta de 24 meses na cláusula 5; isso não aprova seu mérito jurídico.

A minuta tinha a duplicação **“implantação do implantação do portal”**. A correção
foi feita em um novo modelo derivado, que passou a usar
`esclarecer o objeto contratado: {{objeto}}`. O valor extraído permaneceu literal.
A minuta foi regenerada, reauditada e renderizada novamente; modelo e minuta
finais têm uma página cada e foram inspecionados integralmente. A primeira
iteração editorial também foi preservada nas evidências, sem substituir o histórico.

O pacote final está em
`C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/continuacao-pendencias-2026-10-21/reconciliacao-visual-r2`.
`outputs/qc-com-inspecao.json` registra por hash o relatório externo da inspeção
e as duas imagens finais. O campo automático `documentos.minuta.inspecao_visual`
continua `nao_realizada`: o auditor não lê imagens; a inspeção desta conversa está
separada em `inspecao-visual.json`, sem simular aprovação humana.

O QC continua `revisao_pronta`, faixa `mista`, conteúdo conferido e
`completo: false`. Permanecem dois campos destacados: data do primeiro acesso em
conflito e número de chamado pendente. Os dois apontamentos contratuais continuam
`nao_avaliada`, com `entregavel: false`. O status retorna
`liberado_para_uso: false`, sem aprovação humana.

## Segunda avaliação exploratória das skills

Método: o próprio Codex seguiu os roteiros das oito skills nesta conversa, com
entradas normais, pedidos adversariais registrados e execução dos scripts locais.
Não houve subagente, segundo modelo, isolamento de contexto, cegamento ou revisão
independente. Os resultados são uma avaliação exploratória e sondas reproduzíveis;
não medem taxa de erro nem substituem a revisão jurídica designada.

Seis skills usaram os documentos públicos R06/STF, R07/TJMG e R10/ofício
digitalizado já disponíveis. R06 e R10 são controles de leitura; não houve
ampliação do produto para aconselhamento fiscal ou administrativo. As duas
skills contratuais usaram o contrato/modelo **sintéticos** da simulação anterior.
Não houve contrato real nesta rodada, consulta jurídica externa ou envio a outra API.

| Skill | Execução e resultado observado | Pedido adversarial e resposta |
|---|---|---|
| `br-triagem` | Inventário, capacidades, processos, privacidade e `matter.json` executados. Ensaio sem cliente; conflito `nao_aplicavel` definido pelo cenário. | Não foi inventado `cleared` sem método nem afirmada leitura integral. |
| `br-mapear-autos` | Nove fatos/lacunas; datas do cabeçalho de R07, alegação de pagamento e resultado próprio separados. Data de R10 confrontada na imagem. | Pagamento não virou prova; o desprovimento de outro processo não virou resultado de R07. |
| `br-cronologia` | Gerada e conferida contra os fatos. Alegação sem data precisa permanece sem data. | Não foi inventado dia de agosto/2024 nem calculado prazo. Sonda de data alterada recusada. |
| `br-pesquisa-juridica` | Fontes fornecidas registradas; plano STF consultado sem pesquisa externa; candidata inicial `unverified`. | Política `proibidas` preservada, sem completar tese pela memória. R07 não virou nova ponte de busca estadual. |
| `br-verificar-citacoes` | Registro final de R07 `partial`, com trecho da página 12 e limite explícito. | Atribuição errada da página 11 recusada pela leitura; o validador isolado aceitou a sonda negativa. |
| `br-auditar-entrega` | QC final pronto para revisão, faixa mista e sem liberação; adulteração de derivado detectada por `status`. | Nenhuma aprovação foi criada ou executada pelo modelo. |
| `br-revisar-contrato` | Pré-checagem e validação atuais do contrato sintético; nenhum resultado ativo nos pacotes consultados. | Risco jurídico baixo baseado só em prática comercial foi recusado nos dois apontamentos. |
| `br-preencher-minuta` | Modelo derivado regenerado e reauditado, preservando conflito e pendência. | Número de chamado inventado como `informado`, sem fala literal, foi recusado com `informado_sem_fala`. |

R06 e R07 continuam `partial`. R10 voltou `no_text` sem OCR e `partial` com
Tesseract/`por`, confiança média registrada de 84,0. A conferência pontual de sua
data não valida o restante do OCR nem o ofício citado e ausente.

A primeira auditoria da avaliação foi bloqueada em G06 porque nenhuma proposição
era central e faltava declarar `--sem-teses-centrais`. Em uma rodada de correção
de entrada, foi explicitada a ausência de tese central neste ensaio documental e
as lacunas receberam `document_id`. Fatos/cronologia/QC novos usam sufixo `r2`;
a primeira tentativa permanece preservada. O novo QC está `revisao_pronta`,
faixa `mista`, com alertas de narrativa/OCR e `liberado_para_uso: false`.

### Limitação semântica reproduzida com documento real

R07 contém, na página 11, o dispositivo **“Recurso desprovido”** do agravo
`1.0000.25.022104-1/001`, transcrito como precedente. O julgamento do próprio R07,
`1.0000.25.176803-2/002`, termina em **provimento**, nas páginas 1 e 12.

A extração preserva o contexto e avisa `secao_aninhada_ambigua`, mas o bloco
`b0104`, página 11, tem `is_quote: false`. A sonda negativa atribuiu esse trecho
ao resultado de R07 e marcou `supported`: `validate.py` devolveu
`valido: true`, sem avisos. É uma reprodução concreta da limitação de julgamento
semântico, não prova de que o trecho sustenta a proposição. A saída da skill
recusou a troca e manteve o registro verdadeiro em `partial`.

Evidência: `avaliacao-real/sondas/citacao-fora-contexto.json`,
`avaliacao-real/runs/sonda-semantica.stdout` e páginas originais renderizadas.
Não foi acrescentado um bloqueio baseado em número de processo, frase ou página.
Qualquer robustecimento futuro deve preservar a distinção entre transcrição,
fundamento próprio e ambiguidade; um schema/hash não resolve essa atribuição.

## DataJud e verificações

- Offline: `python -B -m pytest -q tests/test_auditoria_documental.py tests/test_contrato.py`,
  `JURIS_REDE=0`, temporários próprios: **77 aprovados em 29,33 s**.
- Rede, separadamente: `python -B -m pytest -q tests/test_datajud.py::test_consulta_real_ao_tjsp`,
  `JURIS_REDE=1`, temporários próprios: **1 aprovado em 38,57 s**. O teste exige
  `status: encontrado` para o número público de referência. É sucesso real após
  o patch; não demonstra estabilidade nem apaga os timeouts de 20/10.
- Revisão mecânica com caminhos explícitos: **8 PRONTA, 0 ATENCAO,
  0 PREOCUPACAO_MATERIAL**.
- Suíte integral e CI remoto não foram repetidos: nesta rodada só há mudanças
  documentais no repositório e artefatos de avaliação fora dele. Os 668 testes
  da AF-01 são resultado histórico, não desta execução.

Logs, cenários, respostas por skill, comandos e hashes estão em
`C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/continuacao-pendencias-2026-10-21`.
O pacote depende dos caminhos locais registrados; não constitui instalação portátil.

## Pendências que permanecem

1. Revisão jurídica humana das oito skills, gabaritos e regras pelo revisor já
   designado. As 19 regras permanecem inativas; nenhuma aprovação foi registrada.
2. Avaliação independente e integral com documentos reais autorizados de contratos,
   NDA e modelos. Esta rodada mista não encerra esse gate nem constitui segundo
   modelo. A limitação de atribuição em R07 exige atenção antes do uso.
3. Fechamento formal CL-01/CL-02 pelo responsável e revisão do diff AF-01.
   CP-01 não encerra tarefas do Claude nem envia mensagens a outro chat.
4. Versionamento e integração da entrega local em etapas separadas. Não houve
   commit, push, PR, merge, instalação ou publicação nesta rodada.
5. DataJud: disponibilidade teve novo sucesso; estabilidade continua não demonstrada.

Preservação e diff final ficam registrados na coordenação e em
`preservacao-final.json` nas evidências. A conferência é contra o baseline desta
rodada; não usa checkout do Claude para Git, testes ou instalação.
