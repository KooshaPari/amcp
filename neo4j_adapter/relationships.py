"""Relationship CRUD operations for Neo4j adapter."""

import uuid
from typing import Any, Dict, List, Optional

from .core import Neo4jStorageAdapter
from .models import Relationship, _utcnow


class RelationshipOperations:
    """Relationship CRUD operations mixin."""

    async def create_relationship(
        self: Neo4jStorageAdapter,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Relationship:
        """Create relationship between entities."""
        rel_id = str(uuid.uuid4())
        now = _utcnow().isoformat()

        query = f"""
            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            CREATE (a)-[r:{rel_type} $props]->(b)
            RETURN r
        """

        props = {
            "id": rel_id,
            "created_at": now,
            **(properties or {})
        }

        await self.execute_query(query, {
            "source_id": source_id,
            "target_id": target_id,
            "props": props
        })

        return Relationship(
            id=rel_id,
            type=rel_type,
            source_id=source_id,
            target_id=target_id,
            properties=properties or {}
        )

    async def get_relationships(
        self: Neo4jStorageAdapter,
        entity_id: str,
        direction: str = "both",
        rel_type: Optional[str] = None
    ) -> List[Relationship]:
        """Get relationships for entity."""
        rel_pattern = f":{rel_type}" if rel_type else ""

        if direction == "outgoing":
            query = f"""
                MATCH (a {{id: $entity_id}})-[r{rel_pattern}]->(b)
                RETURN r, a.id as source_id, b.id as target_id, type(r) as rel_type
            """
        elif direction == "incoming":
            query = f"""
                MATCH (a {{id: $entity_id}})<-[r{rel_pattern}]-(b)
                RETURN r, b.id as source_id, a.id as target_id, type(r) as rel_type
            """
        else:
            query = f"""
                MATCH (a {{id: $entity_id}})-[r{rel_pattern}]-(b)
                RETURN r,
                       CASE WHEN startNode(r).id = $entity_id THEN startNode(r).id ELSE endNode(r).id END as source_id,
                       CASE WHEN startNode(r).id = $entity_id THEN endNode(r).id ELSE startNode(r).id END as target_id,
                       type(r) as rel_type
            """

        result = await self.execute_query(query, {"entity_id": entity_id})

        relationships = []
        for record in result.records:
            rel_props = dict(record["r"]) if hasattr(record["r"], '__iter__') else {}
            relationships.append(Relationship(
                id=rel_props.get("id", str(uuid.uuid4())),
                type=record["rel_type"],
                source_id=record["source_id"],
                target_id=record["target_id"],
                properties={k: v for k, v in rel_props.items() if k not in ["id", "created_at"]}
            ))

        return relationships

    async def delete_relationship(self: Neo4jStorageAdapter, rel_id: str) -> bool:
        """Delete relationship by ID."""
        query = """
            MATCH ()-[r {id: $rel_id}]-()
            DELETE r
            RETURN count(r) as deleted
        """

        result = await self.execute_query(query, {"rel_id": rel_id})
        return result.records[0].get("deleted", 0) > 0 if result.records else False

    async def batch_create_relationships(
        self: Neo4jStorageAdapter,
        relationships: List[tuple[str, str, str, Optional[Dict[str, Any]]]]
    ) -> List[Relationship]:
        """Create multiple relationships in single transaction."""
        created = []

        async with self.session() as session:
            async with session.begin_transaction() as tx:
                for source_id, target_id, rel_type, properties in relationships:
                    rel_id = str(uuid.uuid4())
                    now = _utcnow().isoformat()

                    query = f"""
                        MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                        CREATE (a)-[r:{rel_type} $props]->(b)
                        RETURN r
                    """

                    props = {
                        "id": rel_id,
                        "created_at": now,
                        **(properties or {})
                    }

                    await tx.run(query, {
                        "source_id": source_id,
                        "target_id": target_id,
                        "props": props
                    })

                    created.append(Relationship(
                        id=rel_id,
                        type=rel_type,
                        source_id=source_id,
                        target_id=target_id,
                        properties=properties or {}
                    ))

                await tx.commit()

        return created
