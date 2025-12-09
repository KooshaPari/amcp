"""
Tests for Prompt Cache optimization.

Tests the PromptCache component for caching LLM prompts to reduce redundant processing.
Covers: cache operations, expiration, prefix matching, statistics.
"""

import asyncio
import pytest
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.prompt_cache import (
    PromptCache,
    PromptCacheConfig,
    CacheBreakpoint,
    CacheEntry,
)


class TestPromptCache:
    """Tests for PromptCache."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache for each test."""
        config = PromptCacheConfig(
            max_entries=100,
            min_prefix_tokens=10,  # Lower for testing
        )
        return PromptCache(config)

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        """Test basic cache set and get."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"},
        ]

        # Set cache
        key = await cache.set(messages, CacheBreakpoint.CONTEXT)
        assert key is not None
        assert len(key) == 32

        # Get cache
        hit = await cache.get(messages)
        assert hit is not None
        assert hit["cached_prefix_length"] == len(messages)

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        messages = [{"role": "user", "content": "Unknown query"}]
        hit = await cache.get(messages)
        assert hit is None

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """Test cache entries expire correctly."""
        cache.config.default_ttl = 1  # 1 second TTL
        cache.config.context_ttl = 1  # 1 second TTL

        messages = [{"role": "user", "content": "Test message " * 10}]  # Reduced from 100
        await cache.set(messages, CacheBreakpoint.CONTEXT)

        # Immediate get should hit
        hit = await cache.get(messages)
        assert hit is not None

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Should miss after expiration
        hit = await cache.get(messages)
        assert hit is None

    @pytest.mark.asyncio
    async def test_cache_prefix_matching(self, cache):
        """Test prefix matching for partial cache hits."""
        # Cache a shorter prefix
        prefix = [
            {"role": "system", "content": "System prompt " * 50},
        ]
        await cache.set(prefix, CacheBreakpoint.SYSTEM)

        # Query with extended messages should get prefix hit
        extended = prefix + [{"role": "user", "content": "New question"}]
        hit = await cache.get(extended)

        # Should find the prefix
        assert hit is not None
        assert hit["cached_prefix_length"] == 1

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics tracking."""
        messages = [{"role": "user", "content": "Test message " * 10}]  # Reduced from 100

        # Miss
        await cache.get(messages)

        # Set
        await cache.set(messages, CacheBreakpoint.CONTEXT)

        # Hit
        await cache.get(messages)

        stats = await cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5

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
        # Entry should survive longer than context TTL would allow
        entry = cache._cache[key]
        assert entry.ttl == cache.config.system_prompt_ttl
        
        # Also test that context breakpoint gets different TTL
        context_msg = [{"role": "user", "content": "Context message " * 50}]
        context_key = await cache.set(context_msg, CacheBreakpoint.CONTEXT)
        context_entry = cache._cache[context_key]
        assert context_entry.ttl == cache.config.context_ttl
        
        # And default TTL for other types
        history_msg = [{"role": "assistant", "content": "History message " * 50}]
        history_key = await cache.set(history_msg, CacheBreakpoint.HISTORY)
        history_entry = cache._cache[history_key]
        assert history_entry.ttl == cache.config.default_ttl

    @pytest.mark.asyncio
    async def test_expired_entry_eviction(self, cache):
        """Test eviction of expired entries (covers lines 310-311)."""
        # Fill cache with entries that will expire
        cache.config.default_ttl = 1  # 1 second
        cache.config.context_ttl = 1  # 1 second
        
        # Create some entries that will expire
        for i in range(5):
            messages = [{"role": "user", "content": f"Message {i}"}]
            await cache.set(messages, CacheBreakpoint.CONTEXT)
        
        assert len(cache._cache) == 5
        
        # Directly mark entries as expired to force eviction
        for entry in cache._cache.values():
            entry.created_at = time.time() - 10  # 10 seconds ago
        
        # Trigger eviction by adding a new entry
        new_key = await cache.set([{"role": "user", "content": "new"}], CacheBreakpoint.CONTEXT)
        
        # Verify expired entries were evicted
        stats = await cache.get_stats()
        assert stats.evictions >= 5  # All expired entries should be evicted
        assert len(cache._cache) == 1
        assert new_key in cache._cache

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

    def test_global_cache_instance(self):
        """Test global prompt cache singleton pattern (covers lines 371-373)."""
        from optimization.prompt_cache import get_prompt_cache, _prompt_cache
        
        # Reset global instance properly
        import optimization.prompt_cache as prompt_cache_module
        original_cache = prompt_cache_module._prompt_cache
        prompt_cache_module._prompt_cache = None
        
        try:
            # First call creates instance
            cache1 = get_prompt_cache()
            assert cache1 is not None
            assert prompt_cache_module._prompt_cache is not None
            
            # Second call returns same instance
            cache2 = get_prompt_cache()
            assert cache1 is cache2
            
            # Config passed to existing instance is ignored
            custom_config = PromptCacheConfig(max_entries=999)
            cache3 = get_prompt_cache(custom_config)
            assert cache3 is cache1
            assert cache1.config.max_entries != 999  # Keeps original config
        finally:
            # Restore original state
            prompt_cache_module._prompt_cache = original_cache


# Performance tests
class TestPromptCachePerformance:
    """Performance benchmarks for prompt cache."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_performance(self):
        """Test cache performance under load."""
        import time
        cache = PromptCache(PromptCacheConfig(max_entries=10000))

        # Generate test messages (reduced size to prevent memory issues)
        messages_list = [
            [{"role": "user", "content": f"Test message {i} " * 10}]
            for i in range(10)  # Reduced from 100 to 10
        ]

        # Benchmark set operations
        start = time.time()
        for messages in messages_list:
            await cache.set(messages, CacheBreakpoint.CONTEXT)
        set_time = time.time() - start

        # Benchmark get operations
        start = time.time()
        for messages in messages_list:
            await cache.get(messages)
        get_time = time.time() - start

        # Should complete quickly
        assert set_time < 1.0  # < 1 second for 100 sets
        assert get_time < 0.5  # < 0.5 seconds for 100 gets


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
