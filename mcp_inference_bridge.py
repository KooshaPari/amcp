"""
MCP Inference Bridge - Integrates ComprehensiveScopeInferenceEngine with FastMCP

Bridges the gap between FastMCP server and the DSL scope inference system.
Automatically processes OpenAI-compatible messages to infer and activate scopes.

Features:
- Intercepts OpenAI-compatible message requests
- Analyzes chat messages for scope signals
- Processes tool calls for scope patterns
- Auto-activates scopes via DSL system
- Stores inference signals to Neo4j (when available)
- Maintains inference history for context building
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from dsl_scope import (
    get_dsl_scope_system,
    ComprehensiveScopeInferenceEngine,
    ScopeLevel,
)
from dsl_scope.inference_engine import InferenceSignal

logger = logging.getLogger(__name__)


@dataclass
class InferenceContext:
    """Context for inference operations."""
    session_id: str
    request_id: str
    timestamp: datetime
    model: Optional[str] = None
    temperature: Optional[float] = None


class MCPInferenceBridge:
    """Bridge between MCP server and inference engine."""

    def __init__(self, dsl_system=None, inference_engine=None):
        """Initialize bridge with optional custom instances."""
        self.dsl_system = dsl_system or get_dsl_scope_system()
        self.inference_engine = (
            inference_engine or ComprehensiveScopeInferenceEngine()
        )
        self.inference_history: List[Dict[str, Any]] = []
        logger.info("MCP Inference Bridge initialized")

    async def process_openai_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process OpenAI completion request with inference.

        Args:
            messages: OpenAI message format messages
            tools: Available tools list
            session_id: Session ID for context
            request_id: Request ID for tracing
            **kwargs: Additional context (model, temperature, etc.)

        Returns:
            Dictionary with inference results and metadata
        """
        # Create inference context
        context = InferenceContext(
            session_id=session_id or "unknown",
            request_id=request_id or "unknown",
            timestamp=datetime.now(),
            model=kwargs.get("model"),
            temperature=kwargs.get("temperature"),
        )

        # Process messages through inference engine
        signals = await self.inference_engine.process_openai_completion(
            messages=messages,
            tools=tools,
            metadata=asdict(context),
        )

        # Store in history
        history_entry = {
            "context": asdict(context),
            "signals": [
                {
                    "scope_level": s.scope_level.value,
                    "key": s.key,
                    "value": s.value,
                    "confidence": s.confidence,
                    "evidence": s.evidence,
                }
                for s in signals
            ],
        }
        self.inference_history.append(history_entry)

        # Auto-activate scopes
        activated_scopes = await self.inference_engine.auto_activate_scopes(
            signals=signals,
            dsl_system=self.dsl_system,
        )

        logger.info(
            f"Inference complete: session={context.session_id}, "
            f"signals={len(signals)}, activated={len(activated_scopes)}"
        )

        return {
            "success": True,
            "signals": signals,
            "activated_scopes": activated_scopes,
            "inference_context": asdict(context),
        }

    async def process_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        context: Optional[InferenceContext] = None,
    ) -> List[InferenceSignal]:
        """
        Process tool call through inference engine.

        Args:
            tool_name: Name of tool being called
            arguments: Tool arguments
            result: Tool result (optional)
            context: Inference context

        Returns:
            List of detected signals
        """
        signals = await self.inference_engine.analyze_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
        )

        if signals:
            logger.debug(
                f"Tool call analysis: {tool_name} → {len(signals)} signals"
            )

        return signals

    async def get_current_scopes(self) -> Dict[str, str]:
        """Get currently active scopes."""
        current_context = self.dsl_system.get_current_context()
        return {
            "session_id": current_context.session_id,
            "tool_call_id": current_context.tool_call_id,
            "prompt_chain_id": current_context.prompt_chain_id,
            "phase_id": current_context.phase_id,
            "phase_type": current_context.phase_type,
            "project_id": current_context.project_id,
            "project_name": current_context.project_name,
            "workspace_id": current_context.workspace_id,
            "workspace_name": current_context.workspace_name,
            "organization_id": current_context.organization_id,
            "organization_name": current_context.organization_name,
        }

    async def infer_from_recent_history(
        self, window: int = 10
    ) -> Dict[str, Any]:
        """Infer context from recent inference history."""
        if not self.inference_history:
            return {"message": "No inference history"}

        # Get most recent entries within window
        recent = self.inference_history[-window:]

        # Count signal types
        signal_counts = {}
        for entry in recent:
            for signal in entry["signals"]:
                scope = signal["scope_level"]
                signal_counts[scope] = signal_counts.get(scope, 0) + 1

        return {
            "recent_entries": len(recent),
            "signal_counts": signal_counts,
            "last_timestamp": recent[-1]["context"]["timestamp"]
            if recent
            else None,
        }

    def get_inference_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get inference history (most recent first)."""
        return self.inference_history[-limit:][::-1]

    def clear_inference_history(self) -> None:
        """Clear inference history."""
        count = len(self.inference_history)
        self.inference_history.clear()
        logger.info(f"Cleared {count} inference history entries")


class InferenceMiddleware:
    """Middleware to inject inference into MCP request/response pipeline."""

    def __init__(self, bridge: Optional[MCPInferenceBridge] = None):
        """Initialize middleware with optional bridge."""
        self.bridge = bridge or MCPInferenceBridge()

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request through inference."""
        # Check if this is an OpenAI-compatible completion request
        if (
            request.get("method") == "POST"
            and "/completions" in request.get("path", "")
        ):
            try:
                body = request.get("body", {})
                result = await self.bridge.process_openai_completion(
                    messages=body.get("messages", []),
                    tools=body.get("tools"),
                    session_id=request.get("headers", {}).get("X-Session-ID"),
                    request_id=request.get("headers", {}).get("X-Request-ID"),
                    model=body.get("model"),
                    temperature=body.get("temperature"),
                )
                # Attach inference result to request
                request["_inference_result"] = result
                logger.debug(
                    f"Inference attached to request: {result['signals']}"
                )
            except Exception as e:
                logger.error(f"Inference processing failed: {e}", exc_info=True)
                # Don't fail request if inference fails
                request["_inference_error"] = str(e)

        return request

    async def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process outgoing response with inference metadata."""
        # Add inference context to response if available
        # This is optional - can be used for observability
        return response


# Convenience function for MCP server setup
def create_inference_middleware() -> InferenceMiddleware:
    """Factory function to create inference middleware."""
    bridge = MCPInferenceBridge()
    return InferenceMiddleware(bridge=bridge)


# Export public API
__all__ = [
    "MCPInferenceBridge",
    "InferenceMiddleware",
    "InferenceContext",
    "create_inference_middleware",
]
