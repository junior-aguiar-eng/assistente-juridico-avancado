# Sondagem das pontes de fontes (17/10/2026)

Método: `scripts/sonda_pontes.py` (User-Agent de navegador, 2 tentativas, depois sem o cabeçalho, timeout 25 s) mais chamadas diretas às ferramentas MCP. Dados brutos: [sondagem-pontes.json](sondagem-pontes.json). Foi uma consulta curta por ponte; não mede estabilidade nem limites de uso.

## Resultado

| Ponte | Resultado | Uso na v0.1 |
|---|---|---|
| Planalto, CC compilado | 200, 0,9 MB, "Art. 206" encontrado (windows-1252) | **Ativa.** Texto vigente de lei federal |
| Planalto, CPC | 200, 1,7 MB, "Art. 85" encontrado | **Ativa** (a URL usada foi a não compilada; preferir `...compilada.htm`) |
| Senado, `/legislacao/lista` | 200, JSON com Lei 10.406 (id 552282) | **Ativa.** Metadados, não o texto consolidado |
| Senado, `/v3/api-docs` | 200, 174 KB | Ativa; endpoints `/legislacao/{tipo}/{numdata}/{anoseq}` e `/legislacao/urn` disponíveis |
| STJ dados abertos (portal) | 200; arquivos JSON de espelhos de acórdãos baixáveis (2 MB) | **Ativa.** Ementas oficiais em lote |
| STJ inteiro teor (`processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao`) | 200, `application/pdf` | **Ativa.** Texto integral do acórdão (conferir leitura do PDF) |
| STJ `scon.stj.jus.br` | 403 nas 3 tentativas; resposta `Cf-Mitigated: challenge` (Cloudflare) | **Bloqueada por desafio anti-robô.** Não contornar. Usar dados abertos e `processo.stj.jus.br` |
| STF, portal | 200, 76 KB | Ativa para páginas institucionais |
| STF, `jurisprudencia.stf.jus.br` | 202 vazio nas 3 tentativas; `x-amzn-waf-action: challenge` (AWS WAF) | **Bloqueada por desafio anti-robô.** Não contornar. Ver "Lacunas" |
| LexML (SRU) | 200, mas a resposta é página "Verificação de segurança — Senado Federal" | **Bloqueada por verificação.** Não contornar |
| DataJud (TJSP, sem credencial) | 401 | Host alcançável; exige chave. Só metadados e movimentações, não inteiro teor. Pendente: decisão do usuário sobre a credencial |
| Câmara, API de dados abertos | 200, JSON | Ativa (proposições; fora do foco da v0.1) |
| `consultar_artigo` (enam-estudo) | OK: CC art. 206 §5º devolvido com localização, URL do Planalto e data de obtenção (30/09/2026) | **Ativa**, cobre só diplomas indexados. O texto vem recortado com `[...]`; não serve como literalidade integral |
| ForgeLex `forgelex_connection_status` | autenticado, sem custo | Ativa |
| ForgeLex `research_search_case_law` | OK: 2 acórdãos do STJ, com origem nos dados abertos do STJ, hash do conteúdo, data de captura e `fullTextUrl` | **Ativa como localizador.** Exige `idempotencyKey` em cada chamada |

## Achados que mudam o desenho

1. **STF não tem ponte automática hoje.** Jurisprudência do STF fica como `source_missing`, com o pedido de documento ao usuário como último recurso. Teses de repercussão geral e súmulas vinculantes podem ser buscadas pelo ForgeLex, a validar.
2. **STJ tem ponte oficial completa:** busca (ForgeLex, que se apoia nos dados abertos do STJ) mais inteiro teor pelo host `processo.stj.jus.br`. O estado `supported` exige ler o inteiro teor, não só a ementa.
3. **ForgeLex localiza; a confirmação vem da fonte.** A proveniência declarada (`OFFICIAL_SOURCE_HASH`) é do ForgeLex, não minha. Para o pacote, ele conta como ponte secundária até a skill reler a fonte oficial.
4. **Senado dá metadados e histórico; o texto vigente vem do Planalto.** As duas pontes funcionam e se complementam.
5. **Desafios anti-robô não são contornados.** STF, `scon.stj.jus.br` e LexML ficam fora da v0.1, e o relatório da skill deve mostrar esse estado em vez de dizer "não encontrado".

## Teste complementar: STF pelo navegador integrado do app

Resultado: **funciona.** O navegador do app abriu `jurisprudencia.stf.jus.br`, a página carregou sozinha (o desafio do AWS WAF, que devolvia 202 vazio ao script, foi concluído pelo próprio navegador, sem CAPTCHA e sem intervenção minha). Uma busca comum ("prescrição intercorrente execução fiscal") devolveu 61 acórdãos, 3 de repercussão geral, 940 decisões monocráticas e 1 informativo, com ementa, órgão julgador, relator e datas (ex.: ARE 1563128 RG, Tema 1473). O texto da página é legível por `get_page_text`, e a busca usa `POST /api/search/search`, respondido com 200.

Limites: é uma ponte **manual e lenta** (uma sessão de navegador por consulta), não uma API; depende de a pane do app estar aberta; não foi testado o inteiro teor nem o download de PDF; o desafio pode passar a exigir interação humana a qualquer momento, e nesse caso a skill para e pede a você. Não foi tentado nenhum contorno.

## Teste de leitura do inteiro teor (17/10/2026)

**STJ** (`processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202302535191`, AREsp 2.432.194/SP, rel. Min. Moura Ribeiro): baixou por HTTP simples, PDF de 16 páginas e 301 KB, com camada de texto (35,9 mil caracteres, sem página escaneada). Três extratores, mesmo arquivo:

| Extrator | Resultado na ementa (p. 1) |
|---|---|
| pypdf 6.19 | Acentos corretos, mas **palavras fora de ordem** ("ART. 206" vai para o meio da frase, "DISSÍDIO7/STJ") |
| pdfplumber | **Ordem correta e legível**, idêntica à ementa dos dados abertos |
| PyMuPDF | Ordem parcial, texto fragmentado em linhas curtas; licença AGPL |

Correção do que se viu no terminal: os caracteres "�" apareceram só na exibição do console; o texto extraído não contém U+FFFD.

O que a extração localiza com pdfplumber: ementa (p. 1 a 3), RELATÓRIO (p. 4), VOTO (p. 5), dispositivo "CONHEÇO... NEGAR-LHE PROVIMENTO" (p. 14), e as ocorrências de "art. 206, § 5º, I" nas páginas 1, 2, 3, 4, 6 a 10. Cuidados: (a) o voto transcreve decisões e ementas de outros julgados (p. 7 a 10), então um trecho encontrado pode ser **citação**, não fundamento do relator; o localizador precisa registrar a seção e se o trecho está entre aspas; (b) a p. 15 traz listas de números de processo que geram falso positivo em busca por "206"; (c) "Certidão de julgamento" não foi achada pelo texto.

**STF** (ARE 1563128 RG, Tema 1473, `idDocumento=801173345`): o script cai no desafio do AWS WAF (HTTP 202) no segundo salto, em `redir.stf.jus.br`. O navegador do app, sessão comum, recebeu o PDF (`%PDF-1.4`, 276.767 bytes, 200). Não consegui trazer o arquivo para o disco: o navegador impediu o envio a um receptor local em 127.0.0.1 e o painel do app não expõe o texto do PDF. Portanto **a extração do inteiro teor do STF não foi testada**. Por outro lado, a própria resposta da busca do STF (`POST /api/search/search`) já entrega campos estruturados: ementa completa, tese, tema, ata da decisão, legislação citada, datas, partes e a URL do inteiro teor. Isso sustenta citação em nível de ementa e tese, mas não prova fundamento do voto.

### Efeito no desenho

1. **Extrator de PDF muda de pypdf para pdfplumber** (MIT; usa pdfminer.six). pypdf fica como reserva e para metadados. PyMuPDF segue fora (AGPL).
2. O extrator deve gravar **página, seção (ementa, relatório, voto, dispositivo) e marca de citação** em cada trecho, e permitir comparar a ementa extraída do PDF com a ementa da fonte estruturada.
3. STF: v0.1 usa a ementa e a tese da busca do navegador do app; inteiro teor vem do PDF fornecido por você até haver ponte comprovada.

## Lacunas e decisões pendentes

- **STF:** decidir se vale usar o navegador integrado do app (uma sessão humana) ou apenas aceitar o documento fornecido.
- **DataJud:** a chave pública é distribuída pelo CNJ, mas é uma credencial; só entra se você autorizar o uso. Sem ela, nada de consulta processual.
- Ler o PDF de inteiro teor do STJ e testar a extração de trecho (será feito com `extract.py`).
- Testar a estabilidade: repetir a sondagem em outros horários e medir limites.

## Nova sondagem (2026-10-17)

Resultado igual ao anterior em 10 de 11 alvos (Planalto, Senado, STF portal, Câmara: 200 com o conteúdo esperado; SCON do STJ: 403; DataJud sem chave: 401; STF jurisprudência: 202 com desafio; LexML: 200 sem o conteúdo esperado). Única mudança: `dadosabertos.web.stj.jus.br` estourou 25 s nas três tentativas da sondagem, mas respondeu 200 em 17,6 s num `curl` logo depois. Tratar como lento e intermitente: usar timeout de 60 s e uma nova tentativa antes de declarar indisponível.
