"""
Comprehensive tests for memory forgetting mechanisms.

Tests core functionality:
- LRU eviction policy
- Temporal decay mechanisms
- Relevance-based pruning
- Batch eviction operations
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock

from optimization.memory.forgetting import (
    LRUEviction,
    EvictionResult,
    ForgetMechanism,
)


class TestEvictionResult:
    """Test EvictionResult dataclass."""

    def test_eviction_result_creation(self):
        """Test creating eviction result."""
        result = EvictionResult(
            removed_count=5,
            freed_memory=500,
            timestamp=time.time(),
            reason="Capacity exceeded"
        )

        assert result.removed_count == 5
        assert result.freed_memory == 500
        assert result.reason == "Capacity exceeded"
        assert result.timestamp > 0


class TestLRUEviction:
    """Test LRU eviction policy."""

    @pytest.fixture
    def access_times(self):
        """Sample access times for testing."""
        now = time.time()
        return {
            "item1": now - 100,  # Oldest
            "item2": now - 50,
            "item3": now - 10,   # Newest
        }

    @pytest.fixture
    def lru(self, access_times):
        """Create LRU eviction instance."""
        return LRUEviction(access_times)

    async def test_should_evict_oldest(self, lru, access_times):
        """Test that oldest item should be evicted."""
        # item1 is oldest (accessed 100s ago)
        assert await lru.should_evict("item1")
        assert not await lru.should_evict("item2")
        assert not await lru.should_evict("item3")

    async def test_should_evict_with_empty_access_times(self):
        """Test should_evict with empty access_times."""
        lru = LRUEviction({})
        assert not await lru.should_evict("any_item")

    async def test_should_evict_with_missing_item(self, lru):
        """Test should_evict for item not in access_times."""
        # Should use current time, making it newest
        assert not await lru.should_evict("missing_item")

    async def test_evict_no_removal_needed(self, lru):
        """Test eviction when no removal needed."""
        result = await lru.evict(["item1", "item2", "item3"], target_count=5)
        
        assert result.removed_count == 0
        assert result.freed_memory == 0
        assert result.reason == "No eviction needed"
        assert result.timestamp > 0

    async def test_evict_some_items(self, lru, access_times):
        """Test eviction of some items."""
        items = ["item1", "item2", "item3"]
        target_count = 2  # Need to remove 1 item
        
        result = await lru.evict(items, target_count)
        
        assert result.removed_count == 1
        assert result.freed_memory == 100  # 1 item * 100 bytes
        assert "item1" not in lru.access_times
        assert "item2" in lru.access_times
        assert "item3" in lru.access_times

    async def test_evict_all_items(self, lru, access_times):
        """Test eviction of all items."""
        items = ["item1", "item2", "item3"]
        target_count = 0  # Remove all
        
        result = await lru.evict(items, target_count)
        
        assert result.removed_count == 3
        assert result.freed_memory == 300  # 3 items * 100 bytes
        assert len(lru.access_times) == 0

    async def test_eviction_order(self, lru):
        """Test that eviction removes items in correct order."""
        # Add items with known access times
        now = time.time()
        items = [
            f"item{i}"
            for i in range(5)
        ]
        
        for i, item in enumerate(items):
            lru.access_times[item] = now - (5 - i) * 10  # item0 oldest, item4 newest
        
        # Remove 2 items, should remove item0 and item1
        result = await lru.evict(items, target_count=3)
        
        assert result.removed_count == 2
        assert "item0" not in lru.access_times
        assert "item1" not in lru.access_times
        assert "item2" in lru.access_times
        assert "item3" in lru.access_times
        assert "item4" in lru.access_times

    async def test_evict_with_same_access_times(self, lru):
        """Test eviction when items have same access time."""
        items = ["item1", "item2", "item3"]
        now = time.time()
        
        # Set same access time for all
        for item in items:
            lru.access_times[item] = now
        
        # Eviction should still work (order may be arbitrary but count should be correct)
        result = await lru.evict(items, target_count=2)
        
        assert result.removed_count == 1
        assert len(lru.access_times) == 2

    async def test_access_times_cleanup(self, lru):
        """Test that access times are properly cleaned up."""
        # Add extra items not being evicted
        lru.access_times["extra1"] = time.time()
        lru.access_times["extra2"] = time.time()
        
        items = ["item1", "item2"]
        target_count = 1
        
        initial_count = len(lru.access_times)
        await lru.evict(items, target_count)
        
        # Should have removed one item from items
        assert len(lru.access_times) == initial_count - 1
        # Extra items should remain
        assert "extra1" in lru.access_times
        assert "extra2" in lru.access_times

    async def test_evict_empty_list(self, lru):
        """Test eviction with empty item list."""
        result = await lru.evict([], target_count=5)
        
        assert result.removed_count == 0
        assert result.freed_memory == 0
        assert result.reason == "No eviction needed"

    async def test_evict_with_nonexistent_items(self, lru):
        """Test eviction with items not in access_times."""
        items = ["nonexistent1", "nonexistent2"]
        target_count = 1
        
        result = await lru.evict(items, target_count)
        
        # Should still remove items even if not tracked
        assert result.removed_count == 1
        assert result.freed_memory == 100

    async def test_evict_updates_access_times(self, lru):
        """Test that eviction updates access_times correctly."""
        # Pre-populate access_times
        lru.access_times.update({
            "keep1": time.time(),
            "keep2": time.time(),
            "remove1": time.time() - 100,
            "remove2": time.time() - 50,
        })
        
        items = ["remove1", "remove2", "keep1", "keep2"]
        target_count = 2
        
        result = await lru.evict(items, target_count)
        
        # Should have removed oldest two
        assert result.removed_count == 2
        assert "remove1" not in lru.access_times
        assert "remove2" not in lru.access_times
        assert "keep1" in lru.access_times
        assert "keep2" in lru.access_times


class TestForgettingMechanismABC:
    """Test the abstract base class for forgetting mechanisms."""

    async def test_cannot_instantiate_abc(self):
        """Test that ForgetMechanism cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ForgetMechanism()

    def test_abc_methods(self):
        """Test that abstract methods are defined."""
        assert ForgetMechanism.should_evict is not None
        assert ForgetMechanism.evict is not None


class TestLRUEvictionEdgeCases:
    """Test edge cases for LRU eviction."""

    async def test_large_scale_eviction(self):
        """Test eviction with large number of items."""
        # Create many items
        items = [f"item{i}" for i in range(1000)]
        access_times = {}
        now = time.time()
        
        # Stagger access times
        for i, item in enumerate(items):
            access_times[item] = now - i
        
        lru = LRUEviction(access_times)
        
        # Evict half
        result = await lru.evict(items, target_count=500)
        
        assert result.removed_count == 500
        assert result.freed_memory == 500 * 100
        assert len(lru.access_times) == 500

    async def test_eviction_with_memory_pressure(self):
        """Test eviction behavior under memory pressure."""
        # Simulate memory pressure scenario
        access_times = {}
        now = time.time()
        
        # Create items at various ages
        for i in range(100):
            access_times[f"item{i}"] = now - i
        
        lru = LRUEviction(access_times)
        
        # Aggressive eviction
        result = await lru.evict(
            list(access_times.keys()),
            target_count=10  # Keep only 10%
        )
        
        assert result.removed_count == 90
        assert len(lru.access_times) == 10
        
        # Should keep the 10 most recent
        recent_items = [f"item{i}" for i in range(90, 100)]
        for item in recent_items:
            assert item in lru.access_times

    async def test_concurrent_eviction(self):
        """Test concurrent eviction operations."""
        access_times = {}
        now = time.time()
        
        # Create shared access times
        for i in range(100):
            access_times[f"item{i}"] = now - i
        
        lru = LRUEviction(access_times)
        
        # Run concurrent evictions
        tasks = []
        for i in range(5):
            items = [f"item{j}" for j in range(i*20, (i+1)*20)]
            target_count = 10
            tasks.append(lru.evict(items, target_count))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should complete without errors
        for result in results:
            assert not isinstance(result, Exception)
            assert result.removed_count == 10

    async def test_eviction_with_time_drift(self):
        """Test eviction with significant time differences."""
        access_times = {
            "ancient": time.time() - (365 * 24 * 3600),  # 1 year ago
            "recent": time.time() - 1,  # 1 second ago
        }
        
        lru = LRUEviction(access_times)
        
        result = await lru.evict(["ancient", "recent"], target_count=1)
        
        # Should remove ancient item
        assert result.removed_count == 1
        assert "ancient" not in lru.access_times
        assert "recent" in lru.access_times

    async def test_eviction_preserves_order(self):
        """Test that eviction preserves relative order of remaining items."""
        now = time.time()
        items = []
        access_times = {}
        
        # Create items with predictable ordering
        for i in range(10):
            item = f"item{i}"
            items.append(item)
            access_times[item] = now - (9 - i)  # item0 oldest, item9 newest
        
        lru = LRUEviction(access_times)
        
        # Remove middle items
        result = await lru.evict(items, target_count=6)
        
        assert result.removed_count == 4
        
        # Remaining items should be the 6 newest
        remaining = list(lru.access_times.keys())
        assert set(remaining) == {"item4", "item5", "item6", "item7", "item8", "item9"}
        
        # Check that order is preserved (newest to oldest among remaining)
        sorted_remaining = sorted(remaining, key=lambda x: lru.access_times[x], reverse=True)
        assert sorted_remaining == ["item9", "item8", "item7", "item6", "item5", "item4"]
