"""Shared fixtures for Neo4j storage adapter tests."""

import pytest
import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j_storage_adapter import (
    Neo4jStorageAdapter,
    Neo4jConfig,
    Neo4jConnectionState,
)


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class _MockCounters:
    """Simple counters mock that provides empty __dict__."""
    pass


def _create_result_summary(query_type: str = "r") -> MagicMock:
    """Create a mock result summary with properly configured counters.

    Uses a simple object for counters since MagicMock has issues with
    __dict__ manipulation in Python 3.13.
    """
    mock_counters = _MockCounters()
    return MagicMock(counters=mock_counters, query_type=query_type)


@pytest.fixture
def adapter():
    """Create adapter with mocked driver for testing."""
    config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="test"
    )
    adapter = Neo4jStorageAdapter(config)
    return adapter
