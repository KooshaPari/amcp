#!/bin/bash
# Test runner script for SmartCP

set -e

echo "🧪 SmartCP Test Suite"
echo "===================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test categories
run_unit() {
    echo -e "\n${YELLOW}Running unit tests...${NC}"
    pytest tests/unit/ -v --tb=short -m unit
}

run_component() {
    echo -e "\n${YELLOW}Running component tests...${NC}"
    pytest tests/component/ -v --tb=short -m component
}

run_integration() {
    echo -e "\n${YELLOW}Running integration tests...${NC}"
    pytest tests/integration/ -v --tb=short -m integration
}

run_e2e() {
    echo -e "\n${YELLOW}Running E2E tests...${NC}"
    pytest tests/e2e/ -v --tb=short -m e2e
}

run_smoke() {
    echo -e "\n${YELLOW}Running smoke tests...${NC}"
    pytest tests/smoke/ -v --tb=short -m smoke
}

run_performance() {
    echo -e "\n${YELLOW}Running performance tests...${NC}"
    pytest tests/performance/ -v --tb=short -m performance
}

run_all() {
    echo -e "\n${YELLOW}Running all tests...${NC}"
    pytest tests/ -v --tb=short
}

run_coverage() {
    echo -e "\n${YELLOW}Running tests with coverage...${NC}"
    pytest tests/ --cov=smartcp --cov-report=term --cov-report=html
    echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
}

# Parse arguments
case "${1:-all}" in
    unit)
        run_unit
        ;;
    component)
        run_component
        ;;
    integration)
        run_integration
        ;;
    e2e)
        run_e2e
        ;;
    smoke)
        run_smoke
        ;;
    performance)
        run_performance
        ;;
    coverage)
        run_coverage
        ;;
    all)
        run_smoke
        run_unit
        run_component
        run_integration
        run_e2e
        echo -e "\n${GREEN}✅ All tests completed!${NC}"
        ;;
    *)
        echo "Usage: $0 [unit|component|integration|e2e|smoke|performance|coverage|all]"
        exit 1
        ;;
esac
