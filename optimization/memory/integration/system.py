"""
Memory System Core

Unified memory system coordinating episodic, semantic, and working memory.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from ..episodic import EpisodicConfig, EpisodicMemory
from ..forgetting import (
    EvictionResult,
    HybridForgetting,
    LRUEviction,
    RelevancePruning,
    TemporalDecay,
)
from ..semantic import SemanticConfig, SemanticMemory
from ..working import WorkingConfig, WorkingMemory
from .cleanup import MemoryCleanup
from .config import MemoryConfig
from .operations import MemoryOperations
from .stats import MemoryStats

logger = logging.getLogger(__name__)


class MemorySystem:
    """Unified memory system for AI agents."""

    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self._lock = asyncio.Lock()

        # Initialize individual memory systems
        self.episodic = EpisodicMemory(self.config.episodic_config)
        self.semantic = SemanticMemory(self.config.semantic_config)
        self.working = WorkingMemory(self.config.working_config)

        # Initialize subsystems
        self.operations = MemoryOperations(
            episodic=self.episodic,
            semantic=self.semantic,
            working=self.working
        )
        self.cleanup = MemoryCleanup(
            config=self.config,
            episodic=self.episodic,
            semantic=self.semantic
        )

        # Initialize forgetting mechanisms
        self._init_forgetting()

        # Tracking
        self._last_cleanup = time.time()
        self._last_eviction: Optional[EvictionResult] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    def _init_forgetting(self) -> None:
        """Initialize forgetting mechanisms."""
        if not self.config.enable_forgetting:
            self._forget = None
            return

        if self.config.hybrid_forgetting:
            self._forget = HybridForgetting(
                lru=LRUEviction({}),
                temporal_decay=TemporalDecay(),
                relevance_pruning=RelevancePruning(),
                lru_weight=0.4,
                temporal_weight=0.3,
                relevance_weight=0.3
            )
        else:
            self._forget = TemporalDecay()

    async def start(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Memory system cleanup task started")

    async def stop(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Memory system cleanup task stopped")

    # Delegate operations to operations subsystem
    async def record_task(self, *args, **kwargs) -> str:
        """Record a completed task in episodic memory."""
        async with self._lock:
            return await self.operations.record_task(*args, **kwargs)

    async def recall_similar_tasks(self, *args, **kwargs):
        """Recall similar past tasks from episodic memory."""
        async with self._lock:
            return await self.operations.recall_similar_tasks(*args, **kwargs)

    async def assert_fact(self, *args, **kwargs) -> str:
        """Assert a fact in semantic memory."""
        async with self._lock:
            return await self.operations.assert_fact(*args, **kwargs)

    async def assert_relationship(self, *args, **kwargs) -> str:
        """Assert a relationship in semantic memory."""
        async with self._lock:
            return await self.operations.assert_relationship(*args, **kwargs)

    async def query_facts(self, *args, **kwargs):
        """Query facts from semantic memory."""
        async with self._lock:
            return await self.operations.query_facts(*args, **kwargs)

    async def find_related_entities(self, *args, **kwargs):
        """Find entities related to given entity."""
        async with self._lock:
            return await self.operations.find_related_entities(*args, **kwargs)

    async def create_context(self) -> str:
        """Create new working context."""
        async with self._lock:
            return await self.operations.create_context()

    async def push_frame(self, *args, **kwargs) -> str:
        """Push new frame onto context stack."""
        async with self._lock:
            return await self.operations.push_frame(*args, **kwargs)

    async def pop_frame(self, *args, **kwargs):
        """Pop frame from context stack."""
        async with self._lock:
            return await self.operations.pop_frame(*args, **kwargs)

    async def bind_variable(self, *args, **kwargs) -> bool:
        """Bind variable in working memory."""
        async with self._lock:
            return await self.operations.bind_variable(*args, **kwargs)

    async def get_variable(self, *args, **kwargs):
        """Get variable value from working memory."""
        async with self._lock:
            return await self.operations.get_variable(*args, **kwargs)

    async def cleanup_idle(self) -> int:
        """Clean up idle contexts from working memory."""
        async with self._lock:
            count = await self.operations.cleanup_idle()
            if count > 0:
                self._last_cleanup = time.time()
            return count

    async def decay_semantic_confidence(self) -> int:
        """Apply temporal decay to semantic facts."""
        async with self._lock:
            return await self.operations.decay_semantic_confidence()

    async def enforce_capacity(self) -> Optional[EvictionResult]:
        """Enforce capacity limits across all memory systems."""
        async with self._lock:
            result = await self.cleanup.enforce_capacity()
            if result:
                self._last_eviction = result
            return result

    async def get_stats(self) -> MemoryStats:
        """Get comprehensive memory statistics."""
        async with self._lock:
            episodic_stats = await self.episodic.stats()
            semantic_stats = await self.semantic.stats()
            working_stats = await self.working.stats()

            # Calculate total memory (rough estimate)
            working_bindings = 0
            for context in self.working.contexts.values():
                for frame in context.frame_stack:
                    working_bindings += len(frame.bindings)

            total_memory = (
                len(self.episodic.entries) * 150 +  # Episodic entries
                len(self.semantic.entries) * 100 +  # Semantic entries
                working_bindings * 50  # Working memory bindings
            )

            # Calculate capacity utilization
            total_capacity = (
                self.config.episodic_config.max_entries * 150 +
                self.config.semantic_config.max_entries * 100 +
                self.config.working_config.max_contexts *
                self.config.working_config.max_frame_depth *
                self.config.working_config.max_bindings_per_frame * 50
            )

            capacity_utilization = (
                total_memory / total_capacity if total_capacity > 0 else 0.0
            )

            return MemoryStats(
                episodic=episodic_stats,
                semantic=semantic_stats,
                working=working_stats,
                total_memory_bytes=total_memory,
                capacity_utilization=capacity_utilization,
                last_cleanup=self._last_cleanup,
                last_eviction=self._last_eviction
            )

    async def _cleanup_loop(self) -> None:
        """Background cleanup task."""
        try:
            while True:
                await asyncio.sleep(self.config.cleanup_interval_seconds)

                # Decay semantic confidence
                await self.decay_semantic_confidence()

                # Clean up idle working contexts
                await self.cleanup_idle()

                # Enforce capacity
                await self.enforce_capacity()

                logger.debug("Memory cleanup cycle completed")
        except asyncio.CancelledError:
            logger.debug("Memory cleanup loop cancelled")
            raise

    async def clear_all(self) -> None:
        """Clear all memory systems."""
        async with self._lock:
            await self.episodic.clear()
            await self.semantic.clear()
            await self.working.clear_all()
            logger.info("All memory systems cleared")

    async def export_snapshot(self) -> Dict[str, Any]:
        """Export complete memory snapshot."""
        async with self._lock:
            return {
                "episodic": {
                    "entries": {
                        eid: e.to_dict()
                        for eid, e in self.episodic.entries.items()
                    },
                    "stats": await self.episodic.stats()
                },
                "semantic": {
                    "entries": {
                        eid: e.to_dict()
                        for eid, e in self.semantic.entries.items()
                    },
                    "relations": {
                        rid: r.to_dict()
                        for rid, r in self.semantic.relations.items()
                    },
                    "stats": await self.semantic.stats()
                },
                "working": {
                    "contexts": len(self.working.contexts),
                    "stats": await self.working.stats()
                },
                "timestamp": time.time()
            }
