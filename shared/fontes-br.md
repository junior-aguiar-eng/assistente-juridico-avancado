# Fontes brasileiras: ordem de tentativa

Base: [docs/sondagem-pontes.md](../docs/sondagem-pontes.md) (17/10/2026). Toda consulta registra URL, data, hash do conteúdo e trecho. Ver [estados.md](estados.md).

| Preciso de | 1ª opção | 2ª opção | Último recurso |
|---|---|---|---|
| Texto vigente de lei federal | Planalto, versão `compilada` (`fetch_oficial.py`, windows-1252) | `consultar_artigo` (só diplomas indexados; texto recortado) | Documento fornecido pelo usuário |
| Alterações e revogações | API de Dados Abertos do Senado (`/legislacao/...`) | Notas do Planalto | Usuário |
| Acórdão do STJ | ForgeLex localiza, `processo.stj.jus.br` entrega o inteiro teor | Dados abertos do STJ (ementa) | Usuário |
| Acórdão, tema ou súmula do STF | Navegador integrado do app em `jurisprudencia.stf.jus.br` (manual, lido da página) | ForgeLex localiza (a validar) | Usuário |
| Número de processo | `cnj.py` valida a estrutura e o dígito | — | — |

## Regras

- Ponte secundária (ForgeLex, `consultar_artigo`) localiza; teto `partial` até a fonte oficial ser lida.
- Desafio anti-robô (Cloudflare, AWS WAF, "verificação de segurança") não é contornado. Se o navegador do app o concluir sozinho, a leitura vale; se pedir interação humana ou CAPTCHA, para e pede ao usuário. Registra-se `source_missing` com o host.
- Ementa não equivale a inteiro teor. Proposição sobre fundamentos do acórdão exige o trecho pertinente do voto.
- Falha de ponte nunca vira "não existe".
