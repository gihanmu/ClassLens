# Specification: 003 — Bounded Agent Orchestration & Mock Pipeline

**Specification ID:** SPEC-003
**Module:** `services/worker/agents/`
**Related Documents:** [`agent-design.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/architecture/agent-design.md), [`decision-register.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/review/decision-register.md)
**Guided by Skills:** `google-agents-cli-workflow`, `google-agents-cli-adk-code`, `gemini-api`
**Status:** Approved for Implementation Planning

---

## 1. Purpose & User Value

ClassLens diagnoses complex student handwriting using collaborative multi-agent reasoning. To ensure reliable, testable, and cost-effective development, the agent architecture strictly separates perception, hypothesis generation, mathematical checking, adversarial criticism, and cohort synthesis.

`003-agent-orchestration` defines the Google Agent Development Kit (ADK) agent pipeline, rigid Pydantic JSON contracts, uncertainty propagation rules, and a **deterministic offline mock adapter**. The mock adapter allows developing the entire vertical slice, frontend UI, and end-to-end integration tests without making live paid calls to Vertex AI or claiming to understand handwriting before Gate 3 live testing.

---

## 2. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-003.1 (Definitive 5 ADK Agents)**:
  1. `VisualEvidenceAgent`: Transcribes observable visual marks into `VisualEvidenceOutput`.
  2. `MathInterpretationAgent`: Converts visual observations into candidate step hypotheses (`CandidateHypothesesOutput`).
  3. `DiagnosticAgent`: Calls deterministic SymPy and geometry tools (`SPEC-001`), localizes first error, maps taxonomy (`DiagnosticOutput`).
  4. `IndependentCriticAgent`: Adversarially audits diagnosis against visual evidence. Triggers at most **ONE** bounded reinterpretation request or flags for teacher review (`CriticAuditOutput`).
  5. `CohortIntelligenceAgent`: Takes precomputed class statistics and synthesizes qualitative narrative + differentiated reteaching plan + SymPy-checked exit ticket (`CohortIntelligenceOutput`).
- **FR-003.2 (Offline Mock Adapter)**: In offline development mode (`MOCK_LLM=true`), agents use an in-memory fixture loader returning structured responses for the 13 cases of Problem #1065658, completely bypassing Vertex AI.
- **FR-003.3 (Uncertainty Propagation & Escalation)**: If any agent outputs confidence $< 0.75$, or if the Critic flags an unresolvable contradiction, sets `needs_teacher_review = True`.
- **FR-003.4 (Strict Anti-Hallucination Guardrail)**: Prohibits inferring unobserved student intent. If arrows or addends are missing, outputs `reasoning_status = "incomplete"`.

### Non-Functional Requirements
- **NFR-003.1 (Schema Enforcement)**: 100% of agent outputs must parse into Pydantic v2 models without validation errors.
- **NFR-003.2 (Bounded Execution)**: At most 1 Critic reinterpretation pass per response. Maximum generation tokens capped at `max_output_tokens = 1024`.

---

## 3. Typed Contracts (Pydantic Schemas)

Schemas match the approved [`agent-design.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/architecture/agent-design.md):
- `VisualEvidenceOutput`
- `CandidateHypothesesOutput`
- `DiagnosticOutput`
- `CriticAuditOutput`
- `CohortIntelligenceOutput`
- `StudentResponseAnalysis`
