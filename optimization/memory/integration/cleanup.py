"""
Memory System Cleanup and Eviction

Cleanup, eviction, and capacity management for memory systems.
"""

import logging
import time
from typing import Optional

from ..episodic import EpisodicMemory
from ..forgetting import EvictionResult
from ..semantic import SemanticMemory
from .config import MemoryConfig

logger = logging.getLogger(__name__)


class MemoryCleanup:
    """Handles cleanup and eviction for memory systems."""

    def __init__(
        self,
        config: MemoryConfig,
        episodic: EpisodicMemory,
        semantic: SemanticMemory
    ):
        self.config = config
        self.episodic = episodic
        self.semantic = semantic

    async def enforce_capacity(self) -> Optional[EvictionResult]:
        """Enforce capacity limits across all memory systems."""
        # Check episodic memory
        episodic_entries = list(self.episodic.entries.values())
        if len(episodic_entries) > self.config.episodic_config.max_entries:
            result = await self._evict_episodic()
            if result:
                return result

        # Check semantic memory
        semantic_entries = list(self.semantic.entries.values())
        if len(semantic_entries) > self.config.semantic_config.max_entries:
            result = await self._evict_semantic()
            if result:
                return result

        return None

    async def _evict_episodic(self) -> Optional[EvictionResult]:
        """Evict items from episodic memory."""
        entries = list(self.episodic.entries.values())
        target_count = int(self.config.episodic_config.max_entries * 0.9)

        # Remove least recently used + lowest confidence
        sorted_entries = sorted(
            entries,
            key=lambda e: (
                self.episodic.access_times.get(e.entry_id, 0),
                e.confidence
            )
        )

        to_remove = len(entries) - target_count
        for entry in sorted_entries[:to_remove]:
            del self.episodic.entries[entry.entry_id]
            self.episodic.access_times.pop(entry.entry_id, None)

        logger.info(f"Episodic eviction: removed {to_remove} entries")

        return EvictionResult(
            removed_count=to_remove,
            freed_memory=to_remove * 150,  # Estimate 150 bytes per episodic entry
            timestamp=time.time(),
            reason="Episodic capacity limit"
        )

    async def _evict_semantic(self) -> Optional[EvictionResult]:
        """Evict items from semantic memory."""
        entries = list(self.semantic.entries.values())
        target_count = int(self.config.semantic_config.max_entries * 0.9)

        # Remove lowest confidence entries
        sorted_entries = sorted(entries, key=lambda e: e.confidence)

        to_remove = len(entries) - target_count
        for entry in sorted_entries[:to_remove]:
            # Update entity index
            if entry.entity in self.semantic.entity_index:
                self.semantic.entity_index[entry.entity].discard(entry.entry_id)
            del self.semantic.entries[entry.entry_id]

        logger.info(f"Semantic eviction: removed {to_remove} entries")

        return EvictionResult(
            removed_count=to_remove,
            freed_memory=to_remove * 100,  # Estimate 100 bytes per semantic entry
            timestamp=time.time(),
            reason="Semantic capacity limit"
        )
