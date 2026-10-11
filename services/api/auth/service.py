"""Authentication service for session management and demo login."""

from __future__ import annotations

import hmac
import hashlib
import json
import secrets
import time
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel

from services.api.config import settings
from services.api.repository.memory_repo import UserDoc, memory_repo


class SessionData(BaseModel):
    user_id: str
    organization_id: str
    role: str
    created_at: float


class AuthService:
    """Manages session tokens, CSRF tokens, and local demo authentication."""

    @staticmethod
    def generate_csrf_token() -> str:
        """Generates a cryptographically secure CSRF token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_session_token(user: UserDoc) -> str:
        """Mints a signed session token encoding user and organization claims."""
        payload = {
            "sub": user.id,
            "org": user.organization_id,
            "role": user.role,
            "iat": time.time(),
        }
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            settings.secret_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        token = f"{payload_bytes.hex()}.{signature}"
        return token

    @staticmethod
    def verify_session_token(token: str) -> Optional[UserDoc]:
        """Validates a signed session token and returns the corresponding UserDoc."""
        if not token or "." not in token:
            return None

        try:
            payload_hex, signature = token.split(".", 1)
            payload_bytes = bytes.fromhex(payload_hex)
            expected_sig = hmac.new(
                settings.secret_key.encode("utf-8"),
                payload_bytes,
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                return None

            payload = json.loads(payload_bytes.decode("utf-8"))
            user_id = payload.get("sub")
            if not user_id:
                return None

            user = memory_repo.get_user(user_id)
            return user
        except Exception:
            return None

    @classmethod
    def authenticate_demo_or_google(
        cls,
        credential: Optional[str] = None,
        demo_mode: bool = True,
    ) -> Tuple[UserDoc, str, str]:
        """Authenticates either via local sandbox demo user or mock GIS credential.

        Returns:
            Tuple of (UserDoc, session_token, csrf_token)
        """
        # Security Guardrail: Demo authentication is strictly forbidden in production
        if settings.environment == "production" and (demo_mode or not credential):
            raise PermissionError("Demo mode authentication is strictly prohibited in production mode")

        # In offline/development mode, authenticate Sarah Lim
        user = memory_repo.get_user(settings.demo_user_id)
        if not user:
            user = UserDoc(
                id=settings.demo_user_id,
                email=settings.demo_user_email,
                name=settings.demo_user_name,
                role=settings.demo_user_role,
                organization_id=settings.default_org_id,
            )
            memory_repo.users[user.id] = user

        session_token = cls.create_session_token(user)
        csrf_token = cls.generate_csrf_token()
        return user, session_token, csrf_token
