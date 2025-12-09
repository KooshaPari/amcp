"""
GraphQL Subscription Client - Base client logic.

Provides core WebSocket connection management and subscription lifecycle.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class ConnectionState(str):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


class SubscriptionState(str):
    """Subscription lifecycle states."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class SubscriptionMessage:
    """GraphQL subscription message with JSON serialization."""

    def __init__(
        self,
        id: str,
        type: str,
        payload: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.type = type
        self.payload = payload

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {"id": self.id, "type": self.type}
        if self.payload:
            data["payload"] = self.payload
        return json.dumps(data)

    @classmethod
    def from_json(cls, data: str) -> "SubscriptionMessage":
        """Deserialize from JSON string."""
        parsed = json.loads(data)
        return cls(
            id=parsed.get("id", ""),
            type=parsed["type"],
            payload=parsed.get("payload")
        )


class Subscription:
    """Active subscription with metadata and state tracking."""

    def __init__(
        self,
        id: str,
        query: str,
        variables: Optional[Dict[str, Any]],
        handler: Any,
        state: str = SubscriptionState.PENDING
    ):
        self.id = id
        self.query = query
        self.variables = variables
        self.handler = handler
        self.state = state
        self.created_at = _utcnow()
        self.last_message_at: Optional[datetime] = None
        self.message_count = 0
        self.error: Optional[str] = None

    def to_subscribe_message(self) -> SubscriptionMessage:
        """Create subscription start message."""
        return SubscriptionMessage(
            id=self.id,
            type="subscribe",
            payload={
                "query": self.query,
                "variables": self.variables or {}
            }
        )


class ConnectionConfig:
    """GraphQL WebSocket connection configuration."""

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        subprotocol: str = "graphql-transport-ws",
        connection_timeout: float = 30.0,
        keep_alive_interval: float = 30.0,
        reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
        reconnect_delay_max: float = 60.0,
        max_queue_size: int = 1000
    ):
        self.url = url
        self.headers = headers or {}
        self.subprotocol = subprotocol
        self.connection_timeout = connection_timeout
        self.keep_alive_interval = keep_alive_interval
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.reconnect_delay_max = reconnect_delay_max
        self.max_queue_size = max_queue_size


class GraphQLSubscriptionClient:
    """
    GraphQL subscription client with WebSocket support.

    Implements graphql-transport-ws protocol for real-time subscriptions.
    Manages connection state, subscription lifecycle, and reconnection logic.
    """

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._state = ConnectionState.DISCONNECTED
        self._websocket: Optional[Any] = None
        self._subscriptions: Dict[str, Subscription] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._reconnect_count = 0
        self._connection_id: Optional[str] = None

    @property
    def state(self) -> str:
        """Current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._state == ConnectionState.CONNECTED

    @property
    def subscription_count(self) -> int:
        """Number of active subscriptions."""
        return len([s for s in self._subscriptions.values()
                   if s.state == SubscriptionState.ACTIVE])

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to GraphQL server.

        Returns True if connection successful.
        """
        if self._state == ConnectionState.CONNECTED:
            return True

        self._state = ConnectionState.CONNECTING
        logger.info(f"Connecting to {self.config.url}")

        try:
            # Import websockets lazily to avoid hard dependency
            try:
                import websockets
            except ImportError:
                logger.error("websockets package not installed")
                self._state = ConnectionState.DISCONNECTED
                return False

            self._websocket = await asyncio.wait_for(
                websockets.connect(
                    self.config.url,
                    subprotocols=[self.config.subprotocol],
                    extra_headers=self.config.headers
                ),
                timeout=self.config.connection_timeout
            )

            # Send connection init
            await self._send_message(SubscriptionMessage(
                id="",
                type="connection_init",
                payload={}
            ))

            # Wait for connection ack
            response = await asyncio.wait_for(
                self._receive_raw(),
                timeout=self.config.connection_timeout
            )

            if response.get("type") != "connection_ack":
                raise ConnectionError(f"Expected connection_ack, got {response.get('type')}")

            self._connection_id = str(uuid.uuid4())
            self._state = ConnectionState.CONNECTED
            self._reconnect_count = 0

            # Start background tasks
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())

            logger.info(f"Connected with ID {self._connection_id}")
            return True

        except asyncio.TimeoutError:
            logger.error("Connection timeout")
            self._state = ConnectionState.DISCONNECTED
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._state = ConnectionState.DISCONNECTED
            return False

    async def disconnect(self) -> None:
        """Close WebSocket connection gracefully."""
        if self._state == ConnectionState.DISCONNECTED:
            return

        logger.info("Disconnecting...")
        self._state = ConnectionState.CLOSED

        # Cancel background tasks
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass

        # Complete all subscriptions
        for sub_id in list(self._subscriptions.keys()):
            await self._complete_subscription(sub_id)

        # Close WebSocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        self._state = ConnectionState.DISCONNECTED
        logger.info("Disconnected")

    async def subscribe(
        self,
        query: str,
        handler: Any,
        variables: Optional[Dict[str, Any]] = None,
        subscription_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to GraphQL subscription.

        Args:
            query: GraphQL subscription query
            handler: Async callback for each message
            variables: Optional query variables
            subscription_id: Optional custom ID

        Returns:
            Subscription ID
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to GraphQL server")

        sub_id = subscription_id or str(uuid.uuid4())

        subscription = Subscription(
            id=sub_id,
            query=query,
            variables=variables,
            handler=handler
        )

        self._subscriptions[sub_id] = subscription

        # Send subscribe message
        await self._send_message(subscription.to_subscribe_message())

        subscription.state = SubscriptionState.ACTIVE
        logger.info(f"Subscribed: {sub_id}")

        return sub_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from subscription.

        Returns True if subscription existed and was removed.
        """
        if subscription_id not in self._subscriptions:
            return False

        # Send complete message
        await self._send_message(SubscriptionMessage(
            id=subscription_id,
            type="complete"
        ))

        await self._complete_subscription(subscription_id)
        logger.info(f"Unsubscribed: {subscription_id}")
        return True

    async def _send_message(self, message: SubscriptionMessage) -> None:
        """Send message to WebSocket."""
        if not self._websocket:
            raise ConnectionError("WebSocket not connected")

        await self._websocket.send(message.to_json())

    async def _receive_raw(self) -> Dict[str, Any]:
        """Receive raw message from WebSocket."""
        if not self._websocket:
            raise ConnectionError("WebSocket not connected")

        data = await self._websocket.recv()
        return json.loads(data)

    async def _receive_loop(self) -> None:
        """Background task to receive messages."""
        while self._state == ConnectionState.CONNECTED:
            try:
                message = await self._receive_raw()
                await self._handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                if self._state == ConnectionState.CONNECTED:
                    await self._handle_disconnect()
                break

    async def _keepalive_loop(self) -> None:
        """Background task for keepalive pings."""
        while self._state == ConnectionState.CONNECTED:
            try:
                await asyncio.sleep(self.config.keep_alive_interval)
                if self._websocket and self._state == ConnectionState.CONNECTED:
                    await self._send_message(SubscriptionMessage(
                        id="",
                        type="ping"
                    ))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Keepalive error: {e}")

    async def _complete_subscription(self, sub_id: str) -> None:
        """Mark subscription as completed and clean up."""
        subscription = self._subscriptions.pop(sub_id, None)
        if subscription:
            subscription.state = SubscriptionState.COMPLETED
            logger.debug(f"Subscription completed: {sub_id}")

    async def _handle_disconnect(self) -> None:
        """Handle unexpected disconnect and attempt reconnection."""
        if self._state == ConnectionState.CLOSED:
            return

        logger.warning("Connection lost, attempting reconnect...")
        self._state = ConnectionState.RECONNECTING

        for attempt in range(self.config.reconnect_attempts):
            delay = min(
                self.config.reconnect_delay * (2 ** attempt),
                self.config.reconnect_delay_max
            )
            logger.info(f"Reconnect attempt {attempt + 1} in {delay}s")
            await asyncio.sleep(delay)

            if await self.connect():
                # Resubscribe to active subscriptions
                await self._resubscribe_all()
                return

        logger.error("Reconnection failed, giving up")
        self._state = ConnectionState.DISCONNECTED

    async def _resubscribe_all(self) -> None:
        """Resubscribe to all active subscriptions after reconnect."""
        for subscription in list(self._subscriptions.values()):
            if subscription.state in (SubscriptionState.ACTIVE, SubscriptionState.PAUSED):
                await self._send_message(subscription.to_subscribe_message())
                subscription.state = SubscriptionState.ACTIVE
                logger.info(f"Resubscribed: {subscription.id}")

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        msg_type = message.get("type", "")
        msg_id = message.get("id", "")

        if msg_type == "next":
            await self._handle_subscription_data(msg_id, message.get("payload", {}))
        elif msg_type == "error":
            await self._handle_subscription_error(msg_id, message.get("payload", []))
        elif msg_type == "complete":
            await self._complete_subscription(msg_id)
        elif msg_type == "pong":
            pass
        elif msg_type == "ping":
            await self._send_message(SubscriptionMessage(id="", type="pong"))
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_subscription_data(
        self,
        sub_id: str,
        payload: Dict[str, Any]
    ) -> None:
        """Handle subscription data message."""
        subscription = self._subscriptions.get(sub_id)
        if not subscription:
            logger.warning(f"Data for unknown subscription: {sub_id}")
            return

        subscription.last_message_at = _utcnow()
        subscription.message_count += 1

        try:
            await subscription.handler(payload)
        except Exception as e:
            logger.error(f"Handler error for {sub_id}: {e}")

    async def _handle_subscription_error(
        self,
        sub_id: str,
        errors: list
    ) -> None:
        """Handle subscription error."""
        subscription = self._subscriptions.get(sub_id)
        if subscription:
            subscription.state = SubscriptionState.ERROR
            subscription.error = str(errors)
            logger.error(f"Subscription error {sub_id}: {errors}")
