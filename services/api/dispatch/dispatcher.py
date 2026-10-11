"""Abstract interface for task dispatching."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseDispatcher(ABC):
    """Abstract base class for asynchronous task dispatchers."""

    @abstractmethod
    async def dispatch_analysis_batch(
        self,
        job_id: str,
        assessment_id: str,
        response_ids: List[str],
    ) -> None:
        """Dispatches an analysis batch to workers."""
        pass
