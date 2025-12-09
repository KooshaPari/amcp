# Bifrost Client Consolidation Strategy

**Session**: 2025-12-09
**Goal**: Consolidate 4 duplicate Bifrost client implementations into a single canonical version
**Status**: Planning & Execution

## Current State Analysis

### 4 Duplicate Implementations (1,184 total lines)

1. **`/bifrost_client.py` (102 lines)**
   - Location: Project root
   - Purpose: Minimal async GraphQL client
   - Features: Basic query/mutate, context manager, health check
   - Issues: No resilience, no retry logic, basic error handling

2. **`/services/bifrost/client.py` (458 lines)**
   - Location: Service layer
   - Purpose: Comprehensive GraphQL subscription client
   - Features: Full WebSocket support, subscription lifecycle, reconnection logic
   - Issues: Subscription-only, not general-purpose routing

3. **`/bifrost_extensions/http_client.py` (297 lines)**
   - Location: Extensions package
   - Purpose: HTTP API client with retry + resilience
   - Features: Tenacity retry, OpenTelemetry tracing, structured errors, routing APIs
   - Issues: HTTP-only, no GraphQL support, focuses on specific endpoints

4. **`/bifrost_extensions/resilient_client/client.py` (321 lines)**
   - Location: Extensions package (nested)
   - Purpose: Production-hardened client with full resilience
   - Features: Circuit breaker, rate limiting, retry, metrics, validation
   - Issues: Most complex, incomplete integration, duplicates http_client functionality

## Consolidation Strategy

### Phase 1: Design Canonical Client

**Canonical Location**: `/infrastructure/bifrost_client.py` (or `/services/bifrost_client.py`)

**Unified Features**:
```
Core:
- Async GraphQL queries & mutations (from bifrost_client.py)
- HTTP API support (from http_client.py)
- WebSocket subscriptions (from services/bifrost/client.py)
- Health checks

Resilience:
- Exponential backoff retry with jitter (from resilient_client.py)
- Circuit breaker pattern (from resilient_client.py)
- Token bucket rate limiting (from resilient_client.py)
- Timeout handling

Observability:
- OpenTelemetry tracing (from http_client.py)
- Structured logging (from resilient_client.py)
- Request ID tracking (from resilient_client.py)
- Metrics collection (optional)

Quality:
- Input/output validation (from resilient_client.py)
- API key validation (from resilient_client.py)
- Error categorization (from http_client.py)
- Context manager support
```

### Phase 2: Extract Unique Features

**From bifrost_client.py** (Keep):
- Simple async initialization pattern
- Basic query/mutate pattern
- Health check implementation
- Context manager (`__aenter__`, `__aexit__`)

**From http_client.py** (Keep):
- HTTP-specific retry logic with tenacity
- Route/route-tool/classify methods
- OpenTelemetry span decoration
- Structured error mapping (401→AuthenticationError, 429→RateLimitError)

**From services/bifrost/client.py** (Keep):
- WebSocket connection management
- Subscription lifecycle (subscribe, unsubscribe)
- Connection state tracking
- Reconnection with resubscription

**From resilient_client.py** (Keep):
- Circuit breaker logic
- Rate limiting with token bucket
- Comprehensive logging/metrics
- API key validation

### Phase 3: Consolidate into Canonical

**New file**: `infrastructure/bifrost/client.py`

```python
class BifrostClient:
    """Unified Bifrost client supporting GraphQL, HTTP APIs, and WebSocket subscriptions.

    Features:
    - GraphQL queries/mutations (async)
    - HTTP API routing/classification/tool routing
    - WebSocket subscriptions (real-time)
    - Retry with exponential backoff
    - Circuit breaker pattern
    - Rate limiting (token bucket)
    - OpenTelemetry tracing
    - Full error handling
    """

    def __init__(self, config: BifrostClientConfig):
        # Initialize all components
        pass

    # GraphQL operations
    async def query(self, query: str, variables: dict = None) -> dict:
        ...

    async def mutate(self, mutation: str, variables: dict = None) -> dict:
        ...

    # HTTP API operations
    async def route(...) -> RoutingResponse:
        ...

    async def route_tool(...) -> ToolRoutingDecision:
        ...

    async def classify(...) -> ClassificationResult:
        ...

    # WebSocket subscriptions
    async def subscribe(...) -> str:
        ...

    async def unsubscribe(sub_id: str) -> bool:
        ...

    # Lifecycle
    async def connect() -> bool:
        ...

    async def disconnect() -> None:
        ...

    async def health() -> bool:
        ...

    # Context manager support
    async def __aenter__():
        ...

    async def __aexit__(...):
        ...
```

### Phase 4: Update Public API

**Location**: `bifrost_extensions/__init__.py`

```python
# Keep backward compatibility for 3 implementations
from infrastructure.bifrost.client import BifrostClient
from infrastructure.bifrost.config import BifrostClientConfig

# Keep aliases for migration period
from infrastructure.bifrost.client import (
    BifrostClient as HTTPClient,
    BifrostClient as BifrostHTTPClient,
    BifrostClient as ProductionGatewayClient,
    BifrostClient as GraphQLSubscriptionClient,
)

__all__ = [
    "BifrostClient",
    "BifrostClientConfig",
    # Aliases
    "HTTPClient",
    "BifrostHTTPClient",
    "ProductionGatewayClient",
]
```

### Phase 5: Update All Callers

**Files to update** (10+ callers):
- `/bifrost_extensions/__init__.py` - Re-export unified client
- `/bifrost_extensions/client/gateway.py` - Use unified client
- `/server.py` - Client initialization
- `/main.py` - Client initialization
- `/infrastructure/state/factory.py` - State initialization
- `bifrost/control_plane/client.py` - Control plane integration
- `bifrost/plugin.py` - Plugin integration
- Tests - Update imports and mocks

### Phase 6: Delete Redundant Implementations

```bash
rm /bifrost_client.py                                    # 102 lines
rm /bifrost_extensions/http_client.py                   # 297 lines
rm /bifrost_extensions/resilient_client/              # 321 lines
rm /services/bifrost/client.py                         # 458 lines (keep if subscriptions-only)
```

**Total lines removed**: ~1,180 lines
**Net lines added**: ~400-500 (consolidated client + config)
**Consolidation ratio**: 70% reduction

## Implementation Plan

1. Create `infrastructure/bifrost/` submodule
2. Implement consolidated `BifrostClient` with all features
3. Create `BifrostClientConfig` for configuration
4. Update `bifrost_extensions/__init__.py` with exports + aliases
5. Update all callers (GatewayClient, server, main, etc.)
6. Run all tests
7. Delete redundant implementations
8. Verify backward compatibility

## Testing Strategy

- Unit tests for each feature (query, mutate, route, subscribe)
- Integration tests with real Bifrost instance
- Resilience tests (retry, circuit breaker, rate limiting)
- Error handling tests
- WebSocket subscription tests
- Context manager tests
- Backward compatibility tests for aliases

## Known Issues & Risks

- **WebSocket subscriptions**: `/services/bifrost/client.py` is subscription-focused; may need separate consideration
- **HTTP-specific retry**: tenacity retry logic is HTTP-centric; need generic retry wrapper
- **Rate limiting**: Simplistic in http_client; need proper token bucket from resilient_client
- **Metrics**: resilient_client has metrics; http_client doesn't; need unified metrics strategy

## Success Criteria

- Single consolidated `BifrostClient` implementation
- All 1,184 lines of duplicate code reduced to ~500 lines
- 10+ callers updated to use new location
- 3-4 old implementations deleted
- All tests pass
- Backward compatibility via aliases maintained
- Clear migration path for consumers

## Timeline

- Phase 1-2 (Design): 30 minutes
- Phase 3 (Implementation): 45 minutes
- Phase 4-5 (Integration): 30 minutes
- Phase 6 (Testing & Cleanup): 15 minutes
- Total: ~2 hours

---

## Notes

- Keep this document updated as consolidation progresses
- Document any blockers or architectural conflicts discovered
- Verify all 10+ callers work with new consolidated client
- Consider if subscriptions should remain separate or be fully integrated
