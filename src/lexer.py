from .errors import LexerError
from .tokens import ONE_CHAR_TOKENS, TWO_CHAR_TOKENS, Token, TokenType, lookup_ident

EOF_CHAR = "\0"
WHITESPACE = " \t\r\n"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.read_position = 0
        self.ch = EOF_CHAR
        self.line = 1
        self.column = 0
        self.read_char()

    def read_char(self) -> None:
        if self.ch == "\n":
            self.line += 1
            self.column = 0
        if self.read_position >= len(self.source):
            self.ch = EOF_CHAR
        else:
            self.ch = self.source[self.read_position]
        self.position = self.read_position
        self.read_position += 1
        self.column += 1

    def peek_char(self) -> str:
        if self.read_position >= len(self.source):
            return EOF_CHAR
        return self.source[self.read_position]

    def next_token(self) -> Token:
        self.skip_whitespace_and_comments()
        line, column = self.line, self.column

        if self.ch == EOF_CHAR:
            return Token(TokenType.EOF, "", line, column)

        two = self.ch + self.peek_char()
        if two in TWO_CHAR_TOKENS:
            self.read_char()
            self.read_char()
            return Token(TWO_CHAR_TOKENS[two], two, line, column)

        if self.ch in ONE_CHAR_TOKENS:
            ch = self.ch
            self.read_char()
            return Token(ONE_CHAR_TOKENS[ch], ch, line, column)

        if self.ch == '"':
            return Token(TokenType.STRING, self.read_string(), line, column)

        if is_letter(self.ch):
            word = self.read_identifier()
            return Token(lookup_ident(word), word, line, column)

        if is_digit(self.ch):
            return Token(TokenType.INT, self.read_number(), line, column)

        raise LexerError(f"carácter no reconocido {self.ch!r}", line, column)

    def skip_whitespace_and_comments(self) -> None:
        while True:
            if self.ch in WHITESPACE:
                self.read_char()
            elif self.ch == "/" and self.peek_char() == "/":
                while self.ch not in ("\n", EOF_CHAR):
                    self.read_char()
            else:
                return

    def read_identifier(self) -> str:
        start = self.position
        while is_letter(self.ch) or is_digit(self.ch):
            self.read_char()
        return self.source[start:self.position]

    def read_number(self) -> str:
        start, line, column = self.position, self.line, self.column
        while is_digit(self.ch):
            self.read_char()
        if is_letter(self.ch):
            raise LexerError("un identificador no puede empezar con un dígito", line, column)
        return self.source[start:self.position]

    def read_string(self) -> str:
        line, column = self.line, self.column
        self.read_char()
        start = self.position
        while self.ch != '"':
            if self.ch == EOF_CHAR:
                raise LexerError("cadena sin cerrar, falta la comilla final", line, column)
            self.read_char()
        text = self.source[start:self.position]
        self.read_char()
        return text


def is_letter(ch: str) -> bool:
    return ch.isalpha() or ch == "_"


def is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def tokenize(source: str) -> list[Token]:
    lexer = Lexer(source)
    tokens = []
    while True:
        token = lexer.next_token()
        tokens.append(token)
        if token.type == TokenType.EOF:
            return tokens
