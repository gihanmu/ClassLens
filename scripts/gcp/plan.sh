#!/usr/bin/env bash
# ==============================================================================
# ClassLens Terraform Infrastructure Planning Script (Safe / Non-Destructive)
# ==============================================================================
# Usage: ./scripts/gcp/plan.sh [--dry-run] [PROJECT_ID] [REGION] [IMAGE_TAG]
#
# Generates a speculative Terraform execution plan using exact image references.
# Enforces Cloud SQL PostgreSQL enablement for production durability.
# Does NOT apply changes or modify cloud resources.
# ==============================================================================

set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

IS_DRY_RUN=false
if [ "${1:-}" == "--dry-run" ]; then
  IS_DRY_RUN=true
  shift
fi

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
  echo -e "${RED}[ERROR] No GCP project ID specified.${NC}"
  echo -e "        Usage: ./scripts/gcp/plan.sh [--dry-run] <PROJECT_ID> [REGION] [IMAGE_TAG]"
  exit 1
fi

REGION="${2:-asia-southeast1}"
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "v1")
TAG="${3:-${IMAGE_TAG:-sha-${GIT_SHA}}}"
REPO_NAME="classlens-repo"
TF_DIR="infra/terraform"

FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/frontend:${TAG}"
BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:${TAG}"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Terraform Infrastructure Plan (Dry-Run / Speculative)${NC}"
echo -e "${BLUE} Mode:           $([ "$IS_DRY_RUN" = true ] && echo "DRY-RUN (Syntax check only)" || echo "ACTIVE PLAN GENERATION")${NC}"
echo -e "${BLUE} Project:        ${PROJECT_ID}${NC}"
echo -e "${BLUE} Region:         ${REGION}${NC}"
echo -e "${BLUE} Frontend Image: ${FRONTEND_IMAGE}${NC}"
echo -e "${BLUE} Backend Image:  ${BACKEND_IMAGE}${NC}"
echo -e "${BLUE} Persistence:    Cloud SQL PostgreSQL (enable_cloud_sql = true)${NC}"
echo -e "${BLUE}==============================================================================${NC}"

cd "$TF_DIR"

echo -e "\n${YELLOW}[1/4] Checking Terraform formatting...${NC}"
terraform fmt -check || {
  echo -e "${YELLOW}Notice: Formatting Terraform files...${NC}"
  terraform fmt
}

echo -e "\n${YELLOW}[2/4] Validating Terraform configuration syntax...${NC}"
terraform validate

if [ "$IS_DRY_RUN" = true ]; then
  echo -e "\n${YELLOW}[DRY-RUN] Speculative Terraform planning preview (No cloud calls):${NC}"
  echo -e "  Planned command:"
  echo -e "    terraform plan \\"
  echo -e "      -var=\"project_id=${PROJECT_ID}\" \\"
  echo -e "      -var=\"region=${REGION}\" \\"
  echo -e "      -var=\"frontend_image=${FRONTEND_IMAGE}\" \\"
  echo -e "      -var=\"backend_image=${BACKEND_IMAGE}\" \\"
  echo -e "      -var=\"enable_cloud_sql=true\" \\"
  echo -e "      -out=\"tfplan\""
  echo -e "\n  Expected Billable Resources (Cost-Optimized Cloud Run BFF Architecture):"
  echo -e "    - google_sql_database_instance.postgres (db-f1-micro, PostgreSQL 15)"
  echo -e "    - google_cloud_run_v2_service.frontend (Public Google-managed HTTPS + BFF, 0-2 instances)"
  echo -e "    - google_cloud_run_v2_service.backend (Private IAM-restricted service, 0-2 instances)"
  echo -e "    - google_storage_bucket.worksheets (Uniform bucket-level access)"
  echo -e "    - google_artifact_registry_repository.classlens (Docker OCI repository)"
  echo -e "    - google_secret_manager_secret.* (4 runtime secrets)"
  echo -e "\n${GREEN}[DRY-RUN] Terraform planning pre-check passed successfully.${NC}"
  exit 0
fi

echo -e "\n${YELLOW}[3/4] Initializing Terraform providers and state backend...${NC}"
terraform init

echo -e "\n${YELLOW}[4/4] Generating speculative execution plan with immutable image tags...${NC}"
terraform plan \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="frontend_image=${FRONTEND_IMAGE}" \
  -var="backend_image=${BACKEND_IMAGE}" \
  -var="enable_cloud_sql=true" \
  -out="tfplan"

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} Terraform plan generated successfully and saved to ${TF_DIR}/tfplan.${NC}"
echo -e "${GREEN} Review the planned additions and modifications above.${NC}"
echo -e "${GREEN} To deploy with explicit confirmation: ./scripts/gcp/deploy.sh --confirm${NC}"
echo -e "${GREEN}==============================================================================${NC}"
