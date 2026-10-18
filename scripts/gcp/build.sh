#!/usr/bin/env bash
# ==============================================================================
# ClassLens Production Container Build & Registry Push Script
# ==============================================================================
# Usage: ./scripts/gcp/build.sh [--dry-run] [--push] [PROJECT_ID] [REGION] [IMAGE_TAG]
#
# Builds Next.js frontend and FastAPI backend production Docker images.
# Enforces immutable Git commit SHA tags (never relies on mutable 'latest').
# Safe by default: Does NOT push to Artifact Registry unless --push is specified.
# ==============================================================================

set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

IS_DRY_RUN=false
DO_PUSH=false

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      IS_DRY_RUN=true
      shift
      ;;
    --push)
      DO_PUSH=true
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
  PROJECT_ID="classlens-demo"
  echo -e "${YELLOW}[WARN] No GCP project configured. Defaulting project to '${PROJECT_ID}'.${NC}"
fi

REGION="${2:-asia-southeast1}"
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "v1")
TAG="${3:-${IMAGE_TAG:-sha-${GIT_SHA}}}"
REPO_NAME="classlens-repo"

FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/frontend:${TAG}"
BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:${TAG}"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Container Build & Packaging (Docker Multi-Stage)${NC}"
echo -e "${BLUE} Mode:           $([ "$IS_DRY_RUN" = true ] && echo "DRY-RUN (No images built or pushed)" || echo "ACTIVE BUILD")${NC}"
echo -e "${BLUE} Project:        ${PROJECT_ID}${NC}"
echo -e "${BLUE} Region:         ${REGION}${NC}"
echo -e "${BLUE} Immutable Tag:  ${TAG}${NC}"
echo -e "${BLUE} Target Images:${NC}"
echo -e "${BLUE}   Frontend:     ${FRONTEND_IMAGE}${NC}"
echo -e "${BLUE}   Backend:      ${BACKEND_IMAGE}${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Check Docker daemon
if [ "$IS_DRY_RUN" = false ]; then
  if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker daemon is not running. Please start Docker and re-run.${NC}"
    exit 1
  fi
fi

if [ "$IS_DRY_RUN" = true ]; then
  echo -e "\n${YELLOW}[DRY-RUN] Verifying Dockerfile existence...${NC}"
  [ -f "apps/web/Dockerfile" ] && echo -e "  ${GREEN}[PASS]${NC} apps/web/Dockerfile exists."
  [ -f "Dockerfile" ] && echo -e "  ${GREEN}[PASS]${NC} root Dockerfile exists."
  echo -e "\n${YELLOW}[DRY-RUN] Image build commands that would be executed:${NC}"
  echo -e "  docker build -t ${FRONTEND_IMAGE} -f apps/web/Dockerfile apps/web/"
  echo -e "  docker build -t ${BACKEND_IMAGE} -f Dockerfile ."
  if [ "$DO_PUSH" = true ]; then
    echo -e "\n${YELLOW}[DRY-RUN] Push commands that would be executed:${NC}"
    echo -e "  gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet"
    echo -e "  docker push ${FRONTEND_IMAGE}"
    echo -e "  docker push ${BACKEND_IMAGE}"
  fi
  echo -e "\n${GREEN}[DRY-RUN] Container packaging pre-check completed successfully.${NC}"
  exit 0
fi

# 1. Build Frontend Image
echo -e "\n${YELLOW}[1/2] Building Next.js Frontend image (apps/web)...${NC}"
docker build \
  -t "${FRONTEND_IMAGE}" \
  -t "classlens-frontend:local" \
  -f apps/web/Dockerfile \
  apps/web/

echo -e "${GREEN}[PASS] Frontend image built successfully: ${FRONTEND_IMAGE}${NC}"

# 2. Build Backend Image
echo -e "\n${YELLOW}[2/2] Building FastAPI Backend image...${NC}"
docker build \
  -t "${BACKEND_IMAGE}" \
  -t "classlens-backend:local" \
  -f Dockerfile \
  .

echo -e "${GREEN}[PASS] Backend image built successfully: ${BACKEND_IMAGE}${NC}"

# 3. Push to Artifact Registry if requested
if [ "$DO_PUSH" = true ]; then
  echo -e "\n${YELLOW}[PUSH] Authenticating Docker with Artifact Registry for ${REGION}...${NC}"
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

  echo -e "${YELLOW}[PUSH] Pushing frontend image to ${FRONTEND_IMAGE}...${NC}"
  docker push "${FRONTEND_IMAGE}"

  echo -e "${YELLOW}[PUSH] Pushing backend image to ${BACKEND_IMAGE}...${NC}"
  docker push "${BACKEND_IMAGE}"

  echo -e "\n${GREEN}[PASS] Both container images pushed to Artifact Registry successfully!${NC}"
else
  echo -e "\n${YELLOW}[INFO] Images built locally with immutable tag '${TAG}'.${NC}"
  echo -e "       To push to Artifact Registry, run with --push:"
  echo -e "       ${BLUE}./scripts/gcp/build.sh --push ${PROJECT_ID} ${REGION} ${TAG}${NC}"
fi
