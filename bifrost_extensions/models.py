"""Data models for Bifrost Extensions SDK."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RoutingStrategy(str, Enum):
    """Model routing optimization strategies."""

    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    SPEED_OPTIMIZED = "speed_optimized"
    BALANCED = "balanced"
    PARETO = "pareto"


class Message(BaseModel):
    """Chat message."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class RoutingConstraints(BaseModel):
    """Constraints for routing decisions."""

    max_cost_usd: Optional[float] = Field(None, description="Maximum cost per request")
    max_latency_ms: Optional[float] = Field(None, description="Maximum latency")
    required_capabilities: Optional[List[str]] = Field(
        None, description="Required model capabilities"
    )


class RoutingRequest(BaseModel):
    """Request for model routing."""

    messages: List[Message] = Field(..., description="Conversation messages")
    strategy: RoutingStrategy = Field(
        RoutingStrategy.BALANCED, description="Routing strategy"
    )
    constraints: Optional[RoutingConstraints] = Field(
        None, description="Routing constraints"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ModelInfo(BaseModel):
    """Selected model information."""

    model_id: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name")
    estimated_cost_usd: float = Field(..., description="Estimated cost")
    estimated_latency_ms: float = Field(..., description="Estimated latency")


class RoutingResponse(BaseModel):
    """Response from model routing."""

    model: ModelInfo = Field(..., description="Selected model")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Routing confidence")
    reasoning: Optional[str] = Field(None, description="Routing reasoning")
    alternatives: Optional[List[ModelInfo]] = Field(
        None, description="Alternative models"
    )


class ToolRoutingRequest(BaseModel):
    """Request for tool routing."""

    action: str = Field(..., description="Action to perform")
    available_tools: List[str] = Field(..., description="Available tool names")
    context: Optional[Dict[str, Any]] = Field(None, description="Context information")


class ToolRoutingDecision(BaseModel):
    """Decision from tool routing."""

    recommended_tool: str = Field(..., description="Recommended tool name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(None, description="Decision reasoning")
    alternatives: Optional[List[str]] = Field(None, description="Alternative tools")


class ClassificationRequest(BaseModel):
    """Request for prompt classification."""

    prompt: str = Field(..., description="Prompt to classify")
    categories: Optional[List[str]] = Field(
        None, description="Target categories (or auto-detect)"
    )


class ClassificationResult(BaseModel):
    """Result from prompt classification."""

    category: str = Field(..., description="Classified category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    subcategories: Optional[List[str]] = Field(None, description="Subcategories")
    complexity: Optional[str] = Field(
        None, description="Complexity level (simple, moderate, complex)"
    )


class UsageStats(BaseModel):
    """Usage statistics."""

    total_requests: int = Field(..., description="Total requests")
    total_cost_usd: float = Field(..., description="Total cost")
    avg_latency_ms: float = Field(..., description="Average latency")
    requests_by_model: Dict[str, int] = Field(..., description="Requests per model")
    cost_by_model: Dict[str, float] = Field(..., description="Cost per model")
