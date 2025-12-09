"""
Tests for Parallel Tool Executor.

Tests the ParallelToolExecutor and DependencyAnalyzer for concurrent tool execution.
Covers: single execution, batch execution, timeout/error handling, dependency analysis.
"""

import asyncio
import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.parallel_executor.executor import ParallelToolExecutor
from optimization.parallel_executor.analyzer import DependencyAnalyzer
from optimization.parallel_executor.models import (
    ExecutionConfig,
    ExecutionStatus,
)


class TestParallelToolExecutor:
    """Tests for ParallelToolExecutor."""

    @pytest.fixture
    def executor(self):
        """Create executor."""
        config = ExecutionConfig(
            max_concurrent=3,
            default_timeout=5.0,
        )
        return ParallelToolExecutor(config)

    @pytest.mark.asyncio
    async def test_single_execution(self, executor):
        """Test single tool execution."""
        async def mock_tool(name: str, input: dict) -> str:
            return f"Result for {name}"

        result = await executor.execute_single(
            "test_tool",
            {"param": "value"},
            mock_tool,
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.output == "Result for test_tool"

    @pytest.mark.asyncio
    async def test_batch_execution(self, executor):
        """Test parallel batch execution."""
        call_times = []

        async def mock_tool(name: str, input: dict) -> str:
            call_times.append(time.time())
            await asyncio.sleep(0.1)
            return f"Result for {name}"

        tools = [
            ("tool1", {}),
            ("tool2", {}),
            ("tool3", {}),
        ]

        batch = await executor.execute_batch(tools, mock_tool)

        assert batch.success_count == 3
        assert batch.failure_count == 0

        # Should have parallel speedup
        # If executed sequentially, would take ~0.3s
        # Parallel should be closer to ~0.1s
        assert batch.total_execution_time_ms < 300

    @pytest.mark.asyncio
    async def test_timeout_handling(self, executor):
        """Test timeout handling."""
        async def slow_tool(name: str, input: dict) -> str:
            await asyncio.sleep(10)
            return "Never reached"

        executor.config.default_timeout = 0.1

        result = await executor.execute_single(
            "slow_tool",
            {},
            slow_tool,
        )

        assert result.status == ExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_error_handling(self, executor):
        """Test error handling."""
        async def failing_tool(name: str, input: dict) -> str:
            raise ValueError("Test error")

        result = await executor.execute_single(
            "failing_tool",
            {},
            failing_tool,
        )

        assert result.status == ExecutionStatus.FAILED
        assert "Test error" in result.error


class TestDependencyAnalyzer:
    """Tests for DependencyAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer."""
        return DependencyAnalyzer()

    def test_independent_tools(self, analyzer):
        """Test independent tools can be parallelized."""
        tools = [
            ("search", {"query": "test1"}),
            ("search", {"query": "test2"}),
            ("list", {"path": "/"}),
        ]

        groups = analyzer.analyze(tools)

        # All should be in the same group (parallelizable)
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_dependent_tools(self, analyzer):
        """Test dependent tools are serialized."""
        tools = [
            ("read", {"file": "test.txt"}),
            ("update", {"file": "test.txt"}),
        ]

        groups = analyzer.analyze(tools)

        # Should be in separate groups
        assert len(groups) == 2


class TestParallelExecutorPerformance:
    """Performance tests for parallel executor."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_parallel_speedup(self):
        """Test parallel execution speedup."""
        executor = ParallelToolExecutor(ExecutionConfig(max_concurrent=5))

        async def slow_tool(name: str, input: dict) -> str:
            await asyncio.sleep(0.1)
            return f"Result: {name}"

        tools = [(f"tool_{i}", {}) for i in range(10)]

        # Parallel execution
        start = time.time()
        batch = await executor.execute_batch(tools, slow_tool)
        parallel_time = time.time() - start

        # Sequential would take ~1 second (10 * 0.1)
        # Parallel should be much faster
        assert parallel_time < 0.5
        assert batch.parallel_speedup > 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
