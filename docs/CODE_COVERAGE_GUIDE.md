# Code Coverage Guide

This guide walks you through using code coverage for tests in this project.

## Overview

Code coverage measures which lines of your code are executed during tests. The project uses:
- **pytest-cov** (≥4.1.0) - Coverage plugin for pytest
- **coverage.py** - Underlying coverage tool
- **Target**: >80% coverage for critical paths

## Quick Start

### 1. Run Tests with Coverage (CLI - Recommended)

```bash
# Via project CLI (if available)
python cli.py test run --coverage

# Or directly with pytest
uv run pytest --cov=. --cov-report=term-missing
```

### 2. Generate HTML Report

```bash
# Generate HTML report (opens in browser)
uv run pytest --cov=. --cov-report=html
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### 3. View Coverage Summary

```bash
# Terminal summary with missing lines
uv run pytest --cov=. --cov-report=term-missing

# JSON report
uv run pytest --cov=. --cov-report=json
```

## Coverage Commands

### Basic Coverage

```bash
# Run tests with coverage
uv run pytest --cov=.

# Specify source directory
uv run pytest --cov=src

# Multiple source directories
uv run pytest --cov=src --cov=tools --cov=services
```

### Coverage Reports

```bash
# Terminal report (default)
uv run pytest --cov=. --cov-report=term

# Terminal report showing missing lines
uv run pytest --cov=. --cov-report=term-missing

# HTML report
uv run pytest --cov=. --cov-report=html

# XML report (for CI/CD)
uv run pytest --cov=. --cov-report=xml

# JSON report
uv run pytest --cov=. --cov-report=json

# Multiple formats
uv run pytest --cov=. --cov-report=term --cov-report=html --cov-report=xml
```

### Coverage Scope

```bash
# Unit tests only
uv run pytest tests/unit --cov=. --cov-report=term-missing

# Integration tests only
uv run pytest tests/integration --cov=. --cov-report=term-missing

# Specific test file
uv run pytest tests/unit/test_auth.py --cov=. --cov-report=term-missing

# Specific module
uv run pytest --cov=auth --cov-report=term-missing
```

## Configuration

### Coverage Configuration File

Create `.coveragerc` or `pyproject.toml` section:

**`.coveragerc`:**
```ini
[run]
source = .
omit =
    tests/*
    */venv/*
    */__pycache__/*
    */migrations/*
    */conftest.py
    setup.py

[report]
precision = 2
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

**`pyproject.toml` (alternative):**
```toml
[tool.coverage.run]
source = ["."]
omit = [
    "tests/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]

[tool.coverage.html]
directory = "htmlcov"
```

### Pytest Configuration

Add to `pytest.ini`:

```ini
[pytest]
addopts = 
    --cov=.
    --cov-report=term-missing
    --cov-report=html
```

## Understanding Coverage Reports

### Terminal Output

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
auth/__init__.py                 5      0   100%
auth/token.py                   45      8    82%   23-30
auth/validators.py              30     15    50%   10-25
-----------------------------------------------------------
TOTAL                          500    100    80%
```

**Columns:**
- **Stmts**: Total statements (lines of code)
- **Miss**: Missed statements (not executed)
- **Cover**: Coverage percentage
- **Missing**: Line numbers not covered

### HTML Report

1. **Overview**: Summary by module
2. **File View**: Line-by-line coverage with:
   - Green: Covered
   - Red: Not covered
   - Yellow: Partially covered (branches)

## Coverage Targets

### Project Standards

- **Overall**: >80% coverage
- **Critical paths**: 100% coverage
- **New code**: Must maintain or improve coverage
- **Edge cases**: Comprehensive coverage

### What to Exclude

```python
# Exclude from coverage
if TYPE_CHECKING:  # Type checking only
    from typing import Protocol

def __repr__(self) -> str:  # Usually not tested
    return f"{self.__class__.__name__}()"

# Mark as intentionally not covered
def experimental_feature():  # pragma: no cover
    pass
```

## Best Practices

### 1. Run Coverage Regularly

```bash
# Before committing
uv run pytest --cov=. --cov-report=term-missing

# In CI/CD
uv run pytest --cov=. --cov-report=xml
```

### 2. Focus on Critical Paths

```bash
# Test critical modules
uv run pytest --cov=auth --cov=services --cov-report=term-missing
```

### 3. Use Coverage to Find Gaps

```bash
# Find files with low coverage
uv run pytest --cov=. --cov-report=term-missing | grep -E "^\w.*\s+\d+\s+\d+\s+[0-4]\d%"
```

### 4. Incremental Coverage

```bash
# Check coverage for changed files only
git diff --name-only main | grep '\.py$' | xargs pytest --cov=. --cov-report=term-missing
```

## Common Workflows

### Workflow 1: Full Coverage Report

```bash
# 1. Run all tests with coverage
uv run pytest --cov=. --cov-report=html

# 2. Open HTML report
open htmlcov/index.html

# 3. Review missing lines
# 4. Write tests for uncovered code
# 5. Re-run to verify improvement
```

### Workflow 2: Coverage for New Feature

```bash
# 1. Write feature code
# 2. Run tests with coverage
uv run pytest tests/unit/test_new_feature.py --cov=new_feature --cov-report=term-missing

# 3. Check coverage percentage
# 4. Add tests for uncovered lines
# 5. Aim for >80% coverage
```

### Workflow 3: Coverage in CI/CD

```bash
# Generate XML for CI tools (Codecov, Coveralls, etc.)
uv run pytest --cov=. --cov-report=xml

# Upload to coverage service
# Example with Codecov:
codecov -f coverage.xml
```

## Troubleshooting

### Coverage Not Showing

```bash
# Check pytest-cov is installed
uv pip list | grep pytest-cov

# Install if missing
uv pip install pytest-cov>=4.1.0

# Verify installation
python -c "import pytest_cov; print('OK')"
```

### Coverage Too Low

```bash
# Find files with lowest coverage
uv run pytest --cov=. --cov-report=term | sort -k4 -n

# Focus on one file at a time
uv run pytest tests/unit/test_low_coverage.py --cov=low_coverage --cov-report=term-missing
```

### Coverage Includes Test Files

```bash
# Exclude tests in .coveragerc
[run]
omit = tests/*

# Or in command
uv run pytest --cov=. --cov-config=.coveragerc
```

### Branch Coverage

```bash
# Include branch coverage
uv run pytest --cov=. --cov-branch --cov-report=term-missing
```

## Advanced Usage

### Coverage for Specific Modules

```bash
# Only measure coverage for specific packages
uv run pytest --cov=auth --cov=services --cov-report=term-missing
```

### Combine with Markers

```bash
# Coverage for unit tests only
uv run pytest -m unit --cov=. --cov-report=term-missing

# Coverage excluding slow tests
uv run pytest -m "not slow" --cov=. --cov-report=term-missing
```

### Coverage Thresholds

```bash
# Fail if coverage below threshold (requires pytest-cov plugin)
uv run pytest --cov=. --cov-fail-under=80
```

### Parallel Coverage

```bash
# Run tests in parallel with coverage
uv run pytest -n auto --cov=. --cov-report=term-missing
```

## Integration with Tools

### VS Code

Install "Coverage Gutters" extension:
1. Run coverage: `uv run pytest --cov=. --cov-report=xml`
2. Extension shows coverage inline
3. Green/red indicators on lines

### CI/CD Integration

**GitHub Actions:**
```yaml
- name: Run tests with coverage
  run: |
    uv run pytest --cov=. --cov-report=xml --cov-report=term
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

**GitLab CI:**
```yaml
test:
  script:
    - uv run pytest --cov=. --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Current Coverage Status

Check `coverage.json` for current coverage data:

```bash
# View coverage summary
cat coverage.json | python -m json.tool | grep -A 5 totals
```

## Resources

- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [coverage.py Documentation](https://coverage.readthedocs.io/)
- [Project Testing Guide](docs/TESTING.md)

## Quick Reference

```bash
# Basic coverage
uv run pytest --cov=.

# HTML report
uv run pytest --cov=. --cov-report=html && open htmlcov/index.html

# Missing lines
uv run pytest --cov=. --cov-report=term-missing

# Specific module
uv run pytest --cov=auth --cov-report=term-missing

# Fail if below threshold
uv run pytest --cov=. --cov-fail-under=80
```
