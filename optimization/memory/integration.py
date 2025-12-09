"""
Memory System Integration Layer

DEPRECATED: This file is maintained for backward compatibility.
All functionality has been moved to the integration/ submodule.

Please import from:
    from smartcp.optimization.memory.integration import (
        MemoryConfig,
        MemoryStats,
        MemorySystem,
    )
"""

# Re-export all components for backward compatibility
from .integration import (
    MemoryCleanup,
    MemoryConfig,
    MemoryOperations,
    MemoryStats,
    MemorySystem,
)

__all__ = [
    "MemoryConfig",
    "MemoryStats",
    "MemorySystem",
    "MemoryOperations",
    "MemoryCleanup",
]
