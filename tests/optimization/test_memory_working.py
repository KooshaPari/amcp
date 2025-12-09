"""
Comprehensive tests for working memory system.

Tests core functionality:
- Context stack management
- Variable binding and retrieval
- Attention mechanism
- Intermediate result storage
- Capacity management
"""

import asyncio
import pytest
import time

from optimization.memory.working import (
    WorkingMemory,
    ContextFrame,
    WorkingContext,
)


class TestContextFrame:
    """Test ContextFrame dataclass."""

    def test_frame_creation(self):
        """Test creating a context frame."""
        frame = ContextFrame(
            goal="Process user request",
            bindings={"user_id": "123", "request_type": "query"},
            attention_weights={"input": 0.9, "output": 0.7},
            intermediate_results=[{"step": 1, "result": "parsed"}],
        )

        assert frame.goal == "Process user request"
        assert frame.bindings == {"user_id": "123", "request_type": "query"}
        assert frame.attention_weights == {"input": 0.9, "output": 0.7}
        assert frame.intermediate_results == [{"step": 1, "result": "parsed"}]
        assert frame.frame_id is not None
        assert frame.timestamp > 0
        assert frame.depth == 0

    def test_age_calculation(self):
        """Test age calculation."""
        past_time = time.time() - 100
        frame = ContextFrame(timestamp=past_time)
        
        assert frame.age_seconds >= 99
        assert frame.age_seconds <= 101

    def test_variable_binding(self):
        """Test variable binding and retrieval."""
        frame = ContextFrame()
        
        # Bind variable
        frame.bind_variable("user_id", "test_user")
        assert frame.get_binding("user_id") == "test_user"
        
        # Override binding
        frame.bind_variable("user_id", "updated_user")
        assert frame.get_binding("user_id") == "updated_user"
        
        # Get non-existent binding
        assert frame.get_binding("non_existent") is None

    def test_attention_weights(self):
        """Test attention weight management."""
        frame = ContextFrame()
        
        # Set attention
        frame.set_attention("input", 0.8)
        assert frame.get_attention("input") == 0.8
        
        # Test bounds - should clamp to [0, 1]
        frame.set_attention("test", 1.5)
        assert frame.get_attention("test") == 1.0
        
        frame.set_attention("test", -0.5)
        assert frame.get_attention("test") == 0.0
        
        # Default attention for unknown item
        assert frame.get_attention("unknown") == 0.5

    def test_to_dict(self):
        """Test dictionary conversion."""
        frame = ContextFrame(
            goal="Test goal",
            bindings={"var": "val"},
            attention_weights={"item": 0.7},
            intermediate_results=[{"result": "test"}],
            depth=2,
        )

        d = frame.to_dict()
        assert d["goal"] == "Test goal"
        assert d["bindings"] == {"var": "val"}
        assert d["attention_weights"] == {"item": 0.7}
        assert d["intermediate_results"] == [{"result": "test"}]
        assert d["depth"] == 2
        assert "age_seconds" in d


class TestWorkingContext:
    """Test WorkingContext dataclass."""

    def test_context_creation(self):
        """Test creating a working context."""
        frame1 = ContextFrame(goal="Task 1", depth=1)
        frame2 = ContextFrame(goal="Task 2", depth=2, parent_frame_id=frame1.frame_id)
        
        context = WorkingContext(
            frame_stack=[frame1, frame2],
            global_bindings={"user": "test"},
            focus_item="current_task",
            capacity=50,
        )

        assert len(context.frame_stack) == 2
        assert context.global_bindings == {"user": "test"}
        assert context.focus_item == "current_task"
        assert context.capacity == 50
        assert context.context_id is not None
        assert context.timestamp > 0

    def test_current_frame(self):
        """Test getting current frame."""
        frame1 = ContextFrame(goal="Bottom")
        frame2 = ContextFrame(goal="Top")
        
        context = WorkingContext(frame_stack=[frame1, frame2])
        
        # Current frame should be the last one
        assert context.current_frame == frame2
        assert context.current_frame.goal == "Top"

    def test_current_frame_empty_stack(self):
        """Test current frame with empty stack."""
        context = WorkingContext(frame_stack=[])
        assert context.current_frame is None

    def test_size_calculation(self):
        """Test size calculation."""
        frame1 = ContextFrame(
            bindings={"a": 1, "b": 2},
            intermediate_results=[{"x": 1}, {"y": 2}],
        )
        frame2 = ContextFrame(
            bindings={"c": 3},
            intermediate_results=[{"z": 3}],
        )
        
        context = WorkingContext(
            frame_stack=[frame1, frame2],
            global_bindings={"global": "value"},
        )

        # Size = global_bindings (1) + frame1 bindings (2) + frame1 results (2) + frame2 bindings (1) + frame2 results (1)
        assert context.size == 7

    def test_to_dict(self):
        """Test dictionary conversion."""
        context = WorkingContext(
            frame_stack=[ContextFrame(goal="Test")],
            global_bindings={"key": "val"},
            focus_item="focus",
        )

        d = context.to_dict()
        assert d["frame_count"] == 1
        assert d["global_bindings"] == {"key": "val"}
        assert d["focus_item"] == "focus"
        assert "context_id" in d
        assert "size" in d


class TestWorkingMemory:
    """Test WorkingMemory class."""

    @pytest.fixture
    async def memory(self):
        """Create working memory instance."""
        return WorkingMemory()

    async def test_create_context(self, memory):
        """Test creating a new working context."""
        context_id = await memory.create_context(
            initial_goal="Main task",
            capacity=100,
        )

        assert context_id is not None
        assert context_id in memory.contexts
        
        context = memory.contexts[context_id]
        assert len(context.frame_stack) == 1
        assert context.current_frame.goal == "Main task"
        assert context.capacity == 100

    async def test_create_context_with_bindings(self, memory):
        """Test creating context with initial bindings."""
        initial_bindings = {"user_id": "123", "session": "abc"}
        
        context_id = await memory.create_context(
            initial_goal="Task",
            initial_bindings=initial_bindings,
        )

        context = memory.contexts[context_id]
        assert context.global_bindings == initial_bindings

    async def test_push_frame(self, memory):
        """Test pushing a new frame."""
        # Create context
        context_id = await memory.create_context("Main task")
        
        # Push new frame
        frame_id = await memory.push_frame(
            context_id,
            goal="Subtask",
            parent_frame_id=None,  # Will be set to current frame
        )

        assert frame_id is not None
        
        context = memory.contexts[context_id]
        assert len(context.frame_stack) == 2
        
        new_frame = context.current_frame
        assert new_frame.goal == "Subtask"
        assert new_frame.depth == 1
        assert new_frame.parent_frame_id is not None

    async def test_push_frame_with_parent(self, memory):
        """Test pushing frame with specific parent."""
        context_id = await memory.create_context("Main")
        
        # Push first frame
        frame1_id = await memory.push_frame(context_id, "Subtask 1")
        
        # Push second frame as child of first
        frame2_id = await memory.push_frame(
            context_id,
            "Subtask 2",
            parent_frame_id=frame1_id,
        )

        context = memory.contexts[context_id]
        frame2 = None
        for frame in context.frame_stack:
            if frame.frame_id == frame2_id:
                frame2 = frame
                break
        
        assert frame2 is not None
        assert frame2.parent_frame_id == frame1_id
        assert frame2.depth == 2

    async def test_pop_frame(self, memory):
        """Test popping a frame."""
        context_id = await memory.create_context("Main")
        
        # Push some frames
        await memory.push_frame(context_id, "Subtask 1")
        await memory.push_frame(context_id, "Subtask 2")
        
        context = memory.contexts[context_id]
        assert len(context.frame_stack) == 3
        
        # Pop frame
        popped_frame = await memory.pop_frame(context_id)
        
        assert popped_frame is not None
        assert popped_frame.goal == "Subtask 2"
        
        context = memory.contexts[context_id]
        assert len(context.frame_stack) == 2
        assert context.current_frame.goal == "Subtask 1"

    async def test_pop_frame_empty_stack(self, memory):
        """Test popping from empty stack."""
        context_id = await memory.create_context("Main")
        
        # Pop the only frame
        popped = await memory.pop_frame(context_id)
        assert popped is not None
        
        # Try to pop again
        popped = await memory.pop_frame(context_id)
        assert popped is None

    async def test_bind_variable_global(self, memory):
        """Test binding global variable."""
        context_id = await memory.create_context("Main")
        
        success = await memory.bind_variable(
            context_id,
            "user_id",
            "test_user",
            global_binding=True,
        )
        
        assert success
        
        context = memory.contexts[context_id]
        assert context.global_bindings["user_id"] == "test_user"

    async def test_bind_variable_frame(self, memory):
        """Test binding variable in current frame."""
        context_id = await memory.create_context("Main")
        
        success = await memory.bind_variable(
            context_id,
            "local_var",
            "local_value",
            global_binding=False,
        )
        
        assert success
        
        context = memory.contexts[context_id]
        current_frame = context.current_frame
        assert current_frame.get_binding("local_var") == "local_value"

    async def test_get_variable(self, memory):
        """Test retrieving variable with fallback."""
        context_id = await memory.create_context("Main")
        
        # Set global and local bindings
        await memory.bind_variable(context_id, "shared", "global_value", global_binding=True)
        await memory.bind_variable(context_id, "local", "local_value", global_binding=False)
        
        # Test variable retrieval
        assert await memory.get_variable(context_id, "local") == "local_value"
        assert await memory.get_variable(context_id, "shared") == "global_value"
        assert await memory.get_variable(context_id, "nonexistent") is None

    async def test_set_attention(self, memory):
        """Test setting attention weights."""
        context_id = await memory.create_context("Main")
        
        success = await memory.set_attention(context_id, "input", 0.9)
        assert success
        
        context = memory.contexts[context_id]
        assert context.current_frame.get_attention("input") == 0.9

    async def test_add_intermediate_result(self, memory):
        """Test adding intermediate results."""
        context_id = await memory.create_context("Main")
        
        result = {"step": 1, "data": "processed"}
        success = await memory.add_intermediate_result(context_id, result)
        
        assert success
        
        context = memory.contexts[context_id]
        current_frame = context.current_frame
        assert result in current_frame.intermediate_results

    async def test_set_focus(self, memory):
        """Test setting focus item."""
        context_id = await memory.create_context("Main")
        
        success = await memory.set_focus(context_id, "current_subtask")
        assert success
        
        context = memory.contexts[context_id]
        assert context.focus_item == "current_subtask"

    async def test_get_context(self, memory):
        """Test getting context information."""
        context_id = await memory.create_context("Main")
        await memory.bind_variable(context_id, "user", "test", global_binding=True)
        await memory.push_frame(context_id, "Subtask")
        
        info = await memory.get_context(context_id)
        
        assert info["context_id"] == context_id
        assert info["goal"] == "Subtask"  # Current frame
        assert info["depth"] == 1
        assert info["size"] > 0
        assert info["focus_item"] is not None

    async def test_clear_context(self, memory):
        """Test clearing a context."""
        context_id = await memory.create_context("Main")
        await memory.bind_variable(context_id, "var", "val")
        await memory.push_frame(context_id, "Subtask")
        
        # Verify data exists
        context = memory.contexts[context_id]
        assert len(context.frame_stack) > 0
        assert len(context.global_bindings) > 0
        
        # Clear context
        await memory.clear_context(context_id)
        
        # Should be empty
        assert context_id in memory.contexts  # Context still exists
        context = memory.contexts[context_id]
        assert len(context.frame_stack) == 0
        assert len(context.global_bindings) == 0

    async def test_remove_context(self, memory):
        """Test removing a context."""
        context_id = await memory.create_context("Main")
        
        assert context_id in memory.contexts
        
        await memory.remove_context(context_id)
        
        assert context_id not in memory.contexts

    async def test_capacity_enforcement(self, memory):
        """Test capacity enforcement."""
        context_id = await memory.create_context("Main", capacity=10)
        
        # Fill up to capacity
        for i in range(10):
            await memory.bind_variable(context_id, f"var{i}", f"val{i}")
        
        context = memory.contexts[context_id]
        assert context.size == 10
        
        # Try to add one more - should enforce capacity
        success = await memory.bind_variable(context_id, "overflow", "value")
        
        # Should either reject or remove old items (implementation dependent)
        # Here we just verify it doesn't crash
        context = memory.contexts[context_id]
        assert context.size <= context.capacity

    async def test_context_age_cleanup(self, memory):
        """Test cleanup of old contexts."""
        # Create context
        context_id = await memory.create_context("Test")
        
        # Manually age it
        context = memory.contexts[context_id]
        context.timestamp = time.time() - (2 * 3600)  # 2 hours old
        
        # Cleanup old contexts (assuming 1 hour threshold)
        await memory.cleanup_old_contexts(max_age_seconds=3600)
        
        # Context should be removed
        assert context_id not in memory.contexts

    async def test_concurrent_context_operations(self, memory):
        """Test concurrent operations on contexts."""
        # Create multiple contexts
        context_ids = []
        for i in range(5):
            ctx_id = await memory.create_context(f"Context {i}")
            context_ids.append(ctx_id)
        
        # Concurrent operations
        tasks = []
        for i, ctx_id in enumerate(context_ids):
            # Bind variable
            tasks.append(memory.bind_variable(ctx_id, f"var{i}", f"val{i}"))
            # Push frame
            tasks.append(memory.push_frame(ctx_id, f"Frame {i}"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
        
        # Verify all contexts have their data
        for i, ctx_id in enumerate(context_ids):
            context = memory.contexts[ctx_id]
            assert len(context.frame_stack) == 2  # Initial + pushed
            assert context.global_bindings.get(f"var{i}") == f"val{i}"

    async def test_frame_hierarchy(self, memory):
        """Test frame hierarchy tracking."""
        context_id = await memory.create_context("Root")
        
        # Build hierarchy
        frame1_id = await memory.push_frame(context_id, "Level 1")
        frame2_id = await memory.push_frame(context_id, "Level 2")
        frame3_id = await memory.push_frame(context_id, "Level 3")
        
        context = memory.contexts[context_id]
        frames = context.frame_stack
        
        # Check hierarchy
        assert frames[0].frame_id not in [f.parent_frame_id for f in frames]  # Root has no parent
        assert frames[1].parent_frame_id == frames[0].frame_id
        assert frames[2].parent_frame_id == frames[1].frame_id
        assert frames[3].parent_frame_id == frames[2].frame_id
        
        # Check depths
        assert frames[0].depth == 0
        assert frames[1].depth == 1
        assert frames[2].depth == 2
        assert frames[3].depth == 3

    async def test_variable_scope_resolution(self, memory):
        """Test variable scope resolution."""
        context_id = await memory.create_context("Root")
        
        # Set variables at different levels
        await memory.bind_variable(context_id, "global", "root_value", global_binding=True)
        
        await memory.push_frame(context_id, "Level 1")
        await memory.bind_variable(context_id, "local1", "level1_value", global_binding=False)
        
        await memory.push_frame(context_id, "Level 2")
        await memory.bind_variable(context_id, "local2", "level2_value", global_binding=False)
        
        # Test scope resolution
        assert await memory.get_variable(context_id, "local2") == "level2_value"
        assert await memory.get_variable(context_id, "local1") == "level1_value"
        assert await memory.get_variable(context_id, "global") == "root_value"

    async def test_stats(self, memory):
        """Test memory statistics."""
        # Create some contexts
        ctx1 = await memory.create_context("Context 1")
        ctx2 = await memory.create_context("Context 2")
        
        # Add some data
        await memory.bind_variable(ctx1, "var", "val")
        await memory.push_frame(ctx2, "Frame")
        
        stats = await memory.stats()
        
        assert stats["total_contexts"] == 2
        assert stats["active_frames"] == 3  # 2 initial + 1 pushed
        assert stats["total_variables"] >= 1
        assert stats["total_intermediate_results"] >= 0

    async def test_clear_all(self, memory):
        """Test clearing all contexts."""
        # Create contexts
        ctx1 = await memory.create_context("Context 1")
        ctx2 = await memory.create_context("Context 2")
        
        assert len(memory.contexts) == 2
        
        # Clear all
        await memory.clear_all()
        
        assert len(memory.contexts) == 0

    async def test_attention_decay(self, memory):
        """Test attention weight decay over time."""
        context_id = await memory.create_context("Test")
        
        # Set attention
        await memory.set_attention(context_id, "item", 0.9)
        
        # Manually age the frame
        context = memory.contexts[context_id]
        frame = context.current_frame
        frame.timestamp = time.time() - 3600  # 1 hour old
        
        # Apply decay
        await memory.apply_attention_decay(context_id, decay_rate=0.1)
        
        # Attention should have decayed
        current_attention = frame.get_attention("item")
        assert current_attention < 0.9
        assert current_attention >= 0.0
