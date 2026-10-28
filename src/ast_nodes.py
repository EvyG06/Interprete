from __future__ import annotations

from dataclasses import dataclass, fields

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


def format_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value) if isinstance(value, str) else str(value)


def node_label(node: Node) -> str:
    scalars = [
        format_scalar(getattr(node, f.name))
        for f in fields(node)
        if f.name != "token" and isinstance(getattr(node, f.name), (str, int))
    ]
    return " ".join([type(node).__name__, *scalars])


def node_children(node: Node) -> list[tuple[str, Node]]:
    children = []
    for f in fields(node):
        value = getattr(node, f.name)
        if isinstance(value, Node):
            children.append((f.name, value))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, tuple):
                    children.append((f"{f.name}[{i}].clave", item[0]))
                    children.append((f"{f.name}[{i}].valor", item[1]))
                else:
                    children.append((f"{f.name}[{i}]", item))
    return children


def format_tree(node: Node) -> str:
    lines = [node_label(node)]
    add_children(node, "", lines)
    return "\n".join(lines)


def add_children(node: Node, prefix: str, lines: list[str]) -> None:
    children = node_children(node)
    for i, (label, child) in enumerate(children):
        last = i == len(children) - 1
        lines.append(f"{prefix}{'`-- ' if last else '|-- '}{label}: {node_label(child)}")
        add_children(child, prefix + ("    " if last else "|   "), lines)
