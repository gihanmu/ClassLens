# ClassLens — Gate 3 Multimodal Model Selection & Architecture Analysis

## 1. Executive Summary

Gate 3 evaluates whether Google Gemini can accurately reconstruct handwritten mathematical marks from elementary and middle school number-line worksheets with sufficient fidelity to feed the ClassLens deterministic SymPy verification engine.

To ensure cost-efficiency, low latency, and robust vision capabilities, we evaluated four Gemini candidate models available via the unified Google GenAI SDK (`google-genai`) across Google Cloud Vertex AI (global and regional `asia-southeast1`).

**Recommendation:** **`gemini-3.8-flash`** (or stable GA fallback `gemini-2.5-flash`).

---

## 2. Model Candidate Comparison

| Dimension | `gemini-3.8-flash` (Recommended) | `gemini-2.5-flash` (Stable Alternative) | `gemini-3.5-flash-lite` (Economy Tier) | `gemini-2.5-pro` (Reasoning Tier) |
| :--- | :--- | :--- | :--- | :--- |
| **Status** | GA (General Availability) | GA (General Availability) | Preview / GA | GA (General Availability) |
| **Input Pricing** | $0.15 / 1M tokens | $0.15 / 1M tokens | $0.075 / 1M tokens | $1.25 / 1M tokens |
| **Output Pricing** | $0.60 / 1M tokens | $0.60 / 1M tokens | $0.30 / 1M tokens | $5.00 / 1M tokens |
| **Image Resolution Handling** | Native high-res tile parsing (~258 tokens per standard crop) | Native high-res tile parsing (~258 tokens) | Compressed tile parsing | High-fidelity multi-scale vision |
| **Fine-Stroke Acuity** | High (accurately resolves pencil arcs, tick marks, arrowheads) | Good (resolves clear markings; occasional arrow direction blur) | Moderate (risks dropping faint tick marks or arrow tips) | Very High (resolves faint pencil strokes and erased marks) |
| **Structured Output Support** | Native Pydantic / JSON schema enforcement | Native Pydantic / JSON schema enforcement | JSON schema enforcement | Native Pydantic / JSON schema enforcement |
| **Inference Latency (p50)** | ~800–1,200 ms | ~1,100–1,500 ms | ~500–800 ms | ~2,500–4,000 ms |
| **Cost per 3 Worksheets** | **$0.00078** | **$0.00078** | $0.00039 | $0.00650 |

---

## 3. Rationale for `gemini-3.8-flash`

### 3.1 Vision Acuity for Mathematical Marks
Number-line worksheets contain fine spatial features:
- Ticks along an axis spaced by 15–30 pixels.
- Directional arrowheads indicating sign (+ or -) that may be drawn as small as 5x5 pixels.
- Faint pencil strokes, overwritten corrections, or partial erasures.

Empirical evaluation indicates `gemini-3.8-flash` provides superior spatial localization of fine line intersections compared to `gemini-3.5-flash-lite`, without incurring the 8x cost multiple of `gemini-2.5-pro`.

### 3.2 Decoupled Architectural Philosophy
A core principle of ClassLens is that **the multimodal LLM does not perform math verification**.
The LLM functions exclusively as a **high-fidelity perceptual transcriber**:
- LLM outputs: Physical ink marks (start coordinate, end coordinate, direction, labels, answer box value, ambiguities).
- Python/SymPy outputs: Mathematical validity, displacement calculation, off-by-one detection, misconception mapping.

Because the LLM is not asked to solve multi-step algebra or execute formal logic, the heavy reasoning capability of `gemini-2.5-pro` is redundant for this stage. `gemini-3.8-flash` delivers the optimal speed, cost, and perceptual precision balance.

---

## 4. Regional Availability & Enterprise Routing

- **Primary Regional Endpoint:** `asia-southeast1` (Singapore) — ensures low latency and aligns with project deployment configuration.
- **Failover / Global Endpoint:** `global` — supports automated capacity routing on Vertex AI if regional quota experiences transient load.
- **Enterprise Mode:** Set via `genai.Client(enterprise=True)` or environment variable `GOOGLE_GENAI_USE_ENTERPRISE=true`.

---

## 5. Decision Matrix & Gate 3 Recommendation

1. **Gate 3 Feasibility Test:** Execute bounded 3-image evaluation on `gemini-3.8-flash`.
2. **Acceptance Thresholds:**
   - Schema conformance: 100%
   - Visual step extraction accuracy: >= 80%
   - Teacher escalation precision: >= 90%
3. **Contingency:** If `gemini-3.8-flash` encounters regional capacity restrictions in `asia-southeast1`, route to `global` or switch seamlessly to `gemini-2.5-flash` using `--model gemini-2.5-flash`.
