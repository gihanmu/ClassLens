"""Gemini Multimodal Evaluation Adapter for Gate 3 Handwriting Feasibility.

Provides an enterprise-ready, bounded adapter using the Google GenAI SDK (`google-genai`).
Features strict call ceilings (max 3 calls), zero retries, zero automatic region fallback,
synthetic-only image enforcement, in-memory image streaming (zero GCS uploads),
and decoupled deterministic SymPy verification compatibility.
"""

from __future__ import annotations

import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.worker.evaluation.contracts import (
    ExtractionCertainty,
    GeminiVisualEvidenceSchema,
    HopDirection,
    ImageQualityAssessment,
    NumberLineObservation,
    ObservedHop,
    VisibleFinalAnswer,
    VisualAmbiguity,
)

# Published Vertex AI token pricing schedules per 1,000,000 tokens
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.5-flash": {
        "input_per_million": 0.30,
        "output_per_million": 2.50,
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
    "gemini-3.8-flash": {
        "input_per_million": 0.75,  # Introductory pricing through Dec 2026
        "output_per_million": 3.75,
    },
}

DEFAULT_FALLBACK_PRICING = {
    "input_per_million": 0.30,
    "output_per_million": 2.50,
}

DEFAULT_SYSTEM_PROMPT = """You are an objective handwriting and mathematical mark transcription assistant for elementary and middle school mathematics worksheets.
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


class GeminiEvaluationAdapter:
    """Adapter for executing or simulating Gemini visual evidence extractions.

    SAFETY AND BOUNDARY GUARANTEES:
    - Exactly 1 API call per worksheet (NO retries, NO multi-agent loops, NO fallback requests).
    - Hard software ceiling of `max_calls` (default: 3).
    - Regional data residency: strictly connects to the configured `location` (no automatic global failover).
    - Synthetic isolation: prohibits transmitting images from real dataset directories.
    - Zero GCS uploads: image bytes streamed in-memory via types.Part.from_bytes.
    """

    def __init__(
        self,
        model_id: str = "gemini-3.8-flash",
        location: str = "global",
        project: Optional[str] = "precise-equator-511303-m1",
        vertexai: bool = True,
        max_calls: int = 3,
        timeout_seconds: float = 30.0,
        dry_run: bool = True,
        live_opt_in: bool = False,
    ) -> None:
        self.model_id = model_id
        self.location = location
        self.project = project
        self.vertexai = vertexai
        self.max_calls = max_calls
        self.timeout_seconds = timeout_seconds
        self.dry_run = dry_run
        self.live_opt_in = live_opt_in

        # Telemetry and local accounting
        self.call_count: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_estimated_cost_usd: float = 0.0
        self.last_latency_ms: int = 0
        self.call_history: List[Dict[str, Any]] = []

    def get_token_rates(self) -> Dict[str, float]:
        """Returns input and output price per token for the active model."""
        rates = MODEL_PRICING.get(self.model_id, DEFAULT_FALLBACK_PRICING)
        return {
            "input_per_token": rates["input_per_million"] / 1_000_000.0,
            "output_per_token": rates["output_per_million"] / 1_000_000.0,
        }

    def extract_visual_evidence(
        self,
        image_path: str,
        response_id: str,
        prompt_override: Optional[str] = None,
    ) -> GeminiVisualEvidenceSchema:
        """Extract visual evidence from an image file.

        In dry-run mode (default), returns deterministic synthetic observations
        without network calls or cost.
        In live mode, enforces strict security and budget guardrails.
        """
        # Strict synthetic isolation check: real student datasets must never be transmitted
        norm_path = str(Path(image_path).resolve()).lower()
        if "/dataset/" in norm_path or "drawedumath" in norm_path or "mathwriting" in norm_path or "dataset/" in image_path.lower():
            raise PermissionError(
                f"Security Guardrail Violation: Path '{image_path}' points to a real dataset location. "
                "Gate 3 live evaluation is strictly restricted to synthetic fixtures in tests/fixtures/."
            )

        p = Path(image_path)
        if not p.is_file():
            raise FileNotFoundError(f"Evaluation image not found: {image_path}")

        start_time = time.perf_counter()

        # Dry-run execution
        if self.dry_run or not self.live_opt_in:
            result = self._emulate_dry_run(response_id=response_id, image_path=image_path)
            latency = int((time.perf_counter() - start_time) * 1000)
            self._record_telemetry(
                response_id=response_id,
                input_tokens=258,  # Standard ~258 tokens per image
                output_tokens=320,
                latency_ms=max(latency, 12),
                is_dry_run=True,
            )
            return result

        # Live execution Guardrails
        if not self.live_opt_in:
            raise PermissionError(
                "Gate 3 Guardrail Block: Live Gemini evaluation is disabled by default. "
                "Explicit authorization flag '--live-opt-in' is required."
            )

        if self.call_count >= self.max_calls:
            raise RuntimeError(
                f"Gate 3 Budget Exceeded: Call count ({self.call_count}) has reached the "
                f"authorized maximum ceiling of {self.max_calls} calls."
            )

        # Execute single, non-retried live GenAI API call
        result = self._execute_live_call(
            image_path=p,
            response_id=response_id,
            prompt=prompt_override or DEFAULT_SYSTEM_PROMPT,
            start_time=start_time,
        )
        return result

    def _execute_live_call(
        self,
        image_path: Path,
        response_id: str,
        prompt: str,
        start_time: float,
    ) -> GeminiVisualEvidenceSchema:
        """Execute real multimodal call using google.genai SDK with in-memory streaming.

        Guarantees:
        - Exactly one API call. No automatic retry loop.
        - Strictly targeted to self.location. No automatic global fallback.
        - Uses vertexai=True SDK parameter.
        """
        from google import genai
        from google.genai import types

        # Read image directly into memory (NO GCS upload)
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/png"

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        # Initialize Vertex AI client with validated SDK parameters
        client_kwargs: Dict[str, Any] = {
            "vertexai": self.vertexai,
            "location": self.location,
        }
        if self.project:
            client_kwargs["project"] = self.project

        client = genai.Client(**client_kwargs)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiVisualEvidenceSchema,
            temperature=0.0,
            max_output_tokens=4096,
        )

        user_content = [
            image_part,
            f"Analyze this student number-line response. Unique Response ID: {response_id}.\n{prompt}",
        ]

        # Single non-retried call
        response = client.models.generate_content(
            model=self.model_id,
            contents=user_content,
            config=config,
        )

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
            is_dry_run=False,
        )

        if not response.text:
            raise ValueError(f"Empty response text received from Gemini for {response_id}")

        raw_json = response.text.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.startswith("```"):
            raw_json = raw_json[3:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]
        raw_json = raw_json.strip()

        evidence = GeminiVisualEvidenceSchema.model_validate_json(raw_json)
        return evidence

    def _record_telemetry(
        self,
        response_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        is_dry_run: bool,
    ) -> None:
        """Update cumulative usage, costs, and call logs."""
        rates = self.get_token_rates()
        call_est_cost = (input_tokens * rates["input_per_token"]) + (output_tokens * rates["output_per_token"])

        self.call_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_estimated_cost_usd += call_est_cost
        self.last_latency_ms = latency_ms

        self.call_history.append(
            {
                "call_index": self.call_count,
                "response_id": response_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": round(call_est_cost, 6),
                "latency_ms": latency_ms,
                "dry_run": is_dry_run,
                "model_id": self.model_id,
                "location": self.location,
            }
        )

    def _emulate_dry_run(self, response_id: str, image_path: str) -> GeminiVisualEvidenceSchema:
        """Deterministic mock responses corresponding to Gate 3 evaluation test cases."""
        # Case 1: Canonical Correct (0 -> -6 -> 6 -> 2, final answer 2)
        if "case_01" in response_id or "canonical" in response_id or "04255753" in response_id:
            return GeminiVisualEvidenceSchema(
                response_id=response_id,
                image_quality=ImageQualityAssessment.CLEAR,
                visible_final_answer=VisibleFinalAnswer(
                    value="2",
                    evidence_location="Answer box and circled '2' on number line",
                    certainty=ExtractionCertainty.HIGH,
                ),
                number_line=NumberLineObservation(
                    is_present=True,
                    min_visible_tick=-12.0,
                    max_visible_tick=12.0,
                    zero_position_visible=True,
                    observed_hops=[
                        ObservedHop(
                            hop_index=1,
                            start_value=0.0,
                            end_value=-6.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            arc_drawn=True,
                            arrowhead_visible=True,
                            stated_magnitude_label="-6",
                            evidence_description="Clear leftward curved arc from 0 to -6 with visible arrowhead.",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=2,
                            start_value=-6.0,
                            end_value=6.0,
                            direction=HopDirection.RIGHT_POSITIVE,
                            arc_drawn=True,
                            arrowhead_visible=True,
                            stated_magnitude_label="+12",
                            evidence_description="Clear rightward curved arc spanning -6 to +6 with clear arrowhead.",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=3,
                            start_value=6.0,
                            end_value=2.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            arc_drawn=True,
                            arrowhead_visible=True,
                            stated_magnitude_label="-4",
                            evidence_description="Clear leftward arc from 6 landing on 2 with clear arrowhead.",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                    ],
                ),
                ambiguities=[],
                unsupported_observations=[],
                requires_teacher_review=False,
                teacher_review_reason=None,
            )

        # Case 2: Procedural Error (Off-by-one tick count error landing on 5 instead of 6, then left to 1)
        elif "case_02" in response_id or "procedural" in response_id or "off_by_one" in response_id:
            return GeminiVisualEvidenceSchema(
                response_id=response_id,
                image_quality=ImageQualityAssessment.CLEAR,
                visible_final_answer=VisibleFinalAnswer(
                    value="1",
                    evidence_location="Written answer '1' in answer box",
                    certainty=ExtractionCertainty.HIGH,
                ),
                number_line=NumberLineObservation(
                    is_present=True,
                    min_visible_tick=-10.0,
                    max_visible_tick=10.0,
                    zero_position_visible=True,
                    observed_hops=[
                        ObservedHop(
                            hop_index=1,
                            start_value=0.0,
                            end_value=-6.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            arc_drawn=True,
                            arrowhead_visible=True,
                            stated_magnitude_label="-6",
                            evidence_description="Arc drawn starting at 0 and landing at -6.",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=2,
                            start_value=-6.0,
                            end_value=5.0,
                            direction=HopDirection.RIGHT_POSITIVE,
                            arc_drawn=True,
                            arrowhead_visible=True,
                            stated_magnitude_label="+12",
                            evidence_description="Rightward arc drawn from -6 landing on 5 (+11 units instead of +12).",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                        ObservedHop(
                            hop_index=3,
                            start_value=5.0,
                            end_value=1.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            arc_drawn=True,
                            arrowhead_visible=True,
                            stated_magnitude_label="-4",
                            evidence_description="Leftward arc from 5 landing on 1 with visible arrowhead.",
                            certainty=ExtractionCertainty.HIGH,
                        ),
                    ],
                ),
                ambiguities=[],
                unsupported_observations=[],
                requires_teacher_review=False,
                teacher_review_reason=None,
            )

        # Case 3: Ambiguous / Incomplete / Faint (Missing arrowheads, faint stroke, blank answer)
        elif "case_03" in response_id or "ambiguous" in response_id or "incomplete" in response_id:
            return GeminiVisualEvidenceSchema(
                response_id=response_id,
                image_quality=ImageQualityAssessment.FAINT_READABLE,
                visible_final_answer=VisibleFinalAnswer(
                    value=None,
                    evidence_location=None,
                    certainty=ExtractionCertainty.CANNOT_DETERMINE,
                ),
                number_line=NumberLineObservation(
                    is_present=True,
                    min_visible_tick=-8.0,
                    max_visible_tick=8.0,
                    zero_position_visible=True,
                    observed_hops=[
                        ObservedHop(
                            hop_index=1,
                            start_value=0.0,
                            end_value=-6.0,
                            direction=HopDirection.LEFT_NEGATIVE,
                            arc_drawn=True,
                            arrowhead_visible=False,
                            stated_magnitude_label=None,
                            evidence_description="Faint arc drawn from 0 to -6; arrowhead is absent.",
                            certainty=ExtractionCertainty.MEDIUM,
                        ),
                        ObservedHop(
                            hop_index=2,
                            start_value=-6.0,
                            end_value=None,
                            direction=HopDirection.AMBIGUOUS,
                            arc_drawn=True,
                            arrowhead_visible=False,
                            stated_magnitude_label=None,
                            evidence_description="Incomplete curved stroke from -6 terminating ambiguously near 1-2.",
                            certainty=ExtractionCertainty.LOW,
                        ),
                    ],
                ),
                ambiguities=[
                    VisualAmbiguity(
                        element="arrowhead",
                        description="No arrowheads visible on number line arcs.",
                        severity="minor",
                    ),
                    VisualAmbiguity(
                        element="hop",
                        description="Hop #2 terminates without clear landing tick mark.",
                        severity="blocking",
                    ),
                    VisualAmbiguity(
                        element="final_answer",
                        description="Final answer box is blank.",
                        severity="blocking",
                    ),
                ],
                unsupported_observations=[
                    "Cannot determine if student intended to reach +6 or stop early."
                ],
                requires_teacher_review=True,
                teacher_review_reason="Incomplete hop sequence and blank final answer require human teacher inspection.",
            )

        # Fallback generic mock
        return GeminiVisualEvidenceSchema(
            response_id=response_id,
            image_quality=ImageQualityAssessment.CLEAR,
            visible_final_answer=VisibleFinalAnswer(
                value="2",
                certainty=ExtractionCertainty.MEDIUM,
            ),
            number_line=NumberLineObservation(
                is_present=True,
                min_visible_tick=-10.0,
                max_visible_tick=10.0,
                zero_position_visible=True,
                observed_hops=[
                    ObservedHop(
                        hop_index=1,
                        start_value=0.0,
                        end_value=-6.0,
                        direction=HopDirection.LEFT_NEGATIVE,
                        arc_drawn=True,
                        arrowhead_visible=True,
                        evidence_description="Arc from 0 to -6.",
                    )
                ],
            ),
            ambiguities=[],
            requires_teacher_review=False,
        )
