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


TRUSTED_UPLOADS_DIR = (PROJECT_ROOT / "local-data" / "uploads").resolve()
TRUSTED_EVAL_IMAGES_DIR = (PROJECT_ROOT / "evaluation" / "datasets" / "images").resolve()


def verify_uploaded_worksheet_path(
    file_path: Union[str, Path],
    auth_key: Optional[str] = None,
) -> Path:
    """Verifies that an uploaded worksheet image path is securely confined to local-data/uploads/
    or evaluation/datasets/images/ and that explicit owner authorization is active.

    Enforces Gate 6 DevSecOps Safeguards:
    1. Prohibits accessing raw research datasets or arbitrary external directories.
    2. Fail-closed owner authorization: settings.is_live_authorized(auth_key) MUST be True.
    3. Path traversal & symlink prevention: canonical realpath must resolve strictly within
       TRUSTED_UPLOADS_DIR or TRUSTED_EVAL_IMAGES_DIR.
    4. Regular file verification and size check <= settings.max_image_size_bytes.
    """
    from services.api.config import settings

    # 1. Reject paths pointing to real research datasets or forbidden directories
    str_repr = str(file_path).lower()
    if "drawedumath" in str_repr or "mathwriting" in str_repr or "external_dataset" in str_repr:
        raise UntrustedProvenanceError(
            f"Provenance Guard Block: Path '{file_path}' references a prohibited research dataset. "
            "Live Gemini inference is strictly prohibited from accessing real student datasets."
        )

    # 2. Enforce fail-closed owner authorization
    if not settings.is_live_authorized(auth_key):
        raise UntrustedProvenanceError(
            "Gate 6 Fail-Closed Safeguard: Live Gemini inference on uploaded worksheets requires "
            "explicit owner authorization. Enable CLASSLENS_LIVE_INFERENCE_ENABLED=true and "
            "configure CLASSLENS_LIVE_AUTH_KEY."
        )

    raw_path = Path(file_path)

    # 3. Canonical path resolution
    try:
        resolved = raw_path.resolve(strict=True)
    except FileNotFoundError:
        raise UntrustedProvenanceError(f"Provenance Guard Block: Uploaded worksheet file not found: {file_path}")

    # 4. Path confinement check (must be in uploads or eval images directory)
    in_uploads = False
    in_eval = False
    try:
        resolved.relative_to(TRUSTED_UPLOADS_DIR)
        in_uploads = True
    except ValueError:
        pass

    try:
        resolved.relative_to(TRUSTED_EVAL_IMAGES_DIR)
        in_eval = True
    except ValueError:
        pass

    if not in_uploads and not in_eval:
        raise UntrustedProvenanceError(
            f"Provenance Guard Block: Path '{resolved}' escapes trusted storage directories. "
            f"Path traversal and unauthorized directory access are blocked."
        )

    # 5. Check for symlink escaping
    if os.path.islink(raw_path):
        real_target = Path(os.path.realpath(raw_path))
        target_in_uploads = False
        target_in_eval = False
        try:
            real_target.relative_to(TRUSTED_UPLOADS_DIR)
            target_in_uploads = True
        except ValueError:
            pass
        try:
            real_target.relative_to(TRUSTED_EVAL_IMAGES_DIR)
            target_in_eval = True
        except ValueError:
            pass
        if not target_in_uploads and not target_in_eval:
            raise UntrustedProvenanceError(
                f"Provenance Guard Block: Symlink '{raw_path}' resolves outside trusted roots."
            )

    # 6. Check regular file and size bound
    if not resolved.is_file():
        raise UntrustedProvenanceError(f"Provenance Guard Block: '{resolved}' is not a regular file.")

    file_size = resolved.stat().st_size
    if file_size == 0:
        raise UntrustedProvenanceError("Provenance Guard Block: Uploaded image file is empty.")
    if file_size > settings.max_image_size_bytes:
        raise UntrustedProvenanceError(
            f"Provenance Guard Block: Image size ({file_size} bytes) exceeds maximum limit "
            f"({settings.max_image_size_bytes} bytes)."
        )

    return resolved


def verify_analysis_image_source(
    target: Union[str, Path, bytes],
    response_id: str = "",
    auth_key: Optional[str] = None,
) -> Union[Path, bytes]:
    """Unified verifier for any image source provided to the multi-agent analysis pipeline.

    Supports:
    1. Authorized synthetic fixtures in tests/fixtures/synthetic_evaluation_cases/.
    2. Securely confined uploaded worksheets in local-data/uploads/ (with owner authorization).
    3. Confined evaluation dataset images in evaluation/datasets/images/ (with owner authorization).
    4. In-memory image bytes (synthetic matching allowlist, or uploaded if authorized).
    """
    from services.api.config import settings

    if isinstance(target, (str, Path)):
        str_repr = str(target).lower()
        if "drawedumath" in str_repr or "mathwriting" in str_repr or "external_dataset" in str_repr:
            raise UntrustedProvenanceError(
                f"Provenance Guard Block: Path '{target}' references a prohibited research dataset. "
                "Live Gemini inference is strictly prohibited from accessing real student datasets."
            )

        p = Path(target)
        # Check if it resolves inside TRUSTED_SYNTHETIC_DIR
        try:
            resolved = p.resolve(strict=True)
            try:
                resolved.relative_to(TRUSTED_SYNTHETIC_DIR)
                return verify_synthetic_path(resolved)
            except ValueError:
                pass
        except FileNotFoundError:
            pass

        # Otherwise verify as uploaded worksheet or eval image
        return verify_uploaded_worksheet_path(p, auth_key=auth_key)

    elif isinstance(target, bytes):
        if not target:
            raise UntrustedProvenanceError("Provenance Guard Block: Image bytes are empty.")
        if len(target) > settings.max_image_size_bytes:
            raise UntrustedProvenanceError(
                f"Provenance Guard Block: Image bytes ({len(target)}) exceed maximum allowed size."
            )

        # If it matches synthetic allowlist, it is always permitted
        h = calculate_sha256(target)
        if h in TRUSTED_HASH_SET:
            return target

        # For non-synthetic bytes, enforce fail-closed owner authorization
        if not settings.is_live_authorized(auth_key):
            raise UntrustedProvenanceError(
                "Gate 6 Fail-Closed Safeguard: Live Gemini inference on arbitrary image bytes requires "
                "explicit owner authorization. Enable CLASSLENS_LIVE_INFERENCE_ENABLED=true and "
                "configure CLASSLENS_LIVE_AUTH_KEY."
            )
        return target

    raise UntrustedProvenanceError(f"Unsupported image target type: {type(target)}")

