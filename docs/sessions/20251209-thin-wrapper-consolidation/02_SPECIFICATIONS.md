# Specifications: Consolidation Strategy

## Consolidation Plan

### Phase 1: Delete Orphaned Code (server_control.py)

**Target**: `/infrastructure/server_control.py`
**Lines Removed**: 292
**Risk**: Zero (no callers)

**Acceptance Criteria**:
- [ ] File deleted
- [ ] All tests pass
- [ ] No import errors in codebase

**Verification**:
```bash
grep -r "server_control\|ServerControl\|ServerController\|HealthChecker" \
  /smartcp --include="*.py" | grep -v docs/
# Should return 0 results
```

---

### Phase 2: Flatten infrastructure/bifrost/__init__.py

**Target**: `/infrastructure/bifrost/__init__.py`
**Lines Removed**: 46
**Callers Affected**: 14

**Current State**:
```python
# /infrastructure/bifrost/__init__.py
from .client import BifrostClient
from .errors import BifrostError, ConnectionError, GraphQLError, TimeoutError, ValidationError
from .queries import QueryBuilder, QueryProcessor, RoutingDecision, SearchResult, ToolMetadata
from .mutations import MutationBuilder, MutationFactory, MutationProcessor
from .subscriptions import SubscriptionBuilder, SubscriptionVariables

__all__ = [...]

async def bifrost_client(url: str = None, api_key: str = None, **kwargs):
    client = BifrostClient(url=url, api_key=api_key, **kwargs)
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()
```

**Target State**:
```python
# /infrastructure/bifrost/__init__.py - DELETE FILE
# OR keep only if context manager is frequently used
# Move async context manager to /infrastructure/bifrost/client.py if needed
```

**Callers to Update** (14 total):

**Production Code** (3):
1. `/bifrost/plugin.py`
   - FROM: `from smartcp.infrastructure.bifrost import BifrostClient`
   - TO: `from smartcp.infrastructure.bifrost.client import BifrostClient`

2. `/bifrost/control_plane.py`
   - FROM: `from smartcp.infrastructure.bifrost import BifrostClient`
   - TO: `from smartcp.infrastructure.bifrost.client import BifrostClient`

3. `/main.py`
   - FROM: `from smartcp.infrastructure.bifrost import BifrostClient`
   - TO: `from smartcp.infrastructure.bifrost.client import BifrostClient`

**Test Code** (11):
Multiple test files:
- `/tests/contract/test_bifrost_delegation.py`
- `/tests/test_bifrost_integration.py` (2 imports)
- `/tests/bifrost_client/test_client_init.py`
- `/tests/bifrost_client/conftest.py`
- `/tests/bifrost_client/test_search.py`
- `/tests/bifrost_client/test_error_handling.py`
- `/tests/bifrost_client/test_routing.py`
- `/tests/bifrost_client/test_tool_queries.py`
- `/tests/e2e/conftest.py`

All follow pattern:
- FROM: `from infrastructure.bifrost.<module> import ...`
- TO: Keep as-is (already direct imports) ✓

**Acceptance Criteria**:
- [ ] __init__.py deleted or emptied
- [ ] All 14 callers updated to direct imports
- [ ] All tests pass
- [ ] No import errors

**Verification**:
```bash
# Should show only direct submodule imports
grep -r "from infrastructure.bifrost import" /smartcp --include="*.py"
# Should return 0 results (all should be from infrastructure.bifrost.<submodule>)
```

---

### Phase 3: Flatten services/bifrost/__init__.py

**Target**: `/services/bifrost/__init__.py`
**Lines Removed**: 49
**Callers Affected**: 2

**Current State**:
```python
# /services/bifrost/__init__.py
from .client import (
    GraphQLSubscriptionClient, ConnectionConfig, Subscription,
    SubscriptionMessage, SubscriptionState, ConnectionState,
)
from .subscription_handler import (
    SubscriptionBuilder, SubscriptionHandler, subscription_client,
)
from .message_handlers import (MessageQueue, MCPSubscriptionBridge)

__all__ = [...]
```

**Target State**: DELETE FILE

**Callers to Update** (2 total):

1. `/tests/test_graphql_subscription_client.py`
   ```python
   # FROM:
   from services.bifrost import (
       GraphQLSubscriptionClient, SubscriptionBuilder, SubscriptionHandler,
       subscription_client, ConnectionConfig, Subscription, SubscriptionMessage,
       SubscriptionState, ConnectionState, MessageQueue, MCPSubscriptionBridge
   )

   # TO:
   from services.bifrost.client import (
       GraphQLSubscriptionClient, ConnectionConfig, Subscription,
       SubscriptionMessage, SubscriptionState, ConnectionState,
   )
   from services.bifrost.subscription_handler import (
       SubscriptionBuilder, SubscriptionHandler, subscription_client,
   )
   from services.bifrost.message_handlers import (
       MessageQueue, MCPSubscriptionBridge,
   )
   ```

2. `/tests/e2e/conftest.py`
   ```python
   # FROM:
   from services.bifrost import GraphQLSubscriptionClient, ConnectionConfig

   # TO:
   from services.bifrost.client import GraphQLSubscriptionClient, ConnectionConfig
   ```

**Acceptance Criteria**:
- [ ] __init__.py deleted
- [ ] Both callers updated to direct imports
- [ ] All tests pass
- [ ] No import errors

**Verification**:
```bash
# Should show 0 results
grep -r "from services.bifrost import" /smartcp --include="*.py"
grep -r "from services\.bifrost import" /smartcp --include="*.py"
```

---

### Phase 4: Consolidate bifrost_extensions/client/gateway.py

**Target**: `/bifrost_extensions/client/gateway.py`
**Lines Removed**: ~50 (reduction, not full deletion)
**Callers Affected**: 2

**Current State**: 272 lines
- GatewayClient class with 6 async methods
- Most methods just delegate to module functions
- Initialization handles HTTP client vs internal router config

**Analysis of Value**:
```python
class GatewayClient:
    def __init__(...):  # 30 lines - MEANINGFUL
        # Config storage + client initialization

    async def route(...):  # 40 lines - 32 docstring/types, 8 logic
        # Delegates to route()

    async def route_tool(...):  # 40 lines - 35 docstring/types, 5 logic
        # Delegates to route_tool()

    async def classify(...):  # 30 lines - 25 docstring/types, 5 logic
        # Delegates to classify()

    async def get_usage(...):  # 20 lines - 15 docstring/types, 5 logic
        # Delegates or uses http_client

    async def health_check():  # 15 lines
        # Returns static dict
```

**Recommendation**: Keep the class (preserves public API), but reduce boilerplate

**Option A: Factory Function** (Preferred)
```python
# /bifrost_extensions/__init__.py or new /bifrost_extensions/factory.py
def create_gateway_client(
    api_key: Optional[str] = None,
    base_url: str = "http://localhost:8000",
    timeout: float = 30.0,
    max_retries: int = 3,
    use_http: bool = False,
) -> "GatewayClient":
    """Create configured GatewayClient instance."""
    return GatewayClient(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        use_http=use_http,
    )
```

**Option B: Keep as-is** (for now)
- The class provides semantic clarity
- Docstrings are valuable for users
- Can be optimized further in future refactoring

**Recommendation**: Keep as-is for now. The value lies in the consolidated interface.

**Acceptance Criteria**:
- [ ] Callers verified (only 2)
- [ ] Public API preserved
- [ ] No changes needed (keep current structure)

---

## Summary of Changes

| Phase | Module | Action | Lines | Callers |
|-------|--------|--------|-------|---------|
| 1 | server_control.py | DELETE | -292 | 0 |
| 2 | infrastructure/bifrost/__init__.py | DELETE/FLATTEN | -46 | 14 |
| 3 | services/bifrost/__init__.py | DELETE | -49 | 2 |
| 4 | gateway.py | KEEP (review later) | 0 | 2 |
| **TOTAL** | | | **-387** | **18** |

---

## Risk Assessment

### server_control.py (Delete)
- **Risk Level**: ZERO
- **Callers**: 0
- **Behavioral Impact**: None
- **Rollback**: Restore from git

### infrastructure/bifrost/__init__.py (Delete)
- **Risk Level**: LOW
- **Callers**: 14
- **Behavioral Impact**: Import paths change only
- **Mitigation**: Run full test suite, verify no import errors

### services/bifrost/__init__.py (Delete)
- **Risk Level**: LOW
- **Callers**: 2 (both in tests)
- **Behavioral Impact**: Import paths change only
- **Mitigation**: Run test suite for those specific tests

### gateway.py (Keep for now)
- **Risk Level**: ZERO
- **Callers**: 2
- **Behavioral Impact**: None
- **Future Work**: Can be simplified further (see 05_KNOWN_ISSUES.md)

---

## Testing Strategy

### Unit Tests
```bash
# Run all tests to catch import errors
python cli.py test run

# Specific test files for Phase 2/3
python -m pytest tests/test_bifrost_integration.py -v
python -m pytest tests/test_graphql_subscription_client.py -v
python -m pytest tests/e2e/conftest.py -v
```

### Integration Tests
```bash
# Verify bifrost integration still works
python -m pytest tests/bifrost_client/ -v
python -m pytest tests/e2e/ -v
```

### Import Validation
```bash
# Test that all modules can be imported
python -c "from smartcp.infrastructure.bifrost.client import BifrostClient; print('OK')"
python -c "from smartcp.services.bifrost.client import GraphQLSubscriptionClient; print('OK')"
```

---

## Rollback Plan

If any phase fails:
1. Revert changes with git
2. Identify root cause
3. Fix and retry

No phase requires synchronization with other phases (independent changes).

---

## Success Criteria

- [ ] All 387 lines removed successfully
- [ ] All 18 callers updated without errors
- [ ] Full test suite passes
- [ ] No import errors in codebase
- [ ] Code coverage maintained or improved
