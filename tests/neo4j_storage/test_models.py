"""Tests for Entity and Relationship models."""

from neo4j_adapter import Entity, Relationship
from .conftest import _utcnow


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

    def test_entity_creation_with_timestamps(self):
        """Test entity with custom timestamps."""
        now = _utcnow()
        entity = Entity(
            id="entity-4",
            labels=["Task"],
            properties={"status": "pending"},
            created_at=now,
            updated_at=now
        )

        assert entity.id == "entity-4"
        assert entity.labels == ["Task"]
        assert entity.properties["status"] == "pending"
        assert entity.created_at == now


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

    def test_relationship_with_properties(self):
        """Test relationship with properties."""
        rel = Relationship(
            id="rel-3",
            source_id="x",
            target_id="y",
            type="DEPENDS_ON",
            properties={"weight": 0.5, "priority": "high"}
        )

        assert rel.type == "DEPENDS_ON"
        assert rel.source_id == "x"
        assert rel.properties["weight"] == 0.5
