# ClassLens — Gate 3 Cost Estimation & Accounting Details (Corrected)

## 1. Rate Schedule & Cost Distinction

> [!IMPORTANT]
> The figures presented below are **local software estimates** calculated mathematically from published Google Cloud Vertex AI token rates. They represent an offline budgeting calculation and software-level circuit breaker, **not a guaranteed Google Cloud billing account quota or hard cap**. Actual billing is determined exclusively by Google Cloud invoicing.

### Published Rate Comparison (per 1,000,000 tokens)

| Model | Input Rate (USD) | Output Rate (USD) |
| :--- | :--- | :--- |
| **`gemini-2.5-flash`** *(Recommended Default)* | $0.300000 | $2.500000 |
| **`gemini-1.5-flash`** *(Cost-Optimized)* | $0.075000 | $0.300000 |
| **`gemini-2.0-flash`** | $0.100000 | $0.400000 |
| **`gemini-3.8-flash`** *(Introductory)* | $0.750000 | $3.750000 |

---

## 2. Projected Token Consumption for Bounded 3-Case Run

- **Image Multimodal Tokens:** ~258 tokens per 1000x500 image crop.
- **System Instructions & Schema:** ~200 text input tokens.
- **Estimated Input per Case:** ~458 tokens $\times$ 3 cases = **1,374 input tokens**.
- **Estimated Output per Case:** ~320 tokens $\times$ 3 cases = **960 output tokens**.

### Estimated Software Cost by Model

1. **`gemini-2.5-flash` (Recommended):**
   $$\text{Input Cost} = 1,374 \times \$0.000000300 = \$0.000412$$
   $$\text{Output Cost} = 960 \times \$0.000002500 = \$0.002400$$
   $$\mathbf{\text{Total Estimated Software Cost}} = \mathbf{\$0.002812 \text{ USD}}$$

2. **`gemini-1.5-flash` (Baseline):**
   $$\text{Input Cost} = 1,374 \times \$0.000000075 = \$0.000103$$
   $$\text{Output Cost} = 960 \times \$0.000000300 = \$0.000288$$
   $$\mathbf{\text{Total Estimated Software Cost}} = \mathbf{\$0.000391 \text{ USD}}$$

3. **`gemini-3.8-flash` (If enabled on Agent Platform):**
   $$\text{Input Cost} = 1,374 \times \$0.000000750 = \$0.001031$$
   $$\text{Output Cost} = 960 \times \$0.000003750 = \$0.003600$$
   $$\mathbf{\text{Total Estimated Software Cost}} = \mathbf{\$0.004631 \text{ USD}}$$

---

## 3. Software Safety Guardrails (Not Billing Caps)

- **Hard Call Ceiling:** The evaluation adapter enforces a software circuit breaker of `--max-calls 3`.
- **Zero Retries:** No hidden retry loop; each worksheet receives at most 1 call.
- **Budget Threshold:** A local warning threshold of $0.010000 USD is monitored in software. If estimated local cost exceeds this threshold, the script issues a warning.
