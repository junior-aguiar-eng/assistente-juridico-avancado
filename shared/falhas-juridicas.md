# Falhas jurídicas a evitar

Todas as skills tratam estas três falhas. Cada `SKILL.md` aponta para cá e acrescenta o que é específico dele.

## 1. Apoio, não conselho

O pacote organiza fontes e fatos e registra o que foi ou não verificado. Quem decide é o advogado responsável.

- O resultado é sempre **insumo para a decisão** de uma pessoa: a parte que exige juízo (tese, estratégia, redação final) aparece marcada como não verificada ou como pendência, nunca como conclusão fechada.
- `supported` quer dizer "o trecho lido apoia a proposição, conforme o registro". Não quer dizer "a tese está correta" nem "pode ser protocolada".
- A estrutura de saída carrega a passagem de bastão (estados, pendências, aprovação humana). Um aviso no rodapé não basta.

## 2. Sigilo e privilégio

- Documentos de cliente são sigilosos por padrão. A triagem registra o nível, a política de envio ao modelo e se as consultas externas podem levar termos do caso para fora da máquina (`matter.json`).
- Processo em **segredo de justiça** (CPC, art. 189: interesse público ou social, família, dados protegidos pelo direito à intimidade, arbitragem com confidencialidade comprovada) limita o acesso e a circulação dos autos. Registre se o caso está nessa situação antes de qualquer consulta externa.
- Material produzido pelo pacote (cronologia, mapa, relatório de verificação) herda o sigilo das fontes. Distribuir além do círculo autorizado é decisão do advogado.
- Na dúvida sobre sigilo de um trecho, **sinalize** (`priv: flag`): sinalizar demais se corrige na revisão; sinalizar de menos não se desfaz depois de distribuído.
- Não cole dados pessoais completos (CPF, CNPJ, cartão, conta) em relatórios: mascare ou use `[...]` no trecho.

## 3. Responsabilidade e decisão humana

- A aprovação é de uma pessoa identificada, registrada por ela em terminal interativo e ligada aos hashes do pacote ([auditar.py](../scripts/auditar.py)). Concordância entre passagens do modelo não é revisão.
- O pacote deve tornar difícil **ratificar sem decidir**: pendências, alertas e objeções ficam visíveis e precisam de resposta. "Nenhuma objeção" também é uma resposta escrita.
- Entregas para cliente, petições e contratos nunca ficam na faixa de confiança alta: exigem aprovação humana.
