"""Authentication API routes for teacher login, session management, and logout."""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from services.api.auth.dependencies import get_current_user
from services.api.auth.service import AuthService
from services.api.config import settings
from services.api.repository.memory_repo import UserDoc

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: Optional[str] = Field(default=None, description="Teacher username or email (e.g. teacher@classlens.demo)")
    email: Optional[str] = Field(default=None, description="Optional alias for username")
    password: str = Field(..., description="Teacher password")

    def resolved_username(self) -> str:
        return (self.username or self.email or "").strip()


class AuthRequest(BaseModel):
    credential: Optional[str] = None
    demo_mode: bool = True


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    school: str = "Cedar Secondary School"
    organization_id: str


class AuthResponse(BaseModel):
    user: UserProfileResponse
    csrf_token: str


import time
from collections import defaultdict


class LoginRateLimiter:
    """Sliding-window in-memory rate limiter for login attempts."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: Dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
        return len(self.attempts[key]) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        self.attempts[key].append(time.time())

    def reset(self, key: str) -> None:
        self.attempts.pop(key, None)


login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=60)


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, body: LoginRequest, response: Response):
    """Authenticates the teacher account using Argon2id password verification."""
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host
    uname = body.resolved_username()
    rate_key = f"{client_ip or 'unknown'}:{uname.lower()}"

    if login_rate_limiter.is_rate_limited(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 60 seconds before trying again.",
        )

    try:
        user, session_token, csrf_token = AuthService.authenticate_teacher(
            username=uname,
            password=body.password,
        )
    except ValueError as exc:
        login_rate_limiter.record_failure(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    login_rate_limiter.reset(rate_key)

    is_prod = settings.environment == "production"
    response.set_cookie(
        key="__session",
        value=session_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=settings.session_max_age_seconds,
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=settings.session_max_age_seconds,
    )

    return AuthResponse(
        user=UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            school=user.school or "Cedar Secondary School",
            organization_id=user.organization_id,
        ),
        csrf_token=csrf_token,
    )


@router.post("/google", response_model=AuthResponse)
async def login_google_or_demo(body: Optional[AuthRequest] = None, response: Response = None):
    """Authenticates via Google Identity Services ID token or local sandbox demo user (legacy compatibility)."""
    credential = body.credential if body else None
    demo_mode = body.demo_mode if body else True

    try:
        user, session_token, csrf_token = AuthService.authenticate_demo_or_google(
            credential=credential,
            demo_mode=demo_mode,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    # Set HttpOnly session cookie and accessible CSRF cookie
    is_prod = settings.environment == "production"
    response.set_cookie(
        key="__session",
        value=session_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=settings.session_max_age_seconds,
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=settings.session_max_age_seconds,
    )

    return AuthResponse(
        user=UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            school=user.school or "Cedar Secondary School",
            organization_id=user.organization_id,
        ),
        csrf_token=csrf_token,
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(user: UserDoc = Depends(get_current_user)):
    """Returns the authenticated user profile."""
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        school=user.school or "Cedar Secondary School",
        organization_id=user.organization_id,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clears session and CSRF cookies."""
    response.delete_cookie("__session", path="/", samesite="lax")
    response.delete_cookie("csrf_token", path="/", samesite="lax")
    return {"status": "logged_out"}
