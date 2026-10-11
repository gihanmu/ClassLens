"""SymPy-based mathematical validation for formative exit ticket questions."""

from __future__ import annotations

import re
from typing import List, Optional

from services.worker.agents.contracts import ExitTicketItem
from services.worker.math_verifier.sympy_checker import SymPyChecker


class ExitTicketValidator:
    """Ensures every generated exit ticket problem has exact, SymPy-verified mathematical answers."""

    _EXPR_PATTERN = re.compile(r"([-\d\s\+\*\/\(\)]+)(?:=|\?|$)", re.IGNORECASE)

    @classmethod
    def extract_arithmetic_expr(cls, prompt: str) -> Optional[str]:
        """Extracts arithmetic expression substring from question prompt."""
        if ":" in prompt:
            candidate = prompt.split(":", 1)[1].strip()
            # Clean trailing question mark or period
            candidate = candidate.rstrip("?. ")
            return candidate

        # Fallback regex for pure arithmetic patterns
        match = re.search(r"[-+]?\s*\d+(?:\s*[-+*/]\s*[-+]?\d+)+", prompt)
        if match:
            return match.group(0).strip()
        return None

    @classmethod
    def verify_item(cls, item: ExitTicketItem) -> ExitTicketItem:
        """Verifies a single exit ticket item against SymPy rational calculation."""
        expr = cls.extract_arithmetic_expr(item.prompt)
        if not expr:
            item.sympy_verified = False
            return item

        try:
            expected_num = float(item.expected_answer.strip())
            is_valid = SymPyChecker.verify_equality(expr, expected_num)
            item.sympy_verified = is_valid
        except Exception:
            item.sympy_verified = False

        return item

    @classmethod
    def verify_ticket(cls, items: List[ExitTicketItem]) -> List[ExitTicketItem]:
        """Verifies an entire list of exit ticket items."""
        return [cls.verify_item(item) for item in items]
