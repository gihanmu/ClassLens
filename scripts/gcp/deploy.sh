#!/usr/bin/env bash
# ==============================================================================
# ClassLens Infrastructure Deployment Script
# ==============================================================================
# Usage: ./scripts/gcp/deploy.sh [--confirm] [PROJECT_ID] [REGION]
#
# SAFETY GUARD:
# Requires explicit '--confirm' flag or interactive typed confirmation.
# Never executes automatically or silently.
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONFIRMED=false
if [ "${1:-}" == "--confirm" ]; then
  CONFIRMED=true
  shift
fi

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
  echo -e "${RED}[ERROR] No GCP project ID specified.${NC}"
  echo -e "        Usage: ./scripts/gcp/deploy.sh --confirm <PROJECT_ID> [REGION]"
  exit 1
fi

REGION="${2:-asia-southeast1}"
TF_DIR="infra/terraform"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Production Infrastructure Deployment${NC}"
echo -e "${BLUE} Target Project: ${PROJECT_ID} | Region: ${REGION}${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Explicit Safety Confirmation Guard
if [ "$CONFIRMED" = false ]; then
  echo -e "\n${YELLOW}WARNING: You are about to deploy infrastructure to Google Cloud Platform.${NC}"
  echo -e "This will create Cloud Run services, Serverless NEGs, an HTTPS Load Balancer,"
  echo -e "Cloud Storage buckets, and Secret Manager entries in project '${PROJECT_ID}'.\n"
  
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
  echo -e "\n${YELLOW}[2/3] Applying pre-generated plan 'tfplan'...${NC}"
  terraform apply "tfplan"
  rm -f "tfplan"
else
  echo -e "\n${YELLOW}[2/3] Generating and applying execution plan...${NC}"
  terraform apply \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -auto-approve
fi

# Retrieve Load Balancer outputs
echo -e "\n${YELLOW}[3/3] Fetching deployment outputs...${NC}"
LB_IP=$(terraform output -raw load_balancer_ip 2>/dev/null || echo "Pending")
APP_URL=$(terraform output -raw application_url 2>/dev/null || echo "Pending")

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} Deployment completed successfully!${NC}"
echo -e "${GREEN} Application Load Balancer IP: ${LB_IP}${NC}"
echo -e "${GREEN} Application URL:              ${APP_URL}${NC}"
echo -e "${GREEN} Run verification:             ./scripts/gcp/verify.sh ${APP_URL}${NC}"
echo -e "${GREEN}==============================================================================${NC}"
