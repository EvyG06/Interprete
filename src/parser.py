from enum import IntEnum

from .ast_nodes import (
    ArrayLiteral,
    AssignExpression,
    BlockStatement,
    BooleanLiteral,
    CallExpression,
    Expression,
    ExpressionStatement,
    ForExpression,
    FunctionLiteral,
    HashLiteral,
    Identifier,
    IfExpression,
    IndexExpression,
    InfixExpression,
    IntegerLiteral,
    LetStatement,
    PrefixExpression,
    Program,
    ReturnStatement,
    Statement,
    StringLiteral,
    WhileExpression,
)
from .errors import ParserError
from .lexer import Lexer
from .tokens import Token, TokenType as T


class Precedence(IntEnum):
    LOWEST = 1
    ASSIGNMENT = 2
    OR = 3
    AND = 4
    EQUALITY = 5
    COMPARISON = 6
    TERM = 7
    FACTOR = 8
    UNARY = 9
    POWER = 10
    POSTFIX = 11


PRECEDENCES = {
    T.ASSIGN: Precedence.ASSIGNMENT,
    T.OR: Precedence.OR,
    T.AND: Precedence.AND,
    T.EQ: Precedence.EQUALITY,
    T.NOT_EQ: Precedence.EQUALITY,
    T.LT: Precedence.COMPARISON,
    T.GT: Precedence.COMPARISON,
    T.LTE: Precedence.COMPARISON,
    T.GTE: Precedence.COMPARISON,
    T.PLUS: Precedence.TERM,
    T.MINUS: Precedence.TERM,
    T.ASTERISK: Precedence.FACTOR,
    T.SLASH: Precedence.FACTOR,
    T.MOD: Precedence.FACTOR,
    T.POW: Precedence.POWER,
    T.LPAREN: Precedence.POSTFIX,
    T.LBRACKET: Precedence.POSTFIX,
}

BINARY_OPERATORS = [
    T.OR, T.AND, T.EQ, T.NOT_EQ, T.LT, T.GT, T.LTE, T.GTE,
    T.PLUS, T.MINUS, T.ASTERISK, T.SLASH, T.MOD, T.POW,
]

RIGHT_ASSOCIATIVE = {T.POW}


def describe(token: Token) -> str:
    return "fin del archivo" if token.type == T.EOF else repr(token.literal)


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.cur_token = lexer.next_token()
        self.peek_token = lexer.next_token()

        self.prefix_fns = {
            T.IDENT: self.parse_identifier,
            T.INT: self.parse_integer_literal,
            T.STRING: self.parse_string_literal,
            T.TRUE: self.parse_boolean,
            T.FALSE: self.parse_boolean,
            T.MINUS: self.parse_prefix_expression,
            T.BANG: self.parse_prefix_expression,
            T.LPAREN: self.parse_grouped_expression,
            T.LBRACKET: self.parse_array_literal,
            T.LBRACE: self.parse_hash_literal,
            T.IF: self.parse_if_expression,
            T.WHILE: self.parse_while_expression,
            T.FOR: self.parse_for_expression,
            T.FUNCTION: self.parse_function_literal,
        }
        self.infix_fns = {token_type: self.parse_infix_expression for token_type in BINARY_OPERATORS}
        self.infix_fns[T.ASSIGN] = self.parse_assign_expression
        self.infix_fns[T.LPAREN] = self.parse_call_expression
        self.infix_fns[T.LBRACKET] = self.parse_index_expression

    # ---------- utilidades ----------

    def next_token(self) -> None:
        self.cur_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def expect_peek(self, token_type: T) -> None:
        if self.peek_token.type != token_type:
            expected = "un identificador" if token_type == T.IDENT else repr(token_type.value)
            raise ParserError(
                f"se esperaba {expected} y llegó {describe(self.peek_token)}",
                self.peek_token.line,
                self.peek_token.column,
            )
        self.next_token()

    def peek_precedence(self) -> int:
        return PRECEDENCES.get(self.peek_token.type, Precedence.LOWEST)

    # ---------- sentencias ----------

    def parse_program(self) -> Program:
        token = self.cur_token
        return Program(token, self.parse_statements_until(T.EOF))

    def parse_statements_until(self, end: T) -> list[Statement]:
        statements = []
        while self.cur_token.type not in (end, T.EOF):
            if self.cur_token.type != T.SEMICOLON:
                statements.append(self.parse_statement())
            self.next_token()
        return statements

    def parse_statement(self) -> Statement:
        match self.cur_token.type:
            case T.LET:
                statement = self.parse_let_statement()
            case T.RETURN:
                statement = self.parse_return_statement()
            case _:
                statement = ExpressionStatement(self.cur_token, self.parse_expression(Precedence.LOWEST))
        if self.peek_token.type == T.SEMICOLON:
            self.next_token()
        return statement

    def parse_let_statement(self) -> LetStatement:
        token = self.cur_token
        self.expect_peek(T.IDENT)
        name = Identifier(self.cur_token, self.cur_token.literal)
        self.expect_peek(T.ASSIGN)
        self.next_token()
        return LetStatement(token, name, self.parse_expression(Precedence.LOWEST))

    def parse_return_statement(self) -> ReturnStatement:
        token = self.cur_token
        self.next_token()
        return ReturnStatement(token, self.parse_expression(Precedence.LOWEST))

    def parse_block(self) -> BlockStatement:
        self.expect_peek(T.LBRACE)
        token = self.cur_token
        self.next_token()
        statements = self.parse_statements_until(T.RBRACE)
        if self.cur_token.type == T.EOF:
            raise ParserError("bloque sin cerrar, falta '}'", token.line, token.column)
        return BlockStatement(token, statements)

    # ---------- núcleo de Pratt ----------

    def parse_expression(self, precedence: int) -> Expression:
        prefix = self.prefix_fns.get(self.cur_token.type)
        if prefix is None:
            raise ParserError(
                f"se esperaba una expresión y llegó {describe(self.cur_token)}",
                self.cur_token.line,
                self.cur_token.column,
            )
        left = prefix()
        while precedence < self.peek_precedence():
            self.next_token()
            left = self.infix_fns[self.cur_token.type](left)
        return left

    # ---------- funciones prefijas ----------

    def parse_identifier(self) -> Expression:
        return Identifier(self.cur_token, self.cur_token.literal)

    def parse_integer_literal(self) -> Expression:
        return IntegerLiteral(self.cur_token, int(self.cur_token.literal))

    def parse_string_literal(self) -> Expression:
        return StringLiteral(self.cur_token, self.cur_token.literal)

    def parse_boolean(self) -> Expression:
        return BooleanLiteral(self.cur_token, self.cur_token.type == T.TRUE)

    def parse_prefix_expression(self) -> Expression:
        token = self.cur_token
        self.next_token()
        return PrefixExpression(token, token.literal, self.parse_expression(Precedence.UNARY))

    def parse_grouped_expression(self) -> Expression:
        self.next_token()
        expression = self.parse_expression(Precedence.LOWEST)
        self.expect_peek(T.RPAREN)
        return expression

    def parse_array_literal(self) -> Expression:
        token = self.cur_token
        return ArrayLiteral(token, self.parse_list(T.RBRACKET, self.parse_list_item))

    def parse_hash_literal(self) -> Expression:
        token = self.cur_token
        return HashLiteral(token, self.parse_list(T.RBRACE, self.parse_pair))

    def parse_if_expression(self) -> Expression:
        token = self.cur_token
        condition = self.parse_condition()
        consequence = self.parse_block()
        alternative = None
        if self.peek_token.type == T.ELIF:
            self.next_token()
            alternative = self.parse_if_expression()
        elif self.peek_token.type == T.ELSE:
            self.next_token()
            alternative = self.parse_block()
        return IfExpression(token, condition, consequence, alternative)

    def parse_while_expression(self) -> Expression:
        token = self.cur_token
        condition = self.parse_condition()
        return WhileExpression(token, condition, self.parse_block())

    def parse_for_expression(self) -> Expression:
        token = self.cur_token
        self.expect_peek(T.LPAREN)
        init = condition = update = None

        self.next_token()
        if self.cur_token.type != T.SEMICOLON:
            if self.cur_token.type == T.LET:
                init = self.parse_let_statement()
            else:
                init = self.parse_expression(Precedence.LOWEST)
            self.expect_peek(T.SEMICOLON)

        self.next_token()
        if self.cur_token.type != T.SEMICOLON:
            condition = self.parse_expression(Precedence.LOWEST)
            self.expect_peek(T.SEMICOLON)

        self.next_token()
        if self.cur_token.type != T.RPAREN:
            update = self.parse_expression(Precedence.LOWEST)
            self.expect_peek(T.RPAREN)

        return ForExpression(token, init, condition, update, self.parse_block())

    def parse_function_literal(self) -> Expression:
        token = self.cur_token
        self.expect_peek(T.LPAREN)
        parameters = self.parse_list(T.RPAREN, self.parse_parameter)
        return FunctionLiteral(token, parameters, self.parse_block())

    # ---------- funciones infijas ----------

    def parse_infix_expression(self, left: Expression) -> Expression:
        token = self.cur_token
        precedence = PRECEDENCES[token.type]
        if token.type in RIGHT_ASSOCIATIVE:
            precedence -= 1
        self.next_token()
        return InfixExpression(token, left, token.literal, self.parse_expression(precedence))

    def parse_assign_expression(self, target: Expression) -> Expression:
        token = self.cur_token
        if not isinstance(target, (Identifier, IndexExpression)):
            raise ParserError(f"no se puede asignar a {target}", token.line, token.column)
        self.next_token()
        return AssignExpression(token, target, self.parse_expression(Precedence.ASSIGNMENT - 1))

    def parse_call_expression(self, function: Expression) -> Expression:
        token = self.cur_token
        return CallExpression(token, function, self.parse_list(T.RPAREN, self.parse_list_item))

    def parse_index_expression(self, left: Expression) -> Expression:
        token = self.cur_token
        self.next_token()
        index = self.parse_expression(Precedence.LOWEST)
        self.expect_peek(T.RBRACKET)
        return IndexExpression(token, left, index)

    # ---------- piezas compartidas ----------

    def parse_condition(self) -> Expression:
        self.expect_peek(T.LPAREN)
        self.next_token()
        condition = self.parse_expression(Precedence.LOWEST)
        self.expect_peek(T.RPAREN)
        return condition

    def parse_list(self, end: T, parse_item) -> list:
        items = []
        if self.peek_token.type == end:
            self.next_token()
            return items
        self.next_token()
        items.append(parse_item())
        while self.peek_token.type == T.COMMA:
            self.next_token()
            self.next_token()
            items.append(parse_item())
        self.expect_peek(end)
        return items

    def parse_list_item(self) -> Expression:
        return self.parse_expression(Precedence.LOWEST)

    def parse_pair(self) -> tuple[Expression, Expression]:
        key = self.parse_expression(Precedence.LOWEST)
        self.expect_peek(T.COLON)
        self.next_token()
        return key, self.parse_expression(Precedence.LOWEST)

    def parse_parameter(self) -> Identifier:
        if self.cur_token.type != T.IDENT:
            raise ParserError(
                f"se esperaba un nombre de parámetro y llegó {describe(self.cur_token)}",
                self.cur_token.line,
                self.cur_token.column,
            )
        return Identifier(self.cur_token, self.cur_token.literal)


def parse(source: str) -> Program:
    return Parser(Lexer(source)).parse_program()
