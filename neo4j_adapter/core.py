"""Core Neo4j storage adapter with connection management."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from .models import Neo4jConfig, Neo4jConnectionState, QueryResult

logger = logging.getLogger(__name__)


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
