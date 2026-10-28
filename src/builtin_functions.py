import re
from typing import TextIO

from .objects import NULL, Array, Boolean, Builtin, Hash, Integer, Object, String

INTEGER_TEXT = re.compile(r"-?[0-9]+")


class BuiltinError(Exception):
    pass


def expect_arguments(name: str, args: list[Object], count: int) -> None:
    if len(args) != count:
        raise BuiltinError(f"{name} espera {count} argumento(s) y recibió {len(args)}")


def builtin_len(args: list[Object]) -> Object:
    expect_arguments("len", args, 1)
    value = args[0]
    if isinstance(value, String):
        return Integer(len(value.value))
    if isinstance(value, Array):
        return Integer(len(value.elements))
    if isinstance(value, Hash):
        return Integer(len(value.pairs))
    raise BuiltinError(f"len no admite {value.type_name}")


def builtin_str(args: list[Object]) -> Object:
    expect_arguments("str", args, 1)
    return String(args[0].inspect())


def builtin_int(args: list[Object]) -> Object:
    expect_arguments("int", args, 1)
    value = args[0]
    if isinstance(value, Integer):
        return value
    if isinstance(value, Boolean):
        return Integer(1 if value.value else 0)
    if isinstance(value, String) and INTEGER_TEXT.fullmatch(value.value.strip()):
        return Integer(int(value.value))
    raise BuiltinError(f"no se puede convertir {value.inspect()!r} a entero")


def builtin_type(args: list[Object]) -> Object:
    expect_arguments("type", args, 1)
    return String(args[0].type_name)


def builtin_push(args: list[Object]) -> Object:
    expect_arguments("push", args, 2)
    array, value = args
    if not isinstance(array, Array):
        raise BuiltinError(f"push espera un ARRAY y recibió {array.type_name}")
    array.elements.append(value)
    return array


def make_builtins(output: TextIO) -> dict[str, Builtin]:
    def builtin_print(args: list[Object]) -> Object:
        print(" ".join(arg.inspect() for arg in args), file=output)
        return NULL

    functions = {
        "print": builtin_print,
        "len": builtin_len,
        "str": builtin_str,
        "int": builtin_int,
        "type": builtin_type,
        "push": builtin_push,
    }
    return {name: Builtin(name, fn) for name, fn in functions.items()}
