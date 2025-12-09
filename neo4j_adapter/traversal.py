"""Graph traversal operations for Neo4j adapter."""

from typing import Any, Dict, List, Optional

from .core import Neo4jStorageAdapter
from .models import Entity


class TraversalOperations:
    """Graph traversal operations mixin."""

    async def get_neighbors(
        self: Neo4jStorageAdapter,
        entity_id: str,
        depth: int = 1,
        rel_types: Optional[List[str]] = None
    ) -> List[Entity]:
        """Get neighboring entities up to specified depth."""
        rel_pattern = "|".join(rel_types) if rel_types else ""
        rel_filter = f":{rel_pattern}" if rel_pattern else ""

        query = f"""
            MATCH (start {{id: $entity_id}})-[{rel_filter}*1..{depth}]-(neighbor)
            WHERE neighbor.id <> $entity_id
            RETURN DISTINCT neighbor
        """

        result = await self.execute_query(query, {"entity_id": entity_id})

        entities = []
        for record in result.records:
            node = record["neighbor"]
            if hasattr(node, 'labels'):
                entities.append(Entity.from_neo4j_node(node))

        return entities

    async def find_path(
        self: Neo4jStorageAdapter,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
        rel_types: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find shortest path between entities."""
        rel_pattern = "|".join(rel_types) if rel_types else ""
        rel_filter = f":{rel_pattern}" if rel_pattern else ""

        query = f"""
            MATCH path = shortestPath(
                (start {{id: $start_id}})-[{rel_filter}*..{max_depth}]-(end {{id: $end_id}})
            )
            RETURN nodes(path) as nodes, relationships(path) as rels
        """

        result = await self.execute_query(query, {
            "start_id": start_id,
            "end_id": end_id
        })

        if result.records:
            record = result.records[0]
            return {
                "nodes": [dict(n) for n in record["nodes"]],
                "relationships": [dict(r) for r in record["rels"]]
            }

        return None
