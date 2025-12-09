"""
Tests for Voyage AI Integration (Phase 6).

NOTE: VoyageAI integration module is not yet implemented.
These tests are skipped until the module is available.

The tests expect the following classes that do not exist:
- VoyageAIClient
- VoyageEmbeddingService
- VoyageNeo4jIntegration
- VoyageConfig
- TestVoyageConfig (test class)
- etc.

When VoyageAI integration is implemented, update this file to:
1. Import from the correct module
2. Remove the skip marker
"""

import pytest

# Skip entire module - VoyageAI classes not implemented
pytestmark = pytest.mark.skip(
    reason="VoyageAI integration module not implemented - "
    "VoyageAIClient, VoyageEmbeddingService, etc. do not exist in bifrost_ml.services.embeddings"
)


class TestVoyageAIIntegration:
    """Placeholder for VoyageAI integration tests."""

    def test_placeholder(self):
        """Placeholder test - VoyageAI not implemented."""
        pass
