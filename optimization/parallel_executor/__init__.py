"""
Parallel Tool Executor

Executes independent tool calls concurrently for 3-5x throughput.

Features:
- Dependency analysis for safe parallelization
- Semaphore-based concurrency control
- Result aggregation and ordering
- Error handling with partial results
- Timeout management per tool

Reference: 2025 Agent Orchestration Research
"""

from .models import (
    ExecutionStatus,
    ExecutionConfig,
    ToolResult,
    ExecutionBatch,
)
from .analyzer import DependencyAnalyzer
from .executor import ParallelToolExecutor
from .factory import get_parallel_executor

__all__ = [
    # Enums
    "ExecutionStatus",
    # Config
    "ExecutionConfig",
    # Results
    "ToolResult",
    "ExecutionBatch",
    # Components
    "DependencyAnalyzer",
    "ParallelToolExecutor",
    # Factory
    "get_parallel_executor",
]
