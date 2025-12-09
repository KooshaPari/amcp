import pytest
from unittest.mock import AsyncMock

from smartcp.infrastructure.state.factory import create_state_adapter
from smartcp.infrastructure.state.bifrost import BifrostStateAdapter
from smartcp.infrastructure.state.memory import InMemoryStateAdapter


def test_create_state_adapter_defaults_to_bifrost():
    adapter = create_state_adapter()
    assert isinstance(adapter, BifrostStateAdapter)


def test_create_state_adapter_memory_flag():
    adapter = create_state_adapter(use_memory=True)
    assert isinstance(adapter, InMemoryStateAdapter)
