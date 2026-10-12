"""Configuration constants and safety policies for ClassLens autonomous development."""

from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOMATION_ROOT = REPO_ROOT / "automation"
TASKS_DIR = AUTOMATION_ROOT / "tasks"
SCHEMA_PATH = TASKS_DIR / "schema" / "task_schema.json"
REPORTS_DIR = AUTOMATION_ROOT / "reports"
APPROVALS_DIR = AUTOMATION_ROOT / "approvals"
QUEUE_DIR = AUTOMATION_ROOT / "queue"
QUEUE_STATE_FILE = QUEUE_DIR / "queue_state.json"
QUEUE_LOCK_FILE = QUEUE_DIR / "runner.lock"

# Mandatory Safety Policy (Authorization limits, NOT cloud hard caps)
DEFAULT_EXTERNAL_SPENDING_LIMIT_USD: float = 0.00
USER_APPROVAL_THRESHOLD_USD: float = 0.50

# Provider risk classification:
# agy binary (1.3.3) does NOT provide an OS-level or provider-side enforceable overage cap.
# Any live external usage requires conservative human-in-the-loop authorization.
PROVIDER_OVERAGE_CAP_ENFORCEABLE: bool = False

# Isolation settings
ISOLATION_SEATBELT_ENABLED: bool = True

# Task Queue Lifecycle States
STATE_PENDING = "PENDING"
STATE_PREFLIGHT = "PREFLIGHT"
STATE_RUNNING = "RUNNING"
STATE_VERIFYING = "VERIFYING"
STATE_PR_CREATED = "PR_CREATED"
STATE_COMPLETE = "COMPLETE"
STATE_BLOCKED = "BLOCKED"
STATE_FAILED = "FAILED"
STATE_AWAITING_APPROVAL = "AWAITING_APPROVAL"
STATE_RETRYING = "RETRYING"

VALID_QUEUE_STATES = [
    STATE_PENDING,
    STATE_PREFLIGHT,
    STATE_RUNNING,
    STATE_VERIFYING,
    STATE_PR_CREATED,
    STATE_COMPLETE,
    STATE_BLOCKED,
    STATE_FAILED,
    STATE_AWAITING_APPROVAL,
    STATE_RETRYING,
]

# Retry and timeout bounds
MAX_REPAIR_ATTEMPTS: int = 3
DEFAULT_COMMAND_TIMEOUT_SECONDS: int = 120
DEFAULT_TASK_TIMEOUT_SECONDS: int = 600

# Protected Files and Patterns (The coding agent or runner may NEVER modify these)
PROTECTED_FILE_PATTERNS = [
    ".env*",
    "*.key",
    "*.pem",
    "*credentials*.json",
    "*service-account*.json",
    "automation/runner/*",
    "automation/approvals/*.json",
    "automation/queue/runner.lock",
    ".github/workflows/*",
    ".git/*",
]

# Prohibited Operations (Commands that could mutate infrastructure, deploy, or exfiltrate)
PROHIBITED_COMMAND_PATTERNS = [
    "gcloud run deploy",
    "gcloud container",
    "gcloud compute",
    "gcloud auth",
    "terraform apply",
    "terraform destroy",
    "rm -rf /",
    "git push --force",
    "git push -f",
    "git reset --hard origin/main",
    "curl .*https?://",
    "wget .*https?://",
    "nc -",
    "CLASSLENS_AI_MODE=live",
]
