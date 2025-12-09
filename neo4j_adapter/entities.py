"""Entity CRUD operations for Neo4j adapter."""

import uuid
from typing import Any, Dict, List, Optional

from .core import Neo4jStorageAdapter
from .models import Entity, _utcnow
from .query_builder import CypherQueryBuilder


class EntityOperations:
    """Entity CRUD operations mixin."""

    async def create_entity(
        self: Neo4jStorageAdapter,
        labels: List[str],
        properties: Dict[str, Any],
        entity_id: Optional[str] = None
    ) -> Entity:
        """Create new entity (node)."""
        entity_id = entity_id or str(uuid.uuid4())
        now = _utcnow().isoformat()

        label_str = ":".join(labels)
        query = f"""
            CREATE (n:{label_str} $props)
            RETURN n
        """

        props = {
            "id": entity_id,
            "created_at": now,
            "updated_at": now,
            **properties
        }

        result = await self.execute_query(query, {"props": props})

        if result.records:
            node = result.records[0]["n"]
            return Entity.from_neo4j_node(node) if hasattr(node, 'labels') else Entity(
                id=entity_id,
                labels=labels,
                properties=properties
            )

        return Entity(id=entity_id, labels=labels, properties=properties)

    async def get_entity(
        self: Neo4jStorageAdapter,
        entity_id: str
    ) -> Optional[Entity]:
        """Get entity by ID."""
        query = """
            MATCH (n {id: $entity_id})
            RETURN n
        """

        result = await self.execute_query(query, {"entity_id": entity_id})

        if result.records:
            node = result.records[0]["n"]
            return Entity.from_neo4j_node(node) if hasattr(node, 'labels') else None

        return None

    async def update_entity(
        self: Neo4jStorageAdapter,
        entity_id: str,
        properties: Dict[str, Any]
    ) -> Optional[Entity]:
        """Update entity properties."""
        now = _utcnow().isoformat()

        query = """
            MATCH (n {id: $entity_id})
            SET n += $props, n.updated_at = $updated_at
            RETURN n
        """

        result = await self.execute_query(query, {
            "entity_id": entity_id,
            "props": properties,
            "updated_at": now
        })

        if result.records:
            node = result.records[0]["n"]
            return Entity.from_neo4j_node(node) if hasattr(node, 'labels') else None

        return None

    async def delete_entity(
        self: Neo4jStorageAdapter,
        entity_id: str,
        detach: bool = True
    ) -> bool:
        """Delete entity by ID."""
        prefix = "DETACH DELETE" if detach else "DELETE"
        query = f"""
            MATCH (n {{id: $entity_id}})
            {prefix} n
            RETURN count(n) as deleted
        """

        result = await self.execute_query(query, {"entity_id": entity_id})
        return result.records[0].get("deleted", 0) > 0 if result.records else False

    async def find_entities(
        self: Neo4jStorageAdapter,
        labels: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Entity]:
        """Find entities matching criteria."""
        builder = CypherQueryBuilder()

        if labels:
            label_str = ":".join(labels)
            builder.match(f"(n:{label_str})")
        else:
            builder.match("(n)")

        if properties:
            for key, value in properties.items():
                builder.where(f"n.{key} = ${key}").param(key, value)

        builder.returns("n").skip(skip).limit(limit)
        query, params = builder.build()

        result = await self.execute_query(query, params)

        entities = []
        for record in result.records:
            node = record["n"]
            if hasattr(node, 'labels'):
                entities.append(Entity.from_neo4j_node(node))
            else:
                # Handle dict response
                entities.append(Entity(
                    id=node.get("id", ""),
                    labels=labels or [],
                    properties={k: v for k, v in node.items() if k not in ["id", "created_at", "updated_at"]}
                ))

        return entities

    async def batch_create_entities(
        self: Neo4jStorageAdapter,
        entities: List[tuple[List[str], Dict[str, Any]]]
    ) -> List[Entity]:
        """Create multiple entities in single transaction."""
        created = []

        async with self.session() as session:
            async with session.begin_transaction() as tx:
                for labels, properties in entities:
                    entity_id = str(uuid.uuid4())
                    now = _utcnow().isoformat()

                    label_str = ":".join(labels)
                    query = f"""
                        CREATE (n:{label_str} $props)
                        RETURN n
                    """

                    props = {
                        "id": entity_id,
                        "created_at": now,
                        "updated_at": now,
                        **properties
                    }

                    await tx.run(query, {"props": props})
                    created.append(Entity(
                        id=entity_id,
                        labels=labels,
                        properties=properties
                    ))

                await tx.commit()

        return created
