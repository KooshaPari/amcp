"""SmartCP Services Package.

Provides core business logic services including:
- User-scoped memory management
- Code execution
- Learning patterns
"""

from .memory import (
    UserScopedMemory,
    MemoryItem,
    MemoryType,
    create_memory_service,
)
from .executor import (
    UserScopedExecutor,
    ExecutionResult,
    SecurityChecker,
    create_executor_service,
)

__all__ = [
    # Memory
    "UserScopedMemory",
    "MemoryItem",
    "MemoryType",
    "create_memory_service",
    # Executor
    "UserScopedExecutor",
    "ExecutionResult",
    "SecurityChecker",
    "create_executor_service",
]
