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


BENCHMARK_FIXTURES: Dict[str, Dict[str, Any]] = {
    "bench_sign_flip_hop2": {
        "response_id": "bench_sign_flip_hop2",
        "quality_status": "clear",
        "confidence": 0.95,
        "has_number_line": True,
        "final_answer_marked": "-22",
        "observations": [
            {"kind": "number_line", "value": "Extended number line [-25, 10]", "confidence": 0.98},
            {"kind": "arrow_jump", "value": "Jump 0 to -6", "confidence": 0.95, "start_pos": 0.0, "end_pos": -6.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -6 to -18 (directional reversal)", "confidence": 0.95, "start_pos": -6.0, "end_pos": -18.0, "direction": "left"},
            {"kind": "arrow_jump", "value": "Jump -18 to -22", "confidence": 0.94, "start_pos": -18.0, "end_pos": -22.0, "direction": "left"},
            {"kind": "circled_result", "value": "-22", "confidence": 0.98},
        ],
    },
    "bench_faint_overlapping": {
        "response_id": "bench_faint_overlapping",
        "quality_status": "faint_readable",
        "confidence": 0.55,
        "has_number_line": True,
        "final_answer_marked": None,
        "observations": [
            {"kind": "number_line", "value": "Faint horizontal line with overlapping marks", "confidence": 0.65},
            {"kind": "arrow_jump", "value": "Faint arc 0 to -6 (missing arrowhead)", "confidence": 0.60, "start_pos": 0.0, "end_pos": -6.0, "direction": "none"},
            {"kind": "arrow_jump", "value": "Overlapping incomplete arc near -6 (missing endpoint)", "confidence": 0.35, "start_pos": -6.0, "end_pos": None, "direction": "none"},
        ],
        "ambiguities": [
            "Overlapping erased pencil marks",
            "Missing directional arrowhead and missing terminal coordinate",
        ],
        "requires_teacher_review": True,
        "teacher_review_reason": "Overlapping strokes and missing coordinate endpoints require educator review.",
    },
}


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
        fixture = MOCK_FIXTURES.get(response_id) or BENCHMARK_FIXTURES.get(response_id)
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
                    "confidence": 0.60,
                    "has_number_line": True,
                    "final_answer_marked": None,
                    "observations": [
                        {"kind": "number_line", "value": "Faint horizontal line [-8, 8]", "confidence": 0.70},
                        {
                            "kind": "arrow_jump",
                            "value": "Faint arc 0 to -6 (missing arrowhead)",
                            "confidence": 0.65,
                            "start_pos": 0.0,
                            "end_pos": -6.0,
                            "direction": "none",
                        },
                        {
                            "kind": "arrow_jump",
                            "value": "Incomplete arc near -6 (missing endpoint)",
                            "confidence": 0.40,
                            "start_pos": -6.0,
                            "end_pos": None,
                            "direction": "none",
                        },
                    ],
                    "ambiguities": [
                        "Faint pencil strokes without directional arrowheads",
                        "Hop #2 terminates ambiguously near 1-2 without clear endpoint",
                    ],
                    "requires_teacher_review": True,
                    "teacher_review_reason": "Visual ambiguities and incomplete student work require teacher review.",
                }
            elif response_id.startswith("upl_"):
                fixture = {
                    "quality_status": "clear",
                    "confidence": 0.0,
                    "has_number_line": False,
                    "final_answer_marked": None,
                    "observations": [],
                    "ambiguities": ["Unseen uploaded worksheet requires live visual analysis."],
                    "requires_teacher_review": True,
                    "teacher_review_reason": "Live visual analysis required for unseen uploaded worksheet.",
                    "provenance": "unseen_upload",
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
            provenance=fixture.get("provenance", "synthetic_mock_fixture"),
            resolution_mode="high_res_evaluation" if high_res_mode else "standard_768px",
            ambiguities=fixture.get("ambiguities", []),
            requires_teacher_review=bool(fixture.get("requires_teacher_review", False)),
            teacher_review_reason=fixture.get("teacher_review_reason"),
        )

    @classmethod
    def get_hypotheses(
        cls,
        visual: VisualEvidenceOutput,
    ) -> CandidateHypothesesOutput:
        """Generates candidate hypotheses from visual evidence."""
        from services.worker.agents.evidence_sufficiency import EvidenceSufficiencyEvaluator

        sufficiency = EvidenceSufficiencyEvaluator.evaluate(visual)
        hops = [obs for obs in visual.observations if obs.kind in ("arrow_jump", "bracket_curve")]

        if not visual.has_number_line or not hops or sufficiency.overall_sufficiency == "insufficient":
            hypotheses_list: List[CandidateHypothesis] = []
            if hops:
                hypotheses_list.append(
                    CandidateHypothesis(
                        hypothesis_id="hyp_insufficient",
                        starting_point=hops[0].start_pos if hops[0].start_pos is not None else 0.0,
                        strategy_description="Insufficient or ambiguous visual evidence: cannot reliably infer mathematical strategy.",
                        step_sequence=[f"Observed mark {i+1}: {h.value}" for i, h in enumerate(hops)],
                        is_valid_alternative_path=False,
                        confidence=min(visual.confidence, 0.60),
                    )
                )

            return CandidateHypothesesOutput(
                hypotheses=hypotheses_list,
                detected_strategy="insufficient_evidence" if hops else "unrecognized",
                reasoning_completeness="incomplete",
                confidence=min(visual.confidence, 0.60) if sufficiency.overall_sufficiency == "insufficient" else visual.confidence,
                evidence_support="insufficient_evidence",
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

        ev_support = "partially_supported" if sufficiency.overall_sufficiency == "partial" else "supported"
        completeness = "partial" if sufficiency.overall_sufficiency == "partial" else ("complete" if len(hops) >= 2 else "partial")

        return CandidateHypothesesOutput(
            hypotheses=[hypothesis],
            detected_strategy=strat,
            reasoning_completeness=completeness,
            confidence=visual.confidence,
            evidence_support=ev_support,
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
        from services.worker.agents.evidence_sufficiency import EvidenceSufficiencyEvaluator

        visual = visual_evidence
        hops = [obs for obs in visual.observations if obs.kind in ("arrow_jump", "bracket_curve")]
        sufficiency = EvidenceSufficiencyEvaluator.evaluate(visual)

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
                evidence_sufficiency="insufficient",
                diagnostic_explanation="Student worksheet handwriting is unreadable. Manual teacher inspection is required.",
            )

        # Parse final answer
        final_ans_val: Optional[float] = None
        if visual.final_answer_marked is not None:
            try:
                final_ans_val = float(visual.final_answer_marked)
            except ValueError:
                final_ans_val = None

        # Execute real deterministic geometry tool passing evidence_status
        moves_payload = []
        for i, h in enumerate(hops):
            step_eval = (
                sufficiency.step_evaluations[i]
                if i < len(sufficiency.step_evaluations)
                else None
            )
            ev_status = step_eval.evidence_status if step_eval else "supported"
            start_coord = h.start_pos if h.start_pos is not None else 0.0
            end_coord = h.end_pos if h.end_pos is not None else start_coord
            moves_payload.append({
                "step_number": i + 1,
                "start": start_coord,
                "end": end_coord,
                "direction": h.direction or "none",
                "stated_magnitude": h.stated_magnitude,
                "evidence_status": ev_status,
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
            is_unverifiable = (
                st.get("verification_status") == "unverifiable"
                or st.get("evidence_status") == "insufficient_evidence"
            )
            st_ev_status = st.get("evidence_status", "supported")
            st_verif_status = st.get("verification_status", "verified_valid")

            start_val = st["start_pos"]
            end_val = st["end_pos"]
            step_idx = st["step_number"] - 1
            if is_unverifiable and step_idx < len(hops) and hops[step_idx].end_pos is None:
                op_label = f"Incomplete jump starting at {start_val:g}"
            else:
                op_label = f"Jump {start_val:g} to {end_val:g}"

            verified_steps.append(
                VerifiedStep(
                    step_number=st["step_number"],
                    operation=op_label,
                    expected_result=st["expected_displacement"],
                    observed_result=st["observed_displacement"] if not is_unverifiable else None,
                    is_correct=st["is_correct"],
                    evidence_citation=st["evidence_notes"],
                    evidence_status=st_ev_status,
                    verification_status=st_verif_status,
                )
            )

        # Build FirstSupportedError if present AND evidence permits diagnosing misconception
        first_err: Optional[FirstSupportedError] = None
        err_step = verdict.get("first_error_step")
        err_tax = verdict.get("first_error_taxonomy")

        # GATE 4A.2 CORE PRINCIPLE: Never infer misconception when evidence is insufficient
        if sufficiency.can_diagnose_misconception and err_step is not None and err_tax is not None:
            err_type = "magnitude_miscount" if ("OFF-BY-ONE" in err_tax or "MISLABEL" in err_tax) else (
                "directional_sign" if "DIR-REVERSE" in err_tax else "arithmetic_slip"
            )
            first_err = FirstSupportedError(
                step_number=err_step,
                error_type=err_type,  # type: ignore[arg-type]
                observed_behavior=f"Deviation detected on Step {err_step}",
                expected_behavior="Expected correct addend displacement",
                explanation=f"Taxonomy classified as {err_tax}",
            )
        elif not hops and visual.final_answer_marked is not None:
            err_tax = "REASONING_INCOMPLETE"
        else:
            err_tax = None

        # Determine AnswerStatus & ReasoningStatus
        if verdict["is_final_answer_valid"]:
            ans_status = AnswerStatus.CORRECT
        elif final_ans_val is not None:
            ans_status = AnswerStatus.INCORRECT
        elif sufficiency.overall_sufficiency == "insufficient" or not verdict["is_reasoning_valid"]:
            ans_status = AnswerStatus.UNDETERMINED
        else:
            ans_status = AnswerStatus.CORRECT

        if not hops:
            reasoning_status = ReasoningStatus.INCOMPLETE
        elif sufficiency.overall_sufficiency == "insufficient":
            reasoning_status = ReasoningStatus.INCOMPLETE
        elif verdict["is_reasoning_valid"]:
            reasoning_status = ReasoningStatus.SUPPORTED_CORRECT
        else:
            reasoning_status = ReasoningStatus.SUPPORTED_ERROR

        # Generate diagnostic explanation
        if sufficiency.overall_sufficiency == "insufficient":
            diag_expl = (
                "Mathematical reasoning cannot be definitively diagnosed: visual evidence is incomplete or ambiguous "
                "(faint strokes, missing arrowheads, or missing endpoints). Educator review is required to interpret student work."
            )
        elif verdict["is_reasoning_valid"]:
            diag_expl = "All observed number-line steps were deterministically verified as mathematically valid."
        elif err_tax:
            diag_expl = f"Procedural deviation identified on Step {err_step}: classified as {err_tax}."
        else:
            diag_expl = "Reasoning contains unverified or inconsistent steps requiring educator review."

        inferred_ans = None
        if visual.final_answer_marked:
            inferred_ans = visual.final_answer_marked
        elif (
            verdict["is_reasoning_valid"]
            and sufficiency.overall_sufficiency != "insufficient"
            and verdict["terminal_position"] is not None
        ):
            inferred_ans = str(int(verdict["terminal_position"]))

        return DiagnosticOutput(
            answer_status=ans_status,
            reasoning_status=reasoning_status,
            inferred_final_answer=inferred_ans,
            verified_steps=verified_steps,
            first_supported_error=first_err,
            misconception_taxonomy_id=err_tax,
            taxonomy_title=err_tax,
            is_compensatory_error=bool(verdict.get("is_compensatory_error", False)),
            confidence=float(verdict.get("confidence", 0.95)),
            evidence_sufficiency=sufficiency.overall_sufficiency,
            diagnostic_explanation=diag_expl,
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
                audit_verdict="audit_rejected",
            )

        discrepancies: List[str] = []
        hops = [obs for obs in visual.observations if obs.kind in ("arrow_jump", "bracket_curve")]

        # 1. Contradiction check: claimed supported_correct reasoning without visible number line hops
        if diagnosis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT and not hops:
            discrepancies.append("Diagnosis claims supported_correct reasoning, but no arrows or jumps are physically visible.")
            return CriticAuditOutput(
                approved=False,
                confidence=0.90,
                evidence_grounded=False,
                contradiction_detected=True,
                reinterpretation_needed=False,
                discrepancy_notes=discrepancies,
                requires_teacher_review=True,
                teacher_review_reason="Contradiction: reasoning claimed correct without physical evidence.",
                critic_attempt_number=attempt_number,
                audit_verdict="audit_rejected",
            )

        # 2. Contradiction check: Hallucinated steps (more steps claimed than physically visible)
        if len(diagnosis.verified_steps) > len(hops) and hops:
            discrepancies.append(
                f"Contradiction: Hallucinated steps: diagnosis verified {len(diagnosis.verified_steps)} steps but only {len(hops)} marks are physically visible."
            )
            return CriticAuditOutput(
                approved=False,
                confidence=0.85,
                evidence_grounded=False,
                contradiction_detected=True,
                reinterpretation_needed=False,
                discrepancy_notes=discrepancies,
                requires_teacher_review=True,
                teacher_review_reason="Contradiction: Hallucinated steps without physical evidence.",
                critic_attempt_number=attempt_number,
                audit_verdict="audit_rejected",
            )

        # 3. Contradiction check: Procedural misconception assigned despite insufficient evidence
        if (
            diagnosis.misconception_taxonomy_id is not None
            and diagnosis.misconception_taxonomy_id != "REASONING_INCOMPLETE"
            and diagnosis.evidence_sufficiency == "insufficient"
        ):
            discrepancies.append(
                f"Contradiction: Misconception '{diagnosis.misconception_taxonomy_id}' assigned on insufficient visual evidence."
            )
            return CriticAuditOutput(
                approved=False,
                confidence=0.55,
                evidence_grounded=False,
                contradiction_detected=True,
                reinterpretation_needed=False,
                discrepancy_notes=discrepancies,
                requires_teacher_review=True,
                teacher_review_reason="Contradiction: Misconception assigned without supported evidence.",
                critic_attempt_number=attempt_number,
                audit_verdict="audit_rejected",
            )

        # 4. Contradiction check: Supported correct reasoning despite mathematically invalid steps
        if (
            diagnosis.reasoning_status == ReasoningStatus.SUPPORTED_CORRECT
            and diagnosis.verified_steps
            and any(not s.is_correct for s in diagnosis.verified_steps)
        ):
            discrepancies.append(
                "Contradiction: Reasoning claimed supported_correct but verified steps contain mathematical deviations."
            )
            return CriticAuditOutput(
                approved=False,
                confidence=0.90,
                evidence_grounded=False,
                contradiction_detected=True,
                reinterpretation_needed=False,
                discrepancy_notes=discrepancies,
                requires_teacher_review=True,
                teacher_review_reason="Contradiction: Mathematical reasoning validity contradicted by step verification.",
                critic_attempt_number=attempt_number,
                audit_verdict="audit_rejected",
            )

        # 3. Grounding audit & teacher review requirement
        needs_review = False
        review_reasons: List[str] = []

        if visual.requires_teacher_review:
            needs_review = True
            review_reasons.append(visual.teacher_review_reason or "Visual extraction flagged perceptual ambiguities.")
        if diagnosis.evidence_sufficiency == "insufficient":
            needs_review = True
            review_reasons.append("Visual evidence is incomplete or ambiguous; educator review required.")
        elif diagnosis.evidence_sufficiency == "partial":
            needs_review = True
            review_reasons.append("Partial evidence only; some student steps are unverifiable.")
        if visual.confidence < 0.70 or diagnosis.confidence < 0.75:
            needs_review = True
            review_reasons.append("Low confidence perception or diagnosis requiring educator verification.")
        if diagnosis.is_compensatory_error:
            needs_review = True
            review_reasons.append("Compensatory error detected: correct final answer reached via flawed intermediate steps.")
        if diagnosis.reasoning_status == ReasoningStatus.INCOMPLETE:
            needs_review = True
            review_reasons.append("Incomplete reasoning: student work does not show full step sequence.")
        if visual.quality_status == QualityStatus.UNREADABLE:
            needs_review = True
            review_reasons.append("Unreadable student submission.")

        # Critic confidence: heuristic indicator based on evidence sufficiency and review flags
        if needs_review:
            critic_conf = min(visual.confidence, diagnosis.confidence, 0.65)
            audit_verdict: Literal["audit_passed", "review_required", "audit_rejected"] = "review_required"
        else:
            critic_conf = 0.95
            audit_verdict = "audit_passed"

        return CriticAuditOutput(
            approved=True,
            confidence=critic_conf,
            evidence_grounded=(diagnosis.evidence_sufficiency != "insufficient"),
            contradiction_detected=False,
            reinterpretation_needed=False,
            discrepancy_notes=discrepancies,
            requires_teacher_review=needs_review,
            teacher_review_reason="; ".join(review_reasons) if review_reasons else None,
            critic_attempt_number=attempt_number,
            audit_verdict=audit_verdict,
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
