"""Password hashing and verification utilities using Argon2id."""

from __future__ import annotations

import logging
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

logger = logging.getLogger(__name__)

# Argon2id password hasher configured with robust parameters:
# - Type: Argon2id (hybrid data-dependent/independent, resists side-channel & GPU attacks)
# - Time cost: 2 iterations
# - Memory cost: 65536 KiB (64 MiB)
# - Parallelism: 1 lane
# - Hash length: 32 bytes
_password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
)


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    if not password:
        raise ValueError("Password cannot be empty")
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash.

    Returns True if valid, False otherwise.
    Never raises on verification mismatch or malformed hash.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False
    except Exception as exc:
        logger.warning(f"Unexpected error during password verification: {exc}")
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Checks whether the password hash was generated with older parameters."""
    try:
        return _password_hasher.check_needs_rehash(hashed_password)
    except Exception:
        return False
