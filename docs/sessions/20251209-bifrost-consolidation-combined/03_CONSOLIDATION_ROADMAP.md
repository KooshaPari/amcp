# Priority 2 & 3 Consolidation Roadmap

## Overview

This document outlines the remaining consolidation opportunities identified in the architectural audit. Priority 1 (325 lines) is complete. Priority 2 & 3 offer 1,900+ additional lines of code elimination.

## Priority 2: Bifrost-Extensions (1,100+ lines)

### Task 1: Replace retry.py with tenacity (213 lines)

**File**: `bifrost_extensions/resilience/retry.py`  
**Current Implementation**: Custom exponential backoff with jitter  
**Target Library**: tenacity >= 8.0.0  
**Effort**: 2-3 hours | **Risk**: Low

**Public API to Preserve**:
- `RetryPolicy` dataclass
- `retry_with_backoff()` decorator
- `AsyncRetryPolicy` dataclass
- `async_retry_with_backoff()` async decorator
- All exception types (TimeoutError, RetryExhaustedError)

**Tenacity Mapping**:
```python
# Current custom pattern:
@retry_with_backoff(max_retries=3, initial_delay=1.0, exponential_base=2.0)
async def fetch_data():
    ...

# Maps to tenacity:
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def fetch_data():
    ...
```

**Consolidation Strategy**:
1. Keep RetryPolicy as thin wrapper over tenacity config
2. Use tenacity decorators internally
3. Maintain same function signatures
4. Zero breaking changes to calling code

**Expected Savings**: 213 lines (100% replacement)

---

### Task 2: Replace rate_limiter.py with slowapi (295 lines)

**File**: `bifrost_extensions/resilience/rate_limiter.py`  
**Current Implementation**: Token bucket + sliding window rate limiter  
**Target Library**: slowapi >= 0.1.5  
**Effort**: 3-4 hours | **Risk**: Low-Medium

**Public API to Preserve**:
- `TokenBucketRateLimiter` class
- `SlidingWindowRateLimiter` class
- `IntelligentRateLimiter` class (orchestrator)
- All rate limit exception types

**Slowapi Mapping**:
```python
# Current custom:
limiter = TokenBucketRateLimiter(rate=100, capacity=20)
limiter.acquire()

# Maps to slowapi:
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
@limiter.limit("100/minute")
async def endpoint():
    ...
```

**Consolidation Strategy**:
1. Use slowapi for rate limiting engine
2. Keep IntelligentRateLimiter as high-level orchestrator
3. Wrap slowapi internals to maintain backward compatibility
4. Handle fallback to in-memory if Redis unavailable

**Expected Savings**: 200-250 lines (use slowapi core, keep adapters)

---

### Task 3: Replace circuit_breaker.py with pybreaker (232 lines)

**File**: `bifrost_extensions/resilience/circuit_breaker.py`  
**Current Implementation**: 3-state pattern (CLOSED/OPEN/HALF_OPEN)  
**Target Library**: pybreaker >= 0.7.0  
**Effort**: 2-3 hours | **Risk**: Low

**Public API to Preserve**:
- `CircuitBreaker` class
- `CircuitBreakerState` enum (CLOSED, OPEN, HALF_OPEN)
- All exception types

**Pybreaker Mapping**:
```python
# Current custom:
breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30
)
breaker.call(func, args)

# Maps to pybreaker:
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=30
)
breaker.call(func, args)
```

**Consolidation Strategy**:
1. Replace internal state machine with pybreaker
2. Keep same public class names and method signatures
3. Add thin wrapper layer for compatibility
4. Maintain OpenTelemetry tracing

**Expected Savings**: 200+ lines (replace state machine implementation)

---

### Task 4: Replace fastmcp_auth/cache.py with cachetools (99 lines)

**File**: `bifrost_extensions/fastmcp_auth/cache.py`  
**Current Implementation**: Simple TTL cache for JWT tokens  
**Target Library**: cachetools >= 5.0.0  
**Effort**: 1 hour | **Risk**: Very Low

**Public API to Preserve**:
- `TokenCache` class
- `get()`, `set()`, `clear()` methods
- TTL handling

**Cachetools Mapping**:
```python
# Current custom:
class TokenCache:
    def __init__(self, ttl=3600):
        self.ttl = ttl
        self._cache = {}
    
    def get(self, key):
        if key in self._cache and not self._is_expired(key):
            return self._cache[key]

# Maps to cachetools:
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=3600)
```

**Consolidation Strategy**:
1. Replace custom cache with cachetools.TTLCache
2. Keep TokenCache wrapper for backward compatibility
3. Minimal code changes required

**Expected Savings**: 70+ lines (direct replacement)

---

### Task 5: Simplify http_client.py with httpx & tenacity (318 lines)

**File**: `bifrost_extensions/http_client.py`  
**Current Implementation**: HTTP wrapper with custom retry logic  
**Target Libraries**: httpx (already available) + tenacity  
**Effort**: 2 hours | **Risk**: Low

**Public API to Preserve**:
- `HTTPClient` class
- `get()`, `post()`, `request()` methods
- All exception types
- Timeout handling
- Retry behavior

**Httpx Mapping**:
```python
# Current custom:
client = HTTPClient(timeout=30, retries=3)
response = client.get(url)

# Maps to httpx + tenacity:
import httpx
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def make_request(url):
    with httpx.Client(timeout=30) as client:
        return client.get(url)
```

**Consolidation Strategy**:
1. Use httpx as HTTP client (already available)
2. Use tenacity for retry logic (being added)
3. Keep HTTPClient class wrapper
4. Simplify connection pooling via httpx

**Expected Savings**: 150-180 lines (replace custom HTTP + retry wrapper)

---

## Priority 3: SmartCP (970+ lines)

### Task 6: Remove fallback async_utils duplication (169 lines)

**Files**:
- `fallbacks/async_utils.py` (122 lines)
- `compat/async_utils.py` (47 lines)

**Issue**: Two-path fallback system for Settings/Logger/MetricsCollector  
**Solution**: Delete both, use standard libraries directly  
**Risk**: Very Low (confirmed all libraries in requirements.txt)

**Action**:
1. Delete `/fallbacks/async_utils.py`
2. Delete `/compat/async_utils.py`
3. Update any imports to use:
   - `pydantic_settings.BaseSettings` directly
   - `stdlib logging` directly
   - `prometheus_client` directly (from bifrost consolidation)
4. Verify tests pass

**Expected Savings**: 169 lines (complete elimination)

---

### Task 7: Consolidate Pheno adapters (96 lines)

**Files**:
- `pheno_rate_limiter_adapter.py` (96 lines)
- `pheno_rate_limiter_wrapper.py` (120+ lines)
- Inline wrapping in `router_core/limits/rate_limiter.py`

**Issue**: Pheno SDK wrapped 3 times with inconsistent patterns  
**Solution**: Single unified adapter  
**Risk**: Low (clear separation of concerns)

**Action**:
1. Create unified `/adapters/pheno_sdk_adapter.py`
2. Consolidate all Pheno SDK integration in one place
3. Update imports to use unified adapter
4. Remove redundant wrappers
5. Verify tests pass

**Expected Savings**: 96 lines (consolidate adapters)

---

### Task 8: Remove TokenBucket duplicate (302 lines)

**Files**:
- `router_core/limits/rate_limiter.py` (754 lines)
- `router_core/rl/rate_limiter_utils.py` (302 lines) ← **EXACT DUPLICATE**

**Issue**: TokenBucketRateLimiter implemented twice identically  
**Solution**: Keep one, delete other, update imports  
**Risk**: Very Low (exact duplicate = no logic difference)

**Action**:
1. Keep: `router_core/limits/rate_limiter.py` (more comprehensive)
2. Delete: `router_core/rl/rate_limiter_utils.py`
3. Update all imports from `rate_limiter_utils` → use `limits` version
4. Verify tests pass

**Expected Savings**: 302 lines (complete elimination of duplicate)

---

## Implementation Sequence

### Phase A (Low Risk, Can Run Parallel)
1. Task 6: Remove fallback async_utils (169 lines, 1 hour)
2. Task 8: Remove TokenBucket duplicate (302 lines, 1 hour)
3. Task 4: Replace cache.py with cachetools (99 lines, 1 hour)

**Subtotal Phase A**: 570 lines, 3 hours, Parallel execution safe

### Phase B (Medium Complexity, Sequential Recommended)
4. Task 1: Replace retry.py with tenacity (213 lines, 2-3 hours)
   - Prerequisite: None
   - Enables: Task 5 (http_client simplification)

5. Task 5: Simplify http_client.py (318 lines, 2 hours)
   - Prerequisite: tenacity added (Task 1)
   - Depends on: Task 1

6. Task 3: Replace circuit_breaker.py with pybreaker (232 lines, 2-3 hours)
   - Prerequisite: None
   - Independent: Can run parallel to Tasks 4-5

7. Task 2: Replace rate_limiter.py with slowapi (295 lines, 3-4 hours)
   - Prerequisite: None
   - Independent: Can run parallel

**Subtotal Phase B**: 1,058 lines, 9-12 hours, Some parallelization possible

### Phase C (SmartCP Integration)
9. Task 7: Consolidate Pheno adapters (96 lines, 2 hours)
   - Prerequisite: Understanding of Pheno SDK usage
   - Integration point: Rate limiter consolidations

**Subtotal Phase C**: 96 lines, 2 hours

---

## Total Consolidation Impact

| Phase | Lines | Hours | Risk |
|-------|-------|-------|------|
| Priority 1 (Complete) | 325 | 4 | Very Low ✅ |
| Priority 2 Phase A | 570 | 3 | Very Low ✅ |
| Priority 2 Phase B | 1,058 | 9-12 | Low ✅ |
| Priority 3 Phase C | 96 | 2 | Very Low ✅ |
| **TOTAL** | **2,049** | **18-21** | **Low** |

---

## Dependencies to Add

```toml
# To requirements.txt (add before Priority 2 Phase B)
tenacity = ">=8.0.0"       # Retry logic
slowapi = ">=0.1.5"        # Rate limiting  
pybreaker = ">=0.7.0"      # Circuit breaker
cachetools = ">=5.0.0"     # Caching
```

All use proven, maintained libraries following Priority 1 consolidation pattern.

---

## Success Criteria

- ✅ All tests pass after each consolidation
- ✅ No breaking changes to public APIs
- ✅ All imports continue to work
- ✅ Code compiles without errors
- ✅ 2,049 lines eliminated across 8 tasks
- ✅ Documentation updated

---

## Timeline Recommendation

**Optimal Sequence**:
1. Add new dependencies to requirements.txt
2. Execute Phase A (3 hours, parallelizable)
3. Execute Phase B (9-12 hours, mostly sequential with some parallelization)
4. Execute Phase C (2 hours, integrates with Phase B results)
5. Full test suite + documentation (1-2 hours)

**Estimated Total**: 15-20 hours of focused development
