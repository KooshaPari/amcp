"""SmartCP Event Emission for Bifrost/NATS Integration.

Provides event publishing for SmartCP operations to enable:
- Tool execution event tracking
- Memory operation events
- State change events
- Performance metrics
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Check if NATS is available
try:
    from nats.aio.client import Client as NATSClient

    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    NATSClient = None  # type: ignore[assignment]


class SmartCPEventType(Enum):
    """SmartCP event types for NATS publishing."""

    # Tool execution events
    TOOL_EXECUTION_STARTED = "smartcp.tool.execution.started"
    TOOL_EXECUTION_COMPLETED = "smartcp.tool.execution.completed"
    TOOL_EXECUTION_FAILED = "smartcp.tool.execution.failed"

    # Memory events
    MEMORY_STORED = "smartcp.memory.stored"
    MEMORY_RETRIEVED = "smartcp.memory.retrieved"
    MEMORY_DELETED = "smartcp.memory.deleted"
    MEMORY_CLEARED = "smartcp.memory.cleared"

    # State events
    STATE_CHANGED = "smartcp.state.changed"
    STATE_CLEARED = "smartcp.state.cleared"

    # Execution events
    CODE_EXECUTION_STARTED = "smartcp.code.execution.started"
    CODE_EXECUTION_COMPLETED = "smartcp.code.execution.completed"
    CODE_EXECUTION_FAILED = "smartcp.code.execution.failed"
    CODE_EXECUTION_TIMEOUT = "smartcp.code.execution.timeout"

    # System events
    SERVER_STARTED = "smartcp.server.started"
    SERVER_STOPPED = "smartcp.server.stopped"
    HEALTH_CHECK = "smartcp.health.check"


@dataclass
class SmartCPEvent:
    """Base SmartCP event structure."""

    event_type: SmartCPEventType
    user_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    event_id: str = field(default_factory=lambda: f"smartcp-{int(time.time() * 1000)}")
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def to_json(self) -> bytes:
        """Serialize event to JSON bytes."""
        return json.dumps(self.to_dict()).encode("utf-8")


@dataclass
class ToolExecutionEvent(SmartCPEvent):
    """Tool execution event with detailed information."""

    tool_name: str = ""
    input_params: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "tool_name": self.tool_name,
            "input_params": self.input_params,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
        })
        return base


@dataclass
class MemoryEvent(SmartCPEvent):
    """Memory operation event."""

    key: str = ""
    memory_type: str = ""
    value_size: int = 0
    ttl: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "key": self.key,
            "memory_type": self.memory_type,
            "value_size": self.value_size,
            "ttl": self.ttl,
        })
        return base


@dataclass
class CodeExecutionEvent(SmartCPEvent):
    """Code execution event."""

    execution_id: str = ""
    language: str = "python"
    code_length: int = 0
    status: str = ""
    duration_ms: float = 0.0
    variables_created: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "execution_id": self.execution_id,
            "language": self.language,
            "code_length": self.code_length,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "variables_created": self.variables_created,
            "error": self.error,
        })
        return base


@dataclass
class EventPublisherConfig:
    """Configuration for SmartCP event publisher."""

    enabled: bool = True
    nats_servers: list[str] = field(
        default_factory=lambda: ["nats://localhost:4222"]
    )
    subject_prefix: str = "smartcp"
    max_payload_size: int = 1048576  # 1MB
    connection_timeout: int = 10
    max_reconnect_attempts: int = 60


class SmartCPEventPublisher:
    """Publishes SmartCP events to NATS.

    Features:
    - Structured event publishing
    - Automatic reconnection
    - Payload size validation
    - Graceful degradation when NATS unavailable
    """

    def __init__(self, config: EventPublisherConfig | None = None) -> None:
        """Initialize event publisher.

        Args:
            config: Publisher configuration
        """
        self._config = config or EventPublisherConfig()
        self._client: Any = None  # NATSClient when available
        self._connected = False
        self._publish_count = 0
        self._error_count = 0
        logger.info("SmartCPEventPublisher initialized")

    async def connect(self) -> bool:
        """Connect to NATS server.

        Returns:
            True if connected successfully
        """
        if not NATS_AVAILABLE:
            logger.warning(
                "NATS library not available. Install with: pip install nats-py"
            )
            return False

        if not self._config.enabled:
            logger.info("Event publishing disabled")
            return False

        try:
            from nats.aio.client import Client as NATSClient

            self._client = NATSClient()
            await self._client.connect(
                servers=self._config.nats_servers,
                connect_timeout=self._config.connection_timeout,
                max_reconnect_attempts=self._config.max_reconnect_attempts,
            )
            self._connected = True
            logger.info(f"Connected to NATS: {self._config.nats_servers}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self._client and self._connected:
            try:
                await self._client.close()
            except Exception as e:
                logger.error(f"Error disconnecting from NATS: {e}")
            finally:
                self._connected = False
                self._client = None

        logger.info("Disconnected from NATS")

    async def __aenter__(self) -> "SmartCPEventPublisher":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if connected to NATS."""
        return self._connected and self._client is not None

    async def publish(self, event: SmartCPEvent) -> bool:
        """Publish an event to NATS.

        Args:
            event: Event to publish

        Returns:
            True if published successfully
        """
        if not self.is_connected:
            logger.debug("Not connected to NATS, skipping event publish")
            return False

        try:
            # Serialize event
            payload = event.to_json()

            # Check payload size
            if len(payload) > self._config.max_payload_size:
                logger.warning(
                    f"Event payload too large: {len(payload)} bytes "
                    f"(max: {self._config.max_payload_size})"
                )
                return False

            # Build subject
            subject = f"{self._config.subject_prefix}.{event.event_type.value}"

            # Publish to NATS
            await self._client.publish(subject, payload)
            self._publish_count += 1

            logger.debug(
                f"Published event: {event.event_type.value}",
                extra={"event_id": event.event_id, "subject": subject},
            )
            return True

        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to publish event: {e}")
            return False

    async def publish_tool_execution_started(
        self,
        user_id: str,
        tool_name: str,
        input_params: dict[str, Any],
    ) -> bool:
        """Publish tool execution started event.

        Args:
            user_id: User ID
            tool_name: Tool being executed
            input_params: Input parameters

        Returns:
            True if published
        """
        event = ToolExecutionEvent(
            event_type=SmartCPEventType.TOOL_EXECUTION_STARTED,
            user_id=user_id,
            tool_name=tool_name,
            input_params=input_params,
        )
        return await self.publish(event)

    async def publish_tool_execution_completed(
        self,
        user_id: str,
        tool_name: str,
        input_params: dict[str, Any],
        output: dict[str, Any],
        duration_ms: float,
    ) -> bool:
        """Publish tool execution completed event.

        Args:
            user_id: User ID
            tool_name: Tool executed
            input_params: Input parameters
            output: Tool output
            duration_ms: Execution duration

        Returns:
            True if published
        """
        event = ToolExecutionEvent(
            event_type=SmartCPEventType.TOOL_EXECUTION_COMPLETED,
            user_id=user_id,
            tool_name=tool_name,
            input_params=input_params,
            output=output,
            duration_ms=duration_ms,
        )
        return await self.publish(event)

    async def publish_tool_execution_failed(
        self,
        user_id: str,
        tool_name: str,
        input_params: dict[str, Any],
        error: str,
        duration_ms: float,
    ) -> bool:
        """Publish tool execution failed event.

        Args:
            user_id: User ID
            tool_name: Tool that failed
            input_params: Input parameters
            error: Error message
            duration_ms: Duration before failure

        Returns:
            True if published
        """
        event = ToolExecutionEvent(
            event_type=SmartCPEventType.TOOL_EXECUTION_FAILED,
            user_id=user_id,
            tool_name=tool_name,
            input_params=input_params,
            error=error,
            duration_ms=duration_ms,
        )
        return await self.publish(event)

    async def publish_memory_stored(
        self,
        user_id: str,
        key: str,
        memory_type: str,
        value_size: int,
        ttl: int | None = None,
    ) -> bool:
        """Publish memory stored event.

        Args:
            user_id: User ID
            key: Memory key
            memory_type: Type of memory
            value_size: Size of stored value
            ttl: Time-to-live

        Returns:
            True if published
        """
        event = MemoryEvent(
            event_type=SmartCPEventType.MEMORY_STORED,
            user_id=user_id,
            key=key,
            memory_type=memory_type,
            value_size=value_size,
            ttl=ttl,
        )
        return await self.publish(event)

    async def publish_memory_retrieved(
        self,
        user_id: str,
        key: str,
        memory_type: str,
        found: bool,
    ) -> bool:
        """Publish memory retrieved event.

        Args:
            user_id: User ID
            key: Memory key
            memory_type: Type of memory
            found: Whether the key was found

        Returns:
            True if published
        """
        event = MemoryEvent(
            event_type=SmartCPEventType.MEMORY_RETRIEVED,
            user_id=user_id,
            key=key,
            memory_type=memory_type,
            metadata={"found": found},
        )
        return await self.publish(event)

    async def publish_code_execution_completed(
        self,
        user_id: str,
        execution_id: str,
        language: str,
        code_length: int,
        status: str,
        duration_ms: float,
        variables_created: list[str] | None = None,
        error: str | None = None,
    ) -> bool:
        """Publish code execution completed event.

        Args:
            user_id: User ID
            execution_id: Execution ID
            language: Programming language
            code_length: Length of code
            status: Execution status
            duration_ms: Execution duration
            variables_created: Variables created
            error: Error message if failed

        Returns:
            True if published
        """
        event_type = (
            SmartCPEventType.CODE_EXECUTION_FAILED
            if error
            else SmartCPEventType.CODE_EXECUTION_COMPLETED
        )

        event = CodeExecutionEvent(
            event_type=event_type,
            user_id=user_id,
            execution_id=execution_id,
            language=language,
            code_length=code_length,
            status=status,
            duration_ms=duration_ms,
            variables_created=variables_created or [],
            error=error,
        )
        return await self.publish(event)

    async def publish_server_started(
        self,
        server_name: str,
        version: str,
        tools_registered: int,
    ) -> bool:
        """Publish server started event.

        Args:
            server_name: Server name
            version: Server version
            tools_registered: Number of tools registered

        Returns:
            True if published
        """
        event = SmartCPEvent(
            event_type=SmartCPEventType.SERVER_STARTED,
            user_id="system",
            metadata={
                "server_name": server_name,
                "version": version,
                "tools_registered": tools_registered,
            },
        )
        return await self.publish(event)

    async def publish_health_check(
        self,
        status: str,
        metrics: dict[str, Any],
    ) -> bool:
        """Publish health check event.

        Args:
            status: Health status
            metrics: Health metrics

        Returns:
            True if published
        """
        event = SmartCPEvent(
            event_type=SmartCPEventType.HEALTH_CHECK,
            user_id="system",
            metadata={
                "status": status,
                "metrics": metrics,
            },
        )
        return await self.publish(event)

    def get_stats(self) -> dict[str, Any]:
        """Get publisher statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "connected": self.is_connected,
            "enabled": self._config.enabled,
            "publish_count": self._publish_count,
            "error_count": self._error_count,
            "nats_servers": self._config.nats_servers,
        }


# Global event publisher instance (lazy initialized)
_event_publisher: SmartCPEventPublisher | None = None


def get_event_publisher(
    config: EventPublisherConfig | None = None,
) -> SmartCPEventPublisher:
    """Get or create the global event publisher.

    Args:
        config: Optional configuration

    Returns:
        SmartCPEventPublisher instance
    """
    global _event_publisher

    if _event_publisher is None:
        _event_publisher = SmartCPEventPublisher(config)

    return _event_publisher


async def init_event_publisher(
    config: EventPublisherConfig | None = None,
) -> SmartCPEventPublisher:
    """Initialize and connect the global event publisher.

    Args:
        config: Optional configuration

    Returns:
        Connected SmartCPEventPublisher
    """
    publisher = get_event_publisher(config)
    await publisher.connect()
    return publisher


async def close_event_publisher() -> None:
    """Close the global event publisher."""
    global _event_publisher

    if _event_publisher is not None:
        await _event_publisher.disconnect()
        _event_publisher = None
