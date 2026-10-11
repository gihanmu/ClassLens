"""FastAPI dependencies for authentication and CSRF validation."""

from __future__ import annotations

from typing import Optional
from fastapi import Header, HTTPException, Request, status

from services.api.auth.service import AuthService
from services.api.repository.memory_repo import UserDoc


async def get_current_user(request: Request) -> UserDoc:
    """Extracts and verifies session from __session cookie or Authorization header."""
    token: Optional[str] = request.cookies.get("__session")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No session provided",
        )

    user = AuthService.verify_session_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )

    return user


async def require_csrf(request: Request) -> None:
    """Enforces CSRF protection on mutating HTTP methods.

    Requires custom header 'X-Requested-With: ClassLens'.
    """
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        requested_with = request.headers.get("X-Requested-With")
        if requested_with != "ClassLens":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: Missing or invalid X-Requested-With header",
            )
