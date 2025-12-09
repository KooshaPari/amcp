"""Shared fixtures for Voyage AI tests.

NOTE: VoyageAI integration module is not yet implemented.
These tests are skipped until the module is available.
"""

import pytest

# Skip all tests in this module - VoyageAI classes not implemented
pytestmark = pytest.mark.skip(
    reason="VoyageAI integration module not implemented - "
    "VoyageAIClient, VoyageEmbeddingService, etc. do not exist in bifrost_ml.services.embeddings"
)


@pytest.fixture
def voyage_config():
    """Create Voyage AI configuration."""
    return None


@pytest.fixture
def voyage_client(voyage_config):
    """Create Voyage AI client."""
    return None


@pytest.fixture
def embedding_service(voyage_client):
    """Create embedding service."""
    return None


@pytest.fixture
def neo4j_integration(voyage_client):
    """Create Neo4j integration instance."""
    return None
