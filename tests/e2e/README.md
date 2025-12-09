# E2E Test Suite

Comprehensive End-to-End tests for SmartCP and Bifrost integration.

## Quick Start

```bash
# Run all E2E tests (automated)
./run_e2e_tests.sh

# Or manually
docker-compose -f docker-compose.local.yml up -d
python utils/wait_for_services.py
pytest . -v -m e2e
docker-compose -f docker-compose.local.yml down
```

## Test Structure

```
tests/e2e/
├── bifrost/               # Bifrost Gateway tests
├── smartcp/               # SmartCP MCP tests
├── integration/           # Full workflow tests
└── utils/                 # Test utilities
```

## Test Categories

- **Smoke** (`-m smoke`): Fast sanity checks (<30s)
- **Integration** (`-m integration`): Cross-service flows (2-5min)
- **Slow** (`-m slow`): Performance/load tests (5-10min)

## Key Tests

### Bifrost Tests
- ✅ Health and routing
- ✅ Tool execution
- ✅ GraphQL queries
- ✅ gRPC classification
- ✅ Semantic search
- ✅ Subscriptions

### SmartCP Tests
- ✅ MCP initialization
- ✅ Tool listing/execution
- ✅ Memory and state
- ✅ Bifrost delegation
- ✅ HTTP transport

### Integration Tests
- ✅ Route → Execute flows
- ✅ Multi-tool workflows
- ✅ Error recovery
- ✅ Concurrent operations
- ✅ Performance under load

## Configuration

```bash
export E2E_BIFROST_URL="http://localhost:8000"
export E2E_GRAPHQL_URL="http://localhost:8080/graphql"
export E2E_GRPC_URL="localhost:8001"
export E2E_SMARTCP_HTTP_URL="http://localhost:8002"
```

## Documentation

See **[E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)** for complete documentation.

## Support

- Check service logs: `docker-compose logs`
- Run health checks: `python utils/wait_for_services.py`
- Clean test data: `python utils/cleanup.py`
