"""
calculator.py — Safe Calculator Tool
======================================
Gives Vaani the ability to perform accurate math calculations.

Uses Python's ast module instead of eval() for safety —
only allows mathematical expressions, blocks any code execution.

Example usage by LLM:
    User: "What is 15% of 2,400?"
    LLM calls: calculate(expression="2400 * 0.15")
    Tool returns: "2400 * 0.15 = 360.0"
    LLM speaks: "15% of 2,400 is 360."
"""

import ast
import math
import operator
from pipecat.processors.frameworks.rtvi import FunctionCallParams

from core.logger import logger


# ── Safe math operators & constants ───────────────────────────────────────────
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,  # unary minus
    ast.UAdd: operator.pos,  # unary plus
    ast.FloorDiv: operator.floordiv,
}

SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node):
    """Recursively evaluate an AST node using only safe math operations."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported literal: {node.value}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return SAFE_OPERATORS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return SAFE_OPERATORS[op_type](operand)

    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls allowed")
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not allowed")
        args = [_safe_eval(arg) for arg in node.args]
        return SAFE_FUNCTIONS[func_name](*args)

    elif isinstance(node, ast.Name):
        # Allow math constants like pi, e
        if node.id in SAFE_FUNCTIONS:
            val = SAFE_FUNCTIONS[node.id]
            if callable(val):
                raise ValueError(f"'{node.id}' is a function, not a constant")
            return val
        raise ValueError(f"Unknown variable: {node.id}")

    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def safe_calculate(expression: str) -> float:
    """
    Safely evaluate a mathematical expression string.

    Args:
        expression: Math expression like "2 + 2", "sqrt(144)", "15 * 0.18"

    Returns:
        The numeric result

    Raises:
        ValueError: If expression is invalid or contains unsafe operations
    """
    # Clean up common user input patterns
    expression = expression.strip()
    expression = expression.replace("^", "**")  # support ^ as power operator
    expression = expression.replace(",", "")     # remove thousands separators

    tree = ast.parse(expression, mode="eval")
    return _safe_eval(tree.body)


# ── Tool Schema ────────────────────────────────────────────────────────────────
CALCULATE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": (
            "Perform accurate mathematical calculations. "
            "Supports basic arithmetic (+, -, *, /), powers (^), percentages, "
            "and math functions (sqrt, round, abs, log, sin, cos, ceil, floor). "
            "Use this for any math computation to ensure accuracy."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "Mathematical expression to evaluate. "
                        "Examples: '15 * 0.18', 'sqrt(144)', '2^10', '(100 + 50) / 3'"
                    )
                }
            },
            "required": ["expression"]
        }
    }
}


# ── Tool Handler ───────────────────────────────────────────────────────────────
async def calculate_handler(params: FunctionCallParams) -> None:
    """Handle a calculate tool call from the LLM."""
    args = params.arguments
    expression = args.get("expression", "").strip()

    logger.info("Tool: calculate | expression='{}'", expression)

    try:
        value = safe_calculate(expression)

        # Format nicely: no unnecessary decimals
        if isinstance(value, float) and value.is_integer():
            formatted = str(int(value))
        else:
            formatted = f"{value:.6g}"  # up to 6 significant figures, no trailing zeros

        result = f"{expression} = {formatted}"
        logger.info("Tool: calculate completed | result='{}'", result)

    except ZeroDivisionError:
        result = "Error: Division by zero."
    except ValueError as e:
        result = f"Invalid expression: {str(e)}"
    except Exception as e:
        result = f"Calculation failed: {str(e)}"
        logger.error("Tool: calculate error | expression='{}' error={}", expression, str(e))

    await params.result_callback(result)
