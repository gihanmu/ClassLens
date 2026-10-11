"""Authentication API routes."""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from services.api.auth.dependencies import get_current_user
from services.api.auth.service import AuthService
from services.api.config import settings
from services.api.repository.memory_repo import UserDoc

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    credential: Optional[str] = None
    demo_mode: bool = True


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    organization_id: str


class AuthResponse(BaseModel):
    user: UserProfileResponse
    csrf_token: str


@router.post("/google", response_model=AuthResponse)
async def login_google_or_demo(body: Optional[AuthRequest] = None, response: Response = None):
    """Authenticates via Google Identity Services ID token or local sandbox demo user."""
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
        max_age=86400,
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=86400,
    )

    return AuthResponse(
        user=UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
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
        organization_id=user.organization_id,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clears session and CSRF cookies."""
    response.delete_cookie("__session", path="/")
    response.delete_cookie("csrf_token", path="/")
    return {"status": "logged_out"}
