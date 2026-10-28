class InterpreterError(Exception):
    stage = "Error"

    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"{self.stage} en línea {self.line}, columna {self.column}: {self.message}"


class LexerError(InterpreterError):
    stage = "Error léxico"


class ParserError(InterpreterError):
    stage = "Error sintáctico"


class EvalError(InterpreterError):
    stage = "Error de ejecución"
