#!/usr/bin/env bash
# ==============================================================================
# ClassLens Post-Deployment Health & Smoke Verification Script
# ==============================================================================
# Usage: ./scripts/gcp/verify.sh [TARGET_URL]
# Example: ./scripts/gcp/verify.sh https://34.120.45.67
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TARGET_URL="${1:-}"

if [ -z "$TARGET_URL" ]; then
  # Try to read from terraform outputs if in repo
  if [ -f "infra/terraform/terraform.tfstate" ]; then
    TARGET_URL=$(cd infra/terraform && terraform output -raw application_url 2>/dev/null || true)
  fi
fi

if [ -z "$TARGET_URL" ]; then
  echo -e "${RED}[ERROR] Target URL not provided.${NC}"
  echo -e "        Usage: ./scripts/gcp/verify.sh <TARGET_URL>"
  exit 1
fi

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE} ClassLens Post-Deployment Verification${NC}"
echo -e "${BLUE} Testing Target: ${TARGET_URL}${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Allow self-signed SSL certs during verification (-k)
CURL_OPTS="-s -k -w \n%{http_code}\n%{time_total}s"

# Test 1: Backend Health Probe (/health)
echo -e "\n${YELLOW}[1/4] Probing backend health endpoint (${TARGET_URL}/health)...${NC}"
HEALTH_RESP=$(curl $CURL_OPTS "${TARGET_URL}/health" || echo "FAILED\n000\n0s")
HTTP_CODE=$(echo "$HEALTH_RESP" | tail -n 2 | head -n 1)
LATENCY=$(echo "$HEALTH_RESP" | tail -n 1)
BODY=$(echo "$HEALTH_RESP" | head -n -2)

if [ "$HTTP_CODE" == "200" ]; then
  echo -e "  ${GREEN}[PASS] Health check returned 200 OK (${LATENCY})${NC}"
  echo -e "         Payload: ${BODY}"
else
  echo -e "  ${RED}[FAIL] Health check returned status ${HTTP_CODE}${NC}"
  echo -e "         Response: ${BODY}"
  exit 1
fi

# Test 2: Frontend Root Page (/)
echo -e "\n${YELLOW}[2/4] Probing Next.js frontend root (${TARGET_URL}/)...${NC}"
FRONTEND_RESP=$(curl $CURL_OPTS "${TARGET_URL}/" || echo "FAILED\n000\n0s")
F_CODE=$(echo "$FRONTEND_RESP" | tail -n 2 | head -n 1)
F_LATENCY=$(echo "$FRONTEND_RESP" | tail -n 1)

if [ "$F_CODE" == "200" ] || [ "$F_CODE" == "307" ] || [ "$F_CODE" == "308" ]; then
  echo -e "  ${GREEN}[PASS] Frontend returned status ${F_CODE} (${F_LATENCY})${NC}"
else
  echo -e "  ${RED}[FAIL] Frontend returned unexpected status ${F_CODE}${NC}"
  exit 1
fi

# Test 3: Backend Authentication Enforcement (/api/v1/auth/me)
echo -e "\n${YELLOW}[3/4] Verifying unauthenticated API access rejection (${TARGET_URL}/api/v1/auth/me)...${NC}"
AUTH_RESP=$(curl $CURL_OPTS "${TARGET_URL}/api/v1/auth/me" || echo "FAILED\n000\n0s")
A_CODE=$(echo "$AUTH_RESP" | tail -n 2 | head -n 1)

if [ "$A_CODE" == "401" ]; then
  echo -e "  ${GREEN}[PASS] Protected API strictly rejected unauthenticated request with 401 Unauthorized.${NC}"
else
  echo -e "  ${RED}[FAIL] Expected 401 Unauthorized, received ${A_CODE}.${NC}"
  exit 1
fi

# Test 4: Defense-in-Depth Security Headers
echo -e "\n${YELLOW}[4/4] Inspecting response security headers...${NC}"
HEADERS=$(curl -s -k -I "${TARGET_URL}/health" || true)

check_header() {
  local name=$1
  if echo "$HEADERS" | grep -i "$name" >/dev/null; then
    echo -e "  ${GREEN}[PASS] Security header present: $name${NC}"
  else
    echo -e "  ${YELLOW}[WARN] Security header not found: $name${NC}"
  fi
}

check_header "x-correlation-id"
check_header "x-content-type-options"
check_header "x-frame-options"

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN} All verification smoke tests passed successfully!${NC}"
echo -e "${GREEN} ClassLens deployment is healthy and operational.${NC}"
echo -e "${GREEN}==============================================================================${NC}"
