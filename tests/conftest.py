"""Pytest configuration ensuring workspace root is on Python path and test data isolation."""

import os
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Fail-safe test data isolation: Guarantee test runs NEVER touch local-data/store or local-data/uploads
_TEST_TEMP_ROOT = tempfile.mkdtemp(prefix="classlens_pytest_session_")
_TEST_DATA_DIR = os.path.join(_TEST_TEMP_ROOT, "store")
_TEST_UPLOADS_DIR = os.path.join(_TEST_TEMP_ROOT, "uploads")
os.makedirs(_TEST_DATA_DIR, exist_ok=True)
os.makedirs(_TEST_UPLOADS_DIR, exist_ok=True)

os.environ["CLASSLENS_DATA_DIR"] = _TEST_DATA_DIR
os.environ["CLASSLENS_UPLOADS_DIR"] = _TEST_UPLOADS_DIR


@pytest.fixture(scope="session", autouse=True)
def ensure_test_session_isolation():
    """Session fixture ensuring isolated database and uploads cleanup."""
    yield _TEST_TEMP_ROOT
    try:
        shutil.rmtree(_TEST_TEMP_ROOT, ignore_errors=True)
    except Exception:
        pass
