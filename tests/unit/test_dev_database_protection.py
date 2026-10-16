"""Regression tests proving that the normal development database and uploads remain untouched during tests."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import pytest

from services.api.repository.storage_config import (
    DEFAULT_DATA_DIR,
    DEFAULT_UPLOADS_DIR,
    get_data_dir,
    get_uploads_dir,
    is_running_under_test,
)
from services.api.repository.sqlite_repository import (
    SqliteAssessmentRepository,
    AssessmentDoc,
    QuestionConfig,
)
from services.api.repository.sqlite_storage import SqliteDatabaseManager


def _calc_file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_is_running_under_test_detection():
    """Confirms is_running_under_test() evaluates to True during pytest execution."""
    assert is_running_under_test() is True


def test_test_environment_never_returns_default_store_or_uploads():
    """Confirms get_data_dir() and get_uploads_dir() never return local-data/store or uploads under test."""
    active_data = get_data_dir()
    active_uploads = get_uploads_dir()

    # Must not match default dev paths
    assert active_data.resolve() != DEFAULT_DATA_DIR.resolve()
    assert active_uploads.resolve() != DEFAULT_UPLOADS_DIR.resolve()


def test_storage_config_diverts_to_temp_if_env_unset_under_test(monkeypatch):
    """Proves that even if CLASSLENS_DATA_DIR is missing, get_data_dir() refuses to touch local-data/store."""
    monkeypatch.delenv("CLASSLENS_DATA_DIR", raising=False)
    monkeypatch.delenv("CLASSLENS_UPLOADS_DIR", raising=False)

    diverted_data = get_data_dir()
    diverted_uploads = get_uploads_dir()

    assert diverted_data.resolve() != DEFAULT_DATA_DIR.resolve()
    assert diverted_uploads.resolve() != DEFAULT_UPLOADS_DIR.resolve()
    assert "classlens" in str(diverted_data).lower() or "tmp" in str(diverted_data).lower() or "fallback" in str(diverted_data).lower()


def test_dev_database_remains_strictly_unchanged():
    """Proves that performing repo operations with SqliteAssessmentRepository does not touch dev DB."""
    dev_db_path = DEFAULT_DATA_DIR / "classlens.db"
    sha_before = _calc_file_sha256(dev_db_path)

    # Perform extensive operations against an isolated repo
    with tempfile.TemporaryDirectory(prefix="test_isolation_verify_") as tmp_dir:
        repo = SqliteAssessmentRepository(data_dir=Path(tmp_dir))
        doc = AssessmentDoc(
            id="asm_test_isolation_check",
            class_id="cls_test",
            organization_id="org_test",
            title="Isolation Verification Assessment",
            is_demo=False,
            question=QuestionConfig(question_text="2 + 2", expected_answer="4"),
        )
        repo.create_assessment(doc)
        assert repo.get_assessment("asm_test_isolation_check") is not None
        assert repo.get_assessment("asm_test_isolation_check").is_demo is False

    # Dev DB SHA-256 must match exactly
    sha_after = _calc_file_sha256(dev_db_path)
    assert sha_before == sha_after, "Development database was modified during testing!"


def test_demo_seeded_metadata_prevents_automatic_recreation():
    """Verifies that app_metadata tracks demo_seeded and prevents auto-recreation of deleted demo assessments."""
    with tempfile.TemporaryDirectory(prefix="test_demo_metadata_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        repo = SqliteAssessmentRepository(data_dir=tmp_path)

        # First run seeds demo data
        assert "asm_1065658" in repo.assessments
        assert repo.db_manager.get_metadata("demo_seeded") == "true"

        # Explicitly remove the demo assessment (e.g. teacher or user deleted it)
        with repo.db_manager.get_connection() as conn:
            conn.execute("DELETE FROM assessments WHERE id = 'asm_1065658'")

        # Re-initialize repo simulating process restart
        repo_restarted = SqliteAssessmentRepository(data_dir=tmp_path)
        assert repo_restarted.db_manager.get_metadata("demo_seeded") == "true"
        # Since demo_seeded is true, it should NOT resurrect the deleted demo record
        assert "asm_1065658" not in repo_restarted.assessments
