#!/usr/bin/env bash
# ==============================================================================
# ClassLens Terraform Plan Script (Safe / Non-Destructive)
# ==============================================================================
# Usage: ./scripts/gcp/plan.sh [PROJECT_ID] [REGION]
#
# Generates a speculative Terraform execution plan.
# Does NOT apply changes or modify cloud resources.
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
  echo -e "${RED}[ERROR] No GCP project ID specified.${NC}"
  echo -e "        Usage: ./scripts/gcp/plan.sh <PROJECT_ID> [REGION]"
  exit 1
fi

REGION="${2:-asia-southeast1}"
TF_DIR="infra/terraform"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Terraform Infrastructure Plan (Dry-Run / Non-Destructive)${NC}"
echo -e "${BLUE} Project: ${PROJECT_ID} | Region: ${REGION}${NC}"
echo -e "${BLUE}==============================================================================${NC}"

cd "$TF_DIR"

echo -e "\n${YELLOW}[1/3] Formatting check...${NC}"
terraform fmt -check || {
  echo -e "${YELLOW}Auto-formatting Terraform files...${NC}"
  terraform fmt
}

echo -e "\n${YELLOW}[2/3] Initializing Terraform providers...${NC}"
terraform init -backend=false

echo -e "\n${YELLOW}[3/3] Generating speculative execution plan...${NC}"
terraform plan \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -out="tfplan"

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} Terraform plan generated successfully and saved to ${TF_DIR}/tfplan.${NC}"
echo -e "${GREEN} Review the planned changes above.${NC}"
echo -e "${GREEN} To deploy with explicit confirmation: ./scripts/gcp/deploy.sh --confirm${NC}"
echo -e "${GREEN}==============================================================================${NC}"
