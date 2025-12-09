# Work Package 07 Enhanced: Prompt Cache Edge Cases & Executor Fix

**Priority**: HIGH  
**Estimated Time**: 45-75 minutes  
**Current Coverage**: 86% → Target: 97%+

## Part 1: Prompt Cache Edge Cases

### Missing Lines Analysis

Based on current coverage report, these lines are not covered:
- **Line 177**: System prompt TTL handling in `_get_ttl()`
- **Lines 310-311**: Expired entry eviction in `_evict_if_needed()`
- **Lines 315-318**: LRU eviction loop for cache size limit
- **Lines 336-339**: Cache statistics updates in clear()
- **Line 351**: Cache warming disabled path
- **Lines 352-361**: System prompt warming loop
- **Lines 371-373**: Global cache instance management

### Test Implementation Plan

#### Test 1: System Prompt TTL Coverage (Line 177)
```python
@pytest.mark.asyncio
async def test_system_prompt_ttl(self, cache):
    """Test system prompts get longer TTL (covers line 177)."""
    # Create cache with distinct TTL values
    cache.config.default_ttl = 60
    cache.config.context_ttl = 120
    cache.config.system_prompt_ttl = 3600  # 1 hour
    
    # Cache system prompt and verify TTL
    system_msg = [{"role": "system", "content": "System prompt " * 50}]
    key = await cache.set(system_msg, CacheBreakpoint.SYSTEM)
    
    # Verify the entry has system TTL through indirect testing
    # Check that it survives longer than context TTL would allow
    entry = cache._cache[key]
    assert entry.ttl == cache.config.system_prompt_ttl
```

#### Test 2: Expired Entry Eviction (Lines 310-311)
```python
@pytest.mark.asyncio
async def test_expired_entry_eviction(self, cache):
    """Test eviction of expired entries (covers lines 310-311)."""
    # Fill cache with entries that will expire
    cache.config.default_ttl = 1  # 1 second
    
    for i in range(10):
        messages = [{"role": "user", "content": f"Message {i}"}]
        await cache.set(messages, CacheBreakpoint.CONTEXT)
    
    assert len(cache._cache) == 10
    
    # Wait for expiration and trigger eviction
    await asyncio.sleep(1.5)
    
    # Trigger eviction by adding a new entry
    await cache.set([{"role": "user", "content": "new"}], CacheBreakpoint.CONTEXT)
    
    # Verify expired entries were evicted before LRU
    assert len(cache._cache) == 1
    stats = await cache.get_stats()
    assert stats.evictions >= 10  # All expired entries evicted
```

#### Test 3: LRU Eviction for Size Limit (Lines 315-318)
```python
@pytest.mark.asyncio
async def test_lru_eviction_size_limit(self, cache):
    """Test LRU eviction when cache hits size limit (covers lines 315-318)."""
    # Set small cache size to trigger LRU eviction
    cache.config.max_entries = 3
    cache.config.default_ttl = 3600  # Long TTL to avoid expiration
    
    # Fill cache beyond limit
    messages_list = [
        [{"role": "user", "content": f"Message {i}"}]
        for i in range(5)
    ]
    
    keys = []
    for messages in messages_list:
        key = await cache.set(messages, CacheBreakpoint.CONTEXT)
        keys.append(key)
    
    # Should only keep 3 most recent entries
    assert len(cache._cache) == 3
    
    # Verify oldest entries were evicted
    stats = await cache.get_stats()
    assert stats.evictions >= 2
    
    # Verify last 3 entries are kept
    assert keys[-1] in cache._cache
    assert keys[-2] in cache._cache
    assert keys[-3] in cache._cache
```

#### Test 4: Cache Statistics in Clear (Lines 336-339)
```python
@pytest.mark.asyncio
async def test_cache_clear_statistics(self, cache):
    """Test cache stats reset after clear (covers lines 336-339)."""
    # Add some entries and update stats
    messages = [{"role": "user", "content": "Test"}]
    await cache.set(messages, CacheBreakpoint.CONTEXT)
    await cache.get(messages)
    
    stats_pre_clear = await cache.get_stats()
    assert stats_pre_clear.total_entries > 0
    assert stats_pre_clear.hits > 0
    
    # Clear cache
    await cache.clear()
    
    # Verify stats are reset
    stats_post_clear = await cache.get_stats()
    assert stats_post_clear.total_entries == 0
    assert stats_post_clear.hits == 0
    assert stats_post_clear.misses == 0
    assert stats_post_clear.evictions == 0
```

#### Test 5: Cache Warming Disabled (Line 351)
```python
@pytest.mark.asyncio
async def test_cache_warming_disabled(self, cache):
    """Test behavior when cache warming is disabled (covers line 351)."""
    # Disable cache warming
    cache.config.enable_cache_warming = False
    
    prompts = ["System prompt 1", "System prompt 2", "System prompt 3"]
    cached_count = await cache.warm_system_prompts(prompts)
    
    # Should return 0 and not cache anything
    assert cached_count == 0
    assert len(cache._cache) == 0
```

#### Test 6: System Prompt Warming (Lines 352-361)
```python
@pytest.mark.asyncio
async def test_system_prompt_warming(self, cache):
    """Test system prompt warming functionality (covers lines 352-361)."""
    # Enable cache warming with system prompts
    cache.config.enable_cache_warming = True
    
    prompts = [
        "You are a helpful assistant.",
        "You are a code expert.",
        "You are a data analyst."
    ]
    
    cached_count = await cache.warm_system_prompts(prompts)
    
    # Should cache all prompts
    assert cached_count == 3
    assert len(cache._cache) == 3
    
    # Verify all entries have system breakpoint TTL
    for entry in cache._cache.values():
        assert entry.breakpoint == CacheBreakpoint.SYSTEM
        assert entry.ttl == cache.config.system_prompt_ttl
```

#### Test 7: Global Cache Instance (Lines 371-373)
```python
def test_global_cache_instance(self):
    """Test global prompt cache singleton pattern (covers lines 371-373)."""
    from optimization.prompt_cache import get_prompt_cache, _prompt_cache
    
    # Reset global instance
    _prompt_cache = None
    
    # First call creates instance
    cache1 = get_prompt_cache()
    assert cache1 is not None
    assert _prompt_cache is not None
    
    # Second call returns same instance
    cache2 = get_prompt_cache()
    assert cache1 is cache2
    
    # Config passed to existing instance is ignored
    custom_config = PromptCacheConfig(max_entries=999)
    cache3 = get_prompt_cache(custom_config)
    assert cache3 is cache1
    assert cache1.config.max_entries != 999  # Keeps original config
```

### Part 2: Parallel Executor Unreachable Code Fix

#### Problem Analysis
- Line 101 in `optimization/parallel_executor/executor.py` contains unreachable code
- It's a `return result` statement after a for loop that always returns inside the loop
- Current loop: `for attempt in range(self.config.max_retries + 1)`
- All paths (success, timeout, exception) return from within the loop
- Line 101 can never be reached

#### Proposed Fix

**Option A: Remove Unreachable Code (Recommended)**
```python
# Before
for attempt in range(self.config.max_retries + 1):
    # ... try/except blocks with returns
    return result if exception or timeout

return result  # Line 101 - UNREACHABLE

# After
for attempt in range(self.config.max_retries + 1):
    # ... try/except blocks with returns
    return result if exception or timeout

# Remove unreachable return statement
```

**Option B: Refactor to Make Path Reachable**
```python
result = None
for attempt in range(self.config.max_retries + 1):
    # ... only return on success
    if success:
        return success_result
    # Continue on failure/timeout for potential fallback

return result or last_known_result  # Line 101 - Now reachable
```

#### Implementation Plan for Option A

1. Remove the unreachable `return result` statement (line 101)
2. Update any tests that depend on this structure (shouldn't be any since it's unreachable)
3. Verify coverage remains at 99% (with only intentionally unreachable code removed)
4. Add comment explaining why this structure was simplified

### Part 3: Verification & Documentation

#### Coverage Verification Commands
```bash
# Verify prompt cache coverage
uv run pytest tests/optimization/test_prompt_cache.py \
  --cov=optimization.prompt_cache \
  --cov-report=term-missing -v

# Verify executor coverage after fix
uv run pytest tests/optimization/test_parallel_executor_detailed.py \
  --cov=optimization.parallel_executor.executor \
  --cov-report=term-missing -v
```

#### Success Criteria
- ✅ Prompt cache coverage reaches 97%+
- ✅ All missing lines (177, 310-311, 315-318, 336-339, 351-361, 371-373) are covered
- ✅ Unreachable line 101 in executor is removed
- ✅ All existing tests continue to pass
- ✅ New tests follow existing patterns and style

#### Documentation Updates
- Update work package with actual implementation details
- Note unreachable code removal in documentation
- Add coverage badges to track progress
- Document any edge case discoveries during testing

## Priority & Timeline

1. **First 45 minutes**: Implement prompt cache tests (7 new test methods)
2. **Next 15 minutes**: Fix unreachable line 101 in executor
3. **Final 15 minutes**: Run full test suite, verify coverage, update documentation

## Risk Mitigation

- Test one missing line at a time to isolate issues
- Keep existing test structure intact to maintain compatibility
- Document any changes to interface or behavior
- Ensure new tests add value beyond just coverage
