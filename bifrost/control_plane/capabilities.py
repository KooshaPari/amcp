"""Capability management for SmartCP Control Plane."""

import logging
from typing import Any

from smartcp.bifrost.control_plane.models import (
    CapabilityType,
    ServerCapability,
)

logger = logging.getLogger(__name__)


class CapabilityManager:
    """Manages server capabilities."""

    def __init__(self) -> None:
        """Initialize capability manager."""
        self._capabilities: list[ServerCapability] = []
        self._init_default_capabilities()

    def _init_default_capabilities(self) -> None:
        """Initialize default SmartCP capabilities."""
        self._capabilities = [
            ServerCapability(
                name=CapabilityType.CODE_EXECUTION,
                version="1.0.0",
                enabled=True,
                config={"language": "python", "sandbox": True},
                limits={"max_execution_time": 300, "max_memory_mb": 512},
            ),
            ServerCapability(
                name=CapabilityType.MEMORY_STORAGE,
                version="1.0.0",
                enabled=True,
                config={"types": ["working", "persistent", "context"]},
                limits={
                    "max_keys_per_user": 1000,
                    "max_value_size_kb": 1024,
                },
            ),
            ServerCapability(
                name=CapabilityType.STATE_MANAGEMENT,
                version="1.0.0",
                enabled=True,
                config={"user_isolated": True},
                limits={"max_keys": 10000},
            ),
            ServerCapability(
                name=CapabilityType.VARIABLE_NAMESPACE,
                version="1.0.0",
                enabled=True,
                config={"user_isolated": True, "persistent": False},
                limits={"max_variables": 500},
            ),
            ServerCapability(
                name=CapabilityType.SANDBOX_ISOLATION,
                version="1.0.0",
                enabled=True,
                config={"isolation_level": "process"},
                limits={},
            ),
            ServerCapability(
                name=CapabilityType.TTL_SUPPORT,
                version="1.0.0",
                enabled=True,
                config={"default_ttl_seconds": 3600},
                limits={"max_ttl_seconds": 86400 * 30},
            ),
        ]

    @property
    def capabilities(self) -> list[ServerCapability]:
        """Get server capabilities."""
        return self._capabilities.copy()

    def add_capability(self, capability: ServerCapability) -> None:
        """Add a capability.

        Args:
            capability: Capability to add
        """
        # Check if already exists
        for i, existing in enumerate(self._capabilities):
            if existing.name == capability.name:
                self._capabilities[i] = capability
                logger.info(f"Updated capability: {capability.name.value}")
                return

        self._capabilities.append(capability)
        logger.info(f"Added capability: {capability.name.value}")

    def remove_capability(self, name: CapabilityType) -> bool:
        """Remove a capability.

        Args:
            name: Capability name to remove

        Returns:
            True if removed
        """
        for i, cap in enumerate(self._capabilities):
            if cap.name == name:
                self._capabilities.pop(i)
                logger.info(f"Removed capability: {name.value}")
                return True
        return False

    async def register_with_bifrost(
        self, client: Any, server_id: str
    ) -> None:
        """Register capabilities with Bifrost.

        Args:
            client: Bifrost client
            server_id: Server ID
        """
        if not client:
            logger.debug("No Bifrost client, skipping capability registration")
            return

        try:
            capabilities_data = [cap.to_dict() for cap in self._capabilities]

            mutation = """
                mutation RegisterCapabilities($serverId: String!, $capabilities: JSON!) {
                    registerServerCapabilities(serverId: $serverId, capabilities: $capabilities) {
                        success
                        message
                    }
                }
            """

            result = await client.mutate(
                mutation,
                variables={
                    "serverId": server_id,
                    "capabilities": capabilities_data,
                },
            )

            registration = result.get("registerServerCapabilities", {})
            if registration.get("success"):
                logger.info(
                    f"Registered {len(self._capabilities)} capabilities with "
                    "Bifrost"
                )
            else:
                logger.warning(
                    f"Capability registration failed: "
                    f"{registration.get('message')}"
                )

        except Exception as e:
            logger.error(f"Failed to register capabilities: {e}")
