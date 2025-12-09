"""Tests for performance characteristics."""

import pytest
import time
from services.embeddings import RateLimiter


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_performance(self, embedding_cache):
        """Test cache operations are fast."""
        # Populate cache
        for i in range(100):
            await embedding_cache.set(f"text-{i}", "voyage-3", [0.1] * 1024)

        # Measure retrieval time
        start = time.perf_counter()
        for i in range(100):
            await embedding_cache.get(f"text-{i}", "voyage-3")
        elapsed = time.perf_counter() - start

        # Should be fast (< 100ms for 100 retrievals)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_under_limit(self):
        """Test rate limiter doesn't block when under limit."""
        limiter = RateLimiter(rpm=1000, tpm=1000000)

        start = time.perf_counter()
        for _ in range(10):
            await limiter.acquire(tokens=100)
        elapsed = time.perf_counter() - start

        # Should complete quickly (< 100ms for 10 acquires)
        assert elapsed < 0.1
