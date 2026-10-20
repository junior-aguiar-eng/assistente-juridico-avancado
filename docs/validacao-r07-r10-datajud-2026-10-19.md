# R07/R10 e diagnóstico do DataJud — 19/10/2026

Escopo autorizado: pendências técnicas no worktree do Codex, base `fcbe5d2`, sem commit, push, regras jurídicas ativas ou alterações no checkout do Claude. Gabaritos abaixo são de **extração**, conferidos no documento público; não são revisão jurídica humana nem avaliação das skills com modelo.

Atualização de 20/10/2026: este documento preserva os resultados de 19/10. A [revisão posterior](revisao-tecnica-2026-10-20.md) registra novas correções e três tentativas de rede: uma consulta DataJud aprovada antes do patch e duas repetições posteriores com timeout. A disponibilidade não deve ser deduzida desta fotografia histórica.

## Documentos públicos e proveniência

Os três PDFs são cópias dos bytes recebidos, sem reparo, OCR gravado no original, anonimização ou substituição de páginas. URLs, data UTC, tamanho e SHA-256 estão em [`proveniencia-r07-r10.json`](../tests/casos/regressao/proveniencia-r07-r10.json). Nomes profissionais e assinaturas presentes nos documentos públicos não foram tratados como dados de cliente. Não foram usados documentos privados.

| Caso | Fonte e conferência | Resultado esperado |
|---|---|---|
| R07 | [TJMG, AI-Cv 1.0000.25.176803-2/002](https://www5.tjmg.jus.br/jurisprudencia/relatorioEspelhoAcordao.do?ano=25&codigoOrigem=0000&inteiroTeor=true&numero=176803&sequencial=002&sequencialAcordao=0&ttriCodigo=1), 12 páginas, relatório oficial de inteiro teor. Não é apresentado como PDF e-SAJ/PJe. As 12 páginas foram renderizadas e examinadas; títulos e fronteiras conferidos no original. | Ementa na página 1; acórdão inicia na página 1, nome do relator na página 2; voto da página 2 à 12. Ementa transcrita na página 9 não inicia nova seção principal. `partial` e aviso `secao_aninhada_ambigua`, porque a fronteira da transcrição exige leitura do original. |
| R10 | [Prefeitura de Picos, ofício 106/2022 PGM](https://www2.picos.pi.gov.br/wp-content/uploads/2022/05/CamScanner-05-26-2022-09.39.pdf), uma página, uma imagem e zero caracteres nativos; página renderizada e conferida. | Sem OCR: `no_text`, aviso e zero blocos. Com Tesseract/`por`: `partial`, blocos com tag `ocr` e `p.1`; âncoras do número, data e corpo. Existem erros, omissões e manuscrito/assinatura sem transcrição confiável; não é certificação de fidelidade integral. |
| Negativo adicional | [Taquaral, ofício 38/2025 digitalizado](https://www.taquaral.sp.gov.br/portal/editais/0/1/1057/), duas páginas visíveis em PDFium/pypdf. O xref clássico inicia a subseção em 1, embora a primeira entrada seja o objeto livre 0; pdfminer retorna catálogo vazio. | `failed`/`erro_de_leitura`, inclusive com OCR solicitado; CLI sai com código 2 e falha não entra no cache. O original não foi reparado para fazer o teste passar. |

O ofício R10 menciona outro ofício ministerial; o arquivo de uma página **não** comprova leitura daquele anexo. O uso do acórdão e dos ofícios é exclusivamente documental; não adiciona módulos de direito agrário ou administrativo ao produto.

Em R10, sem título judicial reconhecido, os 23 blocos OCR permanecem na seção genérica `cabecalho` do extrator. O gabarito verifica o texto-âncora, a página, os avisos e a procedência OCR; não certifica a classificação editorial do corpo do ofício. Esta limitação fica explícita para uso posterior em mapeamento de fatos.

## Correções de extração

- Títulos formados inteiramente por letras maiúsculas separadas por espaços passam pela mesma lista de títulos conhecidos e pelas mesmas verificações geométricas. Texto e imagem originais permanecem intactos. Frases, palavras desconhecidas e linhas fora da posição admitida não viram títulos.
- `EMENTA:` inline dentro de seção narrativa preserva o contexto externo e gera aviso de ambiguidade; o documento fica `partial`. Não se inventa uma fronteira da transcrição ou autoria do trecho.
- PDF para o qual o leitor não encontra nenhuma página produz erro de leitura, em vez de `no_text` silencioso. Extrações anteriores de cache são invalidadas pela versão do extrator `0.4.1`; não há limpeza de caches ou reparo automático.

## DataJud: reprodução e controles

Referências consultadas: [acesso](https://datajud-wiki.cnj.jus.br/api-publica/acesso/), [endpoints](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/) e [consulta por número](https://datajud-wiki.cnj.jus.br/api-publica/exemplos/exemplo1/). O script utiliza o método, cabeçalho e corpo documentados. A chave foi lida em memória da wiki; nenhum valor de chave foi gravado em arquivos ou logs.

| Etapa | Evidência local |
|---|---|
| Wiki sem/com barra final | HTTP 200, 0,44/0,18 s; extração da chave pelo código existente funciona; `DATAJUD_API_KEY` ausente. |
| DNS/TLS e endpoint sem autorização | DNS resolve; GET/HEAD ao `_search` respondem HTTP 401 em 0,47/0,21 s, com verificação TLS padrão e sem proxy configurado. |
| POST com chave sintética inválida | HTTP 401 em 0,25 s. |
| Consulta com chave publicada, cliente atual (`urllib`) | `TimeoutError` de leitura; tanto timeout reduzido de diagnóstico como timeout de 40 s do script foram observados. |
| Mesmo endpoint/chave/consulta, cliente `requests` | `ReadTimeout` em 20,24 s. Trocar a biblioteca não resolveu. |
| `match_none`, `size: 0`, chave publicada | Sem resultado solicitado: timeout em TJSP (12,16 s) e STJ (12,20 s). A falha não depende daquele número de processo. |
| CLI existente | `erro_de_acesso`, motivo `TimeoutError: The read operation timed out`, saída 1. Não retornou processo ausente. |

**Conclusão delimitada:** o problema reproduzido está no recebimento da resposta às buscas que enviam a chave pública; não se reproduz na leitura da wiki, DNS ou acesso sem autorização. A combinação de controles sugere falha no caminho da busca autenticada, mas não comprova qual componente remoto ou intermediário a causa, nem comprova a disponibilidade global do serviço ou a validação bem-sucedida da chave. Uma rodada também retornou `erro_http`; a asserção de rede passou a exibir o diagnóstico devolvido para não perder essa informação.

Nenhuma mudança especulativa em endpoint, chave, validação TLS, timeout padrão ou aceitação de resultado ausente foi feita. Foram acrescentadas regressões offline de timeout explícito. O teste de rede agora exige exatamente `JURIS_REDE=1`: a condição anterior aceitava a string `0`, contrariando o contrato da suíte offline. A exigência de encontrar o processo continua inalterada.

## Verificação

- Antes das correções: sete falhas reproduziram títulos espaçados ignorados e PDF com zero páginas indevidamente aceito; depois, dois testes adicionais reproduziram a perda do contexto por ementa citada. Os casos sintéticos acompanham os PDFs públicos, sem substituí-los.
- Após as correções: 18 testes focados aprovados, incluindo os três PDFs; DataJud offline com `JURIS_REDE=0`: 22 aprovados e um teste de rede ignorado.
- Rede, separada da suíte offline: download real STJ aprovado e consulta DataJud reprovada, em 51,97 s. Falha preservada, sem tratar indisponibilidade como sucesso.
- Repetição isolada do teste DataJud, com diagnóstico na asserção: falhou em 42,35 s com `erro_de_acesso`/`TimeoutError: The read operation timed out`. Não houve correção local demonstrada para o serviço remoto.
- Revisão mecânica: oito skills `PRONTA`; `pip check`: sem conflitos. Segunda suíte integral offline, com JURIS_REDE ausente: **598 aprovados e 3 ignorados em 557,23 s**, sem falhas. Ignorados: dois testes de rede e o marcador de parametrização sem casos aguardando documento; R06/R07/R10 foram executados e aprovados.
- Primeira suíte integral: 596 aprovados, três ignorados e uma divergência em R06, em 691,27 s. Fonte original reconferida: a página 9 do STF contém ementa recuada e transcrita de outro julgado. O novo aviso conserva o contexto `decisao` e marca `partial`; o gabarito anterior exigia `ok` e aceitava a troca de seção. Apenas essa expectativa mecânica foi atualizada, com teste adicional da página/seção/citação. PDF e demais critérios preservados; não houve novo patch em código de produção após essa execução.

Para reproduzir os casos e o diagnóstico (PowerShell, no worktree do Codex):

```powershell
$env:JURIS_REDE = '0'
python -B -m pytest -q tests/test_regressao.py tests/test_regressao_documentos_reais.py tests/test_datajud.py
# Consulta pública explícita; resultado pode variar com a disponibilidade externa:
python -B scripts/datajud.py consultar 1000284-67.2021.8.26.0547
```

`JURIS_REDE` controla os testes opcionais, não bloqueia uma consulta solicitada diretamente pela CLI. A disponibilidade do DataJud deve ser reavaliada no ambiente do usuário; não se justifica ampliar timeouts, usar outras credenciais ou mudar a rota sem nova evidência.

Continuam pendentes revisão jurídica humana, ativação identificada de regras, avaliação das skills com documentos reais e disponibilidade de resposta do DataJud. A conclusão dos casos mecânicos R07/R10 não libera o pacote para uso jurídico nem fecha esses outros gates.

## Preservação e entrega local

Branch `codex/organizacao-colaboracao`, HEAD `fcbe5d2ddc1a70c6327abd6a95bfea0631b18bdf`. O índice permanece vazio, sem commit ou push; regras jurídicas não foram ativadas. As alterações documentais preexistentes foram preservadas. Conferência final por SHA-256 dos 106 arquivos acompanhados no checkout do Claude: nenhuma diferença contra a entrada; o corpus histórico STJ e as regras também mantêm os hashes iniciais.

O manifesto mantém CRLF conforme o original e a política `tests/casos/** -text`. A conferência de whitespace usa `git -c core.whitespace=cr-at-eol diff --check`, sem mudar configuração Git nem normalizar os originais. Logs, baseline e saídas de diagnóstico/extracao ficam em `C:/Users/Boni Jr/AppData/Local/Temp/juris-r07-r10-datajud-5d92525c8edc406b9f22b0095f8a081e/`; comandos, fontes e limites necessários à reprodução estão neste registro e na proveniência.
