# Revisão local e continuidade técnica — 20/10/2026

Base `fcbe5d2ddc1a70c6327abd6a95bfea0631b18bdf`, branch `codex/organizacao-colaboracao`, no worktree exclusivo do Codex. Escopo: diff local, arquivos novos R07/R10/DataJud e correções demonstradas; sem commit, push, ativação de regras ou mudanças no checkout do Claude.

## Achados e correções

1. **Ementa aninhada com título isolado.** A proteção da entrega anterior tratava somente `EMENTA:` inline. `EMENTA` ou `E M E N T A` em uma linha própria passava antes pelo reconhecedor de títulos e convertia a seção de voto/decisão em ementa principal. A correção aplica a mesma ressalva aos dois formatos, preserva texto/localizador/contexto e marca `partial` com `secao_aninhada_ambigua`. Ementa principal continua reconhecida. O extrator passa a `0.4.2`, para não reutilizar resultados antigos de cache; nenhum cache foi apagado.
2. **DataJud com resposta inválida ou incompleta.** O leitor usava lista vazia como padrão quando faltava `hits.hits`, podendo devolver `nao_encontrado` para um corpo de erro. Também ignorava `timed_out`/falhas em shards e podia lançar exceção sem tratamento ou anunciar sucesso sem identificar o processo. A normalização agora exige a estrutura mínima da busca e a identificação compatível; falhas/timeout parcial e formato inválido produzem `erro_de_acesso`, JSON e saída CLI 1. Busca válida vazia continua `nao_encontrado` com a ressalva de que ausência na API não prova inexistência. A conversão dos metadados ocorre dentro do tratamento de erros, antes de entregar qualquer resultado.

O formato de busca e os sinais de resposta foram conferidos no [exemplo oficial do CNJ](https://datajud-wiki.cnj.jus.br/api-publica/exemplos/exemplo1/) e na [documentação da API de busca do Elasticsearch](https://www.elastic.co/docs/solutions/search/the-search-api). A documentação Elastic distingue resultado parcial por timeout e falhas em shards de uma busca completa. O acesso direto à wiki pelo leitor web retornou 403; o mecanismo já existente do projeto conseguiu obter a chave durante o teste de rede. Nenhuma chave foi registrada.

## Revisão da entrega anterior

Conferidos o diff versionado e os arquivos novos: extração, gates de rede/OCR, manifesto, proveniência e documentação. Os originais públicos e seus hashes permanecem preservados; o manifesto mantém CRLF conforme `.gitattributes`. O ajuste pré-existente de `shared/escalacao.md` foi confrontado com a política vigente e preservado. Gabaritos mecânicos anteriores, contratos/minutas, regras e corpus histórico não foram alterados nesta rodada; revisão jurídica continua pendente. Esta é revisão do próprio agente implementador, sem revisão independente ou aprovação humana.

## Verificações

Ambiente local: Windows, Python 3.14.6 e Tesseract disponível com `por` (também `eng`/`osd`). Dependências e configurações não foram modificadas. A suíte integral usa `python -B -m pytest -q -rs --durations=10`, com `JURIS_REDE` ausente e `PYTHONDONTWRITEBYTECODE=1`; o teste real é executado separadamente com `JURIS_REDE=1`.

- Base focada antes das novas correções: **60 aprovados, 1 ignorado**, em 81,80 s.
- Reprodução inicial: **19 falhas e 5 aprovações** em 5,04 s; duas formas adicionais de resultado sem identificação também foram reproduzidas antes da correção. Falhas eram saídas/estados incorretos ou exceções na interpretação da resposta.
- Após a correção: **26 regressões novas aprovadas** em 6,92 s, com PDFs sintéticos gerados pelo helper existente e respostas DataJud controladas offline. Nenhum gabarito preexistente foi relaxado.
- Consulta real do DataJud antes da correção: **1 aprovado em 29,45 s**, com o processo esperado encontrado pelo teste original. O timeout observado em 19/10 não se repetiu nessa tentativa, sem comprovar a causa histórica ou disponibilidade contínua/global do serviço.
- Repetições da consulta após a correção: **duas falhas, em 42,65 s e 42,40 s**, `erro_de_acesso`/`TimeoutError: The read operation timed out`. A exceção ocorre na leitura de rede, antes de normalizar a resposta. As três tentativas são registradas; não houve sucesso real após o patch. O sucesso anterior não comprova estabilidade, e a alteração local não corrige nem explica o timeout remoto/intermediário. Não houve outras tentativas nem mudança de timeout para obter aprovação.
- Revisão mecânica: **8 PRONTA, 0 ATENCAO, 0 PREOCUPACAO_MATERIAL**. `pip check`: sem conflitos.
- Suíte offline integral: **624 aprovados e 3 ignorados em 742,40 s (12min22s)**, saída 0, sem falhas. R06/R07/R10 executados e aprovados. Ignorados: os dois testes reais de rede, por `JURIS_REDE` ausente, e o marcador sem casos aguardando documentos. Essa execução valida o código local; não equivale a CI remoto, avaliação com modelo ou correção jurídica.

## Pendências e limites

Continuam pendentes revisão jurídica humana das skills/gabaritos/regras, segunda avaliação com documentos reais, fechamento formal de CL-01/CL-02 pelo responsável e integração separadamente autorizada. OCR de R10 mantém erros/omissões e a seção genérica `cabecalho`; R07 não comprova cobertura de todos os layouts e-SAJ/PJe. O caso STJ `c005` continua limitado à ementa no pacote externo de reconciliação; o corpus histórico permanece intacto. A ativação de regras exige decisão identificada do revisor, não é consequência desta entrega.

Baseline, logs e saídas próprios: `C:/Users/Boni Jr/AppData/Local/Temp/juris-revisao-20261020-mvoshh6b`. `preservacao-final.json` confirma os 106 arquivos acompanhados do Claude sem diferenças e os hashes de regras, skills, fixtures/corpus e `shared/escalacao.md` preservados em relação à entrada. Nenhum teste ou comando Git foi executado naquele checkout.

Alterados nesta rodada: `scripts/extract.py`, `scripts/datajud.py`, os dois arquivos de testes correspondentes, `README.md`, `docs/COORDENACAO.md`, a atualização datada em `docs/avaliacao-skills-2026-10-18.md` e o aviso histórico em `docs/validacao-r07-r10-datajud-2026-10-19.md`; este relatório é novo. As demais alterações locais da entrega anterior foram preservadas. Conferência final de whitespace sem erros (`git -c core.whitespace=cr-at-eol diff --check`); índice vazio, branch e HEAD iguais à entrada. Sem commit, push, PR, instalação ou ativação de regras.
