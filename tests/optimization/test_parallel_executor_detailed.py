"""
Comprehensive tests for parallel executor.

Tests DependencyAnalyzer and ParallelToolExecutor edge cases.
"""

import pytest
import asyncio
from optimization.parallel_executor.executor import ParallelToolExecutor
from optimization.parallel_executor.analyzer import DependencyAnalyzer
from optimization.parallel_executor.models import (
    ExecutionConfig,
    ExecutionStatus,
    ToolResult,
)


class TestDependencyAnalyzerDetailed:
    """Detailed tests for DependencyAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create dependency analyzer."""
        return DependencyAnalyzer()

    def test_analyze_empty_list(self, analyzer):
        """Test analysis of empty tool list."""
        groups = analyzer.analyze([])
        assert groups == []

    def test_analyze_single_tool(self, analyzer):
        """Test analysis of single tool."""
        tools = [("search", {"query": "test"})]
        groups = analyzer.analyze(tools)
        assert len(groups) == 1
        assert 0 in groups[0]

    def test_has_dependency_independent_tools(self, analyzer):
        """Test dependency check for independent tools."""
        assert analyzer._has_dependency("search", {}, "list", {}) is False
        assert analyzer._has_dependency("check", {}, "validate", {}) is False

    def test_has_dependency_write_after_read(self, analyzer):
        """Test dependency for write after read."""
        assert analyzer._has_dependency(
            "update_file",
            {"path": "/tmp/test.txt"},
            "read_file",
            {"path": "/tmp/test.txt"}
        ) is True

    def test_has_dependency_different_resources(self, analyzer):
        """Test no dependency for different resources."""
        assert analyzer._has_dependency(
            "update_file",
            {"path": "/tmp/file1.txt"},
            "read_file",
            {"path": "/tmp/file2.txt"}
        ) is False

    def test_same_resource_path(self, analyzer):
        """Test same resource detection by path."""
        assert analyzer._same_resource(
            {"path": "/tmp/test.txt"},
            {"path": "/tmp/test.txt"}
        ) is True
        assert analyzer._same_resource(
            {"path": "/tmp/test.txt"},
            {"path": "/tmp/other.txt"}
        ) is False

    def test_same_resource_id(self, analyzer):
        """Test same resource detection by id."""
        assert analyzer._same_resource(
            {"id": "123"},
            {"id": "123"}
        ) is True
        assert analyzer._same_resource(
            {"id": "123"},
            {"id": "456"}
        ) is False

    def test_same_resource_url(self, analyzer):
        """Test same resource detection by url."""
        assert analyzer._same_resource(
            {"url": "https://example.com"},
            {"url": "https://example.com"}
        ) is True

    def test_is_write_operation(self, analyzer):
        """Test write operation detection."""
        assert analyzer._is_write_operation("write_file") is True
        assert analyzer._is_write_operation("update_file") is True
        assert analyzer._is_write_operation("delete_file") is True
        assert analyzer._is_write_operation("create_file") is True
        assert analyzer._is_write_operation("set_value") is True
        assert analyzer._is_write_operation("add_item") is True
        assert analyzer._is_write_operation("remove_item") is True
        assert analyzer._is_write_operation("read_file") is False
        assert analyzer._is_write_operation("search") is False

    def test_is_read_operation(self, analyzer):
        """Test read operation detection."""
        assert analyzer._is_read_operation("read_file") is True
        assert analyzer._is_read_operation("get_data") is True
        assert analyzer._is_read_operation("list_files") is True
        assert analyzer._is_read_operation("search_files") is True
        assert analyzer._is_read_operation("find_item") is True
        assert analyzer._is_read_operation("check_status") is True
        assert analyzer._is_read_operation("write_file") is False
        assert analyzer._is_read_operation("update_file") is False

    def test_analyze_cycle_detection(self, analyzer):
        """Test cycle detection in dependencies."""
        # Create circular dependency
        tools = [
            ("update", {"file": "test.txt"}),  # Depends on read
            ("read", {"file": "test.txt"}),   # Would depend on update (cycle)
        ]

        groups = analyzer.analyze(tools)

        # Should handle cycle gracefully
        assert len(groups) >= 1

    def test_analyze_pattern_dependencies(self, analyzer):
        """Test pattern-based dependency detection."""
        tools = [
            ("read_file", {"file": "test.txt"}),
            ("update_file", {"file": "test.txt"}),  # Depends on read
        ]

        groups = analyzer.analyze(tools)

        # Update should come after read
        assert len(groups) >= 2
        assert 0 in groups[0]  # Read in first group
        assert 1 in groups[1]  # Update in second group


class TestParallelToolExecutorDetailed:
    """Detailed tests for ParallelToolExecutor."""

    @pytest.fixture
    def executor(self):
        """Create parallel executor."""
        config = ExecutionConfig(
            max_concurrent=3,
            default_timeout=5.0,
            max_retries=2,
            retry_delay=0.1,
            retry_backoff=2.0,
        )
        return ParallelToolExecutor(config)

    @pytest.mark.asyncio
    async def test_execute_single_success(self, executor):
        """Test successful single execution."""
        async def mock_tool(name: str, input: dict) -> str:
            return f"Success: {name}"

        result = await executor.execute_single(
            "test_tool",
            {"param": "value"},
            mock_tool,
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.output == "Success: test_tool"
        assert result.retry_count == 0
        assert result.execution_time_ms >= 0  # Can be 0 for very fast operations
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_single_retry_success(self, executor):
        """Test retry on transient failure."""
        attempt = 0

        async def flaky_tool(name: str, input: dict) -> str:
            nonlocal attempt
            attempt += 1
            if attempt < 2:
                raise ValueError("Transient error")
            return "Success after retry"

        result = await executor.execute_single(
            "flaky_tool",
            {},
            flaky_tool,
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.retry_count == 1
        assert result.output == "Success after retry"

    @pytest.mark.asyncio
    async def test_execute_single_max_retries(self, executor):
        """Test max retries exhausted."""
        async def always_failing_tool(name: str, input: dict) -> str:
            raise ValueError("Always fails")

        result = await executor.execute_single(
            "failing_tool",
            {},
            always_failing_tool,
        )

        assert result.status == ExecutionStatus.FAILED
        assert result.retry_count == executor.config.max_retries
        assert "Always fails" in result.error

    @pytest.mark.asyncio
    async def test_execute_single_timeout_retry(self, executor):
        """Test timeout with retries."""
        executor.config.default_timeout = 0.1

        async def slow_tool(name: str, input: dict) -> str:
            await asyncio.sleep(1.0)
            return "Never reached"

        result = await executor.execute_single(
            "slow_tool",
            {},
            slow_tool,
        )

        assert result.status == ExecutionStatus.TIMEOUT
        assert result.retry_count == executor.config.max_retries

    @pytest.mark.asyncio
    async def test_execute_single_custom_timeout(self, executor):
        """Test custom timeout per tool."""
        executor.config.tool_timeouts["slow_tool"] = 0.1

        async def slow_tool(name: str, input: dict) -> str:
            await asyncio.sleep(1.0)
            return "Never reached"

        result = await executor.execute_single(
            "slow_tool",
            {},
            slow_tool,
        )

        assert result.status == ExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_execute_batch_empty(self, executor):
        """Test batch execution with empty list."""
        batch = await executor.execute_batch([], lambda n, i: None)

        assert len(batch.results) == 0
        assert batch.success_count == 0

    @pytest.mark.asyncio
    async def test_execute_batch_sequential(self):
        """Test batch execution in sequential mode."""
        config = ExecutionConfig(enable_parallel=False)
        executor = ParallelToolExecutor(config)

        call_order = []

        async def ordered_tool(name: str, input: dict) -> str:
            call_order.append(name)
            await asyncio.sleep(0.05)
            return f"Result: {name}"

        tools = [("tool1", {}), ("tool2", {}), ("tool3", {})]
        batch = await executor.execute_batch(tools, ordered_tool)

        assert batch.success_count == 3
        # Should be called in order
        assert call_order == ["tool1", "tool2", "tool3"]

    @pytest.mark.asyncio
    async def test_execute_batch_preserve_order(self, executor):
        """Test batch execution preserves order."""
        executor.config.preserve_order = True

        async def mock_tool(name: str, input: dict) -> str:
            await asyncio.sleep(0.01)
            return f"Result: {name}"

        tools = [("tool3", {}), ("tool1", {}), ("tool2", {})]
        batch = await executor.execute_batch(tools, mock_tool)

        assert batch.success_count == 3
        # Results should be sorted by order_index
        assert batch.results[0].order_index == 0
        assert batch.results[1].order_index == 1
        assert batch.results[2].order_index == 2

    @pytest.mark.asyncio
    async def test_execute_batch_partial_failure(self, executor):
        """Test batch execution with partial failures."""
        async def mixed_tool(name: str, input: dict) -> str:
            if "fail" in name:
                raise ValueError("Tool failed")
            return f"Success: {name}"

        tools = [
            ("tool1", {}),
            ("fail_tool", {}),
            ("tool2", {}),
        ]

        batch = await executor.execute_batch(tools, mixed_tool)

        assert batch.success_count == 2
        assert batch.failure_count == 1
        assert batch.success_rate == pytest.approx(2/3, rel=0.1)

    @pytest.mark.asyncio
    async def test_execute_batch_exception_handling(self, executor):
        """Test batch execution handles exceptions."""
        async def exception_tool(name: str, input: dict) -> str:
            raise RuntimeError("Unexpected error")

        tools = [("tool1", {}), ("tool2", {})]
        batch = await executor.execute_batch(tools, exception_tool)

        assert batch.failure_count == 2
        assert all(r.status == ExecutionStatus.FAILED for r in batch.results)

    @pytest.mark.asyncio
    async def test_execute_with_fallback(self, executor):
        """Test execution with fallback executor."""
        async def primary_executor(name: str, input: dict) -> str:
            raise ValueError("Primary failed")

        async def fallback_executor(name: str, input: dict) -> str:
            return f"Fallback: {name}"

        tools = [("tool1", {}), ("tool2", {})]
        batch = await executor.execute_with_fallback(
            tools,
            primary_executor,
            fallback_executor,
        )

        # Should retry failed tools with fallback
        assert batch.success_count == 2
        assert all("Fallback" in str(r.output) for r in batch.results if r.output)

    @pytest.mark.asyncio
    async def test_execute_with_fallback_no_fallback(self, executor):
        """Test execution with no fallback provided."""
        async def failing_executor(name: str, input: dict) -> str:
            raise ValueError("Failed")

        tools = [("tool1", {})]
        batch = await executor.execute_with_fallback(tools, failing_executor)

        assert batch.failure_count == 1

    @pytest.mark.asyncio
    async def test_execute_batch_concurrency_limit(self):
        """Test concurrency limit enforcement."""
        config = ExecutionConfig(max_concurrent=2)
        executor = ParallelToolExecutor(config)

        concurrent_count = 0
        max_concurrent = 0

        async def counting_tool(name: str, input: dict) -> str:
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)
            concurrent_count -= 1
            return f"Result: {name}"

        tools = [("tool1", {}), ("tool2", {}), ("tool3", {}), ("tool4", {})]
        batch = await executor.execute_batch(tools, counting_tool)

        # Should not exceed max_concurrent
        assert max_concurrent <= config.max_concurrent
        assert batch.success_count == 4

    @pytest.mark.asyncio
    async def test_execute_single_retry_exhaustion_returns_result(self, executor):
        """Test that execute_single returns result after all retries exhausted (line 101)."""
        executor.config.max_retries = 2
        
        call_count = 0
        async def always_failing_tool(name: str, input: dict) -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failed attempt {call_count}")
        
        result = await executor.execute_single(
            "failing_tool",
            {},
            always_failing_tool,
        )
        
        # Verify retries exhausted and result returned (line 101 executed)
        assert result.status == ExecutionStatus.FAILED
        assert result.retry_count == executor.config.max_retries
        assert call_count == executor.config.max_retries + 1  # Initial + retries
        assert "Failed attempt" in result.error

    @pytest.mark.asyncio
    async def test_execute_batch_parallel_speedup(self, executor):
        """Test parallel speedup calculation."""
        async def slow_tool(name: str, input: dict) -> str:
            await asyncio.sleep(0.1)
            return f"Result: {name}"

        tools = [("tool1", {}), ("tool2", {}), ("tool3", {})]
        batch = await executor.execute_batch(tools, slow_tool)

        # Should show speedup (parallel faster than sequential)
        assert batch.parallel_speedup >= 1.0
        # Sequential would be ~300ms, parallel should be ~100ms
        assert batch.total_execution_time_ms < 250

    @pytest.mark.asyncio
    async def test_execute_batch_exception_from_gather(self, executor):
        """Test batch execution handles exceptions returned from gather (line 152)."""
        # To properly test line 152, we need execute_single to raise an actual exception
        # (not return a ToolResult). We'll patch execute_single to raise an exception
        # only when called from execute_batch in parallel execution context
        
        import unittest.mock
        import sys
        
        # First, preserve the original execute_single
        original_execute_single = executor.execute_single
        call_count = 0
        
        async def patched_execute_single(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Raise an exception after the first call to simulate a system-level error
            if call_count > 1:
                print(f"DEBUG: Raising exception on call {call_count}", file=sys.stderr)
                raise RuntimeError("System exception from execute_single")
            return await original_execute_single(*args, **kwargs)
        
        # Force parallel execution by patching analyzer to return single group
        with unittest.mock.patch.object(
            executor.analyzer, 
            'analyze', 
            return_value=[{0, 1}]  # Single group with both tools
        ):
            with unittest.mock.patch.object(
                executor, 
                'execute_single', 
                side_effect=patched_execute_single
            ):
                async def dummy_tool(name: str, input: dict) -> str:
                    return "dummy"
                
                tools = [("search", {"query": "test1"}), ("ping", {"host": "host1"})]
                
                # Execute batch - should handle exceptions from execute_single
                batch = await executor.execute_batch(tools, dummy_tool)
                
                # Verify line 152 executed: exceptions converted to failed ToolResults
                assert len(batch.results) == 2
                # At least one should have failed due to our patch
                assert batch.failure_count >= 1
                failed_results = [r for r in batch.results if r.status == ExecutionStatus.FAILED]
                assert len(failed_results) >= 1
                # Check for our custom error message
                assert any("System exception from execute_single" in r.error for r in failed_results)
