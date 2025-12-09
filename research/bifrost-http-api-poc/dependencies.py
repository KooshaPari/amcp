"""Dependency injection for Bifrost API."""

from typing import Optional

try:
    from router.router_core.application.routing_service import RoutingService
    from router.router_core.routing.registry import ModelRegistry
    ROUTER_CORE_AVAILABLE = True
except ImportError:
    ROUTER_CORE_AVAILABLE = False
    RoutingService = None
    ModelRegistry = None


# Singleton instances
_routing_service: Optional[RoutingService] = None
_model_registry: Optional[ModelRegistry] = None


def get_routing_service() -> RoutingService:
    """
    Get or create routing service instance.

    Returns:
        RoutingService instance
    """
    global _routing_service

    if not ROUTER_CORE_AVAILABLE:
        raise ImportError("router_core is not available. Install router dependencies.")

    if _routing_service is None:
        # Initialize routing service with default configuration
        # This is a simplified version - production should use proper factory
        try:
            from router.router_core.application.factory import create_routing_service

            _routing_service = create_routing_service()
        except ImportError:
            # Fallback: create minimal routing service
            from router.router_core.classification.unified_classifier import UnifiedClassifier
            from router.router_core.routing.selector import ModelSelector
            from router.router_core.routing.recommender import ModelRecommender
            from router.router_core.execution.executor import ModelExecutor
            from router.router_core.policies.manager import PolicyManager
            from router.router_core.limits.rate_limiter import RateLimiter
            from router.router_core.limits.budget_manager import BudgetManager
            from router.router_core.limits.credit_optimizer import CreditOptimizer
            from router.router_core.cache.prompt_cache import PromptCache
            from router.router_core.metrics.collector import MetricsCollector
            from router.router_core.adapters.persistence.usage_log import UsageLogger
            from router.router_core.config.settings import Settings
            from router.router_core.refinement.refiner import ResponseRefiner
            from router.router_core.providers.optimizer import ProviderOptimizer

            settings = Settings()
            registry = get_model_registry()

            _routing_service = RoutingService(
                classifier=UnifiedClassifier(),
                selector=ModelSelector(registry),
                recommender=ModelRecommender(),
                executor=ModelExecutor(),
                policy_manager=PolicyManager(),
                rate_limiter=RateLimiter(),
                budget_manager=BudgetManager(),
                credit_optimizer=CreditOptimizer(),
                prompt_cache=PromptCache(),
                metrics_collector=MetricsCollector(),
                usage_logger=UsageLogger(),
                settings=settings,
                registry=registry,
                refiner=ResponseRefiner(),
                provider_optimizer=ProviderOptimizer(),
            )

    return _routing_service


def get_model_registry() -> ModelRegistry:
    """
    Get or create model registry instance.

    Returns:
        ModelRegistry instance
    """
    global _model_registry

    if _model_registry is None:
        _model_registry = ModelRegistry()

    return _model_registry
