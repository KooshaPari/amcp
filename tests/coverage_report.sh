#!/bin/bash
# Coverage report script for SmartCP

set -e

cd "$(dirname "$0")/../.." || exit 1

echo "📊 SmartCP Code Coverage Report"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Clean previous coverage data
echo "Cleaning previous coverage data..."
coverage erase

# Run tests with coverage
echo -e "\n${YELLOW}Running tests with coverage...${NC}"
coverage run --source=smartcp/runtime,smartcp/tools -m pytest smartcp/tests/unit/ smartcp/tests/component/ smartcp/tests/integration/ smartcp/tests/smoke/ -v --tb=short 2>&1 | tail -20

# Generate reports
echo -e "\n${YELLOW}Generating coverage reports...${NC}"

# Terminal report
echo -e "\n${GREEN}Coverage Summary:${NC}"
coverage report --include="smartcp/runtime/**/*.py,smartcp/tools/**/*.py" --show-missing

# HTML report
coverage html --include="smartcp/runtime/**/*.py,smartcp/tools/**/*.py"
echo -e "\n${GREEN}HTML report generated: htmlcov/index.html${NC}"

# Summary
TOTAL_COVERAGE=$(coverage report --include="smartcp/runtime/**/*.py,smartcp/tools/**/*.py" | tail -1 | awk '{print $NF}')
echo -e "\n${GREEN}Total Coverage: ${TOTAL_COVERAGE}${NC}"

# Coverage by module
echo -e "\n${YELLOW}Coverage by Module:${NC}"
coverage report --include="smartcp/runtime/**/*.py,smartcp/tools/**/*.py" --format=markdown | grep -E "^\|.*\|.*\|.*\|$" | head -30
