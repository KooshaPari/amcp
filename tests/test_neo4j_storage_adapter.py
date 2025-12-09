"""Tests for Neo4j Storage Adapter (Phase 5).

BACKWARD COMPATIBILITY WRAPPER: This file re-exports all tests from
the decomposed tests/neo4j_storage/ submodule.

Original file was 921 lines and has been decomposed into:
- test_config.py: Configuration tests
- test_models.py: Entity and Relationship model tests
- test_query_builder.py: Cypher query builder tests
- test_crud.py: Core CRUD operations
- test_vector_index.py: Vector index operations
- test_batch.py: Batch operations
- test_traversal.py: Graph traversal and query operations
"""

# Re-export all test classes for backward compatibility
from tests.neo4j_storage import (
    TestNeo4jConfig,
    TestEntity,
    TestRelationship,
    TestCypherQueryBuilder,
    TestNeo4jStorageAdapter,
    TestVectorIndex,
    TestBatchOperations,
    TestQueryResult,
    TestConnectionState,
    TestFindEntities,
    TestGraphTraversal,
)

__all__ = [
    "TestNeo4jConfig",
    "TestEntity",
    "TestRelationship",
    "TestCypherQueryBuilder",
    "TestNeo4jStorageAdapter",
    "TestVectorIndex",
    "TestBatchOperations",
    "TestQueryResult",
    "TestConnectionState",
    "TestFindEntities",
    "TestGraphTraversal",
]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
