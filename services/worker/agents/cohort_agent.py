"""CohortIntelligenceAgent definition using Google ADK with SymPy tool binding."""

from __future__ import annotations

import os
from typing import Optional
from google.adk.agents import Agent

from services.worker.agents.tools import compute_cohort_statistics, eval_sympy_arithmetic

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

COHORT_AGENT_INSTRUCTION = """You are a master mathematics pedagogical specialist.
Your role is to synthesize class-level assessment distributions into actionable teaching insights:
- Rely strictly on precomputed cohort statistics provided by Python for all numbers, counts, and percentages.
- Never calculate or invent frequencies, counts, or percentages yourself.
- Distinguish between systemic class-wide misconceptions and isolated arithmetic slips.
- Generate targeted, differentiated teaching actions (concrete manipulatives, worked examples, guided inquiry).
- Design a 3-question formative exit ticket and verify all mathematical stems and answers using `eval_sympy_arithmetic`.
"""


def create_cohort_intelligence_agent(model: Optional[str] = None) -> Agent:
    """Builds the CohortIntelligenceAgent instance with SymPy tool binding.

    Args:
        model: Configurable model identifier.

    Returns:
        Configured ADK Agent instance.
    """
    selected_model = model or DEFAULT_MODEL
    return Agent(
        name="cohort_intelligence_agent",
        model=selected_model,
        instruction=COHORT_AGENT_INSTRUCTION,
        description="Synthesizes deterministic cohort statistics into qualitative narratives, differentiated reteaching plans, and SymPy-verified exit tickets.",
        tools=[eval_sympy_arithmetic, compute_cohort_statistics],
    )
