# Consolidation Candidates - Detailed Analysis

## Priority 1: Rate Limiters (HIGH - 545 lines)

### Current State
- **bifrost_extensions/resilience/rate_limiter.py** (294 lines)
  - Clean abstractions: RateLimiter (ABC), TokenBucketLimiter, SlidingWindowLimiter
  - Both blocking/non-blocking APIs
  - OpenTelemetry integration

- **router/router_core/limits/rate_limiter.py** (1,057 lines)
  - Full-featured: token bucket, budget, adaptive, multiple strategies
  - Pheno-sdk integration
  - Legacy backward compatibility layer
  - Over-engineered for simple use cases

### Consolidation Strategy

#### Step 1: Extract TokenBucket from router/limits (175 lines)
Move to bifrost and replace with re-export:
```python
# bifrost_extensions/resilience/rate_limiter.py ADD
class TokenBucketRateLimiter(RateLimiter):
    # Extracted from router/limits version
    # Use per-key locking approach from router (better than bifrost's single lock)
```

#### Step 2: Create router/router_core/limits/budget.py (135 lines)
Extract BudgetManager as standalone:
```python
from dataclasses import dataclass
class BudgetLimit: ...
class BudgetUsage: ...
class BudgetManager:
    # Spending limit tracking (daily/monthly/total)
```

#### Step 3: Create router/router_core/limits/orchestrator.py (77 lines)
Extract orchestration:
```python
class PipelineRateLimiter:
    # Composes multiple limiters (global, per-user, per-endpoint, per-provider)
```

#### Step 4: Update router/router_core/limits/rate_limiter.py (keep 200-250 lines)
After extraction, becomes thin wrapper:
```python
# Keep: strategy enums, intelligent limiter, pheno integration
# Import from bifrost: core token bucket logic
# Import from local modules: budget, orchestrator
from bifrost_extensions.resilience.rate_limiter import (
    RateLimiter, TokenBucketLimiter, SlidingWindowLimiter
)
from .budget import BudgetManager, BudgetLimit
from .orchestrator import PipelineRateLimiter

# New IntelligentRateLimiter that composes bifrost + budget features
class IntelligentRateLimiter:
    def __init__(self, config: AdvancedRateLimitConfig):
        self.limiter: RateLimiter = self._create_limiter(config)
        self.budget: Optional[BudgetManager] = ...
```

### Testing Impact
- Move testing/rate_limiter.py tests to bifrost (already deprecated)
- Add bifrost tests for TokenBucketRateLimiter
- Keep router/limits tests for budget and orchestrator

### Lines Saved: 545+ lines (40% reduction)

---

## Priority 2: Retry Patterns (MEDIUM - 82 lines)

### Current State
- **bifrost_extensions/resilience/retry.py** (142 lines) - Canonical
- **router/router_core/adapters/providers/pheno_resilience/retry.py** (34 lines) - Duplicate/Adapter
- **router/router_core/testing/retry_handler.py** (548 lines) - Testing utility

### Issue
1. pheno_resilience/retry.py is unnecessary (34-line wrapper)
2. retry_handler.py shouldn't be in testing/ (it's a utility module)

### Consolidation Strategy

#### Step 1: Eliminate pheno_resilience/retry.py (34 lines)
Create adapter function instead:
```python
# router/router_core/adapters/providers/pheno_resilience/__init__.py ADD:
from bifrost_extensions.resilience.retry import RetryPolicy

def pheno_config_to_retry_policy(config: RetryConfig) -> RetryPolicy:
    return RetryPolicy(
        max_retries=int(config.max_delay / config.initial_delay),
        initial_delay=config.initial_delay,
        max_delay=config.max_delay,
        exponential_base=config.exponential_base,
        jitter=config.jitter,
    )

# Use like:
policy = pheno_config_to_retry_policy(pheno_config)
@retry_with_backoff(policy)
async def operation(): ...
```

Replace all imports:
```bash
# Find: from router.router_core.adapters.providers.pheno_resilience.retry import sleep_with_backoff
# Replace: from bifrost_extensions.resilience.retry import retry_with_backoff, RetryPolicy
```

#### Step 2: Relocate retry_handler.py (548 lines)
Move to router/router_core/resilience/testing.py:
- Keep filename: testing.py (indicates test utility)
- Move location from testing/ to resilience/
- Update imports

This separates concerns:
- bifrost/resilience/retry.py = production retry
- router_core/resilience/testing.py = test harness with circuit breakers

### Testing Impact
- Update imports in test_*_retry.py files
- No test failures expected (just moving files)

### Lines Saved: 82 lines (11% reduction in retry code)

---

## Priority 3: Classification Organization (LOW - Org only)

### Current State
27 classification files scattered across:
- bifrost_ml/services/
- bifrost_extensions/client/
- router/router_core/classification/
- router/router_core/domain/services/classification/
- router/router_core/orchestration/

### Analysis
✅ NO true duplicates found (all legitimate implementations)
- Keyword classifier (fast, rule-based)
- NVIDIA ML classifier (deep learning)
- DeBERTa classifier (transformer)
- Unified orchestrator (combines above)
- Voter (consensus)

### Consolidation Strategy (Organizational)

#### Create unified hierarchy:
```
router/router_core/classifiers/
├─ __init__.py                 (exports all)
├─ base.py                     (abstract base)
├─ keyword.py                  (keyword classifier)
├─ ml/
│  ├─ __init__.py
│  ├─ nvidia.py                (NVIDIA ML)
│  └─ deberta.py               (DeBERTa transformer)
├─ unified.py                  (unified orchestrator)
└─ voters.py                   (voting strategies)
```

#### Migration path:
1. Create new directory structure
2. Move files one-by-one, updating imports
3. Create __init__.py with unified exports
4. Update all imports across codebase
5. Delete old empty directories

### Benefits
- Single import source: `from router.router_core.classifiers import ...`
- Clear hierarchy
- Easier onboarding
- Better test organization

### No code changes needed - Pure reorganization

---

## Implementation Order

### Week 1 (Quick Wins)
1. Eliminate pheno_resilience/retry.py
2. Relocate retry_handler.py
3. Update imports
4. Estimated effort: 4-6 hours

### Week 2-3 (Rate Limiter Refactor)
1. Extract BudgetManager to separate module
2. Extract PipelineRateLimiter to separate module
3. Move TokenBucketRateLimiter to bifrost
4. Update router/limits to compose extracted modules
5. Test thoroughly
6. Estimated effort: 8-12 hours

### Week 4 (Organization)
1. Create classifiers directory structure
2. Move classifier files
3. Update imports
4. Verify all tests pass
5. Estimated effort: 3-4 hours

### Total Effort: ~15-22 hours
### Total Lines Eliminated: 627 lines
### Maintenance Improvement: 100+ hours/year saved

