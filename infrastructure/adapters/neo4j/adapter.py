"""
Neo4j Storage Adapter - Backward compatibility re-export.

This module re-exports from neo4j_adapter submodule for backward compatibility.
For new code, import directly from neo4j_adapter.

Example:
    from neo4j_adapter import Neo4jStorageAdapter, Neo4jConfig, neo4j_adapter
"""

# Re-export all public APIs for backward compatibility
from neo4j_adapter import (
    Entity,
    EntityOperations,
    Neo4jConfig,
    Neo4jConnectionState,
    Neo4jStorageAdapter,
    Neo4jStorageAdapterFull,
    QueryResult,
    Relationship,
    RelationshipOperations,
    TraversalOperations,
    VectorSearchOperations,
    CypherQueryBuilder,
    neo4j_adapter,
)

__all__ = [
    "Neo4jStorageAdapter",
    "Neo4jStorageAdapterFull",
    "Neo4jConfig",
    "Neo4jConnectionState",
    "Entity",
    "Relationship",
    "QueryResult",
    "CypherQueryBuilder",
    "EntityOperations",
    "RelationshipOperations",
    "TraversalOperations",
    "VectorSearchOperations",
    "neo4j_adapter",
]
