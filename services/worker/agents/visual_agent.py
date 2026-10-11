"""VisualEvidenceAgent definition using Google ADK."""

from __future__ import annotations

import os
from typing import Optional
from google.adk.agents import Agent


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

VISUAL_AGENT_INSTRUCTION = """You are an objective mathematical visual evidence transcriber.
Your sole role is to transcribe physically visible marks on the student response image:
- Identify if a 1D horizontal number line is present.
- Transcribe tick intervals, integer coordinate labels, and arrows/bracket curves.
- For each arrow or jump: record start_pos, end_pos, direction ("left", "right"), and stated_magnitude if written.
- Transcribe any explicit circled or written final answer numbers.
- Record confidence score between 0.0 and 1.0.

STRICT GUARDRAIL:
Do not interpolate missing steps, assume student intent, or guess unobserved marks.
If marks are missing, record only what is visible.
"""


def create_visual_evidence_agent(
    model: Optional[str] = None,
    high_res_mode: bool = False,
) -> Agent:
    """Builds the VisualEvidenceAgent instance using Google ADK.

    Args:
        model: Configurable model identifier (defaults to GEMINI_MODEL env or gemini-3.8-flash).
        high_res_mode: Configurable option for future high-resolution image evaluation.

    Returns:
        Configured ADK Agent instance.
    """
    selected_model = model or DEFAULT_MODEL
    desc = "Transcribes physically visible handwriting, ticks, arrows, and numbers from student math worksheets."
    if high_res_mode:
        desc += " (Configured for high-resolution evaluation)."

    return Agent(
        name="visual_evidence_agent",
        model=selected_model,
        instruction=VISUAL_AGENT_INSTRUCTION,
        description=desc,
        tools=[],
    )
