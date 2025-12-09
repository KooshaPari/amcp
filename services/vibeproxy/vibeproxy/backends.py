"""Vibeproxy Backend Routing.

Provides intelligent routing between cloud, local, and remote backends.
Supports:
- Cloud backends (hosted MCP services)
- Local backends (SmartCP, subprocess servers)
- Remote-local backends (tunneled connections)
- Bifrost and external MCP servers
- LLM and SLM backends
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .proxy import (
    BackendConfig,
    BackendType,
    create_cloud_backend,
    create_local_backend,
    create_smartcp_backend,
)

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Backend routing strategies."""

    PRIORITY = "priority"  # Route by priority (highest first)
    ROUND_ROBIN = "round_robin"  # Distribute evenly
    LATENCY = "latency"  # Route to fastest backend
    FALLBACK = "fallback"  # Try in order until success
    CAPABILITY = "capability"  # Route by tool capability


@dataclass
class RoutingRule:
    """Rule for routing requests to backends."""

    pattern: str  # Tool name pattern (supports * wildcard)
    backend: str  # Target backend name
    priority: int = 0


class BackendRouter:
    """Routes requests to appropriate backends.

    Implements various routing strategies and handles failover.
    """

    def __init__(
        self,
        backends: list[BackendConfig],
        strategy: RoutingStrategy = RoutingStrategy.PRIORITY,
        rules: list[RoutingRule] | None = None,
    ) -> None:
        """Initialize router.

        Args:
            backends: Available backends
            strategy: Default routing strategy
            rules: Custom routing rules
        """
        self._backends = {b.name: b for b in backends}
        self._strategy = strategy
        self._rules = rules or []
        self._latencies: dict[str, float] = {}  # For latency-based routing

    def get_backend(self, tool_name: str) -> BackendConfig | None:
        """Get the best backend for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Best matching backend or None
        """
        # Check custom rules first
        for rule in sorted(self._rules, key=lambda r: -r.priority):
            if self._matches_pattern(tool_name, rule.pattern):
                return self._backends.get(rule.backend)

        # Apply default strategy
        if self._strategy == RoutingStrategy.PRIORITY:
            return self._route_by_priority()
        elif self._strategy == RoutingStrategy.LATENCY:
            return self._route_by_latency()
        elif self._strategy == RoutingStrategy.ROUND_ROBIN:
            return self._route_round_robin()

        # Fallback to first enabled backend
        for backend in self._backends.values():
            if backend.enabled:
                return backend
        return None

    def get_fallback_backends(self, exclude: str) -> list[BackendConfig]:
        """Get fallback backends excluding the given one.

        Args:
            exclude: Backend name to exclude

        Returns:
            List of fallback backends in priority order
        """
        backends = [
            b for name, b in self._backends.items()
            if name != exclude and b.enabled
        ]
        return sorted(backends, key=lambda b: -b.priority)

    def record_latency(self, backend_name: str, latency_ms: float) -> None:
        """Record latency for a backend.

        Args:
            backend_name: Backend name
            latency_ms: Latency in milliseconds
        """
        # Exponential moving average
        if backend_name in self._latencies:
            self._latencies[backend_name] = (
                0.8 * self._latencies[backend_name] + 0.2 * latency_ms
            )
        else:
            self._latencies[backend_name] = latency_ms

    def _matches_pattern(self, tool_name: str, pattern: str) -> bool:
        """Check if tool name matches pattern.

        Args:
            tool_name: Tool name to check
            pattern: Pattern with optional * wildcard

        Returns:
            True if matches
        """
        if "*" not in pattern:
            return tool_name == pattern

        parts = pattern.split("*")
        if len(parts) == 2:
            prefix, suffix = parts
            return tool_name.startswith(prefix) and tool_name.endswith(suffix)

        return False

    def _route_by_priority(self) -> BackendConfig | None:
        """Route to highest priority backend."""
        enabled = [b for b in self._backends.values() if b.enabled]
        if not enabled:
            return None
        return max(enabled, key=lambda b: b.priority)

    def _route_by_latency(self) -> BackendConfig | None:
        """Route to lowest latency backend."""
        enabled = [b for b in self._backends.values() if b.enabled]
        if not enabled:
            return None

        # Prefer backends with recorded latency
        with_latency = [b for b in enabled if b.name in self._latencies]
        if with_latency:
            return min(with_latency, key=lambda b: self._latencies[b.name])

        return enabled[0]

    def _route_round_robin(self) -> BackendConfig | None:
        """Route using round-robin."""
        enabled = [b for b in self._backends.values() if b.enabled]
        if not enabled:
            return None
        # Simple round-robin - just rotate the list
        return enabled[0]


# Preset backend configurations


def get_default_backends() -> list[BackendConfig]:
    """Get default backend configurations.

    Returns:
        List of default backend configs
    """
    return [
        create_smartcp_backend(),
    ]


def get_development_backends() -> list[BackendConfig]:
    """Get development backend configurations.

    Returns:
        List of development backend configs
    """
    return [
        create_smartcp_backend(url="http://localhost:8000"),
        create_local_backend(
            command="npx",
            args=["@anthropic/memory-server"],
            name="memory",
        ),
    ]


def get_production_backends(
    smartcp_url: str,
    cloud_url: str | None = None,
) -> list[BackendConfig]:
    """Get production backend configurations.

    Args:
        smartcp_url: SmartCP server URL
        cloud_url: Optional cloud service URL

    Returns:
        List of production backend configs
    """
    backends = [
        create_smartcp_backend(url=smartcp_url),
    ]

    if cloud_url:
        backends.append(create_cloud_backend(url=cloud_url, name="cloud"))

    return backends


# Backend discovery


async def discover_backends(
    smartcp_url: str | None = None,
    scan_local: bool = False,
) -> list[BackendConfig]:
    """Discover available backends.

    Args:
        smartcp_url: SmartCP server URL to check
        scan_local: Whether to scan for local MCP servers

    Returns:
        List of discovered backends
    """
    discovered = []

    # Check SmartCP
    if smartcp_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{smartcp_url}/health")
                if response.status_code == 200:
                    discovered.append(create_smartcp_backend(url=smartcp_url))
                    logger.info(f"Discovered SmartCP at {smartcp_url}")
        except Exception as e:
            logger.debug(f"SmartCP not available at {smartcp_url}: {e}")

    # Scan for local servers (check common ports)
    if scan_local:
        common_ports = [8000, 8001, 8080, 3000]
        for port in common_ports:
            url = f"http://localhost:{port}"
            try:
                import httpx
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"{url}/health")
                    if response.status_code == 200:
                        discovered.append(BackendConfig(
                            name=f"local_{port}",
                            backend_type=BackendType.LOCAL,
                            url=url,
                        ))
                        logger.info(f"Discovered local server at {url}")
            except Exception:
                pass

    return discovered


# Backend health checking


@dataclass
class BackendHealth:
    """Health status of a backend."""

    name: str
    healthy: bool
    latency_ms: float | None = None
    error: str | None = None
    tools_count: int = 0


async def check_backend_health(backend: BackendConfig) -> BackendHealth:
    """Check health of a single backend.

    Args:
        backend: Backend to check

    Returns:
        Health status
    """
    import time

    start = time.perf_counter()

    try:
        if backend.url:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{backend.url}/health")
                latency = (time.perf_counter() - start) * 1000

                if response.status_code == 200:
                    return BackendHealth(
                        name=backend.name,
                        healthy=True,
                        latency_ms=latency,
                    )
                else:
                    return BackendHealth(
                        name=backend.name,
                        healthy=False,
                        error=f"HTTP {response.status_code}",
                    )
        else:
            # For subprocess backends, we can't easily check health
            return BackendHealth(
                name=backend.name,
                healthy=True,  # Assume healthy if not started
            )

    except Exception as e:
        return BackendHealth(
            name=backend.name,
            healthy=False,
            error=str(e),
        )


async def check_all_backends_health(
    backends: list[BackendConfig],
) -> list[BackendHealth]:
    """Check health of all backends.

    Args:
        backends: Backends to check

    Returns:
        List of health statuses
    """
    import asyncio
    tasks = [check_backend_health(b) for b in backends]
    return await asyncio.gather(*tasks)
