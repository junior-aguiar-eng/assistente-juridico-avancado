# Plano local da auditoria documental

Escopo autorizado: AF-01 em [COORDENACAO.md](COORDENACAO.md), base abbf85a.
Python existente, scripts locais e pytest; sem dependências novas, commit ou push.

## 1. Classificação dos apontamentos

- [x] Reproduzir com testes o falso baixo risco em base apenas comercial e a falta de estado jurídico não avaliado.
- [x] Acrescentar `nao_avaliada` com `motivo_nao_avaliada` obrigatório; manter severidade negocial independente. Recusar graduação jurídica baseada somente em prática comercial. Preservar validação e bloqueio das regras inativas.
- [x] Expor IDs com avaliação jurídica pendente no resultado do validador. Um resultado mecanicamente válido e sem avaliação jurídica não se torna entregável como conclusão.

## 2. Auditoria integrada

- [x] Testar entradas explícitas `--issues`, `--campos`, `--modelo`, `--minuta`, `--regras` e `--pacote`; reconhecer JSONs `issues`/`campos` recebidos por `--artefato`, sem confiar no nome do arquivo. Um conjunto de cada tipo por auditoria; ambiguidade é erro explícito.
- [x] Reutilizar os validadores originais em helper próprio. Apontamentos inválidos bloqueiam; avaliação jurídica não realizada aparece como pendência. Campos exigem modelo e minuta, lint sem erro e confronto do conteúdo OOXML com nova geração temporária sem aceitar inferidos.
- [x] Conservar marcações legítimas como pendências e `completo: false`. Registrar arquivos usados, inclusive pacotes de regras, no manifesto de hashes. Expor o resumo documental e as pendências em `status`, sem mudar aprovação humana.
- [x] Testar erros de leitura/estrutura, múltiplas extrações e alteração posterior; não alegar validação visual ou mérito jurídico. Compatibilidade com os testes antigos conferida na suíte integral.

## 3. Verificação e entrega

- [x] Rodada focada, suíte integral offline e revisão mecânica; não modificar teste para ocultar falha.
- [x] Atualizar exemplos/formatos/instruções; usar derivados novos para reauditar a simulação, preservando os históricos.
- [x] Conferir diff, fontes de verdade, hashes do Claude e das regras, índice e HEAD; registrar resultados na coordenação.

## Decisões

- A política de aprovação humana permanece: checagem pronta permite revisão, não aprovação automática. Os campos marcados e a avaliação jurídica pendente geram alerta/faixa mista; a decisão humana continua uma etapa distinta.
- A inspeção visual de Word está fora deste incremento e continua pendente. O confronto XML prova correspondência de conteúdo gerado, não aparência ou qualidade jurídica.
- A simulação original usa classificação jurídica baixa sem base jurídica. Corrigir somente uma cópia derivada; não reescrever o histórico nem seu QC.
- Revisão independente estática encontrou JSONs mal tipados ignorados no reconhecimento e regra sem conferência que permitia `entregavel: true`. Regressões: nove falhas e uma passagem antes das correções; 77 testes focados aprovados depois. `base_juridica_nao_conferida` mantém a referência não conferida explicitamente não entregável, sem alterar o significado de rascunho.
- Teste de alteração em estilos passou a afirmar que os bytes foram realmente alterados. Rodadas ampliadas anteriores foram interrompidas para aplicar as correções da revisão; não são contadas como verificações aprovadas. Suíte integral final: 668 aprovados, 3 ignorados em 901,83 s, offline e com temporários próprios. Ignorados dois testes de rede e marcador vazio de casos aguardando. Oito skills PRONTA na revisão mecânica; revisão independente estática das correções sem bloqueadores diretos.
