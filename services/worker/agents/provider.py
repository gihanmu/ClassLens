"""Visual Evidence Provider abstraction decoupling visual extraction from downstream mathematical reasoning.

Enforces Gate 4A architectural boundaries:
- VisualEvidenceProvider protocol for swappable provider implementations.
- MockVisualEvidenceProvider: 100% offline, zero network calls, deterministic fixtures.
- GeminiVisualEvidenceProvider: Live multimodal extraction via Vertex AI with strict
  synthetic provenance validation (zero transmission of real student data).
- Robust schema mapper translating GeminiVisualEvidenceSchema to VisualEvidenceOutput
  while strictly preserving SymPy and downstream agents as the mathematical authority.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from services.api.config import settings
from services.worker.agents.contracts import (
    QualityStatus,
    VisualEvidenceOutput,
    VisualObservation,
)
from services.worker.agents.mock_adapter import MockAgentAdapter
from services.worker.evaluation.contracts import (
    ExtractionCertainty,
    GeminiVisualEvidenceSchema,
    HopDirection,
    ImageQualityAssessment,
)
from services.worker.gemini.adapter import GeminiVisionAdapter, get_shared_gemini_adapter
from services.worker.security.provenance_guard import (
    TRUSTED_SYNTHETIC_DIR,
    UntrustedProvenanceError,
    verify_analysis_image_source,
    verify_synthetic_bytes,
    verify_synthetic_path,
)

logger = logging.getLogger(__name__)


@runtime_checkable
class VisualEvidenceProvider(Protocol):
    """Protocol defining the interface for visual evidence extraction providers."""

    last_tokens: int
    last_cost_usd: Optional[float]
    last_latency_ms: int
    last_telemetry: Optional[Dict[str, Any]]

    def extract_evidence(
        self,
        response_id: str,
        image_source: Optional[Union[str, Path, bytes]] = None,
        high_res_mode: bool = False,
        confidence_override: Optional[float] = None,
        **kwargs: Any,
    ) -> VisualEvidenceOutput:
        """Extracts structured visual evidence from student work."""
        ...


class MockVisualEvidenceProvider:
    """Offline mock provider returning deterministic synthetic fixtures without API calls."""

    def __init__(self) -> None:
        self.last_tokens: int = 0
        self.last_cost_usd: Optional[float] = 0.0
        self.last_latency_ms: int = 0
        self.last_telemetry: Optional[Dict[str, Any]] = None

    def extract_evidence(
        self,
        response_id: str,
        image_source: Optional[Union[str, Path, bytes]] = None,
        high_res_mode: bool = False,
        confidence_override: Optional[float] = None,
        **kwargs: Any,
    ) -> VisualEvidenceOutput:
        """Returns deterministic fixture output from MockAgentAdapter."""
        evidence = MockAgentAdapter.get_visual_evidence(
            response_id=response_id,
            high_res_mode=high_res_mode,
            confidence_override=confidence_override,
        )
        self.last_tokens = 0
        self.last_cost_usd = 0.0
        self.last_latency_ms = 1
        self.last_telemetry = {
            "mode": "mock",
            "provider": "MockVisualEvidenceProvider",
            "provenance": evidence.provenance,
        }
        return evidence


def gemini_schema_to_visual_evidence(
    schema: GeminiVisualEvidenceSchema,
    model_id: str = "gemini-3.8-flash",
    high_res_mode: bool = False,
    confidence_override: Optional[float] = None,
) -> VisualEvidenceOutput:
    """Translates GeminiVisualEvidenceSchema into ClassLens VisualEvidenceOutput contract.

    Decouples visual observations from mathematical correctness:
    - Number line hops are transcribed as physical marks.
    - Stated magnitudes and directions are preserved as reported.
    - Ambiguities and teacher review requests are propagated.
    - Downstream SymPy verifier determines mathematical truth.
    """
    quality_map = {
        ImageQualityAssessment.CLEAR: QualityStatus.CLEAR,
        ImageQualityAssessment.FAINT_READABLE: QualityStatus.FAINT_READABLE,
        ImageQualityAssessment.BLURRED: QualityStatus.BLURRED,
        ImageQualityAssessment.LOW_CONTRAST: QualityStatus.LOW_CONTRAST,
        ImageQualityAssessment.UNREADABLE: QualityStatus.UNREADABLE,
    }
    quality_status = quality_map.get(schema.image_quality, QualityStatus.CLEAR)

    observations: List[VisualObservation] = []

    # 1. Number Line presence
    if schema.number_line.is_present:
        min_tick = schema.number_line.min_visible_tick if schema.number_line.min_visible_tick is not None else -10.0
        max_tick = schema.number_line.max_visible_tick if schema.number_line.max_visible_tick is not None else 10.0
        observations.append(
            VisualObservation(
                kind="number_line",
                value=f"Horizontal number line [{min_tick:g}, {max_tick:g}]",
                confidence=0.98,
            )
        )

    # 2. Observed Hops (physical ink strokes)
    certainty_conf = {
        ExtractionCertainty.HIGH: 0.95,
        ExtractionCertainty.MEDIUM: 0.80,
        ExtractionCertainty.LOW: 0.50,
        ExtractionCertainty.CANNOT_DETERMINE: 0.30,
    }

    for hop in schema.number_line.observed_hops:
        # Determine direction
        if hop.direction == HopDirection.LEFT_NEGATIVE:
            dir_str = "left"
        elif hop.direction == HopDirection.RIGHT_POSITIVE:
            dir_str = "right"
        else:
            dir_str = "none"

        # Parse stated magnitude label if written
        mag_val: Optional[float] = None
        if hop.stated_magnitude_label:
            try:
                mag_val = float(hop.stated_magnitude_label.strip().replace("+", ""))
            except ValueError:
                mag_val = None

        hop_conf = certainty_conf.get(hop.certainty, 0.85)

        if hop.start_value is not None and hop.end_value is not None:
            val_text = f"Hop {hop.hop_index}: {hop.start_value:g} to {hop.end_value:g}"
        elif hop.start_value is not None:
            val_text = f"Hop {hop.hop_index}: start {hop.start_value:g} (incomplete termination)"
        else:
            val_text = f"Hop {hop.hop_index} (undetermined coordinates)"

        observations.append(
            VisualObservation(
                kind="arrow_jump",
                value=val_text,
                confidence=hop_conf,
                start_pos=hop.start_value,
                end_pos=hop.end_value,
                direction=dir_str,
                stated_magnitude=mag_val,
                bounding_box=None,
            )
        )

    # 3. Circled or written final answer
    final_ans = schema.visible_final_answer.value if schema.visible_final_answer else None
    if final_ans is not None:
        ans_conf = certainty_conf.get(schema.visible_final_answer.certainty, 0.90)
        observations.append(
            VisualObservation(
                kind="circled_result",
                value=str(final_ans),
                confidence=ans_conf,
            )
        )

    # 4. Alternative visual models or unsupported notations
    unsupported_items = getattr(schema, "unsupported_observations", []) or []
    for unsupp in unsupported_items:
        observations.append(
            VisualObservation(
                kind="text_label",
                value=str(unsupp),
                confidence=0.90,
            )
        )

    req_review = schema.requires_teacher_review
    review_reason = schema.teacher_review_reason

    # 5. Uncertainty and overall confidence
    if confidence_override is not None:
        overall_conf = confidence_override
    elif quality_status == QualityStatus.UNREADABLE:
        overall_conf = 0.30
    elif req_review and any(a.severity == "blocking" for a in schema.ambiguities):
        overall_conf = 0.60
    elif req_review:
        overall_conf = 0.70
    else:
        obs_confs = [o.confidence for o in observations]
        overall_conf = round(sum(obs_confs) / len(obs_confs), 2) if obs_confs else 0.92

    # Ambiguities text list
    ambiguity_strings = [f"{a.element}: {a.description}" for a in schema.ambiguities]

    return VisualEvidenceOutput(
        quality_status=quality_status,
        observations=observations,
        has_number_line=schema.number_line.is_present,
        final_answer_marked=final_ans,
        confidence=overall_conf,
        provenance=model_id,
        resolution_mode="high_res_evaluation" if high_res_mode else "standard_768px",
        ambiguities=ambiguity_strings,
        requires_teacher_review=req_review,
        teacher_review_reason=review_reason,
        raw_extraction=schema.model_dump(),
    )


class GeminiVisualEvidenceProvider:
    """Production Gemini multimodal provider with strict synthetic provenance validation."""

    def __init__(
        self,
        adapter: Optional[GeminiVisionAdapter] = None,
        model_id: Optional[str] = None,
        location: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        self.model_id = model_id or settings.gemini_model
        self.location = location or settings.google_cloud_location
        self.project = project or settings.google_cloud_project

        if adapter is not None:
            self.adapter = adapter
        else:
            self.adapter = get_shared_gemini_adapter(
                model_id=self.model_id,
                location=self.location,
                project=self.project,
            )

        self.last_tokens: int = 0
        self.last_cost_usd: Optional[float] = 0.0
        self.last_latency_ms: int = 0
        self.last_telemetry: Optional[Dict[str, Any]] = None

    def _resolve_synthetic_fixture_for_response(self, response_id: str) -> Path:
        """Maps response identifier to authorized synthetic fixture path in tests/fixtures/."""
        r_lower = response_id.lower()
        if "case_01" in r_lower or "04255753" in r_lower or "canonical" in r_lower:
            return TRUSTED_SYNTHETIC_DIR / "case_01_canonical_correct.png"
        elif "case_02" in r_lower or "off_by_one" in r_lower or "procedural" in r_lower:
            return TRUSTED_SYNTHETIC_DIR / "case_02_off_by_one_error.png"
        elif "case_03" in r_lower or "ambiguous" in r_lower or "incomplete" in r_lower:
            return TRUSTED_SYNTHETIC_DIR / "case_03_ambiguous_incomplete.png"
        else:
            raise UntrustedProvenanceError(
                f"Provenance Guard Block: Response ID '{response_id}' does not map to an authorized "
                "synthetic fixture. Live Gemini inference is strictly restricted to verified synthetic cases in Gate 4A."
            )

    def extract_evidence(
        self,
        response_id: str,
        image_source: Optional[Union[str, Path, bytes]] = None,
        high_res_mode: bool = False,
        confidence_override: Optional[float] = None,
        prompt_override: Optional[str] = None,
        auth_key: Optional[str] = None,
        **kwargs: Any,
    ) -> VisualEvidenceOutput:
        """Extracts structured visual evidence using live Gemini with provenance and authorization verification."""
        # 1. Enforce image source provenance and authorization (Gate 6)
        if image_source is not None:
            verified_target = verify_analysis_image_source(
                image_source,
                response_id=response_id,
                auth_key=auth_key,
            )
            if isinstance(verified_target, Path):
                schema = self.adapter.extract_from_path(
                    image_path=verified_target,
                    response_id=response_id,
                    prompt_override=prompt_override,
                )
            else:
                schema = self.adapter.extract_from_bytes(
                    image_bytes=verified_target,
                    response_id=response_id,
                    prompt_override=prompt_override,
                )
        else:
            # Fall back to resolving authorized synthetic fixture by response_id
            fixture_path = self._resolve_synthetic_fixture_for_response(response_id)
            trusted_path = verify_synthetic_path(fixture_path)
            schema = self.adapter.extract_from_path(
                image_path=trusted_path,
                response_id=response_id,
                prompt_override=prompt_override,
            )

        # 2. Capture telemetry
        if self.adapter.call_history:
            latest = self.adapter.call_history[-1]
            self.last_tokens = latest.get("input_tokens", 0) + latest.get("output_tokens", 0)
            self.last_cost_usd = latest.get("estimated_cost_usd", 0.0)
            self.last_latency_ms = latest.get("latency_ms", self.adapter.last_latency_ms)
            self.last_telemetry = latest

        # 3. Translate schema into VisualEvidenceOutput
        return gemini_schema_to_visual_evidence(
            schema=schema,
            model_id=self.adapter.model_id,
            high_res_mode=high_res_mode,
            confidence_override=confidence_override,
        )


def get_visual_evidence_provider(
    mode: Optional[str] = None,
    adapter: Optional[GeminiVisionAdapter] = None,
    auth_key: Optional[str] = None,
) -> VisualEvidenceProvider:
    """Factory selecting visual evidence provider based on active settings or explicit mode.

    Defaults to MockVisualEvidenceProvider unless live mode is explicitly configured AND authorized.
    """
    selected_mode = mode.lower() if mode else ("live" if settings.is_live_authorized(auth_key) else "mock")

    if selected_mode == "live":
        settings.validate_live_configuration(provided_key=auth_key)
        return GeminiVisualEvidenceProvider(adapter=adapter)

    return MockVisualEvidenceProvider()
