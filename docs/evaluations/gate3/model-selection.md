# ClassLens — Gate 3 Multimodal Model Selection & Architecture Analysis (Corrected)

## 1. Executive Summary & Verification Context

Gate 3 evaluates whether Google Gemini can accurately reconstruct handwritten mathematical marks from student number-line worksheets with sufficient fidelity to feed the ClassLens deterministic SymPy verification engine.

Per explicit engineering review guidelines:
- We do **not** assume `gemini-3.8-flash` is generally available or universally accessible across all Google Cloud environments.
- We evaluate the verified model catalog on Google Cloud Vertex AI, distinguishing between stable GA models, deprecation schedules, and preview/future models.
- **Primary Recommendation:** **`gemini-2.5-flash`** (or stable baseline **`gemini-1.5-flash`** / **`gemini-2.0-flash`**).
- **Data Residency & Regional Policy:** Strictly bound to **`asia-southeast1`** (Singapore). **Automatic fallback to the global endpoint is prohibited and disabled.** Any change of region requires explicit human authorization.

---

## 2. Verified Vertex AI Model Comparison & Actual Pricing

| Model Identifier | Status on Vertex AI | Input Price (per 1M tokens) | Output Price (per 1M tokens) | Multimodal Image Support | Recommended Use |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`gemini-2.5-flash`** *(Recommended)* | Current Generation GA | **$0.30 USD** | **$2.50 USD** | Yes (Native tile encoding) | Primary candidate for Gate 3 multimodal transcription. Balanced latency and visual acuity. |
| **`gemini-1.5-flash`** *(Stable Baseline)* | GA (Long-term baseline) | **$0.075 USD** *(<=128k context)* | **$0.30 USD** | Yes (High-res tile encoding) | Cost-optimized alternative with proven multi-region stability. |
| **`gemini-2.0-flash`** | GA / Active | **$0.10 USD** | **$0.40 USD** | Yes (Fast multimodal) | Intermediate generation for high-throughput testing. |
| **`gemini-3.8-flash`** *(Conditional)* | Agent Platform (Introductory) | **$0.75 USD** *(Introductory)* | **$3.75 USD** *(Introductory)* | Yes | Requires verification of project-level enablement before execution. |

*Note: Pricing reflects published Google Cloud Vertex AI token rates as of late 2026. Local software cost calculations represent mathematical estimates based on these rates; they do not constitute a Google Cloud billing account quota.*

---

## 3. Architectural Rationale for Decoupled Perception

A core principle of ClassLens is that **the multimodal model does not perform mathematical verification or student grading**:
1. **Model Scope:** Performs objective perceptual extraction of physical ink strokes:
   - Start coordinate, end coordinate, directionality (`left_negative`, `right_positive`, `ambiguous`).
   - Arrowhead visibility (`true` / `false`).
   - Written magnitude labels (e.g. `"-6"`, `"+12"`).
   - Answer box text / circled results.
   - Visual ambiguities and legibility flags.
2. **Deterministic SymPy Scope:** Evaluates mathematical reasoning:
   - Compares observed step displacements: $\Delta = \text{end} - \text{start}$.
   - Detects off-by-one errors and computational deviations.
   - Decouples answer correctness from reasoning correctness.
   - Classifies pedagogical misconceptions based strictly on physical evidence.

Because the model is not executing symbolic mathematics, high-cost reasoning models (such as `gemini-2.5-pro` at $1.25/$5.00 per 1M) are unnecessary for this perceptual transcription stage.

---

## 4. Strict Regional Policy & SDK Configuration

- **Target Region:** `asia-southeast1` (Singapore regional endpoint: `asia-southeast1-aiplatform.googleapis.com`).
- **Zero Automatic Global Failover:** In previous drafts, automatic failover to `global` was described. This has been **removed**. The adapter strictly targets `asia-southeast1`. If regional capacity throttling occurs, the call will fail cleanly rather than automatically routing data outside Singapore.
- **SDK Initialization:** Initialized using the official `google-genai` SDK with standard, supported parameters:
  ```python
  from google import genai

  client = genai.Client(
      vertexai=True,
      location="asia-southeast1",
      project=project_id,  # Optional; auto-detected from ADC
  )
  ```
  Unsupported parameters (such as `enterprise=True`) have been removed from the client constructor.
