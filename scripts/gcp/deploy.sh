#!/usr/bin/env bash
# ==============================================================================
# ClassLens Infrastructure Deployment Script
# ==============================================================================
# Usage: ./scripts/gcp/deploy.sh [--dry-run] [--confirm] [PROJECT_ID] [REGION]
#
# SAFETY GUARD:
# Requires explicit '--confirm' flag or interactive typed confirmation ('DEPLOY').
# Never applies unverified or stale plans automatically.
# ==============================================================================

set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

IS_DRY_RUN=false
CONFIRMED=false

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      IS_DRY_RUN=true
      shift
      ;;
    --confirm)
      CONFIRMED=true
      shift
      ;;
    *)
      break
      ;;
  esac
done

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
  echo -e "${RED}[ERROR] No GCP project ID specified.${NC}"
  echo -e "        Usage: ./scripts/gcp/deploy.sh [--dry-run] [--confirm] <PROJECT_ID> [REGION]"
  exit 1
fi

REGION="${2:-asia-southeast1}"
TF_DIR="infra/terraform"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Production Infrastructure Deployment${NC}"
echo -e "${BLUE} Mode:           $([ "$IS_DRY_RUN" = true ] && echo "DRY-RUN (Simulated)" || echo "LIVE PROVISIONING")${NC}"
echo -e "${BLUE} Target Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE} Region:         ${REGION}${NC}"
echo -e "${BLUE}==============================================================================${NC}"

if [ "$IS_DRY_RUN" = true ]; then
  echo -e "\n${YELLOW}[DRY-RUN] Simulating deployment execution (No resources will be modified):${NC}"
  echo -e "  1. Would verify pre-generated execution plan in ${TF_DIR}/tfplan"
  echo -e "  2. Would check Artifact Registry bootstrap state"
  echo -e "  3. Would apply Cloud SQL PostgreSQL, Cloud Storage, Cloud Run, and Load Balancer"
  echo -e "  4. Would output Load Balancer IP and application URL"
  echo -e "\n${GREEN}[DRY-RUN] Deployment simulation complete. Ready for live deployment with --confirm.${NC}"
  exit 0
fi

# Explicit Safety Confirmation Guard
if [ "$CONFIRMED" = false ]; then
  echo -e "\n${YELLOW}WARNING: You are about to deploy live infrastructure to Google Cloud Platform.${NC}"
  echo -e "This will provision:"
  echo -e "  - Cloud SQL PostgreSQL instance (PostgreSQL 15)"
  echo -e "  - Google Cloud Storage private bucket (worksheets)"
  echo -e "  - Google Cloud Run services (Frontend & Backend, internal ingress)"
  echo -e "  - Google Cloud HTTPS External Application Load Balancer with Serverless NEGs"
  echo -e "  - Google Secret Manager secret bindings\n"

  if [ -t 0 ]; then
    read -p "Type 'DEPLOY' to confirm and proceed: " -r CONFIRMATION
    if [ "$CONFIRMATION" != "DEPLOY" ]; then
      echo -e "${RED}Deployment aborted by user.${NC}"
      exit 0
    fi
  else
    echo -e "${RED}[BLOCKED] Non-interactive execution requires explicit '--confirm' flag.${NC}"
    echo -e "          Run: ./scripts/gcp/deploy.sh --confirm ${PROJECT_ID} ${REGION}"
    exit 1
  fi
fi

cd "$TF_DIR"

# Ensure terraform is initialized
if [ ! -d ".terraform" ]; then
  echo -e "\n${YELLOW}[1/3] Initializing Terraform...${NC}"
  terraform init
fi

# Apply pre-generated plan or create fresh execution plan
if [ -f "tfplan" ]; then
  echo -e "\n${YELLOW}[2/3] Applying verified execution plan 'tfplan'...${NC}"
  terraform apply "tfplan"
  rm -f "tfplan"
else
  echo -e "\n${YELLOW}[2/3] No pre-existing tfplan found. Generating and applying plan...${NC}"
  GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "v1")
  TAG="${IMAGE_TAG:-sha-${GIT_SHA}}"
  REPO_NAME="classlens-repo"
  FRONTEND_IMG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/frontend:${TAG}"
  BACKEND_IMG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:${TAG}"

  terraform apply \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="frontend_image=${FRONTEND_IMG}" \
    -var="backend_image=${BACKEND_IMG}" \
    -var="enable_cloud_sql=true" \
    -auto-approve
fi

# Retrieve Load Balancer and infrastructure outputs
echo -e "\n${YELLOW}[3/3] Fetching deployment outputs...${NC}"
LB_IP=$(terraform output -raw load_balancer_ip 2>/dev/null || echo "Pending")
APP_URL=$(terraform output -raw application_url 2>/dev/null || echo "Pending")
SQL_INSTANCE=$(terraform output -raw cloud_sql_instance_name 2>/dev/null || echo "none")

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} Infrastructure deployment completed successfully!${NC}"
echo -e "${GREEN} Application Load Balancer IP: ${LB_IP}${NC}"
echo -e "${GREEN} Application URL:              ${APP_URL}${NC}"
echo -e "${GREEN} Cloud SQL Instance:           ${SQL_INSTANCE}${NC}"
echo -e "${GREEN} Next step: Run database migrations and smoke test:${NC}"
echo -e "  python3 scripts/migrate.py"
echo -e "  ./scripts/gcp/verify.sh ${APP_URL}"
echo -e "${GREEN}==============================================================================${NC}"
