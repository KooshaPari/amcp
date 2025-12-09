"""Neo4j Storage Adapter - Phase 5 Implementation

Provides graph database storage for MCP entities and relationships with:
- Entity CRUD operations with property indexing
- Relationship management with typed edges
- Cypher query builder for complex traversals
- Transaction support with rollback
- Connection pooling and session management
- Vector index support for semantic search
- Batch operations for performance

Designed for knowledge graph applications with MCP tools.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

from .core import Neo4jStorageAdapter
from .entities import EntityOperations
from .models import (
    Entity,
    Neo4jConfig,
    Neo4jConnectionState,
    QueryResult,
    Relationship,
)
from .query_builder import CypherQueryBuilder
from .relationships import RelationshipOperations
from .traversal import TraversalOperations
from .vector_search import VectorSearchOperations


# Compose all operation mixins into Neo4jStorageAdapter
class Neo4jStorageAdapterFull(
    Neo4jStorageAdapter,
    EntityOperations,
    RelationshipOperations,
    TraversalOperations,
    VectorSearchOperations
):
    """Full Neo4j storage adapter with all operations."""
    pass


@asynccontextmanager
async def neo4j_adapter(config: Neo4jConfig):
    """Context manager for Neo4j adapter."""
    adapter = Neo4jStorageAdapterFull(config)
    try:
        await adapter.connect()
        yield adapter
    finally:
        await adapter.disconnect()


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
