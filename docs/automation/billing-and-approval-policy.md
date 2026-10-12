# ClassLens — Autonomous Billing & Approval Policy

**Document Version:** 1.0.0  
**Phase:** Gate AUTO-1 (Secure Autonomous Development Execution)  
**System:** ClassLens Autonomous Development Infrastructure  
**Authority:** Principal DevSecOps & Platform Architect  

---

## 1. Mandatory Spending Policy

The ClassLens Autonomous Development Workflow operates under a strict **deny-by-default financial safety policy**:

```dotenv
DEFAULT_EXTERNAL_SPENDING_LIMIT_USD=0.00
USER_APPROVAL_THRESHOLD_USD=0.50
```

### Critical Policy Interpretation Rules:
1. **Zero Unapproved Spend:** The default authorized external cloud spend for any automated task is strictly **$0.00 USD**.
2. **Threshold Is NOT an Allowance:** The `$0.50 USD` threshold is **NOT** automatic permission to spend up to $0.50. It represents the boundary above which executive-level human approval is mandatory.
3. **No Automatic Bypasses:** The runner will never bypass, override, or self-authorize external metered cloud operations.
4. **Offline First:** All development, testing, builds, evaluation, and quality verification must execute offline using deterministic mocks.

---

## 2. Coding-Agent Allowance vs. Separately Billed Cloud Charges

A crucial distinction exists between **included coding-agent usage** and **separately metered cloud infrastructure charges**:

```
+---------------------------------------------------------------------------------------------------+
|                                     FINANCIAL TAXONOMY MATRIX                                     |
+------------------------------------+----------------------------------+---------------------------+
| Category                           | Provider & Billing Model         | Autonomous Policy Status  |
+------------------------------------+----------------------------------+---------------------------+
| Antigravity Coding Agent (agy)     | Google Plan Included Allowance   | PERMITTED within bounds   |
| Vertex AI Gemini Inference API     | Google Cloud Pay-as-you-go       | STRICTLY PROHIBITED ($0)  |
| Cloud Run Deployments              | Google Cloud Serverless Compute  | STRICTLY PROHIBITED ($0)  |
| Cloud Storage (GCS) Buckets        | Google Cloud Object Storage      | STRICTLY PROHIBITED ($0)  |
| Third-Party Metered APIs           | External Pay-as-you-go APIs      | STRICTLY PROHIBITED ($0)  |
+------------------------------------+----------------------------------+---------------------------+
```

### Permitted Without Separate Charges:
- Antigravity coding-agent code synthesis and edits within the user's verified included plan allowance.
- Local execution of Python tests (`pytest tests/`).
- Local compilation and production builds of Next.js (`npm run build`).
- Git commits, branch creation, and local git operations.
- GitHub pull request creation via `gh pr create`.
- GitHub Actions CI execution within standard repository quotas.

### Strictly Prohibited Without Explicit Human Approval Token:
- Live Gemini API calls from the ClassLens application (`CLASSLENS_AI_MODE=live`).
- Direct Vertex AI inference requests (`aiplatform.googleapis.com`).
- Paid cloud infrastructure provisioning (`terraform apply`).
- Cloud Run service deployment (`gcloud run deploy`).
- Any billable third-party external API requests.

---

## 3. Provider Quota & Overage Risk Classification

### Technical Audit of Antigravity CLI (`agy` 1.3.3):
An independent inspection of the binary `/Users/gihanmu/.local/bin/agy` revealed:
- `agy` connects over TLS to Google's internal model endpoints to service prompts.
- `agy` **does NOT provide an OS-level token meter, remaining quota command, or programmatic hard tripwire**.
- The CLI options (`--help`) include flags for model selection, sandboxing, and output formatting, but no flags for budget limits (e.g. `--max-spend` or `--budget-limit`).

### Formal Risk Determination:
Because the provider CLI exposes **no enforceable client-side or provider-side overage cap**, the risk of accidental overage charges is classified as **UNRESOLVED AT THE PROVIDER LEVEL**.

### Enforced Platform Countermeasures:
To mitigate this provider limitation, the ClassLens orchestrator enforces:
1. **Conservative Approval Boundary:** Any autonomous invocation of `AgyCliAgentRunner` (`--runner agy`) requires an explicit, cryptographically signed approval token in `automation/approvals/`.
2. **Deterministic Fallback Default:** The default runner engine is `DeterministicAgentRunner` (`--runner deterministic`), which guarantees 100% offline execution with $0.00 spend.
3. **Turn Limits & Wall Clocks:** Real agent invocations are bound by a maximum turn limit (1 turn per task, 3 bounded repair attempts) and a strict 600-second execution timeout.

---

## 4. Cryptographic Approval Token Specification

To authorize any task requesting external inference or metered usage, a human authorizer must create a JSON approval token file in `automation/approvals/{token_id}.json`.

### Token JSON Schema:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ClassLensApprovalToken",
  "type": "object",
  "required": [
    "token_id",
    "provider",
    "purpose",
    "max_authorized_calls",
    "authorized_cost_usd",
    "expires_at",
    "approved_by",
    "hmac_signature"
  ],
  "properties": {
    "token_id": { "type": "string" },
    "provider": { "type": "string" },
    "purpose": { "type": "string" },
    "max_authorized_calls": { "type": "integer", "minimum": 1 },
    "authorized_cost_usd": { "type": "number", "minimum": 0.01 },
    "expires_at": { "type": "string", "format": "date-time" },
    "approved_by": { "type": "string" },
    "scoped_task_id": { "type": "string" },
    "hmac_signature": { "type": "string" }
  }
}
```

### Verification Checks Performed by `SafetyEnforcer`:
1. **Anti-Forgery Signature:** HMAC-SHA256 signature generated over canonical string `token_id:provider:purpose:calls:cost:expires_at:scoped_task_id` using host authority secret `CLASSLENS_APPROVAL_SECRET`.
2. **Task-Scoping:** If `scoped_task_id` is set (e.g. `TASK-001`), the token cannot be reused for any other task.
3. **Expiration:** ISO-8601 UTC timestamp check ensures expired tokens are rejected.
4. **Replay & Call Counting:** An internal counter tracks token usage; calls beyond `max_authorized_calls` are rejected.
5. **Cost Capping:** The task's `requested_cost` must not exceed `authorized_cost_usd`.
