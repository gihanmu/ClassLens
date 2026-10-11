"""Comprehensive unit and acceptance test suite for deterministic mathematical verification."""

from __future__ import annotations

import time
import pytest

from services.worker.math_verifier.contracts import (
    NumberLineHop,
    QuestionRule,
)
from services.worker.math_verifier.method_matcher import MethodMatcher
from services.worker.math_verifier.number_line_geometry import (
    NumberLineDisplacementCalculator,
)
from services.worker.math_verifier.sympy_checker import (
    MathEvaluationError,
    SymPyChecker,
)
from services.worker.math_verifier.taxonomy_mapper import TaxonomyMapper
from services.worker.math_verifier.verifier import verify_student_math_reasoning
from tests.fixtures.synthetic_math_fixtures import (
    RULE_PROBLEM_1065658,
    SyntheticMathFixture,
    get_problem_1065658_synthetic_fixtures,
)


# ==============================================================================
# 1. SymPy Exact Arithmetic Evaluator Tests
# ==============================================================================

class TestSymPyChecker:
    """Tests for exact rational arithmetic verification."""

    def test_eval_simple_expressions(self):
        assert SymPyChecker.eval_arithmetic("2 + 2") == 4.0
        assert SymPyChecker.eval_arithmetic("-6 + 12 - 4") == 2.0
        assert SymPyChecker.eval_arithmetic("100 - 250 + 50") == -100.0

    def test_eval_floating_and_rational_numbers(self):
        assert SymPyChecker.eval_arithmetic("1/2 + 1/4") == 0.75
        assert SymPyChecker.eval_arithmetic("-3.5 + 1.5") == -2.0

    def test_eval_unicode_and_formatting(self):
        # Unicode minus and dashes
        assert SymPyChecker.eval_arithmetic("−6 + 12 − 4") == 2.0
        assert SymPyChecker.eval_arithmetic("—10 + 20") == 10.0
        assert SymPyChecker.eval_arithmetic("  4  ×  5  ") == 20.0

    def test_eval_numeric_inputs(self):
        assert SymPyChecker.eval_arithmetic(42) == 42.0
        assert SymPyChecker.eval_arithmetic(-3.14) == -3.14

    def test_eval_algebraic_symbols_rejected(self):
        with pytest.raises(MathEvaluationError, match="free algebraic symbols"):
            SymPyChecker.eval_arithmetic("x + 5")

    def test_eval_division_by_zero(self):
        with pytest.raises(MathEvaluationError, match="Failed to evaluate"):
            SymPyChecker.eval_arithmetic("5 / 0")

    def test_eval_malformed_string(self):
        with pytest.raises(MathEvaluationError):
            SymPyChecker.eval_arithmetic("+++---")
        with pytest.raises(MathEvaluationError):
            SymPyChecker.eval_arithmetic("")

    def test_verify_equality(self):
        assert SymPyChecker.verify_equality("-6 + 12 - 4", 2.0)
        assert SymPyChecker.verify_equality("1/3", 0.333333, tolerance=1e-4)
        assert not SymPyChecker.verify_equality("-6 + 12 - 4", 3.0)

    def test_parse_expression_addends(self):
        assert SymPyChecker.parse_expression_addends("-6 + 12 - 4") == [-6.0, 12.0, -4.0]
        assert SymPyChecker.parse_expression_addends("12 - 4 - 6") == [12.0, -4.0, -6.0]
        assert SymPyChecker.parse_expression_addends("5 + 10") == [5.0, 10.0]
        assert SymPyChecker.parse_expression_addends("") == []


# ==============================================================================
# 2. Number Line Geometry & Vector Displacement Tests
# ==============================================================================

class TestNumberLineGeometry:
    """Tests for vector displacement and geometry checks."""

    def test_compute_displacements(self):
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
        ]
        deltas = NumberLineDisplacementCalculator.compute_displacements(hops)
        assert deltas == [-6.0, 12.0, -4.0]

    def test_direction_consistency(self):
        valid_right = NumberLineHop(step_number=1, start=0, end=5, direction="right")
        valid_left = NumberLineHop(step_number=2, start=5, end=2, direction="left")
        invalid_right = NumberLineHop(step_number=3, start=0, end=5, direction="left")
        invalid_left = NumberLineHop(step_number=4, start=5, end=2, direction="right")

        assert NumberLineDisplacementCalculator.check_direction_consistency(valid_right)
        assert NumberLineDisplacementCalculator.check_direction_consistency(valid_left)
        assert not NumberLineDisplacementCalculator.check_direction_consistency(invalid_right)
        assert not NumberLineDisplacementCalculator.check_direction_consistency(invalid_left)

    def test_path_continuity(self):
        continuous_hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
        ]
        is_cont, gaps = NumberLineDisplacementCalculator.check_path_continuity(continuous_hops)
        assert is_cont
        assert gaps == []

        discontinuous_hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=0.0, end=6.0, direction="right"),  # Gap: starts at 0 instead of -6
        ]
        is_cont, gaps = NumberLineDisplacementCalculator.check_path_continuity(discontinuous_hops)
        assert not is_cont
        assert gaps == [2]


# ==============================================================================
# 3. Strategy & Method Matcher Tests
# ==============================================================================

class TestMethodMatcher:
    """Tests for identifying pedagogical solution strategies."""

    def test_match_hop_from_zero(self):
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
        ]
        match = MethodMatcher.match(hops, RULE_PROBLEM_1065658)
        assert match.method_name == "hop_from_zero"
        assert match.is_exact_match
        assert match.expected_start == 0.0
        assert match.expected_displacements == [-6.0, 12.0, -4.0]

    def test_match_direct_start(self):
        hops = [
            NumberLineHop(step_number=1, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=2, start=6.0, end=2.0, direction="left"),
        ]
        match = MethodMatcher.match(hops, RULE_PROBLEM_1065658)
        assert match.method_name == "direct_start"
        assert match.is_exact_match
        assert match.expected_start == -6.0
        assert match.expected_displacements == [12.0, -4.0]

    def test_match_commutative(self):
        hops = [
            NumberLineHop(step_number=1, start=12.0, end=8.0, direction="left"),
            NumberLineHop(step_number=2, start=8.0, end=2.0, direction="left"),
        ]
        match = MethodMatcher.match(hops, RULE_PROBLEM_1065658)
        assert match.method_name == "commutative"
        assert match.is_exact_match
        assert match.expected_start == 12.0
        assert match.expected_displacements == [-4.0, -6.0]

    def test_match_unrecognized(self):
        hops = [
            NumberLineHop(step_number=1, start=50.0, end=100.0, direction="right"),
        ]
        match = MethodMatcher.match(hops, RULE_PROBLEM_1065658)
        assert match.method_name == "unrecognized"


# ==============================================================================
# 4. Misconception Taxonomy Classification Tests
# ==============================================================================

class TestTaxonomyMapper:
    """Tests for evidence-based taxonomy classifications."""

    def test_classify_direction_reverse(self):
        tax, notes = TaxonomyMapper.classify_step_deviation(
            expected_displacement=-6.0, observed_displacement=6.0
        )
        assert tax == "MISC-NUM-DIR-REVERSE"
        assert "Direction reversed" in notes

    def test_classify_off_by_one(self):
        tax, notes = TaxonomyMapper.classify_step_deviation(
            expected_displacement=12.0, observed_displacement=11.0
        )
        assert tax == "MISC-ARITH-OFF-BY-ONE"
        assert "Off-by-one" in notes

    def test_classify_interval_mislabel_stated_magnitude(self):
        tax, notes = TaxonomyMapper.classify_step_deviation(
            expected_displacement=12.0, observed_displacement=11.0, stated_magnitude=12.0
        )
        assert tax == "MISC-LINE-INTERVAL-MISLABEL"
        assert "mislabeled intervals" in notes

    def test_classify_interval_mislabel_flag(self):
        tax, notes = TaxonomyMapper.classify_step_deviation(
            expected_displacement=12.0, observed_displacement=11.0, has_interval_mislabel=True
        )
        assert tax == "MISC-LINE-INTERVAL-MISLABEL"

    def test_classify_general_slip(self):
        tax, notes = TaxonomyMapper.classify_step_deviation(
            expected_displacement=12.0, observed_displacement=5.0
        )
        assert tax == "MISC-ARITH-SLIP"
        assert "Arithmetic slip" in notes

    def test_classify_empty_reasoning(self):
        tax, notes = TaxonomyMapper.classify_empty_reasoning()
        assert tax == "REASONING_INCOMPLETE"

    def test_classify_contradiction(self):
        tax, notes = TaxonomyMapper.classify_contradiction(1, "left", 6.0)
        assert tax == "REASONING_CONTRADICTORY"


# ==============================================================================
# 5. Core Acceptance Tests (TC-001.01 through TC-001.08)
# ==============================================================================

class TestAcceptanceCases:
    """Verifies all acceptance criteria defined in specs/001-math-verification/acceptance-tests.md."""

    def test_tc_001_01_hop_from_zero_clean_pass(self):
        """TC-001.01: 0 -> -6 -> 6 -> 2, answer: 2."""
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=2.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is True
        assert verdict.is_final_answer_valid is True
        assert verdict.detected_method == "hop_from_zero"
        assert verdict.first_error_step is None
        assert verdict.first_error_taxonomy is None
        assert verdict.is_compensatory_error is False

    def test_tc_001_02_direct_start_clean_pass(self):
        """TC-001.02: -6 -> 6 -> 2, answer: 2."""
        hops = [
            NumberLineHop(step_number=1, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=2, start=6.0, end=2.0, direction="left"),
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=2.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is True
        assert verdict.is_final_answer_valid is True
        assert verdict.detected_method == "direct_start"
        assert verdict.first_error_step is None
        assert verdict.is_compensatory_error is False

    def test_tc_001_03_commutative_clean_pass(self):
        """TC-001.03: 12 -> 8 -> 2, answer: 2."""
        hops = [
            NumberLineHop(step_number=1, start=12.0, end=8.0, direction="left"),
            NumberLineHop(step_number=2, start=8.0, end=2.0, direction="left"),
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=2.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is True
        assert verdict.is_final_answer_valid is True
        assert verdict.detected_method == "commutative"
        assert verdict.first_error_step is None
        assert verdict.is_compensatory_error is False

    def test_tc_001_04_compensatory_error_row_4(self):
        """TC-001.04: 0 -> -6 -> 5 -> 2, answer: 2."""
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=5.0, direction="right"),  # Δ=11 instead of 12
            NumberLineHop(step_number=3, start=5.0, end=2.0, direction="left"),    # Δ=-3 instead of -4
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=2.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is False
        assert verdict.is_final_answer_valid is True
        assert verdict.is_compensatory_error is True
        assert verdict.first_error_step == 2
        assert verdict.first_error_taxonomy == "MISC-ARITH-OFF-BY-ONE"
        assert verdict.needs_teacher_review is True

    def test_tc_001_05_off_by_one_uncompensated_row_5(self):
        """TC-001.05: 0 -> -6 -> 5 -> 1, answer: 1."""
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=5.0, direction="right"),  # Δ=11 instead of 12
            NumberLineHop(step_number=3, start=5.0, end=1.0, direction="left"),    # Δ=-4 (correct displacement applied to flawed position)
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=1.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is False
        assert verdict.is_final_answer_valid is False
        assert verdict.is_compensatory_error is False
        assert verdict.first_error_step == 2
        assert verdict.first_error_taxonomy == "MISC-ARITH-OFF-BY-ONE"

    def test_tc_001_06_correct_hops_wrong_final_answer_row_6(self):
        """TC-001.06: 0 -> -6 -> 6 -> 2, circled answer 3."""
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=3.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is True
        assert verdict.is_final_answer_valid is False
        assert verdict.is_compensatory_error is False
        assert verdict.first_error_step is None

    def test_tc_001_07_directional_reversal(self):
        """TC-001.07: 0 -> 6 -> -6 -> -10 (Reversed start)."""
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=6.0, direction="right"),  # Δ=+6 instead of -6
            NumberLineHop(step_number=2, start=6.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=3, start=-6.0, end=-10.0, direction="left"),
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=-10.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is False
        assert verdict.is_final_answer_valid is False
        assert verdict.first_error_step == 1
        assert verdict.first_error_taxonomy == "MISC-NUM-DIR-REVERSE"

    def test_tc_001_08_empty_reasoning_answer_only_row_11(self):
        """TC-001.08: Empty hops [], answer: 2."""
        verdict = verify_student_math_reasoning([], final_answer=2.0, rule=RULE_PROBLEM_1065658)

        assert verdict.is_reasoning_valid is False
        assert verdict.is_final_answer_valid is True
        assert verdict.detected_method == "unrecognized"
        assert verdict.first_error_step is None
        assert verdict.first_error_taxonomy == "REASONING_INCOMPLETE"
        assert verdict.needs_teacher_review is True


# ==============================================================================
# 6. Evaluation on All 13 Synthetic Test Fixtures (Rows 0-12)
# ==============================================================================

class TestAll13SyntheticFixtures:
    """Validates the verifier against all 13 synthetic fixtures for Problem #1065658."""

    @pytest.mark.parametrize(
        "fixture",
        get_problem_1065658_synthetic_fixtures(),
        ids=[f.fixture_id for f in get_problem_1065658_synthetic_fixtures()],
    )
    def test_synthetic_fixture(self, fixture: SyntheticMathFixture):
        verdict = verify_student_math_reasoning(
            hops=fixture.hops,
            final_answer=fixture.final_answer,
            rule=fixture.rule,
        )

        assert verdict.is_reasoning_valid == fixture.expected_is_reasoning_valid, (
            f"Reasoning validity mismatch for {fixture.fixture_id}"
        )
        assert verdict.is_final_answer_valid == fixture.expected_is_final_answer_valid, (
            f"Final answer validity mismatch for {fixture.fixture_id}"
        )
        assert verdict.detected_method == fixture.expected_method, (
            f"Method mismatch for {fixture.fixture_id}"
        )
        assert verdict.first_error_step == fixture.expected_first_error_step, (
            f"First error step mismatch for {fixture.fixture_id}"
        )
        assert verdict.first_error_taxonomy == fixture.expected_first_error_taxonomy, (
            f"First error taxonomy mismatch for {fixture.fixture_id}"
        )
        assert verdict.is_compensatory_error == fixture.expected_is_compensatory_error, (
            f"Compensatory error mismatch for {fixture.fixture_id}"
        )
        assert verdict.needs_teacher_review == fixture.expected_needs_teacher_review, (
            f"Needs teacher review mismatch for {fixture.fixture_id}"
        )


# ==============================================================================
# 7. General-Purpose Verification (Arbitrary Arithmetic Problems)
# ==============================================================================

class TestGeneralPurposeVerifier:
    """Verifies that the engine generalizes to arbitrary arithmetic expressions without hardcoding."""

    def test_arbitrary_problem_3_minus_7_plus_2(self):
        rule = QuestionRule(
            problem_id="PROB-GEN-001",
            expression="3 - 7 + 2",
            target_value=-2.0,
            expected_addends=[3.0, -7.0, 2.0],
        )

        # Path 1: Hop from zero clean pass: 0 -> 3 -> -4 -> -2, answer: -2
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=3.0, direction="right"),
            NumberLineHop(step_number=2, start=3.0, end=-4.0, direction="left"),
            NumberLineHop(step_number=3, start=-4.0, end=-2.0, direction="right"),
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=-2.0, rule=rule)
        assert verdict.is_reasoning_valid is True
        assert verdict.is_final_answer_valid is True
        assert verdict.detected_method == "hop_from_zero"

        # Path 2: Direct start clean pass: 3 -> -4 -> -2, answer: -2
        direct_hops = [
            NumberLineHop(step_number=1, start=3.0, end=-4.0, direction="left"),
            NumberLineHop(step_number=2, start=-4.0, end=-2.0, direction="right"),
        ]
        verdict_direct = verify_student_math_reasoning(direct_hops, final_answer=-2.0, rule=rule)
        assert verdict_direct.is_reasoning_valid is True
        assert verdict_direct.is_final_answer_valid is True
        assert verdict_direct.detected_method == "direct_start"

    def test_dynamic_target_value_computation_via_sympy(self):
        # Target value is None -> SymPy computes -15 + 30 - 5 = 10.0 dynamically
        rule = QuestionRule(
            problem_id="PROB-GEN-002",
            expression="-15 + 30 - 5",
            target_value=None,  # Not provided! Must be derived dynamically.
            expected_addends=[-15.0, 30.0, -5.0],
        )
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-15.0, direction="left"),
            NumberLineHop(step_number=2, start=-15.0, end=15.0, direction="right"),
            NumberLineHop(step_number=3, start=15.0, end=10.0, direction="left"),
        ]
        verdict = verify_student_math_reasoning(hops, final_answer=10.0, rule=rule)
        assert verdict.is_reasoning_valid is True
        assert verdict.is_final_answer_valid is True
        assert verdict.terminal_position == 10.0

    def test_execution_speed_nfr_benchmark(self):
        """Verifies NFR-001.1: Complete evaluation executes in < 5 ms on single CPU core."""
        hops = [
            NumberLineHop(step_number=1, start=0.0, end=-6.0, direction="left"),
            NumberLineHop(step_number=2, start=-6.0, end=6.0, direction="right"),
            NumberLineHop(step_number=3, start=6.0, end=2.0, direction="left"),
        ]
        start_t = time.perf_counter()
        iterations = 50
        for _ in range(iterations):
            verify_student_math_reasoning(hops, final_answer=2.0, rule=RULE_PROBLEM_1065658)
        elapsed_per_run_ms = ((time.perf_counter() - start_t) / iterations) * 1000.0

        # Assert under 5 ms per evaluation
        assert elapsed_per_run_ms < 5.0, f"Execution was too slow: {elapsed_per_run_ms:.2f} ms"
