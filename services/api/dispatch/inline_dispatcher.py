"""Inline asynchronous dispatcher for offline local development."""

from __future__ import annotations

import asyncio
import logging
from typing import List

from services.api.dispatch.dispatcher import BaseDispatcher
from services.api.repository.memory_repo import memory_repo
from services.worker.agents.pipeline import MultiAgentPipeline

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
