#!/usr/bin/env bash
# ==============================================================================
# ClassLens Docker Container Build Script
# ==============================================================================
# Usage: ./scripts/gcp/build.sh [--push] [PROJECT_ID] [REGION]
#
# Builds Next.js frontend and FastAPI backend production Docker images.
# Safe by default: Does NOT push to Artifact Registry unless --push is specified.
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DO_PUSH=false
if [ "${1:-}" == "--push" ]; then
  DO_PUSH=true
  shift
fi

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
  PROJECT_ID="classlens-demo"
  echo -e "${YELLOW}[WARN] No GCP project configured. Defaulting tag to '${PROJECT_ID}'.${NC}"
fi

REGION="${2:-asia-southeast1}"
REPO_NAME="classlens-repo"
TAG="latest"

FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/frontend:${TAG}"
BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:${TAG}"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Container Build (Docker Multi-Stage)${NC}"
echo -e "${BLUE} Target Images:${NC}"
echo -e "${BLUE}   Frontend: ${FRONTEND_IMAGE}${NC}"
echo -e "${BLUE}   Backend:  ${BACKEND_IMAGE}${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Check docker daemon
if ! docker info >/dev/null 2>&1; then
  echo -e "${RED}[ERROR] Docker daemon is not running. Please start Docker and re-run.${NC}"
  exit 1
fi

# 1. Build Frontend Image
echo -e "\n${YELLOW}[1/2] Building Next.js Frontend image (apps/web)...${NC}"
docker build \
  -t "${FRONTEND_IMAGE}" \
  -t "classlens-frontend:local" \
  -f apps/web/Dockerfile \
  apps/web/

echo -e "${GREEN}[PASS] Frontend image built successfully.${NC}"

# 2. Build Backend Image
echo -e "\n${YELLOW}[2/2] Building FastAPI Backend image...${NC}"
docker build \
  -t "${BACKEND_IMAGE}" \
  -t "classlens-backend:local" \
  -f Dockerfile \
  .

echo -e "${GREEN}[PASS] Backend image built successfully.${NC}"

# 3. Optional Push to Artifact Registry
if [ "$DO_PUSH" = true ]; then
  echo -e "\n${YELLOW}[PUSH] Authenticating Docker with Artifact Registry for ${REGION}...${NC}"
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

  echo -e "${YELLOW}[PUSH] Pushing frontend image to ${FRONTEND_IMAGE}...${NC}"
  docker push "${FRONTEND_IMAGE}"

  echo -e "${YELLOW}[PUSH] Pushing backend image to ${BACKEND_IMAGE}...${NC}"
  docker push "${BACKEND_IMAGE}"

  echo -e "\n${GREEN}[PASS] Both container images pushed to Artifact Registry successfully!${NC}"
else
  echo -e "\n${YELLOW}[INFO] Images built locally. To push to Artifact Registry, run:${NC}"
  echo -e "       ${BLUE}./scripts/gcp/build.sh --push ${PROJECT_ID} ${REGION}${NC}"
fi

echo -e "\n${GREEN}Next step: ./scripts/gcp/plan.sh${NC}"
