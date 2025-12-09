"""Factory function for creating state adapters."""

from typing import Optional

from smartcp.infrastructure.state.adapter import StateAdapter
from smartcp.infrastructure.state.bifrost import BifrostStateAdapter
from smartcp.infrastructure.state.memory import InMemoryStateAdapter


def create_state_adapter(
    bifrost_client=None,
    use_memory: bool = False,
) -> StateAdapter:
    """Factory function to create a state adapter.

    Args:
        bifrost_client: Bifrost GraphQL client for persistent storage
        use_memory: If True, use in-memory adapter (for testing)

    Returns:
        Configured StateAdapter instance
    """
    if use_memory:
        return InMemoryStateAdapter()

    if bifrost_client is None:
        from smartcp.bifrost_client import BifrostClient
        bifrost_client = BifrostClient()

    return BifrostStateAdapter(bifrost_client)
