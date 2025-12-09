"""
Episodic Memory System Tests

Tests for episodic memory system in isolation.
"""

import pytest
from optimization.memory.episodic import TaskOutcome


@pytest.mark.asyncio
class TestEpisodicMemory:
    """Test episodic memory system."""

    async def test_store_and_retrieve(self, episodic_memory):
        """Test storing and retrieving tasks."""
        entry_id = await episodic_memory.store(
            goal="Analyze dataset",
            context={"size": 1000},
            tools_used=["analyzer"],
            outcome=TaskOutcome.SUCCESS,
            confidence=0.9,
            duration=2.5
        )

        assert entry_id in episodic_memory.entries

        # Retrieve
        retrieved = await episodic_memory.retrieve("Analyze")
        assert len(retrieved) == 1
        assert retrieved[0].goal == "Analyze dataset"

    async def test_success_rate_calculation(self, episodic_memory):
        """Test success rate calculation."""
        # Store mixed outcomes
        await episodic_memory.store(
            goal="Task A",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS
        )
        await episodic_memory.store(
            goal="Task A",
            context={},
            tools_used=[],
            outcome=TaskOutcome.FAILURE
        )
        await episodic_memory.store(
            goal="Task A",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS
        )

        rate = await episodic_memory.get_success_rate("Task A")
        assert rate == 2 / 3

    async def test_lessons_learned(self, episodic_memory):
        """Test lesson extraction."""
        # Store failures with lessons
        await episodic_memory.store(
            goal="Failed task",
            context={},
            tools_used=[],
            outcome=TaskOutcome.FAILURE,
            lesson_learned="Need better error handling"
        )

        lessons = await episodic_memory.get_lessons()
        assert len(lessons) > 0
        assert "Need better error handling" in lessons[0]["lesson"]

    async def test_confidence_update(self, episodic_memory):
        """Test confidence updates."""
        entry_id = await episodic_memory.store(
            goal="Test task",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS,
            confidence=0.5
        )

        # Update confidence
        success = await episodic_memory.update_confidence(entry_id, 0.8)
        assert success

        # Verify updated
        entry = episodic_memory.entries[entry_id]
        assert entry.confidence == 0.8

    async def test_capacity_enforcement(self, episodic_memory):
        """Test capacity limit enforcement."""
        # Store more than capacity
        for i in range(110):
            await episodic_memory.store(
                goal=f"Task {i}",
                context={"index": i},
                tools_used=[],
                outcome=TaskOutcome.SUCCESS,
                confidence=0.5 + (i % 10) * 0.1
            )

        # Should be within capacity
        assert len(episodic_memory.entries) <= episodic_memory.config.max_entries

    async def test_recency_score(self, episodic_memory):
        """Test recency score calculation."""
        entry_id = await episodic_memory.store(
            goal="Recent task",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS
        )

        entry = episodic_memory.entries[entry_id]
        recency = entry.recency_score

        # Should be high for recent entries
        assert 0.9 <= recency <= 1.0
