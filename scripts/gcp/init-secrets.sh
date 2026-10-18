#!/usr/bin/env bash
# ==============================================================================
# ClassLens GCP Secret Manager Bootstrap & Initialization Utility
# Safely initializes required Secret Manager containers and secret versions
# without ever logging, echoing, or committing secret values.
#
# Usage:
#   ./scripts/gcp/init-secrets.sh [--dry-run] [PROJECT_ID]
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[PASS]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[FAIL]${NC} $*" >&2; }

DRY_RUN="false"
POSITIONAL_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN="true"
      ;;
    *)
      POSITIONAL_ARGS+=("$arg")
      ;;
  esac
done

PROJECT_ID="${POSITIONAL_ARGS[0]:-${GOOGLE_CLOUD_PROJECT:-precise-equator-511303-m1}}"

REQUIRED_SECRETS=(
  "classlens-production-session-secret"
  "classlens-production-teacher-password"
  "classlens-production-live-auth-key"
)

echo "=============================================================================="
echo " ClassLens Secret Manager Initialization (Project: ${PROJECT_ID})"
if [[ "$DRY_RUN" == "true" ]]; then
  echo " Mode: DRY-RUN (Read-only inspection; zero mutations)"
fi
echo "=============================================================================="

SM_API_ENABLED=$(gcloud services list --enabled \
  --project="$PROJECT_ID" \
  --filter="config.name=secretmanager.googleapis.com" \
  --format="value(config.name)" \
  --quiet 2>/dev/null || echo "")

if [[ -z "$SM_API_ENABLED" ]]; then
  if [[ "$DRY_RUN" == "true" ]]; then
    log_warn "[DRY-RUN] Secret Manager API (secretmanager.googleapis.com) is not enabled yet on '${PROJECT_ID}'."
    for sec in "${REQUIRED_SECRETS[@]}"; do
      log_warn "[DRY-RUN] Secret '${sec}' will be created and populated once Secret Manager API is enabled."
    done
    echo "=============================================================================="
    log_ok "Secret Manager dry-run inspection complete."
    echo "=============================================================================="
    exit 0
  fi
  log_info "Enabling Secret Manager API (secretmanager.googleapis.com)..."
  gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID" --quiet
fi

ensure_secret_container() {
  local sec_name="$1"
  if gcloud secrets describe "$sec_name" --project="$PROJECT_ID" --quiet >/dev/null 2>&1; then
    log_ok "Secret container '${sec_name}' exists."
  else
    if [[ "$DRY_RUN" == "true" ]]; then
      log_warn "[DRY-RUN] Secret container '${sec_name}' does not exist yet."
      return 0
    fi
    log_info "Creating secret container '${sec_name}'..."
    gcloud secrets create "$sec_name" \
      --project="$PROJECT_ID" \
      --replication-policy="automatic" \
      --labels="environment=production,managed_by=terraform" \
      --quiet
    log_ok "Created secret container '${sec_name}'."
  fi
}

has_enabled_version() {
  local sec_name="$1"
  local enabled_ver
  enabled_ver=$(gcloud secrets versions list "$sec_name" \
    --project="$PROJECT_ID" \
    --filter="state=ENABLED" \
    --limit=1 \
    --format="value(name)" \
    --quiet 2>/dev/null || echo "")
  [[ -n "$enabled_ver" ]]
}

for sec in "${REQUIRED_SECRETS[@]}"; do
  ensure_secret_container "$sec"

  if gcloud secrets describe "$sec" --project="$PROJECT_ID" --quiet >/dev/null 2>&1 && has_enabled_version "$sec"; then
    log_ok "Secret '${sec}' already has an ENABLED version (preserving existing version)."
    continue
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    log_warn "[DRY-RUN] Secret '${sec}' has no ENABLED version yet. Run without --dry-run to initialize."
    continue
  fi

  case "$sec" in
    "classlens-production-session-secret")
      log_info "Generating cryptographically random 256-bit HMAC session secret for '${sec}'..."
      openssl rand -hex 32 | tr -d '\n' | gcloud secrets versions add "$sec" \
        --project="$PROJECT_ID" \
        --data-file=- \
        --quiet >/dev/null
      log_ok "Populated initial ENABLED version for '${sec}' (value never logged)."
      ;;

    "classlens-production-live-auth-key")
      log_info "Generating cryptographically random 256-bit live inference authorization key for '${sec}'..."
      openssl rand -hex 32 | tr -d '\n' | gcloud secrets versions add "$sec" \
        --project="$PROJECT_ID" \
        --data-file=- \
        --quiet >/dev/null
      log_ok "Populated initial ENABLED version for '${sec}' (value never logged)."
      ;;

    "classlens-production-teacher-password")
      if [[ -z "${CLASSLENS_INIT_TEACHER_PASSWORD:-}" ]] && [[ -f ".env" ]]; then
        CLASSLENS_INIT_TEACHER_PASSWORD=$(python3 -c '
with open(".env") as f:
    for line in f:
        s = line.strip()
        if s.startswith("CLASSLENS_DEMO_PASSWORD="):
            val = s.split("=", 1)[1].strip().strip("\x27\"")
            if val:
                print(val, end="")
            break
' 2>/dev/null || true)
      fi
      if [[ -n "${CLASSLENS_INIT_TEACHER_PASSWORD:-}" ]]; then
        log_info "Populating '${sec}' from configured local teacher password (value redacted)..."
        printf '%s' "$CLASSLENS_INIT_TEACHER_PASSWORD" | gcloud secrets versions add "$sec" \
          --project="$PROJECT_ID" \
          --data-file=- \
          --quiet >/dev/null
        unset CLASSLENS_INIT_TEACHER_PASSWORD
        log_ok "Populated initial ENABLED version for '${sec}' (value never logged)."
      elif [[ -t 0 ]]; then
        echo ""
        log_info "Action Required: Set production password for teacher@classlens.demo ('${sec}')."
        while true; do
          read -rsp "  Enter teacher password (min 10 chars, input hidden): " teacher_pw
          echo ""
          if [[ "${#teacher_pw}" -lt 10 ]]; then
            log_warn "Password must be at least 10 characters. Please try again."
            continue
          fi
          read -rsp "  Confirm teacher password (input hidden): " teacher_pw_confirm
          echo ""
          if [[ "$teacher_pw" != "$teacher_pw_confirm" ]]; then
            log_warn "Passwords did not match. Please try again."
            continue
          fi
          break
        done
        printf '%s' "$teacher_pw" | gcloud secrets versions add "$sec" \
          --project="$PROJECT_ID" \
          --data-file=- \
          --quiet >/dev/null
        unset teacher_pw teacher_pw_confirm
        log_ok "Populated initial ENABLED version for '${sec}' (value never logged)."
      else
        log_error "Secret '${sec}' has no ENABLED version and terminal is non-interactive."
        log_error "Run './scripts/gcp/init-secrets.sh ${PROJECT_ID}' interactively or set CLASSLENS_INIT_TEACHER_PASSWORD."
        exit 1
      fi
      ;;
  esac
done

echo "=============================================================================="
log_ok "Secret Manager verification/initialization complete."
echo "=============================================================================="
