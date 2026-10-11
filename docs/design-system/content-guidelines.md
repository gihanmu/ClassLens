# ClassLens Design System — Content & Copywriting Guidelines

## 1. Tone of Voice

ClassLens speaks as a **supportive, highly knowledgeable instructional coach**:
- **Empathetic & Teacher-Centric**: We respect teachers' time and classroom expertise. Explanations are actionable, concise, and focused on helping students.
- **Mathematically Grounded**: We use precise mathematical language (e.g. *intervals*, *directed displacements*, *commutative order*, *subtraction vector*) without sounding clinical.
- **Transparent About AI Capabilities**: We never disguise automated suggestions as infallible truth. Diagnostic findings are labeled as "AI-Proposed" until confirmed by the educator.

---

## 2. Terminology Glossary & Substitution Rules

| Discouraged / Technical Term | Required Teacher-First Replacement | Context / Rationale |
|---|---|---|
| `Inference execution` | `Analysis in progress` / `Analyses completed` | Software jargon vs educator workflow |
| `Inference output` | `Diagnostic insights` | Focuses on educational value |
| `Ground truth classification` | `Teacher-confirmed diagnosis` | Respects teacher pedagogical authority |
| `MISC-ARITH-OFF-BY-ONE` | `Off-by-One Interval Miscount` | Primary label must be human-readable |
| `MISC-DIR-INV` | `Directional Vector Inversion` | Technical code kept as secondary tag |
| `Bbox coordinates` | `Observed marks & hops` | Emphasizes student work |
| `Synthetic fixture mock` | `Offline Demo Mode (Simulated AI)` | Transparent about offline status |
| `Model hallucinations` | `Unsupported reasoning steps` | Focuses on student mathematical evidence |

---

## 3. Provenance & Confidence Disclosures

Whenever a diagnostic verdict is displayed, its provenance must be explicitly stated:
1. **Offline Simulated**: *"Offline Demo — Simulated AI analysis verified by SymPy"*
2. **AI-Proposed (Unreviewed)**: *"AI Diagnostic Suggestion — Awaiting Teacher Confirmation"*
3. **Teacher-Confirmed**: *"Teacher Confirmed — Approved by Sarah Lim"*
4. **Teacher-Overridden**: *"Teacher Overridden — Updated with pedagogical notes"*
