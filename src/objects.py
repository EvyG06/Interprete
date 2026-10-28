from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .ast_nodes import BlockStatement, Identifier, join


class Object:
    type_name = "OBJECT"

    def inspect(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.inspect()


@dataclass(frozen=True)
class Integer(Object):
    value: int
    type_name = "INTEGER"

    def inspect(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class String(Object):
    value: str
    type_name = "STRING"

    def inspect(self) -> str:
        return self.value


@dataclass(frozen=True)
class Boolean(Object):
    value: bool
    type_name = "BOOLEAN"

    def inspect(self) -> str:
        return "true" if self.value else "false"


class Null(Object):
    type_name = "NULL"

    def inspect(self) -> str:
        return "null"


TRUE = Boolean(True)
FALSE = Boolean(False)
NULL = Null()
HASHABLE = (Integer, String, Boolean)


def show(value: Object) -> str:
    return f'"{value.value}"' if isinstance(value, String) else value.inspect()


@dataclass
class Array(Object):
    elements: list[Object]
    type_name = "ARRAY"

    def inspect(self) -> str:
        return "[" + ", ".join(show(element) for element in self.elements) + "]"


@dataclass
class Hash(Object):
    pairs: dict[Object, Object]
    type_name = "HASH"

    def inspect(self) -> str:
        return "{" + ", ".join(f"{show(key)}: {show(value)}" for key, value in self.pairs.items()) + "}"


@dataclass(eq=False)
class Function(Object):
    parameters: list[Identifier]
    body: BlockStatement
    env: Environment = field(repr=False)
    type_name = "FUNCTION"

    def inspect(self) -> str:
        return f"function({join(self.parameters)}) {self.body}"


@dataclass(eq=False)
class Builtin(Object):
    name: str
    fn: Callable[[list[Object]], Object]
    type_name = "BUILTIN"

    def inspect(self) -> str:
        return f"<función integrada {self.name}>"


@dataclass
class ReturnValue(Object):
    value: Object
    type_name = "RETURN_VALUE"

    def inspect(self) -> str:
        return self.value.inspect()


class Environment:
    def __init__(self, outer: Environment | None = None):
        self.store: dict[str, Object] = {}
        self.outer = outer

    def resolve(self, name: str) -> Environment | None:
        env = self
        while env is not None and name not in env.store:
            env = env.outer
        return env

    def get(self, name: str) -> Object | None:
        env = self.resolve(name)
        return None if env is None else env.store[name]

    def define(self, name: str, value: Object) -> None:
        self.store[name] = value

    def assign(self, name: str, value: Object) -> bool:
        env = self.resolve(name)
        if env is None:
            return False
        env.store[name] = value
        return True
