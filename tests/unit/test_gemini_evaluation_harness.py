"""Unit tests for Gate 3 Gemini Evaluation Harness, Adapter, Contracts, and Verification Connector."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from services.worker.evaluation.contracts import (
    BatchEvaluationSummary,
    EvaluationCaseResult,
    ExtractionCertainty,
    GeminiVisualEvidenceSchema,
    HopDirection,
    ImageQualityAssessment,
    NumberLineObservation,
    ObservedHop,
    VerifiedStepComparison,
    VisibleFinalAnswer,
    VisualAmbiguity,
)
from services.worker.evaluation.gemini_adapter import (
    DEFAULT_SYSTEM_PROMPT,
    GeminiEvaluationAdapter,
)
from services.worker.evaluation.verification_connector import (
    VerificationConnector,
    get_canonical_problem_1065658_rule,
)
from scripts.evaluate_gemini_handwriting import load_manifest, generate_markdown_report


@pytest.fixture
def sample_canonical_evidence() -> GeminiVisualEvidenceSchema:
    return GeminiVisualEvidenceSchema(
        response_id="case_01_canonical_correct",
        image_quality=ImageQualityAssessment.CLEAR,
        visible_final_answer=VisibleFinalAnswer(
            value="2",
            evidence_location="Answer box",
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
                    evidence_description="Arc from 0 to -6",
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
                    evidence_description="Arc from -6 to 6",
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
                    evidence_description="Arc from 6 to 2",
                    certainty=ExtractionCertainty.HIGH,
                ),
            ],
        ),
        ambiguities=[],
        requires_teacher_review=False,
    )


class TestEvaluationContracts:
    def test_schema_validates_canonical_output(self, sample_canonical_evidence):
        dumped = sample_canonical_evidence.model_dump_json()
        restored = GeminiVisualEvidenceSchema.model_validate_json(dumped)
        assert restored.response_id == "case_01_canonical_correct"
        assert len(restored.number_line.observed_hops) == 3
        assert restored.visible_final_answer.value == "2"

    def test_schema_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            GeminiVisualEvidenceSchema.model_validate({"response_id": "incomplete"})

    def test_observed_hop_defaults_and_validation(self):
        hop = ObservedHop(
            hop_index=1,
            start_value=0.0,
            end_value=-6.0,
            direction=HopDirection.LEFT_NEGATIVE,
            evidence_description="Jump to -6",
        )
        assert hop.arc_drawn is True
        assert hop.arrowhead_visible is False
        assert hop.certainty == ExtractionCertainty.MEDIUM


class TestVerificationConnector:
    def test_verification_canonical_correct(self, sample_canonical_evidence):
        result = VerificationConnector.connect_and_verify(
            extraction=sample_canonical_evidence,
            manifest_category="canonical_correct",
            model_id="gemini-3.8-flash",
            dry_run=True,
        )
        assert result.math_verification_status == "valid"
        assert len(result.verified_steps) == 3
        assert all(s.is_mathematically_valid for s in result.verified_steps)
        assert result.teacher_escalation_correct is True

    def test_verification_detects_off_by_one_error(self):
        evidence = GeminiVisualEvidenceSchema(
            response_id="case_02_off_by_one",
            image_quality=ImageQualityAssessment.CLEAR,
            visible_final_answer=VisibleFinalAnswer(
                value="1",
                certainty=ExtractionCertainty.HIGH,
            ),
            number_line=NumberLineObservation(
                is_present=True,
                observed_hops=[
                    ObservedHop(
                        hop_index=1,
                        start_value=0.0,
                        end_value=-6.0,
                        direction=HopDirection.LEFT_NEGATIVE,
                        stated_magnitude_label="-6",
                        evidence_description="Jump 0 to -6",
                    ),
                    ObservedHop(
                        hop_index=2,
                        start_value=-6.0,
                        end_value=5.0,  # 11 units instead of 12
                        direction=HopDirection.RIGHT_POSITIVE,
                        stated_magnitude_label="+12",
                        evidence_description="Jump -6 to 5",
                    ),
                    ObservedHop(
                        hop_index=3,
                        start_value=5.0,
                        end_value=1.0,
                        direction=HopDirection.LEFT_NEGATIVE,
                        stated_magnitude_label="-4",
                        evidence_description="Jump 5 to 1",
                    ),
                ],
            ),
            ambiguities=[],
            requires_teacher_review=False,
        )
        result = VerificationConnector.connect_and_verify(
            extraction=evidence,
            manifest_category="procedural_error",
            model_id="gemini-3.8-flash",
        )
        assert result.math_verification_status == "arithmetic_error"
        assert result.first_supported_error_step == 2

    def test_verification_handles_ambiguous_incomplete(self):
        evidence = GeminiVisualEvidenceSchema(
            response_id="case_03_ambiguous",
            image_quality=ImageQualityAssessment.FAINT_READABLE,
            visible_final_answer=VisibleFinalAnswer(
                value=None,
                certainty=ExtractionCertainty.CANNOT_DETERMINE,
            ),
            number_line=NumberLineObservation(
                is_present=True,
                observed_hops=[
                    ObservedHop(
                        hop_index=1,
                        start_value=0.0,
                        end_value=-6.0,
                        direction=HopDirection.LEFT_NEGATIVE,
                        arrowhead_visible=False,
                        evidence_description="Faint jump 0 to -6",
                    ),
                    ObservedHop(
                        hop_index=2,
                        start_value=-6.0,
                        end_value=None,  # Incomplete endpoint
                        direction=HopDirection.AMBIGUOUS,
                        arrowhead_visible=False,
                        evidence_description="Incomplete arc terminating ambiguously",
                    ),
                ],
            ),
            ambiguities=[
                VisualAmbiguity(
                    element="hop",
                    description="Terminates without landing mark",
                    severity="blocking",
                )
            ],
            requires_teacher_review=True,
            teacher_review_reason="Incomplete hops and blank answer",
        )
        result = VerificationConnector.connect_and_verify(
            extraction=evidence,
            manifest_category="ambiguous_incomplete",
        )
        assert result.math_verification_status == "uninterpretable"
        assert result.visual_extraction.requires_teacher_review is True
        assert result.teacher_escalation_correct is True


class TestGeminiEvaluationAdapter:
    def test_dry_run_executes_offline_with_deterministic_mock(self):
        adapter = GeminiEvaluationAdapter(
            model_id="gemini-2.5-flash",
            max_calls=3,
            dry_run=True,
            live_opt_in=False,
        )
        image_path = "tests/fixtures/synthetic_evaluation_cases/case_01_canonical_correct.png"
        evidence = adapter.extract_visual_evidence(image_path, "case_01_canonical_correct")

        assert evidence.response_id == "case_01_canonical_correct"
        assert evidence.visible_final_answer.value == "2"
        assert adapter.call_count == 1
        assert adapter.total_input_tokens > 0
        assert adapter.total_estimated_cost_usd > 0.0
        assert adapter.call_history[0]["dry_run"] is True

    def test_token_rates_lookup_for_gemini_2_5_flash(self):
        adapter = GeminiEvaluationAdapter(model_id="gemini-2.5-flash")
        rates = adapter.get_token_rates()
        assert rates["input_per_token"] == 0.30 / 1_000_000.0
        assert rates["output_per_token"] == 2.50 / 1_000_000.0

    def test_token_rates_lookup_for_gemini_3_8_flash(self):
        adapter = GeminiEvaluationAdapter(model_id="gemini-3.8-flash")
        rates = adapter.get_token_rates()
        assert rates["input_per_token"] == 0.75 / 1_000_000.0
        assert rates["output_per_token"] == 3.75 / 1_000_000.0

    def test_synthetic_isolation_guardrail_blocks_dataset_paths(self):
        adapter = GeminiEvaluationAdapter(dry_run=True)
        # Attempt to pass a path containing 'dataset' must raise PermissionError
        with pytest.raises(PermissionError, match="Security Guardrail Violation"):
            adapter.extract_visual_evidence("dataset/raw/image.png", "student_01")

    def test_live_opt_in_guardrail_blocks_unauthorized_call(self):
        # Attempting live execution without live_opt_in=True must fall back to dry run if dry_run=True
        adapter = GeminiEvaluationAdapter(
            model_id="gemini-2.5-flash",
            dry_run=False,
            live_opt_in=False,  # Not opted in
        )
        image_path = "tests/fixtures/synthetic_evaluation_cases/case_01_canonical_correct.png"
        evidence = adapter.extract_visual_evidence(image_path, "case_01_test")
        assert adapter.call_history[-1]["dry_run"] is True

    def test_hard_call_ceiling_blocks_excessive_calls(self):
        adapter = GeminiEvaluationAdapter(
            model_id="gemini-2.5-flash",
            max_calls=2,
            dry_run=False,
            live_opt_in=True,
        )
        # Manually set call count to max to verify enforcement
        adapter.call_count = 2
        with pytest.raises(RuntimeError, match="Budget Exceeded"):
            image_path = "tests/fixtures/synthetic_evaluation_cases/case_01_canonical_correct.png"
            adapter.extract_visual_evidence(image_path, "case_extra")

    def test_missing_image_file_raises_not_found(self):
        adapter = GeminiEvaluationAdapter(dry_run=True)
        with pytest.raises(FileNotFoundError):
            adapter.extract_visual_evidence("tests/fixtures/synthetic_evaluation_cases/non_existent.png", "missing_id")


class TestHarnessManifestAndReport:
    def test_manifest_loads_and_has_valid_structure(self):
        manifest_path = "docs/evaluations/gate3/manifest.json"
        data = load_manifest(manifest_path)
        assert data["gate"] == "Gate 3"
        assert len(data["cases"]) == 3
        for case in data["cases"]:
            assert Path(case["image_path"]).is_file()
            assert "expected" in case

    def test_markdown_report_generation(self, sample_canonical_evidence):
        case_res = EvaluationCaseResult(
            response_id="case_01_test",
            manifest_category="canonical_correct",
            model_id="gemini-3.8-flash",
            latency_ms=25,
            input_tokens=258,
            output_tokens=320,
            estimated_cost_usd=0.0002,
            visual_extraction=sample_canonical_evidence,
            verified_steps=[
                VerifiedStepComparison(
                    step_number=1,
                    operation="0.0 -> -6.0",
                    expected_displacement=-6.0,
                    observed_displacement=-6.0,
                    is_mathematically_valid=True,
                    evidence_citation="Step 1 valid",
                )
            ],
            math_verification_status="valid",
            teacher_escalation_correct=True,
            schema_valid=True,
            dry_run=True,
        )
        summary = BatchEvaluationSummary(
            total_cases=1,
            schema_conformant_count=1,
            mathematical_accuracy_rate=1.0,
            teacher_escalation_precision=1.0,
            total_input_tokens=258,
            total_output_tokens=320,
            total_cost_usd=0.0002,
            mean_latency_ms=25.0,
            model_id="gemini-3.8-flash",
            dry_run=True,
            case_results=[case_res],
        )
        report = generate_markdown_report(summary, [case_res], {})
        assert "# ClassLens — Gate 3 Gemini Feasibility Evaluation Report" in report
        assert "Schema Conformance" in report
        assert "case_01_test" in report
