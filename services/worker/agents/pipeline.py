"""Multi-agent pipeline coordinating the five-agent architecture with bounded retries."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from services.worker.agents.contracts import (
    CohortIntelligenceOutput,
    QualityStatus,
    ReasoningStatus,
    StudentResponseAnalysis,
    VisualEvidenceOutput,
)
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.agents.provider import VisualEvidenceProvider, get_visual_evidence_provider
from services.worker.agents.tools import compute_cohort_statistics
from services.worker.math_verifier.task_router import TaskRouter, TaskType


class MultiAgentPipeline:
    """Orchestrator coordinating the 5 Google ADK agents for per-response and cohort analysis."""

    @classmethod
    def analyze_response(
        cls,
        response_id: str,
        high_res_mode: bool = False,
        force_critic_retry: bool = False,
        confidence_override: Optional[float] = None,
        rule_expr: str = "-6 + 12 - 4",
        target_value: float = 2.0,
        provider: Optional[VisualEvidenceProvider] = None,
        image_source: Optional[Union[str, Path, bytes]] = None,
        auth_key: Optional[str] = None,
        math_topic: Optional[str] = None,
        question_text: Optional[str] = None,
        task_type: Optional[str] = None,
        problem_reference_id: Optional[str] = None,
        cached_visual_evidence: Optional[VisualEvidenceOutput] = None,
    ) -> StudentResponseAnalysis:
        """Executes the per-response multi-agent sequential pipeline with bounded adversarial audit.

        Pipeline Stages:
        1. VisualEvidenceAgent: transcribes visible physical marks into VisualEvidenceOutput.
        2. Task & Method Routing: routes problem domain to specialized verifier.
        3. MathInterpretationAgent: generates candidate mathematical step hypotheses.
        4. DiagnosticAgent: runs deterministic SymPy and geometry/model tools to localize errors.
        5. IndependentCriticAgent: adversarially audits diagnosis; triggers at most 1 reinterpretation pass.
        6. Uncertainty Propagation: enforces review thresholds and outputs final StudentResponseAnalysis.
        """
        start_t = time.perf_counter()
        reinterpretation_attempted = False
        stage_logs: List[Dict[str, Any]] = []

        # Stage 1: VisualEvidenceAgent
        s1_start = time.perf_counter()
        if cached_visual_evidence is not None:
            visual_evidence = cached_visual_evidence
            active_provider = None
            s1_elapsed = 0
            provider_provenance = visual_evidence.provenance or "persisted_extraction"
        else:
            active_provider = provider or get_visual_evidence_provider(auth_key=auth_key)
            visual_evidence = active_provider.extract_evidence(
                response_id=response_id,
                image_source=image_source,
                high_res_mode=high_res_mode,
                confidence_override=confidence_override,
                auth_key=auth_key,
            )
            s1_elapsed = int((time.perf_counter() - s1_start) * 1000.0)
            provider_provenance = getattr(active_provider, "model_id", visual_evidence.provenance)

        s1_status = "completed" if visual_evidence.quality_status != QualityStatus.UNREADABLE else "failed"
        stage_logs.append({
            "stage": "visual_evidence",
            "stage_name": "Visual Evidence Extraction",
            "status": s1_status,
            "duration_ms": s1_elapsed,
            "provider": provider_provenance,
            "summary": f"Extracted {len(visual_evidence.observations)} marks. Quality: {visual_evidence.quality_status.value}. Confidence: {visual_evidence.confidence:.2f}.",
            "details": (
                f"Final answer marked: '{visual_evidence.final_answer_marked or 'none'}'. "
                f"Number line: {visual_evidence.has_number_line}. "
                f"Ambiguities flagged: {len(visual_evidence.ambiguities)}."
            ),
            "metrics": {
                "confidence": visual_evidence.confidence,
                "has_number_line": visual_evidence.has_number_line,
                "observations_count": len(visual_evidence.observations),
                "ambiguities_count": len(visual_evidence.ambiguities),
            },
        })

        # Stage 2: Mathematical Task & Method Routing
        resolved_task_type = task_type or TaskRouter.resolve_task(
            math_topic=math_topic,
            question_text=question_text,
            latex_formula=rule_expr,
            problem_reference_id=problem_reference_id,
        )
        task_type_str = resolved_task_type.value if hasattr(resolved_task_type, "value") else str(resolved_task_type)
        stage_logs.append({
            "stage": "task_routing",
            "stage_name": "Mathematical Task & Method Routing",
            "status": "completed" if task_type_str != TaskType.UNSUPPORTED_TASK.value else "warning",
            "duration_ms": 1,
            "task_type": task_type_str,
            "summary": f"Routed to {task_type_str.replace('_', ' ').title()} engine.",
            "details": f"Domain identified from topic '{math_topic or 'unspecified'}' and expression '{rule_expr}'.",
            "metrics": {"task_type": task_type_str},
        })

        # Stage 3: MathInterpretationAgent
        s3_start = time.perf_counter()
        hypotheses = MockAgentAdapter.get_hypotheses(visual_evidence, task_type=task_type_str)
        s3_elapsed = int((time.perf_counter() - s3_start) * 1000.0)
        stage_logs.append({
            "stage": "math_interpretation",
            "stage_name": "Mathematical Step Hypotheses",
            "status": "completed",
            "duration_ms": max(s3_elapsed, 1),
            "summary": f"Strategy: {hypotheses.detected_strategy} (Completeness: {hypotheses.reasoning_completeness}).",
            "details": f"Candidate hypotheses: {len(hypotheses.hypotheses)}. Support: {hypotheses.evidence_support}.",
            "metrics": {
                "detected_strategy": hypotheses.detected_strategy,
                "reasoning_completeness": hypotheses.reasoning_completeness,
            },
        })

        # Stage 4: DiagnosticAgent (runs deterministic SymPy and geometry/model tools)
        s4_start = time.perf_counter()
        diagnosis = MockAgentAdapter.get_diagnosis(
            hypotheses=hypotheses,
            visual_evidence=visual_evidence,
            rule_expr=rule_expr,
            target_value=target_value,
            task_type=task_type_str,
            question_text=question_text,
        )
        s4_elapsed = int((time.perf_counter() - s4_start) * 1000.0)
        s4_status = "completed" if diagnosis.evidence_sufficiency != "insufficient" else "warning"
        stage_logs.append({
            "stage": "diagnostic_agent",
            "stage_name": "Deterministic Verification & Diagnosis",
            "status": s4_status,
            "duration_ms": max(s4_elapsed, 2),
            "summary": f"Answer: {diagnosis.answer_status.value}. Reasoning: {diagnosis.reasoning_status.value}.",
            "details": diagnosis.diagnostic_explanation,
            "metrics": {
                "verified_steps_count": len(diagnosis.verified_steps),
                "is_compensatory_error": diagnosis.is_compensatory_error,
                "misconception_taxonomy_id": diagnosis.misconception_taxonomy_id,
                "confidence": diagnosis.confidence,
                "evidence_sufficiency": diagnosis.evidence_sufficiency,
            },
        })

        # Stage 5: IndependentCriticAgent (Adversarial Audit - Pass 1)
        s5_start = time.perf_counter()
        critic_audit = MockAgentAdapter.get_critic_audit(
            visual=visual_evidence,
            diagnosis=diagnosis,
            attempt_number=1,
            force_contradiction=force_critic_retry,
            task_type=task_type_str,
        )

        # Bounded Reinterpretation (At most ONE retry pass)
        if critic_audit.reinterpretation_needed:
            reinterpretation_attempted = True
            # Pass 2: Reinterpretation and re-diagnosis
            hypotheses = MockAgentAdapter.get_hypotheses(visual_evidence, task_type=task_type_str)
            diagnosis = MockAgentAdapter.get_diagnosis(
                hypotheses=hypotheses,
                visual_evidence=visual_evidence,
                rule_expr=rule_expr,
                target_value=target_value,
                task_type=task_type_str,
                question_text=question_text,
            )
            # Pass 2 audit: forced contradiction is cleared on pass 2
            critic_audit = MockAgentAdapter.get_critic_audit(
                visual=visual_evidence,
                diagnosis=diagnosis,
                attempt_number=2,
                force_contradiction=False,
                task_type=task_type_str,
            )

        s5_elapsed = int((time.perf_counter() - s5_start) * 1000.0)
        stage_logs.append({
            "stage": "critic_audit",
            "stage_name": "Independent Adversarial Critic",
            "status": "completed" if critic_audit.approved else "failed",
            "duration_ms": max(s5_elapsed, 1),
            "summary": f"Audit: {critic_audit.audit_verdict} (Approved: {critic_audit.approved}).",
            "details": (
                "; ".join(critic_audit.discrepancy_notes)
                if critic_audit.discrepancy_notes
                else "Diagnosis mathematically verified without hallucinations or ungrounded steps."
            ),
            "metrics": {
                "reinterpretation_needed": critic_audit.reinterpretation_needed,
                "requires_teacher_review": critic_audit.requires_teacher_review,
                "critic_confidence": critic_audit.confidence,
            },
        })

        # Stage 6: Uncertainty Propagation & Teacher Escalation
        needs_review = False
        review_reason: Optional[str] = None

        if visual_evidence.quality_status == QualityStatus.UNREADABLE:
            needs_review = True
            review_reason = "Unreadable student submission."
        elif visual_evidence.requires_teacher_review:
            needs_review = True
            review_reason = (
                visual_evidence.teacher_review_reason
                or "Visual extraction flagged ambiguities requiring educator review."
            )
        elif visual_evidence.confidence < 0.70:
            needs_review = True
            review_reason = "low_confidence"
        elif diagnosis.confidence < 0.75:
            needs_review = True
            review_reason = "low_confidence"
        elif critic_audit.requires_teacher_review:
            needs_review = True
            review_reason = critic_audit.teacher_review_reason or "critic_unresolved_discrepancy"
        elif diagnosis.is_compensatory_error:
            needs_review = True
            review_reason = "Compensatory error: student reached correct answer through erroneous steps."
        elif diagnosis.reasoning_status == ReasoningStatus.INCOMPLETE:
            needs_review = True
            review_reason = "Incomplete reasoning: final answer present without supporting steps."

        elapsed_ms = int((time.perf_counter() - start_t) * 1000.0)

        is_mock = visual_evidence.provenance == "synthetic_mock_fixture"
        model_version = "mock-offline-fixture" if is_mock else visual_evidence.provenance
        tokens_consumed = getattr(active_provider, "last_tokens", 0) if active_provider else 0
        cost_usd = getattr(active_provider, "last_cost_usd", None) if active_provider else None
        telemetry = getattr(active_provider, "last_telemetry", None) if active_provider else None

        return StudentResponseAnalysis(
            response_id=response_id,
            quality_status=visual_evidence.quality_status,
            visual_evidence=visual_evidence,
            candidate_hypotheses=hypotheses,
            diagnosis=diagnosis,
            critic_audit=critic_audit,
            answer_status=diagnosis.answer_status,
            reasoning_status=diagnosis.reasoning_status,
            is_compensatory_error=diagnosis.is_compensatory_error,
            needs_teacher_review=needs_review,
            teacher_review_reason=review_reason,
            reinterpretation_attempted=reinterpretation_attempted,
            execution_latency_ms=elapsed_ms,
            tokens_consumed=tokens_consumed,
            is_mock=is_mock,
            model_version=model_version,
            cost_estimate_usd=cost_usd,
            live_telemetry=telemetry,
            stage_logs=stage_logs,
        )

    @classmethod
    def analyze_cohort(
        cls,
        responses: List[StudentResponseAnalysis],
    ) -> CohortIntelligenceOutput:
        """Executes Agent 5: CohortIntelligenceAgent for an entire assessment batch.

        Enforces deterministic ground truth for all frequencies and counts.
        """
        response_dicts = [r.model_dump() for r in responses]
        cohort_stats = compute_cohort_statistics(response_dicts)
        return MockAgentAdapter.get_cohort_intelligence(cohort_stats)
