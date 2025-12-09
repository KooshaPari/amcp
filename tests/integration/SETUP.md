# Integration Test Setup Guide

## Prerequisites

```bash
# Python 3.10+
python --version

# Virtual environment activated
source .venv/bin/activate

# Required packages
pip install pytest pytest-asyncio pytest-cov
```

## Installing SDKs

### Bifrost SDK

```bash
# Install from bifrost_extensions directory
cd bifrost_extensions
pip install -e .

# Or install directly
pip install -e bifrost_extensions/
```

### SmartCP SDK

```bash
# Install SmartCP dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Verifying Installation

```bash
# Check bifrost_extensions is installed
python -c "import bifrost_extensions; print(bifrost_extensions.__file__)"

# Check pytest works
pytest --version

# Check pytest-asyncio works
python -c "import pytest_asyncio; print('OK')"
```

## Running Tests

### Quick Start

```bash
# Make runner executable
chmod +x tests/integration/run_integration_tests.sh

# Run all tests
./tests/integration/run_integration_tests.sh all

# Run with coverage
./tests/integration/run_integration_tests.sh all coverage
```

### Manual pytest Commands

```bash
# Test collection only (verify structure)
pytest tests/integration/ --collect-only

# Run all integration tests
pytest tests/integration/ -v

# Run specific suite
pytest tests/integration/bifrost/ -v
pytest tests/integration/smartcp/ -v
pytest tests/integration/cross_sdk/ -v
```

## Environment Variables

Some tests may require environment variables:

```bash
# Bifrost API (if using real HTTP client)
export BIFROST_API_KEY="your-api-key"
export BIFROST_BASE_URL="http://localhost:8000"

# SmartCP / Supabase (if using real database)
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"

# Optional: Enable real LLM tests
export ENABLE_LLM_TESTS="false"  # Set to "true" to enable
```

## Troubleshooting

### Import Errors

```bash
# ModuleNotFoundError: No module named 'bifrost_extensions'
pip install -e bifrost_extensions/

# ModuleNotFoundError: No module named 'router'
# Make sure router_core is accessible
export PYTHONPATH="${PYTHONPATH}:${PWD}/router"
```

### Async Test Errors

```bash
# RuntimeError: Event loop is closed
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check conftest.py has event_loop fixture
grep "event_loop" tests/conftest.py
```

### Performance Test Failures

```bash
# Latency targets not met (on slow machines)
# Set PERFORMANCE_RELAXED=true to use relaxed targets
export PERFORMANCE_RELAXED="true"

# Or skip performance tests
pytest tests/integration/ -v -m "not performance"
```

### Mock vs Real Integration

Current tests use mocked router service. To use real integration:

```bash
# Set environment variable
export USE_REAL_ROUTER="true"

# Run tests
pytest tests/integration/bifrost/ -v
```

## Development Workflow

### 1. Create New Test

```bash
# Create test file
touch tests/integration/bifrost/test_new_feature.py

# Use template
cat > tests/integration/bifrost/test_new_feature.py << 'EOF'
"""Test description."""

import pytest

class TestNewFeature:
    """Test class description."""

    @pytest.mark.asyncio
    async def test_basic_scenario(self, gateway_client):
        """Test basic scenario."""
        result = await gateway_client.route(...)
        assert result is not None
EOF
```

### 2. Run Test Locally

```bash
# Run single test
pytest tests/integration/bifrost/test_new_feature.py -v

# With verbose output
pytest tests/integration/bifrost/test_new_feature.py -vv -s
```

### 3. Check Coverage

```bash
# Run with coverage
pytest tests/integration/bifrost/test_new_feature.py --cov=bifrost_extensions --cov-report=term-missing

# Generate HTML report
pytest tests/integration/ --cov=bifrost_extensions --cov-report=html
open htmlcov/index.html
```

### 4. Add to CI/CD

```yaml
# .github/workflows/integration.yml
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio pytest-cov
          pip install -e bifrost_extensions/
          pip install -r requirements.txt
      - name: Run integration tests
        run: ./tests/integration/run_integration_tests.sh all coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Docker Setup (Optional)

```dockerfile
# Dockerfile.integration-tests
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install pytest pytest-asyncio pytest-cov

# Copy code
COPY . .

# Install SDKs
RUN pip install -e bifrost_extensions/
RUN pip install -e .

# Run tests
CMD ["./tests/integration/run_integration_tests.sh", "all"]
```

```bash
# Build and run
docker build -f Dockerfile.integration-tests -t smartcp-integration-tests .
docker run smartcp-integration-tests
```

## Performance Tuning

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/integration/ -v -n auto

# Or specify number of workers
pytest tests/integration/ -v -n 4
```

### Test Isolation

```bash
# Run each test in separate process (slower but safer)
pytest tests/integration/ -v --forked
```

### Caching

```bash
# Cache test results
pytest tests/integration/ -v --cache-clear  # Clear cache
pytest tests/integration/ -v --lf           # Run last failed
pytest tests/integration/ -v --ff           # Run failed first
```

## Debugging

### Interactive Debugging

```bash
# Drop into debugger on failure
pytest tests/integration/ -v --pdb

# Drop into debugger on first failure
pytest tests/integration/ -v -x --pdb
```

### Verbose Output

```bash
# Show print statements
pytest tests/integration/ -v -s

# Show full diff on assertion failures
pytest tests/integration/ -v --tb=long

# Show local variables in tracebacks
pytest tests/integration/ -v -l
```

### Profiling

```bash
# Show slowest tests
pytest tests/integration/ -v --durations=10

# Show all test durations
pytest tests/integration/ -v --durations=0

# Profile test execution
pytest tests/integration/ -v --profile
```

## Best Practices

### 1. Fixture Usage

```python
# Use existing fixtures from conftest.py
@pytest.mark.asyncio
async def test_with_fixtures(gateway_client, sample_messages):
    result = await gateway_client.route(messages=sample_messages)
    assert result is not None
```

### 2. Test Isolation

```python
# Each test should be independent
@pytest.mark.asyncio
async def test_isolated(gateway_client):
    # Don't rely on state from other tests
    result = await gateway_client.route(...)
    assert result is not None
```

### 3. Clear Assertions

```python
# Provide clear error messages
assert response.model.estimated_cost_usd <= 0.001, \
    f"Cost {response.model.estimated_cost_usd} exceeds limit"
```

### 4. Markers

```python
# Use markers appropriately
@pytest.mark.asyncio              # For async tests
@pytest.mark.performance          # For performance tests
@pytest.mark.slow                 # For slow tests (>10s)
@pytest.mark.integration          # For integration tests
```

## Support

For issues or questions:
1. Check README.md
2. Review TEST_SUMMARY.md
3. Check conftest.py for fixtures
4. Run with `-vv` for verbose output
5. Use `--pdb` to debug failures

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
