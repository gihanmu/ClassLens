"""Centralized storage and uploads directory configuration for ClassLens.

Provides deterministic resolution of local SQLite database directories and
uploaded worksheet directories, with fail-safe isolation guards during automated testing.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path("local-data/store")
DEFAULT_UPLOADS_DIR = Path("local-data/uploads")

# Cached test fallback directory for test execution when no environment variable was explicitly set
_TEST_FALLBACK_DIR: Path | None = None


def is_running_under_test() -> bool:
    """Returns True if the current process is executing within a pytest or unittest session."""
    return (
        "pytest" in sys.modules
        or os.environ.get("PYTEST_CURRENT_TEST") is not None
        or "unittest" in sys.modules and any("test" in arg.lower() for arg in sys.argv)
    )


def get_data_dir() -> Path:
    """Resolves the active data directory for SQLite database storage.

    Safety Guarantee:
    If executing under automated tests and no explicit CLASSLENS_DATA_DIR was set,
    this function will NEVER return the production/development 'local-data/store' path.
    Instead, it safely diverts to an isolated temporary directory to prevent database pollution.
    """
    global _TEST_FALLBACK_DIR
    env_dir = os.environ.get("CLASSLENS_DATA_DIR")
    if env_dir:
        resolved = Path(env_dir)
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    if is_running_under_test():
        if _TEST_FALLBACK_DIR is None:
            _TEST_FALLBACK_DIR = Path(tempfile.mkdtemp(prefix="classlens_pytest_fallback_"))
            logger.warning(
                "Running under test without CLASSLENS_DATA_DIR. Diverting database to isolated fallback: %s",
                _TEST_FALLBACK_DIR,
            )
        _TEST_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        return _TEST_FALLBACK_DIR

    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DATA_DIR


def get_uploads_dir() -> Path:
    """Resolves the active storage directory for uploaded handwritten worksheets.

    Safety Guarantee:
    Follows CLASSLENS_UPLOADS_DIR if set, or (get_data_dir() / "uploads") if under test,
    preventing any test uploads from escaping into the local development uploads folder.
    """
    env_uploads = os.environ.get("CLASSLENS_UPLOADS_DIR")
    if env_uploads:
        resolved = Path(env_uploads)
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    if is_running_under_test():
        test_dir = get_data_dir() / "uploads"
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir

    DEFAULT_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_UPLOADS_DIR
