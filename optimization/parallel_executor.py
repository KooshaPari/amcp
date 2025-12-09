"""
Parallel Tool Executor (Backward Compatibility Shim)

This file maintains backward compatibility for existing imports.
All implementation has moved to the parallel_executor/ submodule.

DO NOT ADD NEW CODE HERE - Update the submodule instead.
"""

# Re-export all public APIs from submodule
from .parallel_executor import (
    ExecutionStatus,
    ExecutionConfig,
    ToolResult,
    ExecutionBatch,
    DependencyAnalyzer,
    ParallelToolExecutor,
    get_parallel_executor,
)

__all__ = [
    "ExecutionStatus",
    "ExecutionConfig",
    "ToolResult",
    "ExecutionBatch",
    "DependencyAnalyzer",
    "ParallelToolExecutor",
    "get_parallel_executor",
]
