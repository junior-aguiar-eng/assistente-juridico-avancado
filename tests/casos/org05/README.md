# Corpus da ORG-05

Duas novas fixtures públicas do TJMG, obtidas da fonte oficial após congelar o produto em `a3848b1`. Os bytes, URLs, data de coleta e SHA-256 estão em [proveniencia.json](proveniencia.json). Não substituem R07/TJMG, R10/Picos ou os privados ORG-R07-PRIVADO/ORG-R10-PRIVADO.

| ID | Unidade | Páginas | Referência técnica proposta |
|---|---|---|---|
| ORG05-P01 | Apelação Cível 1.0000.25.012630-7/001 | 16 | Uma peça acórdão, páginas 1–16 |
| ORG05-P02 | Agravo de Instrumento-Cv 1.0000.24.455292-3/001 | 14 | Uma peça acórdão, páginas 1–14 |

Os gabaritos foram propostos por leitura do PDF e revisados por outro agente; em 22/10/2026, **o titular confirmou a revisão e aprovação de P01/P02**. O [registro da conferência](conferencia-humana.json) vincula a declaração aos bytes dos PDFs e aos gabaritos; o [manifesto](manifesto.json) identifica o revisor pelo papel e pela participação nesta conversa, sem presumir identidade civil ou assinatura externa. ACÓRDÃO/VOTO e transcrições são seções internas, sem transformar precedentes citados em originais fornecidos. A confirmação é dos gabaritos estruturais; os inventários gerados continuam propostos, sem eventos humanos de uso material. Não houve aprovação do mérito jurídico, das regras ou dos outros casos.

O [manifesto](manifesto.json) também inclui R07 público como desenvolvimento e o ofício R10/Picos com/sem OCR. São cinco observações de quatro unidades: três processos judiciais e um documento administrativo; duas leituras do ofício não criam dois processos. O ofício está fora da taxonomia jurídica atual e sua referência usa `nao_identificada`, sem improvisar nova classe.

A [rodada congelada](../../../docs/resultado-org05-congelado.json) preserva a avaliação inicial, sem ajuste aos casos. As correções posteriores de identidade multidocumento e identificação do relatório redline são verificadas no manifesto atual, marcado `regressao_pos_avaliacao`. Repetir os mesmos processos após essas correções não é nova avaliação independente. O detector de fronteiras/tipos não foi ajustado para reconhecer esses acórdãos.

Execução offline, em destino externo novo (o comando recusa sobrescrever pasta existente):

```powershell
$env:JURIS_REDE = '0'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
python scripts/avaliar_pecas.py --manifesto tests/casos/org05/manifesto.json --saida 'C:/caminho/externo/nova-avaliacao-org05'
```

O avaliador verifica os hashes de produto e insumos, não baixa arquivos, não altera originais e não confirma propostas. O manifesto atual declara `produto_normalizacao: lf`: somente o código tem CRLF convertido a LF para comparação entre checkouts Windows/Linux. PDFs, extrações, inventários e demais insumos mantêm hashes de bytes exatos; a rodada inicial preservada usou os bytes locais do código. Saídas por caso incluem extração, inventário, facts, cronologia e QC quando há fragmento atribuível. OCR sem peça atribuída registra o fluxo de uso como não executado, sem inventar uma peça para passar. Amostras textuais recuperadas não medem fidelidade integral ou taxa de erro de caracteres. Os resultados resumidos não transcrevem nomes ou texto das peças; derivados completos ficam no destino externo.
