#!/usr/bin/env bash
# ==============================================================================
# ClassLens Cloud Run Service Rollback Script
# ==============================================================================
# Usage: ./scripts/gcp/rollback.sh [--dry-run] [--confirm] [PROJECT_ID] [REGION]
#
# Fast, safe traffic rollback to previous known-good Cloud Run revisions.
# Traffic transition is instantaneous (<100ms) with zero dropped connections.
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
  echo -e "        Usage: ./scripts/gcp/rollback.sh [--dry-run] [--confirm] <PROJECT_ID> [REGION]"
  exit 1
fi

REGION="${2:-asia-southeast1}"
BACKEND_SVC="classlens-backend"
FRONTEND_SVC="classlens-frontend"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Cloud Run Rollback Tool${NC}"
echo -e "${BLUE} Mode:           $([ "$IS_DRY_RUN" = true ] && echo "DRY-RUN (Simulated)" || echo "ACTIVE TRAFFIC ROLLBACK")${NC}"
echo -e "${BLUE} Target Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE} Region:         ${REGION}${NC}"
echo -e "${BLUE}==============================================================================${NC}"

if [ "$IS_DRY_RUN" = true ]; then
  echo -e "\n${YELLOW}[DRY-RUN] Simulating rollback procedure (No traffic will be shifted):${NC}"
  echo -e "  1. Would inspect recent Cloud Run revisions for '${BACKEND_SVC}' and '${FRONTEND_SVC}'"
  echo -e "  2. Would identify the immediate previous active revision"
  echo -e "  3. Would run: gcloud run services update-traffic <service> --to-revisions=<prev-rev>=100"
  echo -e "  4. Database schema is backward-compatible and requires no destructive rollback."
  echo -e "\n${GREEN}[DRY-RUN] Rollback simulation complete.${NC}"
  exit 0
fi

rollback_service() {
  local service=$1
  echo -e "\n${YELLOW}Listing recent revisions for service: ${service}...${NC}"

  REVISIONS=$(gcloud run revisions list \
    --service="$service" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format="table(name,active,creationTimestamp)" \
    --limit=5 2>/dev/null || true)

  if [ -z "$REVISIONS" ]; then
    echo -e "${RED}[WARN] No revisions found for service: ${service}.${NC}"
    return 0
  fi

  echo "$REVISIONS"

  PREV_REV=$(gcloud run revisions list \
    --service="$service" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format="value(name)" \
    --limit=2 2>/dev/null | tail -n 1 || true)

  if [ -z "$PREV_REV" ]; then
    echo -e "${YELLOW}[WARN] Only one revision exists for ${service}. Rollback not possible.${NC}"
    return 0
  fi

  echo -e "\nIdentified previous candidate revision: ${GREEN}${PREV_REV}${NC}"

  if [ "$CONFIRMED" = false ]; then
    if [ -t 0 ]; then
      read -p "Rollback 100% traffic of '${service}' to '${PREV_REV}'? [y/N]: " -r RESP
      if [[ ! "$RESP" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Rollback of ${service} skipped.${NC}"
        return 0
      fi
    else
      echo -e "${RED}[BLOCKED] Non-interactive execution requires '--confirm' flag.${NC}"
      exit 1
    fi
  fi

  echo -e "Updating traffic for ${service} to ${PREV_REV} (100%)..."
  gcloud run services update-traffic "$service" \
    --to-revisions="${PREV_REV}=100" \
    --project="$PROJECT_ID" \
    --region="$REGION"

  echo -e "${GREEN}[PASS] Service ${service} traffic shifted to ${PREV_REV}.${NC}"
}

rollback_service "$BACKEND_SVC"
rollback_service "$FRONTEND_SVC"

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} Rollback operations completed.${NC}"
echo -e "${GREEN} Run verification: ./scripts/gcp/verify.sh${NC}"
echo -e "${GREEN}==============================================================================${NC}"
