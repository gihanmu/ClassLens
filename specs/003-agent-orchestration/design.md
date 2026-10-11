# Design: 003 — Bounded Agent Orchestration & Mock Pipeline

**Design ID:** DES-003
**Module:** `services/worker/agents/`
**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/003-agent-orchestration/spec.md)

---

## 1. Module Structure & Google ADK Integration

```text
services/worker/agents/
├── __init__.py
├── contracts.py              # Pydantic v2 schemas for all 5 ADK agents
├── visual_agent.py           # VisualEvidenceAgent definition
├── interpretation_agent.py   # MathInterpretationAgent definition
├── diagnostic_agent.py       # DiagnosticAgent with tool binding
├── critic_agent.py           # IndependentCriticAgent definition
├── cohort_agent.py           # CohortIntelligenceAgent definition
├── mock_adapter.py           # Offline mock runner using structured fixtures
└── pipeline.py               # Orchestrator coordinating sequential execution
```

---

## 2. Mock Adapter Architecture

To enable offline local development without calling paid Gemini APIs or claiming to read handwritten pixels:

```mermaid
flowchart TD
    Run["pipeline.analyze_response(response_id)"] --> CheckMode{"MOCK_LLM == true?"}
    CheckMode -->|Yes| MockRunner["MockAgentRunner: load JSON fixture for response_id"]
    MockRunner --> RetFixture["Return structured VisualEvidenceOutput fixture"]
    RetFixture --> RunTools["Execute Real Python SymPy & Geometry Tools on Fixture"]
    RunTools --> RetDiag["Synthesize DiagnosticOutput & CriticAuditOutput"]
    RetDiag --> Final["Emit Final StudentResponseAnalysis"]

    CheckMode -->|No (Gated Live Mode)| LiveRunner["Vertex AI Gemini 3.8 Flash Runner<br>(Requires Gate 3 User Authorization)"]
```
