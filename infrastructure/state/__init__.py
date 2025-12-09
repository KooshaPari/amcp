"""State Management Adapter for SmartCP.

Provides user-scoped state management backed by Bifrost GraphQL.
All state operations are scoped to UserContext for isolation.
"""

from smartcp.infrastructure.state.adapter import StateAdapter
from smartcp.infrastructure.state.bifrost import BifrostStateAdapter
from smartcp.infrastructure.state.memory import InMemoryStateAdapter
from smartcp.infrastructure.state.errors import (
    StateError,
    StateNotFoundError,
    BifrostStateError,
)
from smartcp.infrastructure.state.factory import create_state_adapter

__all__ = [
    "StateAdapter",
    "BifrostStateAdapter",
    "InMemoryStateAdapter",
    "StateError",
    "StateNotFoundError",
    "BifrostStateError",
    "create_state_adapter",
]
