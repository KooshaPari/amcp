"""
Memory System Operations

Core memory operations for episodic, semantic, and working memory.
"""

import logging
from typing import Any, Dict, List, Optional

from ..episodic import EpisodicMemory, TaskOutcome
from ..semantic import RelationType, SemanticMemory
from ..working import WorkingMemory

logger = logging.getLogger(__name__)


class MemoryOperations:
    """Handles memory operations across all memory systems."""

    def __init__(
        self,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        working: WorkingMemory
    ):
        self.episodic = episodic
        self.semantic = semantic
        self.working = working

    # Episodic Memory Operations
    async def record_task(
        self,
        goal: str,
        context: Dict[str, Any],
        tools_used: List[str],
        outcome: TaskOutcome,
        result: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
        duration: float = 0.0,
        lesson_learned: Optional[str] = None
    ) -> str:
        """Record a completed task in episodic memory."""
        entry_id = await self.episodic.store(
            goal=goal,
            context=context,
            tools_used=tools_used,
            outcome=outcome,
            result=result,
            confidence=confidence,
            duration=duration,
            lesson_learned=lesson_learned
        )
        logger.debug(f"Task recorded: {entry_id}")
        return entry_id

    async def recall_similar_tasks(
        self,
        goal: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Recall similar past tasks from episodic memory."""
        entries = await self.episodic.retrieve(goal, limit=limit)
        return [e.to_dict() for e in entries]

    # Semantic Memory Operations
    async def assert_fact(
        self,
        entity: str,
        property_name: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "observation"
    ) -> str:
        """Assert a fact in semantic memory."""
        entry_id = await self.semantic.assert_fact(
            entity=entity,
            property_name=property_name,
            value=value,
            confidence=confidence,
            source=source
        )
        logger.debug(f"Fact asserted: {entity}.{property_name}")
        return entry_id

    async def assert_relationship(
        self,
        entity1: str,
        relation_type: RelationType,
        entity2: str,
        weight: float = 1.0,
        confidence: float = 1.0
    ) -> str:
        """Assert a relationship in semantic memory."""
        relation_id = await self.semantic.assert_relation(
            entity1=entity1,
            relation_type=relation_type,
            entity2=entity2,
            weight=weight,
            confidence=confidence
        )
        logger.debug(f"Relationship asserted: {entity1} -{relation_type.value}→ {entity2}")
        return relation_id

    async def query_facts(
        self,
        entity: str,
        property_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query facts from semantic memory."""
        entries = await self.semantic.query_facts(entity, property_name)
        return [e.to_dict() for e in entries]

    async def find_related_entities(
        self,
        entity: str,
        relation_type: Optional[RelationType] = None,
        max_depth: int = 2
    ) -> Dict[str, List[str]]:
        """Find entities related to given entity."""
        return await self.semantic.find_neighbors(
            entity=entity,
            relation_type=relation_type,
            max_depth=max_depth
        )

    # Working Memory Operations
    async def create_context(self) -> str:
        """Create new working context."""
        context_id = await self.working.create_context()
        logger.debug(f"Context created: {context_id}")
        return context_id

    async def push_frame(self, goal: str, context_id: Optional[str] = None) -> str:
        """Push new frame onto context stack."""
        frame_id = await self.working.push_frame(goal, context_id)
        logger.debug(f"Frame pushed: {frame_id}")
        return frame_id

    async def pop_frame(self, context_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Pop frame from context stack."""
        frame = await self.working.pop_frame(context_id)
        if frame:
            logger.debug(f"Frame popped: {frame.frame_id}")
            return frame.to_dict()
        return None

    async def bind_variable(
        self,
        var_name: str,
        value: Any,
        frame_id: Optional[str] = None,
        context_id: Optional[str] = None
    ) -> bool:
        """Bind variable in working memory."""
        success = await self.working.bind_variable(
            var_name=var_name,
            value=value,
            frame_id=frame_id,
            context_id=context_id
        )
        if success:
            logger.debug(f"Variable bound: {var_name}")
        return success

    async def get_variable(
        self,
        var_name: str,
        context_id: Optional[str] = None
    ) -> Optional[Any]:
        """Get variable value from working memory."""
        return await self.working.get_variable(var_name, context_id)

    # Cleanup Operations
    async def cleanup_idle(self) -> int:
        """Clean up idle contexts from working memory."""
        count = await self.working.cleanup_idle()
        if count > 0:
            logger.info(f"Cleaned up {count} idle contexts")
        return count

    async def decay_semantic_confidence(self) -> int:
        """Apply temporal decay to semantic facts."""
        count = await self.semantic.decay_confidence()
        if count > 0:
            logger.info(f"Decayed confidence for {count} facts")
        return count
