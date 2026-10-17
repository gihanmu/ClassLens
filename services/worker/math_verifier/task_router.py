"""Deterministic mathematical task and pedagogical method routing.

Routes assessment problems to specialized verification engines (e.g. Number Line
Integer Operations vs Fraction Division with Tape Diagrams vs Algebraic Equations).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class TaskType(str, Enum):
    """Categorical mathematical problem domains supported by ClassLens verification engines."""

    INTEGER_NUMBER_LINE = "integer_number_line"
    FRACTION_DIVISION = "fraction_division"
    DECIMAL_OPERATIONS = "decimal_operations"
    PLACE_VALUE = "place_value"
    UNSUPPORTED_TASK = "unsupported_task"


class TaskRouter:
    """Deterministically identifies the problem domain and routes to the correct verifier."""

    @classmethod
    def resolve_task(
        cls,
        math_topic: Optional[str] = None,
        question_text: Optional[str] = None,
        latex_formula: Optional[str] = None,
        problem_reference_id: Optional[str] = None,
    ) -> TaskType:
        """Determines the appropriate mathematical task type from problem metadata.

        Args:
            math_topic: Title or topic string (e.g. 'Division of Fractions', 'Integer operations on number lines').
            question_text: Natural language prompt or instructions.
            latex_formula: Mathematical equation or expression string.
            problem_reference_id: Dataset problem id if available.

        Returns:
            TaskType enum indicating the target verification engine.
        """
        topic_lower = (math_topic or "").lower()
        q_lower = (question_text or "").lower()
        ref_id = str(problem_reference_id or "").lower()

        # Check explicit problem references
        if ref_id in ("1425504", "e921e6") or "fraction" in ref_id:
            return TaskType.FRACTION_DIVISION
        if ref_id in ("1065658", "synthetic_cases"):
            return TaskType.INTEGER_NUMBER_LINE

        # Check Fraction Division indicators
        is_fraction = (
            "fraction" in topic_lower
            or "fraction" in q_lower
            or "unit form" in q_lower
            or "tape diagram" in q_lower
            or "ninths" in q_lower
            or "eighths" in q_lower
            or "fourths" in q_lower
            or (latex_formula and ("/" in latex_formula or r"\div" in latex_formula or r"\frac" in latex_formula))
        )
        has_division = (
            "division" in topic_lower
            or "divide" in q_lower
            or "quotient" in q_lower
            or "÷" in q_lower
            or (latex_formula and ("/" in latex_formula or "÷" in latex_formula or r"\div" in latex_formula))
        )

        if is_fraction and has_division:
            return TaskType.FRACTION_DIVISION

        # Check Place Value indicators
        is_place_value = (
            "place value" in topic_lower
            or "place value" in q_lower
            or "disks" in topic_lower
            or "disks" in q_lower
            or "disk" in q_lower
            or "hundreds, tens" in topic_lower
            or "base ten" in topic_lower
            or "expanded form" in topic_lower
            or ref_id in ("012a1f01", "place_value")
        )
        if is_place_value:
            return TaskType.PLACE_VALUE

        # Check Decimal Operations indicators
        is_decimal = (
            "decimal" in topic_lower
            or "decimal" in q_lower
            or "estimation" in topic_lower
            or (latex_formula and "." in latex_formula and "/" not in latex_formula)
            or ref_id in ("decimal", "decimals")
        )
        if is_decimal:
            return TaskType.DECIMAL_OPERATIONS

        # Check Integer Number Line indicators
        is_number_line = (
            "number line" in topic_lower
            or "number line" in q_lower
            or "integer" in topic_lower
            or "hops" in q_lower
            or "jump" in q_lower
        )
        if is_number_line:
            return TaskType.INTEGER_NUMBER_LINE

        # Default fallback for simple arithmetic expressions with add/subtract
        if (
            latex_formula
            and any(op in latex_formula for op in ("+", "-"))
            and "/" not in latex_formula
            and (not topic_lower or any(w in topic_lower for w in ("integer", "number", "arithmetic", "addition", "subtraction", "checkpoint", "demo")))
        ):
            return TaskType.INTEGER_NUMBER_LINE

        return TaskType.UNSUPPORTED_TASK
