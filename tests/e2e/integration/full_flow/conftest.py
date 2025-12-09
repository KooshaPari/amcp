"""
Shared fixtures for full flow E2E tests.

Provides common test utilities and fixtures used across
request flow, response flow, and error flow tests.
"""

import pytest


# All fixtures are inherited from parent conftest.py in tests/e2e/
# This file serves as a marker for the full_flow test submodule
# and can be extended with full_flow-specific fixtures if needed

@pytest.fixture
def workflow_timeout():
    """Default timeout for workflow tests."""
    return 30.0
