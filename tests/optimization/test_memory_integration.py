"""
Comprehensive tests for memory integration system.

Tests core functionality:
- Integration of all memory subsystems
- Cross-system operations
- Memory lifecycle management
- Performance and resource coordination
"""

import asyncio
import pytest
import time
from unittest.mock import patch, AsyncMock

from optimization.memory.integration.system import (
    MemorySystem,
)
from optimization.memory.integration.config import (
    MemoryConfig,
)
from optimization.memory.episodic import (
    EpisodicConfig,
    TaskOutcome,
)
from optimization.memory.semantic import (
    SemanticConfig,
)
from optimization.memory.forgetting import (
    LRUEviction,
)


class TestMemoryConfig:
    """Test MemoryConfig dataclass."""

    def test_config_creation(self):
        """Test creating memory configuration."""
        config = MemoryConfig(
            episodic_config=EpisodicConfig(max_entries=100),
            semantic_config=SemanticConfig(max_entries=200),
            cleanup_interval_seconds=1800.0,
            hybrid_forgetting=True,
        )

        assert config.episodic_config.max_entries == 100
        assert config.semantic_config.max_entries == 200
        assert config.cleanup_interval_seconds == 1800.0
        assert config.hybrid_forgetting is True


class TestMemorySystem:
    """Test MemorySystem integration class."""

    @pytest.fixture
    def config(self):
        """Test configuration for memory system."""
        return MemoryConfig(
            episodic_config=EpisodicConfig(max_entries=10),
            semantic_config=SemanticConfig(max_entries=20),
            cleanup_interval_seconds=60.0,  # Short for testing
            hybrid_forgetting=True,
        )

    @pytest.fixture
    async def memory_system(self, config):
        """Create memory system instance."""
        system = MemorySystem(config)
        # Start background task
        await system.start()
        yield system
        # Cleanup
        await system.stop()

    async def test_system_initialization(self, memory_system, config):
        """Test memory system initialization."""
        assert memory_system.config == config
        assert memory_system.episodic is not None
        assert memory_system.semantic is not None
        assert memory_system.working is not None

    async def test_record_task(self, memory_system):
        """Test recording a task execution."""
        task_id = await memory_system.record_task(
            goal="Process document",
            context={"file_type": "pdf", "size": 1024},
            tools_used=["pdf_parser", "text_extractor"],
            outcome=TaskOutcome.SUCCESS,
            result={"pages": 10, "text": "extracted"},
            confidence=0.9,
            duration=5.2,
        )

        assert task_id is not None

        # Check episodic memory
        episodic_entry = await memory_system.episodic.retrieve("Process document")
        assert len(episodic_entry) == 1
        assert episodic_entry[0].goal == "Process document"

    async def test_cleanup_system(self, memory_system):
        """Test cleanup functionality."""
        # Fill memory beyond capacity
        for i in range(15):  # Exceed episodic capacity of 10
            await memory_system.record_task(
                f"Task {i}",
                {"task_id": i},
                [f"tool{i}"],
                TaskOutcome.SUCCESS,
            )

        # Manually trigger cleanup
        await memory_system.cleanup.run_cleanup()

        # Check capacity is respected
        stats = await memory_system.episodic.stats()
        assert stats["total_entries"] <= 10

    async def test_forgetting_mechanisms(self, memory_system):
        """Test forgetting mechanisms are working."""
        # Enable forgetting
        assert memory_system.config.enable_forgetting is True
        
        # Store some tasks
        await memory_system.record_task(
            "Test task",
            {"test": True},
            ["test_tool"],
            TaskOutcome.SUCCESS,
        )

        # Wait a bit
        await asyncio.sleep(0.1)

        # Check that forgetting mechanisms exist
        assert memory_system._forget is not None

    async def test_concurrent_operations(self, memory_system):
        """Test concurrent operations across memory systems."""
        tasks = []
        
        # Record multiple tasks concurrently
        for i in range(10):
            task = memory_system.record_task(
                f"Concurrent task {i}",
                {"index": i},
                [f"tool{i}"],
                TaskOutcome.SUCCESS,
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should complete without errors
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None
        
        # Verify all tasks were recorded
        stats = await memory_system.episodic.stats()
        assert stats["total_entries"] == 10

    async def test_memory_operations(self, memory_system):
        """Test memory operations subsystem."""
        # Operations should exist
        assert memory_system.operations is not None

    async def test_memory_cleanup(self, memory_system):
        """Test memory cleanup subsystem."""
        # Cleanup should exist
        assert memory_system.cleanup is not None

    async def test_stop_and_start(self, memory_system):
        """Test stopping and starting background tasks."""
        # Should be running from fixture
        assert memory_system._cleanup_task is not None
        
        # Stop
        await memory_system.stop()
        assert memory_system._cleanup_task is None
        
        # Start again
        await memory_system.start()
        assert memory_system._cleanup_task is not None

    async def test_task_recording_with_lesson(self, memory_system):
        """Test recording task with lesson learned."""
        task_id = await memory_system.record_task(
            "Failed task",
            {"failure": True},
            ["faulty_tool"],
            TaskOutcome.FAILURE,
            lesson_learned="Always validate input",
        )

        assert task_id is not None

        # Check lesson was recorded
        lessons = await memory_system.episodic.get_lessons(limit=10)
        assert len(lessons) > 0
        lesson_texts = [l["lesson"] for l in lessons]
        assert any("validate input" in lesson for lesson in lesson_texts)

    async def test_different_outcomes(self, memory_system):
        """Test recording tasks with different outcomes."""
        outcomes = [
            TaskOutcome.SUCCESS,
            TaskOutcome.PARTIAL,
            TaskOutcome.FAILURE,
            TaskOutcome.TIMEOUT,
            TaskOutcome.ERROR,
        ]

        for outcome in outcomes:
            task_id = await memory_system.record_task(
                f"Task {outcome.value}",
                {"outcome": outcome.value},
                ["test_tool"],
                outcome,
            )
            assert task_id is not None

        # Check all were recorded
        stats = await memory_system.episodic.stats()
        assert stats["total_entries"] == len(outcomes)

    async def test_background_cleanup(self, config):
        """Test that background cleanup works."""
        # Use very short cleanup interval
        config.cleanup_interval_seconds = 0.1
        
        system = MemorySystem(config)
        
        # Add some tasks
        for i in range(12):  # Exceed capacity
            await system.record_task(f"Task {i}", {}, ["tool"], TaskOutcome.SUCCESS)
        
        initial_stats = await system.episodic.stats()
        assert initial_stats["total_entries"] > 10  # Over capacity
        
        # Start background cleanup
        await system.start()
        
        # Wait for cleanup to run
        await asyncio.sleep(0.3)  # Should trigger 3 cleanup cycles
        
        # Check cleanup happened
        final_stats = await system.episodic.stats()
        assert final_stats["total_entries"] <= 10  # At or under capacity
        
        await system.stop()

    async def test_memory_system_without_forgetting(self, config):
        """Test memory system with forgetting disabled."""
        config.enable_forgetting = False
        
        system = MemorySystem(config)
        
        # Forgetting should be None
        assert system._forget is None

    async def test_hybrid_forgetting(self, config):
        """Test hybrid forgetting configuration."""
        config.hybrid_forgetting = True
        
        system = MemorySystem(config)
        
        # Should have hybrid forgetting enabled
        assert system._forget is not None

    async def test_memory_system_stats(self, memory_system):
        """Test getting memory system statistics."""
        # Record some tasks
        await memory_system.record_task("Task 1", {}, ["tool1"], TaskOutcome.SUCCESS)
        await memory_system.record_task("Task 2", {}, ["tool2"], TaskOutcome.FAILURE)
        
        # Get individual stats
        episodic_stats = await memory_system.episodic.stats()
        semantic_stats = await memory_system.semantic.stats()
        
        # Check episodic stats
        assert episodic_stats["total_entries"] == 2
        assert episodic_stats["successful_tasks"] == 1
        
        # Check semantic stats exist
        assert "total_facts" in semantic_stats
