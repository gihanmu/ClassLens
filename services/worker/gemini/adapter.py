"""Reusable Gemini Multimodal Vision Adapter for Google Cloud Vertex AI.

Provides a unified, production-ready adapter using the Google GenAI SDK (`google-genai`).
Features:
- Managed SDK client lifecycle (cached client instance).
- In-memory image streaming via types.Part.from_bytes (zero GCS bucket staging).
- Native structured JSON output parsing to GeminiVisualEvidenceSchema.
- Strict single-call invocation (zero automatic retries, zero automatic region/model fallbacks).
- Precise token usage accounting and local software cost estimation.
- Typed domain exceptions.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from services.worker.evaluation.contracts import GeminiVisualEvidenceSchema

logger = logging.getLogger(__name__)


class GeminiVisionError(Exception):
    """Base exception for Gemini vision operations."""


class GeminiAuthenticationError(GeminiVisionError):
    """Raised when Google Cloud credentials or ADC authentication fails."""


class GeminiQuotaError(GeminiVisionError):
    """Raised when Vertex AI rate limits or quotas are exhausted (429)."""


class GeminiTimeoutError(GeminiVisionError):
    """Raised when a request to Vertex AI times out."""


class GeminiModelError(GeminiVisionError):
    """Raised when model returns malformed JSON or unparseable schema."""


# Published Vertex AI token pricing schedules per 1,000,000 tokens
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-3.8-flash": {
        "input_per_million": 0.75,  # Introductory rate through Dec 2026
        "output_per_million": 3.75,
    },
    "gemini-3.5-flash-lite": {
        "input_per_million": 0.10,
        "output_per_million": 0.40,
    },
    "gemini-2.5-flash": {
        "input_per_million": 0.30,
        "output_per_million": 2.50,
    },
    "gemini-2.5-pro": {
        "input_per_million": 1.25,
        "output_per_million": 10.00,
    },
    "gemini-1.5-flash": {
        "input_per_million": 0.075,
        "output_per_million": 0.30,
    },
    "gemini-1.5-flash-002": {
        "input_per_million": 0.075,
        "output_per_million": 0.30,
    },
    "gemini-2.0-flash": {
        "input_per_million": 0.10,
        "output_per_million": 0.40,
    },
}

DEFAULT_FALLBACK_PRICING = {
    "input_per_million": 0.75,
    "output_per_million": 3.75,
}

SYSTEM_INSTRUCTION = """You are an objective handwriting and mathematical mark transcription assistant for elementary and middle school mathematics worksheets.
Your sole job is to observe and report physical ink markings on the student's number-line worksheet with high fidelity.

CRITICAL INSTRUCTIONS:
1. DECOUPLE VISUAL EVIDENCE FROM MATHEMATICAL INTENT:
   - Report exactly what ink strokes are physically visible on the number line.
   - Do NOT assume the student's thought process or "correct" their jumps.
   - If an arc starts at 0 and lands at -6, record start=0, end=-6, direction=left_negative.
   - If an arrowhead is missing, explicitly set arrowhead_visible=false.
   - If a magnitude label (e.g. "+12", "-4") is written near the arc, report it.
2. DETECT FINAL ANSWER:
   - Record any number written in the final answer box or distinctly circled as the final answer.
   - If no answer is written, set value=null and certainty=cannot_determine.
3. RECORD AMBIGUITIES & QUALITY:
   - If an ink mark is faint, smudged, or ambiguous between two tick marks, document it in `ambiguities`.
   - If handwriting or marks cannot be confidently resolved, set `requires_teacher_review=true` and explain why.
4. RETURN STRICT JSON:
   - Output must strictly conform to the provided schema.
"""


class GeminiVisionAdapter:
    """Production-grade reusable Gemini multimodal adapter for Vertex AI."""

    def __init__(
        self,
        model_id: str = "gemini-3.8-flash",
        location: str = "global",
        project: Optional[str] = "precise-equator-511303-m1",
        vertexai: bool = True,
        max_calls: int = 3,
        timeout_seconds: float = 30.0,
        max_output_tokens: int = 4096,
        max_image_size_bytes: int = 10 * 1024 * 1024,
    ) -> None:
        self.model_id = model_id
        self.location = location
        self.project = project
        self.vertexai = vertexai
        self.max_calls = max_calls
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.max_image_size_bytes = max_image_size_bytes

        # Cached client instance to avoid recreating client on every request
        self._client: Optional[Any] = None

        # Usage telemetry and local accounting
        self.call_count: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_estimated_cost_usd: float = 0.0
        self.last_latency_ms: int = 0
        self.call_history: List[Dict[str, Any]] = []

    def get_client(self) -> Any:
        """Retrieves or initializes the cached Google GenAI client."""
        if self._client is None:
            try:
                from google import genai

                client_kwargs: Dict[str, Any] = {
                    "vertexai": self.vertexai,
                    "location": self.location,
                }
                if self.project:
                    client_kwargs["project"] = self.project

                self._client = genai.Client(**client_kwargs)
            except Exception as e:
                raise GeminiAuthenticationError(
                    f"Failed to initialize Google GenAI SDK client: {e}"
                ) from e
        return self._client

    def get_token_rates(self) -> Dict[str, float]:
        """Returns input and output price per token for the active model."""
        rates = MODEL_PRICING.get(self.model_id, DEFAULT_FALLBACK_PRICING)
        return {
            "input_per_token": rates["input_per_million"] / 1_000_000.0,
            "output_per_token": rates["output_per_million"] / 1_000_000.0,
        }

    def extract_from_bytes(
        self,
        image_bytes: bytes,
        response_id: str,
        mime_type: str = "image/png",
        prompt_override: Optional[str] = None,
    ) -> GeminiVisualEvidenceSchema:
        """Extracts structured visual evidence directly from in-memory image bytes.

        Enforces:
        - Call ceiling circuit breaker.
        - Strict image payload size bounds.
        - Single non-retried call to Vertex AI with bounded timeout.
        - Structured JSON schema enforcement.
        - Usage and cost telemetry capture.
        """
        if self.call_count >= self.max_calls:
            raise RuntimeError(
                f"Gate 4A Call Budget Exceeded: Reached authorized limit of {self.max_calls} live calls."
            )

        if len(image_bytes) > self.max_image_size_bytes:
            raise GeminiVisionError(
                f"Image size ({len(image_bytes)} bytes) exceeds maximum limit "
                f"of {self.max_image_size_bytes} bytes."
            )

        start_time = time.perf_counter()
        client = self.get_client()

        from google.genai import types

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        # Enforce explicit request timeout and single attempt (zero retries)
        http_options = types.HttpOptions(
            timeout=int(self.timeout_seconds * 1000),
            retry_options=types.HttpRetryOptions(attempts=1),
        )

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiVisualEvidenceSchema,
            temperature=0.0,
            max_output_tokens=self.max_output_tokens,
            http_options=http_options,
        )

        user_content = [
            image_part,
            f"Analyze this student number-line response. Unique Response ID: {response_id}.\n{prompt_override or SYSTEM_INSTRUCTION}",
        ]

        try:
            # Single non-retried call to Vertex AI
            response = client.models.generate_content(
                model=self.model_id,
                contents=user_content,
                config=config,
            )
        except Exception as exc:
            err_str = str(exc).lower()
            if "429" in err_str or "resource exhausted" in err_str or "quota" in err_str:
                raise GeminiQuotaError(f"Vertex AI quota exhausted for {self.model_id}: {exc}") from exc
            elif "403" in err_str or "permission denied" in err_str or "unauthenticated" in err_str:
                raise GeminiAuthenticationError(f"Vertex AI authentication/permission error: {exc}") from exc
            elif "timeout" in err_str or "deadline exceeded" in err_str:
                raise GeminiTimeoutError(f"Vertex AI request timed out: {exc}") from exc
            else:
                raise GeminiVisionError(f"Vertex AI inference failed for {response_id}: {exc}") from exc

        latency = int((time.perf_counter() - start_time) * 1000)

        # Token accounting from actual API usage metadata
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

        self._record_telemetry(
            response_id=response_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
        )

        if not response.text:
            raise GeminiModelError(f"Empty response text received from Gemini for {response_id}")

        raw_json = response.text.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.startswith("```"):
            raw_json = raw_json[3:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]
        raw_json = raw_json.strip()

        try:
            evidence = GeminiVisualEvidenceSchema.model_validate_json(raw_json)
        except Exception as val_err:
            raise GeminiModelError(
                f"Failed to validate response against GeminiVisualEvidenceSchema: {val_err}"
            ) from val_err

        return evidence

    def extract_from_path(
        self,
        image_path: Union[str, Path],
        response_id: str,
        prompt_override: Optional[str] = None,
    ) -> GeminiVisualEvidenceSchema:
        """Reads file into memory and extracts visual evidence."""
        p = Path(image_path)
        if not p.is_file():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image_bytes = p.read_bytes()
        mime_type, _ = mimetypes.guess_type(str(p))
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/png"

        return self.extract_from_bytes(
            image_bytes=image_bytes,
            response_id=response_id,
            mime_type=mime_type,
            prompt_override=prompt_override,
        )

    def _record_telemetry(
        self,
        response_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
    ) -> None:
        """Updates internal telemetry metrics."""
        rates = self.get_token_rates()
        est_cost = (input_tokens * rates["input_per_token"]) + (output_tokens * rates["output_per_token"])

        self.call_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_estimated_cost_usd += est_cost
        self.last_latency_ms = latency_ms

        self.call_history.append(
            {
                "call_index": self.call_count,
                "response_id": response_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": round(est_cost, 6),
                "latency_ms": latency_ms,
                "model_id": self.model_id,
                "location": self.location,
            }
        )


_shared_adapter: Optional[GeminiVisionAdapter] = None


def get_shared_gemini_adapter(
    model_id: Optional[str] = None,
    location: Optional[str] = None,
    project: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    max_calls: Optional[int] = None,
) -> GeminiVisionAdapter:
    """Provides a singleton GeminiVisionAdapter across the application."""
    global _shared_adapter
    from services.api.config import settings

    m_id = model_id or settings.gemini_model
    loc = location or settings.google_cloud_location
    proj = project or settings.google_cloud_project
    tout = timeout_seconds if timeout_seconds is not None else settings.gemini_timeout_seconds
    tokens = max_output_tokens if max_output_tokens is not None else settings.gemini_max_output_tokens
    calls = max_calls if max_calls is not None else settings.max_live_calls

    if _shared_adapter is None:
        _shared_adapter = GeminiVisionAdapter(
            model_id=m_id,
            location=loc,
            project=proj,
            timeout_seconds=tout,
            max_output_tokens=tokens,
            max_calls=calls,
            max_image_size_bytes=settings.max_image_size_bytes,
        )
    return _shared_adapter


def reset_shared_gemini_adapter() -> None:
    """Resets the singleton adapter (primarily for testing and reconfiguration)."""
    global _shared_adapter
    _shared_adapter = None

