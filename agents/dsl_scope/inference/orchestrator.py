"""
Comprehensive scope inference orchestration.

Integrates chat analysis, tool tracking, and database storage with auto-activation.
"""

import logging
from typing import Optional, Dict, List, Any
from collections import defaultdict

from dsl_scope.scope_levels import ScopeLevel
from .types import InferenceSignal
from .detector import ScopeInferenceEngine

logger = logging.getLogger(__name__)


class ComprehensiveScopeInferenceEngine:
    """
    MAXIMUM KNOWLEDGE DENSITY inference system.

    Integrates:
    - Chat log analysis
    - Tool call tracking
    - File system monitoring
    - Neo4j graph relations
    - Historical patterns
    - Time-series analysis
    - Embeddings for semantic similarity
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        redis_url: str,
    ):
        self.scope_engine = ScopeInferenceEngine()

        # Will connect to Neo4j for graph storage
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password

        # Will connect to Redis for real-time state
        self.redis_url = redis_url

        # Confidence thresholds for auto-activation
        self.confidence_thresholds = {
            ScopeLevel.SESSION: 0.8,
            ScopeLevel.PHASE: 0.7,
            ScopeLevel.PROJECT: 0.6,
            ScopeLevel.WORKSPACE: 0.7,
            ScopeLevel.ORGANIZATION: 0.8,
            ScopeLevel.ITERATION: 0.5,
        }

    async def process_openai_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[InferenceSignal]:
        """
        Process an OpenAI completion request from a black-box ReAct agent.

        Extract ALL possible inference signals from:
        - message history
        - tool calls in messages
        - metadata timestamps
        - conversation patterns
        """
        signals = []

        # Extract latest user and assistant messages
        user_msg = ""
        assistant_msg = ""
        tool_calls_data = []

        for msg in reversed(messages):
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user" and not user_msg:
                user_msg = content
            elif role == "assistant" and not assistant_msg:
                assistant_msg = content

                # Extract tool calls if present
                if "tool_calls" in msg:
                    tool_calls_data.extend(msg["tool_calls"])

        # 1. Analyze chat messages
        chat_signals = await self.scope_engine.analyze_chat_message(
            user_msg, assistant_msg, metadata
        )
        signals.extend(chat_signals)

        # 2. Analyze tool calls
        for tool_call in tool_calls_data:
            func = tool_call.get("function", {})
            tool_name = func.get("name", "")
            args_str = func.get("arguments", "{}")

            try:
                import json
                arguments = (
                    json.loads(args_str) if isinstance(args_str, str) else args_str
                )
            except Exception:
                arguments = {}

            tool_signals = await self.scope_engine.analyze_tool_call(
                tool_name, arguments
            )
            signals.extend(tool_signals)

        return signals

    async def auto_activate_scopes(
        self,
        signals: List[InferenceSignal],
        dsl_system
    ) -> Dict[ScopeLevel, str]:
        """
        Automatically activate scope contexts based on inference signals.

        Returns activated scopes.
        """
        activated = {}

        # Group signals by scope level
        by_scope: Dict[ScopeLevel, List[InferenceSignal]] = defaultdict(list)
        for signal in signals:
            by_scope[signal.scope_level].append(signal)

        # For each scope, pick highest confidence signal
        for scope_level, scope_signals in by_scope.items():
            if not scope_signals:
                continue

            # Get highest confidence signal
            best_signal = max(scope_signals, key=lambda s: s.confidence)

            # Check if confidence exceeds threshold
            threshold = self.confidence_thresholds.get(scope_level, 0.7)
            if best_signal.confidence < threshold:
                logger.debug(
                    f"Skipping {scope_level.value}: confidence "
                    f"{best_signal.confidence} < {threshold}"
                )
                continue

            # Activate scope
            logger.info(
                f"Auto-activating {scope_level.value}: {best_signal.value} "
                f"(confidence: {best_signal.confidence:.2f}, "
                f"evidence: {best_signal.evidence})"
            )

            # Set context in DSL system
            if scope_level == ScopeLevel.SESSION:
                await dsl_system.context_manager.set_session_context(
                    best_signal.value
                )
            elif scope_level == ScopeLevel.PHASE:
                phase_type = (
                    best_signal.value.split("_")[1]
                    if "_" in best_signal.value
                    else "unknown"
                )
                await dsl_system.context_manager.set_phase_context(
                    best_signal.value, phase_type
                )
            elif scope_level == ScopeLevel.PROJECT:
                # Extract project name if present
                project_name = next(
                    (
                        s.evidence.split("'")[1]
                        for s in scope_signals
                        if "'" in s.evidence
                    ),
                    None
                )
                await dsl_system.context_manager.set_project_context(
                    best_signal.value, project_name
                )
            elif scope_level == ScopeLevel.WORKSPACE:
                await dsl_system.context_manager.set_workspace_context(
                    best_signal.value
                )
            elif scope_level == ScopeLevel.ORGANIZATION:
                await dsl_system.context_manager.set_organization_context(
                    best_signal.value
                )

            activated[scope_level] = best_signal.value

        return activated

    async def store_to_neo4j(self, signals: List[InferenceSignal]) -> None:
        """
        Store inference signals and relations to Neo4j.

        Creates dense similarity network:
        - Nodes: Sessions, Projects, Files, ToolCalls, Messages
        - Edges: Relations with confidence scores
        - Properties: Timestamps, evidence, metadata
        """
        # TODO: Implement Neo4j storage
        # Will use py2neo or neo4j-driver
        pass

    async def get_historical_context(
        self,
        scope_level: ScopeLevel,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Query historical patterns from Neo4j.

        For a given scope level, return:
        - Most likely values based on past behavior
        - Confidence scores
        - Related entities
        - Temporal patterns
        """
        # TODO: Query Neo4j for patterns
        insights = await self.scope_engine.analyze_historical_patterns()
        return insights
