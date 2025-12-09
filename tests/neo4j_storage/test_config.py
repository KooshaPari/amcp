"""Tests for Neo4j configuration."""

from neo4j_adapter import Neo4jConfig


class TestNeo4jConfig:
    """Test Neo4j configuration."""

    def test_default_config(self):
        """Test default Neo4j config values."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
        assert config.max_connection_pool_size == 50
        assert config.connection_timeout == 30.0

    def test_custom_config(self):
        """Test custom Neo4j config values."""
        config = Neo4jConfig(
            uri="bolt://db.example.com:7687",
            username="admin",
            password="secret",
            database="mydb",
            max_connection_pool_size=100,
            connection_timeout=60.0
        )
        assert config.database == "mydb"
        assert config.max_connection_pool_size == 100
        assert config.connection_timeout == 60.0

    def test_config_encryption_settings(self):
        """Test encryption settings."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password",
            encrypted=False
        )
        assert config.encrypted == False

    def test_config_transaction_retry(self):
        """Test transaction retry settings."""
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password",
            max_transaction_retry_time=60.0
        )
        assert config.max_transaction_retry_time == 60.0
