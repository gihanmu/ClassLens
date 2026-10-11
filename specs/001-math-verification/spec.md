# Specification: 001 — Deterministic Math & Geometry Verification

**Specification ID:** SPEC-001
**Module:** `services/worker/math_verifier/`
**Related Documents:** [`agent-design.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/architecture/agent-design.md), [`decision-register.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/review/decision-register.md)
**Status:** Approved for Implementation Planning

---

## 1. Purpose & User Value

Secondary mathematics educators need objective, mathematically infallible verification of student reasoning steps. Generative AI models frequently make arithmetic slips or hallucinate intermediate algebraic values.

`001-math-verification` provides a 100% deterministic, non-LLM Python verification engine using SymPy and geometry vector math. It evaluates structured student steps, identifies the exact first point of failure, verifies alternate valid pathways (e.g. commutative rearrangements, different start positions), and flags mathematical contradictions before any diagnosis is shown to teachers.

---

## 2. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-001.1 (Rational Arithmetic Verification)**: Parse and evaluate arithmetic expressions involving integers and rational numbers using SymPy. Verify whether each step equality $LHS = RHS$ holds true.
- **FR-001.2 (Number Line Displacement Calculation)**: Given an ordered list of number line moves $[(x_0, x_1), (x_1, x_2), \dots]$, compute the displacement vectors $\Delta x_i = x_{end} - x_{start}$ and compare them against the expected addends of the question.
- **FR-001.3 (First Supported Error Localization)**: Sequentially evaluate step transitions. Identify the exact step number $k$ where $\Delta x_k \ne \text{expected}_k$ or arithmetic deviates. Subsequent errors are recorded as secondary/cascading.
- **FR-001.4 (Alternative Method Acceptance)**: Support alternative valid mathematical methods:
  - *Standard hop from zero*: $0 \to -6 \to +6 \to +2$.
  - *Direct start at first term*: $-6 \to +6 \to +2$.
  - *Commutative rearrangement*: $12 - 4 - 6 = 2$ or $12 \to 8 \to 2$.
  - *Bracket curve / arc representations*.
- **FR-001.5 (Answer vs Reasoning Decoupling)**: Distinguish whether the final answer equals target vs whether the number line path is mathematically valid. Specifically handle compensatory errors (e.g. Problem #1065658 Row 4).

### Non-Functional Requirements
- **NFR-001.1 (Execution Speed)**: Evaluate a complete 3-step vector sequence in $< 5\text{ ms}$ on a single CPU core.
- **NFR-001.2 (Zero LLM Dependency)**: Must not invoke Vertex AI, external network APIs, or disk I/O.
- **NFR-001.3 (Determinism)**: 100% reproducible results; zero stochastic behavior.

---

## 3. In-Scope vs. Out-of-Scope

### In-Scope
- Exact rational arithmetic evaluation via SymPy.
- 1D horizontal number line vector calculations.
- Evaluation of structured observation vectors (`start`, `end`, `direction`, `magnitude`).
- Error classification into standard taxonomy IDs (`MISC-ARITH-OFF-BY-ONE`, `MISC-NUM-DIR-REVERSE`, etc.).

### Out-of-Scope
- Transcribing handwriting from image pixels (responsibility of `VisualEvidenceAgent` in SPEC-003).
- 2D coordinate geometry or curved Bezier fitting.
- Natural language pedagogical explanation generation (responsibility of `DiagnosticAgent` in SPEC-003).

---

## 4. Typed Input / Output Contracts

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class NumberLineHop(BaseModel):
    step_number: int
    start: float
    end: float
    direction: Literal["left", "right", "none"]
    stated_magnitude: Optional[float] = None

class QuestionRule(BaseModel):
    problem_id: str = "1065658"
    expression: str = "-6 + 12 - 4"
    target_value: float = 2.0
    expected_addends: List[float] = [-6.0, 12.0, -4.0]
    allow_direct_start: bool = True
    allow_commutative: bool = True

class StepVerificationResult(BaseModel):
    step_number: int
    operation_str: str
    expected_displacement: float
    observed_displacement: float
    is_correct: bool
    deviation: float
    error_taxonomy: Optional[str] = None

class MathVerificationVerdict(BaseModel):
    is_reasoning_valid: bool
    is_final_answer_valid: bool
    detected_method: Literal["hop_from_zero", "direct_start", "commutative", "unrecognized"]
    verified_steps: List[StepVerificationResult]
    first_error_step: Optional[int] = None
    first_error_taxonomy: Optional[str] = None
    is_compensatory_error: bool = False
```

---

## 5. Error Handling & Abstention Behavior

- If input vectors are empty (no arrows drawn), returns `is_reasoning_valid = False`, `detected_method = "unrecognized"`, and sets `first_error_taxonomy = "REASONING_INCOMPLETE"`.
- If an arithmetic string is malformed or unparseable, catches `sympy.SympifyError`, returns an explicit failure without crashing, and flags for teacher review.
- If floating point values differ by less than $10^{-5}$, treats them as identical to avoid precision drift.
