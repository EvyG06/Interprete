import io

import pytest

from src.errors import EvalError
from src.evaluator import Evaluator
from src.objects import Environment
from src.parser import parse


def run(source):
    output = io.StringIO()
    result = Evaluator(output).eval(parse(source), Environment())
    return result.inspect(), output.getvalue()


def value(source):
    return run(source)[0]


@pytest.mark.parametrize("source, expected", [
    ("1 + 2 * 3", "7"),
    ("(1 + 2) * 3", "9"),
    ("10 - 3 - 2", "5"),
    ("2 ** 3 ** 2", "512"),
    ("-2 ** 2", "-4"),
    ("-7 / 2", "-3"),
    ("-7 % 2", "-1"),
    ("7 % 3", "1"),
    ("3 < 5 == true", "true"),
    ('"hola" + " " + "mundo"', "hola mundo"),
    ("[1] + [2, 3]", "[1, 2, 3]"),
    ('1 == "1"', "false"),
    ("[1, 2] == [1, 2]", "true"),
    ("!true", "false"),
    ("!0", "false"),
    ("true && false || true", "true"),
])
def test_expresiones(source, expected):
    assert value(source) == expected


def test_cortocircuito_no_evalua_el_lado_derecho():
    assert value("false && no_existe") == "false"
    assert value("true || no_existe") == "true"


@pytest.mark.parametrize("source, expected", [
    ("if (1 > 2) { 10 } else { 20 }", "20"),
    ("if (false) { 10 }", "null"),
    ("if (0) { 1 } else { 2 }", "1"),
    ("let n = 5; if (n > 9) { 1 } elif (n > 3) { 2 } else { 3 }", "2"),
    ("let a = 1; if (a > 0) { if (a > 5) { 1 } else { 2 } }", "2"),
])
def test_condicionales(source, expected):
    assert value(source) == expected


def test_ciclos():
    assert value("let n = 0; while (n < 5) { n = n + 1; } n") == "5"
    assert value("let t = 0; for (let i = 1; i <= 4; i = i + 1) { t = t + i; } t") == "10"
    assert value("let f = function() { while (true) { return 7; } }; f()") == "7"


def test_funciones_y_recursion():
    assert value("let suma = function(a, b) { return a + b; }; suma(2, 3)") == "5"
    assert value("let f = function(x) { x * 2 }; f(21)") == "42"
    fib = "let fib = function(n) { if (n <= 1) { return n; } return fib(n - 1) + fib(n - 2); };"
    assert value(fib + " fib(15)") == "610"
    hanoi = (
        "let hanoi = function(n, o, d, a) { if (n == 0) { return []; } "
        "return hanoi(n - 1, o, a, d) + [[o, d]] + hanoi(n - 1, a, d, o); };"
    )
    assert value(hanoi + ' len(hanoi(3, "A", "C", "B"))') == "7"


def test_recursion_profunda_soportada():
    contar = "let f = function(n) { if (n == 0) { return 0; } return 1 + f(n - 1); };"
    assert value(contar + " f(1000)") == "1000"


@pytest.mark.parametrize("source, expected", [
    ("let x = 1; let g = function() { let x = 50; x }; g() + x", "51"),
    ("let x = 10; let f = function(x) { x = 99; x }; f(1) + x", "109"),
    ("let x = 10; let f = function() { x = x + 1; }; f(); f(); x", "12"),
    ("let x = 1; let f = function() { x }; let g = function() { let x = 2; f() }; g()", "1"),
])
def test_ambitos(source, expected):
    assert value(source) == expected


def test_closures():
    source = (
        "let contador = function() { let n = 0; function() { n = n + 1; n } };"
        "let c = contador(); c(); c(); c()"
    )
    assert value(source) == "3"
    assert value("let suma = function(a) { function(b) { a + b } }; suma(5)(3)") == "8"


def test_listas_y_diccionarios():
    assert value("let a = [1, 2, 3]; a[1] = 20; a") == "[1, 20, 3]"
    assert value("[1, 2][5]") == "null"
    assert value('let h = {"a": 1, 2: true}; h["b"] = [3]; h') == '{"a": 1, 2: true, "b": [3]}'
    assert value('{"a": 1}["z"]') == "null"
    assert value("let m = [[1, 2], [3, 4]]; m[1][0] = 9; m") == "[[1, 2], [9, 4]]"


def test_funciones_integradas():
    assert value('len("hola") + len([1, 2]) + len({1: 2})') == "7"
    assert value('int("42") + int(true)') == "43"
    assert value('str(5) + "!"') == "5!"
    assert value('[type(1), type("a"), type([]), type({}), type(len)]') == (
        '["INTEGER", "STRING", "ARRAY", "HASH", "BUILTIN"]'
    )
    assert value("let a = []; push(a, 1); push(a, 2); a") == "[1, 2]"
    assert run('print("hola", 1, ["a"])') == ("null", 'hola 1 ["a"]\n')


@pytest.mark.parametrize("source, line, column, fragment", [
    ('1 + "a"', 1, 3, "tipos incompatibles"),
    ("5 / 0", 1, 3, "división por cero"),
    ("5 % 0", 1, 3, "división por cero"),
    ("y", 1, 1, "variable no definida"),
    ("y = 3", 1, 1, "variable no definida"),
    ("let f = function(a) { a }; f(1, 2)", 1, 28, "argumento"),
    ("5(1)", 1, 1, "no es una función"),
    ("len(1)", 1, 1, "len no admite"),
    ('int("12a")', 1, 1, "no se puede convertir"),
    ('[1]["a"]', 1, 4, "debe ser INTEGER"),
    ("{[1]: 2}", 1, 2, "clave"),
    ("let a = [1]; a[3] = 1", 1, 15, "fuera de rango"),
    ('-"a"', 1, 1, "operador -"),
    ("2 ** -1", 1, 3, "exponente negativo"),
    ("5[0]", 1, 2, "no se puede indexar"),
    ("let a = 1;\nlet b = a + true;", 2, 11, "tipos incompatibles"),
])
def test_errores_de_ejecucion(source, line, column, fragment):
    with pytest.raises(EvalError) as info:
        run(source)
    assert (info.value.line, info.value.column) == (line, column)
    assert fragment in info.value.message


def test_recursion_infinita_es_error_del_lenguaje():
    with pytest.raises(EvalError) as info:
        run("let f = function(n) { f(n + 1) };\nf(0)")
    assert info.value.line == 2
    assert "recursión" in info.value.message
