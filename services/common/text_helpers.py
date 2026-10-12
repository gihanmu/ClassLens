"""Helper functions for text processing and classroom label sanitization."""

import re


def sanitize_classroom_label(label: str, max_length: int = 50) -> str:
    """Sanitize and normalize classroom labels or student identifiers.

    Trims leading/trailing whitespace, strips control characters, and truncates to max_length.
    """
    if not label:
        return ""
    # Strip non-printable and control characters
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", label.strip())
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:max_length]
