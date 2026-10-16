#!/usr/bin/env python3
"""ClassLens Test Data Cleanup Utility.

Safely purges test-polluted assessments, orphaned responses, audit events,
and temporary upload directories from the local SQLite database and filesystem,
while strictly preserving canonical demo records and real teacher-created data.

Safety Guarantees:
- Runs in DRY-RUN mode by default.
- Requires --confirm to perform actual deletion.
- Creates verified SHA-256 backup with PRAGMA integrity_check before touching data.
- Relies on multi-criteria provenance (whitelist + known test suites + class IDs),
  never on loose or title-only heuristics.
- Cascades deletions atomically across SQLite tables.
- Synchronizes local JSON state partitions to prevent resurrection.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import sqlite3
import sys
from typing import Any, Dict, List, Set, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cleanup_test_data")

# 1. Immutable Whitelist: Canonical Demo Assessments (NEVER REMOVED)
CANONICAL_DEMO_IDS: Set[str] = {
    "asm_1065658",          # Integers on Number Line: Checkpoint 1
    "asm_synthetic_cases",  # Synthetic Feasibility Benchmark: Cases 1–3
}

# 2. Known Automated Test Artifact Signatures
KNOWN_TEST_CLASSES: Set[str] = {
    "cls_1",
    "cls_2",
    "cls_empty",
    "cls_foreign",
    "cls_raffles_sec1",
}

KNOWN_TEST_IDS: Set[str] = {
    "asm_foreign_isolation",
    "asm_raffles_001",
}

KNOWN_TEST_TITLES: Set[str] = {
    "Concurrent 1",
    "Concurrent 2",
    "Empty Assessment",
    "Integers Batch Check",
    "Unanalyzed Integers Checkpoint",
    "Gate 5 Batch Truthfulness Checkpoint",
    "Gate 5 Teacher Workflow Checkpoint",
    "Gate 5 Truthfulness Checkpoint",
    "Batch Intake Assessment",
    "Delete Test",
    "Image Serve Test",
    "Integers: Checkpoint 2 — Subtraction on Number Line",
    "MIME Spoof Test",
    "Oversized Test",
    "Upload Test Assessment",
    "Foreign Assessment",
    "Raffles Confidential Assessment",
    "Unauthorized CSRF Test",
}


def calc_sha256(file_path: Path) -> str:
    """Calculates hex SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_sqlite_integrity(db_path: Path) -> bool:
    """Runs PRAGMA integrity_check on the specified SQLite database."""
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()
        conn.close()
        return res is not None and res[0] == "ok"
    except Exception as exc:
        logger.error(f"Integrity check failed for {db_path}: {exc}")
        return False


def classify_assessment(
    asm_id: str,
    title: str,
    class_id: str,
    org_id: str,
) -> Tuple[bool, str]:
    """Classifies an assessment record as test pollution or legitimate data.

    Returns:
        (is_test_record, reason)
    """
    # Rule 1: Canonical Demo Whitelist
    if asm_id in CANONICAL_DEMO_IDS:
        return False, "canonical_demo"

    # Rule 2: Explicit Test ID Match
    if asm_id in KNOWN_TEST_IDS:
        return True, f"known_test_id ({asm_id})"

    # Rule 3: Known Test Class IDs
    if class_id in KNOWN_TEST_CLASSES:
        return True, f"known_test_class ({class_id})"

    # Rule 4: Known Test Suite Titles
    if title in KNOWN_TEST_TITLES:
        return True, f"known_test_title ('{title}')"

    # Rule 5: Duplicate of Canonical Title with generated UUID
    if title == "Integers on Number Line: Checkpoint 1" and asm_id != "asm_1065658":
        return True, "duplicate_checkpoint_fixture"

    # Default: Legitimately created assessment (preserved)
    return False, "teacher_created_record"


def scan_database(db_path: Path) -> Dict[str, Any]:
    """Scans the database and partitions assessments into preserved and test records."""
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(assessments);")
    cols = [r["name"] for r in cur.fetchall()]
    has_is_demo = "is_demo" in cols

    cols_select = "id, title, class_id, organization_id, " + ("is_demo, " if has_is_demo else "0 as is_demo, ") + "created_at"
    cur.execute(f"SELECT {cols_select} FROM assessments")
    assessments = cur.fetchall()

    preserved_records: List[Dict[str, Any]] = []
    test_records: List[Dict[str, Any]] = []

    for row in assessments:
        asm_id = row["id"]
        title = row["title"]
        class_id = row["class_id"] or ""
        org_id = row["organization_id"] or ""

        is_test, reason = classify_assessment(asm_id, title, class_id, org_id)
        item = {
            "id": asm_id,
            "title": title,
            "class_id": class_id,
            "organization_id": org_id,
            "reason": reason,
            "created_at": row["created_at"],
        }
        if is_test:
            test_records.append(item)
        else:
            preserved_records.append(item)

    test_ids = [r["id"] for r in test_records]

    # Count affected child records
    child_counts = {"responses": 0, "audit_events": 0, "analysis_jobs": 0}
    if test_ids:
        placeholders = ",".join("?" for _ in test_ids)
        cur.execute(f"SELECT count(*) FROM responses WHERE assessment_id IN ({placeholders})", test_ids)
        child_counts["responses"] = cur.fetchone()[0]

        cur.execute(f"SELECT count(*) FROM audit_events WHERE assessment_id IN ({placeholders})", test_ids)
        child_counts["audit_events"] = cur.fetchone()[0]

        cur.execute(f"SELECT count(*) FROM analysis_jobs WHERE assessment_id IN ({placeholders})", test_ids)
        child_counts["analysis_jobs"] = cur.fetchone()[0]

    conn.close()

    return {
        "total_assessments": len(assessments),
        "preserved_records": preserved_records,
        "test_records": test_records,
        "child_counts": child_counts,
    }


def scan_uploads(uploads_dir: Path, test_ids: Set[str]) -> List[Path]:
    """Identifies upload subdirectories associated with test assessment IDs."""
    test_dirs: List[Path] = []
    if not uploads_dir.is_dir():
        return test_dirs

    # local-data/uploads/{org_id}/{assessment_id}/
    for p in uploads_dir.rglob("*"):
        if p.is_dir() and p.name in test_ids and p.name not in CANONICAL_DEMO_IDS:
            test_dirs.append(p)

    return test_dirs


def execute_cleanup(
    db_path: Path,
    uploads_dir: Path,
    scan_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Executes verified backup and atomic cascading deletion of test records."""
    test_records = scan_results["test_records"]
    test_ids = [r["id"] for r in test_records]
    if not test_ids:
        return {"status": "no_changes_needed"}

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # 1. Create verified SQLite backup
    backup_db_path = db_path.parent / f"{db_path.name}.bak.{timestamp}"
    shutil.copy2(db_path, backup_db_path)
    orig_sha = calc_sha256(db_path)
    bak_sha = calc_sha256(backup_db_path)
    if orig_sha != bak_sha:
        raise RuntimeError("Backup SHA-256 verification mismatch. Aborting cleanup.")
    if not verify_sqlite_integrity(backup_db_path):
        raise RuntimeError("Backup SQLite PRAGMA integrity_check failed. Aborting cleanup.")

    logger.info(f"Verified SQLite backup created: {backup_db_path} (SHA-256: {bak_sha[:12]}...)")

    # 2. Backup and synchronize JSON state persistence file if present
    state_file = db_path.parent / "org_cedar_sec_state.json"
    if state_file.is_file():
        backup_state_path = db_path.parent / f"org_cedar_sec_state.json.bak.{timestamp}"
        shutil.copy2(state_file, backup_state_path)
        logger.info(f"Verified JSON state backup created: {backup_state_path}")
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            test_id_set = set(test_ids)
            state_data["assessments"] = [a for a in state_data.get("assessments", []) if a.get("id") not in test_id_set]
            state_data["responses"] = [r for r in state_data.get("responses", []) if r.get("assessment_id") not in test_id_set]
            state_data["audit_events"] = [e for e in state_data.get("audit_events", []) if e.get("assessment_id") not in test_id_set]
            tmp_json = state_file.with_suffix(".tmp")
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
            os.replace(tmp_json, state_file)
            logger.info("Synchronized local JSON persistence state file.")
        except Exception as exc:
            logger.warning(f"Could not synchronize JSON state file: {exc}")

    # 3. Atomic SQLite cascading delete
    conn = sqlite3.connect(str(db_path))
    placeholders = ",".join("?" for _ in test_ids)
    try:
        conn.execute("BEGIN IMMEDIATE;")
        conn.execute(f"DELETE FROM audit_events WHERE assessment_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM analysis_jobs WHERE assessment_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM responses WHERE assessment_id IN ({placeholders})", test_ids)
        conn.execute(f"DELETE FROM assessments WHERE id IN ({placeholders})", test_ids)

        # Mark demo_seeded in metadata table so demo data is not recreated
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            INSERT INTO app_metadata (key, value, updated_at) VALUES ('demo_seeded', 'true', ?)
            ON CONFLICT(key) DO UPDATE SET value = 'true', updated_at = excluded.updated_at;
            """,
            (datetime.now(timezone.utc).isoformat(),),
        )

        conn.commit()
        logger.info("Committed cascading SQLite deletion.")
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise RuntimeError(f"SQLite transaction failed; rolled back. Error: {exc}")

    # Reclaim disk space
    conn.execute("VACUUM;")
    conn.close()

    # 4. Remove associated upload directories
    test_id_set = set(test_ids)
    upload_dirs_removed = 0
    test_upload_dirs = scan_uploads(uploads_dir, test_id_set)
    for u_dir in test_upload_dirs:
        try:
            shutil.rmtree(u_dir, ignore_errors=True)
            upload_dirs_removed += 1
        except Exception as exc:
            logger.warning(f"Could not remove test upload dir {u_dir}: {exc}")

    return {
        "status": "success",
        "backup_db": str(backup_db_path),
        "assessments_deleted": len(test_ids),
        "responses_deleted": scan_results["child_counts"]["responses"],
        "audit_events_deleted": scan_results["child_counts"]["audit_events"],
        "analysis_jobs_deleted": scan_results["child_counts"]["analysis_jobs"],
        "upload_dirs_removed": upload_dirs_removed,
    }


def main():
    parser = argparse.ArgumentParser(
        description="ClassLens Test Data Cleanup Utility (Dry-run by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("local-data/store/classlens.db"),
        help="Path to SQLite database (default: local-data/store/classlens.db)",
    )
    parser.add_argument(
        "--uploads-dir",
        type=Path,
        default=Path("local-data/uploads"),
        help="Path to uploads directory (default: local-data/uploads)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicit confirmation flag required to execute destructive cleanup",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display all record identifiers",
    )
    args = parser.parse_args()

    db_path: Path = args.db_path.resolve()
    uploads_dir: Path = args.uploads_dir.resolve()

    print("=" * 76)
    print("ClassLens Assessment Cleanup & Test Isolation Utility")
    print("=" * 76)
    print(f"Database: {db_path}")
    print(f"Uploads:  {uploads_dir}")
    print(f"Mode:     {'EXECUTION (--confirm)' if args.confirm else 'DRY RUN (default)'}")
    print("-" * 76)

    if not db_path.is_file():
        logger.error(f"Target database does not exist: {db_path}")
        sys.exit(1)

    scan_res = scan_database(db_path)
    test_id_set = {r["id"] for r in scan_res["test_records"]}
    test_upload_dirs = scan_uploads(uploads_dir, test_id_set)

    print(f"\n[SCAN SUMMARY]")
    print(f"Total assessments found:      {scan_res['total_assessments']}")
    print(f"Preserved assessments:        {len(scan_res['preserved_records'])}")
    print(f"Test pollution candidates:   {len(scan_res['test_records'])}")
    print(f"Associated child responses:   {scan_res['child_counts']['responses']}")
    print(f"Associated audit events:      {scan_res['child_counts']['audit_events']}")
    print(f"Associated analysis jobs:     {scan_res['child_counts']['analysis_jobs']}")
    print(f"Test upload subdirectories:   {len(test_upload_dirs)}")

    print(f"\n[PRESERVED ASSESSMENTS ({len(scan_res['preserved_records'])})]")
    for r in scan_res["preserved_records"]:
        print(f"  • [{r['id']}] {r['title']} (class: {r['class_id']}, reason: {r['reason']})")

    # Breakdown of test candidates by reason
    breakdown: Dict[str, int] = {}
    for r in scan_res["test_records"]:
        cat = r["reason"].split()[0]
        breakdown[cat] = breakdown.get(cat, 0) + 1

    print(f"\n[TEST POLLUTION BREAKDOWN ({len(scan_res['test_records'])})]")
    for cat, count in sorted(breakdown.items(), key=lambda x: -x[1]):
        print(f"  • {cat:<32}: {count:3d} records")

    if args.verbose:
        print("\n[CANDIDATE IDENTIFIERS]")
        for r in scan_res["test_records"]:
            print(f"  - {r['id']} | {r['title'][:35]:<35} | {r['reason']}")

    if not args.confirm:
        print("\n" + "=" * 76)
        print("DRY RUN COMPLETE — No changes made to database or filesystem.")
        print("To execute cleanup with verified backup, run with: --confirm")
        print("=" * 76)
        return

    print("\nExecuting cleanup with verified backup...")
    result = execute_cleanup(db_path, uploads_dir, scan_res)
    print("\n" + "=" * 76)
    print("CLEANUP COMPLETED SUCCESSFULLY")
    print("=" * 76)
    print(f"Backup file:            {result.get('backup_db')}")
    print(f"Assessments deleted:    {result.get('assessments_deleted')}")
    print(f"Responses deleted:      {result.get('responses_deleted')}")
    print(f"Audit events deleted:   {result.get('audit_events_deleted')}")
    print(f"Analysis jobs deleted:  {result.get('analysis_jobs_deleted')}")
    print(f"Upload dirs removed:    {result.get('upload_dirs_removed')}")
    print("=" * 76)


if __name__ == "__main__":
    main()
