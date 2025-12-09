"""GraphQL subscription builders for BifrostClient."""

from typing import Optional


class SubscriptionBuilder:
    """Builder for GraphQL subscription operations."""

    @staticmethod
    def tool_events_subscription() -> str:
        """Build tool execution events subscription."""
        return """
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

    @staticmethod
    def routing_events_subscription() -> str:
        """Build routing decision events subscription."""
        return """
            subscription RoutingEvents($workspaceId: ID) {
                routingDecision(workspaceId: $workspaceId) {
                    id
                    prompt
                    selectedTool
                    confidence
                    timestamp
                }
            }
        """


class SubscriptionVariables:
    """Factory for subscription variables."""

    @staticmethod
    def tool_events_vars(
        tool_name: str, workspace_id: Optional[str] = None
    ) -> dict:
        """Build variables for tool events subscription."""
        return {"toolName": tool_name, "workspaceId": workspace_id}

    @staticmethod
    def routing_events_vars(workspace_id: Optional[str] = None) -> dict:
        """Build variables for routing events subscription."""
        return {"workspaceId": workspace_id}
