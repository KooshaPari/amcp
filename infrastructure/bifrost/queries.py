"""GraphQL query builders and query operations for BifrostClient."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolMetadata:
    """Tool metadata from Bifrost."""

    name: str
    description: str
    parameters: Dict[str, Any]
    category: Optional[str] = None
    tags: List[str] = None


@dataclass
class RoutingDecision:
    """Routing decision from Bifrost."""

    selected_tool: str
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Search result from Bifrost."""

    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class QueryBuilder:
    """Builder for GraphQL query operations."""

    @staticmethod
    def tools_query(filters: Optional[Dict[str, Any]], limit: int) -> str:
        """Build tools query."""
        return """
            query Tools($filters: ToolFilters, $limit: Int) {
                tools(filters: $filters, limit: $limit) {
                    name
                    description
                    parameters
                    category
                    tags
                }
            }
        """

    @staticmethod
    def tool_query() -> str:
        """Build single tool query."""
        return """
            query Tool($name: String!) {
                tool(name: $name) {
                    name
                    description
                    parameters
                    category
                    tags
                }
            }
        """

    @staticmethod
    def route_query() -> str:
        """Build routing query."""
        return """
            query RouteRequest($prompt: String!, $context: JSON) {
                route(prompt: $prompt, context: $context) {
                    selectedTool
                    confidence
                    reasoning
                    alternatives {
                        tool
                        score
                    }
                }
            }
        """

    @staticmethod
    def semantic_search_query() -> str:
        """Build semantic search query."""
        return """
            query SemanticSearch($query: String!, $limit: Int, $filters: JSON) {
                vectorSearch(query: $query, limit: $limit, filters: $filters) {
                    id
                    content
                    metadata
                    score
                }
            }
        """


class QueryProcessor:
    """Process query results."""

    @staticmethod
    def process_tools(result: Dict[str, Any]) -> List[ToolMetadata]:
        """Process tools query result."""
        tools_data = result.get("tools", [])
        return [
            ToolMetadata(
                name=t["name"],
                description=t["description"],
                parameters=t.get("parameters", {}),
                category=t.get("category"),
                tags=t.get("tags", []),
            )
            for t in tools_data
        ]

    @staticmethod
    def process_tool(result: Dict[str, Any]) -> Optional[ToolMetadata]:
        """Process single tool query result."""
        tool_data = result.get("tool")

        if not tool_data:
            return None

        return ToolMetadata(
            name=tool_data["name"],
            description=tool_data["description"],
            parameters=tool_data.get("parameters", {}),
            category=tool_data.get("category"),
            tags=tool_data.get("tags", []),
        )

    @staticmethod
    def process_routing_decision(result: Dict[str, Any]) -> RoutingDecision:
        """Process routing query result."""
        route_data = result.get("route", {})

        return RoutingDecision(
            selected_tool=route_data.get("selectedTool", ""),
            confidence=route_data.get("confidence", 0.0),
            reasoning=route_data.get("reasoning", ""),
            alternatives=route_data.get("alternatives", []),
        )

    @staticmethod
    def process_search_results(
        result: Dict[str, Any],
    ) -> List[SearchResult]:
        """Process semantic search query result."""
        results_data = result.get("vectorSearch", [])

        return [
            SearchResult(
                id=r["id"],
                content=r["content"],
                metadata=r.get("metadata", {}),
                score=r.get("score", 0.0),
            )
            for r in results_data
        ]
