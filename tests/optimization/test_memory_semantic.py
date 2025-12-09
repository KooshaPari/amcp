"""
Comprehensive tests for semantic memory system.

Tests core functionality:
- Fact storage and retrieval
- Relationship management
- Inference capabilities
- Confidence tracking and decay
- Query operations
"""

import asyncio
import pytest
import time
from unittest.mock import patch, AsyncMock

from optimization.memory.semantic import (
    SemanticMemory,
    SemanticEntry,
    SemanticRelation,
    SemanticConfig,
    RelationType,
)


@pytest.fixture
def config():
    """Test configuration for semantic memory."""
    return SemanticConfig(
        max_entries=100,
        max_relations=50,
        enable_inference=True,
        confidence_threshold=0.5,
        decay_rate=0.01,
    )


@pytest.fixture
async def memory(config):
    """Create semantic memory instance."""
    return SemanticMemory(config)


class TestSemanticEntry:
    """Test SemanticEntry dataclass."""

    def test_entry_creation(self):
        """Test creating an entry."""
        entry = SemanticEntry(
            entity="file_processor",
            property_name="capability",
            value="text_processing",
            confidence=0.9,
            source="observation",
        )

        assert entry.entity == "file_processor"
        assert entry.property_name == "capability"
        assert entry.value == "text_processing"
        assert entry.confidence == 0.9
        assert entry.source == "observation"
        assert entry.entry_id is not None
        assert entry.timestamp > 0

    def test_age_calculation(self):
        """Test age calculation."""
        past_time = time.time() - 100
        entry = SemanticEntry(timestamp=past_time)
        
        assert entry.age_seconds >= 99
        assert entry.age_seconds <= 101

    def test_to_dict(self):
        """Test dictionary conversion."""
        entry = SemanticEntry(
            entity="test_entity",
            property_name="test_prop",
            value="test_value",
            confidence=0.8,
            source="test_source",
        )

        d = entry.to_dict()
        assert d["entity"] == "test_entity"
        assert d["property"] == "test_prop"
        assert d["value"] == "test_value"
        assert d["confidence"] == 0.8
        assert d["source"] == "test_source"
        assert "age_seconds" in d


class TestSemanticRelation:
    """Test SemanticRelation dataclass."""

    def test_relation_creation(self):
        """Test creating a relation."""
        relation = SemanticRelation(
            entity1="task_A",
            relation_type=RelationType.REQUIRES,
            entity2="tool_X",
            weight=0.8,
            confidence=0.9,
        )

        assert relation.entity1 == "task_A"
        assert relation.relation_type == RelationType.REQUIRES
        assert relation.entity2 == "tool_X"
        assert relation.weight == 0.8
        assert relation.confidence == 0.9
        assert relation.relation_id is not None
        assert relation.timestamp > 0

    def test_to_dict(self):
        """Test dictionary conversion."""
        relation = SemanticRelation(
            entity1="A",
            relation_type=RelationType.SIMILAR_TO,
            entity2="B",
            weight=0.5,
            confidence=0.7,
        )

        d = relation.to_dict()
        assert d["entity1"] == "A"
        assert d["relation_type"] == "similar_to"
        assert d["entity2"] == "B"
        assert d["weight"] == 0.5
        assert d["confidence"] == 0.7


class TestSemanticMemory:
    """Test SemanticMemory class."""

    async def test_store_fact(self, memory):
        """Test storing a semantic fact."""
        entry_id = await memory.store_fact(
            entity="text_analyzer",
            property_name="supports_languages",
            value=["en", "es", "fr"],
            confidence=0.95,
            source="documentation",
        )

        assert entry_id is not None
        assert entry_id in memory.entries
        
        entry = memory.entries[entry_id]
        assert entry.entity == "text_analyzer"
        assert entry.property_name == "supports_languages"
        assert entry.value == ["en", "es", "fr"]
        assert entry.confidence == 0.95
        assert entry.source == "documentation"

    async def test_store_duplicate_fact(self, memory):
        """Test storing duplicate fact updates confidence."""
        entry_id1 = await memory.store_fact(
            entity="tool1",
            property_name="cost",
            value=0.5,
            confidence=0.8,
        )

        # Store same fact with higher confidence
        entry_id2 = await memory.store_fact(
            entity="tool1",
            property_name="cost",
            value=0.5,
            confidence=0.9,
        )

        # Should update existing entry
        assert entry_id1 == entry_id2
        entry = memory.entries[entry_id1]
        assert entry.confidence == 0.9

    async def test_store_relation(self, memory):
        """Test storing a semantic relation."""
        relation_id = await memory.store_relation(
            entity1="data_processing",
            relation_type=RelationType.REQUIRES,
            entity2="pandas",
            weight=0.9,
            confidence=0.85,
        )

        assert relation_id is not None
        assert relation_id in memory.relations
        
        relation = memory.relations[relation_id]
        assert relation.entity1 == "data_processing"
        assert relation.relation_type == RelationType.REQUIRES
        assert relation.entity2 == "pandas"
        assert relation.weight == 0.9
        assert relation.confidence == 0.85

    async def test_get_facts(self, memory):
        """Test retrieving facts about an entity."""
        # Store multiple facts
        await memory.store_fact("tool1", "capability", "text_processing", 0.9)
        await memory.store_fact("tool1", "cost", 0.5, 0.8)
        await memory.store_fact("tool1", "speed", "fast", 0.7)
        await memory.store_fact("tool2", "capability", "image_processing", 0.8)

        # Get facts for tool1
        facts = await memory.get_facts("tool1")
        assert len(facts) == 3
        
        # Should not include tool2 facts
        tool1_properties = {f.property_name for f in facts}
        assert tool1_properties == {"capability", "cost", "speed"}

    async def test_get_facts_with_property(self, memory):
        """Test retrieving facts for specific property."""
        await memory.store_fact("tool1", "capability", "text", 0.9)
        await memory.store_fact("tool1", "capability", "image", 0.8)
        await memory.store_fact("tool1", "cost", 0.5, 0.7)

        facts = await memory.get_facts("tool1", "capability")
        assert len(facts) == 2
        assert all(f.property_name == "capability" for f in facts)

    async def test_get_facts_with_threshold(self, memory):
        """Test retrieving facts with confidence threshold."""
        await memory.store_fact("tool1", "prop1", "value1", 0.9)
        await memory.store_fact("tool1", "prop2", "value2", 0.3)  # Below threshold
        await memory.store_fact("tool1", "prop3", "value3", 0.6)  # Above threshold

        facts = await memory.get_facts("tool1", confidence_threshold=0.5)
        assert len(facts) == 2
        
        for fact in facts:
            assert fact.confidence >= 0.5

    async def test_get_relations(self, memory):
        """Test retrieving relations for an entity."""
        # Store relations
        await memory.store_relation("task1", RelationType.REQUIRES, "tool1", 0.9)
        await memory.store_relation("task1", RelationType.PRODUCES, "output1", 0.8)
        await memory.store_relation("task2", RelationType.REQUIRES, "tool2", 0.7)

        # Get relations for task1
        relations = await memory.get_relations("task1")
        assert len(relations) == 2
        
        # Check relation types
        relation_types = {r.relation_type for r in relations}
        assert relation_types == {RelationType.REQUIRES, RelationType.PRODUCES}

    async def test_get_relations_by_type(self, memory):
        """Test retrieving relations of specific type."""
        await memory.store_relation("task1", RelationType.REQUIRES, "tool1", 0.9)
        await memory.store_relation("task1", RelationType.PRODUCES, "output1", 0.8)
        await memory.store_relation("task1", RelationType.REQUIRES, "tool2", 0.7)

        relations = await memory.get_relations("task1", relation_type=RelationType.REQUIRES)
        assert len(relations) == 2
        assert all(r.relation_type == RelationType.REQUIRES for r in relations)

    async def test_get_relations_by_target(self, memory):
        """Test retrieving relations pointing to a target."""
        await memory.store_relation("task1", RelationType.REQUIRES, "tool1", 0.9)
        await memory.store_relation("task2", RelationType.REQUIRES, "tool1", 0.8)
        await memory.store_relation("task3", RelationType.REQUIRES, "tool2", 0.7)

        relations = await memory.get_relations(target_entity="tool1")
        assert len(relations) == 2
        
        # Check entities
        entities = {r.entity1 for r in relations}
        assert entities == {"task1", "task2"}

    async def test_query_entity(self, memory):
        """Test querying entity properties."""
        await memory.store_fact("text_processor", "type", "tool", 0.9)
        await memory.store_fact("text_processor", "supports", ["txt", "md"], 0.8)
        await memory.store_fact("text_processor", "cost", 0.2, 0.7)

        result = await memory.query_entity("text_processor")
        assert result["entity"] == "text_processor"
        assert "facts" in result
        assert len(result["facts"]) == 3
        
        # Check specific fact
        facts = {f.property_name: f.value for f in result["facts"]}
        assert facts["type"] == "tool"
        assert facts["supports"] == ["txt", "md"]
        assert facts["cost"] == 0.2

    async def test_query_nonexistent_entity(self, memory):
        """Test querying non-existent entity."""
        result = await memory.query_entity("nonexistent")
        assert result["entity"] == "nonexistent"
        assert result["facts"] == []
        assert result["relations"] == []

    async def test_find_similar_entities(self, memory):
        """Test finding similar entities."""
        # Store related entities
        await memory.store_relation("text_processor", RelationType.SIMILAR_TO, "text_analyzer", 0.8)
        await memory.store_relation("text_analyzer", RelationType.SIMILAR_TO, "text_extractor", 0.7)
        await memory.store_relation("text_processor", RelationType.REQUIRES, "tool1", 0.9)  # Not similar

        similar = await memory.find_similar_entities("text_processor")
        assert len(similar) == 1
        assert similar[0] == "text_analyzer"

    async def test_find_entity_dependencies(self, memory):
        """Test finding entity dependencies."""
        await memory.store_relation("task1", RelationType.REQUIRES, "tool1", 0.9)
        await memory.store_relation("task1", RelationType.REQUIRES, "tool2", 0.8)
        await memory.store_relation("task1", RelationType.DEPENDS_ON, "task2", 0.7)
        await memory.store_relation("task3", RelationType.REQUIRES, "tool3", 0.6)

        deps = await memory.find_entity_dependencies("task1")
        assert len(deps) == 3
        assert set(deps) == {"tool1", "tool2", "task2"}

    async def test_inference_enabled(self, memory):
        """Test that inference is enabled."""
        assert memory.config.enable_inference is True

    async def test_inference_disabled(self, config):
        """Test behavior when inference is disabled."""
        config.enable_inference = False
        memory = SemanticMemory(config)
        
        # Store facts that could trigger inference
        await memory.store_fact("tool1", "type", "processor", 0.9)
        await memory.store_fact("processor", "requires", "input", 0.8)
        
        # No inference should occur
        facts = await memory.get_facts("tool1")
        assert len(facts) == 1
        assert facts[0].property_name == "type"

    async def test_confidence_decay(self, config):
        """Test confidence decay over time."""
        config.decay_rate = 0.1  # 10% decay
        memory = SemanticMemory(config)
        
        entry_id = await memory.store_fact(
            "test_entity",
            "test_prop",
            "test_value",
            confidence=1.0,
        )
        
        # Manually age the entry
        entry = memory.entries[entry_id]
        entry.timestamp = time.time() - 86400  # 1 day old
        
        # Apply decay
        await memory._apply_decay()
        
        # Confidence should have decayed
        decayed_entry = memory.entries[entry_id]
        assert decayed_entry.confidence < 1.0
        assert abs(decayed_entry.confidence - 0.9) < 0.01  # 1.0 - 0.1

    async def test_capacity_enforcement(self, config):
        """Test capacity enforcement for facts."""
        config.max_entries = 3
        memory = SemanticMemory(config)
        
        # Add entries up to capacity
        await memory.store_fact("entity1", "prop1", "value1", 0.9)
        await memory.store_fact("entity2", "prop2", "value2", 0.9)
        await memory.store_fact("entity3", "prop3", "value3", 0.9)
        
        assert len(memory.entries) == 3
        
        # Add one more - should enforce capacity
        await memory.store_fact("entity4", "prop4", "value4", 0.9)
        
        assert len(memory.entries) == 3  # Should stay at capacity

    async def test_relation_capacity_enforcement(self, config):
        """Test capacity enforcement for relations."""
        config.max_relations = 3
        memory = SemanticMemory(config)
        
        # Add relations up to capacity
        await memory.store_relation("e1", RelationType.REQUIRES, "e2", 0.9)
        await memory.store_relation("e2", RelationType.REQUIRES, "e3", 0.9)
        await memory.store_relation("e3", RelationType.REQUIRES, "e4", 0.9)
        
        assert len(memory.relations) == 3
        
        # Add one more - should enforce capacity
        await memory.store_relation("e4", RelationType.REQUIRES, "e5", 0.9)
        
        assert len(memory.relations) == 3  # Should stay at capacity

    async def test_remove_low_confidence_facts(self, memory):
        """Test removing facts below confidence threshold."""
        await memory.store_fact("entity1", "prop1", "value1", 0.8)
        await memory.store_fact("entity2", "prop2", "value2", 0.4)  # Below threshold
        await memory.store_fact("entity3", "prop3", "value3", 0.3)  # Below threshold
        
        removed = await memory.remove_low_confidence_facts(threshold=0.5)
        
        assert removed == 2
        assert len(memory.entries) == 1
        
        # Should only keep high confidence fact
        remaining = list(memory.entries.values())
        assert remaining[0].entity == "entity1"

    async def test_remove_weak_relations(self, memory):
        """Test removing relations below confidence threshold."""
        await memory.store_relation("e1", RelationType.REQUIRES, "e2", 0.8)
        await memory.store_relation("e2", RelationType.REQUIRES, "e3", 0.4)  # Below threshold
        await memory.store_relation("e3", RelationType.REQUIRES, "e4", 0.3)  # Below threshold
        
        removed = await memory.remove_weak_relations(threshold=0.5)
        
        assert removed == 2
        assert len(memory.relations) == 1
        
        # Should only keep strong relation
        remaining = list(memory.relations.values())
        assert remaining[0].entity1 == "e1"

    async def test_stats(self, memory):
        """Test memory statistics."""
        # Add some data
        await memory.store_fact("entity1", "prop1", "value1", 0.9)
        await memory.store_fact("entity2", "prop2", "value2", 0.7)
        await memory.store_relation("e1", RelationType.REQUIRES, "e2", 0.8)
        
        stats = await memory.stats()
        
        assert stats["total_facts"] == 2
        assert stats["total_relations"] == 1
        assert stats["fact_capacity"] == memory.config.max_entries
        assert stats["relation_capacity"] == memory.config.max_relations
        assert stats["avg_confidence"] == 0.8  # (0.9 + 0.7) / 2

    async def test_clear(self, memory):
        """Test clearing all data."""
        # Add some data
        await memory.store_fact("entity1", "prop1", "value1", 0.9)
        await memory.store_relation("e1", RelationType.REQUIRES, "e2", 0.8)
        
        assert len(memory.entries) > 0
        assert len(memory.relations) > 0
        
        # Clear
        await memory.clear()
        
        assert len(memory.entries) == 0
        assert len(memory.relations) == 0

    async def test_concurrent_access(self, memory):
        """Test concurrent access to memory."""
        tasks = []
        
        # Store facts concurrently
        for i in range(10):
            task = memory.store_fact(
                f"entity{i}",
                f"prop{i}",
                f"value{i}",
                confidence=0.9,
            )
            tasks.append(task)
        
        # Store relations concurrently
        for i in range(5):
            task = memory.store_relation(
                f"task{i}",
                RelationType.REQUIRES,
                f"tool{i}",
                0.8,
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should complete without errors
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None
        
        assert len(memory.entries) == 10
        assert len(memory.relations) == 5

    async def test_different_value_types(self, memory):
        """Test storing different value types."""
        await memory.store_fact("entity1", "string_val", "hello", 0.9)
        await memory.store_fact("entity1", "int_val", 42, 0.9)
        await memory.store_fact("entity1", "float_val", 3.14, 0.9)
        await memory.store_fact("entity1", "list_val", [1, 2, 3], 0.9)
        await memory.store_fact("entity1", "dict_val", {"key": "value"}, 0.9)
        
        facts = await memory.get_facts("entity1")
        assert len(facts) == 5
        
        # Check value types are preserved
        values = {f.property_name: f.value for f in facts}
        assert values["string_val"] == "hello"
        assert values["int_val"] == 42
        assert values["float_val"] == 3.14
        assert values["list_val"] == [1, 2, 3]
        assert values["dict_val"] == {"key": "value"}

    async def test_all_relation_types(self, memory):
        """Test storing all relation types."""
        entity_a = "entity_a"
        entity_b = "entity_b"
        
        for relation_type in RelationType:
            await memory.store_relation(
                entity_a,
                relation_type,
                entity_b,
                0.8,
                0.9,
            )
        
        relations = await memory.get_relations(entity_a)
        assert len(relations) == len(RelationType)
        
        stored_types = {r.relation_type for r in relations}
        assert stored_types == set(RelationType)
