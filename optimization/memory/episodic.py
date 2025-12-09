"""
Episodic Memory Implementation

Stores task history and past experiences:
- Goal + Context → Outcome mapping
- Success/failure lessons learned
- Confidence calibration from experience
- Similar task retrieval for analogical reasoning

Key Features:
- Temporal ordering of events
- Task similarity search (embedding-based)
- Outcome prediction from history
- Lesson extraction and storage
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class TaskOutcome(str, Enum):
    """Result of a task execution."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class EpisodicEntry:
    """Single episodic memory entry."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    goal: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    tools_used: List[str] = field(default_factory=list)
    outcome: TaskOutcome = TaskOutcome.SUCCESS
    result: Optional[Dict[str, Any]] = None
    confidence: float = 0.5
    duration: float = 0.0
    lesson_learned: Optional[str] = None
    similar_past_tasks: List[str] = field(default_factory=list)

    @property
    def age_seconds(self) -> float:
        """How old this entry is in seconds."""
        return time.time() - self.timestamp

    @property
    def recency_score(self) -> float:
        """Score 1.0 (recent) to 0.0 (old). Decays over 30 days."""
        max_age = 30 * 24 * 3600  # 30 days in seconds
        age = min(self.age_seconds, max_age)
        return max(0.0, 1.0 - (age / max_age))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "goal": self.goal,
            "context": self.context,
            "tools_used": self.tools_used,
            "outcome": self.outcome.value,
            "result": self.result,
            "confidence": self.confidence,
            "duration": self.duration,
            "lesson_learned": self.lesson_learned,
            "age_seconds": self.age_seconds,
            "recency_score": self.recency_score,
        }


@dataclass
class EpisodicConfig:
    """Configuration for episodic memory."""
    max_entries: int = 1000
    enable_similarity_search: bool = True
    similarity_threshold: float = 0.7
    max_similar_tasks: int = 5
    retention_days: int = 90
    success_weight: float = 2.0  # Recent successes weighted higher
    failure_weight: float = 1.0  # Failures learn lessons


class EpisodicMemory:
    """Episodic memory system for task history."""

    def __init__(self, config: EpisodicConfig):
        """Initialize episodic memory."""
        self.config = config
        self.entries: Dict[str, EpisodicEntry] = {}
        self.access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def store(
        self,
        goal: str,
        context: Dict[str, Any],
        tools_used: List[str],
        outcome: TaskOutcome,
        result: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
        duration: float = 0.0,
        lesson_learned: Optional[str] = None,
    ) -> str:
        """Store a task execution in episodic memory."""
        async with self._lock:
            entry = EpisodicEntry(
                goal=goal,
                context=context,
                tools_used=tools_used,
                outcome=outcome,
                result=result,
                confidence=confidence,
                duration=duration,
                lesson_learned=lesson_learned,
            )

            # Find similar past tasks
            if self.config.enable_similarity_search:
                similar = await self._find_similar(goal, context)
                entry.similar_past_tasks = [e.entry_id for e in similar]

            self.entries[entry.entry_id] = entry
            self.access_times[entry.entry_id] = time.time()

            # Enforce capacity limit
            await self._enforce_capacity()

            logger.info(
                f"Stored episodic entry {entry.entry_id}: "
                f"{goal} → {outcome.value}"
            )

            return entry.entry_id

    async def retrieve(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 5,
    ) -> List[EpisodicEntry]:
        """Retrieve relevant past experiences."""
        async with self._lock:
            candidates = []

            for entry in self.entries.values():
                # Filter by temporal relevance and outcome type
                if entry.age_seconds > self.config.retention_days * 86400:
                    continue

                # Simple goal matching (can be enhanced with embeddings)
                if goal.lower() in entry.goal.lower() or \
                   entry.goal.lower() in goal.lower():
                    score = entry.recency_score
                    if entry.outcome == TaskOutcome.SUCCESS:
                        score *= self.config.success_weight
                    candidates.append((entry, score))

            # Sort by score and return top K
            candidates.sort(key=lambda x: x[1], reverse=True)
            return [entry for entry, _ in candidates[:limit]]

    async def retrieve_similar(
        self,
        entry_id: str,
        limit: int = 5,
    ) -> List[EpisodicEntry]:
        """Retrieve tasks similar to a given entry."""
        async with self._lock:
            if entry_id not in self.entries:
                return []

            entry = self.entries[entry_id]
            similar_ids = entry.similar_past_tasks[:limit]

            return [
                self.entries[sid]
                for sid in similar_ids
                if sid in self.entries
            ]

    async def update_confidence(
        self,
        entry_id: str,
        new_confidence: float,
    ) -> bool:
        """Update confidence score after reflection."""
        async with self._lock:
            if entry_id not in self.entries:
                return False

            entry = self.entries[entry_id]
            old_confidence = entry.confidence
            entry.confidence = max(0.0, min(1.0, new_confidence))
            self.access_times[entry_id] = time.time()

            logger.debug(
                f"Updated confidence for {entry_id}: "
                f"{old_confidence:.2f} → {new_confidence:.2f}"
            )
            return True

    async def get_lessons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get lessons learned from past experiences."""
        async with self._lock:
            lessons = []

            for entry in self.entries.values():
                if entry.lesson_learned and entry.outcome != TaskOutcome.SUCCESS:
                    lessons.append({
                        "goal": entry.goal,
                        "lesson": entry.lesson_learned,
                        "outcome": entry.outcome.value,
                        "confidence": entry.confidence,
                        "age_days": entry.age_seconds / 86400,
                    })

            # Sort by recency and relevance
            lessons.sort(
                key=lambda x: (
                    x["confidence"],
                    -x["age_days"],
                ),
                reverse=True,
            )

            return lessons[:limit]

    async def get_success_rate(
        self,
        goal_prefix: str = "",
    ) -> float:
        """Calculate success rate for tasks matching goal."""
        async with self._lock:
            if not self.entries:
                return 0.5

            matching = [
                e for e in self.entries.values()
                if not goal_prefix or goal_prefix.lower() in e.goal.lower()
            ]

            if not matching:
                return 0.5

            successes = sum(
                1 for e in matching
                if e.outcome == TaskOutcome.SUCCESS
            )

            return successes / len(matching)

    async def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        async with self._lock:
            if not self.entries:
                return {
                    "total_entries": 0,
                    "successful_tasks": 0,
                    "success_rate": 0.5,
                    "avg_confidence": 0.5,
                }

            successful = sum(
                1 for e in self.entries.values()
                if e.outcome == TaskOutcome.SUCCESS
            )

            avg_confidence = sum(
                e.confidence for e in self.entries.values()
            ) / len(self.entries)

            return {
                "total_entries": len(self.entries),
                "capacity": self.config.max_entries,
                "utilization": len(self.entries) / self.config.max_entries,
                "successful_tasks": successful,
                "success_rate": successful / len(self.entries),
                "avg_confidence": avg_confidence,
                "avg_duration": sum(
                    e.duration for e in self.entries.values()
                ) / len(self.entries),
            }

    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self.entries.clear()
            self.access_times.clear()
            logger.info("Cleared episodic memory")

    async def _find_similar(
        self,
        goal: str,
        context: Dict[str, Any],
    ) -> List[EpisodicEntry]:
        """Find similar past tasks (simple keyword matching)."""
        candidates = []

        for entry in self.entries.values():
            # Goal similarity (can be enhanced with embeddings)
            goal_overlap = self._calculate_overlap(goal, entry.goal)

            # Context similarity
            context_overlap = self._calculate_overlap(
                json.dumps(context, sort_keys=True),
                json.dumps(entry.context, sort_keys=True),
            )

            similarity = (goal_overlap * 0.7 + context_overlap * 0.3)

            if similarity >= self.config.similarity_threshold:
                candidates.append((entry, similarity))

        # Sort by similarity and return
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in candidates[:self.config.max_similar_tasks]]

    @staticmethod
    def _calculate_overlap(str1: str, str2: str) -> float:
        """Calculate string similarity using word overlap."""
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        union = len(words1 | words2)

        return overlap / union if union > 0 else 0.0

    async def _enforce_capacity(self) -> None:
        """Remove least recently used entries if over capacity."""
        if len(self.entries) <= self.config.max_entries:
            return

        # Sort by access time
        sorted_ids = sorted(
            self.access_times.items(),
            key=lambda x: x[1],
        )

        # Remove oldest entries until under capacity
        to_remove = len(self.entries) - self.config.max_entries
        for entry_id, _ in sorted_ids[:to_remove]:
            del self.entries[entry_id]
            del self.access_times[entry_id]

        logger.info(
            f"Enforced capacity: removed {to_remove} entries, "
            f"now {len(self.entries)} entries"
        )
