# ClassLens — Autonomous Development Workflow Architecture & Runbook

**Document:** `docs/automation/autonomous-development.md`  
**System:** ClassLens Autonomous Development Orchestration Framework  
**Safety Status:** Strictly Enforced ($0.00 Default External Spending Policy)  

---

## 1. System Architecture

The ClassLens Autonomous Development Workflow bridges high-level development specifications and reproducible, verified software delivery. It eliminates repeated manual prompt copying and reporting by standardizing task definitions, verification loops, safety gates, and automated Git lifecycle operations.

```
+---------------------------------------------------------------------------------------------------+
|                                  APPROVED TASK SPECIFICATION                                       |
|                               (automation/tasks/TASK-*.yaml)                                      |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                    SAFETY ENFORCEMENT LAYER                                       |
|                                (automation/runner/safety.py)                                      |
|                                                                                                   |
|  - Check Spending Limits: DEFAULT_EXTERNAL_SPENDING_LIMIT_USD = $0.00                              |
|  - Verify Approval Token: If external inference requested, check automation/approvals/<token>.json|
|  - Protect Critical Files: .env, credentials, safety.py, .git                                     |
|  - Reject Paid Provisioning: Cloud deploys & terraform apply prohibited                           |
+---------------------------------------------------------------------------------------------------+
                                                  | Pass
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                    GIT BRANCH ORCHESTRATION                                       |
|                                  (automation/runner/git_ops.py)                                    |
|                                                                                                   |
|  - Ensure Clean Working Tree                                                                      |
|  - Create Isolated Feature Branch: feature/<task-id> from latest main                             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      CODING AGENT RUNNER                                          |
|                                (automation/runner/agent_runner.py)                                 |
|                                                                                                   |
|  [Deterministic/Mock Runner]  <-- Default ($0.00)                                                  |
|  [Antigravity CLI (agy)]      <-- Gated: requires explicit approval token & token authorization   |
|                                                                                                   |
|  - Apply Code Modifications strictly within allowed_file_changes                                  |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                   INDEPENDENT QUALITY GATES                                       |
|                                  (automation/runner/verifier.py)                                   |
|                                                                                                   |
|  - Run Task Test Commands: Pytest unit & integration suites                                       |
|  - Run Frontend Build: Next.js 14 production build + TypeScript typecheck                         |
|  - Run Offline Secret Scanner: Scan for exposed API keys and private credentials                  |
|  - Enforce Offline Mock Mode: CLASSLENS_AI_MODE=mock                                              |
+---------------------------------------------------------------------------------------------------+
                               |                             |
                      Fail (Tests Break)            Pass (All Tests Green)
                               |                             |
                               v                             v
+----------------------------------------------+  +-------------------------------------------------+
|             BOUNDED REPAIR LOOP              |  |               GIT & GITHUB DELIVERY             |
|                                              |  |                                                 |
|  - Feed exact failures to repair()           |  |  - Stage allowed files                          |
|  - Max 3 repair attempts                     |  |  - Conventional commit: feat(<task>): ...       |
|  - Re-verify safety & file boundaries        |  |  - Push branch to origin                        |
|  - Re-run quality gates                      |  |  - Create/Update Pull Request via gh CLI        |
|  - Halt on unresolved failures               |  +-------------------------------------------------+
+----------------------------------------------+                             |
                               |                                             |
                               +---------------------+-----------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------+
|                                     REPORTING & AUDIT TRAIL                                       |
|                                  (automation/reports/)                                            |
|                                                                                                   |
|  - JSON: automation/reports/<task_id>_report.json (machine-readable)                              |
|  - Markdown: automation/reports/<task_id>_report.md (human-readable)                              |
|  - Distinguishes observed execution facts from agent assumptions                                  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Supported Agent Runners

| Runner Engine | Execution Surface | External Cost | Prerequisites | Use Case |
|---|---|---|---|---|
| `deterministic` | Local Python / Shell | **$0.00** | None | Offline testing, dry runs, verified regression tasks, CI workflows |
| `agy` | Google Antigravity CLI (`agy --print`) | Bounded (requires approval) | `agy` binary in PATH, unexpired approval token in `automation/approvals/` | Unattended autonomous feature generation using Gemini / Claude |

### Antigravity Integration & Limitations
- **Headless CLI Invocation:** Supported via `agy --print "<prompt>" --mode accept-edits --output-format text`.
- **Graphical Automation Prohibited:** The desktop GUI of Google Antigravity is never automated via fragile OS mouse/keyboard macros.
- **Spending Boundary:** Calling `agy` without an authorized approval file triggers `SafetyViolationError` and halts before making external model calls.

---

## 3. How to Submit Tasks

1. Create a task specification file in `automation/tasks/TASK-<ID>.yaml` conforming to `automation/tasks/schema/task_schema.json`.
2. Define:
   - `task_id`: Unique identifier (e.g. `TASK-001-GATE-4B`).
   - `title` & `objective`: Clear pedagogical and architectural goals.
   - `scope`: Explicit `included` and `excluded` items.
   - `acceptance_criteria`: List of testable assertions.
   - `allowed_file_changes`: Whitelist of glob patterns the agent is permitted to touch.
   - `test_commands`: Commands that must return exit code 0.
   - `cost_restrictions`: Spending caps (`max_cost_usd: 0.00`).
   - `security_restrictions`: Data and credential boundaries.
   - `git_branch_requirements`: Base and target branches.

---

## 4. How to Execute Tasks

### List Available Tasks
```bash
python3 automation/run.py --list-tasks
```

### Dry Run Execution (Safe, Local, Offline)
```bash
python3 automation/run.py --task TASK-000-DRY-RUN --dry-run
```

### Autonomous Task Execution (Local Deterministic Runner)
```bash
python3 automation/run.py --task TASK-000-DRY-RUN
```

### Autonomous Task Execution (Antigravity CLI Runner)
*(Requires pre-authorized token in `automation/approvals/`)*
```bash
python3 automation/run.py --task TASK-001-GATE-4B --runner agy
```

---

## 5. Cost and Security Safeguards

### Mandatory Spending Controls
```ini
DEFAULT_EXTERNAL_SPENDING_LIMIT_USD=0.00
USER_APPROVAL_THRESHOLD_USD=0.50
```
- **Policy Definition:** The settings represent strict authorization boundaries enforced in software, not cloud billing hard caps.
- **Zero Automatic Spending:** The `$0.50` threshold is **NOT** permission to spend up to `$0.50` automatically.
- **Approval Tokens:** Any task with `max_cost_usd > 0.00` or `allow_external_inference: true` must specify an `approval_token` matching a valid file in `automation/approvals/<token_id>.json`.
- **Expiration:** Tokens past their `expires_at` timestamp are immediately rejected.
- **Protected Files:** The runner unconditionally blocks edits to `.env`, credentials, `automation/runner/safety.py`, and git internals.

---

## 6. How to Monitor Progress & Recover from Failures

### Monitoring
- Progress and test command outputs are streamed to stdout.
- Generated reports are placed in `automation/reports/`:
  - `automation/reports/<task_id>_report.json`
  - `automation/reports/<task_id>_report.md`

### Bounded Repair Loop
- If a verification command (e.g., pytest, build) fails, the orchestrator passes the exact stderr/failure details to the agent's repair hook.
- A maximum of **3 repair attempts** are allowed per task.
- If failures persist after 3 attempts, execution halts cleanly with `status: FAILED` to prevent runaway compute or loops.

### Manual Cancellation & Stop
- Interrupt execution at any time using `Ctrl+C`.
- Because branches are isolated, interrupting an execution leaves the base branch (`main`) clean and unaffected.
- To abort and clean up an unfinished feature branch:
  ```bash
  git checkout main
  git branch -D feature/<task-id>
  ```

---

## 7. GitHub Integration & CI Quality Gates

### Pull Request Automation
- On passing all quality gates, `GitOps` uses the authenticated GitHub CLI (`gh`) to create or update a Pull Request targeting `main`.
- The PR description is automatically populated with the task objective, verified acceptance criteria, test counts, and cost audit.

### GitHub Actions CI (`.github/workflows/ci.yml`)
- **`secret-and-safety-scan`:** Scans for leaked keys, tokens, and verifies `CLASSLENS_AI_MODE=mock`.
- **`backend-quality-gates`:** Runs offline pytest suite on Python 3.12.
- **`frontend-quality-gates`:** Runs Next.js 14 production build and TypeScript checks.
- **`autonomous-runner-verification`:** Runs runner self-checks including dry-run and safety rejection tests.
