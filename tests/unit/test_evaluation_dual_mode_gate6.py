"""Unit tests for Gate 6 Checkpoint D: Dual-Mode Evaluation Harness.

Verifies:
- Offline regression suite runs deterministically with $0.00 spend.
- Authorized live mode fails closed if unauthorized.
- Authorized live mode generates latest_live_evaluation_report.json / .md without overwriting offline report.
- Dev endpoints expose live evaluation status, fail closed on unauthorized live runs,
  and support mode-specific markdown retrieval.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from evaluation.runner import evaluate_single_case, run_benchmark
from evaluation.schemas import BenchmarkReport
from services.api.config import Settings, settings
from services.api.main import app
from services.worker.agents.provider import MockVisualEvidenceProvider


@pytest.fixture
def client():
    return TestClient(app)


def test_offline_regression_mode_produces_benchmark_reports():
    """Verifies mode='offline_regression' produces latest_benchmark_report.json and .md with $0.00 spend."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report = run_benchmark(
            dataset_path="evaluation/datasets/benchmark_v1.json",
            category_filter="canonical_correct",
            output_dir=tmp_dir,
            mode="offline_regression",
            provider=MockVisualEvidenceProvider(),
        )

        assert report.evaluation_mode == "offline_regression"
        assert report.pipeline_mode == "mock-offline"
        assert report.overall_status == "PASS"

        json_path = Path(tmp_dir) / "latest_benchmark_report.json"
        md_path = Path(tmp_dir) / "latest_benchmark_report.md"
        assert json_path.is_file()
        assert md_path.is_file()

        # Offline report notice check
        md_text = md_path.read_text(encoding="utf-8")
        assert "Deterministic Offline Regression Suite" in md_text
        assert "$0.00 spend" in md_text


def test_authorized_live_mode_fails_closed_when_unauthorized():
    """Verifies mode='authorized_live' raises PermissionError when unauthorized."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Default settings: live_inference_enabled is False, auth key is empty
        with pytest.raises(PermissionError) as exc_info:
            run_benchmark(
                dataset_path="evaluation/datasets/handwriting_eval_v1.json",
                output_dir=tmp_dir,
                mode="authorized_live",
            )
        assert "Live inference is strictly disabled to prevent unauthorized charges" in str(exc_info.value)


def test_authorized_live_mode_succeeds_when_authorized_with_provider():
    """Verifies mode='authorized_live' runs when authorized and creates distinct live report files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Simulate authorized configuration
        with patch.object(Settings, "is_live_authorized", return_value=True):
            report = run_benchmark(
                dataset_path="evaluation/datasets/handwriting_eval_v1.json",
                category_filter="clear_correct_solution",
                output_dir=tmp_dir,
                mode="authorized_live",
                provider=MockVisualEvidenceProvider(),
                auth_key="valid-test-key",
            )

            assert report.evaluation_mode == "authorized_live"
            assert report.pipeline_mode == "authorized-live"
            assert report.live_authorized is True

            json_path = Path(tmp_dir) / "latest_live_evaluation_report.json"
            md_path = Path(tmp_dir) / "latest_live_evaluation_report.md"
            assert json_path.is_file()
            assert md_path.is_file()

            # Ensure offline file was NOT created or overwritten
            assert not (Path(tmp_dir) / "latest_benchmark_report.json").exists()

            md_text = md_path.read_text(encoding="utf-8")
            assert "ClassLens Real Gemini Handwriting Evaluation Report (Authorized Live Mode)" in md_text


def test_offline_and_live_reports_do_not_overwrite_each_other():
    """Verifies that running offline and live evaluations produce independent, coexisting reports."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Run offline
        offline_rep = run_benchmark(
            dataset_path="evaluation/datasets/benchmark_v1.json",
            category_filter="canonical_correct",
            output_dir=tmp_dir,
            mode="offline_regression",
            provider=MockVisualEvidenceProvider(),
        )

        offline_json = Path(tmp_dir) / "latest_benchmark_report.json"
        assert offline_json.is_file()

        # 2. Run live
        with patch.object(Settings, "is_live_authorized", return_value=True):
            live_rep = run_benchmark(
                dataset_path="evaluation/datasets/handwriting_eval_v1.json",
                category_filter="clear_correct_solution",
                output_dir=tmp_dir,
                mode="authorized_live",
                provider=MockVisualEvidenceProvider(),
                auth_key="valid-key",
            )

        live_json = Path(tmp_dir) / "latest_live_evaluation_report.json"
        assert live_json.is_file()

        # Re-read offline report to ensure untouched
        with open(offline_json, "r", encoding="utf-8") as f:
            reloaded_offline = json.load(f)
        assert reloaded_offline["evaluation_mode"] == "offline_regression"
        assert reloaded_offline["pipeline_mode"] == "mock-offline"

        # Re-read live report
        with open(live_json, "r", encoding="utf-8") as f:
            reloaded_live = json.load(f)
        assert reloaded_live["evaluation_mode"] == "authorized_live"
        assert reloaded_live["pipeline_mode"] == "authorized-live"


def test_dev_endpoint_get_evaluation_latest_reports_live_status(client):
    """Verifies GET /dev/evaluation/latest reports live_evaluation_status."""
    resp = client.get("/api/v1/dev/evaluation/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert "live_evaluation_status" in data
    assert data["live_evaluation_status"] in ("not_performed", "completed")


def test_dev_endpoint_live_latest_status(client):
    """Verifies GET /dev/evaluation/live-latest returns structured response."""
    resp = client.get("/api/v1/dev/evaluation/live-latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("not_performed", "completed")
    if data["status"] == "not_performed":
        assert "Not yet performed" in data["message"]


def test_dev_endpoint_run_live_fails_closed_unauthorized(client):
    """Verifies POST /dev/evaluation/run-live returns 403 Forbidden when unauthorized."""
    resp = client.post("/api/v1/dev/evaluation/run-live")
    assert resp.status_code == 403
    assert "Live handwriting evaluation requires" in resp.json()["detail"]
    assert "$0.00 spend guarantee" in resp.json()["detail"]


def test_dev_endpoint_run_live_succeeds_when_authorized(client):
    """Verifies POST /dev/evaluation/run-live succeeds when authorized header provided."""
    with patch.object(Settings, "is_live_authorized", return_value=True):
        with patch("evaluation.runner.run_benchmark") as mock_runner:
            mock_report = MagicMock()
            mock_report.model_dump.return_value = {
                "run_id": "test_run",
                "overall_status": "PASS",
                "evaluation_mode": "authorized_live",
                "total_cases": 20,
            }
            mock_runner.return_value = mock_report

            resp = client.post(
                "/api/v1/dev/evaluation/run-live",
                headers={"X-ClassLens-Live-Auth": "valid-secret-key"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["evaluation_mode"] == "authorized_live"
            assert data["total_cases"] == 20


def test_dev_endpoint_markdown_supports_modes(client):
    """Verifies GET /dev/evaluation/markdown supports ?mode=offline and ?mode=live."""
    # Offline mode
    resp_off = client.get("/api/v1/dev/evaluation/markdown?mode=offline")
    assert resp_off.status_code == 200
    assert "markdown" in resp_off.json()

    # Live mode when not yet run
    resp_live = client.get("/api/v1/dev/evaluation/markdown?mode=live")
    assert resp_live.status_code == 200
    assert "markdown" in resp_live.json()
