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

from graphql_subscription_client import (
    GraphQLSubscriptionClient,
    SubscriptionBuilder,
    MCPSubscriptionBridge,
    SubscriptionState,
    ConnectionState,
    GraphQLMessage,
    SubscriptionConfig,
    ReconnectStrategy,
)


# ============================================================================
# GraphQLMessage Tests
# ============================================================================


class TestGraphQLMessage:
    """Test GraphQL message creation and parsing."""

    def test_connection_init_message(self):
        """Test connection init message structure."""
        msg = GraphQLMessage.connection_init({"Authorization": "Bearer token"})
        assert msg["type"] == "connection_init"
        assert msg["payload"]["Authorization"] == "Bearer token"

    def test_subscribe_message(self):
        """Test subscribe message structure."""
        msg = GraphQLMessage.subscribe(
            id="sub-1",
            query="subscription { updates { id } }",
            variables={"filter": "active"}
        )
        assert msg["type"] == "subscribe"
        assert msg["id"] == "sub-1"
        assert msg["payload"]["query"] == "subscription { updates { id } }"
        assert msg["payload"]["variables"]["filter"] == "active"

    def test_complete_message(self):
        """Test complete message structure."""
        msg = GraphQLMessage.complete(id="sub-1")
        assert msg["type"] == "complete"
        assert msg["id"] == "sub-1"

    def test_ping_message(self):
        """Test ping message structure."""
        msg = GraphQLMessage.ping()
        assert msg["type"] == "ping"


# ============================================================================
# SubscriptionConfig Tests
# ============================================================================


class TestSubscriptionConfig:
    """Test subscription configuration."""

    def test_default_config(self):
        """Test default subscription config values."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql"
        )
        assert config.endpoint == "wss://api.example.com/graphql"
        assert config.connection_timeout == 30.0
        assert config.heartbeat_interval == 30.0
        assert config.max_reconnect_attempts == 5

    def test_custom_config(self):
        """Test custom subscription config values."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql",
            connection_timeout=60.0,
            heartbeat_interval=15.0,
            max_reconnect_attempts=10,
            headers={"X-Custom": "header"}
        )
        assert config.connection_timeout == 60.0
        assert config.heartbeat_interval == 15.0
        assert config.max_reconnect_attempts == 10
        assert config.headers["X-Custom"] == "header"


# ============================================================================
# ReconnectStrategy Tests
# ============================================================================


class TestReconnectStrategy:
    """Test reconnection strategy."""

    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        strategy = ReconnectStrategy(
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0
        )

        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 2.0
        assert strategy.get_delay(2) == 4.0
        assert strategy.get_delay(3) == 8.0
        assert strategy.get_delay(4) == 16.0
        assert strategy.get_delay(5) == 30.0  # Capped at max_delay

    def test_jitter(self):
        """Test delay jitter for avoiding thundering herd."""
        strategy = ReconnectStrategy(
            base_delay=1.0,
            max_delay=30.0,
            jitter=0.1
        )

        # With jitter, delays should vary
        delays = [strategy.get_delay_with_jitter(1) for _ in range(10)]
        assert len(set(delays)) > 1  # Not all the same

    def test_should_reconnect(self):
        """Test reconnection decision logic."""
        strategy = ReconnectStrategy(max_attempts=3)

        assert strategy.should_reconnect(0) is True
        assert strategy.should_reconnect(1) is True
        assert strategy.should_reconnect(2) is True
        assert strategy.should_reconnect(3) is False


# ============================================================================
# SubscriptionBuilder Tests
# ============================================================================


class TestSubscriptionBuilder:
    """Test subscription query builder."""

    def test_basic_subscription(self):
        """Test basic subscription query building."""
        builder = SubscriptionBuilder("entityUpdates")
        query = builder.build()

        assert "subscription" in query
        assert "entityUpdates" in query

    def test_subscription_with_fields(self):
        """Test subscription with field selection."""
        builder = (
            SubscriptionBuilder("entityUpdates")
            .select("id", "name", "updatedAt")
        )
        query = builder.build()

        assert "id" in query
        assert "name" in query
        assert "updatedAt" in query

    def test_subscription_with_arguments(self):
        """Test subscription with arguments."""
        builder = (
            SubscriptionBuilder("entityUpdates")
            .arg("workspaceId", "$workspaceId", "ID!")
            .select("id", "name")
        )
        query = builder.build()

        assert "$workspaceId: ID!" in query
        assert "workspaceId: $workspaceId" in query

    def test_subscription_with_nested_fields(self):
        """Test subscription with nested field selection."""
        builder = (
            SubscriptionBuilder("entityUpdates")
            .select("id", "name")
            .nest("relationships", ["id", "type", "targetId"])
        )
        query = builder.build()

        assert "relationships" in query
        assert "targetId" in query


# ============================================================================
# GraphQLSubscriptionClient Tests
# ============================================================================


class TestGraphQLSubscriptionClient:
    """Test GraphQL subscription client."""

    @pytest.fixture
    def client(self):
        """Create subscription client for testing."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql",
            headers={"Authorization": "Bearer test-token"}
        )
        return GraphQLSubscriptionClient(config)

    def test_initial_state(self, client):
        """Test client initial state."""
        assert client.state == ConnectionState.DISCONNECTED
        assert len(client.subscriptions) == 0

    def test_generate_subscription_id(self, client):
        """Test unique subscription ID generation."""
        ids = [client._generate_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    @pytest.mark.asyncio
    async def test_subscription_handler_registration(self, client):
        """Test subscription handler registration."""
        handler = AsyncMock()

        # Mock WebSocket connection
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=json.dumps({
            "type": "connection_ack"
        }))

        with patch.object(client, '_connect_websocket', return_value=mock_ws):
            client._ws = mock_ws
            client._state = ConnectionState.CONNECTED

            sub_id = await client.subscribe(
                query="subscription { updates { id } }",
                handler=handler
            )

            assert sub_id is not None
            assert sub_id in client.subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe(self, client):
        """Test unsubscription removes handler."""
        handler = AsyncMock()

        # Setup mock subscription
        sub_id = "test-sub-1"
        client._subscriptions[sub_id] = {
            "handler": handler,
            "query": "subscription { updates { id } }",
            "state": SubscriptionState.ACTIVE
        }
        client._state = ConnectionState.CONNECTED

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        client._ws = mock_ws

        result = await client.unsubscribe(sub_id)

        assert result is True
        assert sub_id not in client._subscriptions


# ============================================================================
# SubscriptionState Tests
# ============================================================================


class TestSubscriptionState:
    """Test subscription state management."""

    def test_state_transitions(self):
        """Test valid subscription state values."""
        assert SubscriptionState.PENDING == "pending"
        assert SubscriptionState.ACTIVE == "active"
        assert SubscriptionState.COMPLETED == "completed"
        assert SubscriptionState.ERROR == "error"


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
# MCPSubscriptionBridge Tests
# ============================================================================


class TestMCPSubscriptionBridge:
    """Test MCP subscription bridge integration."""

    @pytest.fixture
    def bridge(self):
        """Create MCP subscription bridge for testing."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql"
        )
        client = GraphQLSubscriptionClient(config)
        return MCPSubscriptionBridge(client)

    def test_bridge_initialization(self, bridge):
        """Test bridge initialization."""
        assert bridge.client is not None
        assert len(bridge.mcp_handlers) == 0

    @pytest.mark.asyncio
    async def test_register_mcp_handler(self, bridge):
        """Test MCP handler registration."""
        async def entity_handler(event: dict) -> dict:
            return {"processed": True, "event": event}

        bridge.register_handler("entity_updates", entity_handler)
        assert "entity_updates" in bridge.mcp_handlers

    @pytest.mark.asyncio
    async def test_handler_invocation(self, bridge):
        """Test handler is invoked correctly."""
        received_events = []

        async def capture_handler(event: dict) -> dict:
            received_events.append(event)
            return {"captured": True}

        bridge.register_handler("test_events", capture_handler)

        # Simulate event dispatch
        test_event = {"id": "1", "type": "created"}
        await bridge._dispatch_event("test_events", test_event)

        assert len(received_events) == 1
        assert received_events[0]["id"] == "1"


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create client for error testing."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql"
        )
        return GraphQLSubscriptionClient(config)

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, client):
        """Test connection error is handled gracefully."""
        with patch.object(client, '_connect_websocket', side_effect=Exception("Connection failed")):
            result = await client.connect()
            assert result is False
            assert client.state in (ConnectionState.DISCONNECTED, ConnectionState.RECONNECTING)

    @pytest.mark.asyncio
    async def test_subscription_error_callback(self, client):
        """Test error callback is invoked on subscription error."""
        error_received = []

        async def error_handler(error: Exception):
            error_received.append(str(error))

        client.on_error(error_handler)

        # Simulate error
        await client._handle_error(Exception("Test error"))

        assert len(error_received) == 1
        assert "Test error" in error_received[0]


# ============================================================================
# Message Parsing Tests
# ============================================================================


class TestMessageParsing:
    """Test GraphQL message parsing."""

    @pytest.fixture
    def client(self):
        """Create client for message testing."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql"
        )
        return GraphQLSubscriptionClient(config)

    def test_parse_next_message(self, client):
        """Test parsing next message type."""
        message = {
            "type": "next",
            "id": "sub-1",
            "payload": {
                "data": {"entityUpdates": {"id": "1", "name": "Test"}}
            }
        }

        msg_type, sub_id, payload = client._parse_message(message)

        assert msg_type == "next"
        assert sub_id == "sub-1"
        assert payload["data"]["entityUpdates"]["id"] == "1"

    def test_parse_error_message(self, client):
        """Test parsing error message type."""
        message = {
            "type": "error",
            "id": "sub-1",
            "payload": [{"message": "Query failed"}]
        }

        msg_type, sub_id, payload = client._parse_message(message)

        assert msg_type == "error"
        assert sub_id == "sub-1"

    def test_parse_complete_message(self, client):
        """Test parsing complete message type."""
        message = {
            "type": "complete",
            "id": "sub-1"
        }

        msg_type, sub_id, payload = client._parse_message(message)

        assert msg_type == "complete"
        assert sub_id == "sub-1"


# ============================================================================
# Integration Tests
# ============================================================================


class TestSubscriptionIntegration:
    """Integration tests for subscription workflows."""

    @pytest.mark.asyncio
    async def test_full_subscription_lifecycle(self):
        """Test complete subscription lifecycle."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql"
        )
        client = GraphQLSubscriptionClient(config)

        events_received = []

        async def event_handler(data: dict):
            events_received.append(data)

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()

        # Simulate message sequence
        messages = [
            json.dumps({"type": "connection_ack"}),
            json.dumps({
                "type": "next",
                "id": "sub-1",
                "payload": {"data": {"updates": {"id": "1"}}}
            }),
        ]
        mock_ws.recv = AsyncMock(side_effect=messages)
        mock_ws.close = AsyncMock()

        with patch.object(client, '_connect_websocket', return_value=mock_ws):
            # Connect
            client._ws = mock_ws
            client._state = ConnectionState.CONNECTED

            # Subscribe
            client._subscriptions["sub-1"] = {
                "handler": event_handler,
                "query": "subscription { updates { id } }",
                "state": SubscriptionState.ACTIVE
            }

            # Process one message
            await client._process_message(json.loads(messages[1]))

            assert len(events_received) == 1

    @pytest.mark.asyncio
    async def test_reconnection_restores_subscriptions(self):
        """Test that reconnection restores active subscriptions."""
        config = SubscriptionConfig(
            endpoint="wss://api.example.com/graphql",
            max_reconnect_attempts=3
        )
        client = GraphQLSubscriptionClient(config)

        # Setup existing subscription
        client._subscriptions["sub-1"] = {
            "handler": AsyncMock(),
            "query": "subscription { updates { id } }",
            "variables": {},
            "state": SubscriptionState.ACTIVE
        }

        # Verify subscription exists before reconnect
        assert "sub-1" in client._subscriptions

        # Get subscriptions to restore
        subs_to_restore = client._get_subscriptions_to_restore()
        assert len(subs_to_restore) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
