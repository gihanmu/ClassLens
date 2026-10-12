# ClassLens — Financial & External Operations Authorization Policy

## 1. Safety Defaults

```ini
DEFAULT_EXTERNAL_SPENDING_LIMIT_USD=0.00
USER_APPROVAL_THRESHOLD_USD=0.50
```

- **Deny-by-Default:** Real Gemini calls, Vertex AI requests, paid cloud infrastructure deployment, and production database migrations are completely disabled by default.
- **Authorization Limit vs Cloud Hard Cap:** These settings represent strict local authorization policy enforced outside any coding agent or LLM. They are not cloud billing hard caps.
- **No Automatic Spend:** The `$0.50` threshold is **NOT** permission to spend up to `$0.50` automatically. Any task requesting external inference or cost > `$0.00` must have an explicit, cryptographically verifiable or pre-authorized token file in this directory.

---

## 2. Authorization Token Schema

To grant permission for a specific future operation (e.g. a bounded 3-call Gemini evaluation), the authorized engineer must create an approval file in this directory:

`automation/approvals/<token_id>.json`

### Required Fields:
```json
{
  "token_id": "APPRV-20261012-GEMINI-GATE3C",
  "provider": "google-vertex-ai",
  "purpose": "Feasibility evaluation of 3 synthetic student number-line worksheets",
  "max_authorized_calls": 3,
  "authorized_cost_usd": 0.05,
  "expires_at": "2026-10-12T12:00:00Z",
  "approved_by": "gihanmu",
  "allowed_models": [
    "gemini-3.8-flash"
  ],
  "allowed_regions": [
    "global"
  ]
}
```

---

## 3. Enforcement Mechanism

The autonomous runner's `SafetyEnforcer` (`automation/runner/safety.py`) verifies:
1. The approval file exists on disk in `automation/approvals/`.
2. The current UTC time is strictly before `expires_at`.
3. The requested task cost does not exceed `authorized_cost_usd`.
4. The provider and models match authorized boundaries.

If any check fails, the runner immediately halts with `SafetyViolationError` and zero network requests are made.
