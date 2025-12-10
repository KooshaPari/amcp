# SmartCP Test Suite

Comprehensive test suite for SmartCP runtime system.

## Test Structure

```
tests/
├── unit/              # Unit tests (isolated components)
│   └── runtime/       # Runtime unit tests
├── component/         # Component tests (components working together)
│   └── runtime/      # Runtime component tests
├── integration/      # Integration tests (full system)
├── e2e/              # End-to-end tests (complete workflows)
├── smoke/            # Smoke tests (quick validation)
└── performance/      # Performance tests (load, concurrency)
```

## Running Tests

### All Tests
```bash
pytest tests/
```

### By Category
```bash
# Unit tests only
pytest tests/unit/ -m unit

# Component tests
pytest tests/component/ -m component

# Integration tests
pytest tests/integration/ -m integration

# E2E tests
pytest tests/e2e/ -m e2e

# Smoke tests (fast)
pytest tests/smoke/ -m smoke

# Performance tests
pytest tests/performance/ -m performance
```

### With Coverage
```bash
pytest tests/ --cov=smartcp --cov-report=html
```

### Specific Test File
```bash
pytest tests/unit/runtime/test_tools_registry.py -v
```

## Test Categories

### Unit Tests
- Test individual components in isolation
- Mock dependencies
- Fast execution
- High coverage

### Component Tests
- Test components working together
- Real dependencies
- Integration between 2-3 components

### Integration Tests
- Test full system integration
- All components working together
- Real runtime execution

### E2E Tests
- Complete workflows from MCP tool call
- Real server integration
- Full user scenarios

### Smoke Tests
- Quick validation of basic functionality
- Run in CI/CD pipelines
- Fast feedback

### Performance Tests
- Load testing
- Concurrent execution
- Memory usage
- Response times

## Test Coverage Goals

- Unit tests: >90% coverage
- Component tests: >80% coverage
- Integration tests: Critical paths only
- E2E tests: Main user workflows

## Writing Tests

### Unit Test Example
```python
@pytest.mark.asyncio
async def test_feature():
    component = Component()
    result = await component.method()
    assert result == expected
```

### Component Test Example
```python
@pytest.mark.asyncio
async def test_component_integration():
    component1 = Component1()
    component2 = Component2(component1)
    result = await component2.method()
    assert result is not None
```

### Integration Test Example
```python
@pytest.mark.asyncio
async def test_full_workflow():
    runtime = AgentRuntime()
    result = await runtime.execute(code, user_ctx)
    assert result.status == ExecutionStatus.COMPLETED
```
