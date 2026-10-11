"""DiagnosticAgent definition using Google ADK with deterministic tool binding."""

from __future__ import annotations

import os
from typing import Optional
from google.adk.agents import Agent

from services.worker.agents.tools import eval_sympy_arithmetic, validate_number_line_moves

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

DIAGNOSTIC_AGENT_INSTRUCTION = """You are a diagnostic mathematics assessment agent.
Your role is to diagnose student reasoning using deterministic verification tools:
- Always call `validate_number_line_moves` to calculate vector displacements and verify step correctness.
- Always call `eval_sympy_arithmetic` for exact rational arithmetic verification.
- Localize the FIRST supported error step.
- Map detected errors to standardized pedagogical taxonomy codes (e.g. MISC-ARITH-OFF-BY-ONE, MISC-NUM-DIR-REVERSE, MISC-LINE-INTERVAL-MISLABEL).
- Distinguish between final answer correctness and reasoning correctness.
- Detect compensatory errors where an incorrect step still arrives at the correct final target.
"""


def create_diagnostic_agent(model: Optional[str] = None) -> Agent:
    """Builds the DiagnosticAgent instance with deterministic Python verification tools.

    Args:
        model: Configurable model identifier.

    Returns:
        Configured ADK Agent instance with tool bindings.
    """
    selected_model = model or DEFAULT_MODEL
    return Agent(
        name="diagnostic_agent",
        model=selected_model,
        instruction=DIAGNOSTIC_AGENT_INSTRUCTION,
        description="Diagnoses student mathematical reasoning and localizes errors using deterministic SymPy and geometry tools.",
        tools=[eval_sympy_arithmetic, validate_number_line_moves],
    )
