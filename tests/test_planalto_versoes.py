"""CX-03: versões do Planalto sobrevivem a novos downloads e falhas de conversão."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import fontes  # noqa: E402

URL = "https://www.planalto.gov.br/ccivil_03/leis/lei_compilada.htm"
A = "Art. 1. Texto original da fixture.\n"
B = "Art. 1. Texto atualizado da fixture.\n"
C = "Art. 1. Terceira redação da fixture.\n"


@pytest.fixture
def caso(tmp_path, monkeypatch):
    fetch = tmp_path / "fetch_controlado.py"
    controle = fetch.with_suffix(".json")
    fetch.write_text(
        "import json, sys\nfrom pathlib import Path\n"
        "c = json.loads(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))\n"
        "if c['gravar']:\n    Path(sys.argv[2]).write_bytes(c['texto'].encode('utf-8'))\n"
        "sys.exit(c['codigo'])\n", encoding="utf-8")
    destino, registro = tmp_path / "fontes", tmp_path / "registro.json"
    # Mesmo instante: versões não podem depender da resolução do relógio.
    monkeypatch.setattr(fontes, "_agora", lambda: "2026-10-19T12:00:00+00:00")

    def preparar(texto, codigo=0, gravar=True):
        controle.write_text(json.dumps({"texto": texto, "codigo": codigo, "gravar": gravar}), encoding="utf-8")

    def baixar(texto, codigo=0, gravar=True, com_registro=True):
        preparar(texto, codigo, gravar)
        return fontes.baixar(URL, destino, registro if com_registro else None, nome="lei.md", fetch_oficial=fetch)

    return SimpleNamespace(baixar=baixar, preparar=preparar, destino=destino, registro=registro, fetch=fetch)


def registros(caso):
    return json.loads(caso.registro.read_text(encoding="utf-8"))["fontes"]


def test_downloads_diferentes_preservam_todas_as_versoes_e_seus_registros(caso):
    eventos = [caso.baixar(texto) for texto in (A, B, C)]
    assert all(e["status"] == "lida" for e in eventos)
    assert len({e["local_file"] for e in eventos}) == 3
    assert registros(caso) == eventos
    for texto, e in zip((A, B, C), eventos):
        dados = texto.encode("utf-8")
        assert Path(e["local_file"]).read_bytes() == dados
        assert e["sha256"] == hashlib.sha256(dados).hexdigest()
        assert e["source_id"] == "src-" + e["sha256"][:12]
        assert e["bytes"] == len(dados)
        assert Path(e["local_file"]).parent == caso.destino
    assert len(list(caso.destino.iterdir())) == 3  # sem arquivos temporários publicados


@pytest.mark.parametrize("com_registro", [True, False])
def test_conteudo_identico_reutiliza_arquivo_sem_reescrever(caso, com_registro):
    a = caso.baixar(A, com_registro=com_registro)
    path = Path(a["local_file"])
    os.utime(path, (1_700_000_000, 1_700_000_000))
    antes = path.stat().st_mtime_ns
    b = caso.baixar(A, com_registro=com_registro)
    assert a["local_file"] == b["local_file"]
    assert path.stat().st_mtime_ns == antes
    assert list(caso.destino.iterdir()) == [path]
    if com_registro:
        assert len(registros(caso)) == 2


def test_repetir_versao_nova_ou_retornar_a_antiga_reutiliza_os_caminhos(caso):
    a, b = caso.baixar(A), caso.baixar(B)
    assert a["local_file"] != b["local_file"]
    path = Path(b["local_file"])
    os.utime(path, (1_700_000_000, 1_700_000_000))
    antes = path.stat().st_mtime_ns
    assert caso.baixar(B)["local_file"] == b["local_file"]
    assert path.stat().st_mtime_ns == antes
    assert caso.baixar(A)["local_file"] == a["local_file"]
    assert len(list(caso.destino.iterdir())) == 2
    for e in registros(caso):
        assert hashlib.sha256(Path(e["local_file"]).read_bytes()).hexdigest() == e["sha256"]


def test_arquivo_anterior_sem_registro_tambem_e_preservado(caso):
    caso.destino.mkdir()
    antigo = caso.destino / "lei.md"
    antigo.write_text(A, encoding="utf-8")
    e = caso.baixar(B)
    assert antigo.read_text(encoding="utf-8") == A
    assert Path(e["local_file"]) != antigo
    assert Path(e["local_file"]).read_text(encoding="utf-8") == B


@pytest.mark.parametrize("codigo,gravar", [(1, True), (0, False), (1, False)])
def test_conversao_falha_ou_sem_saida_nao_altera_a_versao_antiga(caso, codigo, gravar):
    antigo = caso.baixar(A)
    falha = caso.baixar("Resultado incompleto.", codigo=codigo, gravar=gravar)
    assert falha["status"] == "source_missing"
    assert "local_file" not in falha
    assert Path(antigo["local_file"]).read_text(encoding="utf-8") == A
    assert list(caso.destino.iterdir()) == [Path(antigo["local_file"])]
    assert registros(caso) == [antigo, falha]


def test_timeout_depois_de_saida_parcial_nao_toca_no_arquivo_antigo(caso, monkeypatch):
    antigo = caso.baixar(A)

    def expirar(args, **kwargs):
        Path(args[3]).write_text("Resultado parcial.", encoding="utf-8")
        raise subprocess.TimeoutExpired(args, 180)

    monkeypatch.setattr(fontes.subprocess, "run", expirar)
    e = caso.baixar(B)
    assert e["status"] == "source_missing" and "180 s" in e["motivo"]
    assert Path(antigo["local_file"]).read_text(encoding="utf-8") == A
    assert list(caso.destino.iterdir()) == [Path(antigo["local_file"])]


@pytest.mark.parametrize("ocupados", [1, 2])
def test_colisao_no_nome_versionado_preserva_arquivos_existentes(caso, ocupados):
    antigo = caso.baixar(A)
    prefixo = hashlib.sha256(B.encode("utf-8")).hexdigest()[:8]
    anteriores = {Path(antigo["local_file"]): A.encode("utf-8")}
    for i in range(1, ocupados + 1):
        path = caso.destino / f"lei-{prefixo}{'-' + str(i) if i > 1 else ''}.md"
        dados = f"Arquivo anterior com nome ocupado {i}.".encode("utf-8")
        path.write_bytes(dados)
        anteriores[path] = dados
    novo = caso.baixar(B)
    assert novo["status"] == "lida"
    assert Path(novo["local_file"]) not in anteriores
    assert Path(novo["local_file"]).read_text(encoding="utf-8") == B
    assert all(path.read_bytes() == dados for path, dados in anteriores.items())


def test_primeira_conversao_sem_saida_nao_registra_fonte_lida(caso):
    e = caso.baixar(A, gravar=False)
    assert e["status"] == "source_missing"
    assert not list(caso.destino.iterdir())
    assert registros(caso) == [e]


def test_erro_ao_executar_conversor_preserva_versao_e_registra_falha(caso, monkeypatch):
    antigo = caso.baixar(A)

    def falhar(*args, **kwargs):
        raise OSError("Falha controlada de execução.")

    monkeypatch.setattr(fontes.subprocess, "run", falhar)
    e = caso.baixar(B)
    assert e["status"] == "source_missing"
    assert Path(antigo["local_file"]).read_text(encoding="utf-8") == A
    assert list(caso.destino.iterdir()) == [Path(antigo["local_file"])]
    assert registros(caso) == [antigo, e]


def test_comando_baixar_tambem_preserva_versoes(caso, monkeypatch, capfd):
    monkeypatch.setattr(fontes, "FETCH_OFICIAL", caso.fetch)
    args = ["baixar", URL, "--destino", str(caso.destino), "--registro", str(caso.registro), "--nome", "lei.md"]
    caso.preparar(A)
    assert fontes.main(args) == 0
    a = json.loads(capfd.readouterr().out)
    caso.preparar(B)
    assert fontes.main(args) == 0
    b = json.loads(capfd.readouterr().out)
    assert a["local_file"] != b["local_file"]
    assert Path(a["local_file"]).read_text(encoding="utf-8") == A
    assert Path(b["local_file"]).read_text(encoding="utf-8") == B
