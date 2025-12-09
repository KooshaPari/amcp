"""Tests for Cypher query builder."""

from neo4j_adapter import CypherQueryBuilder


class TestCypherQueryBuilder:
    """Test Cypher query builder."""

    def test_match_query(self):
        """Test basic MATCH query building."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:Person)")
            .returns("n")
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
            .match("(n:Person)")
            .where("n.name = 'John'")
            .returns("n")
            .build()
        )

        assert "WHERE" in query
        assert "n.name" in query

    def test_create_query(self):
        """Test CREATE query building."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .create("(n:Document {title: $title})")
            .param("title", "Report")
            .returns("n")
            .build()
        )

        assert "CREATE" in query
        assert "(n:Document" in query

    def test_create_relationship_query(self):
        """Test relationship creation query."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(a:Person)")
            .where_id("a", "person-1")
            .match("(b:Person)")
            .where_id("b", "person-2")
            .create("(a)-[:KNOWS]->(b)")
            .returns("a, b")
            .build()
        )

        assert "KNOWS" in query
        assert "MATCH" in query

    def test_optional_match(self):
        """Test OPTIONAL MATCH query."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:Person)")
            .optional_match("(n)-[r]->(m)")
            .returns("n, r, m")
            .build()
        )

        assert "OPTIONAL MATCH" in query

    def test_order_by(self):
        """Test ORDER BY clause."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:Task)")
            .returns("n")
            .order_by("n.created_at", desc=True)
            .build()
        )

        assert "ORDER BY" in query
        assert "DESC" in query

    def test_limit_and_skip(self):
        """Test LIMIT and SKIP clauses."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:Entity)")
            .returns("n")
            .skip(10)
            .limit(20)
            .build()
        )

        assert "SKIP" in query
        assert "LIMIT" in query

    def test_merge_clause(self):
        """Test MERGE clause for upsert operations."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .merge("(n:Person {id: $id})")
            .param("id", "person-1")
            .set("n.updated_at = datetime()")
            .returns("n")
            .build()
        )

        assert "MERGE" in query
        assert "SET" in query

    def test_delete_query(self):
        """Test DELETE query building."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:TempNode)")
            .where("n.id = 'temp-1'")
            .delete("n")
            .build()
        )

        assert "DELETE" in query

    def test_set_clause(self):
        """Test SET clause for property updates."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:Task)")
            .where_id("n", "task-1")
            .set("n.status = 'completed'")
            .returns("n")
            .build()
        )

        assert "SET" in query

    def test_params_method(self):
        """Test adding multiple parameters."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:Person)")
            .where("n.name = $name AND n.age = $age")
            .params(name="John", age=30)
            .returns("n")
            .build()
        )

        assert params["name"] == "John"
        assert params["age"] == 30

    def test_detach_delete(self):
        """Test DETACH DELETE query."""
        builder = CypherQueryBuilder()
        query, params = (
            builder
            .match("(n:Person)")
            .where_id("n", "person-1")
            .delete("n", detach=True)
            .build()
        )

        assert "DETACH DELETE" in query
