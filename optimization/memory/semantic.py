"""
Semantic Memory Implementation

Stores facts, relationships, and general knowledge:
- Tool capabilities and constraints
- Task decomposition strategies
- Entity relationships and properties
- Learned patterns and heuristics

Key Features:
- Graph-based relationship storage
- Fact confidence tracking
- Pattern recognition across domains
- Relationship querying
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class RelationType(str, Enum):
    """Types of semantic relationships."""
    REQUIRES = "requires"          # Task requires capability
    PRODUCES = "produces"          # Tool produces output type
    SIMILAR_TO = "similar_to"      # Tasks are similar
    PRECEDES = "precedes"          # Task ordering
    DEPENDS_ON = "depends_on"      # Dependency relation
    CONTRADICTS = "contradicts"    # Conflicting info
    ENHANCES = "enhances"          # Positive interaction


@dataclass
class SemanticEntry:
    """A semantic fact or knowledge item."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity: str = ""                # Subject (e.g., "tool_name", "task_type")
    property_name: str = ""         # Property (e.g., "capability", "cost")
    value: Any = None               # Value (e.g., "text_processing", 0.5)
    confidence: float = 1.0         # Confidence in fact
    timestamp: float = field(default_factory=time.time)
    source: str = "observation"     # Where fact came from

    @property
    def age_seconds(self) -> float:
        """Age of this fact in seconds."""
        return time.time() - self.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity": self.entity,
            "property": self.property_name,
            "value": str(self.value),
            "confidence": self.confidence,
            "age_seconds": self.age_seconds,
            "source": self.source,
        }


@dataclass
class SemanticRelation:
    """A relationship between two entities."""
    relation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity1: str = ""               # Source entity
    relation_type: RelationType = RelationType.REQUIRES
    entity2: str = ""               # Target entity
    weight: float = 1.0             # Strength of relation
    confidence: float = 1.0         # Confidence in relation
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity1": self.entity1,
            "relation_type": self.relation_type.value,
            "entity2": self.entity2,
            "weight": self.weight,
            "confidence": self.confidence,
        }


@dataclass
class SemanticConfig:
    """Configuration for semantic memory."""
    max_entries: int = 10000
    max_relations: int = 5000
    enable_inference: bool = True
    confidence_threshold: float = 0.5
    decay_rate: float = 0.01        # Daily confidence decay


class SemanticMemory:
    """Semantic memory system for facts and relationships."""

    def __init__(self, config: SemanticConfig):
        """Initialize semantic memory."""
        self.config = config
        self.entries: Dict[str, SemanticEntry] = {}
        self.relations: Dict[str, SemanticRelation] = {}
        self.entity_index: Dict[str, Set[str]] = {}  # entity → entry_ids
        self._lock = asyncio.Lock()

    async def assert_fact(
        self,
        entity: str,
        property_name: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "observation",
    ) -> str:
        """Store a fact in semantic memory."""
        async with self._lock:
            entry = SemanticEntry(
                entity=entity,
                property_name=property_name,
                value=value,
                confidence=confidence,
                source=source,
            )

            self.entries[entry.entry_id] = entry

            # Update entity index
            if entity not in self.entity_index:
                self.entity_index[entity] = set()
            self.entity_index[entity].add(entry.entry_id)

            # Enforce capacity
            await self._enforce_capacity()

            logger.debug(
                f"Asserted fact: {entity}.{property_name} = {value} "
                f"(confidence: {confidence})"
            )

            return entry.entry_id

    async def assert_relation(
        self,
        entity1: str,
        relation_type: RelationType,
        entity2: str,
        weight: float = 1.0,
        confidence: float = 1.0,
    ) -> str:
        """Store a relationship in semantic memory."""
        async with self._lock:
            relation = SemanticRelation(
                entity1=entity1,
                relation_type=relation_type,
                entity2=entity2,
                weight=weight,
                confidence=confidence,
            )

            self.relations[relation.relation_id] = relation

            # Update entity index
            for entity in [entity1, entity2]:
                if entity not in self.entity_index:
                    self.entity_index[entity] = set()

            logger.debug(
                f"Asserted relation: {entity1} -{relation_type.value}→ "
                f"{entity2} (weight: {weight})"
            )

            return relation.relation_id

    async def query_facts(
        self,
        entity: str,
        property_name: Optional[str] = None,
    ) -> List[SemanticEntry]:
        """Query facts about an entity."""
        async with self._lock:
            if entity not in self.entity_index:
                return []

            entry_ids = self.entity_index[entity]
            facts = [
                self.entries[eid]
                for eid in entry_ids
                if eid in self.entries
            ]

            if property_name:
                facts = [f for f in facts if f.property_name == property_name]

            # Filter by confidence threshold
            facts = [
                f for f in facts
                if f.confidence >= self.config.confidence_threshold
            ]

            return sorted(facts, key=lambda f: f.confidence, reverse=True)

    async def query_relations(
        self,
        entity1: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
        entity2: Optional[str] = None,
    ) -> List[SemanticRelation]:
        """Query relationships."""
        async with self._lock:
            relations = list(self.relations.values())

            if entity1:
                relations = [r for r in relations if r.entity1 == entity1]
            if entity2:
                relations = [r for r in relations if r.entity2 == entity2]
            if relation_type:
                relations = [r for r in relations if r.relation_type == relation_type]

            # Filter by confidence threshold
            relations = [
                r for r in relations
                if r.confidence >= self.config.confidence_threshold
            ]

            return sorted(
                relations,
                key=lambda r: r.confidence * r.weight,
                reverse=True,
            )

    async def find_neighbors(
        self,
        entity: str,
        relation_type: Optional[RelationType] = None,
        max_depth: int = 2,
    ) -> Dict[str, List[str]]:
        """Find related entities (graph traversal)."""
        async with self._lock:
            neighbors: Dict[str, List[str]] = {}
            visited = {entity}
            frontier = {entity}

            for depth in range(max_depth):
                next_frontier = set()

                for current in frontier:
                    relations = [
                        r for r in self.relations.values()
                        if (r.entity1 == current and
                            (not relation_type or r.relation_type == relation_type))
                    ]

                    for relation in relations:
                        neighbor = relation.entity2
                        if neighbor not in visited:
                            key = f"depth_{depth + 1}"
                            if key not in neighbors:
                                neighbors[key] = []
                            neighbors[key].append(neighbor)
                            visited.add(neighbor)
                            next_frontier.add(neighbor)

                frontier = next_frontier

            return neighbors

    async def update_confidence(
        self,
        entry_id: str,
        new_confidence: float,
    ) -> bool:
        """Update confidence of a fact."""
        async with self._lock:
            if entry_id in self.entries:
                self.entries[entry_id].confidence = max(0.0, min(1.0, new_confidence))
                return True
            return False

    async def decay_confidence(self) -> int:
        """Decay confidence of facts over time. Returns count of decayed facts."""
        async with self._lock:
            decayed = 0

            for entry in self.entries.values():
                age_days = entry.age_seconds / 86400
                decay = self.config.decay_rate * age_days
                old_confidence = entry.confidence
                entry.confidence = max(0.0, entry.confidence - decay)

                if entry.confidence < self.config.confidence_threshold:
                    decayed += 1

            return decayed

    async def get_capabilities(self, tool_name: str) -> List[str]:
        """Get capabilities of a tool."""
        facts = await self.query_facts(tool_name, "capability")
        return [f.value for f in facts]

    async def get_constraints(self, tool_name: str) -> List[str]:
        """Get constraints of a tool."""
        facts = await self.query_facts(tool_name, "constraint")
        return [f.value for f in facts]

    async def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        async with self._lock:
            return {
                "fact_entries": len(self.entries),
                "fact_capacity": self.config.max_entries,
                "relations": len(self.relations),
                "relation_capacity": self.config.max_relations,
                "entities": len(self.entity_index),
                "avg_confidence": (
                    sum(e.confidence for e in self.entries.values())
                    / len(self.entries)
                    if self.entries
                    else 0.5
                ),
            }

    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self.entries.clear()
            self.relations.clear()
            self.entity_index.clear()
            logger.info("Cleared semantic memory")

    async def _enforce_capacity(self) -> None:
        """Remove low-confidence entries if over capacity."""
        if len(self.entries) <= self.config.max_entries:
            return

        # Sort by confidence and remove lowest confidence entries
        sorted_entries = sorted(
            self.entries.items(),
            key=lambda x: x[1].confidence,
        )

        to_remove = len(self.entries) - self.config.max_entries
        for entry_id, entry in sorted_entries[:to_remove]:
            # Update entity index
            if entry.entity in self.entity_index:
                self.entity_index[entry.entity].discard(entry_id)

            del self.entries[entry_id]

        logger.info(
            f"Enforced capacity: removed {to_remove} low-confidence entries"
        )
