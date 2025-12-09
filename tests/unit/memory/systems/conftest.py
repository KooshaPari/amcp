"""
Shared fixtures for memory system tests.

Provides common fixtures for episodic, semantic, and working memory tests.
"""

import pytest
from optimization.memory.episodic import (
    EpisodicMemory,
    EpisodicConfig,
)
from optimization.memory.semantic import (
    SemanticMemory,
    SemanticConfig,
)
from optimization.memory.working import (
    WorkingMemory,
    WorkingConfig,
)


@pytest.fixture
def episodic_memory():
    """Create episodic memory instance."""
    config = EpisodicConfig(max_entries=100)
    return EpisodicMemory(config)


@pytest.fixture
def semantic_memory():
    """Create semantic memory instance."""
    config = SemanticConfig(max_entries=1000)
    return SemanticMemory(config)


@pytest.fixture
def working_memory():
    """Create working memory instance."""
    config = WorkingConfig(max_contexts=10)
    return WorkingMemory(config)
