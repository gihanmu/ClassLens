"""Inline asynchronous dispatcher for offline local development."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List

from services.api.config import settings
from services.api.dispatch.dispatcher import BaseDispatcher
from services.api.repository.memory_repo import memory_repo
from services.api.repository.storage_config import get_uploads_dir
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
            base_id = ("resp_" + resp_id.split("_resp_")[-1]) if "_resp_" in resp_id else resp_id
            is_known_fixture = (
                base_id in MOCK_FIXTURES
                or resp_id in MOCK_FIXTURES
                or base_id in BENCHMARK_FIXTURES
                or resp_id in BENCHMARK_FIXTURES
                or resp_id.startswith("case_")
                or resp_id.startswith("bench_")
                or base_id.startswith("case_")
                or (bool(resp.source_filename) and "fixture" in resp.source_filename.lower())
            )

            is_live_auth = settings.is_live_authorized()

            # Locate source image if available
            image_source = None
            if resp.source_filename:
                uploads_dir = get_uploads_dir().resolve()
                asm = memory_repo.get_assessment(resp.assessment_id)
                org_id = asm.organization_id if asm else None
                candidates = []
                if org_id:
                    candidates.append(uploads_dir / org_id / resp.assessment_id / resp.source_filename)
                    candidates.append(uploads_dir / org_id / resp.source_filename)
                candidates.append(uploads_dir / resp.assessment_id / resp.source_filename)
                candidates.append(uploads_dir / resp.source_filename)
                for cand in candidates:
                    if cand.is_file():
                        image_source = cand
                        break

            if not is_known_fixture and not is_live_auth:
                # Truthfulness Principle (Gate 5 & 6):
                # Do NOT fabricate an AI diagnosis for an unseen upload without authorized live inference.
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
                            "Live multimodal vision model analysis is required to transcribe and assess this new handwritten worksheet. "
                            "Live inference is currently disabled (default USD $0.00 spend)."
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
                        "offline_note": "Awaiting authorized live vision model analysis",
                    },
                }
                memory_repo.update_response(resp)
                memory_repo.increment_job_progress(job_id, success=True)
                return

            analysis = MultiAgentPipeline.analyze_response(
                response_id=resp_id,
                image_source=image_source,
            )

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
            existing_quality = (resp.analysis_data or {}).get("intake_quality", {})
            resp.analysis_data = {
                "error": str(exc),
                "failed_at_step": "VisualEvidenceAgent",
                "truthfulness_mode": "live_failure",
                "intake_quality": existing_quality,
            }
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
