"""Inline asynchronous dispatcher for offline local development."""

from __future__ import annotations

import asyncio
import logging
from typing import List

from services.api.config import settings
from services.api.dispatch.dispatcher import BaseDispatcher
from services.api.repository.memory_repo import memory_repo
from services.worker.agents.mock_adapter import BENCHMARK_FIXTURES
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.fixtures.problem_1065658_fixtures import MOCK_FIXTURES

logger = logging.getLogger(__name__)


class InlineDispatcher(BaseDispatcher):
    """Executes multi-agent worker pipeline in local background asyncio tasks."""

    async def _process_single_response(self, job_id: str, assessment_id: str, resp_id: str) -> None:
        """Processes a single response through the 5-agent pipeline."""
        resp = memory_repo.get_response(resp_id, assessment_id=assessment_id)
        if not resp:
            memory_repo.increment_job_progress(job_id, success=False)
            return

        resp.task_status = "RUNNING"
        memory_repo.update_response(resp)

        try:
            # Yield control to event loop
            await asyncio.sleep(0.001)

            # Check if this is a known synthetic fixture vs an unseen uploaded worksheet
            is_known_fixture = (
                resp_id in MOCK_FIXTURES
                or resp_id in BENCHMARK_FIXTURES
                or resp_id.startswith("case_")
                or resp_id.startswith("bench_")
                or (bool(resp.source_filename) and "fixture" in resp.source_filename.lower())
            )

            is_offline = not settings.is_live_mode()

            if not is_known_fixture and is_offline:
                # Truthfulness Principle (Gate 5):
                # Do NOT fabricate an AI diagnosis for an unseen upload in offline mode.
                existing_quality = (resp.analysis_data or {}).get("intake_quality", {})
                resp.task_status = "AWAITING_LIVE_ANALYSIS"
                resp.answer_status = "not_assessed"
                resp.reasoning_status = "not_assessed"
                resp.is_mock = True
                resp.model_version = "offline-intake-verified"
                resp.analysis_data = {
                    "diagnosis": {
                        "truthfulness_mode": "offline_unseen_requires_live",
                        "evidence_sufficiency": "unassessed",
                        "offline_truthfulness_message": (
                            "Image intake and image quality validation completed successfully. "
                            "Live multimodal vision model analysis is required to transcribe and assess this new handwritten worksheet."
                        ),
                        "diagnosed_misconception_id": None,
                        "confidence": 0.0,
                    },
                    "intake_quality": existing_quality,
                    "visual_evidence": {
                        "observations": [],
                        "has_number_line": None,
                        "final_answer_marked": None,
                        "quality_status": resp.upload_status or "clear",
                        "provenance": "unseen_upload",
                        "offline_note": "Awaiting live vision model analysis",
                    },
                }
                memory_repo.update_response(resp)
                memory_repo.increment_job_progress(job_id, success=True)
                return

            analysis = MultiAgentPipeline.analyze_response(response_id=resp_id)

            resp.task_status = "COMPLETED"
            resp.answer_status = (
                analysis.answer_status.value
                if hasattr(analysis.answer_status, "value")
                else str(analysis.answer_status)
            )
            resp.reasoning_status = (
                analysis.reasoning_status.value
                if hasattr(analysis.reasoning_status, "value")
                else str(analysis.reasoning_status)
            )
            resp.is_compensatory_error = analysis.is_compensatory_error
            resp.needs_teacher_review = analysis.needs_teacher_review
            resp.misconception_taxonomy_id = analysis.diagnosis.misconception_taxonomy_id
            resp.analysis_data = analysis.model_dump()
            resp.is_mock = analysis.is_mock
            resp.model_version = analysis.model_version
            resp.cost_estimate_usd = analysis.cost_estimate_usd
            memory_repo.update_response(resp)

            memory_repo.increment_job_progress(job_id, success=True)
        except Exception as exc:
            logger.exception(f"Error processing response {resp_id}: {exc}")
            resp.task_status = "FAILED"
            memory_repo.update_response(resp)
            memory_repo.increment_job_progress(job_id, success=False)

    async def dispatch_analysis_batch(
        self,
        job_id: str,
        assessment_id: str,
        response_ids: List[str],
    ) -> None:
        """Dispatches each response analysis in parallel via asyncio tasks."""
        tasks = [
            self._process_single_response(job_id, assessment_id, resp_id)
            for resp_id in response_ids
        ]
        await asyncio.gather(*tasks)


inline_dispatcher = InlineDispatcher()
