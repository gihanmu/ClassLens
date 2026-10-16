#!/usr/bin/env python3
"""ClassLens Default Teacher Account Initialization & Reset Utility.

Creates or updates the default teacher account:
- Display Name: Mrs. Sarah Lim
- School: Cedar Secondary School
- Role: Secondary 1 Mathematics Teacher
- Username: teacher@classlens.demo
- Password: Configured via CLASSLENS_DEMO_PASSWORD environment variable or --password CLI flag

Security & Idempotency:
- Uses Argon2id password hashing.
- Idempotent: Does NOT overwrite an existing password unless --reset or --force is explicitly provided.
- Does NOT print or log passwords in plaintext.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api.auth.security import hash_password
from services.api.config import load_project_env, settings
from services.api.repository.memory_repo import UserDoc, utc_now
import services.api.repository.memory_repo as mem_mod


def init_teacher_account(
    password: str | None = None,
    reset: bool = False,
    quiet: bool = False,
) -> int:
    """Initializes or resets the default teacher account.

    Args:
        password: Plaintext password. If None, reads from CLASSLENS_DEMO_PASSWORD.
        reset: If True, allows updating an existing password.
        quiet: If True, suppresses output on success.

    Returns:
        0 on success, 1 on error.
    """
    load_project_env()

    teacher_id = "usr_sarah_lim"
    teacher_email = "teacher@classlens.demo"
    teacher_name = "Mrs. Sarah Lim"
    teacher_role = "Secondary 1 Mathematics Teacher"
    teacher_school = "Cedar Secondary School"
    org_id = "org_cedar_sec"

    # Check existing record
    existing_user = mem_mod.memory_repo.get_user(teacher_id) or mem_mod.memory_repo.get_user_by_identifier(teacher_email)

    if existing_user and existing_user.password_hash and not reset:
        if not quiet:
            print(
                f"[INFO] Default teacher account '{teacher_email}' ({teacher_name}, {teacher_school}) "
                f"is already initialized with an active password.\n"
                f"       Account initialization is idempotent. Existing password was not modified.\n"
                f"       To update the password, run with '--reset' or '--force'."
            )
        return 0

    # Resolve password
    resolved_pwd = password or os.getenv("CLASSLENS_DEMO_PASSWORD")
    if not resolved_pwd or not resolved_pwd.strip():
        print(
            "[ERROR] Missing password: CLASSLENS_DEMO_PASSWORD environment variable is not set and no --password argument was provided.\n"
            "        Please set CLASSLENS_DEMO_PASSWORD in your .env file or run:\n"
            "        python scripts/init_teacher.py --password <your_password>",
            file=sys.stderr,
        )
        return 1

    resolved_pwd = resolved_pwd.strip()
    if len(resolved_pwd) < 6:
        print("[ERROR] Password must be at least 6 characters long.", file=sys.stderr)
        return 1

    # Generate Argon2id hash
    pwd_hash = hash_password(resolved_pwd)

    user = UserDoc(
        id=teacher_id,
        email=teacher_email,
        name=teacher_name,
        role=teacher_role,
        organization_id=org_id,
        school=teacher_school,
        password_hash=pwd_hash,
        created_at=existing_user.created_at if (existing_user and existing_user.created_at) else utc_now(),
    )

    mem_mod.memory_repo.save_user(user)

    action_label = "updated" if (existing_user and existing_user.password_hash) else "initialized"
    if not quiet:
        print(
            f"[SUCCESS] Default teacher account '{teacher_email}' successfully {action_label}.\n"
            f"          Teacher:  {teacher_name}\n"
            f"          School:   {teacher_school}\n"
            f"          Role:     {teacher_role}\n"
            f"          Username: {teacher_email}\n"
            f"          Security: Argon2id password hash persisted to SQLite ({mem_mod.memory_repo.db_path.name})"
        )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ClassLens Default Teacher Account Initialization Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--password",
        "-p",
        type=str,
        default=None,
        help="Plaintext password for the teacher account (defaults to CLASSLENS_DEMO_PASSWORD env var)",
    )
    parser.add_argument(
        "--reset",
        "--force",
        "-f",
        action="store_true",
        help="Force overwrite/reset of an existing password if the account already has one",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-error output",
    )

    args = parser.parse_args()
    sys.exit(init_teacher_account(password=args.password, reset=args.reset, quiet=args.quiet))


if __name__ == "__main__":
    main()
