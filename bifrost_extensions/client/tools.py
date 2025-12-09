"""Tool routing handler for GatewayClient."""

import asyncio
import logging
from typing import Optional, Dict, Any, List

from opentelemetry import trace

from bifrost_extensions.models import ToolRoutingRequest, ToolRoutingDecision
from bifrost_extensions.exceptions import (
    ValidationError,
    TimeoutError,
    RoutingError,
)

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


async def route_tool(
    action: str,
    available_tools: List[str],
    context: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
    http_client=None,
    default_timeout: float = 30.0,
) -> ToolRoutingDecision:
    """
    Route action to optimal tool.

    Args:
        action: Action description (e.g., "search web")
        available_tools: List of available tool names
        context: Optional context for routing
        timeout: Optional timeout override
        http_client: HTTP client for API calls
        default_timeout: Default timeout if not overridden

    Returns:
        ToolRoutingDecision with recommended tool

    Raises:
        ValidationError: If request is invalid
        RoutingError: If routing fails
        TimeoutError: If operation times out
    """
    # Validate
    if not action:
        raise ValidationError("Action cannot be empty")
    if not available_tools:
        raise ValidationError("Must provide at least one available tool")

    request = ToolRoutingRequest(
        action=action, available_tools=available_tools, context=context
    )

    # Execute with timeout
    timeout_val = timeout or default_timeout
    try:
        decision = await asyncio.wait_for(
            _execute_tool_routing(request, http_client),
            timeout=timeout_val,
        )
        return decision
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Tool routing timed out after {timeout_val}s",
            timeout_ms=timeout_val * 1000,
        )


async def _execute_tool_routing(
    request: ToolRoutingRequest,
    http_client,
) -> ToolRoutingDecision:
    """
    Execute tool routing.

    Uses HTTP client if available, falls back to heuristic matching.
    """
    # Try HTTP client first
    if http_client:
        try:
            return await http_client.route_tool(
                action=request.action,
                available_tools=request.available_tools,
                context=request.context,
            )
        except Exception as e:
            logger.warning(f"HTTP tool routing failed: {e}, using fallback")

    # Fallback to heuristic matching
    return _heuristic_tool_routing(request)


def _heuristic_tool_routing(
    request: ToolRoutingRequest,
) -> ToolRoutingDecision:
    """
    Simple heuristic tool routing based on keyword matching.

    This is a fallback when the HTTP client is unavailable.
    """
    action_lower = request.action.lower()

    # Simple keyword matching for common tools
    tool_scores = {}
    for tool in request.available_tools:
        score = 0.0
        tool_lower = tool.lower()

        # Exact match
        if tool_lower in action_lower:
            score += 1.0

        # Common patterns
        if "search" in action_lower and "search" in tool_lower:
            score += 0.8
        if "web" in action_lower and "web" in tool_lower:
            score += 0.7
        if (
            ("doc" in action_lower or "documentation" in action_lower)
            and "doc" in tool_lower
        ):
            score += 0.8
        if "database" in action_lower and (
            "db" in tool_lower or "database" in tool_lower
        ):
            score += 0.9

        # Context-based scoring
        if request.context:
            # Check for relevant context keywords
            context_str = str(request.context).lower()
            if tool_lower in context_str:
                score += 0.5

        tool_scores[tool] = score

    # Select best tool
    if tool_scores:
        best_tool = max(tool_scores, key=tool_scores.get)
        confidence = min(tool_scores[best_tool], 1.0)

        # Get alternatives (top 2)
        sorted_tools = sorted(
            tool_scores.items(), key=lambda x: x[1], reverse=True
        )
        alternatives = [tool for tool, _ in sorted_tools[1:3]]

        return ToolRoutingDecision(
            recommended_tool=best_tool,
            confidence=confidence if confidence > 0.1 else 0.6,
            reasoning=f"Matched '{request.action}' to '{best_tool}' based on keywords",
            alternatives=alternatives if alternatives else None,
        )

    # Fallback to first tool
    return ToolRoutingDecision(
        recommended_tool=request.available_tools[0],
        confidence=0.5,
        reasoning="Default selection (no strong match found)",
    )
