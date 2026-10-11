"""Synthetic, model-independent observation vectors for mathematical verification.

NOTE ON PROVENANCE:
These test fixtures are strictly synthetic, simulated observation vectors. They
are isolated from raw dataset files and original teacher annotations to ensure
evaluation integrity. All labels represent test fixture specifications.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.worker.math_verifier.contracts import NumberLineHop, QuestionRule


class SyntheticMathFixture(BaseModel):
    """Specification of a synthetic student test vector for verification benchmarking."""

    fixture_id: str
    description: str
    rule: QuestionRule
    hops: List[NumberLineHop]
    final_answer: Optional[float] = None
    expected_is_reasoning_valid: bool
    expected_is_final_answer_valid: bool
    expected_method: str
    expected_first_error_step: Optional[int] = None
    expected_first_error_taxonomy: Optional[str] = None
    expected_is_compensatory_error: bool = False
    expected_needs_teacher_review: bool = False


# Canonical Question Rule for Problem #1065658: "-6 + 12 - 4 = 2"
RULE_PROBLEM_1065658 = QuestionRule(
    problem_id="1065658",
    expression="-6 + 12 - 4",
    target_value=2.0,
    expected_addends=[-6.0, 12.0, -4.0],
    allow_direct_start=True,
    allow_commutative=True,
    tolerance=1e-4,
)


def get_problem_1065658_synthetic_fixtures() -> List[SyntheticMathFixture]:
    """Returns 13 synthetic test fixtures modeling DrawEduMath Problem #1065658 cases (Rows 0-12)."""
    return [
        # Row 0: Standard hop from zero: 0 -> -6 -> 6 -> 2, answer: 2
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-00",
            description="Row 0: Standard hop from zero (0 -> -6 -> 6 -> 2), circled 2.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
                NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
            ],
            final_answer=2.0,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=True,
            expected_method="hop_from_zero",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 1: Standard hop from zero: 0 -> -6 -> 6 -> 2, answer: 2
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-01",
            description="Row 1: Horizontal line, arrows 0 -> -6 -> 6 -> 2, circled 2.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
                NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
            ],
            final_answer=2.0,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=True,
            expected_method="hop_from_zero",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 2: Standard hop, terminal at 2, final answer inferred (final_answer=None)
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-02",
            description="Row 2: Graph paper, arrows end at 2, answer inferred from terminal position.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
                NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
            ],
            final_answer=None,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=True,
            expected_method="hop_from_zero",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 3: Digitally drawn bracket curves: 0 -> -6 -> 6 -> 2, answer: 2
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-03",
            description="Row 3: Digitally drawn curved arrows 0 -> -6 -> 6 -> 2, circled 2.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
                NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
            ],
            final_answer=2.0,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=True,
            expected_method="hop_from_zero",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 4: Compensatory error: 0 -> -6 -> 5 -> 2, answer: 2
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-04",
            description="Row 4: Compensatory error: -6 to +5 (mag 11) then +5 to +2 (mag -3). Answer 2.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=5.0, direction="right"),
                NumberLineHop(step_number=3, start=5.0, end=2.0, direction="left"),
            ],
            final_answer=2.0,
            expected_is_reasoning_valid=False,
            expected_is_final_answer_valid=True,
            expected_method="hop_from_zero",
            expected_first_error_step=2,
            expected_first_error_taxonomy="MISC-ARITH-OFF-BY-ONE",
            expected_is_compensatory_error=True,
            expected_needs_teacher_review=True,
        ),
        # Row 5: Off-by-one magnitude error: 0 -> -6 -> 5 -> 1, answer: 1
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-05",
            description="Row 5: Magnitude error: hopped 11 units instead of 12, landing at 1. Answer 1.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=5.0, direction="right"),
                NumberLineHop(step_number=3, start=5.0, end=1.0, direction="left"),
            ],
            final_answer=1.0,
            expected_is_reasoning_valid=False,
            expected_is_final_answer_valid=False,
            expected_method="hop_from_zero",
            expected_first_error_step=2,
            expected_first_error_taxonomy="MISC-ARITH-OFF-BY-ONE",
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 6: Correct number line 0 -> -6 -> 6 -> 2, but circled answer is 3
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-06",
            description="Row 6: Modeling correct, but circled +3 as final answer instead of +2.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
                NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
            ],
            final_answer=3.0,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=False,
            expected_method="hop_from_zero",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 7: Digital drawing standard pass 0 -> -6 -> 6 -> 2, answer: 2
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-07",
            description="Row 7: Digital drawing standard execution, circled 2.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
                NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
            ],
            final_answer=2.0,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=True,
            expected_method="hop_from_zero",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 8: Number line interval mislabeled (stated magnitude 12, coordinate 11)
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-08",
            description="Row 8: Mislabeled number line intervals: stated +12 hops from -6 to 5.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left", stated_magnitude=6.0),
                NumberLineHop(step_number=2, start=-6.0, end=5.0, direction="right", stated_magnitude=12.0),
                NumberLineHop(step_number=3, start=5.0, end=1.0, direction="left", stated_magnitude=4.0),
            ],
            final_answer=1.0,
            expected_is_reasoning_valid=False,
            expected_is_final_answer_valid=False,
            expected_method="hop_from_zero",
            expected_first_error_step=2,
            expected_first_error_taxonomy="MISC-LINE-INTERVAL-MISLABEL",
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 9: Commutative rearrangement: 12 -> 8 -> 2 (12 - 4 - 6 = 2), answer: 2
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-09",
            description="Row 9: Commutative rearrangement (12 - 4 - 6 = 2), direct start at 12.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=12.0, end=8.0, direction="left"),
                NumberLineHop(step_number=2, start=8.0, end=2.0, direction="left"),
            ],
            final_answer=2.0,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=True,
            expected_method="commutative",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 10: Standard hop pass: 0 -> -6 -> 6 -> 2, answer: 2
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-10",
            description="Row 10: Pre-printed paper, standard hop pass 0 -> -6 -> 6 -> 2.",
            rule=RULE_PROBLEM_1065658,
            hops=[
                NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
                NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
                NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
            ],
            final_answer=2.0,
            expected_is_reasoning_valid=True,
            expected_is_final_answer_valid=True,
            expected_method="hop_from_zero",
            expected_first_error_step=None,
            expected_first_error_taxonomy=None,
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=False,
        ),
        # Row 11: Circled 2 on number line, but zero working shown (answer: 2, hops: [])
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-11",
            description="Row 11: Circled 2, but zero working/arrows shown. Answer 2.",
            rule=RULE_PROBLEM_1065658,
            hops=[],
            final_answer=2.0,
            expected_is_reasoning_valid=False,
            expected_is_final_answer_valid=True,
            expected_method="unrecognized",
            expected_first_error_step=None,
            expected_first_error_taxonomy="REASONING_INCOMPLETE",
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=True,
        ),
        # Row 12: Incomplete/unreadable: no hops, no answer
        SyntheticMathFixture(
            fixture_id="SYNTH-ROW-12",
            description="Row 12: Completely incomplete/unreadable response.",
            rule=RULE_PROBLEM_1065658,
            hops=[],
            final_answer=None,
            expected_is_reasoning_valid=False,
            expected_is_final_answer_valid=False,
            expected_method="unrecognized",
            expected_first_error_step=None,
            expected_first_error_taxonomy="REASONING_INCOMPLETE",
            expected_is_compensatory_error=False,
            expected_needs_teacher_review=True,
        ),
    ]
