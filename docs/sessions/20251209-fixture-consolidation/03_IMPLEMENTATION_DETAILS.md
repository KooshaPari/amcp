# Implementation Details

## Fixture Modules Structure

### `/tests/fixtures/__init__.py`
**Purpose**: Central import point for all fixture modules
**Lines**: 63
**Content**:
- Imports from submodules (clients, database, models, config)
- `__all__` export list for all fixtures
- Docstring explaining module organization

**Provides Access To**:
```python
from tests.fixtures import (
    # Clients
    mock_mcp_server,
    mock_bifrost_client,
    gateway_client,
    mock_router_service,
    # Database
    adapter,
    # Models
    sample_messages,
    sample_messages_simple,
    sample_messages_complex,
    sample_tools,
    sample_graphql_query,
    sample_graphql_mutation,
    sample_tool_definition,
    # Config
    auth_config,
    sandbox_config,
    subscription_config,
    performance_config,
    error_scenarios,
    routing_strategies,
)
```

### `/tests/fixtures/clients.py`
**Purpose**: Mock server and client fixtures
**Lines**: 102
**Fixtures Provided**: 4

#### 1. `mock_mcp_server()`
```python
@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    server = MagicMock()
    server.name = "test-mcp-server"
    server.version = "1.0.0"
    return server
```

**Usage**: SmartCP integration tests
**Dependencies**: unittest.mock
**Scope**: Function (default)

#### 2. `mock_bifrost_client()`
```python
@pytest.fixture
def mock_bifrost_client():
    """Mock BifrostClient for SmartCP tests."""
    client = AsyncMock()
    async def mock_route(*args, **kwargs):
        return {
            "model": {
                "model_id": "claude-sonnet-4",
                "provider": "anthropic",
                "estimated_cost_usd": 0.005,
                "estimated_latency_ms": 200,
            },
            "confidence": 0.9,
        }
    client.route = mock_route
    return client
```

**Usage**: Tests requiring Bifrost client interaction
**Dependencies**: unittest.mock
**Scope**: Function
**Returns**: AsyncMock with route method

#### 3. `mock_router_service()`
```python
@pytest.fixture
def mock_router_service():
    """Mock RoutingService for integration tests."""
    # Complex setup with:
    # - Mock Model object
    # - Mock Classification object
    # - Mock RoutingPlan object
    # - async build_plan method
    return mock_service
```

**Usage**: Bifrost routing tests
**Dependencies**: router.router_core (optional, handles ImportError)
**Scope**: Function
**Complexity**: High - requires external types

#### 4. `gateway_client()`
```python
@pytest.fixture
async def gateway_client(mock_router_service):
    """Create GatewayClient with mocked router service."""
    try:
        from bifrost_extensions import GatewayClient
        # Setup with mocked router
        yield client
    except ImportError:
        yield None
```

**Usage**: Bifrost gateway tests
**Dependencies**: bifrost_extensions (optional)
**Scope**: Function
**Fixtures Used**: mock_router_service
**Behavior**: Gracefully handles missing bifrost_extensions

### `/tests/fixtures/models.py`
**Purpose**: Sample data and model definitions for testing
**Lines**: 118
**Fixtures Provided**: 7

#### 1. `sample_messages()`
Three-message conversation:
- User: "Write a Python function to parse JSON"
- Assistant: "Here's a function to parse JSON..."
- User: "Add error handling"

#### 2. `sample_messages_simple()`
Single message for minimal testing:
- User: "Hello"

#### 3. `sample_messages_complex()`
Six-turn conversation:
- System prompt setup
- User: Implement binary search tree
- Assistant: BST implementation
- User: Add deletion with rebalancing
- Assistant: Deletion logic
- User: Optimize for cache locality

#### 4. `sample_tools()`
List of tool names:
- web_search
- doc_search
- code_search
- file_search

#### 5. `sample_graphql_query()`
GraphQL query for user data retrieval

#### 6. `sample_graphql_mutation()`
GraphQL mutation for entity creation

#### 7. `sample_tool_definition()`
Complete tool schema with:
- Name: test_tool
- Description: A test tool for integration testing
- Input schema with properties and required fields

**Special Feature**: Resilient to missing imports
```python
try:
    from bifrost_extensions.models import Message
    return [Message(role="user", content="..."), ...]
except ImportError:
    # Fallback to dict format
    return [{"role": "user", "content": "..."}, ...]
```

### `/tests/fixtures/config.py`
**Purpose**: Configuration objects for various testing scenarios
**Lines**: 113
**Fixtures Provided**: 6

#### 1. `auth_config()`
OAuth and API key authentication configuration

#### 2. `sandbox_config()`
Sandbox execution environment settings:
- Timeout: 30 seconds
- Memory limit: 512 MB
- Allowed/blocked imports

#### 3. `subscription_config()`
Subscription and connection settings:
- WebSocket and SSE transports
- Max 100 concurrent connections
- 30 second keepalive interval

#### 4. `performance_config()`
Performance testing targets:
- 100 concurrent requests
- P50 latency: 30ms
- P95 latency: 50ms
- P99 latency: 100ms
- Timeout: 5000ms

#### 5. `error_scenarios()`
List of error conditions for testing:
- Timeout errors (asyncio.TimeoutError)
- Validation errors (ValueError)
- Routing errors (generic Exception)

#### 6. `routing_strategies()`
All available routing strategies:
- COST_OPTIMIZED
- PERFORMANCE_OPTIMIZED
- SPEED_OPTIMIZED
- BALANCED
- PARETO

**Special Feature**: Handles missing bifrost_extensions
```python
try:
    from bifrost_extensions import RoutingStrategy
    return [RoutingStrategy.COST_OPTIMIZED, ...]
except ImportError:
    return ["cost_optimized", "performance_optimized", ...]
```

### `/tests/fixtures/database.py`
**Purpose**: Database adapters and utility functions
**Lines**: 45
**Fixtures Provided**: 1
**Utilities Provided**: 3

#### Fixture: `adapter()`
```python
@pytest.fixture
def adapter():
    """Create adapter with mocked driver for testing."""
    try:
        from neo4j_adapter import Neo4jStorageAdapter, Neo4jConfig
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="test"
        )
        adapter = Neo4jStorageAdapter(config)
        return adapter
    except ImportError:
        return None
```

**Usage**: Neo4j storage tests
**Dependencies**: neo4j_adapter (optional)
**Scope**: Function
**Behavior**: Returns None if neo4j_adapter unavailable

#### Utility 1: `utcnow()`
```python
def utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)
```

**Usage**: Testing with UTC timestamps
**Dependencies**: datetime.timezone

#### Utility 2: `_MockCounters`
```python
class _MockCounters:
    """Simple counters mock that provides empty __dict__."""
    pass
```

**Purpose**: Workaround for Python 3.13 MagicMock issues
**Context**: MagicMock has issues with `__dict__` manipulation in Python 3.13

#### Utility 3: `create_result_summary()`
```python
def create_result_summary(query_type: str = "r") -> MagicMock:
    """Create mock result summary with properly configured counters."""
    mock_counters = _MockCounters()
    return MagicMock(counters=mock_counters, query_type=query_type)
```

**Usage**: Creating mock Neo4j result objects
**Parameters**: query_type (default "r" for read)
**Returns**: MagicMock with counters attribute

## Root Conftest Configuration

### `/tests/conftest.py` Enhancements

#### 1. Fixture Module Auto-Loading
```python
pytest_plugins = ["pytest_asyncio"]
pytest_plugins += ["tests.fixtures"]
```

**Effect**:
- Automatically discovers and loads all fixtures from `/tests/fixtures/` submodule
- No need to manually import fixtures in individual conftest.py files
- Fixtures available to all tests in the project

#### 2. Enhanced pytest_configure()
```python
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as asyncio")
    config.addinivalue_line("markers", "smoke: mark test as smoke test (fast)")
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
```

**New Markers Available**:
- `@pytest.mark.smoke` - Fast sanity checks (<1 second)
- `@pytest.mark.slow` - Long-running tests (>10 seconds)
- `@pytest.mark.integration` - Tests requiring external services
- `@pytest.mark.performance` - Performance/load tests

**Usage**:
```bash
pytest -m smoke              # Only fast tests
pytest -m "not slow"        # Skip slow tests
pytest -m integration       # Only integration tests
```

#### 3. Standard Event Loop
```python
@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
```

**Scope**: Function (per-test isolation)
**Provides**: Fresh event loop for each async test

## Import Path Architecture

### Before Consolidation
```
tests/integration/smartcp/test_xyz.py
├── requires mock_mcp_server
│   └── imports from tests/integration/smartcp/conftest.py
├── requires sample_graphql_query
│   └── imports from tests/integration/smartcp/conftest.py
├── requires auth_config
│   └── imports from tests/integration/smartcp/conftest.py
└── requires mock_bifrost_client
    └── imports from tests/integration/smartcp/conftest.py (via bifrost conftest)
```

### After Consolidation
```
tests/integration/smartcp/test_xyz.py
├── pytest auto-loads /tests/conftest.py
│   └── loads pytest_plugins = ["tests.fixtures"]
│       ├── tests/fixtures/__init__.py
│       │   ├── imports from tests/fixtures/clients.py
│       │   ├── imports from tests/fixtures/models.py
│       │   ├── imports from tests/fixtures/config.py
│       │   └── imports from tests/fixtures/database.py
│       └── All fixtures available to any test
```

**Benefit**: No explicit imports needed; fixtures discovered automatically

## Dependency Management

### Optional Dependencies
Several fixtures gracefully handle optional dependencies:

```python
# Pattern used in multiple fixture modules
try:
    from external_module import SomeClass
    # Normal fixture implementation
    return result
except ImportError:
    # Graceful fallback
    return None  # or fallback value
```

**Advantages**:
1. Fixtures available even if optional dependencies missing
2. Tests requiring specific module will fail gracefully
3. Other tests can continue running
4. No need to maintain separate fixture versions

### Required Dependencies
```python
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
```

These are standard library or pytest-provided; always available.

## Fixture Scope Reference

| Fixture | Scope | Reused | Notes |
|---------|-------|--------|-------|
| event_loop | function | No | New loop per test |
| mock_mcp_server | function | No | Fresh mock each test |
| mock_bifrost_client | function | No | Fresh mock each test |
| mock_router_service | function | No | Fresh mock each test |
| gateway_client | function | No | Fresh client per test |
| adapter | function | No | Fresh adapter per test |
| sample_messages | function | Yes | Immutable data |
| sample_graphql_query | function | Yes | Immutable data |
| auth_config | function | Yes | Immutable config |
| performance_config | function | Yes | Immutable config |

**Pattern**: Mocks are function-scoped (isolated per test); data fixtures can be module/session scoped

## Pytest Collection

### How Pytest Finds Fixtures

1. **Root conftest.py**
   - Defines event_loop, anyio_backend
   - Registers pytest_plugins = ["tests.fixtures"]

2. **tests/fixtures/__init__.py**
   - Imports from clients, models, config, database
   - Makes all fixtures available

3. **Individual fixture modules**
   - Define actual fixtures with @pytest.fixture decorator

4. **Test collection**
   ```
   pytest tests/integration/smartcp/test_something.py
   ↓
   pytest loads tests/conftest.py
   ↓
   pytest discovers pytest_plugins = ["tests.fixtures"]
   ↓
   pytest loads tests/fixtures/__init__.py
   ↓
   pytest discovers all @pytest.fixture decorators
   ↓
   All fixtures available to tests
   ```

### Pytest Fixture Resolution

When a test uses a fixture:
```python
def test_something(mock_mcp_server, auth_config):
    pass
```

Pytest resolves:
1. Looks in test file's conftest.py → Not found
2. Looks in parent conftest.py → /tests/conftest.py
3. Registered pytest_plugins = ["tests.fixtures"]
4. Checks tests/fixtures/__init__.py → Imports from submodules
5. Finds fixtures in /tests/fixtures/clients.py and /tests/fixtures/config.py
6. Uses resolved fixtures

## File Size Compliance

### CLAUDE.md Requirements
**Target**: ≤350 lines per file
**Hard Limit**: ≤500 lines per file

### Current Status
```
/tests/conftest.py                              79 lines ✅
/tests/fixtures/__init__.py                     63 lines ✅
/tests/fixtures/clients.py                     102 lines ✅
/tests/fixtures/models.py                      118 lines ✅
/tests/fixtures/config.py                      113 lines ✅
/tests/fixtures/database.py                     45 lines ✅

/tests/integration/smartcp/conftest.py          31 lines ✅
/tests/integration/bifrost/conftest.py          28 lines ✅
/tests/test_fastmcp_auth/conftest.py            18 lines ✅
/tests/neo4j_storage/conftest.py                38 lines ✅
/tests/e2e/conftest.py                         170 lines ✅
/tests/test_streaming_performance/conftest.py   19 lines ✅
```

**All files well under 350 line target** ✅

## Summary

The consolidation creates a clean, maintainable fixture architecture:
- **Central discovery**: Root conftest.py auto-loads fixture modules
- **Clear organization**: Fixtures grouped by concern (clients/models/config/database)
- **No duplication**: Each fixture defined once
- **Backward compatible**: Existing tests work unchanged
- **Well-sized**: All files under 350 lines
- **Resilient**: Optional dependencies handled gracefully
- **Documented**: Clear docstrings and comments throughout
