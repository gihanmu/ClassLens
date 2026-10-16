"""Authentication service for session management, teacher login, and security tokens."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel

from services.api.auth.security import hash_password, verify_password
from services.api.config import settings
from services.api.repository.memory_repo import UserDoc
import services.api.repository.memory_repo as mem_mod


class SessionData(BaseModel):
    user_id: str
    organization_id: str
    role: str
    created_at: float
    expires_at: float


class AuthService:
    """Manages session tokens, CSRF tokens, Argon2id verification, and teacher authentication."""

    @staticmethod
    def generate_csrf_token() -> str:
        """Generates a cryptographically secure CSRF token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_session_token(user: UserDoc, expires_in: Optional[int] = None) -> str:
        """Mints a signed session token encoding user and organization claims with expiration."""
        now = time.time()
        lifetime = expires_in if expires_in is not None else settings.session_max_age_seconds
        payload = {
            "sub": user.id,
            "org": user.organization_id,
            "role": user.role,
            "iat": now,
            "exp": now + lifetime,
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
        """Validates a signed session token, checks expiration, and returns UserDoc."""
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

            # Check session expiration
            exp = payload.get("exp")
            if exp is not None and time.time() > float(exp):
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            user = mem_mod.memory_repo.get_user(user_id)
            return user
        except Exception:
            return None

    @classmethod
    def authenticate_teacher(
        cls,
        username: str,
        password: str,
    ) -> Tuple[UserDoc, str, str]:
        """Authenticates the teacher account via username/email and Argon2id password.

        Returns:
            Tuple of (UserDoc, session_token, csrf_token)
        Raises:
            ValueError if authentication fails.
        """
        if not username or not password:
            raise ValueError("Username and password are required")

        user = mem_mod.memory_repo.get_user_by_identifier(username)
        if not user:
            raise ValueError("Invalid username or password")

        if not user.password_hash:
            raise ValueError("Invalid username or password: account has no password configured")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password")

        session_token = cls.create_session_token(user)
        csrf_token = cls.generate_csrf_token()
        return user, session_token, csrf_token

    @classmethod
    def authenticate_demo_or_google(
        cls,
        credential: Optional[str] = None,
        demo_mode: bool = True,
    ) -> Tuple[UserDoc, str, str]:
        """Authenticates either via local sandbox demo user or mock GIS credential (for backward compatibility).

        Returns:
            Tuple of (UserDoc, session_token, csrf_token)
        """
        # Security Guardrail: Demo authentication is strictly forbidden in production
        if settings.environment == "production" and (demo_mode or not credential):
            raise PermissionError("Demo mode authentication is strictly prohibited in production mode")

        # In offline/development mode, authenticate Sarah Lim
        user = mem_mod.memory_repo.get_user(settings.demo_user_id)
        if not user:
            user = UserDoc(
                id=settings.demo_user_id,
                email=settings.demo_user_email,
                name=settings.demo_user_name,
                role=settings.demo_user_role,
                school=settings.demo_user_school,
                organization_id=settings.default_org_id,
            )
            mem_mod.memory_repo.users[user.id] = user
            mem_mod.memory_repo.save_user(user)

        session_token = cls.create_session_token(user)
        csrf_token = cls.generate_csrf_token()
        return user, session_token, csrf_token
