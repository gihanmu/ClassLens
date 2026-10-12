"""Deterministic offline mock adapter with structured synthetic fixtures."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.worker.agents.contracts import (
    AnswerStatus,
    CandidateHypothesis,
    CandidateHypothesesOutput,
    CohortIntelligenceOutput,
    CriticAuditOutput,
    DifferentiatedAction,
    DiagnosticOutput,
    ExitTicketItem,
    FirstSupportedError,
    QualityStatus,
    ReasoningStatus,
    VerifiedStep,
    VisualEvidenceOutput,
    VisualObservation,
)
from services.worker.agents.tools import eval_sympy_arithmetic, validate_number_line_moves
from services.worker.fixtures.problem_1065658_fixtures import MOCK_FIXTURES


class MockAgentAdapter:
    """Provides deterministic, schema-validated mock outputs for all 5 ADK agents."""

    @classmethod
    def get_visual_evidence(
        cls,
        response_id: str,
        high_res_mode: bool = False,
        confidence_override: Optional[float] = None,
    ) -> VisualEvidenceOutput:
        """Emits deterministic VisualEvidenceOutput from structured synthetic fixtures."""
        fixture = MOCK_FIXTURES.get(response_id)
        if not fixture and "_resp_" in response_id:
            base_id = "resp_" + response_id.split("_resp_")[-1]
            fixture = MOCK_FIXTURES.get(base_id)
        if not fixture:
            r_lower = response_id.lower()
            if "case_01" in r_lower or "canonical" in r_lower:
                fixture = MOCK_FIXTURES["resp_04255753"]
            elif "case_02" in r_lower or "off_by_one" in r_lower or "procedural" in r_lower:
                fixture = MOCK_FIXTURES["resp_a5c95313"]
            elif "case_03" in r_lower or "ambiguous" in r_lower or "incomplete" in r_lower:
                fixture = {
                    "quality_status": "faint_readable",
                    "confidence": 0.65,
                    "has_number_line": True,
                    "final_answer_marked": None,
                    "observations": [
                        {"kind": "number_line", "value": "Faint horizontal line -8 to 8", "confidence": 0.70},
                    ],
                    "ambiguities": ["Faint pencil strokes without directional arrowheads", "Incomplete steps"],
                    "requires_teacher_review": True,
                    "teacher_review_reason": "Visual ambiguities and incomplete student work require teacher review.",
                }
            else:
                # Fallback for arbitrary response IDs: clean hop fixture
                fixture = MOCK_FIXTURES["resp_04255753"]

        conf = confidence_override if confidence_override is not None else float(fixture.get("confidence", 0.95))
        observations: List[VisualObservation] = []
        for obs in fixture.get("observations", []):
            observations.append(VisualObservation(**obs))

        q_status_str = fixture.get("quality_status", "clear")
        quality_status = QualityStatus(q_status_str)

        return VisualEvidenceOutput(
            quality_status=quality_status,
            observations=observations,
            has_number_line=bool(fixture.get("has_number_line", True)),
            final_answer_marked=fixture.get("final_answer_marked"),
            confidence=conf,
            provenance="synthetic_mock_fixture",
            resolution_mode="high_res_evaluation" if high_res_mode else "standard_768px",
        )

    @classmethod
    def get_hypotheses(
        cls,
        visual: VisualEvidenceOutput,
    ) -> CandidateHypothesesOutput:
        """Generates candidate hypotheses from visual evidence."""
        hops = [obs for obs in visual.observations if obs.kind in ("arrow_jump", "bracket_curve")]

        if not visual.has_number_line or not hops:
            return CandidateHypothesesOutput(
                hypotheses=[],
                detected_strategy="unrecognized",
                reasoning_completeness="incomplete",
                confidence=visual.confidence,
            )

        start_pt = hops[0].start_pos if hops[0].start_pos is not None else 0.0

        if abs(start_pt - 0.0) <= 1e-4:
            strat = "hop_from_zero"
            desc = "Standard sequential jumps starting from zero: 0 -> -6 -> +6 -> +2."
        elif abs(start_pt - (-6.0)) <= 1e-4:
            strat = "direct_start"
            desc = "Direct start at first term (-6) followed by jumps: -6 -> +6 -> +2."
        elif abs(start_pt - 12.0) <= 1e-4:
            strat = "commutative"
            desc = "Commutative rearrangement starting at 12: 12 -> 8 -> 2."
        else:
            strat = "unrecognized"
            desc = f"Non-standard starting coordinate at {start_pt}."

        seq = [f"Step {i+1}: {h.value}" for i, h in enumerate(hops)]

        hypothesis = CandidateHypothesis(
            hypothesis_id="hyp_01",
            starting_point=start_pt,
            strategy_description=desc,
            step_sequence=seq,
            is_valid_alternative_path=(strat != "unrecognized"),
            confidence=visual.confidence,
        )

        return CandidateHypothesesOutput(
            hypotheses=[hypothesis],
            detected_strategy=strat,
            reasoning_completeness="complete" if len(hops) >= 2 else "partial",
            confidence=visual.confidence,
        )

    @classmethod
    def get_diagnosis(
        cls,
        hypotheses: CandidateHypothesesOutput,
        visual_evidence: VisualEvidenceOutput,
        rule_expr: str = "-6 + 12 - 4",
        target_value: float = 2.0,
    ) -> DiagnosticOutput:
        """Executes real deterministic tools to evaluate reasoning and localize errors."""
        visual = visual_evidence
        hops = [obs for obs in visual.observations if obs.kind in ("arrow_jump", "bracket_curve")]

        # Case 1: Unreadable or empty response
        if visual.quality_status == QualityStatus.UNREADABLE:
            return DiagnosticOutput(
                answer_status=AnswerStatus.UNDETERMINED,
                reasoning_status=ReasoningStatus.UNDETERMINED,
                inferred_final_answer=None,
                verified_steps=[],
                first_supported_error=None,
                misconception_taxonomy_id=None,
                taxonomy_title=None,
                is_compensatory_error=False,
                confidence=0.5,
            )

        # Parse final answer
        final_ans_val: Optional[float] = None
        if visual.final_answer_marked is not None:
            try:
                final_ans_val = float(visual.final_answer_marked)
            except ValueError:
                final_ans_val = None

        # Execute real deterministic geometry tool
        moves_payload = []
        for i, h in enumerate(hops):
            moves_payload.append({
                "step_number": i + 1,
                "start": h.start_pos if h.start_pos is not None else 0.0,
                "end": h.end_pos if h.end_pos is not None else 0.0,
                "direction": h.direction or "none",
                "stated_magnitude": h.stated_magnitude,
            })

        verdict = validate_number_line_moves(
            start=moves_payload[0]["start"] if moves_payload else 0.0,
            moves=moves_payload,
            target_value=target_value,
            rule_expr=rule_expr,
            final_answer=final_ans_val,
        )

        # Build VerifiedStep records
        verified_steps: List[VerifiedStep] = []
        for st in verdict.get("verified_steps", []):
            verified_steps.append(
                VerifiedStep(
                    step_number=st["step_number"],
                    operation=f"Jump {st['start_pos']:g} to {st['end_pos']:g}",
                    expected_result=st["expected_displacement"],
                    observed_result=st["observed_displacement"],
                    is_correct=st["is_correct"],
                    evidence_citation=st["evidence_notes"],
                )
            )

        # Build FirstSupportedError if present
        first_err: Optional[FirstSupportedError] = None
        err_step = verdict.get("first_error_step")
        err_tax = verdict.get("first_error_taxonomy")

        if err_step is not None and err_tax is not None:
            err_type = "magnitude_miscount" if "OFF-BY-ONE" in err_tax else (
                "directional_sign" if "DIR-REVERSE" in err_tax else "arithmetic_slip"
            )
            first_err = FirstSupportedError(
                step_number=err_step,
                error_type=err_type,  # type: ignore[arg-type]
                observed_behavior=f"Deviation detected on Step {err_step}",
                expected_behavior="Expected correct addend displacement",
                explanation=f"Taxonomy classified as {err_tax}",
            )

        # Determine AnswerStatus & ReasoningStatus
        if verdict["is_final_answer_valid"]:
            ans_status = AnswerStatus.CORRECT
        elif final_ans_val is not None:
            ans_status = AnswerStatus.INCORRECT
        else:
            ans_status = AnswerStatus.CORRECT if verdict["is_reasoning_valid"] else AnswerStatus.UNDETERMINED

        if not hops:
            reasoning_status = ReasoningStatus.INCOMPLETE
        elif verdict["is_reasoning_valid"]:
            reasoning_status = ReasoningStatus.SUPPORTED_CORRECT
        else:
            reasoning_status = ReasoningStatus.SUPPORTED_ERROR

        return DiagnosticOutput(
            answer_status=ans_status,
            reasoning_status=reasoning_status,
            inferred_final_answer=visual.final_answer_marked or (str(int(verdict["terminal_position"])) if verdict["terminal_position"] is not None else None),
            verified_steps=verified_steps,
            first_supported_error=first_err,
            misconception_taxonomy_id=err_tax,
            taxonomy_title=err_tax,
            is_compensatory_error=bool(verdict.get("is_compensatory_error", False)),
            confidence=float(verdict.get("confidence", 0.95)),
        )

    @classmethod
    def get_critic_audit(
        cls,
        visual: Optional[VisualEvidenceOutput] = None,
        diagnosis: Optional[DiagnosticOutput] = None,
        attempt_number: int = 1,
        force_contradiction: bool = False,
        visual_evidence: Optional[VisualEvidenceOutput] = None,
    ) -> CriticAuditOutput:
        """Adversarially checks diagnosis against physical evidence."""
        vis = visual_evidence or visual
        if vis is None or diagnosis is None:
            raise ValueError("Both visual evidence and diagnosis must be provided to CriticAudit.")
        visual = vis
        # Simulated bounded retry test case
        if force_contradiction and attempt_number == 1:
            return CriticAuditOutput(
                approved=False,
                confidence=0.70,
                evidence_grounded=False,
                contradiction_detected=True,
                reinterpretation_needed=True,
                discrepancy_notes=["Critic detected contradiction on pass 1: requesting bounded reinterpretation."],
                requires_teacher_review=False,
                teacher_review_reason=None,
                critic_attempt_number=1,
            )

        # Contradiction check: claimed supported_correct reasoning without visible number line hops
        hops = [obs for obs in visual.observations if obs.kind in ("arrow_jump", "bracket_curve")]
        if diagnosis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT and not hops:
            return CriticAuditOutput(
                approved=False,
                confidence=0.90,
                evidence_grounded=False,
                contradiction_detected=True,
                reinterpretation_needed=False,
                discrepancy_notes=["Diagnosis claims supported_correct reasoning, but no arrows or jumps are physically visible."],
                requires_teacher_review=True,
                teacher_review_reason="Contradiction: reasoning claimed correct without physical evidence.",
                critic_attempt_number=attempt_number,
            )

        # Low confidence or compensatory error escalation
        needs_review = False
        review_reason = None
        if visual.confidence < 0.70 or diagnosis.confidence < 0.75:
            needs_review = True
            review_reason = "Low confidence perception/diagnosis requiring educator verification."
        elif diagnosis.is_compensatory_error:
            needs_review = True
            review_reason = "Compensatory error detected: correct final answer reached via flawed intermediate steps."
        elif diagnosis.reasoning_status == ReasoningStatus.INCOMPLETE:
            needs_review = True
            review_reason = "Incomplete reasoning: final answer marked without showing working."
        elif visual.quality_status == QualityStatus.UNREADABLE:
            needs_review = True
            review_reason = "Unreadable student submission."

        return CriticAuditOutput(
            approved=True,
            confidence=0.95,
            evidence_grounded=True,
            contradiction_detected=False,
            reinterpretation_needed=False,
            discrepancy_notes=[],
            requires_teacher_review=needs_review,
            teacher_review_reason=review_reason,
            critic_attempt_number=attempt_number,
        )

    @classmethod
    def get_cohort_intelligence(
        cls,
        cohort_stats: Dict[str, Any],
    ) -> CohortIntelligenceOutput:
        """Synthesizes deterministic cohort statistics into qualitative narratives and exit ticket."""
        total = cohort_stats.get("total_students", 0)
        correct_pct = cohort_stats.get("correct_answers_pct", 0.0)
        valid_reasoning_pct = cohort_stats.get("valid_reasoning_pct", 0.0)
        compensatory_count = cohort_stats.get("compensatory_errors", 0)
        clusters = cohort_stats.get("misconception_clusters", [])

        narrative = (
            f"Class Assessment Analysis ({total} students): "
            f"{correct_pct}% achieved the correct final answer, but only {valid_reasoning_pct}% demonstrated "
            f"fully valid number line reasoning. {compensatory_count} student(s) arrived at the correct answer "
            f"through compensatory errors. Dominant systemic misconception: "
            f"{clusters[0]['taxonomy_id'] if clusters else 'None identified'}."
        )

        dominant_misconceptions = [c["taxonomy_id"] for c in clusters[:2]]

        actions: List[DifferentiatedAction] = []
        if clusters:
            top_tax = clusters[0]["taxonomy_id"]
            actions.append(
                DifferentiatedAction(
                    target_misconception_id=top_tax,
                    action_type="worked_example",
                    title="Number Line Hop Modeling & Sign Alignment",
                    instructional_steps=[
                        "Model signed integer jumps using physical counters on a large-format number line.",
                        "Explicitly emphasize tick mark counting vs interval jumping to resolve off-by-one errors.",
                    ],
                    student_count_affected=clusters[0]["count"],
                )
            )

        # Generate 3 exit ticket items and verify via SymPy tool
        exit_tickets: List[ExitTicketItem] = []
        stems = [
            ("-4 + 8 - 2", "2", "MISC-ARITH-OFF-BY-ONE"),
            ("-5 + 10 - 3", "2", "MISC-NUM-DIR-REVERSE"),
            ("6 - 10 + 4", "0", "MISC-ARITH-SLIP"),
        ]
        for idx, (expr, expected, tax) in enumerate(stems, start=1):
            eval_res = eval_sympy_arithmetic(expr, float(expected))
            exit_tickets.append(
                ExitTicketItem(
                    question_number=idx,
                    prompt=f"Evaluate using a number line: {expr}",
                    target_misconception=tax,
                    expected_answer=expected,
                    sympy_verified=bool(eval_res.get("is_equal", True)),
                )
            )

        return CohortIntelligenceOutput(
            executive_narrative=narrative,
            dominant_misconceptions=dominant_misconceptions,
            differentiated_actions=actions,
            formative_exit_ticket=exit_tickets,
        )
