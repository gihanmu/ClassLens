# ClassLens — Gate 3 Evaluation Rubric

This rubric establishes the five evaluation dimensions used to grade Gemini's handwriting transcription outputs against ground truth on student number-line worksheets.

---

## 1. Rubric Dimensions

### Dimension 1: Visual Element Capture & Coordinate Fidelity (Weight: 30%)
- **Score 4 (Exemplary):** Accurately identifies all drawn hops, coordinates (start/end), tick marks, written labels, and final answer with zero hallucinations.
- **Score 3 (Proficient):** Identifies all hops and final answer; minor coordinate deviation within +/- 0.5 ticks on dense axes.
- **Score 2 (Developing):** Misses one hop, misidentifies jump direction, or confuses stated label with landing coordinate.
- **Score 1 (Unacceptable):** Misses multiple hops, invents hops not present in the ink, or fails to extract visible final answer.

### Dimension 2: Directionality & Arrowhead Fidelity (Weight: 20%)
- **Score 4 (Exemplary):** Explicitly checks and correctly marks `arrowhead_visible` (true/false) for each arc. Correctly assigns `left_negative` vs `right_positive`.
- **Score 3 (Proficient):** Correctly infers hop direction; correctly identifies arrowhead presence in >= 80% of hops.
- **Score 2 (Developing):** Infers hop direction from arithmetic expectation rather than arrow orientation; incorrectly flags arrowheads when absent.
- **Score 1 (Unacceptable):** Inverts jump direction or consistently reports false arrowheads.

### Dimension 3: Decoupling Evidence from Mathematical Intent (Weight: 25%)
- **Score 4 (Exemplary):** Strictly reports visible ink coordinates. When a student makes a procedural miscount (e.g. landing on 5 instead of 6), reports landing=5 without attempting to "correct" it to 6.
- **Score 3 (Proficient):** Reports physical landing accurately; notes discrepancy between label and landing coordinate in description.
- **Score 2 (Developing):** Conflates drawn coordinate with label or "repairs" the coordinate to make arithmetic balance.
- **Score 1 (Unacceptable):** Ignores physical ink marks in favor of completing the canonical math formula.

### Dimension 4: Ambiguity & Quality Reporting (Weight: 15%)
- **Score 4 (Exemplary):** Systematically documents all faint strokes, incomplete terminations, erasures, and blank answers in `ambiguities`.
- **Score 3 (Proficient):** Flags major blocking ambiguities; minor smudges or faint ticks omitted.
- **Score 2 (Developing):** Fails to flag an incomplete hop or missing answer box value.
- **Score 1 (Unacceptable):** Guesses arbitrarily on unreadable or blank sections without documenting ambiguity.

### Dimension 5: Teacher Escalation Precision (Weight: 10%)
- **Score 4 (Exemplary):** Flags `requires_teacher_review=true` with clear diagnostic reasoning whenever blocking ambiguities or unreadable marks exist; does not over-escalate clear worksheets.
- **Score 3 (Proficient):** Correctly escalates ambiguous worksheets; occasional conservative escalation on clear worksheets.
- **Score 2 (Developing):** Fails to escalate when worksheet is incomplete or unreadable.
- **Score 1 (Unacceptable):** Never escalates or escalates unconditionally regardless of quality.

---

## 2. Gate 3 Pass/Fail Threshold

A test case is considered **Passed** if:
- Aggregate score across all 5 dimensions is >= 85% (17 / 20 points).
- Zero hallucinated hops are generated.
- Teacher escalation matches the ground truth requirement.
