"""Security package for ClassLens worker pipeline."""

from services.worker.security.provenance_guard import (
    UntrustedProvenanceError,
    verify_synthetic_path,
    verify_synthetic_bytes,
    is_trusted_synthetic,
)

__all__ = [
    "UntrustedProvenanceError",
    "verify_synthetic_path",
    "verify_synthetic_bytes",
    "is_trusted_synthetic",
]
