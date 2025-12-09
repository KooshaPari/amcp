#!/bin/bash

# Verify E2E test setup

echo "=================================================="
echo "E2E Test Suite Setup Verification"
echo "=================================================="
echo ""

ISSUES=0

# Check directory structure
echo "Checking directory structure..."
REQUIRED_DIRS=(
    "tests/e2e"
    "tests/e2e/bifrost"
    "tests/e2e/smartcp"
    "tests/e2e/integration"
    "tests/e2e/utils"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ✗ $dir missing"
        ISSUES=$((ISSUES + 1))
    fi
done
echo ""

# Check test files
echo "Checking test files..."
REQUIRED_FILES=(
    "tests/e2e/conftest.py"
    "tests/e2e/bifrost/test_bifrost_live.py"
    "tests/e2e/smartcp/test_smartcp_live.py"
    "tests/e2e/integration/test_full_flow_live.py"
    "tests/e2e/utils/wait_for_services.py"
    "tests/e2e/utils/cleanup.py"
    "tests/e2e/run_e2e_tests.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
        ISSUES=$((ISSUES + 1))
    fi
done
echo ""

# Check executability
echo "Checking executable permissions..."
if [ -x "tests/e2e/run_e2e_tests.sh" ]; then
    echo "  ✓ run_e2e_tests.sh is executable"
else
    echo "  ✗ run_e2e_tests.sh not executable (run: chmod +x tests/e2e/run_e2e_tests.sh)"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check documentation
echo "Checking documentation..."
DOC_FILES=(
    "tests/e2e/README.md"
    "tests/e2e/E2E_TESTING_GUIDE.md"
    "tests/e2e/E2E_SUITE_SUMMARY.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
        ISSUES=$((ISSUES + 1))
    fi
done
echo ""

# Check docker-compose example
echo "Checking configuration..."
if [ -f "docker-compose.local.example.yml" ]; then
    echo "  ✓ docker-compose.local.example.yml exists"
    if [ ! -f "docker-compose.local.yml" ]; then
        echo "  ⚠ docker-compose.local.yml not found (copy from example)"
    else
        echo "  ✓ docker-compose.local.yml exists"
    fi
else
    echo "  ✗ docker-compose.local.example.yml missing"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check Python dependencies
echo "Checking Python dependencies..."
REQUIRED_DEPS=(
    "pytest"
    "pytest-asyncio"
    "httpx"
)

for dep in "${REQUIRED_DEPS[@]}"; do
    if python -c "import $dep" 2>/dev/null; then
        echo "  ✓ $dep installed"
    else
        echo "  ✗ $dep not installed (run: pip install $dep)"
        ISSUES=$((ISSUES + 1))
    fi
done
echo ""

# Summary
echo "=================================================="
if [ $ISSUES -eq 0 ]; then
    echo "✅ All checks passed! E2E test suite is ready."
    echo ""
    echo "Next steps:"
    echo "  1. Copy docker-compose.local.example.yml to docker-compose.local.yml"
    echo "  2. Customize docker-compose.local.yml for your environment"
    echo "  3. Run: ./tests/e2e/run_e2e_tests.sh"
else
    echo "❌ Found $ISSUES issue(s). Please fix before running tests."
fi
echo "=================================================="
