## Integration Test Suite for Bifrost SDK and SmartCP SDK

Comprehensive integration tests ensuring production-ready quality and performance across both SDKs.

### Test Structure

```
tests/integration/
├── bifrost/
│   ├── conftest.py                          # Bifrost test fixtures
│   ├── test_routing_integration.py          # Model routing tests
│   ├── test_tool_routing_integration.py     # Tool routing tests
│   └── test_performance.py                  # Performance benchmarks
├── smartcp/
│   ├── conftest.py                          # SmartCP test fixtures
│   ├── test_mcp_server.py                   # MCP server tests
│   ├── test_bifrost_client.py               # BifrostClient integration
│   └── test_tool_execution.py               # Tool execution tests
└── cross_sdk/
    └── test_bifrost_smartcp_integration.py  # Cross-SDK integration
```

### Bifrost SDK Tests

#### 1. Routing Integration (`test_routing_integration.py`)
- **Basic routing**: Single message routing with all strategies
- **Strategy comparison**: All 5 routing strategies (cost, performance, speed, balanced, pareto)
- **Constraints**: Cost and latency constraints
- **Context**: Additional routing context
- **Alternatives**: Alternative model recommendations
- **Error handling**: Validation, timeout, and error scenarios
- **Performance**: P50/P95/P99 latency targets (<30ms/<50ms/<100ms)
- **Concurrency**: 100 simultaneous requests

#### 2. Tool Routing Integration (`test_tool_routing_integration.py`)
- **Basic tool routing**: Action → Tool mapping
- **Semantic routing**: Web search, code search, doc search
- **Context-aware routing**: Domain-specific routing
- **Validation**: Empty action/tools error handling
- **Performance**: P95 latency <100ms
- **Concurrency**: 100 simultaneous tool routes
- **Semantics**: Similar actions → consistent routing
- **Edge cases**: Single tool, many tools, ambiguous actions

#### 3. Performance Tests (`test_performance.py`)
- **Latency percentiles**: P50/P95/P99 across 1000 requests
- **Concurrent scalability**: 10/50/100/200 concurrent requests
- **Strategy comparison**: Performance across all strategies
- **Message size impact**: Tiny/small/medium/large messages
- **Tool routing throughput**: 500+ requests, throughput >50 RPS
- **Memory leak detection**: Object growth <10%
- **Sustained load**: 60s at 10 RPS with <1% error rate
- **Burst handling**: 50/100/200/500 request bursts with >95% success

### SmartCP SDK Tests

#### 1. MCP Server Tests (`test_mcp_server.py`)
- **Stdio transport**: Tool registration and execution
- **HTTP transport**: Server initialization, concurrent requests
- **Tool execution**: Valid/invalid parameters, timeouts
- **Performance**: Tool execution latency P95 <400ms
- **Security**: Input validation, sandboxing

#### 2. BifrostClient Integration (`test_bifrost_client.py`)
- Integration with Bifrost routing
- Tool execution via BifrostClient
- Error handling and retries

#### 3. Tool Execution Tests (`test_tool_execution.py`)
- Direct tool execution
- Parameter validation
- Sandbox restrictions
- Performance benchmarks

### Cross-SDK Integration Tests

#### Test Scenarios (`test_bifrost_smartcp_integration.py`)

1. **Gateway to SmartCP delegation**
   - Bifrost routes request
   - SmartCP executes tool with selected model

2. **SmartCP to Bifrost routing**
   - SmartCP tool needs model selection
   - Uses Bifrost for routing

3. **Agent-CLI pattern**
   - GatewayClient + ToolClient working together
   - End-to-end workflow

4. **End-to-end workflow**
   - Classification → Routing → Tool execution
   - Multi-step pipeline

5. **Cost optimization**
   - Route with cost constraints
   - Execute with cost-optimized model

6. **Performance optimization**
   - Route with latency constraints
   - Execute with speed-optimized model

### Running Tests

```bash
# All integration tests
pytest tests/integration/ -v

# Bifrost tests only
pytest tests/integration/bifrost/ -v

# SmartCP tests only
pytest tests/integration/smartcp/ -v

# Cross-SDK tests only
pytest tests/integration/cross_sdk/ -v

# Performance tests only
pytest tests/integration/ -v -m performance

# Skip slow tests
pytest tests/integration/ -v -m "not slow"

# With coverage
pytest tests/integration/ -v --cov=bifrost_extensions --cov=smartcp --cov-report=html
```

### Performance Targets

| Metric | Target | Test |
|--------|--------|------|
| **Routing P50** | <30ms | `test_routing_latency_p50` |
| **Routing P95** | <50ms | `test_routing_latency_p95` |
| **Routing P99** | <100ms | `test_routing_latency_p99` |
| **Tool Routing P95** | <100ms | `test_tool_routing_latency` |
| **Tool Execution P95** | <400ms | `test_tool_execution_latency` |
| **Concurrent Requests** | 100+ | `test_concurrent_routing` |
| **Throughput** | >10 RPS | `test_concurrent_routing_scalability` |
| **Error Rate** | <1% | `test_sustained_load` |
| **Memory Growth** | <10% | `test_memory_leak_detection` |

### Fixtures

#### Bifrost Fixtures (`bifrost/conftest.py`)
- `gateway_client`: Mocked GatewayClient with router service
- `sample_messages`: Test message sets (simple, complex, code-focused)
- `sample_tools`: Tool names for routing tests
- `routing_strategies`: All 5 routing strategies
- `performance_config`: Performance test configuration

#### SmartCP Fixtures (`smartcp/conftest.py`)
- `mock_mcp_server`: Mocked MCP server
- `mock_bifrost_client`: Mocked BifrostClient
- `sample_tool_definition`: Tool schema
- `auth_config`: OAuth and API key configs
- `sandbox_config`: Sandbox restrictions

### Test Markers

```python
@pytest.mark.asyncio          # Async test
@pytest.mark.performance      # Performance test
@pytest.mark.slow             # Slow test (>10s)
@pytest.mark.integration      # Integration test
```

### Coverage Requirements

- **Line coverage**: >80%
- **Branch coverage**: >75%
- **Critical paths**: 100% (routing, tool execution, error handling)

### Continuous Integration

Tests run automatically on:
- Every commit (fast suite)
- Pull requests (full suite)
- Main branch merge (full suite + performance)
- Nightly (sustained load tests)

### Debugging Failed Tests

```bash
# Run specific test with verbose output
pytest tests/integration/bifrost/test_routing_integration.py::TestRoutingIntegration::test_basic_routing -vv

# Run with print statements
pytest tests/integration/ -v -s

# Run with debugger on failure
pytest tests/integration/ -v --pdb

# Show slowest tests
pytest tests/integration/ -v --durations=10
```

### Adding New Tests

1. **Choose appropriate location**:
   - `bifrost/` for Bifrost-only tests
   - `smartcp/` for SmartCP-only tests
   - `cross_sdk/` for integration between SDKs

2. **Use existing fixtures**:
   - Check `conftest.py` for available fixtures
   - Add new fixtures if needed

3. **Follow naming conventions**:
   - `test_<feature>_<scenario>.py`
   - `test_<component>_<behavior>`

4. **Add markers**:
   - `@pytest.mark.asyncio` for async tests
   - `@pytest.mark.performance` for perf tests
   - `@pytest.mark.slow` for slow tests

5. **Document expected behavior**:
   - Clear docstrings
   - Assertions with error messages

### Known Issues

- Mock router service doesn't test actual HTTP integration (Phase 2)
- GraphQL subscription tests require running server (Phase 3)
- Sandbox tests need actual Python interpreter isolation (Phase 3)

### Future Enhancements

1. **GraphQL Integration Tests**
   - Query execution
   - Mutation validation
   - Subscription events

2. **Auth Flow Tests**
   - OAuth 2.0 flow
   - API key rotation
   - Token refresh

3. **Real Database Tests**
   - Supabase integration
   - Transaction handling
   - Connection pooling

4. **Load Testing**
   - Extended sustained load (hours)
   - Stress testing (thousands of RPS)
   - Chaos engineering (failure injection)
