"""
Safe AST-based mathematical formula evaluator.
Strictly parses expressions without using eval() or arbitrary code execution.
"""
import ast
import math
from typing import Dict, Set, Any, Callable
from mathematical_engine.core.errors import FormulaEvaluationError, NonFiniteValueError


_SAFE_CONSTANTS: Dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
}

def _clip(val: float, low: float, high: float) -> float:
    return max(low, min(val, high))

_SAFE_FUNCTIONS: Dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "clip": _clip,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pow": math.pow,
    "floor": math.floor,
    "ceil": math.ceil,
}


class SafeFormulaEvaluator:
    """
    Evaluates algebraic formulas against an input variable scope using an AST whitelist.
    """

    def __init__(self, additional_functions: Dict[str, Callable[..., float]] = None):
        self.functions = dict(_SAFE_FUNCTIONS)
        if additional_functions:
            self.functions.update(additional_functions)

    def extract_variables(self, expression: str) -> Set[str]:
        """
        Parses an expression and returns all variable identifier names referenced,
        excluding mathematical constants and built-in function names.
        """
        try:
            tree = ast.parse(expression.strip(), mode="eval")
        except SyntaxError as e:
            raise FormulaEvaluationError(f"Syntax error in formula '{expression}': {e}") from e

        variables: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                id_name = node.id
                if id_name not in _SAFE_CONSTANTS and id_name not in self.functions:
                    variables.add(id_name)
        return variables

    def evaluate(self, expression: str, scope: Dict[str, float]) -> float:
        """
        Safely evaluates an algebraic expression against the provided scope.
        """
        if not expression or not expression.strip():
            raise FormulaEvaluationError("Cannot evaluate empty formula")

        try:
            tree = ast.parse(expression.strip(), mode="eval")
        except SyntaxError as e:
            raise FormulaEvaluationError(f"Syntax error in formula '{expression}': {e}") from e

        val = self._eval_node(tree.body, scope)
        if not isinstance(val, (int, float)):
            raise FormulaEvaluationError(f"Formula '{expression}' evaluated to non-numeric type: {type(val)}")

        val = float(val)
        if math.isnan(val) or math.isinf(val):
            raise NonFiniteValueError(f"Formula '{expression}' resulted in non-finite value: {val}")
        return val

    def _eval_node(self, node: ast.AST, scope: Dict[str, float]) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise FormulaEvaluationError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.Name):
            if node.id in scope:
                return scope[node.id]
            if node.id in _SAFE_CONSTANTS:
                return _SAFE_CONSTANTS[node.id]
            raise FormulaEvaluationError(f"Undefined variable or constant: '{node.id}'")

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, scope)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.Not):
                raise FormulaEvaluationError("Logical 'not' is not permitted in arithmetic formulas")
            raise FormulaEvaluationError(f"Unsupported unary operator: {type(node.op)}")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, scope)
            right = self._eval_node(node.right, scope)
            return self._eval_binop(node.op, left, right)

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise FormulaEvaluationError("Dynamic function or method calls are forbidden")
            func_name = node.func.id
            if func_name not in self.functions:
                raise FormulaEvaluationError(f"Function '{func_name}' is not in allowed whitelist")
            
            args = [self._eval_node(arg, scope) for arg in node.args]
            if node.keywords:
                raise FormulaEvaluationError("Keyword arguments are not supported in formula calls")
            try:
                return self.functions[func_name](*args)
            except Exception as e:
                raise FormulaEvaluationError(f"Error executing function '{func_name}': {e}") from e

        else:
            raise FormulaEvaluationError(f"Disallowed syntax element: {type(node).__name__}")

    def _eval_binop(self, op: ast.operator, left: float, right: float) -> float:
        try:
            if isinstance(op, ast.Add):
                return left + right
            elif isinstance(op, ast.Sub):
                return left - right
            elif isinstance(op, ast.Mult):
                return left * right
            elif isinstance(op, ast.Div):
                if right == 0.0:
                    raise FormulaEvaluationError("Division by zero")
                return left / right
            elif isinstance(op, ast.FloorDiv):
                if right == 0.0:
                    raise FormulaEvaluationError("Floor division by zero")
                return left // right
            elif isinstance(op, ast.Mod):
                if right == 0.0:
                    raise FormulaEvaluationError("Modulo by zero")
                return left % right
            elif isinstance(op, ast.Pow):
                if abs(left) > 1e12 and right > 10:
                    raise FormulaEvaluationError("Exponentiation overflow risk")
                return left ** right
            else:
                raise FormulaEvaluationError(f"Unsupported binary operator: {type(op)}")
        except OverflowError as e:
            raise FormulaEvaluationError(f"Numeric overflow in calculation: {e}") from e


# Shared global evaluator instance
formula_evaluator = SafeFormulaEvaluator()
