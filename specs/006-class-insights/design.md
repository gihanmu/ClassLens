# Design: 006 — Cohort Misconception Dashboard & Differentiated Reteaching

**Design ID:** DES-006
**Module:** `services/worker/cohort/` & `apps/web/`
**Related Spec:** [`spec.md`](file:///Users/gihanmu/Desktop/Projects/AIBuilderCup2026/ClassLens/specs/006-class-insights/spec.md)

---

## 1. Module Structure

```text
services/worker/cohort/
├── __init__.py
├── statistics_calculator.py   # Pure Python cohort frequency aggregator
├── synthesizer.py             # CohortIntelligenceAgent or mock synthesizer
└── exit_ticket_validator.py   # SymPy verification of exit ticket questions
```

---

## 2. Cohort Data Flow

```mermaid
flowchart TD
    Responses["All Completed Response Records (e.g. 13 students)"] --> Calc["statistics_calculator.compute_cohort_statistics()"]
    Calc --> StatsDict["Computed CohortStatistics (Explicit counts & percentages)"]
    StatsDict --> Agent["CohortIntelligenceAgent (Gemini 3.8 Flash or Mock)"]
    Agent --> Plan["Generated Narrative + 2 Differentiated Actions + 3 Exit Tickets"]
    Plan --> SymPyCheck["exit_ticket_validator.py: verify arithmetic with SymPy"]
    SymPyCheck --> Store["Save to Firestore insights/ and reteaching_plans/"]
    Store --> UI["Next.js Cohort Dashboard: accessible bar chart with denominators"]
```
