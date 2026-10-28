import sys
from typing import TextIO

from . import ast_nodes as nodes
from .builtin_functions import BuiltinError, make_builtins
from .errors import EvalError
from .objects import (
    FALSE,
    HASHABLE,
    NULL,
    TRUE,
    Array,
    Boolean,
    Builtin,
    Environment,
    Function,
    Hash,
    Integer,
    Object,
    ReturnValue,
    String,
)

sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))


def error_at(node: nodes.Node, message: str) -> EvalError:
    return EvalError(message, node.token.line, node.token.column)


def native_bool(value: bool) -> Boolean:
    return TRUE if value else FALSE


def is_truthy(value: Object) -> bool:
    if value is NULL:
        return False
    if isinstance(value, Boolean):
        return value.value
    return True


def truncated_division(a: int, b: int) -> int:
    quotient = abs(a) // abs(b)
    return quotient if (a < 0) == (b < 0) else -quotient


class Evaluator:
    def __init__(self, output: TextIO = sys.stdout):
        self.builtins = make_builtins(output)

    def eval(self, node: nodes.Node, env: Environment) -> Object:
        match node:
            case nodes.Program():
                return self.eval_program(node, env)
            case nodes.BlockStatement():
                return self.eval_block(node, env)
            case nodes.ExpressionStatement():
                return self.eval(node.expression, env)
            case nodes.LetStatement():
                env.define(node.name.name, self.eval(node.value, env))
                return NULL
            case nodes.ReturnStatement():
                return ReturnValue(self.eval(node.value, env))
            case nodes.IntegerLiteral():
                return Integer(node.value)
            case nodes.StringLiteral():
                return String(node.value)
            case nodes.BooleanLiteral():
                return native_bool(node.value)
            case nodes.Identifier():
                return self.eval_identifier(node, env)
            case nodes.PrefixExpression():
                return self.eval_prefix(node, env)
            case nodes.InfixExpression():
                return self.eval_infix(node, env)
            case nodes.AssignExpression():
                return self.eval_assign(node, env)
            case nodes.IfExpression():
                return self.eval_if(node, env)
            case nodes.WhileExpression():
                return self.eval_while(node, env)
            case nodes.ForExpression():
                return self.eval_for(node, env)
            case nodes.FunctionLiteral():
                return Function(node.parameters, node.body, env)
            case nodes.CallExpression():
                return self.eval_call(node, env)
            case nodes.ArrayLiteral():
                return Array([self.eval(element, env) for element in node.elements])
            case nodes.HashLiteral():
                return self.eval_hash(node, env)
            case nodes.IndexExpression():
                return self.eval_index(node, env)
        raise TypeError(f"nodo no soportado: {type(node).__name__}")

    # ---------- sentencias y bloques ----------

    def eval_program(self, program: nodes.Program, env: Environment) -> Object:
        result = NULL
        for statement in program.statements:
            try:
                result = self.eval(statement, env)
            except RecursionError:
                raise error_at(statement, "recursión demasiado profunda") from None
            if isinstance(result, ReturnValue):
                return result.value
        return result

    def eval_block(self, block: nodes.BlockStatement, env: Environment) -> Object:
        result = NULL
        for statement in block.statements:
            result = self.eval(statement, env)
            if isinstance(result, ReturnValue):
                return result
        return result

    # ---------- variables ----------

    def eval_identifier(self, node: nodes.Identifier, env: Environment) -> Object:
        value = env.get(node.name)
        if value is None:
            value = self.builtins.get(node.name)
        if value is None:
            raise error_at(node, f"variable no definida: {node.name}")
        return value

    def eval_assign(self, node: nodes.AssignExpression, env: Environment) -> Object:
        target = node.target
        if isinstance(target, nodes.Identifier):
            value = self.eval(node.value, env)
            if not env.assign(target.name, value):
                raise error_at(target, f"variable no definida: {target.name}")
            return value

        container = self.eval(target.left, env)
        index = self.eval(target.index, env)
        if isinstance(container, Array):
            position = self.array_position(target, container, index)
            if position is None:
                raise error_at(target, f"índice fuera de rango: {index.value}")
            value = self.eval(node.value, env)
            container.elements[position] = value
            return value
        if isinstance(container, Hash):
            self.check_hashable(target, index)
            value = self.eval(node.value, env)
            container.pairs[index] = value
            return value
        raise error_at(target, f"no se puede asignar por índice a {container.type_name}")

    # ---------- operadores ----------

    def eval_prefix(self, node: nodes.PrefixExpression, env: Environment) -> Object:
        right = self.eval(node.right, env)
        if node.operator == "!":
            return native_bool(not is_truthy(right))
        if isinstance(right, Integer):
            return Integer(-right.value)
        raise error_at(node, f"el operador - no admite {right.type_name}")

    def eval_infix(self, node: nodes.InfixExpression, env: Environment) -> Object:
        if node.operator in ("&&", "||"):
            return self.eval_logical(node, env)
        left = self.eval(node.left, env)
        right = self.eval(node.right, env)
        operator = node.operator

        if operator == "==":
            return native_bool(left == right)
        if operator == "!=":
            return native_bool(left != right)
        if type(left) is not type(right):
            raise error_at(node, f"tipos incompatibles: {left.type_name} {operator} {right.type_name}")
        if isinstance(left, Integer):
            return self.eval_integer_infix(node, left.value, right.value)
        if isinstance(left, String) and operator == "+":
            return String(left.value + right.value)
        if isinstance(left, Array) and operator == "+":
            return Array(left.elements + right.elements)
        raise error_at(node, f"operador no admitido: {left.type_name} {operator} {right.type_name}")

    def eval_logical(self, node: nodes.InfixExpression, env: Environment) -> Object:
        left = is_truthy(self.eval(node.left, env))
        if node.operator == "&&" and not left:
            return FALSE
        if node.operator == "||" and left:
            return TRUE
        return native_bool(is_truthy(self.eval(node.right, env)))

    def eval_integer_infix(self, node: nodes.InfixExpression, a: int, b: int) -> Object:
        match node.operator:
            case "+":
                return Integer(a + b)
            case "-":
                return Integer(a - b)
            case "*":
                return Integer(a * b)
            case "/" | "%" if b == 0:
                raise error_at(node, "división por cero")
            case "/":
                return Integer(truncated_division(a, b))
            case "%":
                return Integer(a - b * truncated_division(a, b))
            case "**" if b < 0:
                raise error_at(node, "exponente negativo")
            case "**":
                return Integer(a ** b)
            case "<":
                return native_bool(a < b)
            case ">":
                return native_bool(a > b)
            case "<=":
                return native_bool(a <= b)
            case ">=":
                return native_bool(a >= b)
        raise error_at(node, f"operador no admitido: INTEGER {node.operator} INTEGER")

    # ---------- control de flujo ----------

    def eval_if(self, node: nodes.IfExpression, env: Environment) -> Object:
        if is_truthy(self.eval(node.condition, env)):
            return self.eval(node.consequence, env)
        if node.alternative is not None:
            return self.eval(node.alternative, env)
        return NULL

    def eval_while(self, node: nodes.WhileExpression, env: Environment) -> Object:
        result = NULL
        while is_truthy(self.eval(node.condition, env)):
            result = self.eval(node.body, env)
            if isinstance(result, ReturnValue):
                return result
        return result

    def eval_for(self, node: nodes.ForExpression, env: Environment) -> Object:
        if node.init is not None:
            self.eval(node.init, env)
        result = NULL
        while node.condition is None or is_truthy(self.eval(node.condition, env)):
            result = self.eval(node.body, env)
            if isinstance(result, ReturnValue):
                return result
            if node.update is not None:
                self.eval(node.update, env)
        return result

    # ---------- funciones ----------

    def eval_call(self, node: nodes.CallExpression, env: Environment) -> Object:
        function = self.eval(node.function, env)
        arguments = [self.eval(argument, env) for argument in node.arguments]

        if isinstance(function, Builtin):
            try:
                return function.fn(arguments)
            except BuiltinError as error:
                raise error_at(node.function, str(error)) from None

        if not isinstance(function, Function):
            raise error_at(node.function, f"{function.type_name} no es una función")
        if len(arguments) != len(function.parameters):
            raise error_at(
                node.function,
                f"se esperaban {len(function.parameters)} argumento(s) y llegaron {len(arguments)}",
            )

        local = Environment(outer=function.env)
        for parameter, argument in zip(function.parameters, arguments):
            local.define(parameter.name, argument)
        result = self.eval(function.body, local)
        return result.value if isinstance(result, ReturnValue) else result

    # ---------- colecciones ----------

    def eval_hash(self, node: nodes.HashLiteral, env: Environment) -> Object:
        pairs = {}
        for key_node, value_node in node.pairs:
            key = self.eval(key_node, env)
            self.check_hashable(key_node, key)
            pairs[key] = self.eval(value_node, env)
        return Hash(pairs)

    def eval_index(self, node: nodes.IndexExpression, env: Environment) -> Object:
        container = self.eval(node.left, env)
        index = self.eval(node.index, env)
        if isinstance(container, Array):
            position = self.array_position(node, container, index)
            return NULL if position is None else container.elements[position]
        if isinstance(container, Hash):
            self.check_hashable(node, index)
            return container.pairs.get(index, NULL)
        raise error_at(node, f"no se puede indexar un valor {container.type_name}")

    def array_position(self, node: nodes.Node, array: Array, index: Object) -> int | None:
        if not isinstance(index, Integer):
            raise error_at(node, f"el índice de un ARRAY debe ser INTEGER, no {index.type_name}")
        if 0 <= index.value < len(array.elements):
            return index.value
        return None

    def check_hashable(self, node: nodes.Node, key: Object) -> None:
        if not isinstance(key, HASHABLE):
            raise error_at(node, f"una clave de diccionario no puede ser {key.type_name}")
