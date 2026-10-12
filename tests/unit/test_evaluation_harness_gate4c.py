"""Unit tests for ClassLens Gate 4C Evaluation Harness and Benchmark Runner."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from evaluation.metrics import _calc_fraction, compute_evaluation_metrics
from evaluation.runner import (
    evaluate_single_case,
    generate_markdown_report,
    load_benchmark_dataset,
    run_benchmark,
)
from evaluation.schemas import (
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkReport,
    CaseEvaluationResult,
    GroundTruthHop,
    MetricFraction,
)
from services.worker.agents.provider import MockVisualEvidenceProvider


@pytest.fixture
def benchmark_v1_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "evaluation" / "datasets" / "benchmark_v1.json"


def test_load_benchmark_dataset_validates_schema(benchmark_v1_path: Path):
    """Verifies that the benchmark v1 dataset file loads cleanly and matches schema."""
    dataset = load_benchmark_dataset(benchmark_v1_path)
    assert dataset.dataset_name == "ClassLens Number-Line Reliability Benchmark"
    assert dataset.version == "1.0.0"
    assert len(dataset.cases) == 18

    # Verify categories represent all 6 target classes
    categories = {c.category for c in dataset.cases}
    assert "canonical_correct" in categories
    assert "off_by_one" in categories
    assert "compensatory" in categories
    assert "arithmetic_slip" in categories
    assert "sign_error" in categories
    assert "ambiguous_insufficient" in categories


def test_evaluate_single_case_canonical_correct(benchmark_v1_path: Path):
    """Verifies evaluation of a canonical correct student case."""
    dataset = load_benchmark_dataset(benchmark_v1_path)
    case_01 = next(c for c in dataset.cases if c.case_id == "case_01_canonical_correct")

    provider = MockVisualEvidenceProvider()
    result = evaluate_single_case(case_01, provider=provider)

    assert result.passed is True
    assert result.answer_status_match is True
    assert result.final_answer_match is True
    assert result.reasoning_status_match is True
    assert result.error_step_match is True
    assert result.misconception_match is True
    assert result.evidence_sufficiency_match is True
    assert result.teacher_review_match is True
    assert result.critic_verdict_match is True
    assert result.false_positive_misconception is False
    assert len(result.failure_reasons) == 0


def test_evaluate_single_case_off_by_one(benchmark_v1_path: Path):
    """Verifies evaluation of an off-by-one error case with misconception localization."""
    dataset = load_benchmark_dataset(benchmark_v1_path)
    case_02 = next(c for c in dataset.cases if c.case_id == "case_02_off_by_one_error")

    provider = MockVisualEvidenceProvider()
    result = evaluate_single_case(case_02, provider=provider)

    assert result.passed is True
    assert result.actual_values["reasoning_status"] == "supported_error"
    assert result.actual_values["error_step_index"] == 1  # Hop 2
    assert "MISC-" in (result.actual_values["misconception_id"] or "")
    assert result.misconception_match is True


def test_evaluate_single_case_ambiguous_abstention(benchmark_v1_path: Path):
    """Verifies evaluation of ambiguous incomplete work withholding misconception."""
    dataset = load_benchmark_dataset(benchmark_v1_path)
    case_03 = next(c for c in dataset.cases if c.case_id == "case_03_ambiguous_incomplete")

    provider = MockVisualEvidenceProvider()
    result = evaluate_single_case(case_03, provider=provider)

    assert result.passed is True
    assert result.actual_values["answer_status"] == "undetermined"
    assert result.actual_values["reasoning_status"] == "incomplete"
    assert result.actual_values["misconception_id"] is None
    assert result.actual_values["requires_teacher_review"] is True
    assert result.false_positive_misconception is False
    assert result.unsupported_claim_detected is False


def test_evaluate_single_case_compensatory(benchmark_v1_path: Path):
    """Verifies evaluation of a compensatory error case flagging teacher review."""
    dataset = load_benchmark_dataset(benchmark_v1_path)
    case_comp = next(c for c in dataset.cases if c.case_id == "resp_56005c1c")

    provider = MockVisualEvidenceProvider()
    result = evaluate_single_case(case_comp, provider=provider)

    assert result.passed is True
    assert result.actual_values["answer_status"] == "correct"
    assert result.actual_values["reasoning_status"] == "supported_error"
    assert result.actual_values["requires_teacher_review"] is True


def test_calc_fraction_handles_zero_denominator():
    """Verifies that _calc_fraction handles 0 denominators cleanly without division by zero."""
    frac = _calc_fraction(
        name="Empty Metric",
        num=0,
        den=0,
        desc="Test edge case",
        threshold=80.0,
    )
    assert frac.percentage is None
    assert frac.display_value == "N/A"
    assert frac.status == "N/A"


def test_calc_fraction_status_thresholding():
    """Verifies pass/fail thresholding logic in _calc_fraction."""
    pass_frac = _calc_fraction("Test Pass", num=9, den=10, desc="", threshold=85.0)
    assert pass_frac.percentage == 90.0
    assert pass_frac.status == "PASS"

    fail_frac = _calc_fraction("Test Fail", num=8, den=10, desc="", threshold=85.0)
    assert fail_frac.percentage == 80.0
    assert fail_frac.status == "FAIL"


def test_compute_evaluation_metrics_complete_suite(benchmark_v1_path: Path):
    """Verifies metric computation across full suite meets all defined thresholds."""
    dataset = load_benchmark_dataset(benchmark_v1_path)
    provider = MockVisualEvidenceProvider()

    results = [evaluate_single_case(c, provider=provider) for c in dataset.cases]
    metrics = compute_evaluation_metrics(dataset.cases, results, total_eval_duration_sec=0.5)

    assert metrics.answer_status_accuracy.status == "PASS"
    assert metrics.final_answer_agreement.status == "PASS"
    assert metrics.reasoning_status_accuracy.status == "PASS"
    assert metrics.procedural_error_detection_recall.status == "PASS"
    assert metrics.error_step_localization_accuracy.status == "PASS"
    assert metrics.misconception_precision.status == "PASS"
    assert metrics.misconception_recall.status == "PASS"
    assert metrics.false_positive_misconception_rate.status == "PASS"
    assert metrics.evidence_sufficiency_accuracy.status == "PASS"
    assert metrics.appropriate_abstention_rate.status == "PASS"
    assert metrics.unsupported_claim_rate.status == "PASS"
    assert metrics.contradiction_rate.status == "PASS"
    assert metrics.review_routing_precision.status == "PASS"
    assert metrics.review_routing_recall.status == "PASS"
    assert metrics.missed_critical_review_count == 0
    assert metrics.critic_verdict_accuracy.status == "PASS"
    assert metrics.critic_challenge_precision.status == "PASS"


def test_run_benchmark_produces_valid_reports(benchmark_v1_path: Path):
    """Verifies full runner execution produces structured JSON and Markdown reports."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report = run_benchmark(
            dataset_path=benchmark_v1_path,
            output_dir=tmp_dir,
            provider=MockVisualEvidenceProvider(),
        )

        assert report.overall_status == "PASS"
        assert report.total_cases == 18
        assert report.passed_cases == 18
        assert report.failed_cases == 0
        assert report.overall_pass_rate_pct == 100.0

        json_file = Path(tmp_dir) / "latest_benchmark_report.json"
        md_file = Path(tmp_dir) / "latest_benchmark_report.md"

        assert json_file.is_file()
        assert md_file.is_file()

        # Validate JSON content against schema
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        reloaded = BenchmarkReport.model_validate(data)
        assert reloaded.total_cases == 18
        assert reloaded.metrics.answer_status_accuracy.percentage == 100.0

        # Validate Markdown content
        md_text = md_file.read_text(encoding="utf-8")
        assert "# ClassLens AI Assessment Reliability Benchmark Report" in md_text
        assert "Answer Status Accuracy" in md_text
        assert "Category Breakdown" in md_text


def test_run_benchmark_category_filter(benchmark_v1_path: Path):
    """Verifies runner supports filtering by category."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report = run_benchmark(
            dataset_path=benchmark_v1_path,
            category_filter="canonical_correct",
            output_dir=tmp_dir,
            provider=MockVisualEvidenceProvider(),
        )
        assert report.total_cases == 8
        assert report.passed_cases == 8
        assert all(c.category == "canonical_correct" for c in report.case_results)
