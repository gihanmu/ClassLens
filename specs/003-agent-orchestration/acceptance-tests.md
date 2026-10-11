# Acceptance Tests: 003 — Bounded Agent Orchestration & Mock Pipeline

**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/003-agent-orchestration/spec.md)
**Test Suite Path:** `tests/unit/test_agent_orchestration.py`

---

## 1. Test Matrix

| Test Case ID | Test Target | Input Scenario | Expected Output Behavior |
| :--- | :--- | :--- | :--- |
| **TC-003.01** | Mock Pipeline Execution | Clean student response fixture (`resp_04255753`) | Emits valid `StudentResponseAnalysis`; `answer_status = correct`, `reasoning_status = supported_correct`, `needs_teacher_review = False`. |
| **TC-003.02** | Compensatory Error Handling | Compensatory error fixture (`resp_56005c1c`) | Emits `answer_status = correct`, `reasoning_status = supported_error`, localizes Step 2 off-by-one error. |
| **TC-003.03** | Incomplete Reasoning | Answer marked without working (`resp_e33295ea`) | Emits `answer_status = correct`, `reasoning_status = incomplete`, `needs_teacher_review = True`. |
| **TC-003.04** | Critic Bounded Retry | Mock Critic detects contradiction on pass 1 | Triggers exactly 1 reinterpretation pass; halts loop and records attempt count = 1. |
| **TC-003.05** | Low Confidence Escalation | Mock perception emits confidence `0.65` | Sets `needs_teacher_review = True` with reason `low_confidence`. |

---

## 2. Verification Execution Command
```bash
pytest tests/unit/test_agent_orchestration.py -v
```
- **Acceptance Gate**: 100% pass rate in $< 2.0$ seconds with zero live API calls.
