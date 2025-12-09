"""
Parallel tool executor implementation.

Executes tool calls with intelligent parallelization based on dependency analysis.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Awaitable, Optional

from .models import (
    ExecutionConfig,
    ExecutionStatus,
    ToolResult,
    ExecutionBatch,
)
from .analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)


class ParallelToolExecutor:
    """
    Executes tool calls with intelligent parallelization.

    Usage:
        executor = ParallelToolExecutor(ExecutionConfig())

        async def execute_tool(name: str, input: dict) -> Any:
            # Your tool execution logic
            ...

        results = await executor.execute_batch(
            tools=[
                ("search", {"query": "test"}),
                ("read_file", {"path": "/tmp/test.txt"}),
            ],
            executor=execute_tool
        )

        # results.success_rate shows completion rate
        # results.parallel_speedup shows time savings
    """

    def __init__(self, config: ExecutionConfig = None):
        self.config = config or ExecutionConfig()
        self.analyzer = DependencyAnalyzer()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)

    async def execute_single(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        executor: Callable[[str, dict], Awaitable[Any]],
        order_index: int = 0,
    ) -> ToolResult:
        """Execute a single tool with retry and timeout."""
        result = ToolResult(
            tool_name=tool_name,
            tool_input=tool_input,
            order_index=order_index,
        )

        timeout = self.config.tool_timeouts.get(
            tool_name, self.config.default_timeout
        )

        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._semaphore:
                    result.mark_started()
                    result.retry_count = attempt

                    try:
                        output = await asyncio.wait_for(
                            executor(tool_name, tool_input),
                            timeout=timeout
                        )
                        result.mark_completed(output)
                        return result

                    except asyncio.TimeoutError:
                        result.mark_timeout()
                        if attempt < self.config.max_retries:
                            await asyncio.sleep(
                                self.config.retry_delay * (self.config.retry_backoff ** attempt)
                            )
                            continue
                        return result

            except Exception as e:
                result.mark_failed(str(e))
                if attempt < self.config.max_retries:
                    await asyncio.sleep(
                        self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    )
                    continue
                return result

    async def execute_batch(
        self,
        tools: list[tuple[str, dict[str, Any]]],
        executor: Callable[[str, dict], Awaitable[Any]],
    ) -> ExecutionBatch:
        """
        Execute a batch of tools with intelligent parallelization.

        Args:
            tools: List of (tool_name, tool_input) tuples
            executor: Async function to execute tools

        Returns:
            ExecutionBatch with all results
        """
        if not tools:
            return ExecutionBatch(results=[])

        start_time = time.time()

        # Analyze dependencies
        groups = self.analyzer.analyze(tools)

        logger.info(
            f"Executing {len(tools)} tools in {len(groups)} groups "
            f"(parallel={self.config.enable_parallel})"
        )

        results: list[ToolResult] = [None] * len(tools)  # type: ignore

        # Execute groups in order
        for group_idx, group in enumerate(groups):
            group_start = time.time()

            if self.config.enable_parallel and len(group) > 1:
                # Execute group in parallel
                tasks = [
                    self.execute_single(
                        tools[i][0],
                        tools[i][1],
                        executor,
                        order_index=i
                    )
                    for i in group
                ]
                group_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in zip(group, group_results):
                    if isinstance(result, Exception):
                        results[i] = ToolResult(
                            tool_name=tools[i][0],
                            tool_input=tools[i][1],
                            order_index=i,
                            status=ExecutionStatus.FAILED,
                            error=str(result),
                        )
                    else:
                        results[i] = result
            else:
                # Execute sequentially
                for i in group:
                    results[i] = await self.execute_single(
                        tools[i][0],
                        tools[i][1],
                        executor,
                        order_index=i
                    )

            group_time = time.time() - group_start
            logger.debug(
                f"Group {group_idx + 1}/{len(groups)}: {len(group)} tools "
                f"in {group_time:.2f}s"
            )

        total_time = time.time() - start_time
        total_time_ms = int(total_time * 1000)

        # Calculate what sequential execution would have taken
        sequential_time = sum(r.execution_time_ms for r in results if r)
        parallel_speedup = sequential_time / total_time_ms if total_time_ms > 0 else 1.0

        # Sort by order if needed
        if self.config.preserve_order:
            results.sort(key=lambda r: r.order_index if r else 0)

        batch = ExecutionBatch(
            results=results,
            total_execution_time_ms=total_time_ms,
            parallel_speedup=parallel_speedup,
        )

        logger.info(
            f"Batch complete: {batch.success_count}/{len(tools)} succeeded, "
            f"speedup: {parallel_speedup:.1f}x, time: {total_time:.2f}s"
        )

        return batch

    async def execute_with_fallback(
        self,
        tools: list[tuple[str, dict[str, Any]]],
        executor: Callable[[str, dict], Awaitable[Any]],
        fallback_executor: Optional[Callable[[str, dict], Awaitable[Any]]] = None,
    ) -> ExecutionBatch:
        """Execute batch with optional fallback for failures."""
        batch = await self.execute_batch(tools, executor)

        if fallback_executor and batch.failure_count > 0:
            # Retry failed tools with fallback
            failed_indices = [
                i for i, r in enumerate(batch.results)
                if r.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT)
            ]

            logger.info(f"Retrying {len(failed_indices)} failed tools with fallback")

            for i in failed_indices:
                result = await self.execute_single(
                    tools[i][0],
                    tools[i][1],
                    fallback_executor,
                    order_index=i
                )
                batch.results[i] = result

        return batch
