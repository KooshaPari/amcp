"""
Middleware System (Proposal 17)

Provides:
- Client middleware
- Proxy middleware
- Composition middleware
- Request/response transformation
"""

import logging
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MiddlewareConfig:
    """Middleware configuration."""
    name: str
    priority: int
    enabled: bool = True


class MiddlewareStack:
    """Middleware stack."""
    
    def __init__(self):
        self.middlewares: List[Tuple[MiddlewareConfig, Callable]] = []
    
    async def add_middleware(self, config: MiddlewareConfig, handler: Callable) -> None:
        """Add middleware."""
        logger.info(f"Adding middleware: {config.name}")
        
        self.middlewares.append((config, handler))
        self.middlewares.sort(key=lambda x: x[0].priority)
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through middleware."""
        try:
            logger.info("Processing request through middleware")
            
            for config, handler in self.middlewares:
                if config.enabled:
                    request = await handler(request)
            
            return request
        
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return request
    
    async def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process response through middleware."""
        try:
            logger.info("Processing response through middleware")
            
            for config, handler in reversed(self.middlewares):
                if config.enabled:
                    response = await handler(response)
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return response


class ClientMiddleware:
    """Client-side middleware."""
    
    def __init__(self):
        self.stack = MiddlewareStack()
    
    async def add_auth_middleware(self, token: str) -> None:
        """Add authentication middleware."""
        async def auth_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            request["headers"] = request.get("headers", {})
            request["headers"]["Authorization"] = f"Bearer {token}"
            return request
        
        config = MiddlewareConfig(name="auth", priority=1)
        await self.stack.add_middleware(config, auth_handler)
    
    async def add_logging_middleware(self) -> None:
        """Add logging middleware."""
        async def logging_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"Request: {request.get('method')} {request.get('path')}")
            return request
        
        config = MiddlewareConfig(name="logging", priority=2)
        await self.stack.add_middleware(config, logging_handler)
    
    async def add_retry_middleware(self, max_retries: int = 3) -> None:
        """Add retry middleware."""
        async def retry_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            request["max_retries"] = max_retries
            return request
        
        config = MiddlewareConfig(name="retry", priority=3)
        await self.stack.add_middleware(config, retry_handler)


class ProxyMiddleware:
    """Proxy middleware."""
    
    def __init__(self):
        self.stack = MiddlewareStack()
    
    async def add_routing_middleware(self, routes: Dict[str, str]) -> None:
        """Add routing middleware."""
        async def routing_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            path = request.get("path", "")
            for pattern, target in routes.items():
                if pattern in path:
                    request["target"] = target
                    break
            return request
        
        config = MiddlewareConfig(name="routing", priority=1)
        await self.stack.add_middleware(config, routing_handler)
    
    async def add_load_balancing_middleware(self, servers: List[str]) -> None:
        """Add load balancing middleware."""
        self.server_index = 0
        
        async def lb_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            request["server"] = servers[self.server_index % len(servers)]
            self.server_index += 1
            return request
        
        config = MiddlewareConfig(name="load_balance", priority=2)
        await self.stack.add_middleware(config, lb_handler)


class CompositionMiddleware:
    """Composition middleware."""
    
    def __init__(self):
        self.stack = MiddlewareStack()
    
    async def add_transformation_middleware(self, transformer: Callable) -> None:
        """Add transformation middleware."""
        async def transform_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            return await transformer(request)
        
        config = MiddlewareConfig(name="transform", priority=1)
        await self.stack.add_middleware(config, transform_handler)
    
    async def add_validation_middleware(self, validator: Callable) -> None:
        """Add validation middleware."""
        async def validate_handler(request: Dict[str, Any]) -> Dict[str, Any]:
            if await validator(request):
                return request
            raise ValueError("Validation failed")
        
        config = MiddlewareConfig(name="validate", priority=2)
        await self.stack.add_middleware(config, validate_handler)


# Global instances
_client_middleware: Optional[ClientMiddleware] = None
_proxy_middleware: Optional[ProxyMiddleware] = None
_composition_middleware: Optional[CompositionMiddleware] = None


def get_client_middleware() -> ClientMiddleware:
    """Get or create global client middleware."""
    global _client_middleware
    if _client_middleware is None:
        _client_middleware = ClientMiddleware()
    return _client_middleware


def get_proxy_middleware() -> ProxyMiddleware:
    """Get or create global proxy middleware."""
    global _proxy_middleware
    if _proxy_middleware is None:
        _proxy_middleware = ProxyMiddleware()
    return _proxy_middleware


def get_composition_middleware() -> CompositionMiddleware:
    """Get or create global composition middleware."""
    global _composition_middleware
    if _composition_middleware is None:
        _composition_middleware = CompositionMiddleware()
    return _composition_middleware

