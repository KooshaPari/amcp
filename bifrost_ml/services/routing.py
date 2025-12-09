"""ML Routing Service - Wrapper for existing router_core."""
import sys
import os
from typing import Dict, Any, Optional

# Add parent directory to path to import existing code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from optimization.model_router import (
    ComplexityRouter,
    ModelRoutingConfig,
    ComplexityLevel,
    RoutingDecision,
)


class RoutingService:
    """Service for ML model routing."""

    def __init__(self, config: Optional[ModelRoutingConfig] = None):
        """Initialize routing service."""
        self.router = ComplexityRouter(config)

    async def route(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        output_tokens_estimate: int = 1000,
    ) -> RoutingDecision:
        """Route request to optimal model."""
        return await self.router.route(prompt, context, output_tokens_estimate)

    async def route_with_override(
        self,
        prompt: str,
        override_model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """Route with optional model override."""
        return await self.router.route_with_override(
            prompt, override_model=override_model, context=context
        )

    def get_available_models(self) -> list[str]:
        """Get list of available models."""
        return self.router.get_available_models()


# Global instance
_routing_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    """Get or create global routing service."""
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService()
    return _routing_service
