"""Tests for vector_graph_db module.

Validates dependency injection pattern and removal of global mutable state.
"""

import pytest
import asyncio
from infrastructure.adapters.vector_db import (
    VectorRecord,
    GraphNode,
    GraphRelationship,
    VectorDatabase,
    GraphDatabase,
    HybridSearch,
    VectorGraphContext,
    create_vector_graph_context,
)


class TestVectorDatabase:
    """Tests for VectorDatabase class."""

    def test_vector_database_initialization(self):
        """Test VectorDatabase initialization."""
        db = VectorDatabase()
        assert db.provider == "qdrant"
        assert db.vectors == {}

    def test_vector_database_custom_provider(self):
        """Test VectorDatabase with custom provider."""
        db = VectorDatabase(provider="weaviate")
        assert db.provider == "weaviate"

    def test_vector_record_creation(self):
        """Test VectorRecord creation."""
        record = VectorRecord(
            id="test-1",
            vector=[0.1, 0.2, 0.3],
            metadata={"name": "test"},
        )
        assert record.id == "test-1"
        assert record.vector == [0.1, 0.2, 0.3]
        assert record.metadata == {"name": "test"}


class TestGraphDatabase:
    """Tests for GraphDatabase class."""

    def test_graph_database_initialization(self):
        """Test GraphDatabase initialization."""
        db = GraphDatabase()
        assert db.provider == "neo4j"
        assert db.nodes == {}
        assert db.relationships == []

    def test_graph_database_custom_provider(self):
        """Test GraphDatabase with custom provider."""
        db = GraphDatabase(provider="arangodb")
        assert db.provider == "arangodb"

    def test_graph_node_creation(self):
        """Test GraphNode creation."""
        node = GraphNode(
            id="node-1",
            label="Entity",
            properties={"name": "test"},
        )
        assert node.id == "node-1"
        assert node.label == "Entity"
        assert node.properties == {"name": "test"}

    def test_graph_relationship_creation(self):
        """Test GraphRelationship creation."""
        rel = GraphRelationship(
            source_id="node-1",
            target_id="node-2",
            relationship_type="LINKED_TO",
            properties={"weight": 1.0},
        )
        assert rel.source_id == "node-1"
        assert rel.target_id == "node-2"
        assert rel.relationship_type == "LINKED_TO"
        assert rel.properties == {"weight": 1.0}


class TestVectorGraphContext:
    """Tests for VectorGraphContext and dependency injection."""

    def test_context_creation_defaults(self):
        """Test context creation with default instances."""
        context = VectorGraphContext()

        assert isinstance(context.vector_db, VectorDatabase)
        assert isinstance(context.graph_db, GraphDatabase)
        assert isinstance(context.hybrid_search, HybridSearch)

    def test_context_creation_with_custom_instances(self):
        """Test context creation with custom instances."""
        vector_db = VectorDatabase(provider="weaviate")
        graph_db = GraphDatabase(provider="neo4j")

        context = VectorGraphContext(vector_db=vector_db, graph_db=graph_db)

        assert context.vector_db is vector_db
        assert context.graph_db is graph_db
        assert context.hybrid_search.vector_db is vector_db
        assert context.hybrid_search.graph_db is graph_db

    def test_create_context_factory(self):
        """Test factory function for context creation."""
        context = create_vector_graph_context()

        assert isinstance(context.vector_db, VectorDatabase)
        assert isinstance(context.graph_db, GraphDatabase)
        assert isinstance(context.hybrid_search, HybridSearch)

    def test_create_context_with_custom_instances(self):
        """Test factory function with custom instances."""
        vector_db = VectorDatabase()
        graph_db = GraphDatabase()

        context = create_vector_graph_context(
            vector_db=vector_db, graph_db=graph_db
        )

        assert context.vector_db is vector_db
        assert context.graph_db is graph_db

    def test_context_isolation(self):
        """Test that contexts are isolated from each other."""
        context1 = create_vector_graph_context()
        context2 = create_vector_graph_context()

        # Verify they have different instances
        assert context1.vector_db is not context2.vector_db
        assert context1.graph_db is not context2.graph_db

    def test_context_independence(self):
        """Test that contexts have independent database instances."""
        context1 = create_vector_graph_context()
        context2 = create_vector_graph_context()

        # Verify different instances
        assert context1.vector_db is not context2.vector_db
        assert context1.graph_db is not context2.graph_db
        assert context1.hybrid_search is not context2.hybrid_search


class TestHybridSearch:
    """Tests for HybridSearch class."""

    def test_hybrid_search_initialization(self):
        """Test hybrid search initialization with dependency injection."""
        vector_db = VectorDatabase()
        graph_db = GraphDatabase()

        hybrid = HybridSearch(vector_db=vector_db, graph_db=graph_db)

        assert hybrid.vector_db is vector_db
        assert hybrid.graph_db is graph_db

    def test_hybrid_search_default_initialization(self):
        """Test hybrid search with default instances."""
        hybrid = HybridSearch()

        assert isinstance(hybrid.vector_db, VectorDatabase)
        assert isinstance(hybrid.graph_db, GraphDatabase)

    def test_hybrid_search_partial_injection(self):
        """Test hybrid search with partial dependency injection."""
        vector_db = VectorDatabase()

        hybrid = HybridSearch(vector_db=vector_db)

        assert hybrid.vector_db is vector_db
        assert isinstance(hybrid.graph_db, GraphDatabase)


class TestStatelessness:
    """Tests validating removal of global mutable state."""

    def test_no_module_level_state(self):
        """Verify no module-level mutable globals exist."""
        import smartcp.vector_graph_db as module

        # Check that old global variables are removed
        assert not hasattr(module, "_vector_db")
        assert not hasattr(module, "_graph_db")
        assert not hasattr(module, "_hybrid_search")

    def test_no_get_vector_database_function(self):
        """Verify old global getter functions are removed."""
        import smartcp.vector_graph_db as module

        assert not hasattr(module, "get_vector_database")

    def test_no_get_graph_database_function(self):
        """Verify old global getter functions are removed."""
        import smartcp.vector_graph_db as module

        assert not hasattr(module, "get_graph_database")

    def test_no_get_hybrid_search_function(self):
        """Verify old global getter functions are removed."""
        import smartcp.vector_graph_db as module

        assert not hasattr(module, "get_hybrid_search")

    def test_dependency_injection_pattern(self):
        """Verify dependency injection pattern is implemented."""
        import smartcp.vector_graph_db as module

        # Check for factory function
        assert hasattr(module, "create_vector_graph_context")
        assert callable(module.create_vector_graph_context)

        # Check for context class
        assert hasattr(module, "VectorGraphContext")

    def test_multiple_context_instances_are_independent(self):
        """Test that multiple contexts are independent."""
        context1 = create_vector_graph_context()
        context2 = create_vector_graph_context()
        context3 = create_vector_graph_context()

        # Verify all are different instances
        instances = [context1.vector_db, context2.vector_db, context3.vector_db]
        assert len(set(id(inst) for inst in instances)) == 3

        graph_instances = [context1.graph_db, context2.graph_db, context3.graph_db]
        assert len(set(id(inst) for inst in graph_instances)) == 3
