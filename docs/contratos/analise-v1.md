# Análise estruturada — contrato analise-1 (EV-01)

Contrato aditivo aprovado pelo titular em 22/10/2026. Especificação de desenho: [analise-1](../superpowers/specs/2026-10-22-analise-estruturada-design.md). [Schema Draft 2020-12](analise-v1.schema.json). Prioridades/andamento e resultados de verificação somente no [plano principal](../plano-principal.md) e na coordenação.

Esta etapa valida e apresenta uma análise já produzida. **Não gera análise jurídica, não pesquisa, não escolhe tese nem aprova entrega.** Profundidade, cobertura material e redução do trabalho profissional serão avaliadas nas etapas seguintes. As oito skills, formatos e gates legados permanecem intactos; 19 regras inativas, NDA vazio.

## 1. Interfaces e obtenção dos insumos

```python
from analise_estruturada import validar_analise, renderizar_analise

resultado = validar_analise(analise, entradas)
if resultado["valido"]:
    markdown = renderizar_analise(analise)
```

- `validar_analise(obj: dict, entradas: dict[str, bytes]) -> dict`: `entradas` mapeia **artifact_id**, não caminho, para bytes exatos. Não modifica argumentos, cria arquivos, acessa rede ou abre caminhos declarados pelos documentos. O módulo lê somente seu schema empacotado na inicialização.
- `renderizar_analise(obj: dict) -> str`: exige estrutura válida; caso contrário, `ValueError`. Não recebe snapshots: **não verifica referências externas** e marca essa limitação no cabeçalho. O chamador deve validar primeiro; Markdown isolado não é prova de validação ou liberação.
- Saída de validação: `valido`, `erros`, `avisos`, `referencias_resolvidas` e `resultado_tecnico`. Erros/avisos têm `codigo`, `caminho`, `mensagem`; não reproduzem trechos ou valores confidenciais. `valido` significa contrato tecnicamente coerente, não correção jurídica.
- `resultado_tecnico` contém `integrity`, `review_readiness` e `restrictions`. Erro detectado implica `invalida`/`reprocessar`; fora disso, nunca promove integridade declarada como não verificada/inválida. Restrições calculadas são somadas às declaradas sem rebaixar `bloqueada`/`reprocessar` para `com_restricoes`. Estado conservador bloqueado pode coexistir com contrato válido.
- IDs resolvidos apenas demonstram que os objetos existem nos snapshots; não comprovam que seu conteúdo apoia juridicamente a conclusão.

O chamador escolhe e lê arquivos autorizados, sem seguir links que escapem da raiz. Esta API recebe somente bytes e **não resolve symlinks**, nem autentica sua origem física. Rejeita caminhos declarados absolutos, com drive/UNC/ADS, barras invertidas, controles, segmentos vazios, `.` ou `..`. Um caminho seguro no manifesto é metadado, não autorização de leitura. Conservar originais e gravar novos derivados/revisões separadamente cabe ao chamador.

## 2. Envelope e snapshots

O schema fixa os nomes, tipos, obrigatoriedade, enums e campos adicionais proibidos. Textos obrigatórios não podem conter somente espaços. IDs novos usam `[A-Za-z0-9_-]+`; SHA-256 usa 64 hexadecimais minúsculos. Instantes usam RFC3339 com fuso; `as_of` é data ISO válida.

| Campo | Regra adicional do validador |
|---|---|
| `schema_version` | Constante `analise-1`; separado de `schema_version: "1"` do legado |
| `analysis_id`, `matter_id` | ID da análise; ID do caso igual à única triagem fornecida |
| `revision`, `previous_sha256` | Revisão 1 sem anterior; revisão seguinte exige um snapshot `analise_anterior`, hash exato, mesma análise/caso e número +1. Preserva o anterior, sem conferir seu histórico externo recursivamente |
| `run_id`, `created_at`, `as_of`, `objective` | Execução identificada; data de referência e objetivo correspondem à triagem |
| `scope` | `type`: `acordao_isolado`/`conjunto_documental`; `document_ids`, `exclusions` com motivos e `limitations`. Cada documento das extrações é incluído ou excluído, sem sobreposição/IDs fictícios |
| `inputs[]` | `artifact_id`, `type`, `path`, `sha256`; IDs/caminhos sem duplicação. O conjunto de chaves de `entradas` deve ser exatamente o do manifesto |
| `execution_ref` | `input_id`, `path`, `sha256`; resolve insumo `execucao`, mesmo caminho/hash e `run_id` |
| `actors`, `references`, `overview`, `issues`, `requests`, `coverage` | Semântica nas seções seguintes |
| `research_tasks`, `findings`, `professional_decisions`, `technical_result` | Registros declarativos, não execução de agentes ou nova política de liberação |

Tipos de insumo: `matter`, `extracao`, `facts`, `claims`, `original`, `pecas`, `pecas_anterior`, `execucao`, `analise_anterior`, `fontes`, `qc`. Todos, exceto `original`, são objetos JSON UTF-8 estritos: chaves duplicadas, números não finitos e estrutura incompatível são recusados. Bytes/hash de todos são conferidos; `fontes` e `qc` são anexos, sem nova certificação de seu conteúdo.

Manifesto `execucao`: `run_id`, `code_version`, `prompt_version`, `model` (texto ou null), `configuration` (objeto), `tools` (lista de nomes). O caso sintético usa `model: null`, sem inferência. Chaves de credenciais conhecidas, inclusive aninhadas (`api_key`, `password`, `secret`, `access_token`, `authorization`, `cookie`, `credentials`), são recusadas sem imprimir valores. Isso não é detector exaustivo de segredos em texto livre; cabe ao produtor não incluí-los.

## 3. Referências, atores e compatibilidade com o legado

`references[]` contém exatamente `id`, `input_id`, `collection` (`facts`/`claims`), `item_id`. Coleção e tipo do insumo coincidem; o item existe uma única vez. `f001` de arquivos distintos usa namespace `input_id`, sem colisão silenciosa. `matter_id` declarado em facts/claims deve coincidir com o caso; sua ausência em contratos legados não autoriza inventá-lo. Documento explicitamente excluído do escopo não pode sustentar referências da análise. Fatos/proposições novos precisam primeiro existir no formato legado, em snapshots identificados.

São reutilizados os validadores de triagem/fatos/proposições e o contexto de uso de peças. O adaptador em memória monta esse contexto com `ContextoPecas` e `validar_inventario`; não usa o carregador de arquivos `carregar_contexto`, pois ele abriria caminhos. Inventário exige extração e original exatos, além de revisão anterior quando aplicável. Não cria evento nem conferência humana. `supported`/`unsupported` mantêm suas exigências materiais legadas; proposta de peça não libera conclusão jurídica.

`actors[]`: `id`, `label`, `role` e exatamente um entre `matter_input_id`/`reference_id`. O primeiro aponta à triagem, o segundo a uma referência. Isso confere ligação, não autentica identidade ou resolve autoria semântica. Usar identificação mínima suficiente.

Cada `Assertion` usa `id`, `text`, `nature`, `speaker`, `basis_refs`, `qualification`, `limitations`; inferência exige `justification`. Natureza: `relato_documental`, `posicao_processual`, `inferencia_analitica`, `limite`. Qualificação: `sustentada_no_escopo`, `parcial`, `inconclusiva`. Não substituem `facts.kind`/`claims.status`.

- Fala: `speaker.entity_ref` resolve ator ou é null com motivo; `mode`: `fala_propria`, `relato_terceiro`, `transcricao`, `nao_identificado`.
- Afirmação documental/posição/inferência exige referências existentes. Premissas de fato inferido precisam de referências explícitas; ciclos são recusados.
- `parcial`/`inconclusiva` exigem limitações; `limite` exige `missing_input`, sem base fictícia e sem qualificação plena.
- Claim `unverified`, `partial`, `unsupported` ou fato `lacuna`/`informado` não pode sustentar afirmação declarada plena, inclusive através de premissas indiretas. O estado é escolhido pela coleção (`facts.kind`, `claims.status`); campo extra no legado não o substitui. Isso preserva estados; não julga automaticamente a pertinência do texto.
- Trecho inteiramente transcrito não pode ser atribuído como fala própria; ambiguidade conhecida exige restrição. Marcadores podem estar errados: a EV-01 não corrige automaticamente autoria ou OCR.

## 4. Conteúdo analítico

`overview` tem cinco afirmações: `context`, `objective`, `posture`, `outcome`, `reach`.

`issues[]` informa pergunta, importância/motivo, estado, posições, evidências, fundamentos, avaliação sintética, conclusão preliminar, alternativas e ligações. `inconclusiva`/`nao_examinada` exigem `reason`/`next_action`. Listas vazias têm motivo em `empty_reasons`; alternativas vazias têm `alternatives_reason`. Não há campo para raciocínio interno do modelo.

`evidence[]` associa `reference_id`, papel (`favoravel`, `contraria`, `contextual`), origem (`primaria`, `relatada`) e limite. Alegação/inferência/lacuna/informação ou transcrição não pode ser promovida a prova primária. Essa trava é conservadora e não certifica a natureza de uma prova só porque passou.

`requests[]`: descrição, requerente, questões, resultado (`acolhido`, `rejeitado`, `parcial`, `nao_examinado`, `nao_localizado`), resposta e efeito. Descrição/resposta/efeito são afirmações. Pedido sem resposta gera restrição. Ligações questão ↔ pedido/pesquisa/decisão são recíprocas e identificadas.

## 5. Cobertura, pesquisa e achados

`coverage[]`: `input_id` da extração, documento/bloco, tratamento, motivo e `analysis_ids`. Intervalo opcional `start`/`end` usa offsets Unicode, fim exclusivo. Cobrir cada bloco do escopo sem lacuna/sobreposição; bloco vazio pode ter cobertura vazia explícita. Ligações de bloco utilizado apontam questões/pedidos/afirmações. Peça/seção opcionais precisam do inventário íntegro correspondente.

Tratamentos: `utilizado`, `contextual`, `excluido_com_motivo`, `ilegivel`, `nao_examinado`. Os três últimos exigem motivo; os dois de leitura insuficiente exigem restrição. Cobertura técnica não mede recuperação de fatos/questões materiais nem prova exame jurídico integral.

`research_tasks[]` registra questão, razão, termos, consultas (`query`/`outcome`), fontes candidatas, referências examinadas/claims, achados contrários, estado e parada. Referências precisam resolver; `claim_refs` aponta claims. Os estados `planejada`, `executada`, `limitada`, `dispensada` são dados, não prova de consulta. Não há executor de pesquisa nesta etapa.

`findings[]` registra código, categoria, alvos, extensão, impacto, evidências, ação, motivo e método/versionamento. Achado material/crítico não pode ter apenas ação `registrar`; falha de integridade material exige correção técnica. `reprocessar` precisa constar nos impeditivos e manter bloqueio. Outros tratamentos declarados não alteram os gates legados: a política automática geral é EV-03.

`professional_decisions[]` registra questão, motivo, duas ou mais opções, recomendação preliminar nullable, referências e consequência. A API verifica forma e ligações; não decide se a pergunta é juridicamente importante ou trivial. Essa utilidade depende de produção/avaliação futura.

## 6. Resultado e Markdown

`technical_result`: `integrity` (`valida`, `invalida`, `nao_verificada`), `review_readiness` (`apta`, `com_restricoes`, `reprocessar`, `bloqueada`), `blocking_findings`, `restrictions`. Estado que omite restrição conhecida é recusado. Não existe campo de aprovação profissional automática; campos adicionais são inválidos.

Markdown apresenta: síntese/alcance → questões → pedidos/resultado → provas/fundamentos → limitações/pesquisa → decisões profissionais → fontes/cobertura em apêndice. Inclui IDs, qualificações, restrições, alternativas, justificativas e proveniência. Escapa conteúdo de documento para não introduzir HTML/imagens/links Markdown ativos. Alertas materiais ficam no corpo e informativos no apêndice. O cabeçalho distingue estado **declarado**, fontes não verificadas pelo renderizador e ausência de liberação externa.

## 7. Exemplos e validação

[Fixtures sintéticas](../../tests/casos/analise_contrato/exemplos.json): POS-01, análise delimitada do ato; POS-02, prova primária ausente com restrição. Cinco contraexemplos identificados e ligados aos testes: hash incompatível, fonte secundária promovida, autoria ambígua, cobertura insuficiente com falsa aptidão e documento/base inventados. Não são P01/P02, autoridades reais ou eventos humanos.

Teste focado: `python -m pytest -q tests/test_analise_estruturada.py`. Compatibilidade: suíte integral offline com `JURIS_REDE=0`, ambiente próprio do Codex. Resultados efetivamente executados são registrados na coordenação/plano, sem confundir comando documentado com teste passado.

Limites preservados: hash não comprova fidelidade ao original, schema não mede profundidade/completude, estados não autenticam humanos, função de renderização não verifica fontes e aprovação do contrato não é aprovação jurídica do caso. Não houve nova API, dependência, integração, migração ou ativação de regra na EV-01.
