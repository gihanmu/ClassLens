"""Strict server-side provenance guard restricting live Gemini inference to trusted synthetic fixtures.

Complies with Gate 4A Privacy & Security Safeguards:
- Canonical path resolution protecting against path traversal and symlink escapes.
- Cryptographic SHA-256 allowlist of authorized synthetic worksheets.
- Server-side validation of image bytes (arbitrary client uploads blocked in live mode).
- Zero transmission of real student PII or raw research dataset files.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, Set, Union


class UntrustedProvenanceError(PermissionError):
    """Raised when an image fails server-side synthetic provenance validation for live AI."""


# Project root and trusted synthetic fixture root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TRUSTED_SYNTHETIC_DIR = (PROJECT_ROOT / "tests" / "fixtures" / "synthetic_evaluation_cases").resolve()

# Pre-computed cryptographic SHA-256 checksums of authorized synthetic fixtures
TRUSTED_SYNTHETIC_ALLOWLIST: Dict[str, str] = {
    "case_01_canonical_correct.png": "3dd01287f3763a11c6b54d45edfacbc39b6318819fb975e9dc5e74dbd57e98d6",
    "case_02_off_by_one_error.png": "78ff2a0627485b2fc5a4080389b078c4b1c3842de0cf34f15ddacb99b1db3232",
    "case_03_ambiguous_incomplete.png": "9add38ac12542444a7ffe435f8e68cdea8d6bf99c6ce708657241306d88431cc",
}

TRUSTED_HASH_SET: Set[str] = set(TRUSTED_SYNTHETIC_ALLOWLIST.values())


def calculate_sha256(data: bytes) -> str:
    """Calculates SHA-256 digest of binary data."""
    return hashlib.sha256(data).hexdigest()


def verify_synthetic_path(file_path: Union[str, Path]) -> Path:
    """Verifies that a file path points to an authorized, untampered synthetic fixture.

    Enforces:
    1. Realpath resolution (cannot escape TRUSTED_SYNTHETIC_DIR via '..' or symlinks).
    2. Existence and regular file verification.
    3. Content integrity check matching cryptographic SHA-256 allowlist.

    Raises:
        UntrustedProvenanceError: If the path escapes the synthetic root, references
        a non-synthetic file, or content hash does not match allowlist.
    """
    raw_path = Path(file_path)

    # 1. Reject paths pointing to real student datasets
    str_repr = str(file_path).lower()
    if "dataset/" in str_repr or "/dataset" in str_repr or "drawedumath" in str_repr or "mathwriting" in str_repr:
        raise UntrustedProvenanceError(
            f"Provenance Guard Block: Path '{file_path}' references a real dataset or external directory. "
            "Live Gemini inference is strictly restricted to verified synthetic fixtures in Gate 4A."
        )

    # 2. Canonical path resolution
    try:
        resolved = raw_path.resolve(strict=True)
    except FileNotFoundError:
        raise UntrustedProvenanceError(f"Provenance Guard Block: Fixture file not found: {file_path}")

    # 3. Path confinement check
    try:
        resolved.relative_to(TRUSTED_SYNTHETIC_DIR)
    except ValueError:
        raise UntrustedProvenanceError(
            f"Provenance Guard Block: Path '{resolved}' is outside the trusted synthetic directory: "
            f"'{TRUSTED_SYNTHETIC_DIR}'. Path traversal and symlink escapes are blocked."
        )

    # 4. Check for symlink escaping or tampering
    if os.path.islink(raw_path):
        real_target = Path(os.path.realpath(raw_path))
        try:
            real_target.relative_to(TRUSTED_SYNTHETIC_DIR)
        except ValueError:
            raise UntrustedProvenanceError(
                f"Provenance Guard Block: Symlink '{raw_path}' resolves outside trusted root."
            )

    # 5. Cryptographic hash content verification
    file_bytes = resolved.read_bytes()
    computed_hash = calculate_sha256(file_bytes)

    if computed_hash not in TRUSTED_HASH_SET:
        raise UntrustedProvenanceError(
            f"Provenance Guard Block: Content SHA-256 '{computed_hash}' for '{resolved.name}' "
            "is not in the trusted synthetic fixture allowlist. Modified or arbitrary files are blocked."
        )

    return resolved


def verify_synthetic_bytes(image_bytes: bytes) -> str:
    """Verifies that arbitrary binary image bytes match an authorized synthetic fixture.

    In Gate 4A, arbitrary uploaded images are strictly prohibited from invoking live AI.
    Only bytes whose SHA-256 matches a known synthetic fixture are permitted.

    Raises:
        UntrustedProvenanceError: If image bytes do not match the synthetic allowlist.
    """
    if not image_bytes:
        raise UntrustedProvenanceError("Provenance Guard Block: Image bytes are empty.")

    computed_hash = calculate_sha256(image_bytes)

    if computed_hash not in TRUSTED_HASH_SET:
        raise UntrustedProvenanceError(
            "Provenance Guard Block: Submitted image bytes do not match any authorized synthetic fixture. "
            "Arbitrary client uploads cannot be sent to live Gemini in Gate 4A. "
            "Only trusted synthetic fixtures are authorized."
        )

    # Find matching fixture name
    for name, h in TRUSTED_SYNTHETIC_ALLOWLIST.items():
        if h == computed_hash:
            return name

    return computed_hash


def is_trusted_synthetic(target: Union[str, Path, bytes]) -> bool:
    """Boolean helper to check if a path or bytes are trusted synthetic."""
    try:
        if isinstance(target, bytes):
            verify_synthetic_bytes(target)
        else:
            verify_synthetic_path(target)
        return True
    except (UntrustedProvenanceError, Exception):
        return False
