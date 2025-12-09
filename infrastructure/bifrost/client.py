"""Core BifrostClient implementation."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from smartcp.services.bifrost.client import (
    GraphQLSubscriptionClient,
    ConnectionConfig,
)
from smartcp.services.bifrost.subscription_handler import SubscriptionHandler

from .queries import (
    QueryBuilder,
    QueryProcessor,
    RoutingDecision,
    SearchResult,
    ToolMetadata,
)
from .mutations import MutationBuilder, MutationProcessor, MutationFactory
from .subscriptions import SubscriptionBuilder, SubscriptionVariables

logger = logging.getLogger(__name__)


class BifrostClient(GraphQLSubscriptionClient):
    """
    GraphQL client for Bifrost backend integration.

    Extends GraphQLSubscriptionClient with query and mutation support.
    Provides high-level methods for routing, tool execution, and search.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        **kwargs,
    ):
        """
        Initialize BifrostClient.

        Args:
            url: Bifrost GraphQL URL (default: from BIFROST_URL env)
            api_key: API key for authentication (default: from BIFROST_API_KEY env)
            timeout: Request timeout in seconds
            **kwargs: Additional ConnectionConfig parameters
        """
        self.url = url or os.getenv("BIFROST_URL", "ws://localhost:4000/graphql")
        self.api_key = api_key or os.getenv("BIFROST_API_KEY", "")
        self.timeout = timeout

        # Build headers with auth
        headers = kwargs.get("headers", {})
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        kwargs["headers"] = headers

        # Initialize GraphQL subscription client
        config = ConnectionConfig(url=self.url, **kwargs)
        super().__init__(config)

        # HTTP client for queries/mutations
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._http_client = httpx.AsyncClient(
                timeout=self.timeout, headers=headers
            )
        return self._http_client

    async def close_http_client(self) -> None:
        """Close HTTP client if initialized."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def disconnect(self) -> None:
        """Override disconnect to close HTTP client."""
        await super().disconnect()
        await self.close_http_client()

    async def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables
            operation_name: Optional operation name

        Returns:
            Query result data

        Raises:
            httpx.HTTPError: On request failure
            ValueError: On GraphQL errors
        """
        http_url = self.url.replace("ws://", "http://").replace("wss://", "https://")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        try:
            response = await self.http_client.post(http_url, json=payload)
            response.raise_for_status()

            result = response.json()

            if "errors" in result:
                errors = result["errors"]
                error_msg = "; ".join(
                    e.get("message", str(e)) for e in errors
                )
                raise ValueError(f"GraphQL errors: {error_msg}")

            return result.get("data", {})

        except httpx.HTTPError as e:
            logger.error(f"Query failed: {e}")
            raise

    async def mutate(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute GraphQL mutation.

        Args:
            mutation: GraphQL mutation string
            variables: Mutation variables
            operation_name: Optional operation name

        Returns:
            Mutation result data

        Raises:
            httpx.HTTPError: On request failure
            ValueError: On GraphQL errors
        """
        return await self.query(mutation, variables, operation_name)

    # High-level API methods

    async def query_tools(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[ToolMetadata]:
        """
        Query available tools from Bifrost.

        Args:
            filters: Optional filters (category, tags, etc.)
            limit: Maximum number of tools to return

        Returns:
            List of tool metadata
        """
        query = QueryBuilder.tools_query(filters, limit)

        result = await self.query(
            query, variables={"filters": filters, "limit": limit}
        )

        return QueryProcessor.process_tools(result)

    async def query_tool(self, name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a specific tool.

        Args:
            name: Tool name

        Returns:
            Tool metadata if found, None otherwise
        """
        query = QueryBuilder.tool_query()

        result = await self.query(query, variables={"name": name})
        return QueryProcessor.process_tool(result)

    async def route_request(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Get routing decision from Bifrost.

        Args:
            prompt: User prompt to route
            context: Optional context (history, workspace, etc.)

        Returns:
            Routing decision with selected tool and confidence
        """
        query = QueryBuilder.route_query()

        result = await self.query(
            query, variables={"prompt": prompt, "context": context}
        )

        return QueryProcessor.process_routing_decision(result)

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Semantic search via Bifrost.

        Args:
            query: Search query
            limit: Maximum results
            filters: Optional filters (workspace, type, etc.)

        Returns:
            List of search results
        """
        gql_query = QueryBuilder.semantic_search_query()

        result = await self.query(
            gql_query,
            variables={"query": query, "limit": limit, "filters": filters},
        )

        return QueryProcessor.process_search_results(result)

    async def execute_tool(
        self, name: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool via Bifrost.

        Args:
            name: Tool name
            input_data: Tool input parameters

        Returns:
            Tool execution result
        """
        mutation = MutationBuilder.execute_tool_mutation()

        result = await self.mutate(
            mutation, variables={"name": name, "input": input_data}
        )

        return MutationProcessor.process_tool_execution(result)

    async def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Register new tool with Bifrost.

        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameter schema
            category: Optional category
            tags: Optional tags

        Returns:
            True if registration successful
        """
        mutation = MutationBuilder.register_tool_mutation()

        tool_input = MutationFactory.tool_input(
            name, description, parameters, category, tags
        )

        result = await self.mutate(
            mutation, variables={"tool": tool_input}
        )

        return MutationProcessor.process_tool_registration(result)

    # Subscription helpers (from GraphQLSubscriptionClient)

    async def subscribe_tool_events(
        self,
        tool_name: str,
        handler: SubscriptionHandler,
        workspace_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to tool execution events.

        Args:
            tool_name: Tool to monitor
            handler: Async callback for events
            workspace_id: Optional workspace filter

        Returns:
            Subscription ID
        """
        query = SubscriptionBuilder.tool_events_subscription()
        variables = SubscriptionVariables.tool_events_vars(
            tool_name, workspace_id
        )

        return await self.subscribe(query=query, handler=handler, variables=variables)

    async def subscribe_routing_events(
        self,
        handler: SubscriptionHandler,
        workspace_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to routing decision events.

        Args:
            handler: Async callback for events
            workspace_id: Optional workspace filter

        Returns:
            Subscription ID
        """
        query = SubscriptionBuilder.routing_events_subscription()
        variables = SubscriptionVariables.routing_events_vars(workspace_id)

        return await self.subscribe(query=query, handler=handler, variables=variables)
