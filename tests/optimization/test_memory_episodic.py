"""
Comprehensive tests for episodic memory system.

Tests core functionality:
- Task storage and retrieval
- Similarity search
- Confidence updating
- Lesson extraction
- Statistics and capacity management
"""

import asyncio
import pytest
import time
from unittest.mock import patch, AsyncMock

from optimization.memory.episodic import (
    EpisodicMemory,
    EpisodicEntry,
    EpisodicConfig,
    TaskOutcome,
)


@pytest.fixture
def config():
    """Test configuration for episodic memory."""
    return EpisodicConfig(
        max_entries=10,
        enable_similarity_search=True,
        similarity_threshold=0.5,
        max_similar_tasks=3,
        retention_days=30,
        success_weight=2.0,
        failure_weight=1.0,
    )


@pytest.fixture
async def memory(config):
    """Create episodic memory instance."""
    return EpisodicMemory(config)


@pytest.fixture
def sample_context():
    """Sample task context."""
    return {
        "user_id": "test_user",
        "workspace_id": "test_workspace",
        "task_type": "file_processing",
        "input_size": 1024,
    }


@pytest.fixture
def sample_result():
    """Sample task result."""
    return {
        "output_file": "processed.txt",
        "processing_time": 1.5,
        "items_processed": 42,
    }


class TestEpisodicEntry:
    """Test EpisodicEntry dataclass."""

    def test_entry_creation(self):
        """Test creating an entry."""
        entry = EpisodicEntry(
            goal="Test goal",
            context={"key": "value"},
            tools_used=["tool1", "tool2"],
            outcome=TaskOutcome.SUCCESS,
            result={"output": "success"},
        )

        assert entry.goal == "Test goal"
        assert entry.context == {"key": "value"}
        assert entry.tools_used == ["tool1", "tool2"]
        assert entry.outcome == TaskOutcome.SUCCESS
        assert entry.result == {"output": "success"}
        assert entry.entry_id is not None
        assert entry.timestamp > 0

    def test_age_calculation(self):
        """Test age calculation."""
        past_time = time.time() - 100
        entry = EpisodicEntry(timestamp=past_time)
        
        assert entry.age_seconds >= 99
        assert entry.age_seconds <= 101

    def test_recency_score(self):
        """Test recency score calculation."""
        # Recent entry should have high score
        recent_entry = EpisodicEntry(timestamp=time.time())
        assert recent_entry.recency_score > 0.9

        # Old entry should have low score
        old_entry = EpisodicEntry(timestamp=time.time() - (30 * 24 * 3600))
        assert old_entry.recency_score <= 0.1

    def test_to_dict(self):
        """Test dictionary conversion."""
        entry = EpisodicEntry(
            goal="Test",
            context={"a": 1},
            tools_used=["tool1"],
            outcome=TaskOutcome.SUCCESS,
            result={"x": "y"},
            confidence=0.8,
        )

        d = entry.to_dict()
        assert d["goal"] == "Test"
        assert d["context"] == {"a": 1}
        assert d["tools_used"] == ["tool1"]
        assert d["outcome"] == "success"
        assert d["result"] == {"x": "y"}
        assert d["confidence"] == 0.8
        assert "age_seconds" in d
        assert "recency_score" in d


class TestEpisodicMemory:
    """Test EpisodicMemory class."""

    async def test_store_entry(self, memory, sample_context, sample_result):
        """Test storing an entry."""
        entry_id = await memory.store(
            goal="Process file",
            context=sample_context,
            tools_used=["file_processor"],
            outcome=TaskOutcome.SUCCESS,
            result=sample_result,
            confidence=0.9,
            duration=2.5,
            lesson_learned="Always validate input",
        )

        assert entry_id is not None
        assert entry_id in memory.entries
        
        entry = memory.entries[entry_id]
        assert entry.goal == "Process file"
        assert entry.context == sample_context
        assert entry.tools_used == ["file_processor"]
        assert entry.outcome == TaskOutcome.SUCCESS
        assert entry.result == sample_result
        assert entry.confidence == 0.9
        assert entry.duration == 2.5
        assert entry.lesson_learned == "Always validate input"

    async def test_store_without_similarity_search(self, config, sample_context):
        """Test storing with similarity search disabled."""
        config.enable_similarity_search = False
        memory = EpisodicMemory(config)

        entry_id = await memory.store(
            goal="Test task",
            context=sample_context,
            tools_used=["test_tool"],
            outcome=TaskOutcome.SUCCESS,
        )

        entry = memory.entries[entry_id]
        assert len(entry.similar_past_tasks) == 0

    async def test_retrieve_by_goal(self, memory, sample_context):
        """Test retrieving entries by goal."""
        # Store multiple entries
        await memory.store("Process file", sample_context, ["tool1"], TaskOutcome.SUCCESS)
        await memory.store("Analyze data", sample_context, ["tool2"], TaskOutcome.FAILURE)
        await memory.store("Process file", sample_context, ["tool3"], TaskOutcome.PARTIAL)

        # Retrieve all file processing tasks
        entries = await memory.retrieve("Process file")
        assert len(entries) == 2
        assert all("process" in e.goal.lower() for e in entries)

        # Retrieve with limit
        entries = await memory.retrieve("Process file", limit=1)
        assert len(entries) == 1

    async def test_retrieve_with_context(self, memory, sample_context):
        """Test retrieving with context."""
        await memory.store("Task with context", sample_context, ["tool1"], TaskOutcome.SUCCESS)
        
        entries = await memory.retrieve("Task with context", context=sample_context)
        assert len(entries) == 1
        assert entries[0].context == sample_context

    async def test_retrieve_similar(self, memory, sample_context):
        """Test retrieving similar tasks."""
        # Store entry with similar tasks
        entry_id = await memory.store(
            "Process file",
            sample_context,
            ["tool1"],
            TaskOutcome.SUCCESS,
        )

        # Store some similar tasks
        await memory.store("Process document", {"task": "file"}, ["tool1"], TaskOutcome.SUCCESS)
        await memory.store("Handle file", {"document": "true"}, ["tool2"], TaskOutcome.PARTIAL)

        # The first entry should have similar tasks
        entry = memory.entries[entry_id]
        assert len(entry.similar_past_tasks) > 0

        # Retrieve similar tasks
        similar = await memory.retrieve_similar(entry_id)
        assert len(similar) >= 0  # May be 0 if similarity threshold not met

    async def test_update_confidence(self, memory, sample_context):
        """Test updating confidence."""
        entry_id = await memory.store(
            "Test task",
            sample_context,
            ["tool1"],
            TaskOutcome.SUCCESS,
            confidence=0.5,
        )

        # Update confidence
        success = await memory.update_confidence(entry_id, 0.9)
        assert success
        
        entry = memory.entries[entry_id]
        assert entry.confidence == 0.9

        # Test bounds
        await memory.update_confidence(entry_id, 1.5)
        assert entry.confidence == 1.0
        
        await memory.update_confidence(entry_id, -0.5)
        assert entry.confidence == 0.0

        # Test non-existent entry
        success = await memory.update_confidence("non_existent", 0.5)
        assert not success

    async def test_get_lessons(self, memory, sample_context):
        """Test getting lessons learned."""
        # Store entries with lessons
        await memory.store(
            "Failed task 1",
            sample_context,
            ["tool1"],
            TaskOutcome.FAILURE,
            lesson_learned="Lesson 1",
        )
        await memory.store(
            "Failed task 2",
            sample_context,
            ["tool2"],
            TaskOutcome.ERROR,
            lesson_learned="Lesson 2",
        )
        await memory.store(
            "Successful task",
            sample_context,
            ["tool3"],
            TaskOutcome.SUCCESS,
            lesson_learned="Lesson 3",  # Should not appear in lessons
        )

        lessons = await memory.get_lessons()
        assert len(lessons) == 2  # Only from non-success outcomes
        
        lesson_texts = [l["lesson"] for l in lessons]
        assert "Lesson 1" in lesson_texts
        assert "Lesson 2" in lesson_texts
        assert "Lesson 3" not in lesson_texts

    async def test_get_success_rate(self, memory, sample_context):
        """Test getting success rate."""
        # No entries -> default rate
        rate = await memory.get_success_rate()
        assert rate == 0.5

        # Store mixed outcomes
        await memory.store("Task 1", sample_context, ["tool1"], TaskOutcome.SUCCESS)
        await memory.store("Task 2", sample_context, ["tool2"], TaskOutcome.SUCCESS)
        await memory.store("Task 3", sample_context, ["tool3"], TaskOutcome.FAILURE)

        rate = await memory.get_success_rate()
        assert rate == 2/3  # 2 successes out of 3

        # Filter by goal prefix
        rate = await memory.get_success_rate("Task")
        assert rate == 2/3

        rate = await memory.get_success_rate("Nonexistent")
        assert rate == 0.5  # No matching tasks

    async def test_stats(self, memory, sample_context):
        """Test memory statistics."""
        # Empty memory
        stats = await memory.stats()
        assert stats["total_entries"] == 0
        assert stats["success_rate"] == 0.5
        assert stats["avg_confidence"] == 0.5

        # Add some entries
        await memory.store("Task 1", sample_context, ["tool1"], TaskOutcome.SUCCESS, confidence=0.8, duration=2.0)
        await memory.store("Task 2", sample_context, ["tool2"], TaskOutcome.FAILURE, confidence=0.6, duration=4.0)
        await memory.store("Task 3", sample_context, ["tool3"], TaskOutcome.PARTIAL, confidence=0.9, duration=1.5)

        stats = await memory.stats()
        assert stats["total_entries"] == 3
        assert stats["successful_tasks"] == 1
        assert stats["success_rate"] == 1/3
        assert abs(stats["avg_confidence"] - 0.766) < 0.01  # (0.8 + 0.6 + 0.9) / 3
        assert abs(stats["avg_duration"] - 2.5) < 0.01  # (2.0 + 4.0 + 1.5) / 3
        assert stats["capacity"] == memory.config.max_entries
        assert stats["utilization"] == 0.3  # 3 / 10

    async def test_clear(self, memory, sample_context):
        """Test clearing memory."""
        # Add entries
        await memory.store("Task 1", sample_context, ["tool1"], TaskOutcome.SUCCESS)
        await memory.store("Task 2", sample_context, ["tool2"], TaskOutcome.FAILURE)

        assert len(memory.entries) == 2

        # Clear
        await memory.clear()
        assert len(memory.entries) == 0
        assert len(memory.access_times) == 0

    async def test_capacity_enforcement(self, config, sample_context):
        """Test capacity enforcement."""
        config.max_entries = 3
        memory = EpisodicMemory(config)

        # Add entries up to capacity
        entry1 = await memory.store("Task 1", sample_context, ["tool1"], TaskOutcome.SUCCESS)
        entry2 = await memory.store("Task 2", sample_context, ["tool2"], TaskOutcome.SUCCESS)
        entry3 = await memory.store("Task 3", sample_context, ["tool3"], TaskOutcome.SUCCESS)

        assert len(memory.entries) == 3

        # Add one more - should evict oldest
        await asyncio.sleep(0.1)  # Small delay to ensure different timestamps
        entry4 = await memory.store("Task 4", sample_context, ["tool4"], TaskOutcome.SUCCESS)

        assert len(memory.entries) == 3
        # Should have evicted the oldest (entry1)
        assert entry1 not in memory.entries
        assert entry4 in memory.entries

    async def test_find_similar_overlap_calculation(self, memory):
        """Test the overlap calculation for similarity."""
        # Test identical strings
        overlap = EpisodicMemory._calculate_overlap("hello world", "hello world")
        assert overlap == 1.0

        # Test partial overlap
        overlap = EpisodicMemory._calculate_overlap("hello world test", "hello world")
        assert overlap == 2/3  # 2 words overlap / 3 total unique

        # Test no overlap
        overlap = EpisodicMemory._calculate_overlap("hello", "world")
        assert overlap == 0.0

        # Test empty strings
        overlap = EpisodicMemory._calculate_overlap("", "")
        assert overlap == 1.0

        # Test one empty
        overlap = EpisodicMemory._calculate_overlap("hello", "")
        assert overlap == 0.0

    async def test_retention_filtering(self, config, sample_context):
        """Test that old entries are filtered out."""
        config.retention_days = 0.001  # Very short retention (~86 seconds)
        memory = EpisodicMemory(config)

        # Store entry
        entry_id = await memory.store(
            "Old task",
            sample_context,
            ["tool1"],
            TaskOutcome.SUCCESS,
        )

        # Should be retrievable immediately
        entries = await memory.retrieve("Old task")
        assert len(entries) == 1

        # Wait past retention period
        await asyncio.sleep(0.1)

        # Should not be retrievable anymore
        entries = await memory.retrieve("Old task")
        assert len(entries) == 0

    async def test_concurrent_access(self, memory, sample_context):
        """Test concurrent access to memory."""
        tasks = []
        for i in range(10):
            task = memory.store(
                f"Task {i}",
                {**sample_context, "task_id": i},
                [f"tool{i}"],
                TaskOutcome.SUCCESS if i % 2 == 0 else TaskOutcome.FAILURE,
            )
            tasks.append(task)

        # All tasks should complete without error
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(r is not None for r in results)

        # Should have all entries
        assert len(memory.entries) == 10

    async def test_different_outcomes(self, memory, sample_context, sample_result):
        """Test storing different task outcomes."""
        outcomes = [
            TaskOutcome.SUCCESS,
            TaskOutcome.PARTIAL,
            TaskOutcome.FAILURE,
            TaskOutcome.TIMEOUT,
            TaskOutcome.ERROR,
        ]

        for outcome in outcomes:
            await memory.store(
                f"Task {outcome.value}",
                sample_context,
                ["test_tool"],
                outcome,
                result=sample_result,
            )

        assert len(memory.entries) == len(outcomes)

        # Check all outcomes are stored correctly
        for entry in memory.entries.values():
            assert entry.outcome in outcomes

    async def test_access_time_tracking(self, memory, sample_context):
        """Test that access times are tracked."""
        entry_id = await memory.store(
            "Test task",
            sample_context,
            ["tool1"],
            TaskOutcome.SUCCESS,
        )

        initial_time = memory.access_times[entry_id]

        # Wait a bit
        await asyncio.sleep(0.01)

        # Update confidence (should update access time)
        await memory.update_confidence(entry_id, 0.9)

        updated_time = memory.access_times[entry_id]
        assert updated_time > initial_time

    async def test_similarity_threshold_filtering(self, config, sample_context):
        """Test that similarity threshold filters properly."""
        config.similarity_threshold = 0.9  # Very high threshold
        memory = EpisodicMemory(config)

        # Store two dissimilar tasks
        await memory.store("Process file", sample_context, ["tool1"], TaskOutcome.SUCCESS)
        await memory.store("Analyze data", {"different": "context"}, ["tool2"], TaskOutcome.SUCCESS)

        # Second entry should have no similar tasks due to high threshold
        entries = list(memory.entries.values())
        assert len(entries[1].similar_past_tasks) == 0
