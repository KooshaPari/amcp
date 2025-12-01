"""
Neo4j Storage Adapter - Phase 5 Implementation

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

import asyncio
import logging
from datetime import datetime, timezone
from typing import (
    Any, Dict, List, Optional, TypeVar, Generic,
    Tuple, AsyncIterator, Union
)
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import asynccontextmanager
import json
import uuid

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class Neo4jConnectionState(str, Enum):
    """Connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    max_transaction_retry_time: float = 30.0
    encrypted: bool = True
    trust: str = "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES"


@dataclass
class Entity:
    """Graph entity (node) representation."""
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_neo4j_node(cls, node: Any) -> "Entity":
        """Create from Neo4j node object."""
        props = dict(node)
        return cls(
            id=props.pop("id", str(node.id)),
            labels=list(node.labels),
            properties=props,
            created_at=datetime.fromisoformat(props.pop("created_at", _utcnow().isoformat())),
            updated_at=datetime.fromisoformat(props.pop("updated_at", _utcnow().isoformat()))
        )


@dataclass
class Relationship:
    """Graph relationship (edge) representation."""
    id: str
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class QueryResult:
    """Result from Cypher query execution."""
    records: List[Dict[str, Any]]
    summary: Dict[str, Any]
    keys: List[str]
    execution_time_ms: float


class CypherQueryBuilder:
    """Fluent Cypher query builder."""

    def __init__(self):
        self._match_clauses: List[str] = []
        self._where_clauses: List[str] = []
        self._create_clauses: List[str] = []
        self._merge_clauses: List[str] = []
        self._set_clauses: List[str] = []
        self._delete_clauses: List[str] = []
        self._return_clause: Optional[str] = None
        self._order_by: Optional[str] = None
        self._skip: Optional[int] = None
        self._limit: Optional[int] = None
        self._params: Dict[str, Any] = {}

    def match(self, pattern: str) -> "CypherQueryBuilder":
        """Add MATCH clause."""
        self._match_clauses.append(f"MATCH {pattern}")
        return self

    def optional_match(self, pattern: str) -> "CypherQueryBuilder":
        """Add OPTIONAL MATCH clause."""
        self._match_clauses.append(f"OPTIONAL MATCH {pattern}")
        return self

    def where(self, condition: str) -> "CypherQueryBuilder":
        """Add WHERE condition."""
        self._where_clauses.append(condition)
        return self

    def where_id(self, var: str, entity_id: str) -> "CypherQueryBuilder":
        """Add WHERE clause for entity ID."""
        param_name = f"{var}_id"
        self._where_clauses.append(f"{var}.id = ${param_name}")
        self._params[param_name] = entity_id
        return self

    def create(self, pattern: str) -> "CypherQueryBuilder":
        """Add CREATE clause."""
        self._create_clauses.append(f"CREATE {pattern}")
        return self

    def merge(self, pattern: str) -> "CypherQueryBuilder":
        """Add MERGE clause."""
        self._merge_clauses.append(f"MERGE {pattern}")
        return self

    def set(self, assignment: str) -> "CypherQueryBuilder":
        """Add SET clause."""
        self._set_clauses.append(assignment)
        return self

    def delete(self, var: str, detach: bool = False) -> "CypherQueryBuilder":
        """Add DELETE clause."""
        prefix = "DETACH DELETE" if detach else "DELETE"
        self._delete_clauses.append(f"{prefix} {var}")
        return self

    def returns(self, expression: str) -> "CypherQueryBuilder":
        """Add RETURN clause."""
        self._return_clause = f"RETURN {expression}"
        return self

    def order_by(self, expression: str, desc: bool = False) -> "CypherQueryBuilder":
        """Add ORDER BY clause."""
        direction = " DESC" if desc else ""
        self._order_by = f"ORDER BY {expression}{direction}"
        return self

    def skip(self, n: int) -> "CypherQueryBuilder":
        """Add SKIP clause."""
        self._skip = n
        return self

    def limit(self, n: int) -> "CypherQueryBuilder":
        """Add LIMIT clause."""
        self._limit = n
        return self

    def param(self, name: str, value: Any) -> "CypherQueryBuilder":
        """Add query parameter."""
        self._params[name] = value
        return self

    def params(self, **kwargs: Any) -> "CypherQueryBuilder":
        """Add multiple query parameters."""
        self._params.update(kwargs)
        return self

    def build(self) -> Tuple[str, Dict[str, Any]]:
        """Build Cypher query string and parameters."""
        parts = []

        parts.extend(self._match_clauses)

        if self._where_clauses:
            parts.append("WHERE " + " AND ".join(self._where_clauses))

        parts.extend(self._create_clauses)
        parts.extend(self._merge_clauses)

        if self._set_clauses:
            parts.append("SET " + ", ".join(self._set_clauses))

        parts.extend(self._delete_clauses)

        if self._return_clause:
            parts.append(self._return_clause)

        if self._order_by:
            parts.append(self._order_by)

        if self._skip is not None:
            parts.append(f"SKIP {self._skip}")

        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")

        query = "\n".join(parts)
        return query, self._params


class Neo4jStorageAdapter:
    """
    Neo4j storage adapter for MCP entities and relationships.

    Provides high-level operations for graph database storage.
    """

    def __init__(self, config: Neo4jConfig):
        self.config = config
        self._driver: Optional[Any] = None
        self._state = Neo4jConnectionState.DISCONNECTED

    @property
    def state(self) -> Neo4jConnectionState:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._state == Neo4jConnectionState.CONNECTED

    async def connect(self) -> bool:
        """
        Establish connection to Neo4j database.

        Returns True if connection successful.
        """
        if self._state == Neo4jConnectionState.CONNECTED:
            return True

        self._state = Neo4jConnectionState.CONNECTING
        logger.info(f"Connecting to Neo4j at {self.config.uri}")

        try:
            # Import neo4j lazily
            try:
                from neo4j import AsyncGraphDatabase
            except ImportError:
                logger.error("neo4j package not installed")
                self._state = Neo4jConnectionState.DISCONNECTED
                return False

            self._driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_timeout=self.config.connection_timeout,
                max_transaction_retry_time=self.config.max_transaction_retry_time
            )

            # Verify connectivity
            await self._driver.verify_connectivity()

            self._state = Neo4jConnectionState.CONNECTED
            logger.info("Connected to Neo4j")
            return True

        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            self._state = Neo4jConnectionState.ERROR
            return False

    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
        self._state = Neo4jConnectionState.DISCONNECTED
        logger.info("Disconnected from Neo4j")

    @asynccontextmanager
    async def session(self):
        """Get database session context manager."""
        if not self._driver:
            raise ConnectionError("Not connected to Neo4j")

        async with self._driver.session(database=self.config.database) as session:
            yield session

    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Execute Cypher query."""
        import time
        start = time.perf_counter()

        async with self.session() as session:
            result = await session.run(query, params or {})
            records = [dict(record) for record in await result.data()]
            summary = await result.consume()

        execution_time = (time.perf_counter() - start) * 1000

        return QueryResult(
            records=records,
            summary={
                "counters": dict(summary.counters.__dict__) if hasattr(summary, 'counters') else {},
                "query_type": summary.query_type if hasattr(summary, 'query_type') else None
            },
            keys=list(records[0].keys()) if records else [],
            execution_time_ms=execution_time
        )

    # Entity operations

    async def create_entity(
        self,
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

    async def get_entity(self, entity_id: str) -> Optional[Entity]:
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
        self,
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

    async def delete_entity(self, entity_id: str, detach: bool = True) -> bool:
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
        self,
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

    # Relationship operations

    async def create_relationship(
        self,
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
        self,
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

    async def delete_relationship(self, rel_id: str) -> bool:
        """Delete relationship by ID."""
        query = """
            MATCH ()-[r {id: $rel_id}]-()
            DELETE r
            RETURN count(r) as deleted
        """

        result = await self.execute_query(query, {"rel_id": rel_id})
        return result.records[0].get("deleted", 0) > 0 if result.records else False

    # Graph traversal operations

    async def get_neighbors(
        self,
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
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
        rel_types: Optional[List[str]] = None
    ) -> Optional[List[Dict[str, Any]]]:
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

    # Vector search operations (requires Neo4j 5.x with vector index)

    async def create_vector_index(
        self,
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
        self,
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

    # Batch operations

    async def batch_create_entities(
        self,
        entities: List[Tuple[List[str], Dict[str, Any]]]
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

    async def batch_create_relationships(
        self,
        relationships: List[Tuple[str, str, str, Optional[Dict[str, Any]]]]
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


@asynccontextmanager
async def neo4j_adapter(config: Neo4jConfig):
    """Context manager for Neo4j adapter."""
    adapter = Neo4jStorageAdapter(config)
    try:
        await adapter.connect()
        yield adapter
    finally:
        await adapter.disconnect()
