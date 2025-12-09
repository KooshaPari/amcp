"""Bifrost GraphQL client module."""

from .client import BifrostClient
from .errors import BifrostError, ConnectionError, GraphQLError, TimeoutError, ValidationError
from .queries import QueryBuilder, QueryProcessor, RoutingDecision, SearchResult, ToolMetadata
from .mutations import MutationBuilder, MutationFactory, MutationProcessor
from .subscriptions import SubscriptionBuilder, SubscriptionVariables

__all__ = [
    "BifrostClient",
    "BifrostError",
    "ConnectionError",
    "GraphQLError",
    "TimeoutError",
    "ValidationError",
    "QueryBuilder",
    "QueryProcessor",
    "MutationBuilder",
    "MutationFactory",
    "MutationProcessor",
    "SubscriptionBuilder",
    "SubscriptionVariables",
    "RoutingDecision",
    "SearchResult",
    "ToolMetadata",
]


async def bifrost_client(
    url: str = None,
    api_key: str = None,
    **kwargs,
):
    """
    Create BifrostClient context manager.

    Example:
        async with bifrost_client() as client:
            tools = await client.query_tools()
    """
    client = BifrostClient(url=url, api_key=api_key, **kwargs)
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()
