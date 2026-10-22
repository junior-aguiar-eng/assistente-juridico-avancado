# Planejamento v2: juris-skills-br (8 skills, infraestrutura enxuta)

> **Histórico — substituído em 2026-10-22 pelo [plano principal vigente](plano-principal.md).** As prioridades, os estados e os critérios abaixo registram decisões de 16/10/2026 e não são o andamento atual.

Data-base: 16/10/2026. Substitui as fases 0 a 5 do blueprint original.

## 1. Decisões

- **Mantidas:** as 8 skills, a separação "existe / foi lida / apoia a tese", localizador em toda afirmação, falha explícita, regras brasileiras com fonte oficial datada.
- **Cortadas:** bundles por host, adapters, `build_bundle.py`, `upstream.lock.json`, `adaptations.json`, CLI, 7 schemas versionados, máquina de 9 estados, campanha de 72 execuções.
- **Simplificadas:** 2 formatos de dados (`facts.json`, `claims.json`), 4 estados de verificação, 3 scripts, 12 casos de regressão, um `THIRD_PARTY_NOTICES.md`.
- **Fora da v0.1:** OCR, DOCX/redline, PJe/eSAJ/DataJud, penal, trabalhista, tributário, previdenciário, prazos, cálculos, protocolo.

## 2. Estrutura do repositório

```
juris-skills-br/
  README.md
  THIRD_PARTY_NOTICES.md
  shared/
    garantias.md      # as 4 garantias; todas as skills apontam para cá
    estados.md        # unverified | supported | partial | unsupported
    fontes-br.md      # fontes oficiais e como citar
    dados.md          # formato de facts.json e claims.json
  skills/
    br-triagem/  br-mapear-autos/  br-cronologia/  br-pesquisa-juridica/
    br-verificar-citacoes/  br-revisar-contrato/  br-preencher-minuta/  br-auditar-entrega/
  scripts/
    extract.py   cnj.py   validate.py
  tests/
    casos/            # 12 casos fixos
    test_cnj.py  test_extract.py  test_validate.py
```

Cada `SKILL.md` tem no máximo 2 páginas: gatilho, entrada, saída, limites, link para `shared/`.

## 3. Quatro garantias (inegociáveis)

1. Estados separados: existência, leitura da fonte, apoio à proposição. Fonte não lida = `unverified`.
2. Localizador (documento + trecho) em toda afirmação material, ou marca explícita de inferência/lacuna.
3. Falha explícita: documento ilegível ou parcial vira `partial`; nunca silêncio.
4. Regra brasileira só com fonte oficial e data; indisponível nunca vira "inexistente".

## 4. Fases

| Fase | Entrega | Critério de saída | Estimativa |
|---|---|---|---|
| **0. Base** | Repo novo, `shared/`, `THIRD_PARTY_NOTICES.md` com origem e licença dos arquivos adaptados | Todo arquivo adaptado tem origem, commit e licença anotados | 1 a 2 dias |
| **1. Scripts** | `cnj.py` (do zero, pela Res. 65 CNJ), `extract.py` (pdfplumber + python-docx, JSON limpo, pt-BR, cache por hash), `validate.py` | Testes CNJ incluem DV 76 da base sintética `000215020238260024`; stdout sempre JSON parseável; PDF sem texto retorna `partial` | 3 a 4 dias |
| **2. Núcleo** | `br-mapear-autos`, `br-verificar-citacoes`, `br-auditar-entrega` | Fluxo "mapear, verificar, auditar" roda em 1 caso sintético e 1 caso real autorizado; nenhuma citação inventada passa como verificada | 4 a 5 dias |
| **3. Entorno** | `br-triagem`, `br-cronologia`, `br-pesquisa-juridica` | Triagem gera `matter.md`; cronologia mantém data ambígua; pesquisa sem fonte gera fila, não conclusão | 3 a 4 dias |
| **4. Contratos e minuta** | `br-revisar-contrato` (NDA e serviços/SaaS), `br-preencher-minuta` (Markdown primeiro) | **Bloqueada até revisor jurídico nomeado validar `rules/br`**; parâmetro estrangeiro nunca vira regra brasileira; campo sem prova fica pendente | 4 a 5 dias + revisão |
| **5. Liberação** | 12 casos de regressão rodados, README com limites | Zero falha crítica de invenção, fonte, sigilo ou alteração de original | 2 dias |

Total: cerca de 2 a 3 semanas de engenharia. A fase 4 depende de pessoa, não de código.

## 5. Ordem de dependência

`shared/` → `cnj.py`/`extract.py`/`validate.py` → mapear-autos → verificar-citacoes → auditar-entrega → triagem/cronologia/pesquisa → contrato → minuta.

Marco utilizável: fim da fase 2.

## 6. Mapeamento de fontes (resumido)

| Skill | Base aproveitada | Observação |
|---|---|---|
| br-triagem | Anthropic `matter-intake` | Sem caminhos fixos |
| br-mapear-autos | Chen Friedman `extract.py` (reescrita parcial) | Corrigir stdout, idioma e cache; sem PyMuPDF |
| br-cronologia | Anthropic `chronology` | Sem cálculo de prazo |
| br-pesquisa-juridica | Lex Intelligentia FIRAC-JB | Rejeitar o critério "CONFIRMADO" com número a confirmar |
| br-verificar-citacoes | LegalQuants `proposition-checking`, `ACCESS-MODES` | Estados próprios, 4 valores |
| br-revisar-contrato | evolsb (método), code-lawyer (formato de pacote) | Regras brasileiras escritas do zero |
| br-preencher-minuta | code-lawyer `document-fill` (conceito) | Markdown na v0.1 |
| br-auditar-entrega | LegalQuants `adversarial-qc` (checklist) | Gate técnico separado de aprovação humana |

CNJ do autodevx: não copiar. Brasil Legal Skills: só referência temática.

## 7. Testes

- **Unitários:** CNJ (válidos, inválidos, DV deslocado), extração (PDF textual, DOCX com tabela, corrompido, sem texto), validação dos 2 formatos.
- **12 casos fixos:** 4 cíveis, 4 contratos, 4 adversariais (citação inventada, citação real com tese errada, instrução embutida em PDF, anexo ausente). Gabarito com localizadores, revisado por profissional jurídico.
- Rodados a cada mudança em skill ou script. Sem campanha comparativa na v0.1.

## 8. Segurança e dados

- Documentos e citações são dados não confiáveis; instrução embutida em PDF não aciona ferramenta.
- Casos ficam fora do repositório, em pasta autorizada; `input/` somente leitura.
- Extração local não implica inferência local: política de envio ao modelo definida por caso.
- Mascarar CPF/CNPJ no resumo não anonimiza originais nem cache.

## 9. Pendências do usuário

1. Diretório do repositório novo.
2. Nome do revisor jurídico (necessário antes da fase 4).
3. Pequeno corpus autorizado, público ou anonimizado, para os casos reais.
4. Ambiente de execução principal e política de dados do modelo.

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Gargalo na revisão jurídica | Fase 4 só começa com revisor; fases 0 a 3 já entregam valor |
| PDF escaneado comum nos autos | Marcado `partial`; OCR é item futuro |
| Skills duplicando regra | Regra só em `shared/`, skills apenas apontam |
| Licenças | `THIRD_PARTY_NOTICES.md`, conferir licença local de cada componente LegalQuants; PyMuPDF fora |
| Estimativa otimista | Revisitar ao fim da fase 2 com o tempo real gasto |
