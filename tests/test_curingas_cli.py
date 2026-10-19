"""CX-04: argumentos de arquivo funcionam sem expansão de curingas pelo shell."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SHELLS = [shutil.which(nome) for nome in ("powershell", "pwsh") if shutil.which(nome)]
SHELLS = SHELLS or [pytest.param(None, marks=pytest.mark.skip(reason="PowerShell não instalado"))]


@pytest.fixture
def caso(tmp_path):
    base = tmp_path / "pasta com espaços"
    for nome in ("br-triagem", "br-cronologia"):
        pasta = base / "skills" / nome
        pasta.mkdir(parents=True)
        shutil.copyfile(RAIZ / "skills" / nome / "SKILL.md", pasta / "SKILL.md")
    entrada = base / "input"
    entrada.mkdir()
    for i in (1, 2):
        (entrada / f"doc {i}.txt").write_text(f"Documento sintético número {i} para extração.", encoding="utf-8")
    return SimpleNamespace(base=base, saida=base / "extracao.json")


def argumentos(caso, script, entradas):
    extras = ["--hoje", "2026-10-19"] if script == "revisar_skill.py" else ["--no-cache", "--saida", str(caso.saida)]
    return [sys.executable, "-P", str(RAIZ / "scripts" / script), *map(str, entradas), *extras]


def executar(caso, script, entradas):
    return subprocess.run(argumentos(caso, script, entradas), cwd=caso.base, capture_output=True,
                          stdin=subprocess.DEVNULL, timeout=60)


def nomes(resultado, script):
    obj = json.loads(resultado.stdout.decode("utf-8"))
    if script == "revisar_skill.py":
        return [s["nome"] for s in obj["skills"]]
    assert all(d["status"] == "ok" for d in obj["documents"])
    return [Path(d["path"]).name for d in obj["documents"]]


@pytest.mark.parametrize("script,padrao,esperados", [
    ("revisar_skill.py", "skills/br-*/SKILL.md", ["br-cronologia", "br-triagem"]),
    ("extract.py", "input/*", ["doc 1.txt", "doc 2.txt"]),
])
def test_cli_expande_padrao_literal_e_entrega_todos_os_arquivos(caso, script, padrao, esperados):
    r = executar(caso, script, [padrao])
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    assert nomes(r, script) == esperados


@pytest.mark.parametrize("script,padrao,quantidade", [
    ("revisar_skill.py", "skills/br-cronologi?/SKILL.md", 1),
    ("revisar_skill.py", "skills/br-[ct]*/SKILL.md", 2),
    ("extract.py", "input/doc ?.txt", 2),
    ("extract.py", "input/doc [12].txt", 2),
])
def test_interrogacao_e_colchetes_funcionam_como_padrao(caso, script, padrao, quantidade):
    r = executar(caso, script, [padrao])
    assert r.returncode == 0
    assert len(nomes(r, script)) == quantidade


@pytest.mark.parametrize("entrada", ["skills/ausente*/SKILL.md", "skills/ausente/SKILL.md"])
def test_revisor_recusa_entrada_sem_arquivo_com_erro_claro(caso, entrada):
    r = executar(caso, "revisar_skill.py", [entrada])
    assert r.returncode == 2
    assert r.stdout == b""
    assert entrada in r.stderr.decode("utf-8", "replace")
    assert "Traceback" not in r.stderr.decode("utf-8", "replace")


def test_revisor_nao_ignora_padrao_sem_correspondencia_ao_lado_de_um_valido(caso):
    r = executar(caso, "revisar_skill.py", ["skills/br-*/SKILL.md", "skills/ausente*/SKILL.md"])
    assert r.returncode == 2
    assert r.stdout == b""  # não emite uma revisão parcial como sucesso
    assert "skills/ausente*/SKILL.md" in r.stderr.decode("utf-8", "replace")


@pytest.mark.parametrize("entrada", ["skills/br-triagem", "skills/br-*"])
def test_revisor_recusa_diretorio_em_vez_de_arquivo(caso, entrada):
    r = executar(caso, "revisar_skill.py", [entrada])
    assert r.returncode == 2 and r.stdout == b""
    assert "Traceback" not in r.stderr.decode("utf-8", "replace")


@pytest.mark.parametrize("script", ["revisar_skill.py", "extract.py"])
def test_caminho_literal_com_colchetes_nao_e_descartado_junto_de_outros(caso, script):
    pasta = caso.base / "[documentos] com espaços"
    pasta.mkdir()
    if script == "revisar_skill.py":
        literal = pasta / "br-triagem" / "SKILL.md"
        literal.parent.mkdir()
        shutil.copyfile(RAIZ / "skills/br-triagem/SKILL.md", literal)
        entradas = ["skills/br-cronologia/SKILL.md", literal]
        esperado = ["br-cronologia", "br-triagem"]
    else:
        literal = pasta / "nota [1].txt"
        literal.write_text("Documento literal com colchetes.", encoding="utf-8")
        entradas = ["input/doc 1.txt", literal]
        esperado = ["doc 1.txt", "nota [1].txt"]
    r = executar(caso, script, entradas)
    assert r.returncode == 0
    assert nomes(r, script) == esperado


@pytest.mark.parametrize("script", ["revisar_skill.py", "extract.py"])
def test_caminhos_explicitos_e_padrao_sobreposto_nao_duplicam_arquivos(caso, script):
    if script == "revisar_skill.py":
        entradas = ["skills/br-triagem/SKILL.md", "skills/br-*/SKILL.md",
                    caso.base / "skills/br-triagem/SKILL.md"]
        esperado = ["br-triagem", "br-cronologia"]
    else:
        entradas = ["input/doc 2.txt", "input/*", caso.base / "input/doc 2.txt"]
        esperado = ["doc 2.txt", "doc 1.txt"]
    r = executar(caso, script, entradas)
    assert r.returncode == 0
    assert nomes(r, script) == esperado


@pytest.mark.parametrize("com_valido", [False, True])
def test_extrator_mantem_relato_failed_para_padrao_sem_arquivo(caso, com_valido):
    entradas = (["input/doc 1.txt"] if com_valido else []) + ["input/ausente*.txt"]
    r = executar(caso, "extract.py", entradas)
    assert r.returncode == 2
    docs = json.loads(r.stdout.decode("utf-8"))["documents"]
    assert [d["status"] for d in docs] == (["ok"] if com_valido else []) + ["failed"]
    assert docs[-1]["path"] == "input/ausente*.txt"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("script", ["revisar_skill.py", "extract.py"])
def test_comandos_recebem_curinga_literal_no_powershell_real(caso, shell, script):
    env = dict(os.environ, CX04_PYTHON=sys.executable, CX04_SCRIPT=str(RAIZ / "scripts" / script),
               CX04_PADRAO="skills/br-*/SKILL.md" if script == "revisar_skill.py" else "input/*",
               CX04_SAIDA=str(caso.saida))
    extras = "--hoje 2026-10-19" if script == "revisar_skill.py" else "--no-cache --saida $env:CX04_SAIDA"
    comando = "& $env:CX04_PYTHON -P $env:CX04_SCRIPT $env:CX04_PADRAO " + extras + "; exit $LASTEXITCODE"
    r = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", comando], env=env, cwd=caso.base,
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=60)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    esperado = ["br-cronologia", "br-triagem"] if script == "revisar_skill.py" else ["doc 1.txt", "doc 2.txt"]
    assert nomes(r, script) == esperado


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("fonte", ["README.md", ".github/workflows/ci.yml"])
def test_comando_documentado_e_de_ci_revisa_as_oito_skills_no_powershell(shell, fonte):
    texto = (RAIZ / fonte).read_text(encoding="utf-8")
    comando = re.search(r"python scripts/revisar_skill\.py[^\n`]*", texto).group(0).split("#")[0].strip()
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    r = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command",
                        comando + " --hoje 2026-10-19; exit $LASTEXITCODE"], env=env, cwd=RAIZ,
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=60)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    obj = json.loads(r.stdout.decode("utf-8"))
    assert len(obj["skills"]) == 8
    assert obj["resumo"] == {"PRONTA": 8, "ATENCAO": 0, "PREOCUPACAO_MATERIAL": 0}
