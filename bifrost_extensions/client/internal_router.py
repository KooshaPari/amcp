"""Internal router fallback for Week 1 support (legacy)."""

import logging
from typing import Optional

from bifrost_extensions.models import (
    RoutingRequest,
    RoutingResponse,
    ModelInfo,
    ToolRoutingRequest,
    ToolRoutingDecision,
    ClassificationRequest,
    ClassificationResult,
)
from bifrost_extensions.exceptions import RoutingError

logger = logging.getLogger(__name__)

# Try importing internal router (Week 1 fallback only)
try:
    from router.router_core.application.di_container import get_routing_service
    ROUTER_AVAILABLE = True
except ImportError:
    get_routing_service = None
    ROUTER_AVAILABLE = False


def is_router_available() -> bool:
    """Check if internal router is available."""
    return ROUTER_AVAILABLE


async def route_with_internal_router(
    router,
    request: RoutingRequest,
) -> RoutingResponse:
    """
    Execute routing using internal router (Week 1 fallback).

    Args:
        router: Initialized routing service
        request: Routing request

    Returns:
        Routing response

    Raises:
        RoutingError: If routing fails
    """
    if not router:
        raise RoutingError(
            "Router not initialized",
            details={"reason": "RoutingService not available"},
        )

    try:
        # Import internal router components
        from router.router_core.adapters.http.schemas import (
            Message as InternalMessage,
            ChatCompletionRequest,
        )
        from router.router_core.application.routing_service import RoutingContext

        # Convert SDK messages to internal format
        internal_messages = [
            InternalMessage(role=msg.role, content=msg.content)
            for msg in request.messages
        ]

        # Build chat completion request
        # Map SDK strategy to router strategy
        strategy_map = {
            "cost_optimized": "router:free-first",
            "performance_optimized": "router:premium",
            "speed_optimized": "router:fast",
            "balanced": "router:balanced",
            "pareto": "router:pareto",
        }
        model_strategy = strategy_map.get(
            request.strategy.value, "router:balanced"
        )

        internal_request = ChatCompletionRequest(
            model=model_strategy,
            messages=internal_messages,
            temperature=0.7,  # Default
            stream=False,
        )

        # Create routing context
        context = RoutingContext(
            request_id=f"bifrost_{id(request)}",
            tenant="bifrost_sdk",
            stream=False,
        )

        # Build routing plan
        plan = await router.build_plan(internal_request, context=context)

        # Extract model info from plan
        primary_model = plan.primary_model

        # Convert back to SDK format
        return RoutingResponse(
            model=ModelInfo(
                model_id=primary_model.key,
                provider=primary_model.provider,
                estimated_cost_usd=(
                    primary_model.price_in + primary_model.price_out
                )
                / 1_000_000,
                estimated_latency_ms=getattr(
                    primary_model, "avg_latency_ms", 200.0
                ),
            ),
            confidence=plan.classification.confidence
            if plan.classification
            else 0.85,
            reasoning=plan.classification.reasoning
            if plan.classification
            else None,
            alternatives=[
                ModelInfo(
                    model_id=model.key,
                    provider=model.provider,
                    estimated_cost_usd=(
                        model.price_in + model.price_out
                    )
                    / 1_000_000,
                    estimated_latency_ms=getattr(
                        model, "avg_latency_ms", 200.0
                    ),
                )
                for model in plan.candidates[1:4]  # Top 3 alternatives
            ]
            if len(plan.candidates) > 1
            else None,
        )

    except Exception as e:
        raise RoutingError(
            f"Routing failed: {e}", details={"error": str(e)}
        )


async def classify_with_internal_router(
    request: ClassificationRequest,
) -> ClassificationResult:
    """
    Execute classification using internal router (Week 1 fallback).

    Args:
        request: Classification request

    Returns:
        Classification result

    Raises:
        RoutingError: If classification fails
    """
    try:
        # Import unified classifier
        from router.router_core.classification.unified_classifier import (
            get_unified_classifier,
        )
        from router.router_core.adapters.http.schemas import (
            Message as InternalMessage,
        )

        # Get classifier instance
        classifier = get_unified_classifier()

        # Convert prompt to messages format for classifier
        messages = [InternalMessage(role="user", content=request.prompt)]

        # Classify
        result = classifier.classify(
            messages=messages,
            has_tools=False,
            has_response_format=False,
        )

        # Map internal classification to SDK format
        # Determine category based on task
        category_map = {
            "code_generation": "coding",
            "qa": "question_answering",
            "creative": "creative",
            "analysis": "analysis",
            "chat": "general",
            "summarization": "summarization",
            "translation": "translation",
        }
        category = category_map.get(result.task, result.task)

        # If categories provided, try to match to one
        if request.categories:
            # Simple matching logic
            category_lower = category.lower()
            for cat in request.categories:
                if (
                    cat.lower() in category_lower
                    or category_lower in cat.lower()
                ):
                    category = cat
                    break
            else:
                # No match, default to first category
                category = request.categories[0]

        # Determine complexity from classification
        complexity_score = result.complexity_score
        if complexity_score < 0.3:
            complexity = "simple"
        elif complexity_score < 0.7:
            complexity = "moderate"
        else:
            complexity = "complex"

        # Build subcategories from complexity breakdown
        subcategories = []
        if result.complexity.creativity > 0.7:
            subcategories.append("creative")
        if result.complexity.reasoning > 0.7:
            subcategories.append("analytical")
        if result.complexity.domain_knowledge > 0.7:
            subcategories.append("specialized")

        return ClassificationResult(
            category=category,
            confidence=result.confidence,
            subcategories=subcategories if subcategories else None,
            complexity=complexity,
        )

    except Exception as e:
        # Fallback classification
        logger.warning(f"Classification failed: {e}, using fallback")

        # Simple keyword-based fallback
        prompt_lower = request.prompt.lower()

        # Determine category
        if any(
            word in prompt_lower
            for word in ["code", "function", "python", "javascript"]
        ):
            category = "coding"
            complexity = "moderate"
        elif any(
            word in prompt_lower for word in ["analyze", "explain", "why", "how"]
        ):
            category = "analysis"
            complexity = "moderate"
        elif any(
            word in prompt_lower
            for word in ["write", "create", "story", "poem"]
        ):
            category = "creative"
            complexity = "simple"
        elif len(request.prompt.split()) < 10:
            category = "general"
            complexity = "simple"
        else:
            category = "general"
            complexity = "moderate"

        # Match to provided categories if available
        if request.categories:
            category = request.categories[0]

        return ClassificationResult(
            category=category,
            confidence=0.65,  # Lower confidence for fallback
            complexity=complexity,
        )


def initialize_internal_router():
    """Initialize internal router service if available.

    Returns:
        Router service or None if not available
    """
    if not ROUTER_AVAILABLE:
        return None

    try:
        router = get_routing_service()
        logger.info("Initialized internal router for SDK")
        return router
    except Exception as e:
        logger.warning(f"Failed to initialize internal router: {e}")
        return None
