"""Tests for Voyage AI infrastructure components (rate limiter, cache)."""

import pytest
import asyncio
from services.embeddings import RateLimiter, EmbeddingCache


class TestRateLimiter:
    """Test rate limiter."""

    def test_rate_limiter_creation(self):
        """Test rate limiter creation."""
        limiter = RateLimiter(rpm=60, tpm=100000)

        assert limiter.rpm == 60
        assert limiter.tpm == 100000

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test rate limiter acquire."""
        limiter = RateLimiter(rpm=1000, tpm=1000000)

        # Should acquire without waiting
        await limiter.acquire(tokens=100)

        # Verify usage was tracked
        assert len(limiter._token_usage) > 0

    @pytest.mark.asyncio
    async def test_rate_limiter_request_tracking(self):
        """Test rate limiter tracks requests."""
        limiter = RateLimiter(rpm=100, tpm=10000)

        await limiter.acquire(tokens=1000)
        await limiter.acquire(tokens=500)

        # Should have tracked 2 requests
        assert len(limiter._request_times) == 2


class TestEmbeddingCache:
    """Test embedding cache."""

    def test_cache_key_generation(self, embedding_cache):
        """Test cache key is deterministic."""
        text = "Test text"
        key1 = embedding_cache._get_cache_key(text, "voyage-3", None)
        key2 = embedding_cache._get_cache_key(text, "voyage-3", None)

        assert key1 == key2

    def test_cache_key_different_models(self, embedding_cache):
        """Test different models produce different keys."""
        text = "Test text"
        key1 = embedding_cache._get_cache_key(text, "voyage-3", None)
        key2 = embedding_cache._get_cache_key(text, "voyage-3-lite", None)

        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, embedding_cache):
        """Test cache set and get."""
        embedding = [0.1, 0.2, 0.3]
        await embedding_cache.set("test-text", "voyage-3", embedding)

        cached = await embedding_cache.get("test-text", "voyage-3")

        assert cached == embedding

    @pytest.mark.asyncio
    async def test_cache_miss(self, embedding_cache):
        """Test cache miss returns None."""
        cached = await embedding_cache.get("nonexistent", "voyage-3")

        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_with_input_type(self, embedding_cache):
        """Test cache respects input type."""
        embedding = [0.1, 0.2]
        await embedding_cache.set("test", "voyage-3", embedding, input_type="query")

        # Same text without input_type should not match
        cached_without = await embedding_cache.get("test", "voyage-3", input_type=None)
        cached_with = await embedding_cache.get("test", "voyage-3", input_type="query")

        assert cached_without is None
        assert cached_with == embedding

    @pytest.mark.asyncio
    async def test_cache_clear(self, embedding_cache):
        """Test cache clear."""
        await embedding_cache.set("test", "voyage-3", [0.1, 0.2])
        await embedding_cache.clear()

        # Memory cache should be empty
        assert len(embedding_cache._memory_cache) == 0
