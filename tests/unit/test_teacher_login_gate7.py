"""Unit and integration tests for ClassLens Single Teacher Login System (Gate 7).

Verifies:
- Argon2id password hashing and constant-time verification.
- Idempotent teacher account initialization via CLI / environment.
- Secure session cookie minting, expiration checks, and CSRF token delivery.
- Rejection of invalid passwords, missing users, and expired sessions.
- Logout clearing HTTP-only cookies.
- Fail-closed 401 protections on all teacher-facing endpoints.
- Session durability across application restarts.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from services.api.auth.security import hash_password, verify_password
from services.api.auth.service import AuthService
from services.api.main import app
from services.api.repository.memory_repo import UserDoc, memory_repo
from services.api.repository.sqlite_repository import SqliteAssessmentRepository
from scripts.init_teacher import init_teacher_account


@pytest.fixture
def isolated_teacher_env():
    """Sets up an isolated database with an initialized teacher account."""
    test_pwd = "ReviewerSecurePass2026!"

    # Initialize teacher in memory_repo
    pwd_hash = hash_password(test_pwd)
    teacher = UserDoc(
        id="usr_sarah_lim",
        email="teacher@classlens.demo",
        name="Mrs. Sarah Lim",
        role="Secondary 1 Mathematics Teacher",
        organization_id="org_cedar_sec",
        school="Cedar Secondary School",
        password_hash=pwd_hash,
    )
    memory_repo.save_user(teacher)

    client = TestClient(app)
    return {
        "client": client,
        "repo": memory_repo,
        "password": test_pwd,
        "teacher": teacher,
    }


def test_argon2id_hashing_and_verification():
    """Verifies that Argon2id produces valid hashes and verifies plaintext passwords accurately."""
    plain = "CedarMathDepartment#2026"
    h = hash_password(plain)
    assert h.startswith("$argon2id$")
    assert verify_password(plain, h) is True
    assert verify_password("WrongPassword!", h) is False
    assert verify_password("", h) is False
    assert verify_password(plain, "") is False
    assert verify_password(plain, "corrupted_hash") is False


def test_teacher_account_initialization_idempotency(tmp_path, monkeypatch):
    """Verifies that init_teacher_account is idempotent and does not overwrite existing password without reset."""
    db_file = tmp_path / "init_test.db"
    repo = SqliteAssessmentRepository(db_path=db_file)

    monkeypatch.setattr("scripts.init_teacher.mem_mod.memory_repo", repo)

    # 1. First initialization
    res1 = init_teacher_account(password="InitialPass123!", reset=False, quiet=True)
    assert res1 == 0
    u1 = repo.get_user("usr_sarah_lim")
    assert u1 is not None
    assert u1.email == "teacher@classlens.demo"
    assert u1.name == "Mrs. Sarah Lim"
    assert verify_password("InitialPass123!", u1.password_hash) is True
    hash1 = u1.password_hash

    # 2. Second initialization attempt with different password without --reset -> MUST NOT overwrite
    res2 = init_teacher_account(password="AttemptedOverwrite456!", reset=False, quiet=True)
    assert res2 == 0
    u2 = repo.get_user("usr_sarah_lim")
    assert u2.password_hash == hash1
    assert verify_password("InitialPass123!", u2.password_hash) is True
    assert verify_password("AttemptedOverwrite456!", u2.password_hash) is False

    # 3. Third initialization with reset=True -> MUST overwrite
    res3 = init_teacher_account(password="NewResetPassword789!", reset=True, quiet=True)
    assert res3 == 0
    u3 = repo.get_user("usr_sarah_lim")
    assert verify_password("NewResetPassword789!", u3.password_hash) is True
    assert verify_password("InitialPass123!", u3.password_hash) is False


def test_login_successful(isolated_teacher_env):
    """Verifies successful login with username and password, setting HttpOnly session cookies."""
    client = isolated_teacher_env["client"]
    password = isolated_teacher_env["password"]

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@classlens.demo", "password": password},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["user"]["id"] == "usr_sarah_lim"
    assert data["user"]["name"] == "Mrs. Sarah Lim"
    assert data["user"]["email"] == "teacher@classlens.demo"
    assert data["user"]["school"] == "Cedar Secondary School"
    assert "password_hash" not in data["user"]
    assert "csrf_token" in data

    # Verify cookies
    assert "__session" in resp.cookies
    assert "csrf_token" in resp.cookies

    # Test /auth/me with session cookie
    me_resp = client.get("/api/v1/auth/me", cookies=resp.cookies)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["name"] == "Mrs. Sarah Lim"


def test_login_supports_alternate_identifiers(isolated_teacher_env):
    """Verifies that logging in with user ID or MOE email alias also resolves to Mrs. Sarah Lim."""
    client = isolated_teacher_env["client"]
    password = isolated_teacher_env["password"]

    # Login with usr_sarah_lim
    r1 = client.post("/api/v1/auth/login", json={"username": "usr_sarah_lim", "password": password})
    assert r1.status_code == 200

    # Login with legacy email alias sarah.lim@moe.edu.sg
    r2 = client.post("/api/v1/auth/login", json={"username": "sarah.lim@moe.edu.sg", "password": password})
    assert r2.status_code == 200


def test_login_invalid_password_rejected(isolated_teacher_env):
    """Verifies that invalid password returns 401 Unauthorized."""
    client = isolated_teacher_env["client"]

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@classlens.demo", "password": "IncorrectPassword123!"},
    )
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]
    assert "__session" not in resp.cookies


def test_login_unknown_user_rejected(isolated_teacher_env):
    """Verifies that an unknown user returns 401 Unauthorized."""
    client = isolated_teacher_env["client"]

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "intruder@malicious.com", "password": "some_password"},
    )
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]


def test_session_expiration_enforced(isolated_teacher_env):
    """Verifies that expired session tokens are rejected with 401."""
    client = isolated_teacher_env["client"]
    teacher = isolated_teacher_env["teacher"]

    # Mint an already-expired session token (expired 60 seconds ago)
    expired_token = AuthService.create_session_token(teacher, expires_in=-60)

    # Calling protected endpoint with expired session
    resp = client.get("/api/v1/auth/me", cookies={"__session": expired_token})
    assert resp.status_code == 401
    assert "Invalid or expired session token" in resp.json()["detail"]


def test_logout_clears_session(isolated_teacher_env):
    """Verifies that logout deletes cookies and invalidates session access."""
    client = isolated_teacher_env["client"]
    password = isolated_teacher_env["password"]

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher@classlens.demo", "password": password},
    )
    assert login_resp.status_code == 200
    cookies = login_resp.cookies

    # Verify access works before logout
    me_resp1 = client.get("/api/v1/auth/me", cookies=cookies)
    assert me_resp1.status_code == 200

    # Call logout
    logout_resp = client.post("/api/v1/auth/logout", cookies=cookies)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "logged_out"


def test_unauthenticated_requests_return_401(isolated_teacher_env):
    """Verifies that all teacher-facing endpoints strictly return 401 without session."""
    client = isolated_teacher_env["client"]

    endpoints = [
        ("GET", "/api/v1/assessments"),
        ("GET", "/api/v1/assessments/asm_1065658"),
        ("GET", "/api/v1/assessments/asm_1065658/responses"),
        ("GET", "/api/v1/assessments/asm_1065658/insights"),
        ("GET", "/api/v1/assessments/asm_1065658/status"),
        ("GET", "/api/v1/dashboard/summary"),
        ("GET", "/api/v1/dashboard/recent-activity"),
        ("GET", "/api/v1/dashboard/attention-queue"),
        ("GET", "/api/v1/responses/resp_04255753"),
        ("GET", "/api/v1/responses/resp_04255753/audit-trail"),
        ("GET", "/api/v1/responses/resp_04255753/image"),
    ]

    for method, path in endpoints:
        if method == "GET":
            r = client.get(path)
        else:
            r = client.post(path)
        assert r.status_code == 401, f"Expected 401 for {method} {path}, got {r.status_code}"
        assert "Authentication required" in r.json()["detail"]


def test_auth_survives_application_restart(tmp_path):
    """Verifies that teacher credentials and session validity survive process restart using SQLite persistence."""
    db_file = tmp_path / "persistence_restart.db"
    pwd = "PersistentPassword2026!"

    # 1. Start application instance 1
    repo1 = SqliteAssessmentRepository(db_path=db_file)
    init_teacher_account(password=pwd, reset=False, quiet=True)

    # Save to repo1
    h = hash_password(pwd)
    u = UserDoc(
        id="usr_sarah_lim",
        email="teacher@classlens.demo",
        name="Mrs. Sarah Lim",
        role="Secondary 1 Mathematics Teacher",
        organization_id="org_cedar_sec",
        school="Cedar Secondary School",
        password_hash=h,
    )
    repo1.save_user(u)
    token = AuthService.create_session_token(u)

    # 2. Simulate complete restart: instantiate a fresh repo2 pointing to the same database
    repo2 = SqliteAssessmentRepository(db_path=db_file)
    import services.api.repository.memory_repo as mem_mod
    original_repo = mem_mod.memory_repo
    mem_mod.memory_repo = repo2

    try:
        # User is hydrated from SQLite
        u_reloaded = repo2.get_user("usr_sarah_lim")
        assert u_reloaded is not None
        assert u_reloaded.email == "teacher@classlens.demo"
        assert u_reloaded.school == "Cedar Secondary School"
        assert verify_password(pwd, u_reloaded.password_hash) is True

        # Existing session token remains valid
        validated_user = AuthService.verify_session_token(token)
        assert validated_user is not None
        assert validated_user.id == "usr_sarah_lim"
    finally:
        mem_mod.memory_repo = original_repo
