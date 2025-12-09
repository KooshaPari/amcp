"""
Memory System Stress Tests

Stress tests for all memory systems.
"""

import asyncio
import pytest
from optimization.memory.episodic import (
    EpisodicMemory,
    EpisodicConfig,
    TaskOutcome
)
from optimization.memory.semantic import RelationType


@pytest.mark.asyncio
class TestMemoryStress:
    """Stress tests for memory systems."""

    async def test_large_episodic_storage(self):
        """Test storing many episodic entries."""
        # Create episodic memory with large capacity for stress test
        config = EpisodicConfig(max_entries=1000)
        episodic_memory = EpisodicMemory(config)

        for i in range(500):
            await episodic_memory.store(
                goal=f"Task {i}",
                context={"index": i},
                tools_used=[],
                outcome=TaskOutcome.SUCCESS if i % 2 == 0 else TaskOutcome.FAILURE,
                confidence=0.5 + (i % 100) * 0.005
            )

        # Should be within capacity
        assert len(episodic_memory.entries) <= episodic_memory.config.max_entries

        # Should be able to query
        retrieved = await episodic_memory.retrieve("Task 250")
        assert len(retrieved) > 0

    async def test_large_semantic_graph(self, semantic_memory):
        """Test large semantic graph."""
        # Create large graph
        for i in range(100):
            await semantic_memory.assert_fact(
                entity=f"entity_{i}",
                property_name="prop",
                value=f"value_{i}"
            )

            if i > 0:
                await semantic_memory.assert_relation(
                    entity1=f"entity_{i}",
                    relation_type=RelationType.DEPENDS_ON,
                    entity2=f"entity_{i-1}"
                )

        # Should be able to traverse
        neighbors = await semantic_memory.find_neighbors("entity_50", max_depth=5)
        assert len(neighbors) > 0

    async def test_concurrent_memory_operations(self, working_memory):
        """Test concurrent operations."""
        # Create contexts concurrently
        tasks = [
            working_memory.create_context()
            for _ in range(20)
        ]

        context_ids = await asyncio.gather(*tasks)
        assert len(context_ids) == 20
        assert all(cid in working_memory.contexts for cid in context_ids)
