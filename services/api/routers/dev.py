"""Development-only manual testing routes for Gate 4A Gemini validation.

STRICT SECURITY CONTROLS:
- Available ONLY when ENVIRONMENT == 'development'.
- Bounded strictly to localhost.
- Accepts ONLY predefined synthetic fixture IDs ('case_01', 'case_02', 'case_03').
- Resolves all image paths internally through provenance_guard.
- Never accepts arbitrary paths, arbitrary uploads, or user-supplied claims.
- Reuses the existing 5-agent MultiAgentPipeline without a separate code path.
- Tracks and enforces server-side call allowance limits during manual test sessions.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.api.config import settings
from services.worker.agents.pipeline import MultiAgentPipeline
from services.worker.agents.provider import get_visual_evidence_provider
from services.worker.gemini.adapter import GeminiVisionError
from services.worker.security.provenance_guard import (
    TRUSTED_SYNTHETIC_ALLOWLIST,
    TRUSTED_SYNTHETIC_DIR,
    UntrustedProvenanceError,
    verify_synthetic_path,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["development"])

# Authorized synthetic fixtures allowlist
VALID_FIXTURE_IDS = {
    "case_01_canonical_correct": {
        "id": "case_01_canonical_correct",
        "name": "Case 1: Canonical Correct Strategy",
        "description": "Sequential number-line jumps starting from zero: 0 -> -6 -> +6 -> +2, final answer 2.",
        "category": "canonical_correct",
        "expected_answer": "2",
        "expected_reasoning": "supported_correct",
        "filename": "case_01_canonical_correct.png",
    },
    "case_02_off_by_one_error": {
        "id": "case_02_off_by_one_error",
        "name": "Case 2: Procedural Off-By-One Error",
        "description": "Student jumps from -6 landing on 5 instead of 6 (+11 instead of +12), terminating at 1.",
        "category": "procedural_error",
        "expected_answer": "1",
        "expected_reasoning": "supported_error",
        "filename": "case_02_off_by_one_error.png",
    },
    "case_03_ambiguous_incomplete": {
        "id": "case_03_ambiguous_incomplete",
        "name": "Case 3: Ambiguous & Incomplete Work",
        "description": "Faint handwriting, missing arrowheads, incomplete stroke near 1-2, blank final answer.",
        "category": "ambiguous_incomplete",
        "expected_answer": None,
        "expected_reasoning": "incomplete",
        "filename": "case_03_ambiguous_incomplete.png",
    },
}

FixtureIdType = Literal[
    "case_01_canonical_correct",
    "case_02_off_by_one_error",
    "case_03_ambiguous_incomplete",
]


class DevSessionTracker:
    """In-memory session call counter enforcing manual testing ceilings."""

    def __init__(self) -> None:
        self.live_call_count: int = 0

    def get_count(self) -> int:
        return self.live_call_count

    def increment(self) -> int:
        self.live_call_count += 1
        return self.live_call_count

    def reset(self) -> None:
        self.live_call_count = 0


dev_session_tracker = DevSessionTracker()


def _assert_development_mode() -> None:
    """Rejects request if application is not in development mode."""
    if settings.environment != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development endpoints are strictly disabled outside local development.",
        )


class SyntheticAnalysisRequest(BaseModel):
    """Payload for manual synthetic test analysis."""

    fixture_id: FixtureIdType = Field(
        description="Predefined authorized synthetic fixture identifier"
    )
    rule_expr: str = Field(
        default="-6 + 12 - 4",
        description="Mathematical problem expression",
    )
    target_value: float = Field(
        default=2.0,
        description="Expected final numerical answer",
    )


class SyntheticAnalysisResponse(BaseModel):
    """Standardized response from manual test lab."""

    fixture_id: str
    mode: Literal["mock", "live"]
    model_version: str
    is_mock: bool
    execution_latency_ms: int
    tokens_consumed: int
    cost_estimate_usd: Optional[float] = None
    live_telemetry: Optional[Dict[str, Any]] = None
    calls_used: int
    calls_remaining: int
    analysis: Dict[str, Any]


@router.get("/status")
async def get_dev_status():
    """Returns local AI execution mode, configuration, and remaining call allowance."""
    _assert_development_mode()

    is_live = settings.is_live_mode()
    is_live_auth = settings.is_live_authorized()
    calls_used = dev_session_tracker.get_count()
    calls_remaining = max(0, settings.max_live_calls - calls_used)

    return {
        "environment": settings.environment,
        "ai_mode": settings.ai_mode,
        "live_inference_enabled": settings.live_inference_enabled,
        "is_live_mode": is_live,
        "is_live_authorized": is_live_auth,
        "owner_auth_configured": bool(settings.live_auth_key and settings.live_auth_key.strip()),
        "model": settings.gemini_model,
        "project": settings.google_cloud_project,
        "location": settings.google_cloud_location,
        "use_vertexai": settings.google_genai_use_vertexai,
        "timeout_seconds": settings.gemini_timeout_seconds,
        "max_output_tokens": settings.gemini_max_output_tokens,
        "max_calls": settings.max_live_calls,
        "calls_used": calls_used,
        "calls_remaining": calls_remaining,
        "authorized_fixtures": list(VALID_FIXTURE_IDS.values()),
    }


@router.get("/synthetic-fixtures/{fixture_id}/image")
async def get_synthetic_fixture_image(fixture_id: str):
    """Serves the authorized synthetic worksheet image file for browser preview."""
    _assert_development_mode()

    if fixture_id not in VALID_FIXTURE_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fixture ID '{fixture_id}'. Must be one of: {list(VALID_FIXTURE_IDS.keys())}",
        )

    fixture_meta = VALID_FIXTURE_IDS[fixture_id]
    image_path = TRUSTED_SYNTHETIC_DIR / fixture_meta["filename"]

    try:
        # Provenance guard verify ensures file is inside trusted root and SHA-256 matches allowlist
        verified_path = verify_synthetic_path(image_path)
    except UntrustedProvenanceError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Provenance guard violation: {e}",
        )

    return FileResponse(
        path=verified_path,
        media_type="image/png",
        filename=fixture_meta["filename"],
    )


@router.post("/analyze-synthetic", response_model=SyntheticAnalysisResponse)
async def analyze_synthetic_fixture(req: SyntheticAnalysisRequest):
    """Executes multi-agent analysis on an authorized synthetic worksheet.

    Reuses the existing MultiAgentPipeline and provenance guard.
    In live mode, enforces call ceiling and records session usage.
    """
    _assert_development_mode()

    if req.fixture_id not in VALID_FIXTURE_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fixture ID '{req.fixture_id}'. Must be one of: {list(VALID_FIXTURE_IDS.keys())}",
        )

    fixture_meta = VALID_FIXTURE_IDS[req.fixture_id]
    image_path = TRUSTED_SYNTHETIC_DIR / fixture_meta["filename"]

    try:
        verified_path = verify_synthetic_path(image_path)
    except UntrustedProvenanceError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Provenance guard violation: {e}",
        )

    is_live = settings.is_live_mode()

    # Enforce session call ceiling in live mode
    if is_live:
        current_calls = dev_session_tracker.get_count()
        if current_calls >= settings.max_live_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Gate 4A Live Call Budget Exceeded: Reached session ceiling of "
                    f"{settings.max_live_calls} live calls. Restart server to reset allowance."
                ),
            )

    try:
        # Use existing provider factory
        provider = get_visual_evidence_provider()

        analysis = MultiAgentPipeline.analyze_response(
            response_id=req.fixture_id,
            provider=provider,
            image_source=verified_path,
            rule_expr=req.rule_expr,
            target_value=req.target_value,
        )
    except GeminiVisionError as gve:
        logger.error(f"Gemini vision error during manual test: {gve}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Vertex AI Gemini inference error: {gve}",
        )
    except Exception as exc:
        logger.exception(f"Unexpected pipeline error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution error: {exc}",
        )

    # Increment counter if live call was executed
    if is_live and not analysis.is_mock:
        dev_session_tracker.increment()

    calls_used = dev_session_tracker.get_count()
    calls_remaining = max(0, settings.max_live_calls - calls_used)

    return SyntheticAnalysisResponse(
        fixture_id=req.fixture_id,
        mode="live" if not analysis.is_mock else "mock",
        model_version=analysis.model_version,
        is_mock=analysis.is_mock,
        execution_latency_ms=analysis.execution_latency_ms,
        tokens_consumed=analysis.tokens_consumed,
        cost_estimate_usd=analysis.cost_estimate_usd,
        live_telemetry=analysis.live_telemetry,
        calls_used=calls_used,
        calls_remaining=calls_remaining,
        analysis=analysis.model_dump(),
    )


# ==============================================================================
# Gate 4C: AI Reliability & Benchmark Evaluation Endpoints
# ==============================================================================
# Gate 4C & Gate 6: AI Reliability & Benchmark Evaluation Endpoints
# ==============================================================================

@router.get("/evaluation/latest")
async def get_latest_evaluation_report(mode: str = "offline") -> Dict[str, Any]:
    """Returns the latest serialized evaluation report (offline benchmark by default, or live)."""
    _assert_development_mode()

    live_report_path = Path("evaluation/reports/latest_live_evaluation_report.json")
    has_live_report = live_report_path.is_file()
    live_report_data = None
    if has_live_report:
        try:
            with open(live_report_path, "r", encoding="utf-8") as f:
                live_report_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load live evaluation report: {e}")

    live_status = "completed" if live_report_data else "not_performed"

    if mode == "live":
        if not live_report_data:
            return {
                "status": "not_performed",
                "message": (
                    "Live handwriting evaluation: Not yet performed. "
                    "Live inference requires explicit owner authorization and budget allocation."
                ),
                "dataset_version": "1.0.0",
                "cases_available": 20,
            }
        return live_report_data

    # Default: offline regression benchmark report
    report_path = Path("evaluation/reports/latest_benchmark_report.json")
    if not report_path.is_file():
        from evaluation.runner import run_benchmark
        report = run_benchmark(mode="offline_regression")
        data = report.model_dump()
    else:
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            logger.exception(f"Failed to read latest benchmark report: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load latest benchmark report: {exc}",
            )

    # Attach live evaluation status metadata to report response
    data["live_evaluation_status"] = live_status
    data["live_report"] = live_report_data
    return data


@router.get("/evaluation/live-latest")
async def get_latest_live_evaluation_report() -> Dict[str, Any]:
    """Returns the latest authorized live evaluation report, or status 'not_performed'."""
    _assert_development_mode()

    live_report_path = Path("evaluation/reports/latest_live_evaluation_report.json")
    if not live_report_path.is_file():
        return {
            "status": "not_performed",
            "message": (
                "Live handwriting evaluation: Not yet performed. "
                "Live inference requires explicit owner authorization and budget allocation."
            ),
            "dataset_version": "1.0.0",
            "cases_available": 20,
            "report": None,
        }

    try:
        with open(live_report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"status": "completed", "report": data}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read live evaluation report: {exc}",
        )


@router.post("/evaluation/run")
async def trigger_evaluation_run() -> Dict[str, Any]:
    """Triggers an offline benchmark evaluation run against the versioned dataset ($0.00 spend)."""
    _assert_development_mode()

    try:
        from evaluation.runner import run_benchmark
        report = run_benchmark(
            dataset_path="evaluation/datasets/benchmark_v1.json",
            mode="offline_regression",
        )
        return report.model_dump()
    except Exception as exc:
        logger.exception(f"Failed to execute benchmark evaluation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark evaluation execution failed: {exc}",
        )


@router.post("/evaluation/run-live")
async def trigger_live_evaluation_run(
    x_classlens_live_auth: Optional[str] = Header(None, alias="X-ClassLens-Live-Auth"),
) -> Dict[str, Any]:
    """Triggers an authorized live evaluation run against handwriting_eval_v1.json.
    
    Strictly fails closed if live inference is not enabled or authorization key is invalid.
    """
    _assert_development_mode()

    if not settings.is_live_authorized(provided_key=x_classlens_live_auth):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Live handwriting evaluation requires CLASSLENS_LIVE_INFERENCE_ENABLED=true "
                "and valid owner authorization key via X-ClassLens-Live-Auth. "
                "Live inference is strictly disabled to prevent unauthorized charges ($0.00 spend guarantee)."
            ),
        )

    try:
        from evaluation.runner import run_benchmark
        report = run_benchmark(
            dataset_path="evaluation/datasets/handwriting_eval_v1.json",
            mode="authorized_live",
            auth_key=x_classlens_live_auth,
        )
        return report.model_dump()
    except Exception as exc:
        logger.exception(f"Failed to execute live benchmark evaluation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Live benchmark evaluation execution failed: {exc}",
        )


@router.get("/evaluation/markdown")
async def get_latest_evaluation_markdown(mode: str = "offline") -> Dict[str, str]:
    """Returns the rendered markdown text of the latest benchmark or live evaluation report."""
    _assert_development_mode()

    if mode == "live":
        md_path = Path("evaluation/reports/latest_live_evaluation_report.md")
        if not md_path.is_file():
            return {
                "markdown": (
                    "# ClassLens Real Gemini Handwriting Evaluation Report\n\n"
                    "> **Status:** Not yet performed.\n"
                    "> Live inference requires explicit owner authorization and budget allocation."
                )
            }
    else:
        md_path = Path("evaluation/reports/latest_benchmark_report.md")
        if not md_path.is_file():
            from evaluation.runner import run_benchmark
            run_benchmark(mode="offline_regression")

    try:
        content = md_path.read_text(encoding="utf-8")
        return {"markdown": content}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read markdown report: {exc}",
        )


