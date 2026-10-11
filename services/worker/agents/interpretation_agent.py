"""MathInterpretationAgent definition using Google ADK."""

from __future__ import annotations

import os
from typing import Optional
from google.adk.agents import Agent

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

INTERPRETATION_AGENT_INSTRUCTION = """You are a mathematical reasoning interpreter for K-12 integer arithmetic.
Your role is to map raw visual observations into candidate mathematical step hypotheses:
- Analyze number line arrow jumps and identify candidate strategies (e.g. hop from zero, direct jump from first addend, commutative rearrangement).
- Evaluate alternative valid mathematical representations.
- Assess reasoning completeness: "complete", "partial", or "incomplete".
- If no working or jumps are shown, flag reasoning_completeness as "incomplete".

STRICT GUARDRAIL:
Never invent unobserved terms or assume student intentions.
"""


def create_math_interpretation_agent(model: Optional[str] = None) -> Agent:
    """Builds the MathInterpretationAgent instance using Google ADK.

    Args:
        model: Configurable model identifier.

    Returns:
        Configured ADK Agent instance.
    """
    selected_model = model or DEFAULT_MODEL
    return Agent(
        name="math_interpretation_agent",
        model=selected_model,
        instruction=INTERPRETATION_AGENT_INSTRUCTION,
        description="Generates candidate mathematical step hypotheses and alternative solution paths from visual evidence.",
        tools=[],
    )
