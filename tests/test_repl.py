import io

from src.repl import start


def session(*lines):
    output = io.StringIO()
    start(io.StringIO("\n".join(lines) + "\n"), output)
    return output.getvalue()


def test_las_variables_persisten_entre_entradas():
    assert "7" in session("let x = 1 + 2 * 3;", "x")


def test_entrada_de_varias_lineas():
    text = session("let f = function(n) {", "  n * 2", "};", "f(21)")
    assert ".. " in text
    assert "42" in text


def test_modos_lexer_y_parser():
    text = session(":lexer", "a >= 1", ":parser", "1 + 2 * 3")
    assert "GTE" in text
    assert "(1 + (2 * 3))" in text
    assert "InfixExpression '+'" in text


def test_errores_no_cierran_la_sesion():
    text = session("1 + true", "2 + 2")
    assert "Error de ejecución" in text
    assert "4" in text


def test_comando_desconocido_y_salir():
    text = session(":foo", ":salir", "1 + 1")
    assert "comando desconocido" in text
    assert "2\n" not in text
