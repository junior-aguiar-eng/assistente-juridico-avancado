---
name: br-revisar-contrato
description: Revisa um contrato brasileiro (NDA ou prestação de serviços/SaaS) na posição de uma das partes. Faz a pré-checagem do texto (campos em branco, anexos ausentes, remissões quebradas, assinatura, marca de minuta), registra cada apontamento com a cláusula inteira, o localizador, severidade jurídica e negocial separadas e a base, e gera uma cópia em DOCX com as alterações propostas como controle de alterações. Use quando o usuário pedir "revisar este contrato", "analisar as cláusulas", "o que devo negociar neste NDA" ou "redline do contrato". Não use para redigir contrato do zero, preencher modelo com dados (br-preencher-minuta) nem para conferir citações de uma peça.
version: 0.1.0
last_reviewed: 2026-10-17
owner: "José Bonifácio de Aguiar Santos Júnior (revisor jurídico designado em 2026-10-18; revisão ainda não realizada); mantenedor técnico: pendente"
---

# Revisão de contrato

Regras comuns: [garantias](../../shared/garantias.md), [estados](../../shared/estados.md), [formatos](../../shared/dados.md), [falhas jurídicas](../../shared/falhas-juridicas.md), [escalação](../../shared/escalacao.md).

**Estado desta skill: rascunho.** Das regras de revisão (`rules/br`), **20 foram ativadas pelo revisor jurídico em 30/10/2026** (8 do Código Civil, as 10 da LGPD e as 2 de NDA) e sustentam apontamento, como alerta a verificar, nunca como conclusão automática de infração ou crime; só a `civ-598` segue **inativa e sem revisor**. Enquanto o revisor não ativar a `civ-598`, a skill faz a pré-checagem e o redline mecânico, e qualquer apontamento sustentado só por regra de rascunho sai marcado `RASCUNHO_NAO_REVISADO` e **não pode ser entregue como conclusão**.

## Público e natureza do trabalho

Para o advogado que revisa contrato para uma das partes. A skill organiza e aponta; **quem decide o que é risco, o que negociar e o que aceitar é o advogado**. Nada aqui é parecer.

## Entrada e saída

- **Entrada:** o contrato (DOCX de preferência; PDF e TXT servem para leitura, não para redline) e o `matter.json` com a **posição da parte** (`client_role`): a gravidade de uma cláusula depende de quem a revisa.
- **Saída:** `outputs/precheck.json`, `outputs/issues.json` validado e, se pedido, `outputs/contrato-redline.docx` com alterações rastreadas. O original nunca é alterado.

## Roteiro

1. **Posição da parte.** Sem `client_role` em `matter.json`, pare e pergunte: contratante ou contratada, divulgadora ou receptora. Não assuma.
2. **Extraia** (`python scripts/extract.py contrato.docx --saida derived/extracao.json`). Se o status não for `ok`, diga o que faltou (coluna, tabela, imagem, alteração rastreada) antes de seguir.
3. **Pré-checagem:** `python scripts/contrato.py precheck derived/extracao.json > outputs/precheck.json`. Apresente os achados com localizador. São sinais do texto, não conclusões: campo em branco pode ser intencional; anexo "ausente" pode estar em outro arquivo.
4. **Leia o contrato inteiro** e monte a tabela de termos (partes, objeto, preço, prazo, renovação, rescisão, multa, limitação de responsabilidade, confidencialidade, foro) citando o localizador de cada termo. Termo que não está no texto aparece como "não localizado", nunca como "não há".
5. **Regras.** `python scripts/regras.py listar --pacote servicos_saas` entrega só regra ativa e revisada; se o contrato trata dado pessoal, consulte também `--pacote lgpd` (arts. 7, 11, 18, 33, 37, 39, 41, 42, 46 e 48 da Lei 13.709, texto compilado lido em 2026-10-18). Com `--incluir-inativas`, as regras vêm marcadas como rascunho: use-as como **roteiro de perguntas**, citando o artigo literal, nunca como conclusão. NDA: `--pacote nda` traz só o art. 195, XI e XII, da Lei 9.279/1996 (texto compilado lido em 2026-10-29), como rascunho inativo; as pendências (a via civil nos arts. 207 e 209, prazo do sigilo e foro) ficam para o revisor e não viram regra por conta própria (a LGPD, quando houver dado pessoal, está no pacote `lgpd`); não improvise regra.
6. **Registre cada apontamento** em `issues.json` com: cláusula **inteira** (`clause_text`), `document_id` e `locator`, `severidade_juridica` e `severidade_negocial` **separadas**, descrição, base (`regra`, `fonte` lida ou `pratica_do_cliente` com nota) e eventual sugestão. Sem avaliação jurídica, use `nao_avaliada` e `motivo_nao_avaliada`; não atribua risco baixo por padrão. Só prática comercial não sustenta graduação jurídica (baixa a crítica); a severidade negocial continua baixa a alta. Parâmetro de mercado ou regra de outra jurisdição não é base.
7. **Valide:** `python scripts/contrato.py validar-issues outputs/issues.json --extracoes derived/extracao.json --regras rules/br --pacote servicos_saas,lgpd` (sem `--pacote`, só o primeiro é lido e regras do outro dão `regra_inexistente`). Base `fonte` exige `source_id`, `retrieved_at`, `locator` e `local_file` ou `url`. Corrija os erros na origem. `--permitir-rascunho` só para preparar a conversa com o revisor; o resultado fica marcado.
8. **Redline (opcional):** `python scripts/redline_docx.py contrato.docx edicoes.json outputs/contrato-redline.docx --issues outputs/issues.json > outputs/redline-relatorio.json`.
   Cada edição traz `issue_id` correspondente ao `id` do achado; `de` (substituir/excluir) ou `ancora` (inserir_apos) deve constar literalmente no `clause_text` desse achado. O relatório registra o vínculo por edição e o SHA-256 de `issues.json`; entregue-o junto com o DOCX.
   Vínculo ausente, desconhecido ou trecho fora da cláusula é recusado. Sem `--issues`, só há redline mecânico, sem rastreabilidade dos achados; `issue_id` sem arquivo também é recusado. Isso não substitui a validação do passo 7 nem aprova o texto sugerido.
   Edição ambígua, não localizada ou que atravessa hiperlink/tabulação é recusada e listada; **releia o texto resultante** (excluir uma cláusula pode deixar remissões truncadas, como "sanções previstas na  deste"); as demais são aplicadas como alteração rastreada para o advogado aceitar ou rejeitar no Word.
9. **Audite** com `br-auditar-entrega`, informando `--issues outputs/issues.json` (tipo `contrato`: entrega externa nunca sai com faixa alta). O QC executa o validador contratual; `nao_avaliada` aparece como pendência, não aprovação. `entregavel: false` impede apresentar o apontamento como conclusão jurídica.

## O que não fazer

- **Não use memória como regra.** Artigo, súmula ou prática de mercado só entra com fonte lida ou marcado "não verificado".
- **Não funda as duas severidades.** Cláusula pode ser juridicamente segura e comercialmente ruim, ou o inverso.
- **Não declare cláusula nula, abusiva ou válida** como fato: aponte a pergunta de revisão e a norma, e deixe a conclusão ao advogado.
- **Não trate "não encontrei" como "não existe".** Cláusula ausente é lacuna a confirmar no original.
- **Respeite a política do usuário** em `confidentiality.consultas_externas` (padrão `permitidas`): se ele a restringiu, não envie o contrato a serviço externo.

## Quando escalar

- **Pedido de conclusão final** ("diga se a cláusula é nula", "entregue como parecer final"): recuse a conclusão, entregue as perguntas de revisão com a norma literal e o encaminhamento ao advogado.
- **Resultado com `rascunho: true` ou `entregavel: false`** na validação de `issues.json`: não sai da casa.
Além de [escalacao.md](../../shared/escalacao.md): contrato de adesão ou consumerista (outro regime), cláusula de arbitragem ou foro estrangeiro, contrato com ente público, regulado (saúde, financeiro, telecom) ou com dado pessoal sensível; alteração rastreada preexistente no arquivo; qualquer apontamento de severidade crítica.

## Limites

Cobre NDA e prestação de serviços/SaaS sob o Código Civil. OCR é opcional e sempre `partial` (PDF digitalizado só é revisado depois de conferido no original). Redline só em texto simples de parágrafo: hiperlinks, campos e tabulações são barreiras. As 19 regras de Código Civil e LGPD e as 2 regras-rascunho de NDA (art. 195 da Lei 9.279/1996) permanecem inativas nesta cópia. Não calcula valores nem prazos. Casos de referência: [tests/test_contrato.py](../../tests/test_contrato.py) (contrato sintético com defeitos conhecidos) e [tests/test_docx_edicao.py](../../tests/test_docx_edicao.py) (redline).
