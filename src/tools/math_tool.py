"""Math tool for safe arithmetic expression evaluation"""

import ast
import operator
from typing import Dict, Any
from .base import BaseTool


# Whitelist of safe operations
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class MathTool(BaseTool):
    """Tool for evaluating safe arithmetic expressions"""

    @property
    def name(self) -> str:
        return "math"

    @property
    def description(self) -> str:
        return "Evaluates arithmetic expressions safely. Supports +, -, *, /, //, %, ** operators and parentheses. Example: '(2 + 3) * 4'"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The arithmetic expression to evaluate (e.g., '2 + 2', '(10 * 5) / 2')",
                }
            },
            "required": ["expression"],
        }

    def _safe_eval(self, node: ast.AST) -> float:
        """
        Recursively evaluate AST node with only safe operations.

        Args:
            node: AST node to evaluate

        Returns:
            Numeric result

        Raises:
            ValueError: If expression contains unsafe operations
        """
        if isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            return float(node.n)
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operation: {op_type.__name__}")
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            return SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported unary operation: {op_type.__name__}")
            operand = self._safe_eval(node.operand)
            return SAFE_OPERATORS[op_type](operand)
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression safely.

        Args:
            params: Must contain 'expression' key with string value

        Returns:
            Dictionary with 'result' key containing the numeric result
        """
        expression = params.get("expression")
        if not expression:
            raise ValueError("Missing required parameter: expression")

        if not isinstance(expression, str):
            raise ValueError("Expression must be a string")

        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode="eval")

            # Evaluate safely
            result = self._safe_eval(tree.body)

            return {
                "result": result,
                "expression": expression,
            }
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")
        except ZeroDivisionError:
            raise ValueError("Division by zero")
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {e}")
