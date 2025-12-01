"""
Tests for Neo4j Storage Adapter (Phase 5).

Tests graph database operations including entity CRUD, relationship management,
Cypher query builder, vector indexes, and batch operations.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, List, Dict, Any
import uuid


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j_storage_adapter import (
    Neo4jStorageAdapter,
    CypherQueryBuilder,
    Entity,
    Relationship,
    Neo4jConfig,
    QueryResult,
    BatchOperation,
    VectorIndex,
)


# ============================================================================
# Neo4jConfig Tests
# ============================================================================


class TestNeo4jConfig:
    """Test Neo4j configuration."""

    def test_default_config(self):
        """Test default Neo4j config values."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        assert config.uri == "bolt://localhost:7687"
        assert config.user == "neo4j"
        assert config.max_connection_pool_size == 50
        assert config.connection_timeout == 30.0

    def test_custom_config(self):
        """Test custom Neo4j config values."""
        config = Neo4jConfig(
            uri="bolt://db.example.com:7687",
            user="admin",
            password="secret",
            database="mydb",
            max_connection_pool_size=100,
            connection_timeout=60.0
        )
        assert config.database == "mydb"
        assert config.max_connection_pool_size == 100
        assert config.connection_timeout == 60.0


# ============================================================================
# Entity Tests
# ============================================================================


class TestEntity:
    """Test Entity model."""

    def test_entity_creation(self):
        """Test entity creation with required fields."""
        entity = Entity(
            id="entity-1",
            labels=["Person"],
            properties={"name": "John", "age": 30}
        )
        assert entity.id == "entity-1"
        assert "Person" in entity.labels
        assert entity.properties["name"] == "John"

    def test_entity_with_multiple_labels(self):
        """Test entity with multiple labels."""
        entity = Entity(
            id="entity-2",
            labels=["Person", "Employee", "Manager"],
            properties={"name": "Jane"}
        )
        assert len(entity.labels) == 3
        assert "Employee" in entity.labels

    def test_entity_to_dict(self):
        """Test entity serialization."""
        entity = Entity(
            id="entity-3",
            labels=["Document"],
            properties={"title": "Report", "pages": 10},
            created_at=_utcnow()
        )
        data = entity.to_dict()

        assert data["id"] == "entity-3"
        assert data["labels"] == ["Document"]
        assert data["properties"]["title"] == "Report"
        assert "created_at" in data

    def test_entity_from_dict(self):
        """Test entity deserialization."""
        data = {
            "id": "entity-4",
            "labels": ["Task"],
            "properties": {"status": "pending"},
            "created_at": _utcnow().isoformat()
        }
        entity = Entity.from_dict(data)

        assert entity.id == "entity-4"
        assert entity.labels == ["Task"]
        assert entity.properties["status"] == "pending"


# ============================================================================
# Relationship Tests
# ============================================================================


class TestRelationship:
    """Test Relationship model."""

    def test_relationship_creation(self):
        """Test relationship creation."""
        rel = Relationship(
            id="rel-1",
            source_id="entity-1",
            target_id="entity-2",
            type="KNOWS",
            properties={"since": 2020}
        )
        assert rel.id == "rel-1"
        assert rel.source_id == "entity-1"
        assert rel.target_id == "entity-2"
        assert rel.type == "KNOWS"

    def test_relationship_to_dict(self):
        """Test relationship serialization."""
        rel = Relationship(
            id="rel-2",
            source_id="a",
            target_id="b",
            type="RELATED_TO",
            properties={"weight": 0.8}
        )
        data = rel.to_dict()

        assert data["source_id"] == "a"
        assert data["target_id"] == "b"
        assert data["type"] == "RELATED_TO"

    def test_relationship_from_dict(self):
        """Test relationship deserialization."""
        data = {
            "id": "rel-3",
            "source_id": "x",
            "target_id": "y",
            "type": "DEPENDS_ON",
            "properties": {}
        }
        rel = Relationship.from_dict(data)

        assert rel.type == "DEPENDS_ON"
        assert rel.source_id == "x"


# ============================================================================
# CypherQueryBuilder Tests
# ============================================================================


class TestCypherQueryBuilder:
    """Test Cypher query builder."""

    def test_match_query(self):
        """Test basic MATCH query building."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["Person"])
            .return_("n")
            .build()
        )

        assert "MATCH" in query
        assert "(n:Person)" in query
        assert "RETURN n" in query

    def test_match_with_properties(self):
        """Test MATCH with property filters."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["Person"])
            .where("n.name", "=", "John")
            .return_("n")
            .build()
        )

        assert "WHERE" in query
        assert "n.name" in query

    def test_create_query(self):
        """Test CREATE query building."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .create("n", labels=["Document"], properties={"title": "Report"})
            .return_("n")
            .build()
        )

        assert "CREATE" in query
        assert "(n:Document" in query

    def test_create_relationship_query(self):
        """Test relationship creation query."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("a", labels=["Person"])
            .where("a.id", "=", "person-1")
            .match("b", labels=["Person"])
            .where("b.id", "=", "person-2")
            .create_relationship("a", "b", "KNOWS", {"since": 2020})
            .return_("a", "b")
            .build()
        )

        assert "KNOWS" in query
        assert "MATCH" in query

    def test_optional_match(self):
        """Test OPTIONAL MATCH query."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["Person"])
            .optional_match("n", "r", "m")
            .return_("n", "r", "m")
            .build()
        )

        assert "OPTIONAL MATCH" in query

    def test_order_by(self):
        """Test ORDER BY clause."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["Task"])
            .return_("n")
            .order_by("n.created_at", descending=True)
            .build()
        )

        assert "ORDER BY" in query
        assert "DESC" in query

    def test_limit_and_skip(self):
        """Test LIMIT and SKIP clauses."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["Entity"])
            .return_("n")
            .skip(10)
            .limit(20)
            .build()
        )

        assert "SKIP" in query
        assert "LIMIT" in query

    def test_with_clause(self):
        """Test WITH clause for query chaining."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["Person"])
            .with_("n", "count(*) AS total")
            .return_("n", "total")
            .build()
        )

        assert "WITH" in query
        assert "total" in query

    def test_delete_query(self):
        """Test DELETE query building."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["TempNode"])
            .where("n.id", "=", "temp-1")
            .delete("n")
            .build()
        )

        assert "DELETE" in query

    def test_set_properties(self):
        """Test SET clause for property updates."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("n", labels=["Task"])
            .where("n.id", "=", "task-1")
            .set_properties("n", {"status": "completed", "updated_at": _utcnow()})
            .return_("n")
            .build()
        )

        assert "SET" in query


# ============================================================================
# Neo4jStorageAdapter Tests
# ============================================================================


class TestNeo4jStorageAdapter:
    """Test Neo4j storage adapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked driver."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test"
        )
        adapter = Neo4jStorageAdapter(config)
        adapter._driver = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_create_entity(self, adapter):
        """Test entity creation."""
        # Mock session and transaction
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_result = MagicMock()
        mock_record = MagicMock()

        mock_record.__getitem__ = lambda self, key: {
            "id": "new-entity",
            "labels": ["Person"],
            "properties": {"name": "Test"}
        }.get(key)

        mock_result.single.return_value = mock_record
        mock_tx.run.return_value = mock_result

        adapter._driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        adapter._driver.session.return_value.__exit__ = MagicMock(return_value=None)

        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Entity(
                id="new-entity",
                labels=["Person"],
                properties={"name": "Test"}
            )

            entity = await adapter.create_entity(
                labels=["Person"],
                properties={"name": "Test"}
            )

            assert entity.id == "new-entity"
            assert "Person" in entity.labels

    @pytest.mark.asyncio
    async def test_get_entity(self, adapter):
        """Test entity retrieval."""
        with patch.object(adapter, '_execute_read', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Entity(
                id="entity-1",
                labels=["Document"],
                properties={"title": "Report"}
            )

            entity = await adapter.get_entity("entity-1")

            assert entity is not None
            assert entity.id == "entity-1"
            assert entity.properties["title"] == "Report"

    @pytest.mark.asyncio
    async def test_get_entity_not_found(self, adapter):
        """Test entity not found returns None."""
        with patch.object(adapter, '_execute_read', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            entity = await adapter.get_entity("nonexistent")

            assert entity is None

    @pytest.mark.asyncio
    async def test_update_entity(self, adapter):
        """Test entity update."""
        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Entity(
                id="entity-1",
                labels=["Task"],
                properties={"status": "completed"}
            )

            entity = await adapter.update_entity(
                entity_id="entity-1",
                properties={"status": "completed"}
            )

            assert entity.properties["status"] == "completed"

    @pytest.mark.asyncio
    async def test_delete_entity(self, adapter):
        """Test entity deletion."""
        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = True

            result = await adapter.delete_entity("entity-1")

            assert result is True

    @pytest.mark.asyncio
    async def test_create_relationship(self, adapter):
        """Test relationship creation."""
        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Relationship(
                id="rel-1",
                source_id="entity-1",
                target_id="entity-2",
                type="RELATED_TO",
                properties={}
            )

            rel = await adapter.create_relationship(
                source_id="entity-1",
                target_id="entity-2",
                rel_type="RELATED_TO"
            )

            assert rel.source_id == "entity-1"
            assert rel.target_id == "entity-2"
            assert rel.type == "RELATED_TO"

    @pytest.mark.asyncio
    async def test_get_relationships(self, adapter):
        """Test getting entity relationships."""
        with patch.object(adapter, '_execute_read', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [
                Relationship(
                    id="rel-1",
                    source_id="entity-1",
                    target_id="entity-2",
                    type="KNOWS",
                    properties={}
                ),
                Relationship(
                    id="rel-2",
                    source_id="entity-1",
                    target_id="entity-3",
                    type="WORKS_WITH",
                    properties={}
                )
            ]

            relationships = await adapter.get_relationships("entity-1")

            assert len(relationships) == 2
            assert relationships[0].type == "KNOWS"

    @pytest.mark.asyncio
    async def test_delete_relationship(self, adapter):
        """Test relationship deletion."""
        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = True

            result = await adapter.delete_relationship("rel-1")

            assert result is True


# ============================================================================
# Vector Index Tests
# ============================================================================


class TestVectorIndex:
    """Test vector index operations."""

    def test_vector_index_config(self):
        """Test vector index configuration."""
        index = VectorIndex(
            name="entity_embeddings",
            label="Entity",
            property="embedding",
            dimensions=1536,
            similarity_function="cosine"
        )

        assert index.name == "entity_embeddings"
        assert index.dimensions == 1536
        assert index.similarity_function == "cosine"

    @pytest.fixture
    def adapter(self):
        """Create adapter for vector tests."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test"
        )
        adapter = Neo4jStorageAdapter(config)
        adapter._driver = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_create_vector_index(self, adapter):
        """Test vector index creation."""
        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = True

            index_config = VectorIndex(
                name="test_index",
                label="Document",
                property="embedding",
                dimensions=768
            )

            result = await adapter.create_vector_index(index_config)

            assert result is True

    @pytest.mark.asyncio
    async def test_vector_search(self, adapter):
        """Test vector similarity search."""
        with patch.object(adapter, '_execute_read', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [
                (Entity(id="doc-1", labels=["Document"], properties={"title": "Report"}), 0.95),
                (Entity(id="doc-2", labels=["Document"], properties={"title": "Summary"}), 0.85),
            ]

            query_vector = [0.1] * 768
            results = await adapter.vector_search(
                index_name="test_index",
                query_vector=query_vector,
                limit=10
            )

            assert len(results) == 2
            assert results[0][1] == 0.95  # Similarity score


# ============================================================================
# Batch Operations Tests
# ============================================================================


class TestBatchOperations:
    """Test batch operations."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for batch tests."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test"
        )
        adapter = Neo4jStorageAdapter(config)
        adapter._driver = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_batch_create_entities(self, adapter):
        """Test batch entity creation."""
        entities_data = [
            {"labels": ["Person"], "properties": {"name": "Alice"}},
            {"labels": ["Person"], "properties": {"name": "Bob"}},
            {"labels": ["Person"], "properties": {"name": "Charlie"}},
        ]

        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [
                Entity(id=f"entity-{i}", labels=e["labels"], properties=e["properties"])
                for i, e in enumerate(entities_data)
            ]

            entities = await adapter.batch_create_entities(entities_data)

            assert len(entities) == 3

    @pytest.mark.asyncio
    async def test_batch_create_relationships(self, adapter):
        """Test batch relationship creation."""
        relationships_data = [
            {"source_id": "a", "target_id": "b", "type": "KNOWS"},
            {"source_id": "b", "target_id": "c", "type": "KNOWS"},
        ]

        with patch.object(adapter, '_execute_write', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [
                Relationship(
                    id=f"rel-{i}",
                    source_id=r["source_id"],
                    target_id=r["target_id"],
                    type=r["type"],
                    properties={}
                )
                for i, r in enumerate(relationships_data)
            ]

            relationships = await adapter.batch_create_relationships(relationships_data)

            assert len(relationships) == 2


# ============================================================================
# Query Result Tests
# ============================================================================


class TestQueryResult:
    """Test query result handling."""

    def test_query_result_creation(self):
        """Test query result creation."""
        result = QueryResult(
            records=[{"n": {"id": "1"}}, {"n": {"id": "2"}}],
            summary={"nodes_created": 0, "relationships_created": 0}
        )

        assert len(result.records) == 2
        assert result.summary["nodes_created"] == 0

    def test_query_result_single(self):
        """Test getting single result."""
        result = QueryResult(
            records=[{"n": {"id": "1"}}],
            summary={}
        )

        single = result.single()
        assert single["n"]["id"] == "1"

    def test_query_result_empty(self):
        """Test empty result handling."""
        result = QueryResult(records=[], summary={})

        assert result.single() is None
        assert len(result.records) == 0


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for error tests."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test"
        )
        adapter = Neo4jStorageAdapter(config)
        adapter._driver = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, adapter):
        """Test connection error is handled."""
        with patch.object(adapter, '_execute_read', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Connection refused")

            with pytest.raises(Exception) as exc_info:
                await adapter.get_entity("entity-1")

            assert "Connection refused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_syntax_error(self, adapter):
        """Test query syntax error handling."""
        with patch.object(adapter, '_execute_read', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Invalid Cypher syntax")

            with pytest.raises(Exception) as exc_info:
                await adapter.execute_query("INVALID CYPHER")

            assert "Invalid" in str(exc_info.value)


# ============================================================================
# Transaction Tests
# ============================================================================


class TestTransactions:
    """Test transaction handling."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for transaction tests."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test"
        )
        adapter = Neo4jStorageAdapter(config)
        adapter._driver = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_transaction_commit(self, adapter):
        """Test successful transaction commit."""
        operations = [
            BatchOperation(
                operation="create",
                entity_data={"labels": ["Test"], "properties": {"name": "Test"}}
            )
        ]

        with patch.object(adapter, '_execute_transaction', new_callable=AsyncMock) as mock_tx:
            mock_tx.return_value = {"committed": True}

            result = await adapter.execute_transaction(operations)

            assert result["committed"] is True

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, adapter):
        """Test transaction rollback on error."""
        operations = [
            BatchOperation(
                operation="create",
                entity_data={"labels": ["Test"], "properties": {"name": "Test"}}
            )
        ]

        with patch.object(adapter, '_execute_transaction', new_callable=AsyncMock) as mock_tx:
            mock_tx.side_effect = Exception("Constraint violation")

            with pytest.raises(Exception):
                await adapter.execute_transaction(operations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
