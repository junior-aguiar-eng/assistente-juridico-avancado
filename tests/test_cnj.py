import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import cnj  # noqa: E402


def _dv_modular(seq, ano, seg, tr, org):
    """Implementação independente: resto calculado por blocos (sem inteiro grande)."""
    r = int(seq) % 97
    r = int(f"{r:02d}{ano}{seg}{tr}") % 97
    r = int(f"{r:02d}{org}00") % 97
    return f"{98 - r:02d}"


def test_caso_sintetico_documentado():
    # base 0002150 2023 8 26 0024: DV esperado 76 (e não 26)
    assert cnj.calcular_dv("0002150", "2023", "8", "26", "0024") == "76"
    assert cnj.validar("0002150-76.2023.8.26.0024") == (True, "ok")
    assert cnj.validar("0002150-26.2023.8.26.0024")[0] is False


def test_forma_corrida_e_formatada_equivalem():
    assert cnj.validar("00021507620238260024")[0] is True
    assert cnj.parse("00021507620238260024").formatado == "0002150-76.2023.8.26.0024"


def test_estrutura_invalida():
    for ruim in ["", "123", "0002150-76.2023.8.26.002", "abc", "0002150-76.2023.8.26.0024 x"]:
        assert cnj.validar(ruim)[0] is False


def test_segmento_zero_rejeitado():
    dv = cnj.calcular_dv("0000001", "2020", "0", "01", "0001")
    assert cnj.validar(f"0000001-{dv}.2020.0.01.0001")[0] is False


def test_propriedade_resto_um_e_algoritmo_independente():
    rng = random.Random(42)
    for _ in range(2000):
        seq = f"{rng.randrange(10**7):07d}"
        ano = str(rng.randrange(1990, 2031))
        seg = str(rng.randrange(1, 10))
        tr = f"{rng.randrange(100):02d}"
        org = f"{rng.randrange(10000):04d}"
        dv = cnj.calcular_dv(seq, ano, seg, tr, org)
        assert dv == _dv_modular(seq, ano, seg, tr, org)
        assert int(f"{seq}{ano}{seg}{tr}{org}{dv}") % 97 == 1
        assert cnj.validar(f"{seq}-{dv}.{ano}.{seg}.{tr}.{org}")[0] is True


def test_dv_errado_e_detectado():
    ok = "0002150-76.2023.8.26.0024"
    for dv in ("75", "77", "00", "26"):
        assert cnj.validar(ok.replace("-76.", f"-{dv}."))[0] is False
