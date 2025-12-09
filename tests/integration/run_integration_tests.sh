#!/bin/bash
# Integration test runner for Bifrost and SmartCP SDKs
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Integration Test Suite"
echo "Bifrost SDK + SmartCP SDK"
echo "========================================="
echo

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check dependencies
echo "Checking dependencies..."
python -c "import pytest; import pytest_asyncio" 2>/dev/null || {
    echo -e "${RED}Error: pytest or pytest-asyncio not installed${NC}"
    echo "Install with: pip install pytest pytest-asyncio"
    exit 1
}

# Default: run all tests
TEST_SUITE="${1:-all}"
COVERAGE="${2:-no}"

echo -e "${GREEN}Running test suite: $TEST_SUITE${NC}"
echo

case "$TEST_SUITE" in
    "all")
        echo "Running all integration tests..."
        if [ "$COVERAGE" = "coverage" ]; then
            pytest tests/integration/ -v --cov=bifrost_extensions --cov-report=html --cov-report=term
        else
            pytest tests/integration/ -v
        fi
        ;;

    "bifrost")
        echo "Running Bifrost SDK tests..."
        if [ "$COVERAGE" = "coverage" ]; then
            pytest tests/integration/bifrost/ -v --cov=bifrost_extensions --cov-report=html --cov-report=term
        else
            pytest tests/integration/bifrost/ -v
        fi
        ;;

    "smartcp")
        echo "Running SmartCP SDK tests..."
        pytest tests/integration/smartcp/ -v
        ;;

    "cross")
        echo "Running cross-SDK integration tests..."
        pytest tests/integration/cross_sdk/ -v
        ;;

    "performance")
        echo "Running performance tests..."
        pytest tests/integration/ -v -m performance
        ;;

    "fast")
        echo "Running fast tests (skipping slow tests)..."
        pytest tests/integration/ -v -m "not slow and not performance"
        ;;

    "smoke")
        echo "Running smoke tests..."
        pytest tests/integration/ -v -m smoke -k "test_basic"
        ;;

    *)
        echo -e "${RED}Unknown test suite: $TEST_SUITE${NC}"
        echo "Usage: $0 [all|bifrost|smartcp|cross|performance|fast|smoke] [coverage]"
        exit 1
        ;;
esac

EXIT_CODE=$?

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${GREEN}=========================================${NC}"
else
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}Some tests failed!${NC}"
    echo -e "${RED}=========================================${NC}"
fi

exit $EXIT_CODE
