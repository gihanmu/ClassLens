# ClassLens — Gate 3 Cost Estimation & Token Budgeting

## 1. Rate Schedule (Google Cloud Vertex AI / GenAI SDK)

The Gate 3 evaluation uses `gemini-3.8-flash` (or `gemini-2.5-flash`), with standard multimodal API pricing:

| Item | Rate per 1,000,000 Tokens | Cost per Token |
| :--- | :--- | :--- |
| **Input Tokens (Text & Image)** | $0.150000 USD | $0.000000150 USD |
| **Output Tokens (JSON Schema)** | $0.600000 USD | $0.000000600 USD |

---

## 2. Token Consumption Per Image Worksheet

- **Image Multimodal Token Cost:** Standard resolution number-line image (1000x500 pixels) consumes ~258 input tokens in Gemini tile encoding.
- **System Prompt & Instructions:** ~200 text input tokens.
- **Total Input Tokens Per Image:** ~458 tokens.
- **Structured JSON Output:** Detailed `GeminiVisualEvidenceSchema` response (3 hops, coordinates, labels, description, quality) produces ~320 output tokens.

---

## 3. Projected Budget for Bounded 3-Case Feasibility Test

| Component | Quantity | Tokens per Unit | Total Tokens | Rate USD | Subtotal USD |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Input Tokens | 3 worksheets | 458 tokens | 1,374 tokens | $0.15 / 1M | **$0.000206** |
| Output Tokens | 3 worksheets | 320 tokens | 960 tokens | $0.60 / 1M | **$0.000576** |
| **Total Estimated Run Cost** | — | — | **2,334 tokens** | — | **$0.000782** |

---

## 4. Safety Margins and Hard Caps

- **Authorized Cost Ceiling:** $0.010000 USD (1 cent USD).
- **Buffer Ratio:** Projected cost ($0.000782) is less than **8%** of the $0.01 authorized ceiling.
- **Hard Call Ceiling:** `--max-calls 3` prevents accidental repeated or looped invocations.
- **Max Output Token Ceiling:** `--max-output-tokens 2048` limits maximum response length per request.
