"""State Management for SmartCP.

Provides user-scoped state management backed by Bifrost GraphQL.
All state operations are scoped to UserContext for isolation.

Unified state management layer combining:
- StateAdapter: Abstract interface for state backends
- BifrostStateAdapter: GraphQL-backed persistent storage
- InMemoryStateAdapter: In-memory testing backend
- UserScopedMemory: High-level memory service with specialized types
- MemoryType/MemoryItem: Models for typed memory storage
"""

from smartcp.infrastructure.state.adapter import StateAdapter
from smartcp.infrastructure.state.bifrost import BifrostStateAdapter
from smartcp.infrastructure.state.errors import (
    BifrostStateError,
    StateError,
    StateNotFoundError,
)
from smartcp.infrastructure.state.factory import create_state_adapter
from smartcp.infrastructure.state.memory import InMemoryStateAdapter
from smartcp.infrastructure.state.memory_service import (
    UserScopedMemory,
    create_memory_service,
)
from smartcp.infrastructure.state.models import MemoryItem, MemoryStats, MemoryType

__all__ = [
    # Adapters
    "StateAdapter",
    "BifrostStateAdapter",
    "InMemoryStateAdapter",
    # Errors
    "StateError",
    "StateNotFoundError",
    "BifrostStateError",
    # Factory
    "create_state_adapter",
    # Memory Service
    "UserScopedMemory",
    "create_memory_service",
    # Models
    "MemoryType",
    "MemoryItem",
    "MemoryStats",
]
