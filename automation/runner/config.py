"""Configuration constants and safety policies for ClassLens autonomous development workflow."""

from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOMATION_ROOT = REPO_ROOT / "automation"
TASKS_DIR = AUTOMATION_ROOT / "tasks"
SCHEMA_PATH = TASKS_DIR / "schema" / "task_schema.json"
REPORTS_DIR = AUTOMATION_ROOT / "reports"
APPROVALS_DIR = AUTOMATION_ROOT / "approvals"

# Mandatory Safety Policy (Authorization limits, NOT cloud hard caps)
DEFAULT_EXTERNAL_SPENDING_LIMIT_USD: float = 0.00
USER_APPROVAL_THRESHOLD_USD: float = 0.50

# Retry and timeout bounds
MAX_REPAIR_ATTEMPTS: int = 3
DEFAULT_COMMAND_TIMEOUT_SECONDS: int = 120

# Protected Files and Patterns (The coding agent or runner may NEVER modify these)
PROTECTED_FILE_PATTERNS = [
    ".env*",
    "*.key",
    "*.pem",
    "*credentials*.json",
    "*service-account*.json",
    "automation/runner/*",
    "automation/approvals/*.json",
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
