"""
Multi-Transport Implementation for FastMCP 2.13

Supports:
- stdio (standard input/output)
- SSE (Server-Sent Events)
- HTTP (REST API)
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TransportConfig:
    """Transport configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    base_path: str = "/mcp"
    timeout: int = 30
    max_connections: int = 100


class Transport(ABC):
    """Abstract base class for transports."""
    
    def __init__(self, config: TransportConfig):
        self.config = config
        self.handlers: Dict[str, Callable] = {}
    
    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        pass
    
    def register_handler(self, method: str, handler: Callable) -> None:
        """Register a request handler."""
        self.handlers[method] = handler
    
    async def dispatch(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch request to handler."""
        if method not in self.handlers:
            return {"error": f"Unknown method: {method}"}
        
        try:
            handler = self.handlers[method]
            result = await handler(params) if asyncio.iscoroutinefunction(handler) else handler(params)
            return {"result": result}
        except Exception as e:
            logger.error(f"Error handling {method}: {e}")
            return {"error": str(e)}


class StdioTransport(Transport):
    """Standard input/output transport."""
    
    async def start(self) -> None:
        """Start stdio transport."""
        logger.info("Starting stdio transport")
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Read from stdin
                line = await loop.run_in_executor(None, input)
                request = json.loads(line)
                
                # Dispatch request
                method = request.get("method")
                params = request.get("params", {})
                response = await self.dispatch(method, params)
                
                # Write to stdout
                print(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            except EOFError:
                logger.info("EOF received, shutting down")
                break
            except Exception as e:
                logger.error(f"Error in stdio transport: {e}")
    
    async def stop(self) -> None:
        """Stop stdio transport."""
        logger.info("Stopping stdio transport")


class SSETransport(Transport):
    """Server-Sent Events transport."""
    
    def __init__(self, config: TransportConfig):
        super().__init__(config)
        self.clients: Dict[str, asyncio.Queue] = {}
        self.server = None
    
    async def start(self) -> None:
        """Start SSE transport."""
        logger.info(f"Starting SSE transport on {self.config.host}:{self.config.port}")
        
        try:
            from aiohttp import web
            
            app = web.Application()
            app.router.add_get(f"{self.config.base_path}/events", self._handle_sse)
            app.router.add_post(f"{self.config.base_path}/request", self._handle_request)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.config.host, self.config.port)
            await site.start()
            
            logger.info(f"SSE transport listening on {self.config.host}:{self.config.port}")
            
            # Keep running
            await asyncio.Event().wait()
            
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")
    
    async def _handle_sse(self, request):
        """Handle SSE connection."""
        from aiohttp import web
        
        client_id = request.remote
        queue = asyncio.Queue()
        self.clients[client_id] = queue
        
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        
        await response.prepare(request)
        
        try:
            while True:
                message = await asyncio.wait_for(queue.get(), timeout=self.config.timeout)
                await response.write(f"data: {json.dumps(message)}\n\n".encode())
        except asyncio.TimeoutError:
            pass
        finally:
            del self.clients[client_id]
        
        return response
    
    async def _handle_request(self, request):
        """Handle HTTP POST request."""
        from aiohttp import web
        
        try:
            data = await request.json()
            method = data.get("method")
            params = data.get("params", {})
            
            response = await self.dispatch(method, params)
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def stop(self) -> None:
        """Stop SSE transport."""
        logger.info("Stopping SSE transport")


class HTTPTransport(Transport):
    """HTTP REST API transport."""
    
    def __init__(self, config: TransportConfig):
        super().__init__(config)
        self.server = None
    
    async def start(self) -> None:
        """Start HTTP transport."""
        logger.info(f"Starting HTTP transport on {self.config.host}:{self.config.port}")
        
        try:
            from aiohttp import web
            
            app = web.Application()
            app.router.add_post(f"{self.config.base_path}/call", self._handle_call)
            app.router.add_get(f"{self.config.base_path}/health", self._handle_health)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.config.host, self.config.port)
            await site.start()
            
            logger.info(f"HTTP transport listening on {self.config.host}:{self.config.port}")
            
            # Keep running
            await asyncio.Event().wait()
            
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")
    
    async def _handle_call(self, request):
        """Handle HTTP POST call."""
        from aiohttp import web
        
        try:
            data = await request.json()
            method = data.get("method")
            params = data.get("params", {})
            
            response = await self.dispatch(method, params)
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling call: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def _handle_health(self, request):
        """Handle health check."""
        from aiohttp import web
        return web.json_response({"status": "healthy"})
    
    async def stop(self) -> None:
        """Stop HTTP transport."""
        logger.info("Stopping HTTP transport")


def create_transport(transport_type: str, config: TransportConfig) -> Transport:
    """Factory function to create transport."""
    if transport_type == "stdio":
        return StdioTransport(config)
    elif transport_type == "sse":
        return SSETransport(config)
    elif transport_type == "http":
        return HTTPTransport(config)
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")

