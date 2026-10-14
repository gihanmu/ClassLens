"""Unit tests for Gate 6.1 Checkpoint D: Offline Evaluation Dry-Run Safety Mode.

Verifies:
1. Dry-run executes with strictly zero external requests ($0.00 spend).
2. Physical image absence is accurately detected and reported.
3. Missing ground-truth annotations are accurately reported.
4. Synthetic fixtures are strictly rejected when evaluating real handwriting datasets.
5. Max cases ceiling bounds the evaluation scope.
6. Live authorization status is accurately verified and reported.
7. Dry-run reports are isolated and do not overwrite standard benchmark outputs.
8. Actionable diagnostics and readiness verdicts correctly reflect prerequisites.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evaluation.runner import load_benchmark_dataset, run_benchmark, run_dry_run
from evaluation.schemas import DryRunReport
from services.api.config import Settings


def test_dry_run_executes_zero_external_requests():
    """Confirms dry-run never invokes Gemini or makes external API requests."""
    with patch("services.worker.gemini.adapter.GeminiVisionAdapter.extract_from_bytes") as mock_extract:
        report = run_benchmark(
            dataset_path="evaluation/datasets/blind_eval_specification.json",
            dry_run=True,
            output_dir=tempfile.gettempdir(),
        )

    assert isinstance(report, DryRunReport)
    assert report.external_requests_sent == 0
    assert mock_extract.call_count == 0


def test_dry_run_accurately_detects_missing_images():
    """Ensures dry-run correctly flags that physical images are missing from disk."""
    report = run_dry_run(
        dataset_path="evaluation/datasets/blind_eval_specification.json",
        output_dir=tempfile.gettempdir(),
    )

    assert report.total_cases_selected == 5
    assert report.images_present_count == 0
    assert report.images_missing_count == 5
    assert report.readiness_verdict == "NOT_READY_MISSING_PREREQUISITES"

    for case_res in report.case_manifest:
        assert case_res.image_exists_on_disk is False
        assert case_res.ready_for_evaluation is False
        assert any("not found on disk" in b for b in case_res.blockers)


def test_dry_run_verifies_quarantined_annotations():
    """Confirms dry-run verifies sequestered human ground-truth annotations in blind_eval_ground_truth.json."""
    report = run_dry_run(
        dataset_path="evaluation/datasets/blind_eval_specification.json",
        output_dir=tempfile.gettempdir(),
    )

    # All 5 blind cases have corresponding entries in blind_eval_ground_truth.json
    assert report.annotations_present_count == 5
    assert report.annotations_missing_count == 0
    for case_res in report.case_manifest:
        assert case_res.has_ground_truth_annotation is True


def test_dry_run_rejects_synthetic_fixtures_for_handwriting():
    """Confirms that existing synthetic fixtures in tests/fixtures/ are rejected for handwriting cases."""
    temp_dir = tempfile.mkdtemp()
    temp_dataset_path = Path(temp_dir) / "test_handwriting_with_synthetic.json"

    # Author a dataset case that illicitly points to a synthetic fixture
    payload = {
        "dataset_name": "Test Synthetic Contamination Dataset",
        "version": "1.0.0",
        "created_at": "2026-10-14T00:00:00Z",
        "description": "Tests synthetic fixture rejection",
        "target_problem_reference": "problem_1065658",
        "cases": [
            {
                "case_id": "hw_eval_sneaky_synthetic",
                "category": "clear_correct_solution",
                "target_canonical_value": "2",
                "image_reference": "case_01_canonical_correct.png",  # Exists in tests/fixtures/!
                "source_type": "adult_consenting_synthetic",
                "expected_answer": "2",
                "expected_answer_status": "correct",
                "expected_reasoning_status": "supported_correct",
            }
        ],
    }

    temp_dataset_path.write_text(json.dumps(payload), encoding="utf-8")

    report = run_dry_run(
        dataset_path=temp_dataset_path,
        output_dir=temp_dir,
    )

    assert report.total_cases_selected == 1
    assert report.images_present_count == 0  # Not counted as present for handwriting!
    assert report.synthetic_fixtures_rejected_count == 1
    assert report.readiness_verdict == "NOT_READY_MISSING_PREREQUISITES"

    case_res = report.case_manifest[0]
    assert case_res.image_exists_on_disk is False
    assert any("REJECTED: synthetic fixtures cannot stand in" in b for b in case_res.blockers)


def test_dry_run_respects_max_cases_ceiling():
    """Verifies that max_cases limits the scope of cases selected for evaluation."""
    report = run_dry_run(
        dataset_path="evaluation/datasets/blind_eval_specification.json",
        max_cases=2,
        output_dir=tempfile.gettempdir(),
    )

    assert report.max_cases_ceiling == 2
    assert report.total_cases_selected == 2
    assert len(report.case_manifest) == 2
    assert report.case_manifest[0].case_id == "blind_eval_01_canonical_correct"
    assert report.case_manifest[1].case_id == "blind_eval_02_off_by_one_under"


def test_dry_run_checks_live_authorization_safeguards():
    """Verifies that authorized_live mode dry run verifies live enablement and auth keys."""
    # Subtest 1: Live mode disabled (default)
    mock_settings_disabled = Settings(
        ai_mode="mock",
        live_inference_enabled=False,
        mock_llm=True,
    )
    with patch("services.api.config.settings", mock_settings_disabled):
        report = run_dry_run(
            dataset_path="evaluation/datasets/blind_eval_specification.json",
            mode="authorized_live",
            output_dir=tempfile.gettempdir(),
        )

    assert report.live_inference_enabled is False
    assert report.live_authorization_valid is False
    assert report.readiness_verdict == "NOT_READY_MISSING_PREREQUISITES"
    assert any("strictly disabled in settings" in d for d in report.actionable_diagnostics)


def test_dry_run_generates_isolated_reports():
    """Confirms dry-run writes latest_dry_run_report.* without modifying latest_benchmark_report.*."""
    temp_dir = tempfile.mkdtemp()
    report = run_dry_run(
        dataset_path="evaluation/datasets/blind_eval_specification.json",
        output_dir=temp_dir,
    )

    dry_json = Path(temp_dir) / "latest_dry_run_report.json"
    dry_md = Path(temp_dir) / "latest_dry_run_report.md"
    bench_json = Path(temp_dir) / "latest_benchmark_report.json"
    bench_md = Path(temp_dir) / "latest_benchmark_report.md"

    assert dry_json.is_file()
    assert dry_md.is_file()
    assert not bench_json.exists()
    assert not bench_md.exists()

    loaded = json.loads(dry_json.read_text(encoding="utf-8"))
    assert loaded["dry_run_id"] == report.dry_run_id
    assert loaded["external_requests_sent"] == 0
