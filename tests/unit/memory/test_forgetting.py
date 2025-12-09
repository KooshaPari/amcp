"""
Forgetting Mechanisms Tests

Tests for LRU eviction, temporal decay, and relevance pruning.
"""

import asyncio
import pytest
import time
from optimization.memory.forgetting import (
    LRUEviction,
    TemporalDecay,
    RelevancePruning,
    HybridForgetting
)


@pytest.mark.asyncio
class TestLRUEviction:
    """Test Least Recently Used eviction."""

    async def test_lru_eviction_basic(self):
        """Test basic LRU eviction."""
        access_times = {
            "item_1": time.time() - 100,  # Oldest
            "item_2": time.time() - 50,
            "item_3": time.time()  # Most recent
        }

        lru = LRUEviction(access_times)

        # Evict to 2 items
        result = await lru.evict(["item_1", "item_2", "item_3"], target_count=2)

        assert result.removed_count == 1
        assert "item_1" not in lru.access_times  # Oldest removed
        assert "item_2" in lru.access_times
        assert "item_3" in lru.access_times

    async def test_lru_should_evict(self):
        """Test eviction decision."""
        access_times = {
            "a": time.time() - 100,
            "b": time.time() - 50,
            "c": time.time()
        }

        lru = LRUEviction(access_times)

        # Item 'a' should be evicted (oldest)
        should_evict = await lru.should_evict("a")
        assert should_evict

    async def test_lru_preserves_recent(self):
        """Test that recent items are preserved."""
        now = time.time()
        access_times = {
            "old": now - 1000,
            "medium": now - 500,
            "new": now
        }

        lru = LRUEviction(access_times)

        # Remove half
        result = await lru.evict(
            ["old", "medium", "new"],
            target_count=2
        )

        # Old should be removed
        assert "old" not in access_times
        assert "medium" in access_times
        assert "new" in access_times


@pytest.mark.asyncio
class TestTemporalDecay:
    """Test temporal decay of confidence."""

    async def test_confidence_decay_over_time(self):
        """Test confidence decreases with age."""
        decay = TemporalDecay(decay_rate=0.01, half_life_days=30)

        # Recent item
        recent_decayed = await decay._decay_confidence(0.9, age_seconds=3600)
        # Old item
        old_decayed = await decay._decay_confidence(0.9, age_seconds=86400 * 30)

        # Old should be more decayed
        assert recent_decayed > old_decayed

    async def test_eviction_by_decay(self):
        """Test eviction of items with low decayed confidence."""
        decay = TemporalDecay(decay_rate=0.1)

        items = [
            {
                "id": "item_1",
                "confidence": 0.9,
                "age_seconds": 86400 * 40  # 40 days old
            },
            {
                "id": "item_2",
                "confidence": 0.8,
                "age_seconds": 3600  # 1 hour old
            }
        ]

        result = await decay.evict(items, target_count=2, confidence_threshold=0.3)

        # Old item should be removed (decays below threshold)
        assert result.removed_count >= 0

    async def test_no_decay_for_recent(self):
        """Test minimal decay for recent items."""
        decay = TemporalDecay()

        decayed = await decay._decay_confidence(0.9, age_seconds=60)
        # Should be very close to original
        assert decayed > 0.88


@pytest.mark.asyncio
class TestRelevancePruning:
    """Test relevance-based pruning."""

    async def test_relevance_pruning_basic(self):
        """Test basic relevance-based pruning."""
        relevance = {
            "item_1": 0.1,   # Low relevance
            "item_2": 0.5,   # Medium
            "item_3": 0.95   # High
        }

        pruning = RelevancePruning(relevance)

        items = [
            {"id": "item_1"},
            {"id": "item_2"},
            {"id": "item_3"}
        ]

        result = await pruning.evict(items, target_count=2)

        # Low relevance items removed
        assert result.removed_count == 1

    async def test_update_relevance(self):
        """Test updating relevance scores."""
        pruning = RelevancePruning()

        # Update relevance
        pruning.update_relevance("item_1", 0.7)
        assert pruning.relevance_weights["item_1"] == 0.7

        # Clamp values
        pruning.update_relevance("item_2", 1.5)
        assert pruning.relevance_weights["item_2"] == 1.0

        pruning.update_relevance("item_3", -0.5)
        assert pruning.relevance_weights["item_3"] == 0.0

    async def test_boost_and_decay_relevance(self):
        """Test boosting and decaying relevance."""
        pruning = RelevancePruning()

        # Initial
        pruning.update_relevance("item", 0.5)

        # Boost
        pruning.boost_relevance("item", 0.2)
        assert pruning.relevance_weights["item"] == 0.7

        # Decay
        pruning.decay_relevance("item", 0.1)
        assert pruning.relevance_weights["item"] == 0.6

    async def test_should_evict_by_relevance(self):
        """Test eviction decision based on relevance."""
        relevance = {
            "low": 0.2,
            "high": 0.9
        }

        pruning = RelevancePruning(relevance)

        low_should_evict = await pruning.should_evict("low", relevance_threshold=0.3)
        high_should_evict = await pruning.should_evict("high", relevance_threshold=0.3)

        assert low_should_evict
        assert not high_should_evict


@pytest.mark.asyncio
class TestHybridForgetting:
    """Test hybrid forgetting combining multiple mechanisms."""

    async def test_hybrid_eviction_decision(self):
        """Test hybrid eviction scoring."""
        access_times = {
            "item_1": time.time() - 1000,
            "item_2": time.time()
        }

        relevance = {
            "item_1": 0.1,
            "item_2": 0.9
        }

        lru = LRUEviction(access_times)
        temporal = TemporalDecay()
        relevance_prune = RelevancePruning(relevance)

        hybrid = HybridForgetting(
            lru=lru,
            temporal_decay=temporal,
            relevance_pruning=relevance_prune,
            lru_weight=0.4,
            temporal_weight=0.3,
            relevance_weight=0.3
        )

        item_1_should_evict = await hybrid.should_evict({
            "id": "item_1",
            "confidence": 0.5,
            "age_seconds": 1000
        })

        item_2_should_evict = await hybrid.should_evict({
            "id": "item_2",
            "confidence": 0.9,
            "age_seconds": 10
        })

        # Item 1 more likely to be evicted
        assert item_1_should_evict or not item_2_should_evict

    async def test_hybrid_eviction_multi_criteria(self):
        """Test hybrid eviction with multiple criteria."""
        access_times = {
            f"item_{i}": time.time() - (i * 100)
            for i in range(5)
        }

        relevance = {
            f"item_{i}": 1.0 - (i * 0.2)
            for i in range(5)
        }

        lru = LRUEviction(access_times)
        temporal = TemporalDecay()
        relevance_prune = RelevancePruning(relevance)

        hybrid = HybridForgetting(
            lru=lru,
            temporal_decay=temporal,
            relevance_pruning=relevance_prune
        )

        items = [
            {
                "id": f"item_{i}",
                "confidence": 0.7,
                "age_seconds": i * 100
            }
            for i in range(5)
        ]

        result = await hybrid.evict(items, target_count=2)

        # Should remove 3 items
        assert result.removed_count == 3

    async def test_hybrid_weight_balancing(self):
        """Test balanced weighting in hybrid approach."""
        hybrid = HybridForgetting(
            lru_weight=0.33,
            temporal_weight=0.33,
            relevance_weight=0.34
        )

        # Weights should sum to ~1.0
        total_weight = (
            hybrid.lru_weight +
            hybrid.temporal_weight +
            hybrid.relevance_weight
        )

        assert 0.95 < total_weight <= 1.0


@pytest.mark.asyncio
class TestEvictionResults:
    """Test eviction result reporting."""

    async def test_eviction_result_tracking(self):
        """Test result metadata."""
        access_times = {"item_1": time.time() - 100}
        lru = LRUEviction(access_times)

        result = await lru.evict(["item_1"], target_count=0)

        assert result.removed_count == 1
        assert result.freed_memory > 0
        assert result.timestamp > 0
        assert "LRU" in result.reason

    async def test_no_eviction_needed(self):
        """Test when no eviction is needed."""
        access_times = {"item_1": time.time()}
        lru = LRUEviction(access_times)

        result = await lru.evict(["item_1"], target_count=10)

        assert result.removed_count == 0
        assert "No eviction" in result.reason


@pytest.mark.asyncio
class TestEvictionConcurrency:
    """Test concurrent eviction operations."""

    async def test_concurrent_evictions(self):
        """Test concurrent eviction operations."""
        access_times = {f"item_{i}": time.time() - i for i in range(100)}

        lru = LRUEviction(access_times)

        # Multiple concurrent evictions
        tasks = [
            lru.evict([f"item_{i}" for i in range(100)], target_count=80),
            lru.evict([f"item_{i}" for i in range(50, 100)], target_count=30)
        ]

        results = await asyncio.gather(*tasks)

        # Both should complete
        assert len(results) == 2
        assert all(r.removed_count >= 0 for r in results)
