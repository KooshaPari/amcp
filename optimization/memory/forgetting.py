"""
Forgetting Mechanisms for Memory Systems

Implements three types of forgetting to manage memory capacity and relevance:
- LRU Eviction: Least Recently Used items removed first
- Temporal Decay: Confidence degrades over time
- Relevance Pruning: Items removed based on relevance score

Key Features:
- Configurable capacity limits
- Decay rate customization
- Relevance-based pruning
- Batch operations for efficiency
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EvictionResult:
    """Result of eviction operation."""

    removed_count: int
    freed_memory: int
    timestamp: float
    reason: str


class ForgetMechanism(ABC):
    """Base class for forgetting mechanisms."""

    @abstractmethod
    async def should_evict(self, item: Any) -> bool:
        """Determine if item should be evicted."""
        pass

    @abstractmethod
    async def evict(self, items: List[Any], target_count: int) -> EvictionResult:
        """Evict items until target count reached."""
        pass


class LRUEviction(ForgetMechanism):
    """Least Recently Used eviction policy."""

    def __init__(self, access_times: Dict[str, float]):
        self.access_times = access_times

    async def should_evict(self, item_id: str) -> bool:
        """Item should be evicted if least recently used."""
        if not self.access_times:
            return False

        oldest_time = min(self.access_times.values())
        return self.access_times.get(item_id, time.time()) <= oldest_time

    async def evict(
        self,
        item_ids: List[str],
        target_count: int
    ) -> EvictionResult:
        """Evict least recently used items."""
        start_time = time.time()

        if len(item_ids) <= target_count:
            return EvictionResult(
                removed_count=0,
                freed_memory=0,
                timestamp=start_time,
                reason="No eviction needed"
            )

        # Sort by access time (oldest first)
        sorted_ids = sorted(
            item_ids,
            key=lambda x: self.access_times.get(x, 0)
        )

        to_remove = len(item_ids) - target_count
        removed_ids = sorted_ids[:to_remove]

        # Clean up access times
        for item_id in removed_ids:
            self.access_times.pop(item_id, None)

        logger.info(
            f"LRU eviction: removed {to_remove} items, "
            f"{len(item_ids) - to_remove} remaining"
        )

        return EvictionResult(
            removed_count=to_remove,
            freed_memory=to_remove * 100,  # Estimate 100 bytes per item
            timestamp=start_time,
            reason="LRU eviction"
        )


class TemporalDecay(ForgetMechanism):
    """Temporal decay of confidence over time."""

    def __init__(
        self,
        decay_rate: float = 0.01,
        half_life_days: float = 30.0
    ):
        self.decay_rate = decay_rate
        self.half_life_seconds = half_life_days * 86400

    async def should_evict(
        self,
        confidence: float,
        age_seconds: float,
        threshold: float = 0.3
    ) -> bool:
        """Item should be evicted if confidence decays below threshold."""
        decayed = await self._decay_confidence(confidence, age_seconds)
        return decayed < threshold

    async def evict(
        self,
        items: List[Dict[str, Any]],
        target_count: int,
        confidence_threshold: float = 0.3
    ) -> EvictionResult:
        """Remove items with decayed confidence below threshold."""
        start_time = time.time()

        # Filter items by confidence threshold
        to_keep = []
        to_remove = []

        for item in items:
            confidence = item.get("confidence", 0.5)
            age_seconds = item.get("age_seconds", 0)

            decayed = await self._decay_confidence(confidence, age_seconds)

            if decayed >= confidence_threshold:
                to_keep.append(item)
            else:
                to_remove.append(item)

        # If still over target, remove lowest confidence
        if len(to_keep) > target_count:
            to_keep.sort(
                key=lambda x: self._decay_confidence_sync(
                    x.get("confidence", 0.5),
                    x.get("age_seconds", 0)
                ),
                reverse=True
            )
            excess = len(to_keep) - target_count
            to_remove.extend(to_keep[target_count:])
            to_keep = to_keep[:target_count]

        logger.info(
            f"Temporal decay: removed {len(to_remove)} items, "
            f"{len(to_keep)} remaining"
        )

        return EvictionResult(
            removed_count=len(to_remove),
            freed_memory=len(to_remove) * 100,
            timestamp=start_time,
            reason="Temporal decay"
        )

    async def _decay_confidence(
        self,
        confidence: float,
        age_seconds: float
    ) -> float:
        """Calculate decayed confidence value."""
        if age_seconds <= 0:
            return confidence

        # Exponential decay: C(t) = C0 * e^(-decay_rate * t)
        decay_factor = (age_seconds / self.half_life_seconds) * self.decay_rate
        decayed = confidence * (1 - decay_factor)
        return max(0.0, min(1.0, decayed))

    def _decay_confidence_sync(
        self,
        confidence: float,
        age_seconds: float
    ) -> float:
        """Synchronous version for sorting."""
        if age_seconds <= 0:
            return confidence

        decay_factor = (age_seconds / self.half_life_seconds) * self.decay_rate
        decayed = confidence * (1 - decay_factor)
        return max(0.0, min(1.0, decayed))


class RelevancePruning(ForgetMechanism):
    """Relevance-based pruning of items."""

    def __init__(
        self,
        relevance_weights: Optional[Dict[str, float]] = None
    ):
        self.relevance_weights = relevance_weights or {}

    async def should_evict(
        self,
        item_id: str,
        relevance_threshold: float = 0.3
    ) -> bool:
        """Item should be evicted if relevance below threshold."""
        relevance = self.relevance_weights.get(item_id, 0.5)
        return relevance < relevance_threshold

    async def evict(
        self,
        items: List[Dict[str, Any]],
        target_count: int,
        relevance_threshold: float = 0.3
    ) -> EvictionResult:
        """Remove low-relevance items."""
        start_time = time.time()

        # Calculate relevance for each item
        scored_items = []
        for item in items:
            item_id = item.get("id")
            relevance = self.relevance_weights.get(item_id, 0.5)
            scored_items.append((item, relevance))

        # Sort by relevance (highest first)
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Keep top items by relevance
        to_keep = [item for item, _ in scored_items[:target_count]]
        to_remove = [item for item, _ in scored_items[target_count:]]

        # Remove below-threshold items regardless
        remaining = []
        also_removed = []
        for item, relevance in scored_items[target_count:]:
            if relevance >= relevance_threshold:
                remaining.append(item)
            else:
                also_removed.append(item)

        to_remove = [item for item, _ in scored_items[target_count:]]

        logger.info(
            f"Relevance pruning: removed {len(to_remove)} items, "
            f"kept {len(to_keep)} relevant items"
        )

        return EvictionResult(
            removed_count=len(to_remove),
            freed_memory=len(to_remove) * 100,
            timestamp=start_time,
            reason="Relevance pruning"
        )

    def update_relevance(self, item_id: str, relevance: float) -> None:
        """Update relevance score for an item."""
        self.relevance_weights[item_id] = max(0.0, min(1.0, relevance))

    def boost_relevance(self, item_id: str, boost: float = 0.1) -> None:
        """Increase relevance score for an item."""
        current = self.relevance_weights.get(item_id, 0.5)
        self.relevance_weights[item_id] = min(1.0, current + boost)

    def decay_relevance(self, item_id: str, decay: float = 0.05) -> None:
        """Decrease relevance score for an item."""
        current = self.relevance_weights.get(item_id, 0.5)
        self.relevance_weights[item_id] = max(0.0, current - decay)


class HybridForgetting(ForgetMechanism):
    """Combination of multiple forgetting mechanisms."""

    def __init__(
        self,
        lru: Optional[LRUEviction] = None,
        temporal_decay: Optional[TemporalDecay] = None,
        relevance_pruning: Optional[RelevancePruning] = None,
        lru_weight: float = 0.4,
        temporal_weight: float = 0.3,
        relevance_weight: float = 0.3
    ):
        self.lru = lru
        self.temporal_decay = temporal_decay
        self.relevance_pruning = relevance_pruning
        self.lru_weight = lru_weight
        self.temporal_weight = temporal_weight
        self.relevance_weight = relevance_weight

    async def should_evict(self, item: Dict[str, Any]) -> bool:
        """Combined eviction decision."""
        score = 0.0

        if self.lru and self.lru_weight > 0:
            is_lru_candidate = await self.lru.should_evict(item.get("id"))
            score += self.lru_weight * (1.0 if is_lru_candidate else 0.0)

        if self.temporal_decay and self.temporal_weight > 0:
            is_decay_candidate = await self.temporal_decay.should_evict(
                item.get("confidence", 0.5),
                item.get("age_seconds", 0)
            )
            score += self.temporal_weight * (1.0 if is_decay_candidate else 0.0)

        if self.relevance_pruning and self.relevance_weight > 0:
            is_relevance_candidate = await self.relevance_pruning.should_evict(
                item.get("id")
            )
            score += self.relevance_weight * (1.0 if is_relevance_candidate else 0.0)

        # Evict if combined score > threshold
        return score > 0.5

    async def evict(
        self,
        items: List[Dict[str, Any]],
        target_count: int
    ) -> EvictionResult:
        """Multi-criteria eviction."""
        start_time = time.time()

        if len(items) <= target_count:
            return EvictionResult(
                removed_count=0,
                freed_memory=0,
                timestamp=start_time,
                reason="No eviction needed"
            )

        # Score items using multiple criteria
        scored_items = []
        for item in items:
            score = 0.0

            if self.lru:
                is_lru_candidate = await self.lru.should_evict(item.get("id"))
                score += self.lru_weight * (1.0 if is_lru_candidate else 0.0)

            if self.temporal_decay:
                is_decay_candidate = await self.temporal_decay.should_evict(
                    item.get("confidence", 0.5),
                    item.get("age_seconds", 0)
                )
                score += self.temporal_weight * (1.0 if is_decay_candidate else 0.0)

            if self.relevance_pruning:
                is_relevance_candidate = (
                    await self.relevance_pruning.should_evict(
                        item.get("id")
                    )
                )
                score += self.relevance_weight * (1.0 if is_relevance_candidate else 0.0)

            scored_items.append((item, score))

        # Sort by score (highest first - most likely to evict)
        scored_items.sort(key=lambda x: x[1], reverse=True)

        to_remove_count = len(items) - target_count
        removed_items = [item for item, _ in scored_items[:to_remove_count]]

        logger.info(
            f"Hybrid forgetting: removed {to_remove_count} items using "
            f"LRU({self.lru_weight}) + Temporal({self.temporal_weight}) + "
            f"Relevance({self.relevance_weight})"
        )

        return EvictionResult(
            removed_count=to_remove_count,
            freed_memory=to_remove_count * 100,
            timestamp=start_time,
            reason="Hybrid forgetting"
        )
