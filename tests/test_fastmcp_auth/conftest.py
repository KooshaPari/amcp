"""Shared fixtures and utilities for FastMCP auth tests."""

import sys
import os
from datetime import datetime, timezone

import pytest

# Add smartcp directory to path for direct module imports
smartcp_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, smartcp_dir)


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    return str(tmp_path / ".cache")
