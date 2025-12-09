"""Shared fixtures and utilities for FastMCP auth tests.

Imports common utilities from tests.fixtures module.
"""

import pytest
from datetime import datetime, timezone


def _utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    return str(tmp_path / ".cache")
