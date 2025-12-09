"""
Subscription handler and builder for GraphQL subscriptions.

Provides fluent builder for creating subscriptions and context manager support.
"""

from contextlib import asynccontextmanager
from typing import Any, Callable, Coroutine, Dict, Optional

# Type variables for generic subscription handling
SubscriptionHandler = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]


class SubscriptionBuilder:
    """Fluent builder for creating subscriptions."""

    def __init__(self, client: "GraphQLSubscriptionClient"):
        self._client = client
        self._query: Optional[str] = None
        self._variables: Dict[str, Any] = {}
        self._handler: Optional[SubscriptionHandler] = None
        self._id: Optional[str] = None

    def query(self, query: str) -> "SubscriptionBuilder":
        """Set subscription query."""
        self._query = query
        return self

    def variables(self, **kwargs: Any) -> "SubscriptionBuilder":
        """Set query variables."""
        self._variables.update(kwargs)
        return self

    def on_data(self, handler: SubscriptionHandler) -> "SubscriptionBuilder":
        """Set data handler."""
        self._handler = handler
        return self

    def with_id(self, subscription_id: str) -> "SubscriptionBuilder":
        """Set custom subscription ID."""
        self._id = subscription_id
        return self

    async def subscribe(self) -> str:
        """Execute subscription."""
        if not self._query:
            raise ValueError("Query is required")
        if not self._handler:
            raise ValueError("Handler is required")

        return await self._client.subscribe(
            query=self._query,
            handler=self._handler,
            variables=self._variables or None,
            subscription_id=self._id
        )


@asynccontextmanager
async def subscription_client(config: "ConnectionConfig"):
    """
    Context manager for GraphQL subscription client.

    Example:
        async with subscription_client(config) as client:
            await client.subscribe(query, handler)
    """
    # Import here to avoid circular dependency
    from .client import GraphQLSubscriptionClient

    client = GraphQLSubscriptionClient(config)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()
