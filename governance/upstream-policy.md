# Política para trazer ideias ou arquivos de repositórios de referência

1. **Leia a fonte, não o resumo.** Abra o arquivo no commit fixado (`raw.githubusercontent.com/OWNER/REPO/COMMIT/CAMINHO`) antes de dizer que o pacote incorporou algo. Anote o commit.
2. **Confira a licença do componente**, não só a da raiz (ex.: LegalQuants tem licenças locais por componente; o repositório chen-friedman declara Apache-2.0 e NOTICE, mas o GitHub o lista como `NOASSERTION`). Sem licença clara, não copie.
3. **Prefira adaptar a copiar.** Copiar texto ou código exige registrar em `THIRD_PARTY_NOTICES.md`: repositório, commit, caminho, licença e a alteração feita. Adaptar a estrutura ou a ideia também se registra.
4. **Rejeite o que contradiz as garantias.** Exemplos já rejeitados: o nível "CONFIRMADO" com "[CONFIRMAR número]" do Guia Anti-Alucinação (afirma de memória); parâmetros de mercado dos EUA como se fossem brasileiros; preferência por ferramentas de fonte única.
5. **Não importe execução.** Hooks, `.mcp.json`, agentes agendados, scripts que baixam código: fora, salvo decisão registrada.
6. **Teste o que adaptar.** Todo item adotado entra com teste ou com caso real e, se for prompt, com avaliação por modelo.
7. **Atualização de upstream** entra por comparação de commits em branch própria, com diff dos arquivos relevantes. Sem atualização automática durante um caso.
8. **Rode a revisão de skill** (`scripts/revisar_skill.py`) em tudo que mudar.
