"""Deterministic Python tools bound to Google ADK agents."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from services.worker.math_verifier.contracts import NumberLineHop, QuestionRule
from services.worker.math_verifier.sympy_checker import MathEvaluationError, SymPyChecker
from services.worker.math_verifier.verifier import verify_student_math_reasoning


def eval_sympy_arithmetic(expr: str, expected_value: Optional[float] = None) -> Dict[str, Any]:
    """Evaluates an exact arithmetic expression using SymPy rational arithmetic.

    Args:
        expr: Mathematical expression string (e.g. '-6 + 12 - 4' or '12 - 4').
        expected_value: Optional target float to verify equality against.

    Returns:
        Dict with computed value, equality status, and signed addends.
    """
    try:
        val = SymPyChecker.eval_arithmetic(expr)
        addends = SymPyChecker.parse_expression_addends(expr)
        is_equal = None
        if expected_value is not None:
            is_equal = SymPyChecker.verify_equality(expr, expected_value)
        return {
            "success": True,
            "expression": expr,
            "computed_value": val,
            "is_equal": is_equal,
            "addends": addends,
            "error": None,
        }
    except MathEvaluationError as err:
        return {
            "success": False,
            "expression": expr,
            "computed_value": None,
            "is_equal": False,
            "addends": [],
            "error": str(err),
        }


def validate_number_line_moves(
    start: float,
    moves: List[Dict[str, Any]],
    target_value: float = 2.0,
    rule_expr: str = "-6 + 12 - 4",
    final_answer: Optional[float] = None,
) -> Dict[str, Any]:
    """Verifies a sequence of number line hops using deterministic geometry tools.

    Args:
        start: Initial coordinate on the number line.
        moves: List of move dicts with keys 'step_number', 'start', 'end', 'direction', 'stated_magnitude'.
        target_value: Expected final mathematical answer.
        rule_expr: Original question expression string.
        final_answer: Explicit student final answer if present.

    Returns:
        Dict matching MathVerificationVerdict fields.
    """
    rule = QuestionRule(
        problem_id="1065658",
        expression=rule_expr,
        target_value=target_value,
        expected_addends=SymPyChecker.parse_expression_addends(rule_expr),
    )

    hops: List[NumberLineHop] = []
    for m in moves:
        direction = m.get("direction", "none")
        if direction not in ("left", "right", "none"):
            direction = "none"
        hops.append(
            NumberLineHop(
                step_number=int(m.get("step_number", len(hops) + 1)),
                start=float(m.get("start", start)),
                end=float(m.get("end", start)),
                direction=direction,  # type: ignore[arg-type]
                stated_magnitude=m.get("stated_magnitude"),
            )
        )

    verdict = verify_student_math_reasoning(hops=hops, final_answer=final_answer, rule=rule)
    return verdict.model_dump()


def compute_cohort_statistics(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes exact deterministic cohort distributions and error clusters.

    Ensures that LLMs never calculate counts or percentages.

    Args:
        responses: List of response records or StudentResponseAnalysis dicts.

    Returns:
        Dict containing exact counts, percentages, and ranked misconception clusters.
    """
    total = len(responses)
    if total == 0:
        return {
            "total_students": 0,
            "correct_answers": 0,
            "correct_answers_pct": 0.0,
            "valid_reasoning": 0,
            "valid_reasoning_pct": 0.0,
            "compensatory_errors": 0,
            "needs_teacher_review": 0,
            "misconception_clusters": [],
        }

    correct_answers = sum(1 for r in responses if r.get("answer_status") == "correct")
    valid_reasoning = sum(1 for r in responses if r.get("reasoning_status") == "supported_correct")
    compensatory_errors = sum(1 for r in responses if r.get("is_compensatory_error") is True)
    needs_review = sum(1 for r in responses if r.get("needs_teacher_review") is True)

    # Cluster by taxonomy ID
    cluster_counts: Counter[str] = Counter()
    cluster_students: Dict[str, List[str]] = {}

    for r in responses:
        resp_id = r.get("response_id", "unknown")
        # Check diagnosis for misconception_taxonomy_id
        diag = r.get("diagnosis", {})
        tax_id = diag.get("misconception_taxonomy_id") if isinstance(diag, dict) else None
        if not tax_id:
            tax_id = r.get("misconception_taxonomy_id")

        if tax_id:
            cluster_counts[tax_id] += 1
            if tax_id not in cluster_students:
                cluster_students[tax_id] = []
            cluster_students[tax_id].append(resp_id)

    ranked_clusters = []
    for tax_id, count in cluster_counts.most_common():
        pct = round((count / total) * 100.0, 1)
        ranked_clusters.append({
            "taxonomy_id": tax_id,
            "count": count,
            "percentage": pct,
            "student_ids": cluster_students.get(tax_id, []),
        })

    return {
        "total_students": total,
        "correct_answers": correct_answers,
        "correct_answers_pct": round((correct_answers / total) * 100.0, 1),
        "valid_reasoning": valid_reasoning,
        "valid_reasoning_pct": round((valid_reasoning / total) * 100.0, 1),
        "compensatory_errors": compensatory_errors,
        "compensatory_errors_pct": round((compensatory_errors / total) * 100.0, 1),
        "needs_teacher_review": needs_review,
        "needs_teacher_review_pct": round((needs_review / total) * 100.0, 1),
        "misconception_clusters": ranked_clusters,
    }
