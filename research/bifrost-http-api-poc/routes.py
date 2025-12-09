"""API routes for Bifrost HTTP API."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from opentelemetry import trace
from pydantic import BaseModel, Field

from bifrost_api.dependencies import get_routing_service
from bifrost_extensions.models import (
    ClassificationRequest,
    ClassificationResult,
    RoutingRequest,
    RoutingResponse,
    ToolRoutingRequest,
    ToolRoutingDecision,
    UsageStats,
    ModelInfo,
)


router = APIRouter()
tracer = trace.get_tracer(__name__)


# ============================================================================
# Request/Response Models (HTTP-specific)
# ============================================================================


class RouteRequestHTTP(BaseModel):
    """HTTP request for routing."""

    messages: List[Dict[str, str]]
    strategy: str = "balanced"
    constraints: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class RouteResponseHTTP(BaseModel):
    """HTTP response for routing."""

    model: ModelInfo
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    request_id: str


class ToolRouteRequestHTTP(BaseModel):
    """HTTP request for tool routing."""

    action: str
    available_tools: List[str]
    context: Optional[Dict[str, Any]] = None


class ToolRouteResponseHTTP(BaseModel):
    """HTTP response for tool routing."""

    recommended_tool: str
    confidence: float
    reasoning: Optional[str] = None
    request_id: str


class ClassifyRequestHTTP(BaseModel):
    """HTTP request for classification."""

    prompt: str
    categories: Optional[List[str]] = None


class ClassifyResponseHTTP(BaseModel):
    """HTTP response for classification."""

    category: str
    confidence: float
    complexity: str
    request_id: str


class UsageRequestHTTP(BaseModel):
    """HTTP request for usage stats."""

    start_date: str
    end_date: str
    group_by: str = "model"


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    error_code: str
    request_id: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/route", response_model=RouteResponseHTTP)
@tracer.start_as_current_span("api.route")
async def route_request(
    request: RouteRequestHTTP,
    http_request: Request,
    routing_service=Depends(get_routing_service),
) -> RouteResponseHTTP:
    """
    Route request to optimal model.

    This endpoint selects the best model for a given request based on the
    specified strategy, constraints, and conversation context.

    Args:
        request: Routing request with messages and strategy
        http_request: FastAPI request object
        routing_service: Injected routing service

    Returns:
        Routing response with selected model and metadata

    Raises:
        HTTPException: If routing fails
    """
    span = trace.get_current_span()
    request_id = http_request.state.request_id

    span.set_attribute("routing.strategy", request.strategy)
    span.set_attribute("routing.message_count", len(request.messages))
    span.set_attribute("request.id", request_id)

    try:
        # Convert HTTP request to internal format
        from router_core.domain.models.requests import (
            RoutingRequest as InternalRoutingRequest,
        )

        # Extract last user message as prompt
        prompt = ""
        for msg in reversed(request.messages):
            if msg.get("role") == "user" and msg.get("content"):
                prompt = msg["content"]
                break

        if not prompt:
            raise HTTPException(status_code=400, detail="No user message found")

        internal_request = InternalRoutingRequest(
            prompt=prompt, strategy=request.strategy
        )

        # Route using internal service
        # TODO: This is a simplified version - full implementation will use
        # routing_service.build_plan() and handle full request flow
        result = await routing_service._execute_routing_simple(
            internal_request, request.constraints
        )

        # Convert to HTTP response
        return RouteResponseHTTP(
            model=ModelInfo(
                model_id=result.model_id,
                provider=result.provider,
                estimated_cost_usd=result.estimated_cost,
                estimated_latency_ms=result.estimated_latency,
            ),
            confidence=getattr(result, "confidence", 0.9),
            reasoning=getattr(result, "reasoning", None),
            request_id=request_id,
        )

    except Exception as e:
        span.set_attribute("error", True)
        span.set_attribute("error.message", str(e))
        raise HTTPException(status_code=500, detail=f"Routing failed: {e}")


@router.post("/route-tool", response_model=ToolRouteResponseHTTP)
@tracer.start_as_current_span("api.route_tool")
async def route_tool(
    request: ToolRouteRequestHTTP,
    http_request: Request,
    routing_service=Depends(get_routing_service),
) -> ToolRouteResponseHTTP:
    """
    Route action to optimal tool.

    Selects the best tool from available options for the given action.

    Args:
        request: Tool routing request
        http_request: FastAPI request object
        routing_service: Injected routing service

    Returns:
        Tool routing decision with recommended tool

    Raises:
        HTTPException: If routing fails
    """
    request_id = http_request.state.request_id

    try:
        # Simple tool routing (placeholder - implement actual logic)
        # For now, just return first available tool
        if not request.available_tools:
            raise HTTPException(status_code=400, detail="No tools available")

        return ToolRouteResponseHTTP(
            recommended_tool=request.available_tools[0],
            confidence=0.8,
            reasoning="Placeholder routing - Week 1 implementation",
            request_id=request_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool routing failed: {e}")


@router.post("/classify", response_model=ClassifyResponseHTTP)
@tracer.start_as_current_span("api.classify")
async def classify_prompt(
    request: ClassifyRequestHTTP,
    http_request: Request,
    routing_service=Depends(get_routing_service),
) -> ClassifyResponseHTTP:
    """
    Classify prompt.

    Determines category, complexity, and confidence for a prompt.

    Args:
        request: Classification request
        http_request: FastAPI request object
        routing_service: Injected routing service

    Returns:
        Classification result

    Raises:
        HTTPException: If classification fails
    """
    request_id = http_request.state.request_id

    try:
        # Use routing service classifier
        classification = routing_service._classifier.classify(
            messages=[{"role": "user", "content": request.prompt}],
            has_tools=False,
            has_response_format=False,
        )

        # Determine category
        category = "general"
        if request.categories:
            # If categories provided, pick first one (simplified)
            category = request.categories[0]
        elif hasattr(classification, "task"):
            category = classification.task

        return ClassifyResponseHTTP(
            category=category,
            confidence=0.85,
            complexity=getattr(classification, "complexity", "moderate"),
            request_id=request_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")


@router.get("/usage", response_model=UsageStats)
@tracer.start_as_current_span("api.usage")
async def get_usage(
    start_date: str,
    end_date: str,
    group_by: str = "model",
    request: Request = None,
    routing_service=Depends(get_routing_service),
) -> UsageStats:
    """
    Get usage statistics.

    Returns aggregated usage metrics for the specified date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        group_by: Grouping dimension (model, provider, user)
        request: FastAPI request object
        routing_service: Injected routing service

    Returns:
        Usage statistics

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # TODO Week 3: Implement actual usage tracking
        # For now, return placeholder data
        return UsageStats(
            total_requests=0,
            total_cost_usd=0.0,
            avg_latency_ms=0.0,
            requests_by_model={},
            cost_by_model={},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Usage retrieval failed: {e}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "version": "1.0.0", "service": "bifrost-api"}
