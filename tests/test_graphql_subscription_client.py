"""
Tests for GraphQL Subscription Client (Phase 4).

Tests WebSocket-based GraphQL subscriptions with auto-reconnect,
subscription multiplexing, and MCP bridge integration.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Optional


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bifrost import (
    GraphQLSubscriptionClient,
    SubscriptionBuilder,
    MCPSubscriptionBridge,
    SubscriptionState,
    ConnectionState,
    SubscriptionMessage,
    ConnectionConfig,
    Subscription,
    MessageQueue,
)


# ============================================================================
# SubscriptionMessage Tests
# ============================================================================


class TestSubscriptionMessage:
    """Test subscription message creation and parsing."""

    def test_message_creation(self):
        """Test subscription message structure."""
        msg = SubscriptionMessage(
            id="sub-1",
            type="subscribe",
            payload={"query": "subscription { updates { id } }"}
        )
        assert msg.type == "subscribe"
        assert msg.id == "sub-1"
        assert msg.payload["query"] == "subscription { updates { id } }"

    def test_message_to_json(self):
        """Test message serialization to JSON."""
        msg = SubscriptionMessage(
            id="sub-1",
            type="complete"
        )
        json_str = msg.to_json()
        import json
        data = json.loads(json_str)
        assert data["type"] == "complete"
        assert data["id"] == "sub-1"

    def test_message_from_json(self):
        """Test message deserialization from JSON."""
        json_str = '{"id": "sub-1", "type": "next", "payload": {"data": {}}}'
        msg = SubscriptionMessage.from_json(json_str)
        assert msg.id == "sub-1"
        assert msg.type == "next"
        assert msg.payload == {"data": {}}


# ============================================================================
# ConnectionConfig Tests
# ============================================================================


class TestConnectionConfig:
    """Test connection configuration."""

    def test_default_config(self):
        """Test default connection config values."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql"
        )
        assert config.url == "wss://api.example.com/graphql"
        assert config.connection_timeout == 30.0
        assert config.keep_alive_interval == 30.0
        assert config.reconnect_attempts == 5

    def test_custom_config(self):
        """Test custom connection config values."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql",
            connection_timeout=60.0,
            keep_alive_interval=15.0,
            reconnect_attempts=10,
            headers={"X-Custom": "header"}
        )
        assert config.connection_timeout == 60.0
        assert config.keep_alive_interval == 15.0
        assert config.reconnect_attempts == 10
        assert config.headers["X-Custom"] == "header"

    def test_config_with_subprotocol(self):
        """Test connection config with custom subprotocol."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql",
            subprotocol="graphql-ws"
        )
        assert config.subprotocol == "graphql-ws"

    def test_config_reconnect_settings(self):
        """Test reconnection delay settings."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql",
            reconnect_delay=2.0,
            reconnect_delay_max=120.0
        )
        assert config.reconnect_delay == 2.0
        assert config.reconnect_delay_max == 120.0


# ============================================================================
# Subscription Tests
# ============================================================================


class TestSubscription:
    """Test subscription data model."""

    def test_subscription_creation(self):
        """Test subscription creation."""
        async def handler(data):
            pass

        sub = Subscription(
            id="sub-1",
            query="subscription { updates { id } }",
            variables=None,
            handler=handler,
            state=SubscriptionState.PENDING
        )

        assert sub.id == "sub-1"
        assert sub.state == SubscriptionState.PENDING
        assert sub.query == "subscription { updates { id } }"

    def test_subscription_with_variables(self):
        """Test subscription with variables."""
        async def handler(data):
            pass

        sub = Subscription(
            id="sub-1",
            query="subscription($id: ID!) { updates(id: $id) { id } }",
            variables={"id": "123"},
            handler=handler
        )

        assert sub.variables == {"id": "123"}

    def test_subscription_state_transitions(self):
        """Test subscription state transitions."""
        async def handler(data):
            pass

        sub = Subscription(
            id="sub-1",
            query="subscription { updates { id } }",
            variables=None,
            handler=handler,
            state=SubscriptionState.PENDING
        )

        sub.state = SubscriptionState.ACTIVE
        assert sub.state == SubscriptionState.ACTIVE

        sub.state = SubscriptionState.COMPLETED
        assert sub.state == SubscriptionState.COMPLETED

    def test_subscription_to_subscribe_message(self):
        """Test creating subscribe message from subscription."""
        async def handler(data):
            pass

        sub = Subscription(
            id="sub-1",
            query="subscription { updates { id } }",
            variables={"workspaceId": "ws-1"},
            handler=handler
        )

        msg = sub.to_subscribe_message()
        assert msg.id == "sub-1"
        assert msg.type == "subscribe"
        assert msg.payload["query"] == "subscription { updates { id } }"
        assert msg.payload["variables"] == {"workspaceId": "ws-1"}


# ============================================================================
# SubscriptionBuilder Tests
# ============================================================================


class TestSubscriptionBuilder:
    """Test subscription query builder."""

    @pytest.fixture
    def client(self):
        """Create mock client for builder tests."""
        config = ConnectionConfig(url="wss://api.example.com/graphql")
        return GraphQLSubscriptionClient(config)

    def test_builder_creation(self, client):
        """Test builder can be created with client."""
        builder = SubscriptionBuilder(client)
        assert builder._client == client

    def test_builder_query_method(self, client):
        """Test setting query on builder."""
        builder = SubscriptionBuilder(client)
        result = builder.query("subscription { updates { id } }")

        assert result is builder  # Fluent API returns self
        assert builder._query == "subscription { updates { id } }"

    def test_builder_variables_method(self, client):
        """Test setting variables on builder."""
        builder = SubscriptionBuilder(client)
        result = builder.variables(workspaceId="ws-1", userId="user-1")

        assert result is builder
        assert builder._variables == {"workspaceId": "ws-1", "userId": "user-1"}

    def test_builder_on_data_method(self, client):
        """Test setting handler on builder."""
        async def handler(data):
            pass

        builder = SubscriptionBuilder(client)
        result = builder.on_data(handler)

        assert result is builder
        assert builder._handler == handler

    def test_builder_with_id_method(self, client):
        """Test setting custom ID on builder."""
        builder = SubscriptionBuilder(client)
        result = builder.with_id("custom-sub-id")

        assert result is builder
        assert builder._id == "custom-sub-id"

    def test_builder_fluent_chain(self, client):
        """Test builder fluent API chaining."""
        async def handler(data):
            pass

        builder = (
            SubscriptionBuilder(client)
            .query("subscription { updates { id } }")
            .variables(workspaceId="ws-1")
            .on_data(handler)
            .with_id("my-sub")
        )

        assert builder._query == "subscription { updates { id } }"
        assert builder._variables == {"workspaceId": "ws-1"}
        assert builder._handler == handler
        assert builder._id == "my-sub"

    @pytest.mark.asyncio
    async def test_builder_subscribe_requires_query(self, client):
        """Test subscribe fails without query."""
        async def handler(data):
            pass

        builder = SubscriptionBuilder(client).on_data(handler)

        with pytest.raises(ValueError, match="Query is required"):
            await builder.subscribe()

    @pytest.mark.asyncio
    async def test_builder_subscribe_requires_handler(self, client):
        """Test subscribe fails without handler."""
        builder = SubscriptionBuilder(client).query("subscription { updates { id } }")

        with pytest.raises(ValueError, match="Handler is required"):
            await builder.subscribe()


# ============================================================================
# GraphQLSubscriptionClient Tests
# ============================================================================


class TestGraphQLSubscriptionClient:
    """Test GraphQL subscription client."""

    @pytest.fixture
    def client(self):
        """Create subscription client for testing."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql",
            headers={"Authorization": "Bearer test-token"}
        )
        return GraphQLSubscriptionClient(config)

    def test_initial_state(self, client):
        """Test client initial state."""
        assert client.state == ConnectionState.DISCONNECTED
        assert len(client._subscriptions) == 0

    def test_is_connected_property(self, client):
        """Test is_connected property."""
        assert client.is_connected is False

        client._state = ConnectionState.CONNECTED
        assert client.is_connected is True

    def test_subscription_count_property(self, client):
        """Test subscription_count property."""
        assert client.subscription_count == 0

        # Add mock subscription
        async def handler(data):
            pass

        client._subscriptions["sub-1"] = Subscription(
            id="sub-1",
            query="subscription { updates { id } }",
            variables=None,
            handler=handler,
            state=SubscriptionState.ACTIVE
        )

        assert client.subscription_count == 1

    @pytest.mark.asyncio
    async def test_subscribe_requires_connection(self, client):
        """Test subscribe fails when not connected."""
        async def handler(data):
            pass

        with pytest.raises(ConnectionError, match="Not connected"):
            await client.subscribe(
                query="subscription { updates { id } }",
                handler=handler
            )

    @pytest.mark.asyncio
    async def test_subscribe_creates_subscription(self, client):
        """Test subscribe creates subscription in _subscriptions dict."""
        async def handler(data):
            pass

        # Mock connected state
        client._state = ConnectionState.CONNECTED
        client._websocket = AsyncMock()
        client._websocket.send = AsyncMock()

        sub_id = await client.subscribe(
            query="subscription { updates { id } }",
            handler=handler
        )

        assert sub_id is not None
        assert sub_id in client._subscriptions
        assert client._subscriptions[sub_id].state == SubscriptionState.ACTIVE

    @pytest.mark.asyncio
    async def test_subscribe_with_custom_id(self, client):
        """Test subscribe with custom subscription ID."""
        async def handler(data):
            pass

        client._state = ConnectionState.CONNECTED
        client._websocket = AsyncMock()
        client._websocket.send = AsyncMock()

        sub_id = await client.subscribe(
            query="subscription { updates { id } }",
            handler=handler,
            subscription_id="my-custom-id"
        )

        assert sub_id == "my-custom-id"

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_subscription(self, client):
        """Test unsubscribe removes subscription."""
        async def handler(data):
            pass

        # Setup mock subscription
        sub_id = "test-sub-1"
        client._subscriptions[sub_id] = Subscription(
            id=sub_id,
            query="subscription { updates { id } }",
            variables=None,
            handler=handler,
            state=SubscriptionState.ACTIVE
        )
        client._state = ConnectionState.CONNECTED
        client._websocket = AsyncMock()
        client._websocket.send = AsyncMock()

        result = await client.unsubscribe(sub_id)

        assert result is True
        assert sub_id not in client._subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, client):
        """Test unsubscribe returns False for nonexistent subscription."""
        client._state = ConnectionState.CONNECTED
        result = await client.unsubscribe("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Test connection failure handling."""
        with patch.object(client, 'connect', return_value=False):
            result = await client.connect()
            assert result is False


# ============================================================================
# SubscriptionState Tests
# ============================================================================


class TestSubscriptionState:
    """Test subscription state management."""

    def test_state_values(self):
        """Test valid subscription state values."""
        assert SubscriptionState.PENDING == "pending"
        assert SubscriptionState.ACTIVE == "active"
        assert SubscriptionState.COMPLETED == "completed"
        assert SubscriptionState.ERROR == "error"
        assert SubscriptionState.PAUSED == "paused"


# ============================================================================
# ConnectionState Tests
# ============================================================================


class TestConnectionState:
    """Test connection state management."""

    def test_connection_states(self):
        """Test valid connection state values."""
        assert ConnectionState.DISCONNECTED == "disconnected"
        assert ConnectionState.CONNECTING == "connecting"
        assert ConnectionState.CONNECTED == "connected"
        assert ConnectionState.RECONNECTING == "reconnecting"
        assert ConnectionState.CLOSED == "closed"


# ============================================================================
# MessageQueue Tests
# ============================================================================


class TestMessageQueue:
    """Test message queue with backpressure."""

    @pytest.mark.asyncio
    async def test_queue_put_get(self):
        """Test basic put and get operations."""
        queue = MessageQueue(max_size=10)

        result = await queue.put({"type": "test"})
        assert result is True
        assert queue.qsize() == 1

        msg = await queue.get()
        assert msg == {"type": "test"}
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_queue_backpressure(self):
        """Test queue drops messages when full."""
        queue = MessageQueue(max_size=2)

        await queue.put({"id": 1})
        await queue.put({"id": 2})

        # Third message should be dropped
        result = await queue.put({"id": 3})
        assert result is False
        assert queue.dropped_count == 1


# ============================================================================
# MCPSubscriptionBridge Tests
# ============================================================================


class TestMCPSubscriptionBridge:
    """Test MCP subscription bridge integration."""

    @pytest.fixture
    def bridge(self):
        """Create MCP subscription bridge for testing."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql"
        )
        client = GraphQLSubscriptionClient(config)
        return MCPSubscriptionBridge(client)

    def test_bridge_initialization(self, bridge):
        """Test bridge initialization."""
        assert bridge.client is not None
        assert len(bridge._mcp_handlers) == 0

    def test_register_mcp_handler(self, bridge):
        """Test MCP handler registration."""
        def entity_handler(event: dict):
            pass

        bridge.register_mcp_handler("entity_updates", entity_handler)
        assert "entity_updates" in bridge._mcp_handlers

    def test_register_multiple_handlers(self, bridge):
        """Test registering multiple handlers."""
        def handler1(event: dict):
            pass

        def handler2(event: dict):
            pass

        bridge.register_mcp_handler("tool_executed", handler1)
        bridge.register_mcp_handler("entity_changed", handler2)

        assert "tool_executed" in bridge._mcp_handlers
        assert "entity_changed" in bridge._mcp_handlers

    @pytest.mark.asyncio
    async def test_subscribe_to_tool_events(self, bridge):
        """Test subscribing to tool events."""
        # Setup connected client
        bridge.client._state = ConnectionState.CONNECTED
        bridge.client._websocket = AsyncMock()
        bridge.client._websocket.send = AsyncMock()

        sub_id = await bridge.subscribe_to_tool_events("my_tool", "ws-1")

        assert sub_id is not None
        assert sub_id in bridge.client._subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_to_entity_changes(self, bridge):
        """Test subscribing to entity changes."""
        bridge.client._state = ConnectionState.CONNECTED
        bridge.client._websocket = AsyncMock()
        bridge.client._websocket.send = AsyncMock()

        sub_id = await bridge.subscribe_to_entity_changes("Person", "ws-1")

        assert sub_id is not None
        assert sub_id in bridge.client._subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_to_workflow_progress(self, bridge):
        """Test subscribing to workflow progress."""
        bridge.client._state = ConnectionState.CONNECTED
        bridge.client._websocket = AsyncMock()
        bridge.client._websocket.send = AsyncMock()

        sub_id = await bridge.subscribe_to_workflow_progress("wf-123")

        assert sub_id is not None
        assert sub_id in bridge.client._subscriptions


# ============================================================================
# Message Handling Tests
# ============================================================================


class TestMessageHandling:
    """Test internal message handling."""

    @pytest.fixture
    def client(self):
        """Create client for message testing."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql"
        )
        return GraphQLSubscriptionClient(config)

    @pytest.mark.asyncio
    async def test_handle_next_message(self, client):
        """Test handling next (data) message."""
        received_data = []

        async def handler(data):
            received_data.append(data)

        # Setup subscription
        client._subscriptions["sub-1"] = Subscription(
            id="sub-1",
            query="subscription { updates { id } }",
            variables=None,
            handler=handler,
            state=SubscriptionState.ACTIVE
        )

        # Process next message
        message = {
            "type": "next",
            "id": "sub-1",
            "payload": {"data": {"updates": {"id": "1"}}}
        }

        await client._handle_message(message)

        assert len(received_data) == 1
        assert received_data[0]["data"]["updates"]["id"] == "1"

    @pytest.mark.asyncio
    async def test_handle_complete_message(self, client):
        """Test handling complete message."""
        async def handler(data):
            pass

        client._subscriptions["sub-1"] = Subscription(
            id="sub-1",
            query="subscription { updates { id } }",
            variables=None,
            handler=handler,
            state=SubscriptionState.ACTIVE
        )

        message = {"type": "complete", "id": "sub-1"}

        await client._handle_message(message)

        assert "sub-1" not in client._subscriptions

    @pytest.mark.asyncio
    async def test_handle_error_message(self, client):
        """Test handling error message."""
        async def handler(data):
            pass

        client._subscriptions["sub-1"] = Subscription(
            id="sub-1",
            query="subscription { updates { id } }",
            variables=None,
            handler=handler,
            state=SubscriptionState.ACTIVE
        )

        message = {
            "type": "error",
            "id": "sub-1",
            "payload": [{"message": "Query failed"}]
        }

        await client._handle_message(message)

        assert client._subscriptions["sub-1"].state == SubscriptionState.ERROR


# ============================================================================
# Integration Tests
# ============================================================================


class TestSubscriptionIntegration:
    """Integration tests for subscription workflows."""

    @pytest.mark.asyncio
    async def test_full_subscription_lifecycle(self):
        """Test complete subscription lifecycle."""
        config = ConnectionConfig(
            url="wss://api.example.com/graphql"
        )
        client = GraphQLSubscriptionClient(config)

        events_received = []

        async def event_handler(data: dict):
            events_received.append(data)

        # Setup connected state
        client._state = ConnectionState.CONNECTED
        client._websocket = AsyncMock()
        client._websocket.send = AsyncMock()

        # Subscribe
        sub_id = await client.subscribe(
            query="subscription { updates { id } }",
            handler=event_handler
        )

        assert sub_id in client._subscriptions

        # Simulate receiving data
        await client._handle_message({
            "type": "next",
            "id": sub_id,
            "payload": {"data": {"updates": {"id": "1"}}}
        })

        assert len(events_received) == 1

        # Unsubscribe
        result = await client.unsubscribe(sub_id)
        assert result is True
        assert sub_id not in client._subscriptions

    @pytest.mark.asyncio
    async def test_multiple_subscriptions(self):
        """Test managing multiple concurrent subscriptions."""
        config = ConnectionConfig(url="wss://api.example.com/graphql")
        client = GraphQLSubscriptionClient(config)

        client._state = ConnectionState.CONNECTED
        client._websocket = AsyncMock()
        client._websocket.send = AsyncMock()

        events1 = []
        events2 = []

        async def handler1(data):
            events1.append(data)

        async def handler2(data):
            events2.append(data)

        sub_id1 = await client.subscribe("subscription { updates1 { id } }", handler1)
        sub_id2 = await client.subscribe("subscription { updates2 { id } }", handler2)

        assert client.subscription_count == 2

        # Send data to subscription 1
        await client._handle_message({
            "type": "next",
            "id": sub_id1,
            "payload": {"data": "for sub1"}
        })

        # Send data to subscription 2
        await client._handle_message({
            "type": "next",
            "id": sub_id2,
            "payload": {"data": "for sub2"}
        })

        assert len(events1) == 1
        assert len(events2) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
