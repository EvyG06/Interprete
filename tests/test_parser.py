import pytest

from src.ast_nodes import (
    AssignExpression,
    ForExpression,
    FunctionLiteral,
    IfExpression,
    InfixExpression,
    LetStatement,
)
from src.errors import ParserError
from src.parser import parse


def first(source):
    statement = parse(source).statements[0]
    return getattr(statement, "expression", statement)


@pytest.mark.parametrize("source, expected", [
    ("1 + 2 * 3", "(1 + (2 * 3))"),
    ("(1 + 2) * 3", "((1 + 2) * 3)"),
    ("10 - 3 - 2", "((10 - 3) - 2)"),
    ("2 ** 3 ** 2", "(2 ** (3 ** 2))"),
    ("-2 ** 2", "(-(2 ** 2))"),
    ("2 ** -1", "(2 ** (-1))"),
    ("!x == y", "((!x) == y)"),
    ("a + b < c * d", "((a + b) < (c * d))"),
    ("a || b && c == d", "(a || (b && (c == d)))"),
    ("a = b = 5", "(a = (b = 5))"),
    ("x = 1 + 2", "(x = (1 + 2))"),
    ("-a[0]", "(-(a[0]))"),
    ("f(1, 2)[0] + 1", "((f(1, 2)[0]) + 1)"),
])
def test_precedencia_y_asociatividad(source, expected):
    assert str(parse(source)) == expected


def test_let_statement():
    statement = parse("let x = 5 * 2;").statements[0]
    assert isinstance(statement, LetStatement)
    assert statement.name.name == "x"
    assert str(statement.value) == "(5 * 2)"


def test_punto_y_coma_opcional_y_vacio():
    assert len(parse("let x = 5 let y = 6;;; x").statements) == 3


def test_if_elif_else_se_anida():
    node = first("if (a) { 1 } elif (b) { 2 } else { 3 }")
    assert isinstance(node, IfExpression)
    assert isinstance(node.alternative, IfExpression)
    assert str(node.alternative.alternative) == "{ 3; }"


def test_for_completo_y_vacio():
    node = first("for (let i = 0; i < 3; i = i + 1) { x = x + i; }")
    assert isinstance(node, ForExpression)
    assert isinstance(node.init, LetStatement)
    assert str(node.condition) == "(i < 3)"
    assert isinstance(node.update, AssignExpression)
    empty = first("for (;;) { }")
    assert (empty.init, empty.condition, empty.update) == (None, None, None)


def test_funcion_y_llamada():
    node = first("function(a, b) { return a + b; }")
    assert isinstance(node, FunctionLiteral)
    assert [p.name for p in node.parameters] == ["a", "b"]
    assert str(parse("suma(1, 2 * 3)")) == "suma(1, (2 * 3))"


def test_listas_diccionarios_e_indices():
    assert str(parse("[1, [2, 3], []]")) == "[1, [2, 3], []]"
    assert str(parse('{"a": 1, 2: [3]}')) == '{"a": 1, 2: [3]}'
    assert str(parse("a[0] = b[1 + 1]")) == "((a[0]) = (b[(1 + 1)]))"


def test_logicos_son_infijos():
    node = first("a && b")
    assert isinstance(node, InfixExpression)
    assert node.operator == "&&"


@pytest.mark.parametrize("source, line, column, fragment", [
    ("let = 5;", 1, 5, "un identificador"),
    ("let x 5", 1, 7, "'='"),
    ("5 = 3", 1, 3, "no se puede asignar"),
    ("x + y = 3", 1, 7, "no se puede asignar"),
    ("(1 + 2", 1, 7, "fin del archivo"),
    ("if (x) { 1 ", 1, 8, "bloque sin cerrar"),
    ("f(1, )", 1, 6, "se esperaba una expresión"),
    ("function(a, 1) {}", 1, 13, "parámetro"),
    ('{"a" 1}', 1, 6, "':'"),
    ("if x { 1 }", 1, 4, "'('"),
    ("let x = 1;\nlet y = ;", 2, 9, "se esperaba una expresión"),
])
def test_errores_sintacticos(source, line, column, fragment):
    with pytest.raises(ParserError) as info:
        parse(source)
    assert (info.value.line, info.value.column) == (line, column)
    assert fragment in info.value.message
