# RC-01 — reconciliação isolada de ORG-01 a ORG-03

Estado: concluída localmente para revisão, sem commit ou push. Pedido de 22/10/2026: reconciliar em cópia isolada, preservar correções locais, manter regras inativas, separar R07/R10, corrigir codificação e executar testes; sem commit/push.

Base: snapshot integral de 127 arquivos do worktree Codex, HEAD `abbf85a779627a49ac38def046bbc142bacbacd1`, incluindo AF-01/CP-01/AC-01/GT-01 sem commit. Recuperada: `ff225a7b3c228e50d71f1c56439575b44b16834c`, base comum `4e9989c`. Implementação somente nesta cópia independente, branch `codex/reconciliacao-org01-org03`; fontes preservadas e verificadas por hash/refs/índice antes/depois.

Escopo: importar inventário/contrato/validador/propostas/piloto/diagnóstico OCR e robustecimentos versionados recuperados; conciliar extração, DOCX, documentação, dependências e testes sem substituir controles locais. Preservar `scripts/auditar.py`, `scripts/validate.py`, `scripts/auditoria_documental.py`, regras e governança locais salvo necessidade comprovada de compatibilidade. Não implementar ORG-04/05.

Corpus: manter R07/R10 públicos locais. Renomear os dois casos privados recuperados para `ORG-R07-PRIVADO`/`ORG-R10-PRIVADO`, com hashes próprios; renomear metadados/gabaritos e suas referências. Não importar PDFs privados nem sobrescrever expectativas públicas.

Regras: conservar os 19 rascunhos inativos e não importar aprovação/ativação do commit `c951aba`. Preservar metadados de revisão locais; relatórios históricos não são aprovação da cópia reconciliada.

Aceitação: testes locais de atribuição/integridade/auditoria e testes recuperados de peças/OCR passam; JSON UTF-8 independe da locale Windows; casos sem colisão; regras inativas; suíte integral offline e revisão mecânica das oito skills; diff sem erros; checkouts de origem e histórico de evidências intactos. Resultados históricos 676/732 não contam como execução desta cópia.

Arquivos previstos: módulos novos `scripts/pecas*.py`, `piloto_pecas.py`, `diagnostico_ocr.py`, `ocr.py`, conciliação de `extract.py`, `preencher.py`, `redline_docx.py`; testes e fixtures sintéticas associados; documentos ORG, plano principal, README, shared, requirements e coordenação. Não modificar origens nem índices/refs alheios.

## Implementação e validação

- Snapshot local preservado como base; módulos recuperados de peças/OCR e robustecimentos DOCX conciliados. `auditar.py`, `validate.py`, `auditoria_documental.py`, `contrato.py`, regras e governança permanecem byte a byte iguais à fonte local. O extrator `0.5.1` incorpora OCR `0.5.0`, atribuição contextual e curingas PowerShell; invalida os caches anteriores sem migrar snapshots históricos.
- O manifesto público permanece byte a byte igual à fonte. Os dois privados estão em `tests/casos/regressao/manifesto-privado-org.json`, com IDs `ORG-R07-PRIVADO`/`ORG-R10-PRIVADO`, gabaritos renomeados e hashes próprios; o runner combina os registros apenas para os testes. Os originais privados continuam ausentes e ignorados pelo Git.
- Não foram importadas ativações ou metadados de aprovação da branch recuperada. As 19 regras continuam inativas. O plano principal foi conciliado; ORG-04/05 continuam não iniciadas.
- Codificação: leituras JSON de fixtures recuperadas agora declaram UTF-8. As entradas da CLI são gravadas nos bytes UTF-8/LF esperados pelos hashes, sem depender de cp1252/CRLF do Windows.
- RED inicial de separação: 1 falha/1 controle aprovado; RED de codificação: 1 falha/2 controles aprovados. Rodada focada inicial: 303 aprovados/1 falha na gravação da fixture CLI, corrigida sem alterar o validador. Rodada de CLI/contrato/separação após correção: 28 aprovados.
- Ambiente limpo próprio `.venv-limpo`, Python 3.14.6, instalado com os requirements existentes conciliados; `pip check`: sem requisitos quebrados. Revisão focada final nesse ambiente: **304 aprovados em 75,24 s**, sem ignorados. O ambiente inicial `.venv` herdava bibliotecas do sistema e não modificou a instalação global; não é o ambiente recomendado de reprodução.
- Revisão mecânica das oito skills: 8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL. Links locais conferidos; `git diff --check` sem erros. Sem lint/build próprios configurados no projeto.
- Revisão estática independente, somente leitura: nenhum achado material pendente após corrigir a identificação pública de R07 no plano principal. Não julgou mérito jurídico, fidelidade dos privados ausentes, Docling opcional ou ORG-04/05; não executou testes.
- Suíte integral offline concluída: **943 aprovados e 5 ignorados em 728,37 s (12m08s)**, Python 3.14.6/Windows, `JURIS_REDE=0`, `PYTHONDONTWRITEBYTECODE=1`, `--basetemp=../pytest-integral`, cache do pytest desativado. Usou o ambiente inicial próprio `.venv` com dependências de sistema herdadas; a rodada final de 304 testes focados e o `pip check` foram executados adicionalmente no ambiente limpo `.venv-limpo`. Ignorados: rede DataJud, rede fontes, Docling Parse opcional não instalado e os dois PDFs privados ausentes. Nenhuma falha final. Evidências, baseline, logs de instalação/testes e delta incremental em `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/reconciliacao-org-2026-10-22-ijrtytf6`, fora do repositório.

## Entrega e limites

A cópia independente está em `C:/Users/Boni Jr/Documents/Codex/assistente-juridico-evidencias/reconciliacao-org-2026-10-22-ijrtytf6/Skill Legal`, branch `codex/reconciliacao-org01-org03`, HEAD-base `abbf85a779627a49ac38def046bbc142bacbacd1`. Não foi criado commit, feito push ou integrado o resultado aos dois checkouts anteriores. As alterações locais anteriores foram copiadas, preservadas e distinguidas do delta RC-01.

- Não há conflito textual de mescla pendente. O delta incremental contra o snapshot local está em `delta-rc01.patch` e `delta-rc01.json`, na pasta externa de evidências. A aplicabilidade foi conferida em outro snapshot, sem aplicar o patch nas origens. O patch textual normaliza CRLF/LF para comparação; a identidade dos PDFs e o manifesto público permaneceram intactos.
- A conferência final verifica os hashes de 127 arquivos Codex e 106 do checkout original, além de branch, HEAD, refs, status e índice. O resultado detalhado está em `preservacao-final.json`. Regras, governança, controles locais e manifesto público são também comparados diretamente entre a fonte e a cópia.
- Os 943 testes não conferem mérito jurídico nem validam o texto privado: os PDFs privados estão ausentes. Os seis trechos e as fronteiras recuperadas continuam evidências históricas com escopo limitado. Não houve nova conferência humana.
- Docling Parse permanece opcional e não foi instalado no ambiente de validação desta reconciliação. Não foram executados testes de rede, CI remoto, instalação/distribuição do produto, ORG-04/05 ou ativação de regras.
- Ambiente recomendado para continuar: `../.venv-limpo/Scripts/python.exe`, criado sem bibliotecas de sistema herdadas e com dependências diretas dos requirements conciliados. `ambiente-limpo-freeze.txt` registra as versões instaladas; `pip-check.txt` confirma ausência de requisitos quebrados. Suíte completa nesse ambiente limpo específico não foi repetida: há 304 testes focados completos nele, e suíte integral no ambiente inicial.
