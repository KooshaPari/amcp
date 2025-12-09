#!/bin/bash

# E2E Test Runner
# Starts all services, waits for health, runs E2E tests, cleans up

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting E2E Test Suite${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.local.yml}"
SERVICES_TIMEOUT="${SERVICES_TIMEOUT:-60}"
TEST_SCOPE="${TEST_SCOPE:-e2e}"
TEST_VERBOSE="${TEST_VERBOSE:-false}"

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: $COMPOSE_FILE not found${NC}"
    echo "Please create docker-compose.local.yml with all services"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Cleaning up...${NC}"
    echo -e "${YELLOW}========================================${NC}\n"

    # Stop services
    docker-compose -f "$COMPOSE_FILE" down

    echo -e "${GREEN}Cleanup completed${NC}"
}

# Register cleanup on exit
trap cleanup EXIT INT TERM

# Step 1: Start services
echo -e "${YELLOW}Step 1: Starting services...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start services${NC}"
    exit 1
fi

echo -e "${GREEN}Services started${NC}\n"

# Step 2: Wait for services to be healthy
echo -e "${YELLOW}Step 2: Waiting for services to be healthy...${NC}"
python tests/e2e/utils/wait_for_services.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Services failed health check${NC}"
    echo -e "${YELLOW}Showing service logs:${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

echo -e "${GREEN}All services healthy${NC}\n"

# Step 3: Run E2E tests
echo -e "${YELLOW}Step 3: Running E2E tests...${NC}\n"

PYTEST_ARGS="-v --tb=short -m $TEST_SCOPE"

if [ "$TEST_VERBOSE" = "true" ]; then
    PYTEST_ARGS="$PYTEST_ARGS -s"
fi

# Add coverage if requested
if [ "$WITH_COVERAGE" = "true" ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=. --cov-report=term-missing"
fi

pytest tests/e2e/ $PYTEST_ARGS

TEST_EXIT_CODE=$?

# Step 4: Show results
echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Results${NC}"
echo -e "${YELLOW}========================================${NC}\n"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All E2E tests passed${NC}"
else
    echo -e "${RED}❌ Some E2E tests failed (exit code: $TEST_EXIT_CODE)${NC}"

    # Show logs on failure
    echo -e "\n${YELLOW}Service logs (last 100 lines):${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=100
fi

# Step 5: Cleanup test data (optional)
if [ "$CLEANUP_DATA" = "true" ]; then
    echo -e "\n${YELLOW}Step 5: Cleaning up test data...${NC}"
    python tests/e2e/utils/cleanup.py
fi

# Exit with test exit code
exit $TEST_EXIT_CODE
