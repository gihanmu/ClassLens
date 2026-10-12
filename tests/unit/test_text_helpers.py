"""Unit tests for services.common.text_helpers."""

from services.common.text_helpers import sanitize_classroom_label


def test_sanitize_classroom_label():
    # Basic whitespace trimming
    assert sanitize_classroom_label("  Grade 8 Math  ") == "Grade 8 Math"

    # Multiple whitespace collapse
    assert sanitize_classroom_label("Period   1  -   Algebra") == "Period 1 - Algebra"

    # Truncation to max length
    assert sanitize_classroom_label("A" * 60, max_length=10) == "A" * 10

    # Control characters stripped
    assert sanitize_classroom_label("Classroom\x00\x08Name") == "ClassroomName"

    # Empty string
    assert sanitize_classroom_label("") == ""
    assert sanitize_classroom_label(None) == ""
