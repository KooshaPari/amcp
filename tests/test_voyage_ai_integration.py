"""
Tests for Voyage AI Integration (Phase 6).

IMPORTANT: This file has been decomposed into the voyage_ai/ submodule.
All test classes are re-exported here for backward compatibility.

New structure:
- voyage_ai/conftest.py - Shared fixtures
- voyage_ai/test_config.py - Configuration tests
- voyage_ai/test_models.py - Model and enum tests
- voyage_ai/test_infrastructure.py - Rate limiter and cache tests
- voyage_ai/test_client.py - VoyageAIClient tests
- voyage_ai/test_service.py - VoyageEmbeddingService tests
- voyage_ai/test_neo4j_integration.py - Neo4j integration tests
- voyage_ai/test_error_handling.py - Error handling tests
- voyage_ai/test_performance.py - Performance tests
- voyage_ai/test_workflows.py - Integration workflow tests

To run all Voyage AI tests:
    pytest tests/voyage_ai/ -v

To run specific test category:
    pytest tests/voyage_ai/test_config.py -v
    pytest tests/voyage_ai/test_client.py -v
    pytest tests/voyage_ai/test_service.py -v
"""

import pytest

# Re-export all test classes for backward compatibility
from voyage_ai import (
    TestVoyageConfig,
    TestVoyageModel,
    TestInputType,
    TestEmbeddingResult,
    TestBatchEmbeddingResult,
    TestRerankResult,
    TestRateLimiter,
    TestEmbeddingCache,
    TestVoyageAIClient,
    TestVoyageEmbeddingService,
    TestVoyageNeo4jIntegration,
    TestErrorHandling,
    TestPerformance,
    TestIntegrationWorkflow,
)

__all__ = [
    "TestVoyageConfig",
    "TestVoyageModel",
    "TestInputType",
    "TestEmbeddingResult",
    "TestBatchEmbeddingResult",
    "TestRerankResult",
    "TestRateLimiter",
    "TestEmbeddingCache",
    "TestVoyageAIClient",
    "TestVoyageEmbeddingService",
    "TestVoyageNeo4jIntegration",
    "TestErrorHandling",
    "TestPerformance",
    "TestIntegrationWorkflow",
]


if __name__ == "__main__":
    pytest.main(["-v", "tests/voyage_ai/"])
