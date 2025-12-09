"""Bifrost client and communication for SmartCP Control Plane."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from smartcp.bifrost.control_plane.models import ControlPlaneConfig

logger = logging.getLogger(__name__)


class BifrostClient:
    """Manages connection to Bifrost."""

    def __init__(self, config: ControlPlaneConfig) -> None:
        """Initialize Bifrost client.

        Args:
            config: Control plane configuration
        """
        self._config = config
        self._client: Any = None
        self._running = False

    async def connect(self) -> None:
        """Connect to Bifrost gateway."""
        try:
            from smartcp.infrastructure.bifrost import BifrostClient as BifrClient

            self._client = BifrClient(
                url=self._config.bifrost_url,
                api_key=self._config.api_key,
            )
            await self._client.connect()
            logger.info(f"Connected to Bifrost: {self._config.bifrost_url}")

        except ImportError:
            logger.warning("BifrostClient not available")
            self._client = None
        except Exception as e:
            logger.error(f"Bifrost connection error: {e}")
            self._client = None

    async def disconnect(self) -> None:
        """Disconnect from Bifrost gateway."""
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                logger.error(f"Bifrost disconnect error: {e}")
            finally:
                self._client = None

    def is_connected(self) -> bool:
        """Check if connected to Bifrost.

        Returns:
            True if connected
        """
        return self._client is not None

    async def send_heartbeat(self) -> None:
        """Send heartbeat to Bifrost."""
        if not self._client:
            return

        try:
            mutation = """
                mutation ServerHeartbeat($serverId: String!, $timestamp: String!) {
                    serverHeartbeat(serverId: $serverId, timestamp: $timestamp) {
                        acknowledged
                    }
                }
            """

            await self._client.mutate(
                mutation,
                variables={
                    "serverId": self._config.server_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            logger.debug("Heartbeat sent")

        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    async def query(self, query_str: str, variables: dict = None) -> dict:
        """Execute GraphQL query.

        Args:
            query_str: GraphQL query string
            variables: Query variables

        Returns:
            Query result
        """
        if not self._client:
            return {}

        try:
            return await self._client.query(query_str, variables=variables)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {}

    async def mutate(self, mutation_str: str, variables: dict = None) -> dict:
        """Execute GraphQL mutation.

        Args:
            mutation_str: GraphQL mutation string
            variables: Mutation variables

        Returns:
            Mutation result
        """
        if not self._client:
            return {}

        try:
            return await self._client.mutate(mutation_str, variables=variables)
        except Exception as e:
            logger.error(f"Mutation failed: {e}")
            return {}

    async def sync_configuration(self) -> dict[str, Any]:
        """Sync configuration with Bifrost.

        Returns:
            Synced configuration
        """
        if not self._client:
            return {}

        try:
            query = """
                query GetServerConfig($serverId: String!) {
                    serverConfiguration(serverId: $serverId) {
                        config
                        version
                        updatedAt
                    }
                }
            """

            result = await self._client.query(
                query,
                variables={"serverId": self._config.server_id},
            )

            config_data = result.get("serverConfiguration", {})
            logger.info(
                f"Configuration synced: version "
                f"{config_data.get('version', 'unknown')}"
            )
            return config_data.get("config", {})

        except Exception as e:
            logger.error(f"Configuration sync failed: {e}")
            return {}

    async def push_configuration(self, config: dict[str, Any]) -> bool:
        """Push configuration to Bifrost.

        Args:
            config: Configuration to push

        Returns:
            True if successful
        """
        if not self._client:
            return False

        try:
            mutation = """
                mutation UpdateServerConfig($serverId: String!, $config: JSON!) {
                    updateServerConfiguration(serverId: $serverId, config: $config) {
                        success
                        version
                    }
                }
            """

            result = await self._client.mutate(
                mutation,
                variables={
                    "serverId": self._config.server_id,
                    "config": config,
                },
            )

            update_result = result.get("updateServerConfiguration", {})
            if update_result.get("success"):
                logger.info(
                    f"Configuration pushed: "
                    f"version {update_result.get('version')}"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Configuration push failed: {e}")
            return False
