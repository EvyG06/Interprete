from __future__ import annotations

from dataclasses import dataclass

from .tokens import Token


@dataclass
class Node:
    token: Token


class Statement(Node):
    pass


class Expression(Node):
    pass


def join(nodes) -> str:
    return ", ".join(str(node) for node in nodes)


@dataclass
class Program(Node):
    statements: list[Statement]

    def __str__(self) -> str:
        return "\n".join(str(statement) for statement in self.statements)


@dataclass
class BlockStatement(Statement):
    statements: list[Statement]

    def __str__(self) -> str:
        return "{" + "".join(f" {statement};" for statement in self.statements) + " }"


@dataclass
class LetStatement(Statement):
    name: Identifier
    value: Expression

    def __str__(self) -> str:
        return f"let {self.name} = {self.value}"


@dataclass
class ReturnStatement(Statement):
    value: Expression

    def __str__(self) -> str:
        return f"return {self.value}"


@dataclass
class ExpressionStatement(Statement):
    expression: Expression

    def __str__(self) -> str:
        return str(self.expression)


@dataclass
class Identifier(Expression):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class IntegerLiteral(Expression):
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class StringLiteral(Expression):
    value: str

    def __str__(self) -> str:
        return f'"{self.value}"'


@dataclass
class BooleanLiteral(Expression):
    value: bool

    def __str__(self) -> str:
        return "true" if self.value else "false"


@dataclass
class PrefixExpression(Expression):
    operator: str
    right: Expression

    def __str__(self) -> str:
        return f"({self.operator}{self.right})"


@dataclass
class InfixExpression(Expression):
    left: Expression
    operator: str
    right: Expression

    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass
class AssignExpression(Expression):
    target: Expression
    value: Expression

    def __str__(self) -> str:
        return f"({self.target} = {self.value})"


@dataclass
class IfExpression(Expression):
    condition: Expression
    consequence: BlockStatement
    alternative: BlockStatement | IfExpression | None

    def __str__(self) -> str:
        text = f"if ({self.condition}) {self.consequence}"
        if self.alternative is not None:
            text += f" else {self.alternative}"
        return text


@dataclass
class WhileExpression(Expression):
    condition: Expression
    body: BlockStatement

    def __str__(self) -> str:
        return f"while ({self.condition}) {self.body}"


@dataclass
class ForExpression(Expression):
    init: Node | None
    condition: Expression | None
    update: Expression | None
    body: BlockStatement

    def __str__(self) -> str:
        parts = ["" if part is None else str(part) for part in (self.init, self.condition, self.update)]
        return f"for ({'; '.join(parts)}) {self.body}"


@dataclass
class FunctionLiteral(Expression):
    parameters: list[Identifier]
    body: BlockStatement

    def __str__(self) -> str:
        return f"function({join(self.parameters)}) {self.body}"


@dataclass
class CallExpression(Expression):
    function: Expression
    arguments: list[Expression]

    def __str__(self) -> str:
        return f"{self.function}({join(self.arguments)})"


@dataclass
class ArrayLiteral(Expression):
    elements: list[Expression]

    def __str__(self) -> str:
        return f"[{join(self.elements)}]"


@dataclass
class HashLiteral(Expression):
    pairs: list[tuple[Expression, Expression]]

    def __str__(self) -> str:
        return "{" + ", ".join(f"{key}: {value}" for key, value in self.pairs) + "}"


@dataclass
class IndexExpression(Expression):
    left: Expression
    index: Expression

    def __str__(self) -> str:
        return f"({self.left}[{self.index}])"
