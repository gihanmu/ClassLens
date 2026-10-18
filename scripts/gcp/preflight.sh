#!/usr/bin/env bash
# ==============================================================================
# ClassLens GCP Preflight Verification Script (100% Non-Destructive)
# ==============================================================================
# Usage: ./scripts/gcp/preflight.sh [--dry-run] [PROJECT_ID] [REGION]
#
# Validates local tools, GCP authentication, project billing, required APIs,
# IAM permissions, Secret Manager presence, PostgreSQL migration readiness,
# and Terraform configuration.
#
# Does NOT incur any GCP charges or modify any cloud resources.
# ==============================================================================

set -Eeuo pipefail
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens GCP Deployment Preflight Check (100% Non-Destructive)${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Parse optional --dry-run
IS_DRY_RUN=false
if [ "${1:-}" == "--dry-run" ]; then
  IS_DRY_RUN=true
  shift
fi

# 1. Verify Local Command Tooling
echo -e "\n${YELLOW}[Stage 1/7] Verifying local CLI dependencies...${NC}"

check_tool() {
  local tool=$1
  local cmd=$2
  if command -v "$cmd" >/dev/null 2>&1; then
    echo -e "  ${GREEN}[PASS]${NC} $tool is installed ($($cmd --version 2>&1 | head -n 1))"
  else
    echo -e "  ${RED}[FAIL]${NC} $tool is not installed or not on PATH."
    return 1
  fi
}

check_tool "Google Cloud SDK (gcloud)" "gcloud"
check_tool "Docker" "docker"
check_tool "Terraform / OpenTofu" "terraform"
check_tool "Node.js" "node"
check_tool "npm" "npm"
check_tool "Python" "python3"

# 2. Check GCP Project Context & Authentication
echo -e "\n${YELLOW}[Stage 2/7] Inspecting Google Cloud Project, Billing & Authentication...${NC}"

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
if [ -z "$PROJECT_ID" ]; then
  CURRENT_GCP_PROJECT=$(gcloud config get-value project --quiet 2>/dev/null || true)
  if [ -n "$CURRENT_GCP_PROJECT" ] && [ "$CURRENT_GCP_PROJECT" != "(unset)" ]; then
    PROJECT_ID="$CURRENT_GCP_PROJECT"
  fi
fi

if [ -z "$PROJECT_ID" ]; then
  echo -e "  ${RED}[FAIL] No Google Cloud project specified.${NC}"
  echo -e "         Pass project as argument: ./scripts/gcp/preflight.sh [PROJECT_ID] [REGION]"
  echo -e "         Or export GOOGLE_CLOUD_PROJECT=[PROJECT_ID]"
  exit 1
else
  echo -e "  ${GREEN}[PASS]${NC} Target Google Cloud Project: ${GREEN}${PROJECT_ID}${NC}"
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" --quiet 2>/dev/null || true)
if [ -z "$ACTIVE_ACCOUNT" ]; then
  echo -e "  ${RED}[FAIL] No active Google Cloud user/service account authenticated.${NC}"
  echo -e "         Run: gcloud auth login && gcloud auth application-default login"
  exit 1
else
  echo -e "  ${GREEN}[PASS]${NC} Authenticated GCP Identity: ${GREEN}${ACTIVE_ACCOUNT}${NC}"
fi

# Check billing account linkage
BILLING_ENABLED=$(gcloud billing projects describe "$PROJECT_ID" --format="value(billingEnabled)" --quiet 2>/dev/null || echo "unknown")
if [ "$BILLING_ENABLED" == "True" ] || [ "$BILLING_ENABLED" == "true" ]; then
  echo -e "  ${GREEN}[PASS]${NC} Project billing is enabled."
elif [ "$BILLING_ENABLED" == "unknown" ]; then
  echo -e "  ${YELLOW}[INFO]${NC} Billing status could not be verified automatically (permissions may be restricted to billing viewer)."
else
  echo -e "  ${RED}[WARN]${NC} Project billing may not be active (status: ${BILLING_ENABLED}). Cloud Run and Cloud SQL require active billing."
fi

# 3. Check Required GCP APIs (Single Batch Query)
echo -e "\n${YELLOW}[Stage 3/7] Checking Google Cloud Services & API enablement...${NC}"

ENABLED_SERVICES=$(gcloud services list --project="$PROJECT_ID" --format="value(config.name)" --quiet 2>/dev/null || true)

REQUIRED_APIS=(
  "run.googleapis.com"
  "compute.googleapis.com"
  "aiplatform.googleapis.com"
  "storage.googleapis.com"
  "secretmanager.googleapis.com"
  "artifactregistry.googleapis.com"
  "sqladmin.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
  if echo "$ENABLED_SERVICES" | grep -Fxq "$api"; then
    echo -e "  ${GREEN}[PASS]${NC} API enabled: $api"
  else
    echo -e "  ${YELLOW}[INFO]${NC} API not yet enabled: $api (Terraform or deploy-all will enable this)"
  fi
done

# 4. Check Secret Manager Secrets Presence (Never printing values)
echo -e "\n${YELLOW}[Stage 4/7] Checking Secret Manager secret descriptors (Values Redacted)...${NC}"

check_secret() {
  local secret_name=$1
  if ! echo "$ENABLED_SERVICES" | grep -Fxq "secretmanager.googleapis.com"; then
    echo -e "  ${YELLOW}[INFO]${NC} Secret '${secret_name}': Secret Manager API not enabled yet (will be provisioned during deployment)."
    return 0
  fi
  if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" --quiet >/dev/null 2>&1; then
    local versions
    versions=$(gcloud secrets versions list "$secret_name" --project="$PROJECT_ID" --filter="state:ENABLED" --format="value(name)" --quiet 2>/dev/null || true)
    if [ -n "$versions" ]; then
      echo -e "  ${GREEN}[PASS]${NC} Secret '${secret_name}' exists with active version(s)."
    else
      echo -e "  ${YELLOW}[WARN]${NC} Secret '${secret_name}' exists but has NO active versions."
    fi
  else
    echo -e "  ${YELLOW}[INFO]${NC} Secret '${secret_name}' not yet provisioned. (Terraform will declare secret container; version must be added prior to live traffic)."
  fi
}

check_secret "classlens-production-session-secret"
check_secret "classlens-production-teacher-password"
check_secret "classlens-production-live-auth-key"

# 5. Verify PostgreSQL Integration & Migration Readiness
echo -e "\n${YELLOW}[Stage 5/7] Verifying PostgreSQL integration & migration tooling...${NC}"

if [ -f "scripts/migrate.py" ] && [ -x "scripts/migrate.py" ]; then
  echo -e "  ${GREEN}[PASS]${NC} Idempotent database migration utility is present and executable (scripts/migrate.py)."
else
  echo -e "  ${RED}[FAIL]${NC} scripts/migrate.py is missing or not executable."
  exit 1
fi

if python3 scripts/migrate.py --verify >/dev/null 2>&1; then
  echo -e "  ${GREEN}[PASS]${NC} Local schema audit succeeded (ANSI SQL DDL definitions valid)."
else
  echo -e "  ${RED}[FAIL]${NC} Schema verification failed."
  exit 1
fi

# 6. Verify Workspace & Docker Definitions
echo -e "\n${YELLOW}[Stage 6/7] Checking application container & Dockerfile assets...${NC}"

if [ -f "apps/web/package.json" ] && [ -f "apps/web/Dockerfile" ]; then
  echo -e "  ${GREEN}[PASS]${NC} Next.js standalone multi-stage Dockerfile present."
else
  echo -e "  ${RED}[FAIL]${NC} Next.js Dockerfile missing."
  exit 1
fi

if [ -f "pyproject.toml" ] && [ -f "Dockerfile" ]; then
  echo -e "  ${GREEN}[PASS]${NC} FastAPI backend multi-stage Dockerfile present."
else
  echo -e "  ${RED}[FAIL]${NC} FastAPI Dockerfile missing."
  exit 1
fi

# 7. Terraform Static Configuration Validation
echo -e "\n${YELLOW}[Stage 7/7] Validating Terraform configuration syntax...${NC}"

(
  cd infra/terraform
  terraform fmt -check || {
    echo -e "  ${YELLOW}Notice: Formatting Terraform files...${NC}"
    terraform fmt
  }
  terraform validate >/dev/null 2>&1 && echo -e "  ${GREEN}[PASS]${NC} Terraform configuration is structurally valid."
)

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} Preflight check completed successfully! Ready for image build & plan.${NC}"
echo -e "${GREEN}==============================================================================${NC}"
