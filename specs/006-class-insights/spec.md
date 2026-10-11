# Specification: 006 — Cohort Misconception Dashboard & Differentiated Reteaching

**Specification ID:** SPEC-006
**Module:** `services/worker/cohort/` & `apps/web/`
**Related Documents:** [`functional-requirements.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/requirements/functional-requirements.md), [`agent-design.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/docs/architecture/agent-design.md)
**Guided by Skills:** `google-agents-cli-adk-code`, `gemini-api`
**Status:** Approved for Implementation Planning

---

## 1. Purpose & User Value

Grading individual student papers leaves educators with a stack of scores but without clear insight into systemic class-wide misconceptions. Teachers need to know: *Did 60% of the class make the same off-by-one directional error, or were these isolated slips? What concrete activity should I run tomorrow?*

`006-class-insights` computes deterministic cohort statistics (counts, percentages, confirmed vs AI-proposed breakdowns) and pairs them with `CohortIntelligenceAgent` (or an offline mock synthesizer). It generates:
1. An accessible misconception distribution chart with explicit denominators (e.g. `5/13 students`).
2. Differentiated small-group action cards (concrete manipulatives, worked examples).
3. A 3-question formative exit ticket verified with SymPy.

---

## 2. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-006.1 (Deterministic Cohort Computation)**:
  - Pure Python function `compute_cohort_statistics(responses: List[StudentResponseAnalysis]) -> CohortStatistics`.
  - Calculates total responses, correct count/percentage, error count/percentage, unreadable count/percentage, and aggregates misconception clusters.
  - **Strict Rule**: The LLM is **never allowed to count or compute percentages**. All math is calculated by code and supplied as ground truth facts.
- **FR-006.2 (Accessible UI Visualization)**:
  - Horizontal bar chart rendering misconception frequency.
  - Every bar displays an explicit fractional denominator (e.g. `4 of 13 students (30.8%)`).
  - Distinguishes teacher-confirmed errors from AI-proposed errors.
- **FR-006.3 (Differentiated Pedagogical Cards)**:
  - Generates small-group recommendations based on dominant clusters (e.g., "Use integer chip modeling for students struggling with $-6 + 12$").
- **FR-006.4 (SymPy-Verified Exit Ticket)**:
  - Generates 3 formative exit ticket questions targeting the identified misconceptions.
  - All question arithmetic expressions are validated by `SymPyChecker`.

### Non-Functional Requirements
- **NFR-006.1 (Cohort Execution Speed)**: Deterministic statistics computed in $< 10\text{ ms}$ for 30 responses.
- **NFR-006.2 (Accessible Charts)**: Chart elements feature high contrast, dual indicators, and text table alternatives for screen readers.

---

## 3. Typed Contracts

```python
class MisconceptionCluster(BaseModel):
    taxonomy_id: str
    title: str
    affected_count: int
    affected_percentage: float
    teacher_confirmed_count: int
    ai_proposed_count: int
    sample_response_ids: List[str]

class CohortStatistics(BaseModel):
    total_responses: int
    correct_count: int
    correct_percentage: float
    error_count: int
    error_percentage: float
    unreadable_count: int
    unreadable_percentage: float
    misconception_clusters: List[MisconceptionCluster]
```
