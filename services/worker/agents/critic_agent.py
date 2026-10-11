"""IndependentCriticAgent definition using Google ADK."""

from __future__ import annotations

import os
from typing import Optional
from google.adk.agents import Agent

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

CRITIC_AGENT_INSTRUCTION = """You are an independent adversarial auditor for mathematical assessments.
Your role is to strictly audit diagnostic conclusions against raw physical visual evidence:
- Check for hallucinations: Does the diagnosis claim steps that are not visibly drawn in the observations?
- Check for evidence grounding: Is the identified error step physically visible on the number line?
- Check for contradictions: Does the diagnosed error contradict the student's stated answer or drawing?
- If an ungrounded claim or contradiction is found on pass 1, flag `reinterpretation_needed = True`.
- If an unresolvable contradiction persists after reinterpretation, set `requires_teacher_review = True` with a clear rationale.
- Cap reinterpretation to at most ONE bounded attempt.
"""


def create_critic_agent(model: Optional[str] = None) -> Agent:
    """Builds the IndependentCriticAgent instance using Google ADK.

    Args:
        model: Configurable model identifier.

    Returns:
        Configured ADK Agent instance.
    """
    selected_model = model or DEFAULT_MODEL
    return Agent(
        name="independent_critic_agent",
        model=selected_model,
        instruction=CRITIC_AGENT_INSTRUCTION,
        description="Adversarially audits mathematical diagnoses against visual evidence, catching hallucinations and bounding retries.",
        tools=[],
    )
