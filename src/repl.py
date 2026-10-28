import sys
from pathlib import Path
from typing import TextIO

from .ast_nodes import format_tree
from .errors import InterpreterError
from .evaluator import Evaluator
from .lexer import tokenize
from .objects import NULL, Environment
from .parser import parse
from .tokens import TokenType

OPENERS = {TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE}
CLOSERS = {TokenType.RPAREN, TokenType.RBRACKET, TokenType.RBRACE}
MODES = ("lexer", "parser", "evaluator")

HELP = """Comandos
  :lexer          muestra los tokens de cada entrada
  :parser         muestra el AST de cada entrada
  :evaluator      ejecuta cada entrada (modo inicial)
  :cargar RUTA    ejecuta un archivo dentro de la sesión actual
  :ayuda          muestra esta ayuda
  :salir          termina la sesión
Si una entrada deja (, [ o { sin cerrar, el REPL pide más líneas con '..'."""


def read_source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def run_file(path, output: TextIO = sys.stdout, errors: TextIO = sys.stderr) -> int:
    try:
        source = read_source(path)
    except OSError as error:
        print(f"No se pudo leer {path}: {error.strerror}", file=errors)
        return 1
    try:
        result = Evaluator(output).eval(parse(source), Environment())
    except InterpreterError as error:
        print(error, file=errors)
        return 1
    if result is not NULL:
        print(result.inspect(), file=output)
    return 0


def is_incomplete(source: str) -> bool:
    try:
        tokens = tokenize(source)
    except InterpreterError:
        return False
    depth = 0
    for token in tokens:
        if token.type in OPENERS:
            depth += 1
        elif token.type in CLOSERS:
            depth -= 1
    return depth > 0


def read_entry(input_stream: TextIO, output: TextIO) -> str | None:
    lines = []
    prompt = ">> "
    while True:
        output.write(prompt)
        output.flush()
        line = input_stream.readline()
        if not line:
            return "\n".join(lines) if lines else None
        lines.append(line.rstrip("\n"))
        source = "\n".join(lines)
        if source.lstrip().startswith(":") or not is_incomplete(source):
            return source
        prompt = ".. "


def show(source: str, mode: str, evaluator: Evaluator, env: Environment, output: TextIO) -> None:
    try:
        if mode == "lexer":
            for token in tokenize(source):
                print(token, file=output)
        elif mode == "parser":
            program = parse(source)
            print(program, file=output)
            print(format_tree(program), file=output)
        else:
            result = evaluator.eval(parse(source), env)
            if result is not NULL:
                print(result.inspect(), file=output)
    except InterpreterError as error:
        print(error, file=output)


def run_command(command: str, mode: str, evaluator: Evaluator, env: Environment, output: TextIO) -> str:
    name, _, argument = command[1:].partition(" ")
    if name in MODES:
        print(f"modo {name}", file=output)
        return name
    if name == "ayuda":
        print(HELP, file=output)
    elif name == "cargar":
        try:
            show(read_source(argument.strip()), "evaluator", evaluator, env, output)
        except OSError as error:
            print(f"No se pudo leer {argument.strip()}: {error.strerror}", file=output)
    else:
        print(f"comando desconocido :{name}, escribe :ayuda", file=output)
    return mode


def start(input_stream: TextIO = sys.stdin, output: TextIO = sys.stdout) -> None:
    evaluator = Evaluator(output)
    env = Environment()
    mode = "evaluator"
    print("Intérprete de Compiladores EIA. Escribe :ayuda para ver los comandos.", file=output)
    while True:
        source = read_entry(input_stream, output)
        if source is None:
            print(file=output)
            return
        command = source.strip()
        if not command:
            continue
        if command == ":salir":
            return
        if command.startswith(":"):
            mode = run_command(command, mode, evaluator, env, output)
        else:
            show(source, mode, evaluator, env, output)
