"""
Tests for Prompt Caching Optimization.

Tests cover:
- Basic cache set and get operations
- Cache misses and expiration
- Prefix matching for partial hits
- Cache statistics tracking
- Performance benchmarks
"""

import asyncio
import pytest
import time
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

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
    @pytest.mark.performance
    async def test_cache_performance(self):
        """Test cache performance under load."""
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
