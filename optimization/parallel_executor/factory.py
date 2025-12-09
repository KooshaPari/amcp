"""
Global executor factory.

Provides singleton access to parallel executor instance.
"""

from typing import Optional
from .executor import ParallelToolExecutor
from .models import ExecutionConfig


# Global executor instance
_parallel_executor: Optional[ParallelToolExecutor] = None


def get_parallel_executor(config: ExecutionConfig = None) -> ParallelToolExecutor:
    """Get or create global parallel executor instance."""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelToolExecutor(config or ExecutionConfig())
    return _parallel_executor
