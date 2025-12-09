# E2E Testing Guide

Comprehensive guide for running End-to-End tests that validate all services working together locally.

## Overview

E2E tests validate the complete stack running together:

- **Bifrost Gateway** (localhost:8000) - HTTP routing and API
- **Go GraphQL Backend** (localhost:8080) - GraphQL queries and subscriptions
- **MLX gRPC Service** (localhost:8001) - Model inference and classification
- **SmartCP MCP Server** - Tool execution (stdio + HTTP)

## Prerequisites

### 1. Docker and Docker Compose

```bash
# Verify Docker is installed
docker --version
docker-compose --version
```

### 2. Services Configuration

Create `docker-compose.local.yml` with all services:

```yaml
version: '3.8'

services:
  bifrost:
    image: bifrost-gateway:latest
    ports:
      - "8000:8000"
    environment:
      - GRAPHQL_URL=http://graphql:8080
      - GRPC_URL=grpc:8001
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 3s
      retries: 10

  graphql:
    image: go-backend:latest
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://...
      - GRPC_URL=grpc:8001
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 5s
      timeout: 3s
      retries: 10

  grpc:
    image: mlx-service:latest
    ports:
      - "8001:8001"
    healthcheck:
      test: ["CMD", "grpc_health_probe", "-addr=localhost:8001"]
      interval: 5s
      timeout: 3s
      retries: 10

  # Optional: SmartCP HTTP endpoint
  smartcp:
    build: .
    ports:
      - "8002:8002"
    command: python server.py --http
```

### 3. Python Dependencies

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx grpc grpcio-health-checking

# Or with uv
uv pip install pytest pytest-asyncio httpx grpc grpcio-health-checking
```

## Running E2E Tests

### Quick Start

```bash
# Run all E2E tests (starts services automatically)
./tests/e2e/run_e2e_tests.sh
```

### Manual Steps

```bash
# 1. Start services
docker-compose -f docker-compose.local.yml up -d

# 2. Wait for services
python tests/e2e/utils/wait_for_services.py

# 3. Run tests
pytest tests/e2e/ -v -m e2e

# 4. Cleanup
docker-compose -f docker-compose.local.yml down
```

### Running Specific Test Categories

```bash
# Bifrost tests only
pytest tests/e2e/bifrost/ -v

# SmartCP tests only
pytest tests/e2e/smartcp/ -v

# Integration tests only
pytest tests/e2e/integration/ -v -m integration

# Smoke tests (fast)
pytest tests/e2e/ -v -m smoke

# Skip slow tests
pytest tests/e2e/ -v -m "e2e and not slow"
```

## Test Structure

```
tests/e2e/
├── conftest.py                    # Shared fixtures
├── run_e2e_tests.sh              # Test runner script
├── E2E_TESTING_GUIDE.md          # This file
├── bifrost/
│   └── test_bifrost_live.py      # Bifrost stack tests
├── smartcp/
│   └── test_smartcp_live.py      # SmartCP MCP tests
├── integration/
│   └── test_full_flow_live.py    # End-to-end workflows
└── utils/
    ├── wait_for_services.py      # Health check utility
    └── cleanup.py                # Cleanup utility
```

## Environment Variables

Configure via environment variables:

```bash
# Service URLs
export E2E_BIFROST_URL="http://localhost:8000"
export E2E_GRAPHQL_URL="http://localhost:8080/graphql"
export E2E_GRPC_URL="localhost:8001"
export E2E_SMARTCP_HTTP_URL="http://localhost:8002"

# Test configuration
export E2E_TIMEOUT="30"
export E2E_TEST_WORKSPACE_ID="test-workspace-123"
export E2E_TEST_USER_ID="test-user-123"

# Cleanup
export CLEANUP_DATA="true"

# Run tests
pytest tests/e2e/ -v
```

## Test Categories

### Smoke Tests (`@pytest.mark.smoke`)

Fast tests that validate basic functionality:

```bash
pytest tests/e2e/ -v -m smoke
# Expected: <30 seconds
```

### Integration Tests (`@pytest.mark.integration`)

Tests that validate cross-service interactions:

```bash
pytest tests/e2e/ -v -m integration
# Expected: 2-5 minutes
```

### Performance Tests (`@pytest.mark.slow`)

Tests that measure performance under load:

```bash
pytest tests/e2e/ -v -m slow
# Expected: 5-10 minutes
```

## What Each Test Validates

### Bifrost Tests (`test_bifrost_live.py`)

- ✅ Health endpoint
- ✅ Routing decisions
- ✅ Tool execution
- ✅ GraphQL queries
- ✅ gRPC classification
- ✅ Semantic search
- ✅ Concurrent requests
- ✅ GraphQL subscriptions
- ✅ Error handling

### SmartCP Tests (`test_smartcp_live.py`)

- ✅ MCP server initialization (stdio)
- ✅ Tool listing
- ✅ Tool execution
- ✅ Memory tool
- ✅ State management
- ✅ Bifrost delegation
- ✅ HTTP transport (if available)
- ✅ Concurrent tool calls
- ✅ Error handling

### Integration Tests (`test_full_flow_live.py`)

- ✅ Route → Execute flow
- ✅ Classification → Routing → Execution
- ✅ Semantic search → Tool discovery
- ✅ Multi-tool workflows
- ✅ Error recovery
- ✅ Concurrent workflows
- ✅ Subscription-based workflows
- ✅ Performance under load

## Performance Expectations

| Test | Expected Duration | Performance Threshold |
|------|------------------|----------------------|
| Health checks | <1s | <1s |
| Routing | <5s | <5s |
| Tool execution | <10s | <10s |
| Search | <5s | <5s |
| Full workflow | <15s | <15s |
| Concurrent (10 ops) | <10s | <10s |
| Load test (50 ops) | <60s | <60s |

## Debugging Failed Tests

### Check Service Logs

```bash
# All services
docker-compose -f docker-compose.local.yml logs

# Specific service
docker-compose -f docker-compose.local.yml logs bifrost
docker-compose -f docker-compose.local.yml logs graphql
docker-compose -f docker-compose.local.yml logs grpc
```

### Run Individual Test with Verbose Output

```bash
pytest tests/e2e/bifrost/test_bifrost_live.py::test_bifrost_health -v -s
```

### Check Service Health Manually

```bash
# Bifrost
curl http://localhost:8000/health

# GraphQL
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'

# gRPC (requires grpcurl)
grpcurl -plaintext localhost:8001 grpc.health.v1.Health/Check
```

### Inspect Network

```bash
# Show network connections
docker-compose -f docker-compose.local.yml ps
docker network inspect smartcp_default
```

### Common Issues

#### Services Not Starting

```bash
# Check Docker resources
docker system df
docker system prune  # If low on space

# Rebuild images
docker-compose -f docker-compose.local.yml build --no-cache
docker-compose -f docker-compose.local.yml up -d
```

#### Connection Refused

- Verify services are running: `docker-compose ps`
- Check port mappings: `docker-compose -f docker-compose.local.yml config`
- Verify URLs in environment variables

#### Timeout Errors

- Increase timeout: `export E2E_TIMEOUT=60`
- Check service logs for slow operations
- Verify system resources (CPU, memory)

#### Test Data Conflicts

```bash
# Clean up test data
python tests/e2e/utils/cleanup.py test-workspace-123

# Or use cleanup flag
CLEANUP_DATA=true ./tests/e2e/run_e2e_tests.sh
```

## Adding New E2E Tests

### Test Template

```python
import pytest

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_my_new_feature(
    bifrost_client,
    smartcp_stdio_client,
    track_performance
):
    """Test description."""
    stop = track_performance("my_feature")

    # Arrange
    # ... setup

    # Act
    result = await bifrost_client.some_operation()

    # Assert
    assert result.success

    duration = stop()
    assert duration < 5.0, f"Too slow: {duration:.3f}s"
```

### Best Practices

1. **Use fixtures**: Leverage shared fixtures from `conftest.py`
2. **Track performance**: Use `track_performance` fixture
3. **Mark appropriately**: Add `@pytest.mark.e2e` and other markers
4. **Clean up**: Use `cleanup_test_data` fixture for cleanup
5. **Assert performance**: Include duration assertions
6. **Handle errors**: Test both success and failure cases

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose -f docker-compose.local.yml up -d

      - name: Wait for services
        run: python tests/e2e/utils/wait_for_services.py

      - name: Run E2E tests
        run: pytest tests/e2e/ -v -m e2e

      - name: Cleanup
        if: always()
        run: docker-compose -f docker-compose.local.yml down
```

## Maintenance

### Regular Tasks

- **Weekly**: Review performance metrics, update thresholds
- **Monthly**: Update service images, verify compatibility
- **After changes**: Run full E2E suite before deploying

### Updating Tests

When adding new features:

1. Add E2E test for the feature
2. Update this guide if new patterns introduced
3. Update docker-compose if new services added
4. Verify all tests still pass

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Bifrost API docs](../../../docs/bifrost-api.md)
- [SmartCP MCP docs](../../../docs/smartcp-mcp.md)

## Support

For issues with E2E tests:

1. Check service logs: `docker-compose logs`
2. Verify configuration: Environment variables, compose file
3. Run health checks: `python tests/e2e/utils/wait_for_services.py`
4. Review this guide's troubleshooting section
5. Open issue with logs and test output
