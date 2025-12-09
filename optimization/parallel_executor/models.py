"""
Data models for parallel executor.

Defines execution status, configuration, and result types.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class ExecutionStatus(str, Enum):
    """Tool execution status."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class ExecutionConfig:
    """Configuration for parallel execution."""

    # Concurrency
    max_concurrent: int = 5
    enable_parallel: bool = True

    # Timeouts
    default_timeout: float = 30.0
    tool_timeouts: dict[str, float] = field(
        default_factory=lambda: {
            "search": 60.0,
            "analyze": 120.0,
            "generate": 90.0,
        }
    )

    # Retry
    max_retries: int = 2
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

    # Ordering
    preserve_order: bool = True

    # Resource limits
    max_total_execution_time: float = 300.0


@dataclass
class ToolResult:
    """Result of a tool execution."""

    tool_name: str
    tool_input: dict[str, Any]
    output: Any = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[str] = None
    execution_time_ms: int = 0
    retry_count: int = 0
    order_index: int = 0

    # Metadata
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def mark_started(self) -> None:
        """Mark execution as started."""
        self.status = ExecutionStatus.EXECUTING
        self.started_at = time.time()

    def mark_completed(self, output: Any) -> None:
        """Mark execution as completed."""
        self.output = output
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = time.time()
        if self.started_at:
            self.execution_time_ms = int((self.completed_at - self.started_at) * 1000)

    def mark_failed(self, error: str) -> None:
        """Mark execution as failed."""
        self.error = error
        self.status = ExecutionStatus.FAILED
        self.completed_at = time.time()

    def mark_timeout(self) -> None:
        """Mark execution as timed out."""
        self.error = "Execution timed out"
        self.status = ExecutionStatus.TIMEOUT
        self.completed_at = time.time()


@dataclass
class ExecutionBatch:
    """A batch of tool executions."""

    results: list[ToolResult]
    total_execution_time_ms: int = 0
    parallel_speedup: float = 1.0

    @property
    def success_count(self) -> int:
        """Count of successful executions."""
        return sum(1 for r in self.results if r.status == ExecutionStatus.COMPLETED)

    @property
    def failure_count(self) -> int:
        """Count of failed executions."""
        return sum(
            1 for r in self.results
            if r.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT)
        )

    @property
    def success_rate(self) -> float:
        """Success rate of batch."""
        total = len(self.results)
        return self.success_count / total if total > 0 else 0.0
