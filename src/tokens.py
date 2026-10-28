from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    EOF = "EOF"
    IDENT = "IDENT"
    INT = "INT"
    STRING = "STRING"

    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    BANG = "!"
    ASTERISK = "*"
    SLASH = "/"
    MOD = "%"
    POW = "**"

    EQ = "=="
    NOT_EQ = "!="
    LT = "<"
    GT = ">"
    LTE = "<="
    GTE = ">="
    AND = "&&"
    OR = "||"

    COMMA = ","
    SEMICOLON = ";"
    COLON = ":"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"

    LET = "let"
    FUNCTION = "function"
    TRUE = "true"
    FALSE = "false"
    IF = "if"
    ELIF = "elif"
    ELSE = "else"
    RETURN = "return"
    WHILE = "while"
    FOR = "for"


@dataclass(frozen=True)
class Token:
    type: TokenType
    literal: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}\t{self.type.name}\t{self.literal!r}"


KEYWORDS = {
    "let": TokenType.LET,
    "function": TokenType.FUNCTION,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "return": TokenType.RETURN,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
}

TWO_CHAR_TOKENS = {
    "==": TokenType.EQ,
    "!=": TokenType.NOT_EQ,
    "<=": TokenType.LTE,
    ">=": TokenType.GTE,
    "**": TokenType.POW,
    "&&": TokenType.AND,
    "||": TokenType.OR,
}

ONE_CHAR_TOKENS = {
    "=": TokenType.ASSIGN,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "!": TokenType.BANG,
    "*": TokenType.ASTERISK,
    "/": TokenType.SLASH,
    "%": TokenType.MOD,
    "<": TokenType.LT,
    ">": TokenType.GT,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    ":": TokenType.COLON,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
}


def lookup_ident(word: str) -> TokenType:
    return KEYWORDS.get(word, TokenType.IDENT)
