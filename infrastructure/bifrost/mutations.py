"""GraphQL mutation builders and mutation operations for BifrostClient."""

from typing import Any, Dict, List, Optional


class MutationBuilder:
    """Builder for GraphQL mutation operations."""

    @staticmethod
    def execute_tool_mutation() -> str:
        """Build execute tool mutation."""
        return """
            mutation ExecuteTool($name: String!, $input: JSON!) {
                executeTool(name: $name, input: $input) {
                    success
                    data
                    error
                    metadata {
                        duration
                        model
                        tokens
                    }
                }
            }
        """

    @staticmethod
    def register_tool_mutation() -> str:
        """Build register tool mutation."""
        return """
            mutation RegisterTool($tool: ToolInput!) {
                registerTool(tool: $tool) {
                    success
                    message
                }
            }
        """


class MutationProcessor:
    """Process mutation results."""

    @staticmethod
    def process_tool_execution(result: Dict[str, Any]) -> Dict[str, Any]:
        """Process tool execution mutation result."""
        return result.get("executeTool", {})

    @staticmethod
    def process_tool_registration(result: Dict[str, Any]) -> bool:
        """Process tool registration mutation result."""
        registration = result.get("registerTool", {})
        return registration.get("success", False)


class MutationFactory:
    """Factory for creating mutation variables."""

    @staticmethod
    def tool_input(
        name: str,
        description: str,
        parameters: Dict[str, Any],
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create tool input for registration."""
        return {
            "name": name,
            "description": description,
            "parameters": parameters,
            "category": category,
            "tags": tags or [],
        }
