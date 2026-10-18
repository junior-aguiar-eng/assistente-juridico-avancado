"""Gatilhos das skills: pedidos reais de usuário contra as descrições (aproximação lexical, não é teste do modelo)."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import revisar_skill as rs  # noqa: E402

SKILLS = sorted((RAIZ / "skills").glob("*/SKILL.md"))

PEDIDOS = {
    "br-triagem": [
        "vamos começar um caso novo, tenho os documentos do cliente",
        "abrir o caso e registrar o papel do cliente e o sigilo",
        "confira os números de processo e os dados pessoais dos documentos recebidos",
    ],
    "br-mapear-autos": [
        "mapear o caso a partir dos autos",
        "organizar os fatos e provas dos documentos do processo",
        "o que os autos dizem sobre o contrato",
    ],
    "br-cronologia": [
        "monte a linha do tempo dos fatos",
        "preciso da cronologia do caso",
        "faça a exposição de fatos em ordem",
    ],
    "br-pesquisa-juridica": [
        "pesquise a tese sobre prescrição",
        "ache o precedente do STJ sobre o tema",
        "qual a lei aplicável a esse contrato",
    ],
    "br-verificar-citacoes": [
        "confira essas citações antes de protocolar",
        "verifique se o acórdão realmente apoia essa tese",
        "as referências de jurisprudência da minha peça estão certas",
    ],
    "br-auditar-entrega": [
        "audite o pacote antes de entregar ao cliente",
        "revisar antes de entregar e liberar o trabalho",
        "faça o gate final antes da entrega",
    ],
}
CASOS = [(skill, pedido) for skill, ps in PEDIDOS.items() for pedido in ps]


@pytest.mark.parametrize("skill,pedido", CASOS)
def test_pedido_cai_na_skill_certa_sem_empate(skill, pedido):
    r = rs.casar_pedido(pedido, SKILLS)
    assert r[0]["skill"] == skill, r[:3]
    assert r[0]["pontos"] > r[1]["pontos"], f"empate entre {r[0]['skill']} e {r[1]['skill']}"


def test_pedido_fora_do_escopo_nao_tem_dono():
    r = rs.casar_pedido("escreva um poema sobre o mar e as ondas", SKILLS)
    assert r[0]["pontos"] == 0


def test_pedidos_que_cada_skill_manda_para_outra_nao_sao_atraidos_por_ela():
    # "Não use para ...": o que a descrição exclui não deve atrair o pedido
    assert rs.casar_pedido("calcular o prazo processual do recurso", SKILLS)[0]["pontos"] <= 1
    nao_cronologia = rs.casar_pedido("extraia os fatos dos documentos do processo", SKILLS)
    assert "br-mapear-autos" in [x["skill"] for x in nao_cronologia[:2]]  # a cronologia não atrai o pedido de extrair fatos
    assert nao_cronologia[0]["skill"] != "br-cronologia"
