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
)
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.agents.provider import VisualEvidenceProvider, get_visual_evidence_provider
from services.worker.agents.tools import compute_cohort_statistics


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
    ) -> StudentResponseAnalysis:
        """Executes the per-response multi-agent sequential pipeline with bounded adversarial audit.

        Pipeline Stages:
        1. VisualEvidenceAgent: transcribes visible physical marks into VisualEvidenceOutput.
        2. MathInterpretationAgent: generates candidate mathematical step hypotheses.
        3. DiagnosticAgent: runs deterministic SymPy and geometry tools to localize errors.
        4. IndependentCriticAgent: adversarially audits diagnosis; triggers at most 1 reinterpretation pass.
        5. Uncertainty Propagation: enforces review thresholds and outputs final StudentResponseAnalysis.

        Args:
            response_id: Student response identifier.
            high_res_mode: Configurable option for future high-resolution evaluation.
            force_critic_retry: Test flag simulating Critic discrepancy on pass 1.
            confidence_override: Test override for visual perception confidence.
            rule_expr: Arithmetic expression string.
            target_value: Expected target numerical value.
            provider: Optional injected VisualEvidenceProvider (defaults to configured provider).
            image_source: Optional file path or raw image bytes for visual evidence extraction.
            auth_key: Optional explicit owner authorization key for live Gemini execution.

        Returns:
            Validated StudentResponseAnalysis Pydantic record.
        """
        start_t = time.perf_counter()
        reinterpretation_attempted = False

        # Stage 1: VisualEvidenceAgent
        active_provider = provider or get_visual_evidence_provider(auth_key=auth_key)
        visual_evidence = active_provider.extract_evidence(
            response_id=response_id,
            image_source=image_source,
            high_res_mode=high_res_mode,
            confidence_override=confidence_override,
            auth_key=auth_key,
        )

        # Stage 2: MathInterpretationAgent
        hypotheses = MockAgentAdapter.get_hypotheses(visual_evidence)

        # Stage 3: DiagnosticAgent (runs deterministic SymPy and geometry tools)
        diagnosis = MockAgentAdapter.get_diagnosis(
            hypotheses=hypotheses,
            visual_evidence=visual_evidence,
            rule_expr=rule_expr,
            target_value=target_value,
        )

        # Stage 4: IndependentCriticAgent (Adversarial Audit - Pass 1)
        critic_audit = MockAgentAdapter.get_critic_audit(
            visual=visual_evidence,
            diagnosis=diagnosis,
            attempt_number=1,
            force_contradiction=force_critic_retry,
        )

        # Bounded Reinterpretation (At most ONE retry pass)
        if critic_audit.reinterpretation_needed:
            reinterpretation_attempted = True
            # Pass 2: Reinterpretation and re-diagnosis
            hypotheses = MockAgentAdapter.get_hypotheses(visual_evidence)
            diagnosis = MockAgentAdapter.get_diagnosis(
                hypotheses=hypotheses,
                visual_evidence=visual_evidence,
                rule_expr=rule_expr,
                target_value=target_value,
            )
            # Pass 2 audit: forced contradiction is cleared on pass 2
            critic_audit = MockAgentAdapter.get_critic_audit(
                visual=visual_evidence,
                diagnosis=diagnosis,
                attempt_number=2,
                force_contradiction=False,
            )

        # Stage 5: Uncertainty Propagation & Teacher Escalation
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
        tokens_consumed = getattr(active_provider, "last_tokens", 0)
        cost_usd = getattr(active_provider, "last_cost_usd", None)
        telemetry = getattr(active_provider, "last_telemetry", None)

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
        )

    @classmethod
    def analyze_cohort(
        cls,
        responses: List[StudentResponseAnalysis],
    ) -> CohortIntelligenceOutput:
        """Executes Agent 5: CohortIntelligenceAgent for an entire assessment batch.

        Enforces deterministic ground truth for all frequencies and counts.

        Args:
            responses: List of StudentResponseAnalysis records for the cohort.

        Returns:
            CohortIntelligenceOutput with executive narrative and SymPy-verified exit ticket.
        """
        response_dicts = [r.model_dump() for r in responses]
        cohort_stats = compute_cohort_statistics(response_dicts)
        return MockAgentAdapter.get_cohort_intelligence(cohort_stats)
