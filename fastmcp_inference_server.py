"""
FastMCP 2.13 Server with Integrated Inference Engine

Extends the base FastMCP 2.13 server with:
- Automatic scope inference from messages and tool calls
- Integrated DSL scope system
- Black-box agent support (ReAct, OpenAI-compatible)
- Middleware-based inference processing
- Neo4j relation building
- Redis state persistence

This is the production-ready server combining:
1. FastMCP 2.13 framework (fastmcp_2_13_server.py)
2. DSL Scope System (dsl_scope/)
3. Comprehensive Inference Engine (dsl_scope/inference_engine.py)
4. MCP Inference Bridge (mcp_inference_bridge.py)
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from fastmcp import FastMCP, Tool, Resource, Prompt

from fastmcp_2_13_server import (
    FastMCP213Server,
    ServerConfig,
    TransportType,
    AuthType,
    MiddlewareStack,
    AuthenticationProvider,
)

from mcp.inference import (
    MCPInferenceBridge,
    InferenceMiddleware,
    create_inference_middleware,
)

from agents.dsl_scope import get_dsl_scope_system, ScopeLevel

logger = logging.getLogger(__name__)


class FastMCPInferenceServer(FastMCP213Server):
    """
    FastMCP 2.13 server with integrated inference capabilities.

    Automatically processes OpenAI-compatible completions to infer and activate
    scopes without explicit agent instrumentation.
    """

    def __init__(self, config: ServerConfig):
        """Initialize with inference capabilities."""
        super().__init__(config)

        # Initialize DSL scope system
        self.dsl_system = get_dsl_scope_system()

        # Initialize inference bridge
        self.inference_bridge = MCPInferenceBridge(
            dsl_system=self.dsl_system
        )

        # Add inference middleware to stack
        inference_middleware = InferenceMiddleware(
            bridge=self.inference_bridge
        )
        self.add_middleware(inference_middleware.process_request)

        logger.info(
            "FastMCP Inference Server initialized with DSL scope system"
        )

    async def process_completion_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process OpenAI-compatible completion request with automatic inference.

        This method:
        1. Extracts scope signals from messages
        2. Detects tool calls
        3. Auto-activates scopes
        4. Stores signals to Neo4j
        5. Returns completion with scope metadata

        Args:
            messages: OpenAI-format message list
            tools: Available tools
            **kwargs: Additional parameters (model, temperature, etc.)

        Returns:
            Dictionary with completion and inference metadata
        """
        # Run inference
        inference_result = await self.inference_bridge.process_openai_completion(
            messages=messages,
            tools=tools,
            session_id=kwargs.get("session_id"),
            request_id=kwargs.get("request_id"),
            model=kwargs.get("model"),
            temperature=kwargs.get("temperature"),
        )

        # Return result with scope metadata
        return {
            "inference": inference_result,
            "scopes": await self.get_current_scopes(),
        }

    async def get_current_scopes(self) -> Dict[str, str]:
        """Get currently active scopes."""
        return await self.inference_bridge.get_current_scopes()

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process tool call through inference engine.

        Args:
            tool_name: Name of tool
            arguments: Tool arguments
            result: Tool result (optional)

        Returns:
            Inference signals detected
        """
        signals = await self.inference_bridge.process_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
        )

        return {"tool": tool_name, "signals": signals}

    def get_inference_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent inference history."""
        return self.inference_bridge.get_inference_history(limit)

    def clear_inference_history(self) -> None:
        """Clear inference history."""
        self.inference_bridge.clear_inference_history()

    async def infer_from_recent_context(
        self, window: int = 10
    ) -> Dict[str, Any]:
        """Infer context from recent history."""
        return await self.inference_bridge.infer_from_recent_history(
            window=window
        )


def create_smartcp_inference_server(
    name: str,
    transport: TransportType = TransportType.STDIO,
    auth_type: AuthType = AuthType.NONE,
    enable_inference: bool = True,
    **kwargs,
) -> FastMCPInferenceServer:
    """
    Factory function to create SmartCP server with inference.

    Args:
        name: Server name
        transport: Transport type (STDIO, SSE, HTTP)
        auth_type: Authentication type
        enable_inference: Enable inference capabilities (default: True)
        **kwargs: Additional configuration

    Returns:
        Configured FastMCPInferenceServer instance

    Example:
        ```python
        server = create_smartcp_inference_server(
            name="smartcp-agent",
            transport=TransportType.STDIO,
            auth_type=AuthType.BEARER,
            bearer_tokens=["token1", "token2"]
        )
        await server.start()
        ```
    """
    config = ServerConfig(
        name=name,
        transport=transport,
        auth_type=auth_type,
        **kwargs,
    )

    server = FastMCPInferenceServer(config)

    # Configure authentication if specified
    if auth_type != AuthType.NONE:
        from fastmcp_2_13_server import (
            OAuthProvider,
            BearerTokenProvider,
            EnvAuthProvider,
        )

        if auth_type == AuthType.OAUTH:
            server.set_auth_provider(
                OAuthProvider(
                    client_id=kwargs.get("oauth_client_id", ""),
                    client_secret=kwargs.get("oauth_client_secret", ""),
                    provider_url=kwargs.get("oauth_provider_url", ""),
                )
            )
        elif auth_type == AuthType.BEARER:
            server.set_auth_provider(
                BearerTokenProvider(
                    valid_tokens=kwargs.get("bearer_tokens", [])
                )
            )
        elif auth_type == AuthType.ENV:
            server.set_auth_provider(
                EnvAuthProvider(
                    env_var=kwargs.get("env_var", "MCP_TOKEN")
                )
            )

    logger.info(
        f"Created SmartCP inference server: {name} (inference={enable_inference})"
    )
    return server


# Example usage for documentation
EXAMPLE_USAGE = """
# Example: Using FastMCP Inference Server

from fastmcp_inference_server import create_smartcp_inference_server, TransportType

# Create server
server = create_smartcp_inference_server(
    name="smartcp-agent",
    transport=TransportType.STDIO,
    auth_type=AuthType.BEARER,
    bearer_tokens=["your-token"]
)

# Server automatically infers scopes from OpenAI messages:
result = await server.process_completion_request(
    messages=[
        {"role": "user", "content": "I'm working on MyApp project"},
        {"role": "assistant", "content": "Great! Let's start implementing..."},
    ]
)

# Result includes:
# - Inferred scopes (PROJECT: MyApp, PHASE: implementation)
# - Confidence scores
# - Evidence for each inference
# - Active scopes set in DSL system

# Get current scopes
scopes = await server.get_current_scopes()
# {
#     "project_id": "myapp-123",
#     "project_name": "MyApp",
#     "phase_id": "impl-456",
#     "phase_type": "implementation",
#     ...
# }

# View inference history
history = server.get_inference_history(limit=10)

# Clear history when needed
server.clear_inference_history()

# Start server
await server.start()
"""

__all__ = [
    "FastMCPInferenceServer",
    "create_smartcp_inference_server",
]
