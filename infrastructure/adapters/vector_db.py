"""
Vector & Graph Database Integration (Proposal 18)

Provides:
- Vector DB (Qdrant/Weaviate)
- Graph DB (Neo4j)
- Hybrid search
- Relationship management

This module has been refactored to eliminate module-level mutable state.
All database instances are now passed through dependency injection via context.
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """Vector record."""

    id: str
    vector: List[float]
    metadata: Dict[str, Any]


@dataclass
class GraphNode:
    """Graph node."""

    id: str
    label: str
    properties: Dict[str, Any]


@dataclass
class GraphRelationship:
    """Graph relationship."""

    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any]


class VectorDatabase:
    """Vector database integration."""

    def __init__(self, provider: str = "qdrant") -> None:
        self.provider = provider
        self.vectors: Dict[str, VectorRecord] = {}

    async def insert_vector(self, record: VectorRecord) -> bool:
        """Insert vector."""
        try:
            logger.info(f"Inserting vector: {record.id}")

            self.vectors[record.id] = record

            logger.info(f"Inserted vector: {record.id}")
            return True

        except Exception as e:
            logger.error(f"Error inserting vector: {e}")
            return False

    async def search_vectors(
        self, query_vector: List[float], top_k: int = 10
    ) -> List[VectorRecord]:
        """Search vectors."""
        try:
            logger.info(f"Searching vectors (top_k={top_k})")

            # Mock similarity search
            results = list(self.vectors.values())[:top_k]

            logger.info(f"Found {len(results)} vectors")
            return results

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []

    async def delete_vector(self, vector_id: str) -> bool:
        """Delete vector."""
        try:
            if vector_id in self.vectors:
                del self.vectors[vector_id]
                logger.info(f"Deleted vector: {vector_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting vector: {e}")
            return False


class GraphDatabase:
    """Graph database integration."""

    def __init__(self, provider: str = "neo4j") -> None:
        self.provider = provider
        self.nodes: Dict[str, GraphNode] = {}
        self.relationships: List[GraphRelationship] = []

    async def create_node(self, node: GraphNode) -> bool:
        """Create graph node."""
        try:
            logger.info(f"Creating node: {node.id}")

            self.nodes[node.id] = node

            logger.info(f"Created node: {node.id}")
            return True

        except Exception as e:
            logger.error(f"Error creating node: {e}")
            return False

    async def create_relationship(self, rel: GraphRelationship) -> bool:
        """Create relationship."""
        try:
            logger.info(f"Creating relationship: {rel.source_id} -> {rel.target_id}")

            if rel.source_id not in self.nodes or rel.target_id not in self.nodes:
                logger.error("Source or target node not found")
                return False

            self.relationships.append(rel)

            logger.info("Relationship created")
            return True

        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return False

    async def query_graph(self, query: str) -> List[Dict[str, Any]]:
        """Query graph."""
        try:
            logger.info(f"Querying graph: {query}")

            # Mock graph query
            results = [
                {
                    "node": node,
                    "relationships": len(
                        [r for r in self.relationships if r.source_id == node.id]
                    ),
                }
                for node in self.nodes.values()
            ]

            logger.info(f"Query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error querying graph: {e}")
            return []

    async def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighboring nodes."""
        try:
            neighbors = [
                r.target_id
                for r in self.relationships
                if r.source_id == node_id
            ]

            return neighbors

        except Exception as e:
            logger.error(f"Error getting neighbors: {e}")
            return []


class HybridSearch:
    """Hybrid vector + graph search."""

    def __init__(
        self,
        vector_db: Optional[VectorDatabase] = None,
        graph_db: Optional[GraphDatabase] = None,
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            vector_db: Vector database instance (created if not provided).
            graph_db: Graph database instance (created if not provided).
        """
        self.vector_db = vector_db or VectorDatabase()
        self.graph_db = graph_db or GraphDatabase()

    async def hybrid_search(
        self, query_vector: List[float], query_graph: str
    ) -> Dict[str, Any]:
        """Perform hybrid search."""
        try:
            logger.info("Performing hybrid search")

            # Vector search
            vector_results = await self.vector_db.search_vectors(query_vector)

            # Graph search
            graph_results = await self.graph_db.query_graph(query_graph)

            return {
                "vector_results": vector_results,
                "graph_results": graph_results,
            }

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return {}


@dataclass
class VectorGraphContext:
    """Context object for passing database instances through call stack.

    This replaces module-level global state with explicit dependency injection.
    Each request or operation receives its own context with database instances.
    """

    vector_db: VectorDatabase = field(default_factory=VectorDatabase)
    graph_db: GraphDatabase = field(default_factory=GraphDatabase)
    hybrid_search: Optional[HybridSearch] = None

    def __post_init__(self) -> None:
        """Initialize hybrid search with injected databases."""
        if self.hybrid_search is None:
            self.hybrid_search = HybridSearch(
                vector_db=self.vector_db, graph_db=self.graph_db
            )


def create_vector_graph_context(
    vector_db: Optional[VectorDatabase] = None,
    graph_db: Optional[GraphDatabase] = None,
) -> VectorGraphContext:
    """Create a new vector/graph database context.

    Use this factory function to create contexts for dependency injection.

    Args:
        vector_db: Custom VectorDatabase instance (optional).
        graph_db: Custom GraphDatabase instance (optional).

    Returns:
        VectorGraphContext with initialized database instances.

    Example:
        # In your service or handler
        context = create_vector_graph_context()
        await context.vector_db.insert_vector(record)

        # Or pass to functions
        async def process_data(context: VectorGraphContext) -> None:
            results = await context.vector_db.search_vectors(query)
    """
    return VectorGraphContext(
        vector_db=vector_db or VectorDatabase(),
        graph_db=graph_db or GraphDatabase(),
    )

