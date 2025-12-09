#!/bin/bash
# Test the local deployment end-to-end

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SmartCP Deployment Test${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

failed=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>&1 || echo "000")

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_status, got $response)"
        failed=$((failed + 1))
        return 1
    fi
}

echo -e "${YELLOW}Testing HTTP Endpoints:${NC}"
test_endpoint "SmartCP Health" "http://localhost:8000/health"
test_endpoint "Bifrost API Health" "http://localhost:8001/health"
test_endpoint "Bifrost Backend Health" "http://localhost:8080/health"
test_endpoint "Bifrost ML Health" "http://localhost:8002/health"
echo ""

echo -e "${YELLOW}Testing Infrastructure:${NC}"
test_endpoint "Qdrant Health" "http://localhost:6333/health"
echo ""

echo -e "${YELLOW}Testing API Functionality:${NC}"

# Test SmartCP tools list
echo -n "SmartCP Tools List... "
tools=$(curl -s http://localhost:8000/tools 2>&1)
if echo "$tools" | grep -q "tools" || echo "$tools" | grep -q "\["; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    failed=$((failed + 1))
fi

# Test Bifrost API docs
echo -n "Bifrost API Docs... "
if curl -s http://localhost:8001/docs | grep -q "FastAPI\|OpenAPI\|swagger" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    failed=$((failed + 1))
fi

# Test GraphQL playground
echo -n "GraphQL Playground... "
if curl -s http://localhost:8080/ | grep -q "GraphQL\|playground" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    failed=$((failed + 1))
fi

echo ""

# Database test
echo -e "${YELLOW}Testing Database:${NC}"
echo -n "PostgreSQL Connection... "
if docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U smartcp_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    failed=$((failed + 1))
fi

# Test table exists
echo -n "Database Schema... "
result=$(docker-compose -f docker-compose.local.yml exec -T postgres \
    psql -U smartcp_user -d smartcp -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='users';" 2>&1)
if [ "$result" = "1" ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    failed=$((failed + 1))
fi

echo ""

# Redis test
echo -e "${YELLOW}Testing Redis:${NC}"
echo -n "Redis PING... "
if docker-compose -f docker-compose.local.yml exec -T redis redis-cli ping 2>&1 | grep -q "PONG"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    failed=$((failed + 1))
fi

echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${GREEN}Deployment is working correctly!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. View API docs: http://localhost:8001/docs"
    echo "  2. Try GraphQL: http://localhost:8080/graphql"
    echo "  3. Run integration tests: docker-compose exec smartcp pytest tests/"
    exit 0
else
    echo -e "${RED}$failed test(s) failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: ./scripts/logs.sh all"
    echo "  2. Health check: ./scripts/health-check.sh"
    echo "  3. Restart services: ./scripts/stop-local.sh && ./scripts/start-local.sh"
    exit 1
fi
