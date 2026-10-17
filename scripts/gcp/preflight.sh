#!/usr/bin/env bash
# ==============================================================================
# ClassLens GCP Preflight Verification Script (Dry-Run / Safe Check)
# ==============================================================================
# Usage: ./scripts/gcp/preflight.sh [PROJECT_ID]
#
# Performs non-destructive prerequisite and configuration checks.
# Does NOT incur any GCP charges or modify any cloud resources.
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens GCP Deployment Preflight Check (100% Non-Destructive)${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# 1. Verify Local Command Tooling
echo -e "\n${YELLOW}[1/5] Verifying local CLI dependencies...${NC}"

check_tool() {
  local tool=$1
  local cmd=$2
  if command -v "$cmd" >/dev/null 2>&1; then
    echo -e "  [PASS] $tool is installed ($($cmd --version 2>&1 | head -n 1))"
  else
    echo -e "  ${RED}[FAIL] $tool is not installed or not on PATH.${NC}"
    return 1
  fi
}

check_tool "Google Cloud SDK (gcloud)" "gcloud"
check_tool "Docker" "docker"
check_tool "Terraform / OpenTofu" "terraform"
check_tool "Node.js" "node"
check_tool "npm" "npm"
check_tool "Python" "python3"

# 2. Check GCP Project Context
echo -e "\n${YELLOW}[2/5] Inspecting Google Cloud Project & Authentication...${NC}"

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"

if [ -z "$PROJECT_ID" ]; then
  CURRENT_GCP_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
  if [ -n "$CURRENT_GCP_PROJECT" ] && [ "$CURRENT_GCP_PROJECT" != "(unset)" ]; then
    PROJECT_ID="$CURRENT_GCP_PROJECT"
  fi
fi

if [ -z "$PROJECT_ID" ]; then
  echo -e "  ${RED}[FAIL] No Google Cloud project specified.${NC}"
  echo -e "         Pass project as argument: ./scripts/gcp/preflight.sh <PROJECT_ID>"
  echo -e "         Or export GOOGLE_CLOUD_PROJECT=<PROJECT_ID>"
  exit 1
else
  echo -e "  [PASS] Target Google Cloud Project: ${GREEN}${PROJECT_ID}${NC}"
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)
if [ -z "$ACTIVE_ACCOUNT" ]; then
  echo -e "  ${RED}[FAIL] No active Google Cloud user/service account authenticated.${NC}"
  echo -e "         Run: gcloud auth login && gcloud auth application-default login"
  exit 1
else
  echo -e "  [PASS] Authenticated GCP Identity: ${GREEN}${ACTIVE_ACCOUNT}${NC}"
fi

# 3. Check Required GCP APIs
echo -e "\n${YELLOW}[3/5] Checking Google Cloud Services & API statuses...${NC}"

REQUIRED_APIS=(
  "run.googleapis.com"
  "compute.googleapis.com"
  "aiplatform.googleapis.com"
  "storage.googleapis.com"
  "secretmanager.googleapis.com"
  "artifactregistry.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
  STATUS=$(gcloud services list --project="$PROJECT_ID" --filter="name:$api" --format="value(name)" 2>/dev/null || true)
  if [ -n "$STATUS" ]; then
    echo -e "  [PASS] API enabled: $api"
  else
    echo -e "  ${YELLOW}[INFO] API not yet enabled: $api (Terraform or preflight can enable this)${NC}"
  fi
done

# 4. Verify Local Workspace State
echo -e "\n${YELLOW}[4/5] Checking application source code readiness...${NC}"

if [ -f "apps/web/package.json" ] && [ -f "apps/web/Dockerfile" ]; then
  echo -e "  [PASS] Next.js frontend source & Dockerfile present."
else
  echo -e "  ${RED}[FAIL] Next.js frontend Dockerfile missing.${NC}"
  exit 1
fi

if [ -f "pyproject.toml" ] && [ -f "Dockerfile" ]; then
  echo -e "  [PASS] FastAPI backend source & Dockerfile present."
else
  echo -e "  ${RED}[FAIL] FastAPI backend Dockerfile missing.${NC}"
  exit 1
fi

if [ -d "infra/terraform" ] && [ -f "infra/terraform/main.tf" ]; then
  echo -e "  [PASS] Terraform infrastructure configuration present."
else
  echo -e "  ${RED}[FAIL] Terraform files missing.${NC}"
  exit 1
fi

# 5. Local Non-Destructive Validation
echo -e "\n${YELLOW}[5/5] Performing local Terraform static validation...${NC}"
(
  cd infra/terraform
  terraform validate >/dev/null 2>&1 && echo -e "  [PASS] Terraform configuration syntax is valid."
)

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} Preflight check completed successfully! Ready for image build & plan.${NC}"
echo -e "${GREEN} Next step: ./scripts/gcp/build.sh${NC}"
echo -e "${GREEN}==============================================================================${NC}"
