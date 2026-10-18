#!/usr/bin/env python3
"""ClassLens Database Migration Engine & Verification Utility.

Provides:
- Idempotent, non-destructive migration execution for both SQLite and PostgreSQL.
- Schema verification and table presence auditing.
- Explicit safety controls: NEVER drops tables or columns.
- Support for dry-run inspection (--dry-run) and health verification (--verify).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Auto-bootstrap project virtual environment if dependencies are not installed in active interpreter
try:
    import dotenv  # noqa: F401
except ImportError:
    venv_py = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_py.is_file() and os.access(venv_py, os.X_OK) and Path(sys.executable).resolve() != venv_py.resolve():
        os.execv(str(venv_py), [str(venv_py)] + sys.argv)

from services.api.config import load_project_env, settings
from services.api.repository.storage_config import get_data_dir

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("classlens.migrate")

SCHEMA_VERSION = "1.0.0"
EXPECTED_TABLES = [
    "users",
    "classes",
    "students",
    "assessments",
    "responses",
    "audit_events",
    "analysis_jobs",
    "app_metadata",
]


def get_active_manager():
    """Instantiates the database manager based on active configuration."""
    db_url = os.getenv("CLASSLENS_DATABASE_URL")
    if db_url and (db_url.startswith("postgres://") or db_url.startswith("postgresql://")):
        logger.info("Using PostgreSQL Database Manager with Cloud SQL / connection string.")
        from services.api.repository.postgres_storage import PostgresDatabaseManager
        return PostgresDatabaseManager(db_url), "postgresql"
    else:
        db_path = get_data_dir() / "classlens.db"
        logger.info(f"Using SQLite Database Manager: {db_path}")
        from services.api.repository.sqlite_storage import SqliteDatabaseManager
        return SqliteDatabaseManager(db_path), "sqlite"


def verify_schema(manager, db_type: str) -> bool:
    """Verifies that all expected tables exist in the target database."""
    logger.info(f"Auditing schema integrity for {db_type} database...")
    found_tables = set()

    with manager.get_connection() as conn:
        if db_type == "sqlite":
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            found_tables = {row[0] for row in cur.fetchall()}
        else:
            cur = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
            )
            found_tables = {row[0] for row in cur.fetchall()}

    missing = [t for t in EXPECTED_TABLES if t not in found_tables]
    if missing:
        logger.error(f"Schema verification FAILED. Missing tables: {missing}")
        return False

    current_ver = manager.get_metadata("schema_version")
    logger.info(f"Schema verification PASSED. All {len(EXPECTED_TABLES)} required tables exist. Version: {current_ver or 'initial'}")
    return True


def run_migrations(dry_run: bool = False, verify_only: bool = False) -> int:
    """Runs database migrations idempotently."""
    load_project_env()

    try:
        manager, db_type = get_active_manager()
    except Exception as exc:
        logger.error(f"Failed to connect to database: {exc}")
        return 1

    if verify_only:
        return 0 if verify_schema(manager, db_type) else 1

    if dry_run:
        logger.info(f"[DRY-RUN] Target database type: {db_type}")
        logger.info(f"[DRY-RUN] Target schema version: {SCHEMA_VERSION}")
        logger.info(f"[DRY-RUN] DDL statements to apply: {len(manager.DDL_STATEMENTS)} statements")
        verify_schema(manager, db_type)
        logger.info("[DRY-RUN] Dry run complete. No modifications applied.")
        return 0

    logger.info(f"Applying idempotent schema migrations to {db_type} database...")
    try:
        manager._init_db()
        manager.set_metadata("schema_version", SCHEMA_VERSION)
        manager.set_metadata("migrated_at", manager.get_metadata("updated_at") or "now")
        logger.info(f"Schema migration to version {SCHEMA_VERSION} completed successfully.")
    except Exception as exc:
        logger.error(f"Migration execution failed: {exc}")
        return 1

    # Verify newly applied schema
    if not verify_schema(manager, db_type):
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(description="ClassLens Database Migration Engine")
    parser.add_argument("--dry-run", action="store_true", help="Preview migrations without applying")
    parser.add_argument("--verify", action="store_true", help="Audit schema integrity and table existence")
    args = parser.parse_args()

    exit_code = run_migrations(dry_run=args.dry_run, verify_only=args.verify)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
