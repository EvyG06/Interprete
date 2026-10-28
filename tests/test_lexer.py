import pytest

from src.errors import LexerError
from src.lexer import tokenize
from src.tokens import TokenType as T


def pairs(source):
    return [(token.type, token.literal) for token in tokenize(source)]


def types(source):
    return [token.type for token in tokenize(source)]


def test_let_con_potencia():
    assert pairs("let x = 10 ** 2;") == [
        (T.LET, "let"),
        (T.IDENT, "x"),
        (T.ASSIGN, "="),
        (T.INT, "10"),
        (T.POW, "**"),
        (T.INT, "2"),
        (T.SEMICOLON, ";"),
        (T.EOF, ""),
    ]


@pytest.mark.parametrize("source, expected", [
    ("==", T.EQ),
    ("!=", T.NOT_EQ),
    ("<=", T.LTE),
    (">=", T.GTE),
    ("**", T.POW),
    ("&&", T.AND),
    ("||", T.OR),
])
def test_operadores_de_dos_caracteres(source, expected):
    assert pairs(source) == [(expected, source), (T.EOF, "")]


def test_coincidencia_mas_larga():
    assert types("x>=-1") == [T.IDENT, T.GTE, T.MINUS, T.INT, T.EOF]


def test_reservadas_contra_identificadores():
    assert types("let letra if iffy") == [T.LET, T.IDENT, T.IF, T.IDENT, T.EOF]


def test_identificadores_unicode_y_con_digitos():
    assert pairs("año x1 _tmp") == [
        (T.IDENT, "año"),
        (T.IDENT, "x1"),
        (T.IDENT, "_tmp"),
        (T.EOF, ""),
    ]


def test_cadena_sin_comillas_en_el_literal():
    assert pairs('"hola mundo"') == [(T.STRING, "hola mundo"), (T.EOF, "")]


def test_comentarios_se_descartan():
    assert types("5 // nada\n/ 2") == [T.INT, T.SLASH, T.INT, T.EOF]


def test_linea_y_columna():
    tokens = tokenize("let a = 1;\n  a")
    assert (tokens[0].line, tokens[0].column) == (1, 1)
    assert (tokens[5].line, tokens[5].column) == (2, 3)


@pytest.mark.parametrize("source, line, column, fragment", [
    ('let s = "abc', 1, 9, "cadena sin cerrar"),
    ("let x = 2y;", 1, 9, "dígito"),
    ("let a = 1;\nlet b = a @ 2;", 2, 11, "'@'"),
    ("a & b", 1, 3, "'&'"),
])
def test_errores_lexicos(source, line, column, fragment):
    with pytest.raises(LexerError) as info:
        tokenize(source)
    assert (info.value.line, info.value.column) == (line, column)
    assert fragment in info.value.message
