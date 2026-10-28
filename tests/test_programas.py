import io
from pathlib import Path

import pytest

from src.repl import run_file

CASES = sorted((Path(__file__).parent / "casos").glob("*.ssg"))
EXAMPLES = sorted((Path(__file__).parent.parent / "examples").glob("*.ssg"))


@pytest.mark.parametrize("program", CASES, ids=lambda path: path.stem)
def test_caso_con_resultado_esperado(program):
    output = io.StringIO()
    exit_code = run_file(program, output, output)
    expected = program.with_suffix(".esperado").read_text(encoding="utf-8")
    assert output.getvalue() == expected
    assert exit_code == (1 if program.stem.startswith("error") else 0)


@pytest.mark.parametrize("program", EXAMPLES, ids=lambda path: path.stem)
def test_ejemplo_se_ejecuta_sin_errores(program):
    output = io.StringIO()
    assert run_file(program, output, output) == 0, output.getvalue()
