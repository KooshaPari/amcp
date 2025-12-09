"""Shared fixtures for Voyage AI tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add bifrost-extensions to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "../bifrost-extensions"
    )
)

from services.embeddings import (
    VoyageAIClient,
    VoyageEmbeddingService,
    VoyageNeo4jIntegration,
    VoyageConfig,
)


@pytest.fixture
def voyage_config():
    """Create Voyage AI configuration."""
    return VoyageConfig(api_key="test-api-key")


@pytest.fixture
def voyage_client(voyage_config):
    """Create Voyage AI client."""
    return VoyageAIClient(voyage_config)


@pytest.fixture
def embedding_service(voyage_client):
    """Create embedding service."""
    return VoyageEmbeddingService(voyage_client)


@pytest.fixture
def neo4j_integration(voyage_client):
    """Create Neo4j integration instance."""
    mock_neo4j = MagicMock()
    return VoyageNeo4jIntegration(voyage_client, mock_neo4j)
