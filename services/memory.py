"""User-Scoped Memory Service - Backward Compatibility Module.

This module provides backward compatibility by re-exporting the canonical
memory service implementation from infrastructure.state.

New code should import directly from:
    from smartcp.infrastructure.state import UserScopedMemory, MemoryType, MemoryItem

This module will be deprecated in a future release.
"""

# Re-export all memory-related items from canonical location
from smartcp.infrastructure.state.memory_service import (
    UserScopedMemory,
    create_memory_service,
)
from smartcp.infrastructure.state.models import MemoryItem, MemoryStats, MemoryType

__all__ = [
    "MemoryType",
    "MemoryItem",
    "MemoryStats",
    "UserScopedMemory",
    "create_memory_service",
]
