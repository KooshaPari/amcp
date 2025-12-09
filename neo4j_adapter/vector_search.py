"""Vector search operations for Neo4j adapter."""

import logging
from typing import List, Optional, Tuple

from .core import Neo4jStorageAdapter
from .models import Entity

logger = logging.getLogger(__name__)


class VectorSearchOperations:
    """Vector search operations mixin (requires Neo4j 5.x with vector index)."""

    async def create_vector_index(
        self: Neo4jStorageAdapter,
        index_name: str,
        label: str,
        property_name: str,
        dimensions: int,
        similarity_function: str = "cosine"
    ) -> bool:
        """Create vector index for similarity search."""
        query = f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON (n.{property_name})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimensions},
                    `vector.similarity_function`: '{similarity_function}'
                }}
            }}
        """

        try:
            await self.execute_query(query)
            logger.info(f"Created vector index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return False

    async def vector_search(
        self: Neo4jStorageAdapter,
        index_name: str,
        query_vector: List[float],
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[Entity, float]]:
        """Search entities by vector similarity."""
        query = f"""
            CALL db.index.vector.queryNodes($index_name, $top_k, $query_vector)
            YIELD node, score
            WHERE score >= $min_score
            RETURN node, score
            ORDER BY score DESC
        """

        result = await self.execute_query(query, {
            "index_name": index_name,
            "top_k": top_k,
            "query_vector": query_vector,
            "min_score": min_score
        })

        results = []
        for record in result.records:
            node = record["node"]
            score = record["score"]
            if hasattr(node, 'labels'):
                results.append((Entity.from_neo4j_node(node), score))

        return results
