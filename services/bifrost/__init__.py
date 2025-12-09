"""
GraphQL Subscription Client for Bifrost.

Provides WebSocket-based GraphQL subscription support with:
- Automatic reconnection with exponential backoff
- Subscription multiplexing over single connection
- Message queue with backpressure handling
- Type-safe subscription handlers
- Integration with FastMCP event system
- Fluent builder API
- MCP bridge for tool event subscriptions

Supports graphql-ws protocol (subscriptions-transport-ws deprecated).
"""

from .client import (
    GraphQLSubscriptionClient,
    ConnectionConfig,
    Subscription,
    SubscriptionMessage,
    SubscriptionState,
    ConnectionState,
)
from .subscription_handler import (
    SubscriptionBuilder,
    SubscriptionHandler,
    subscription_client,
)
from .message_handlers import (
    MessageQueue,
    MCPSubscriptionBridge,
)

__all__ = [
    # Client
    "GraphQLSubscriptionClient",
    "ConnectionConfig",
    "Subscription",
    "SubscriptionMessage",
    "SubscriptionState",
    "ConnectionState",
    # Subscription handling
    "SubscriptionBuilder",
    "SubscriptionHandler",
    "subscription_client",
    # Message handling
    "MessageQueue",
    "MCPSubscriptionBridge",
]
