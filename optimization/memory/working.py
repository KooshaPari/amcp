"""
Working Memory Implementation

Manages current context and active information:
- Current task goal and progress
- Available tools and their state
- Intermediate results and computations
- Active constraints and objectives

Key Features:
- LIFO context stack for nested reasoning
- Attention mechanism for relevance
- Binding of variables to values
- Automatic cleanup of completed contexts
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextFrame:
    """Single frame in working memory context stack."""
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    timestamp: float = field(default_factory=time.time)
    bindings: Dict[str, Any] = field(default_factory=dict)
    attention_weights: Dict[str, float] = field(default_factory=dict)
    intermediate_results: List[Dict[str, Any]] = field(default_factory=list)
    parent_frame_id: Optional[str] = None
    depth: int = 0

    @property
    def age_seconds(self) -> float:
        """How old this frame is."""
        return time.time() - self.timestamp

    def bind_variable(self, var_name: str, value: Any) -> None:
        """Bind a variable to a value."""
        self.bindings[var_name] = value

    def get_binding(self, var_name: str) -> Optional[Any]:
        """Get binding for a variable."""
        return self.bindings.get(var_name)

    def set_attention(self, item: str, weight: float) -> None:
        """Set attention weight for an item."""
        self.attention_weights[item] = max(0.0, min(1.0, weight))

    def get_attention(self, item: str) -> float:
        """Get attention weight for an item."""
        return self.attention_weights.get(item, 0.5)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frame_id": self.frame_id,
            "goal": self.goal,
            "bindings": self.bindings,
            "attention_weights": self.attention_weights,
            "intermediate_results": self.intermediate_results,
            "depth": self.depth,
            "age_seconds": self.age_seconds,
        }


@dataclass
class WorkingContext:
    """Current working memory state."""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    frame_stack: List[ContextFrame] = field(default_factory=list)
    global_bindings: Dict[str, Any] = field(default_factory=dict)
    focus_item: Optional[str] = None
    capacity: int = 100  # Max items in working memory

    @property
    def current_frame(self) -> Optional[ContextFrame]:
        """Get current (top) frame."""
        return self.frame_stack[-1] if self.frame_stack else None

    @property
    def size(self) -> int:
        """Total items in working memory."""
        size = len(self.global_bindings)
        for frame in self.frame_stack:
            size += len(frame.bindings) + len(frame.intermediate_results)
        return size

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "frame_count": len(self.frame_stack),
            "global_bindings": self.global_bindings,
            "focus": self.focus_item,
            "size": self.size,
            "capacity": self.capacity,
        }


@dataclass
class WorkingConfig:
    """Configuration for working memory."""
    max_contexts: int = 100
    max_frame_depth: int = 10
    max_bindings_per_frame: int = 50
    idle_timeout_seconds: float = 3600.0  # 1 hour
    enable_attention_mechanism: bool = True


class WorkingMemory:
    """Working memory system for current context."""

    def __init__(self, config: WorkingConfig):
        """Initialize working memory."""
        self.config = config
        self.contexts: Dict[str, WorkingContext] = {}
        self._current_context_id: Optional[str] = None
        self._lock = asyncio.Lock()

    async def create_context(self) -> str:
        """Create a new working context."""
        async with self._lock:
            context = WorkingContext()
            self.contexts[context.context_id] = context

            if not self._current_context_id:
                self._current_context_id = context.context_id

            logger.debug(f"Created working context {context.context_id}")
            return context.context_id

    async def push_frame(
        self,
        goal: str,
        context_id: Optional[str] = None,
    ) -> str:
        """Push a new frame onto the context stack."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                raise ValueError(f"Invalid context: {cid}")

            context = self.contexts[cid]

            # Check depth limit
            if len(context.frame_stack) >= self.config.max_frame_depth:
                raise RuntimeError(f"Max frame depth ({self.config.max_frame_depth}) exceeded")

            # Create frame
            parent_id = context.current_frame.frame_id if context.current_frame else None
            depth = len(context.frame_stack)

            frame = ContextFrame(
                goal=goal,
                parent_frame_id=parent_id,
                depth=depth,
            )

            context.frame_stack.append(frame)

            logger.debug(f"Pushed frame {frame.frame_id} (depth {depth}) in context {cid}")
            return frame.frame_id

    async def pop_frame(
        self,
        context_id: Optional[str] = None,
    ) -> Optional[ContextFrame]:
        """Pop frame from context stack."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                return None

            context = self.contexts[cid]
            if not context.frame_stack:
                return None

            frame = context.frame_stack.pop()
            logger.debug(f"Popped frame {frame.frame_id} from context {cid}")
            return frame

    async def bind_variable(
        self,
        var_name: str,
        value: Any,
        frame_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> bool:
        """Bind variable in current or specified frame."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                return False

            context = self.contexts[cid]

            if frame_id:
                # Find frame by ID
                frame = None
                for f in context.frame_stack:
                    if f.frame_id == frame_id:
                        frame = f
                        break
                if not frame:
                    return False
            else:
                # Use current frame
                frame = context.current_frame
                if not frame:
                    return False

            # Check capacity
            if len(frame.bindings) >= self.config.max_bindings_per_frame:
                logger.warning(
                    f"Frame {frame.frame_id} has reached binding capacity"
                )
                return False

            frame.bind_variable(var_name, value)
            return True

    async def get_variable(
        self,
        var_name: str,
        context_id: Optional[str] = None,
    ) -> Optional[Any]:
        """Get variable value, searching from current frame upward."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                return None

            context = self.contexts[cid]

            # Search from top frame downward
            for frame in reversed(context.frame_stack):
                if var_name in frame.bindings:
                    return frame.bindings[var_name]

            # Check global bindings
            return context.global_bindings.get(var_name)

    async def add_intermediate_result(
        self,
        result: Dict[str, Any],
        context_id: Optional[str] = None,
    ) -> bool:
        """Add intermediate computation result."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                return False

            context = self.contexts[cid]
            frame = context.current_frame
            if not frame:
                return False

            frame.intermediate_results.append(result)
            return True

    async def set_focus(
        self,
        item: str,
        context_id: Optional[str] = None,
    ) -> None:
        """Set attention focus to an item."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                return

            context = self.contexts[cid]
            context.focus_item = item

            # Increase attention weight for focused item
            if context.current_frame:
                context.current_frame.set_attention(item, 0.9)

    async def get_context(self, context_id: Optional[str] = None) -> Optional[WorkingContext]:
        """Get context snapshot."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                return None
            return self.contexts[cid]

    async def clear_context(self, context_id: Optional[str] = None) -> bool:
        """Clear a context entirely."""
        async with self._lock:
            cid = context_id or self._current_context_id
            if not cid or cid not in self.contexts:
                return False

            del self.contexts[cid]

            if self._current_context_id == cid:
                self._current_context_id = None

            logger.info(f"Cleared context {cid}")
            return True

    async def cleanup_idle(self) -> int:
        """Remove idle contexts. Returns count removed."""
        async with self._lock:
            now = time.time()
            to_remove = []

            for cid, context in self.contexts.items():
                age = now - context.timestamp
                if age > self.config.idle_timeout_seconds:
                    to_remove.append(cid)

            for cid in to_remove:
                del self.contexts[cid]

            if self._current_context_id in to_remove:
                self._current_context_id = None

            return len(to_remove)

    async def stats(self) -> Dict[str, Any]:
        """Get working memory statistics."""
        async with self._lock:
            if not self.contexts:
                return {
                    "contexts": 0,
                    "total_frames": 0,
                    "total_bindings": 0,
                    "capacity_utilization": 0.0,
                }

            total_frames = sum(len(c.frame_stack) for c in self.contexts.values())
            total_bindings = sum(
                sum(len(f.bindings) for f in c.frame_stack)
                for c in self.contexts.values()
            )

            return {
                "contexts": len(self.contexts),
                "max_contexts": self.config.max_contexts,
                "total_frames": total_frames,
                "total_bindings": total_bindings,
                "capacity_utilization": total_bindings / (
                    self.config.max_contexts *
                    self.config.max_frame_depth *
                    self.config.max_bindings_per_frame
                ),
            }

    async def clear_all(self) -> None:
        """Clear all contexts."""
        async with self._lock:
            self.contexts.clear()
            self._current_context_id = None
            logger.info("Cleared all working memory contexts")
