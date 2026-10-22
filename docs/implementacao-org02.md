# ORG-02 — implementação e verificação

> Execução nativa com `superpowers:executing-plans` e TDD. Este documento detalha o pacote; prioridades e andamento permanecem no [plano principal](plano-principal.md).

**Objetivo:** verificar o contrato antes de propor peças e avaliar uma segmentação assistida de referência.
**Arquitetura:** `scripts/pecas.py` expõe `validar_inventario` conforme o contrato; histórico fica em módulo próprio se necessário. Propostas opcionais usam módulo separado e nunca conferem automaticamente. Consumidores e extrator legados não mudam.
**Tecnologias:** Python >=3.12; JSON Schema Draft 2020-12 com verificador RFC 3339. Sem serviço de inferência remoto.
**Especificação:** [contrato v1](contratos/pecas-v1.md).

## Restrições e interfaces

- Preservar bytes de extração, IDs, offsets Unicode e hashes SHA-256; nenhum remapeamento silencioso.
- Retorno: `{valido, erros: [{codigo, onde, mensagem}], avisos}`. Diagnósticos não transcrevem conteúdo dos documentos.
- Validade significa integridade do contrato; não mérito, correção de classificação ou autorização de uso material.
- Originais e artefatos privados ficam fora do Git. Commits locais, sem push.
- `jsonschema` e `rfc3339-validator` passam a dependências de execução somente quando o validador os consumir; licenças já verificadas em ORG-01.
- Piloto não ativa novos extratores nas skills. Adoção depende de resultado, licença e custo medidos.

## Foco de revisão

Extrações malformadas/ambíguas; perda de um caractere ou ordem de leitura incoerente; conferência humana antiga reaplicada após alteração material; OCR ou localização incerta apresentados como conferidos; histórico com objetos removidos e referências a identidades inexistentes. Os testes das tarefas abaixo cobrem essas classes.

## Tarefa 1 — identidade e estrutura

Arquivos: `scripts/pecas.py`, `tests/test_pecas.py`, requirements e avisos de terceiros.
Interface produzida: `validar_inventario(inventario: dict, extracao_bytes: bytes, *, arquivo_sha256: str, anterior_bytes: bytes | None = None) -> dict`.

- [x] Escrever testes positivos CT01–CT07 e negativos de esquema, bytes/hash, documento ambíguo, configuração, versão do extrator e JSON inválido; observar falhas antes do código.
- [x] Implementar validação estrutural e identidade sem expor conteúdo em mensagens.
- [x] Executar `python -m pytest -q tests/test_pecas.py`; esperado: todos os casos implementados passam.

## Tarefa 2 — grafo, cobertura e leitura

Consome a mesma interface. Arquivos: `scripts/pecas.py`, `tests/test_pecas.py`.

- [x] Adicionar negativos para cada código do contrato: IDs duplicados/reservados, referências ausentes, lacuna/sobreposição/offset, página ausente, limites trocados/intercalados, seção de outra peça, evento incompatível, OCR oculto e pendências ausentes; observar RED.
- [x] Implementar referências, partição exata, ordem física, estados de leitura e conferência; pendências materiais tornam-se avisos, sem transformar contrato íntegro em aprovação.
- [x] Executar testes focados; esperado: CT01–CT07 válidos e mutações recusadas pelo código correspondente.

## Tarefa 3 — histórico

Arquivos: `scripts/pecas_historico.py`, `scripts/pecas.py`, `tests/test_pecas.py`. Consome revisão anterior em bytes exatos.

- [x] Adicionar RH01 positivo e negativos para cadeia/hash/prefixo, origem trocada, exclusão com alvo inválido, eventos fora de ordem, identidade reutilizada e conferência preservada após mudança de conteúdo/localização/evidência; observar RED.
- [x] Implementar comparação entre revisões e invalidação por dimensão, aceitando nova conferência posterior à correção.
- [x] Executar testes focados; esperado: fusão RH01 válida e alterações materiais sem nova conferência recusadas.

## Tarefa 4 — comando verificável

Arquivos: `scripts/pecas.py`, `tests/test_pecas_cli.py`, documentação do comando.

- [x] Testar processo real: `validar` lê original autorizado e calcula hash, retorna JSON/exit 0 para íntegro e exit 1 para inválido, não escreve entradas nem imprime trechos; observar RED.
- [x] Implementar CLI somente de validação, com revisão anterior opcional.
- [x] Executar testes de CLI e contrato; esperado: sucesso e falhas explícitas, originais intactos.

## Tarefa 5 — segmentação de referência e piloto

Consome o validador; propostas novas devem passar nele. Arquivos próprios de proposta/piloto e respectivos testes, sem integrar consumidores.

- [x] Exercitar títulos espaçados, títulos citados, duas peças do mesmo tipo, fronteiras no bloco e revisão manual com sinais e pendências explícitos, antes da implementação.
- [x] Implementar proposta conservadora: sem título/autoria confiáveis, não inventar natureza nem conferência; mapa de páginas insuficiente permanece incerto.
- [x] Comparar baseline e candidato Docling em execução local opcional, registrando versões, licenças, tempo e falhas; rejeitar adoção se os requisitos ou resultados não a sustentarem. Distinguir piloto não executado de resultado negativo.
- [x] Medir fronteira ORG-R07-PRIVADO contra gabarito humano, sem publicar textos privados; os exemplos artificiais não são benchmark independente.

## Fechamento

- [x] Revisão independente única do conjunto; corrigir achados materiais com RED→GREEN.
- [x] Executar `JURIS_TESSDATA=... python -m pytest -q -ra`, conferir dependências, geração de fixtures e `git diff --check`.
- [x] Fechar os arquivos e verificações desta entrega em commit local; sem push.
