"""Unit and regression tests for topic-aware teaching recommendations and cross-assessment isolation.

Verifies:
1. Strict assessment scoping (no cross-assessment data or recommendation leakage).
2. Mathematical topic compatibility (fraction division never receives integer number-line interventions).
3. Evidence-grounded student counts (exact count equals len(supporting_response_ids), no fabricated fallbacks).
4. Truthful representation gap handling (missing visual models are tracked as representation follow-up, not arithmetic errors).
5. Empty, unanalyzed, and all-insufficient assessment states suppress fabricated plans.
6. Topic-appropriate, SymPy-verified formative exit tickets.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from services.api.auth.service import AuthService
from services.api.main import app
from services.api.repository.memory_repo import AssessmentDoc, QuestionConfig, UserDoc, memory_repo
from services.worker.agents.contracts import DifferentiatedAction
from services.worker.cohort.contracts import CohortStatistics, MisconceptionCluster
from services.worker.cohort.recommendations import RecommendationCatalog
from services.worker.cohort.statistics_calculator import CohortStatisticsCalculator
from services.worker.cohort.synthesizer import CohortSynthesizer
from services.worker.math_verifier.task_router import TaskRouter, TaskType


@pytest.fixture
def auth_client():
    client = TestClient(app)
    user = memory_repo.get_user("usr_sarah_lim")
    if not user:
        user = UserDoc(
            id="usr_sarah_lim",
            email="teacher@classlens.demo",
            name="Mrs. Sarah Lim",
            role="Secondary 1 Mathematics Teacher",
            organization_id="org_cedar_sec",
            school="Cedar Secondary School",
            password_hash="mock_hash",
        )
        memory_repo.save_user(user)

    # Seed asm_32f82ce3 if missing in isolated test repo
    if not memory_repo.get_assessment("asm_32f82ce3", org_id="org_cedar_sec"):
        frac_asm = AssessmentDoc(
            id="asm_32f82ce3",
            organization_id="org_cedar_sec",
            title="Fraction Division — Unit Form and Visual Models",
            math_topic="Division of Fractions",
            grade_level="Primary 6",
            status="ready",
            question=QuestionConfig(
                problem_reference_id="e921e6",
                question_text="A) Rewrite 8/9 ÷ 4/9 in unit form.\nB) Find the quotient of 8/9 ÷ 4/9.\nC) Draw a model.",
                latex_formula="(8/9) / (4/9)",
                expected_answer="2",
            ),
        )
        memory_repo.create_assessment(frac_asm)

        from services.api.repository.sqlite_repository import ResponseDoc
        for i in range(1, 16):
            resp_id = f"resp_frac_{i:02d}"
            ans_st = "correct"
            reas_st = "supported_correct"
            if i in (2, 12):
                reas_st = "incomplete"
            elif i == 14:
                ans_st = "undetermined"
                reas_st = "incomplete"

            r = ResponseDoc(
                id=resp_id,
                assessment_id="asm_32f82ce3",
                pseudonymous_student_id=f"stu_f_{i}",
                pseudonym_label=f"Student-{i:02d}",
                source_filename=f"student_{i:02d}.jpg",
                answer_status=ans_st,
                reasoning_status=reas_st,
                task_status="COMPLETED",
                needs_teacher_review=(i in (2, 12, 14)),
                analysis_data={
                    "response_id": resp_id,
                    "answer_status": ans_st,
                    "reasoning_status": reas_st,
                    "needs_teacher_review": (i in (2, 12, 14)),
                    "diagnosis": {
                        "answer_status": ans_st,
                        "reasoning_status": reas_st,
                        "evidence_sufficiency": "insufficient" if i == 14 else "sufficient",
                    },
                },
            )
            memory_repo.create_response(r)

    # Seed asm_a709e8be if missing in isolated test repo
    if not memory_repo.get_assessment("asm_a709e8be", org_id="org_cedar_sec"):
        empty_asm = AssessmentDoc(
            id="asm_a709e8be",
            organization_id="org_cedar_sec",
            title="Custom Diagnostic Checkpoint d294",
            math_topic="Linear Equations and Number Lines",
            status="ready",
        )
        memory_repo.create_assessment(empty_asm)

    # Ensure integer assessment responses are marked analyzed in test session
    r1 = memory_repo.get_response("resp_56005c1c")
    if r1 and not r1.analysis_data:
        r1.task_status = "COMPLETED"
        r1.answer_status = "correct"
        r1.reasoning_status = "supported_error"
        r1.is_compensatory_error = True
        r1.misconception_taxonomy_id = "MISC-ARITH-OFF-BY-ONE"
        r1.analysis_data = {
            "response_id": "resp_56005c1c",
            "answer_status": "correct",
            "reasoning_status": "supported_error",
            "misconception_taxonomy_id": "MISC-ARITH-OFF-BY-ONE",
            "diagnosis": {
                "answer_status": "correct",
                "reasoning_status": "supported_error",
                "misconception_taxonomy_id": "MISC-ARITH-OFF-BY-ONE",
                "evidence_sufficiency": "sufficient",
            },
        }
        memory_repo.update_response(r1)

    r2 = memory_repo.get_response("resp_80545ef3")
    if r2 and not r2.analysis_data:
        r2.task_status = "COMPLETED"
        r2.answer_status = "incorrect"
        r2.reasoning_status = "supported_error"
        r2.misconception_taxonomy_id = "MISC-ARITH-OFF-BY-ONE"
        r2.analysis_data = {
            "response_id": "resp_80545ef3",
            "answer_status": "incorrect",
            "reasoning_status": "supported_error",
            "misconception_taxonomy_id": "MISC-ARITH-OFF-BY-ONE",
            "diagnosis": {
                "answer_status": "incorrect",
                "reasoning_status": "supported_error",
                "misconception_taxonomy_id": "MISC-ARITH-OFF-BY-ONE",
                "evidence_sufficiency": "sufficient",
            },
        }
        memory_repo.update_response(r2)

    session_token = AuthService.create_session_token(user)
    csrf_token = AuthService.generate_csrf_token()
    client.cookies.set("__session", session_token)
    client.cookies.set("csrf_token", csrf_token)
    return client


def test_task_router_resolves_all_math_topics():
    """Verifies TaskRouter accurately resolves topics across the curriculum."""
    # Fraction Division
    assert (
        TaskRouter.resolve_task(
            math_topic="Division of Fractions",
            question_text="Rewrite 8/9 ÷ 4/9 in unit form and draw a tape diagram",
            latex_formula=r"\frac{8}{9} \div \frac{4}{9}",
            problem_reference_id="asm_32f82ce3",
        )
        == TaskType.FRACTION_DIVISION
    )

    # Integer Number Line
    assert (
        TaskRouter.resolve_task(
            math_topic="Integer operations on number lines",
            question_text="Use the number line to evaluate -6 + 12 - 4",
            latex_formula="-6 + 12 - 4",
            problem_reference_id="asm_1065658",
        )
        == TaskType.INTEGER_NUMBER_LINE
    )

    # Decimal Operations
    assert (
        TaskRouter.resolve_task(
            math_topic="Decimal Operations and Estimation",
            question_text="Estimate the product of 3.45 and 6.2",
            latex_formula="3.45 * 6.2",
        )
        == TaskType.DECIMAL_OPERATIONS
    )

    # Place Value
    assert (
        TaskRouter.resolve_task(
            math_topic="Place Value — Hundreds, Tens and Ones",
            question_text="Represent 560 using place value disks",
            problem_reference_id="asm_012a1f01",
        )
        == TaskType.PLACE_VALUE
    )

    # Unsupported Task
    assert (
        TaskRouter.resolve_task(
            math_topic="Vector Geometry in 3D Space",
            question_text="Find the cross product of vectors u and v",
        )
        == TaskType.UNSUPPORTED_TASK
    )


def test_fraction_division_assessment_never_receives_number_line_interventions():
    """Scenario B: Fraction division assessment MUST NOT generate integer number-line recommendations."""
    # Build stats for fraction assessment where 12 students are correct and 2 have representation gaps
    fraction_stats = CohortStatistics(
        total_responses=15,
        correct_count=12,
        correct_percentage=80.0,
        error_count=0,
        error_percentage=0.0,
        incomplete_count=2,
        incomplete_percentage=13.3,
        unreadable_count=1,
        unreadable_percentage=6.7,
        misconception_clusters=[],
    )

    dummy_responses = [
        {"id": "resp_01", "answer_status": "correct", "reasoning_status": "supported_correct"},
        {"id": "resp_02", "answer_status": "correct", "reasoning_status": "incomplete"},
        {"id": "resp_03", "answer_status": "correct", "reasoning_status": "supported_correct"},
        {"id": "resp_12", "answer_status": "correct", "reasoning_status": "incomplete"},
        {"id": "resp_14", "answer_status": "undetermined", "reasoning_status": "incomplete"},
    ]

    asm = AssessmentDoc(
        id="asm_32f82ce3",
        title="Fraction Division — Unit Form and Visual Models",
        math_topic="Division of Fractions",
        question=QuestionConfig(
            question_text="Rewrite 8/9 ÷ 4/9 in unit form and draw a model",
            latex_formula=r"\frac{8}{9} \div \frac{4}{9}",
            expected_answer="2",
        ),
    )

    intelligence = CohortSynthesizer.synthesize_insights(
        fraction_stats,
        assessment=asm,
        assessment_id="asm_32f82ce3",
        responses=dummy_responses,
    )

    # 1. Must be recognized as fraction division
    assert intelligence.task_type == "fraction_division"

    # 2. Executive narrative must NOT mention number line
    assert "number line" not in intelligence.executive_narrative.lower()
    assert "-6" not in intelligence.executive_narrative
    assert "+6" not in intelligence.executive_narrative

    # 3. Interventions must NOT contain integer number line actions
    for action in intelligence.differentiated_actions:
        assert "number line" not in action.title.lower()
        assert action.target_misconception_id not in (
            "MISC-ARITH-OFF-BY-ONE",
            "MISC-DIR-INV",
            "MISC-MAG-COUNT",
            "START_POINT_ZERO_MISUNDERSTANDING",
        )

    # 4. Incomplete visual model is recognized as representation follow-up with exact count
    assert len(intelligence.differentiated_actions) == 1
    rep_action = intelligence.differentiated_actions[0]
    assert rep_action.status == "representation_followup"
    assert rep_action.student_count_affected == 2
    assert set(rep_action.supporting_response_ids) == {"resp_02", "resp_12"}

    # 5. Formative exit tickets must be fraction problems, all SymPy verified
    assert len(intelligence.formative_exit_ticket) == 3
    for ticket in intelligence.formative_exit_ticket:
        assert ticket.sympy_verified is True
        assert "/" in ticket.prompt


def test_integer_assessment_receives_only_verified_interventions_with_exact_counts():
    """Scenario A: Integer assessment with real clusters produces exact student counts without fallbacks."""
    integer_stats = CohortStatistics(
        total_responses=13,
        correct_count=7,
        correct_percentage=53.8,
        error_count=4,
        error_percentage=30.8,
        incomplete_count=1,
        incomplete_percentage=7.7,
        unreadable_count=1,
        unreadable_percentage=7.7,
        misconception_clusters=[
            MisconceptionCluster(
                taxonomy_id="MISC-ARITH-OFF-BY-ONE",
                title="Off-by-One Interval Miscount",
                affected_count=2,
                affected_percentage=15.4,
                sample_response_ids=["resp_56005c1c", "resp_80545ef3"],
            ),
            MisconceptionCluster(
                taxonomy_id="MISC-LINE-INTERVAL-MISLABEL",
                title="Number-Line Interval Mislabel",
                affected_count=1,
                affected_percentage=7.7,
                sample_response_ids=["resp_a5c95313"],
            ),
        ],
    )

    asm = AssessmentDoc(
        id="asm_1065658",
        title="Integers on Number Line: Checkpoint 1",
        math_topic="Integer operations on number lines",
        question=QuestionConfig(
            question_text="Use the number line to evaluate -6 + 12 - 4",
            latex_formula="-6 + 12 - 4",
            expected_answer="2",
        ),
    )

    intelligence = CohortSynthesizer.synthesize_insights(
        integer_stats,
        assessment=asm,
        assessment_id="asm_1065658",
    )

    assert intelligence.task_type == "integer_number_line"
    assert len(intelligence.differentiated_actions) == 2

    # Verify action 1: Off-by-one with EXACT count 2 and exact response IDs
    act1 = next(a for a in intelligence.differentiated_actions if a.target_misconception_id == "MISC-ARITH-OFF-BY-ONE")
    assert act1.student_count_affected == 2
    assert act1.supporting_response_ids == ["resp_56005c1c", "resp_80545ef3"]

    # Verify action 2: Interval mislabel with EXACT count 1 and exact response ID
    act2 = next(a for a in intelligence.differentiated_actions if a.target_misconception_id == "MISC-LINE-INTERVAL-MISLABEL")
    assert act2.student_count_affected == 1
    assert act2.supporting_response_ids == ["resp_a5c95313"]

    # No unevidenced actions (e.g. MISC-DIR-INV must NOT be present when count is 0)
    assert not any(a.target_misconception_id == "MISC-DIR-INV" for a in intelligence.differentiated_actions)


def test_empty_assessment_generates_zero_actions():
    """Scenario C: Assessments with no submitted responses generate 0 actions and 0 exit tickets."""
    empty_stats = CohortStatistics(
        total_responses=0,
        correct_count=0,
        correct_percentage=0.0,
        error_count=0,
        error_percentage=0.0,
        unreadable_count=0,
        unreadable_percentage=0.0,
        misconception_clusters=[],
    )

    intelligence = CohortSynthesizer.synthesize_insights(
        empty_stats,
        problem_id="asm_a709e8be",
        assessment_id="asm_a709e8be",
    )

    assert intelligence.cohort_status == "empty"
    assert len(intelligence.differentiated_actions) == 0
    assert len(intelligence.formative_exit_ticket) == 0
    assert "no student responses" in intelligence.executive_narrative.lower()


def test_all_insufficient_submissions_generates_zero_actions():
    """Scenario D: When all submissions have insufficient evidence, no interventions are fabricated."""
    insufficient_stats = CohortStatistics(
        total_responses=5,
        correct_count=0,
        correct_percentage=0.0,
        error_count=0,
        error_percentage=0.0,
        unreadable_count=5,
        unreadable_percentage=100.0,
        insufficient_evidence_count=5,
        insufficient_evidence_percentage=100.0,
        misconception_clusters=[],
    )

    intelligence = CohortSynthesizer.synthesize_insights(
        insufficient_stats,
        assessment_id="asm_blurry_cases",
    )

    assert intelligence.cohort_status == "all_insufficient"
    assert len(intelligence.differentiated_actions) == 0
    assert len(intelligence.formative_exit_ticket) == 0
    assert "manual review" in intelligence.executive_narrative.lower()


def test_unsupported_task_suppresses_generic_recommendations():
    """Unsupported topics return unsupported_task status and zero generic number line actions."""
    asm = AssessmentDoc(
        id="asm_advanced_calculus",
        title="Derivatives and Tangent Lines",
        math_topic="Differentiation and Chain Rule",
        question=QuestionConfig(
            question_text="Find d/dx of sin(x)",
            latex_formula=r"\frac{d}{dx}\sin(x)",
            expected_answer=r"\cos(x)",
        ),
    )
    stats = CohortStatistics(
        total_responses=10,
        correct_count=5,
        correct_percentage=50.0,
        error_count=5,
        error_percentage=50.0,
        unreadable_count=0,
        unreadable_percentage=0.0,
        misconception_clusters=[],
    )

    intelligence = CohortSynthesizer.synthesize_insights(
        stats,
        assessment=asm,
        assessment_id="asm_advanced_calculus",
    )

    assert intelligence.cohort_status == "unsupported_task"
    assert len(intelligence.differentiated_actions) == 0
    assert len(intelligence.formative_exit_ticket) == 0
    assert "outside the supported" in intelligence.executive_narrative.lower()


def test_api_insights_strict_cross_assessment_isolation(auth_client):
    """Scenario F: Switching between fraction and integer assessments preserves complete isolation."""
    # 1. Fetch Fraction Division insights
    resp_frac = auth_client.get("/api/v1/assessments/asm_32f82ce3/insights")
    assert resp_frac.status_code == 200
    data_frac = resp_frac.json()
    intel_frac = data_frac["intelligence"]

    assert intel_frac["task_type"] == "fraction_division"
    # Ensure zero integer number line actions are present
    assert not any("number line" in a["title"].lower() for a in intel_frac["differentiated_actions"])
    # Ensure exit tickets are fractions
    for ticket in intel_frac["formative_exit_ticket"]:
        assert "/" in ticket["prompt"]

    # 2. Fetch Integer Assessment insights
    resp_int = auth_client.get("/api/v1/assessments/asm_1065658/insights")
    assert resp_int.status_code == 200
    data_int = resp_int.json()
    intel_int = data_int["intelligence"]

    assert intel_int["task_type"] == "integer_number_line"
    # Ensure integer actions are present with exact counts
    int_tax_ids = [a["target_misconception_id"] for a in intel_int["differentiated_actions"]]
    assert "MISC-ARITH-OFF-BY-ONE" in int_tax_ids
    # Verify no fraction actions leaked into integer assessment
    assert not any("fraction" in a["title"].lower() for a in intel_int["differentiated_actions"])

    # 3. Fetch Empty Assessment insights
    resp_empty = auth_client.get("/api/v1/assessments/asm_a709e8be/insights")
    assert resp_empty.status_code == 200
    data_empty = resp_empty.json()
    intel_empty = data_empty["intelligence"]

    assert intel_empty["cohort_status"] == "empty"
    assert len(intel_empty["differentiated_actions"]) == 0
    assert len(intel_empty["formative_exit_ticket"]) == 0

    # 4. Fetch Fraction Division insights again to prove no cache pollution
    resp_frac_repeat = auth_client.get("/api/v1/assessments/asm_32f82ce3/insights")
    assert resp_frac_repeat.status_code == 200
    data_frac_repeat = resp_frac_repeat.json()
    assert data_frac_repeat["intelligence"]["task_type"] == "fraction_division"
    assert not any("number line" in a["title"].lower() for a in data_frac_repeat["intelligence"]["differentiated_actions"])
