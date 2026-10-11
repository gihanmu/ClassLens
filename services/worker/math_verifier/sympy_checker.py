"""SymPy-based exact rational arithmetic verification."""

from __future__ import annotations

import re
from typing import List, Union
import sympy as sp
from sympy.core.sympify import SympifyError


class MathEvaluationError(Exception):
    """Raised when an expression cannot be parsed or evaluated mathematically."""


class SymPyChecker:
    """Provides exact rational arithmetic evaluation and equality verification using SymPy."""

    @staticmethod
    def eval_arithmetic(expr: Union[str, int, float]) -> float:
        """Parses and evaluates an arithmetic expression into a float value.

        Args:
            expr: Expression string (e.g. '-6 + 12 - 4') or numeric value.

        Returns:
            Computed numerical value as float.

        Raises:
            MathEvaluationError: If the expression cannot be parsed or contains symbols.
        """
        if isinstance(expr, (int, float)):
            return float(expr)

        if not isinstance(expr, str) or not expr.strip():
            raise MathEvaluationError("Empty or invalid expression provided")

        cleaned = expr.strip()

        # Sanitize common human arithmetic artifacts (e.g. unicode minus, redundant spaces)
        cleaned = cleaned.replace("−", "-").replace("—", "-").replace("×", "*").replace("÷", "/")

        try:
            parsed = sp.sympify(cleaned, evaluate=True)
            # Ensure the expression is purely numerical (no free symbols like x, y)
            if parsed.free_symbols:
                raise MathEvaluationError(
                    f"Expression contains free algebraic symbols: {parsed.free_symbols}"
                )
            return float(parsed.evalf())
        except (SympifyError, TypeError, ValueError, ZeroDivisionError) as err:
            raise MathEvaluationError(f"Failed to evaluate expression '{expr}': {err}") from err

    @staticmethod
    def verify_equality(
        lhs: Union[str, int, float],
        rhs: Union[str, int, float],
        tolerance: float = 1e-4,
    ) -> bool:
        """Verifies if two arithmetic expressions or values evaluate to the exact same value.

        Args:
            lhs: Left-hand side expression or number.
            rhs: Right-hand side expression or number.
            tolerance: Maximum allowable difference.

        Returns:
            True if values are equal within tolerance, False otherwise.
        """
        val_lhs = SymPyChecker.eval_arithmetic(lhs)
        val_rhs = SymPyChecker.eval_arithmetic(rhs)
        return abs(val_lhs - val_rhs) <= tolerance

    @staticmethod
    def parse_expression_addends(expr: str) -> List[float]:
        """Extracts individual signed numerical addends from a linear addition/subtraction expression.

        For example:
            "-6 + 12 - 4" -> [-6.0, 12.0, -4.0]
            "12 - 4 - 6"  -> [12.0, -4.0, -6.0]

        Args:
            expr: Arithmetic expression string.

        Returns:
            List of signed float addends.
        """
        if not isinstance(expr, str) or not expr.strip():
            return []

        cleaned = expr.strip().replace(" ", "").replace("−", "-").replace("—", "-")
        # Matches signed numbers: e.g. -6, +12, -4, 12
        tokens = re.findall(r"[+-]?\d+(?:\.\d+)?", cleaned)
        return [float(t) for t in tokens if t]
