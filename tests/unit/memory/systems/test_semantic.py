"""
Semantic Memory System Tests

Tests for semantic memory system in isolation.
"""

import pytest
import time
from optimization.memory.semantic import RelationType


@pytest.mark.asyncio
class TestSemanticMemory:
    """Test semantic memory system."""

    async def test_assert_and_query_facts(self, semantic_memory):
        """Test asserting and querying facts."""
        fact_id = await semantic_memory.assert_fact(
            entity="GPT-4",
            property_name="capability",
            value="code_generation",
            confidence=0.95
        )

        assert fact_id in semantic_memory.entries

        # Query
        facts = await semantic_memory.query_facts("GPT-4")
        assert len(facts) == 1
        assert facts[0].value == "code_generation"

    async def test_relationships(self, semantic_memory):
        """Test relationship assertions."""
        rel_id = await semantic_memory.assert_relation(
            entity1="GPT-4",
            relation_type=RelationType.REQUIRES,
            entity2="OpenAI API",
            weight=0.95
        )

        assert rel_id in semantic_memory.relations

        # Query
        relations = await semantic_memory.query_relations(entity1="GPT-4")
        assert len(relations) > 0
        assert relations[0].entity2 == "OpenAI API"

    async def test_entity_graph_traversal(self, semantic_memory):
        """Test graph traversal to find neighbors."""
        # Create a graph
        await semantic_memory.assert_relation(
            entity1="A",
            relation_type=RelationType.REQUIRES,
            entity2="B"
        )
        await semantic_memory.assert_relation(
            entity1="B",
            relation_type=RelationType.REQUIRES,
            entity2="C"
        )

        # Find neighbors
        neighbors = await semantic_memory.find_neighbors("A", max_depth=2)

        assert "depth_1" in neighbors
        assert "B" in neighbors["depth_1"]
        assert "depth_2" in neighbors
        assert "C" in neighbors["depth_2"]

    async def test_confidence_decay(self, semantic_memory):
        """Test confidence decay over time."""
        fact_id = await semantic_memory.assert_fact(
            entity="old_fact",
            property_name="prop",
            value="value",
            confidence=0.9
        )

        # Simulate old entry (60+ days to decay below 0.5 threshold)
        entry = semantic_memory.entries[fact_id]
        entry.timestamp = time.time() - (60 * 86400)  # 60 days old

        # Decay
        decayed = await semantic_memory.decay_confidence()
        assert decayed > 0

        # Verify decayed
        updated_entry = semantic_memory.entries[fact_id]
        assert updated_entry.confidence < 0.9
        assert updated_entry.confidence < 0.5  # Should be below threshold

    async def test_tool_capability_query(self, semantic_memory):
        """Test querying tool capabilities."""
        await semantic_memory.assert_fact(
            entity="analyzer_tool",
            property_name="capability",
            value="data_processing"
        )
        await semantic_memory.assert_fact(
            entity="analyzer_tool",
            property_name="capability",
            value="pattern_recognition"
        )

        capabilities = await semantic_memory.get_capabilities("analyzer_tool")
        assert "data_processing" in capabilities
        assert "pattern_recognition" in capabilities
