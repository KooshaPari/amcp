"""
Global Router Factory

Provides singleton access to the complexity router instance.
"""

from typing import Optional

from .models import ModelRoutingConfig
from .router import ComplexityRouter

# Global router instance
_complexity_router: Optional[ComplexityRouter] = None


def get_complexity_router(config: ModelRoutingConfig = None) -> ComplexityRouter:
    """Get or create global complexity router instance."""
    global _complexity_router
    if _complexity_router is None:
        _complexity_router = ComplexityRouter(config or ModelRoutingConfig())
    return _complexity_router
