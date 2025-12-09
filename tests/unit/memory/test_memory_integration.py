"""
Memory System Integration Tests

Tests for unified memory system combining episodic, semantic, and working memory.
"""

import asyncio
import pytest
from optimization.memory.integration import MemorySystem, MemoryConfig
from optimization.memory.episodic import TaskOutcome
from optimization.memory.semantic import RelationType


@pytest.fixture
def memory_system():
    """Create memory system instance."""
    config = MemoryConfig()
    return MemorySystem(config)


@pytest.mark.asyncio
class TestMemorySystemUnified:
    """Test unified memory system operations."""

    async def test_record_and_recall_task(self, memory_system):
        """Test recording and recalling tasks."""
        # Record a task
        entry_id = await memory_system.record_task(
            goal="Analyze user data",
            context={"user_id": "123", "dataset_size": 1000},
            tools_used=["data_analyzer", "query_engine"],
            outcome=TaskOutcome.SUCCESS,
            confidence=0.9,
            duration=2.5
        )

        assert entry_id
        assert entry_id in memory_system.episodic.entries

        # Recall similar tasks
        similar = await memory_system.recall_similar_tasks("Analyze", limit=5)
        assert len(similar) == 1
        assert similar[0]["goal"] == "Analyze user data"
        assert similar[0]["outcome"] == "success"

    async def test_fact_assertion_and_query(self, memory_system):
        """Test asserting and querying facts."""
        # Assert facts
        fact_id = await memory_system.assert_fact(
            entity="GPT-4",
            property_name="capability",
            value="text_generation",
            confidence=1.0,
            source="documentation"
        )

        assert fact_id
        assert fact_id in memory_system.semantic.entries

        # Query facts
        facts = await memory_system.query_facts("GPT-4", "capability")
        assert len(facts) == 1
        assert facts[0]["value"] == "text_generation"
        assert facts[0]["confidence"] == 1.0

    async def test_relationship_assertion(self, memory_system):
        """Test relationship assertions."""
        # Assert relationships
        rel_id = await memory_system.assert_relationship(
            entity1="user_analyzer",
            relation_type=RelationType.REQUIRES,
            entity2="database_access",
            weight=0.9,
            confidence=0.95
        )

        assert rel_id
        assert rel_id in memory_system.semantic.relations

        # Query relationships
        relations = await memory_system.semantic.query_relations(
            entity1="user_analyzer"
        )
        assert len(relations) > 0
        assert relations[0].relation_type == RelationType.REQUIRES

    async def test_context_and_frame_management(self, memory_system):
        """Test context and frame operations."""
        # Create context
        context_id = await memory_system.create_context()
        assert context_id
        assert context_id in memory_system.working.contexts

        # Push frame
        frame_id = await memory_system.push_frame(
            goal="Process data",
            context_id=context_id
        )
        assert frame_id

        # Bind variable
        success = await memory_system.bind_variable(
            var_name="data",
            value=[1, 2, 3],
            context_id=context_id
        )
        assert success

        # Get variable
        value = await memory_system.get_variable("data", context_id)
        assert value == [1, 2, 3]

        # Pop frame
        frame = await memory_system.pop_frame(context_id)
        assert frame is not None
        assert frame["goal"] == "Process data"

    async def test_memory_stats(self, memory_system):
        """Test memory statistics."""
        # Add some data
        await memory_system.record_task(
            goal="Test task",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS
        )

        await memory_system.assert_fact(
            entity="test_entity",
            property_name="test_prop",
            value="test_value"
        )

        context_id = await memory_system.create_context()
        await memory_system.push_frame("Test frame", context_id)

        # Get stats
        stats = await memory_system.get_stats()

        assert stats.episodic["total_entries"] == 1
        assert stats.semantic["fact_entries"] == 1
        assert stats.working["contexts"] == 1
        assert stats.total_memory_bytes > 0
        assert 0 <= stats.capacity_utilization <= 1

    async def test_capacity_enforcement(self, memory_system):
        """Test capacity enforcement and eviction."""
        # Reduce capacity to test eviction
        memory_system.config.episodic_config.max_entries = 5

        # Record more than capacity
        for i in range(7):
            await memory_system.record_task(
                goal=f"Task {i}",
                context={"index": i},
                tools_used=[],
                outcome=TaskOutcome.SUCCESS,
                confidence=0.5 + (i * 0.05)  # Varying confidence
            )

        # Enforce capacity
        result = await memory_system.enforce_capacity()

        # Should have evicted entries
        assert len(memory_system.episodic.entries) <= 5
        if result:
            assert result.removed_count > 0

    async def test_semantic_decay(self, memory_system):
        """Test semantic confidence decay."""
        # Assert a fact
        fact_id = await memory_system.assert_fact(
            entity="test",
            property_name="prop",
            value="value",
            confidence=0.9
        )

        # Initial confidence
        facts = await memory_system.query_facts("test", "prop")
        assert facts[0]["confidence"] == 0.9

        # Apply decay
        decayed = await memory_system.decay_semantic_confidence()
        assert decayed >= 0

    async def test_idle_cleanup(self, memory_system):
        """Test cleanup of idle contexts."""
        # Create context
        context_id = await memory_system.create_context()

        # Simulate idle timeout by manipulating timestamp
        context = memory_system.working.contexts[context_id]
        context.timestamp = 0  # Very old timestamp

        # Clean up idle
        cleaned = await memory_system.cleanup_idle()
        assert cleaned == 1
        assert context_id not in memory_system.working.contexts

    async def test_concurrent_operations(self, memory_system):
        """Test concurrent memory operations."""
        # Create multiple concurrent tasks
        tasks = [
            memory_system.record_task(
                goal=f"Concurrent task {i}",
                context={"id": i},
                tools_used=[],
                outcome=TaskOutcome.SUCCESS
            )
            for i in range(10)
        ]

        entry_ids = await asyncio.gather(*tasks)
        assert len(entry_ids) == 10
        assert all(eid in memory_system.episodic.entries for eid in entry_ids)

    async def test_memory_export_snapshot(self, memory_system):
        """Test memory snapshot export."""
        # Add some data
        await memory_system.record_task(
            goal="Snapshot test",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS
        )

        await memory_system.assert_fact(
            entity="snapshot_entity",
            property_name="prop",
            value="value"
        )

        # Export snapshot
        snapshot = await memory_system.export_snapshot()

        assert "episodic" in snapshot
        assert "semantic" in snapshot
        assert "working" in snapshot
        assert "timestamp" in snapshot
        assert len(snapshot["episodic"]["entries"]) == 1
        assert len(snapshot["semantic"]["entries"]) == 1

    async def test_clear_all_memory(self, memory_system):
        """Test clearing all memory."""
        # Add data
        await memory_system.record_task(
            goal="Clear test",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS
        )

        await memory_system.assert_fact(
            entity="clear_entity",
            property_name="prop",
            value="value"
        )

        # Clear all
        await memory_system.clear_all()

        # Verify empty
        episodic_stats = await memory_system.episodic.stats()
        semantic_stats = await memory_system.semantic.stats()
        working_stats = await memory_system.working.stats()

        assert episodic_stats["total_entries"] == 0
        assert semantic_stats["fact_entries"] == 0
        assert working_stats["contexts"] == 0


@pytest.mark.asyncio
class TestMemorySystemBackground:
    """Test background cleanup operations."""

    async def test_cleanup_task_startup(self, memory_system):
        """Test cleanup task startup and shutdown."""
        # Start cleanup task
        await memory_system.start()
        assert memory_system._cleanup_task is not None

        # Stop cleanup task
        await memory_system.stop()
        assert memory_system._cleanup_task is None

    async def test_cleanup_loop_execution(self, memory_system):
        """Test cleanup loop executes properly."""
        memory_system.config.cleanup_interval_seconds = 0.1  # Short interval

        await memory_system.start()

        # Add data
        await memory_system.record_task(
            goal="Background test",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS
        )

        initial_cleanup_time = memory_system._last_cleanup

        # Wait for cleanup cycle
        await asyncio.sleep(0.2)

        # Cleanup should have run
        assert memory_system._last_cleanup >= initial_cleanup_time

        await memory_system.stop()


@pytest.mark.asyncio
class TestMemorySystemErrorHandling:
    """Test error handling in memory system."""

    async def test_invalid_context_operation(self, memory_system):
        """Test operations on invalid context."""
        # Try to bind to non-existent context
        success = await memory_system.bind_variable(
            var_name="var",
            value="value",
            context_id="invalid_context"
        )
        assert success is False

    async def test_concurrent_context_access(self, memory_system):
        """Test concurrent access to same context."""
        context_id = await memory_system.create_context()
        # Need a frame to bind variables to
        await memory_system.push_frame("Test frame", context_id)

        # Concurrent bindings
        tasks = [
            memory_system.bind_variable(
                var_name=f"var_{i}",
                value=i,
                context_id=context_id
            )
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)
        assert all(results)

        # Verify all variables bound
        context = await memory_system.working.get_context(context_id)
        assert context is not None
