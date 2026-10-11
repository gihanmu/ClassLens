# Implementation Tasks: 003 — Bounded Agent Orchestration & Mock Pipeline

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/003-agent-orchestration/spec.md)
**Status:** Completed & Verified via Unit Tests (32/32 passing, 106/106 total)

---

## Task List

- [x] **TASK-003.1**: Implement `services/worker/agents/contracts.py` containing complete Pydantic v2 models (`VisualEvidenceOutput`, `CandidateHypothesesOutput`, `DiagnosticOutput`, `CriticAuditOutput`, `CohortIntelligenceOutput`, `StudentResponseAnalysis`).
- [x] **TASK-003.2**: Create structured JSON mock fixtures for all 13 responses of Problem #1065658 in `services/worker/fixtures/problem_1065658/`.
- [x] **TASK-003.3**: Implement `mock_adapter.py` providing deterministic in-memory mock responses matching Pydantic schemas.
- [x] **TASK-003.4**: Implement `VisualEvidenceAgent`, `MathInterpretationAgent`, `DiagnosticAgent`, `IndependentCriticAgent`, and `CohortIntelligenceAgent` using Google ADK abstractions.
- [x] **TASK-003.5**: Wire deterministic `SymPyChecker` and `NumberLineDisplacementCalculator` tools into `DiagnosticAgent` and `CohortIntelligenceAgent`.
- [x] **TASK-003.6**: Implement `pipeline.py` orchestrating sequential execution, enforcing uncertainty thresholds ($< 0.75 \implies \text{review}$), and bounding Critic reinterpretation to at most 1 attempt.
- [x] **TASK-003.7**: Author unit test suite in `tests/unit/test_agent_orchestration.py` validating schema parsing, tool invocation, and mock pipeline execution.
