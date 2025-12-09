"""
Working Memory System Tests

Tests for working memory system in isolation.
"""

import pytest
from optimization.memory.working import WorkingConfig, WorkingMemory


@pytest.mark.asyncio
class TestWorkingMemory:
    """Test working memory system."""

    async def test_context_creation(self, working_memory):
        """Test context creation."""
        context_id = await working_memory.create_context()

        assert context_id in working_memory.contexts

        context = working_memory.contexts[context_id]
        assert context.frame_stack == []
        assert context.global_bindings == {}

    async def test_frame_stack_operations(self, working_memory):
        """Test frame push/pop."""
        context_id = await working_memory.create_context()

        # Push frame
        frame_id1 = await working_memory.push_frame("Goal 1", context_id)
        assert frame_id1

        frame_id2 = await working_memory.push_frame("Goal 2", context_id)
        assert frame_id2

        # Pop frame
        popped = await working_memory.pop_frame(context_id)
        assert popped.goal == "Goal 2"

        # Verify depth
        context = working_memory.contexts[context_id]
        assert len(context.frame_stack) == 1

    async def test_variable_binding_and_lookup(self, working_memory):
        """Test variable binding and lookup."""
        context_id = await working_memory.create_context()
        await working_memory.push_frame("Goal", context_id)

        # Bind variable
        success = await working_memory.bind_variable(
            "data",
            [1, 2, 3],
            context_id=context_id
        )
        assert success

        # Get variable
        value = await working_memory.get_variable("data", context_id)
        assert value == [1, 2, 3]

    async def test_frame_depth_limit(self, working_memory):
        """Test frame depth limit enforcement."""
        config = WorkingConfig(max_frame_depth=3)
        working_memory = WorkingMemory(config)

        context_id = await working_memory.create_context()

        # Push up to limit
        for i in range(3):
            await working_memory.push_frame(f"Goal {i}", context_id)

        # Should fail to push beyond limit
        with pytest.raises(RuntimeError):
            await working_memory.push_frame("Goal 3", context_id)

    async def test_variable_lookup_chain(self, working_memory):
        """Test variable lookup through frame stack."""
        context_id = await working_memory.create_context()

        # Push frame 1 with variable
        await working_memory.push_frame("Goal 1", context_id)
        await working_memory.bind_variable("x", 10, context_id=context_id)

        # Push frame 2
        await working_memory.push_frame("Goal 2", context_id)

        # Should find x from frame 1
        value = await working_memory.get_variable("x", context_id)
        assert value == 10

        # Bind new value in frame 2
        await working_memory.bind_variable("x", 20, context_id=context_id)

        # Should get frame 2's value
        value = await working_memory.get_variable("x", context_id)
        assert value == 20

    async def test_attention_mechanism(self, working_memory):
        """Test attention weights."""
        context_id = await working_memory.create_context()
        await working_memory.push_frame("Goal", context_id)

        context = working_memory.contexts[context_id]
        frame = context.current_frame

        # Set attention
        frame.set_attention("item_1", 0.9)
        frame.set_attention("item_2", 0.3)

        # Get attention
        assert frame.get_attention("item_1") == 0.9
        assert frame.get_attention("item_2") == 0.3
        assert frame.get_attention("unknown") == 0.5  # Default

    async def test_intermediate_results(self, working_memory):
        """Test storing intermediate results."""
        context_id = await working_memory.create_context()
        await working_memory.push_frame("Goal", context_id)

        # Add intermediate result
        success = await working_memory.add_intermediate_result(
            {"step": 1, "result": "partial"},
            context_id
        )
        assert success

        # Add another
        success = await working_memory.add_intermediate_result(
            {"step": 2, "result": "more_partial"},
            context_id
        )
        assert success

        # Verify results stored
        context = working_memory.contexts[context_id]
        frame = context.current_frame
        assert len(frame.intermediate_results) == 2
