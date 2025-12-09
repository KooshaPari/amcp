"""
MCP subscription bridge and message queue for GraphQL subscriptions.

Provides integration with MCP tool events and message queue with backpressure.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MessageQueue:
    """Async message queue with backpressure handling."""

    def __init__(self, max_size: int = 1000):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._max_size = max_size
        self._dropped_count = 0

    async def put(self, message: Dict[str, Any]) -> bool:
        """Add message to queue, returns False if dropped."""
        try:
            self._queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            self._dropped_count += 1
            logger.warning(f"Message queue full, dropped {self._dropped_count} messages")
            return False

    async def get(self) -> Dict[str, Any]:
        """Get next message from queue."""
        return await self._queue.get()

    def qsize(self) -> int:
        """Current queue size."""
        return self._queue.qsize()

    @property
    def dropped_count(self) -> int:
        """Number of dropped messages."""
        return self._dropped_count


class MCPSubscriptionBridge:
    """Bridge between GraphQL subscriptions and MCP tool events."""

    def __init__(self, client: "GraphQLSubscriptionClient"):
        self.client = client
        self._mcp_handlers: Dict[str, Callable] = {}

    def register_mcp_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register handler for MCP event type."""
        self._mcp_handlers[event_type] = handler

    async def subscribe_to_tool_events(
        self,
        tool_name: str,
        workspace_id: Optional[str] = None
    ) -> str:
        """Subscribe to MCP tool execution events."""
        query = """
            subscription ToolEvents($toolName: String!, $workspaceId: ID) {
                toolExecuted(toolName: $toolName, workspaceId: $workspaceId) {
                    id
                    toolName
                    input
                    output
                    status
                    executedAt
                    duration
                }
            }
        """

        async def handler(payload: Dict[str, Any]) -> None:
            event_data = payload.get("data", {}).get("toolExecuted", {})
            mcp_handler = self._mcp_handlers.get("tool_executed")
            if mcp_handler:
                mcp_handler(event_data)

        return await self.client.subscribe(
            query=query,
            handler=handler,
            variables={"toolName": tool_name, "workspaceId": workspace_id}
        )

    async def subscribe_to_entity_changes(
        self,
        entity_type: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> str:
        """Subscribe to entity change events."""
        query = """
            subscription EntityChanges($entityType: String, $workspaceId: ID) {
                entityChanged(entityType: $entityType, workspaceId: $workspaceId) {
                    id
                    entityType
                    operation
                    entity {
                        id
                        name
                        metadata
                    }
                    changedAt
                }
            }
        """

        async def handler(payload: Dict[str, Any]) -> None:
            event_data = payload.get("data", {}).get("entityChanged", {})
            mcp_handler = self._mcp_handlers.get("entity_changed")
            if mcp_handler:
                mcp_handler(event_data)

        return await self.client.subscribe(
            query=query,
            handler=handler,
            variables={"entityType": entity_type, "workspaceId": workspace_id}
        )

    async def subscribe_to_workflow_progress(
        self,
        workflow_id: str
    ) -> str:
        """Subscribe to workflow execution progress."""
        query = """
            subscription WorkflowProgress($workflowId: ID!) {
                workflowProgress(workflowId: $workflowId) {
                    workflowId
                    stepId
                    status
                    progress
                    message
                    updatedAt
                }
            }
        """

        async def handler(payload: Dict[str, Any]) -> None:
            event_data = payload.get("data", {}).get("workflowProgress", {})
            mcp_handler = self._mcp_handlers.get("workflow_progress")
            if mcp_handler:
                mcp_handler(event_data)

        return await self.client.subscribe(
            query=query,
            handler=handler,
            variables={"workflowId": workflow_id}
        )
