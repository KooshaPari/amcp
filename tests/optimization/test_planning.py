"""
Tests for ReAcTree Planning Strategy.

Tests the ReAcTreePlanner for hierarchical planning and execution.
Covers: plan creation, node states, tree operations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.planning.reactree import ReAcTreePlanner
from optimization.planning.types import (
    PlanningConfig,
    PlanNode,
    PlanTree,
    NodeStatus,
)


class TestReAcTreePlanner:
    """Tests for ReAcTreePlanner."""

    @pytest.fixture
    def planner(self):
        """Create planner."""
        config = PlanningConfig(
            max_depth=3,
            timeout_seconds=10.0,
        )
        return ReAcTreePlanner(config)

    @pytest.mark.asyncio
    async def test_plan_creation(self, planner):
        """Test basic plan creation."""
        # Limit depth and timeout to prevent excessive memory usage
        planner.config.max_depth = 2
        planner.config.timeout_seconds = 2.0
        
        async def mock_executor(tool: str, input: dict) -> str:
            return "done successfully"  # Trigger goal completion

        tree = await planner.plan(
            goal="Find and analyze the test file",
            context={"tools": ["search", "read_file"]},
            tool_executor=mock_executor,
        )

        assert tree.root_id is not None
        assert len(tree.nodes) > 0

    @pytest.mark.asyncio
    async def test_plan_node_states(self, planner):
        """Test plan node state transitions."""
        node = PlanNode(
            id="test_node",
            thought="Initial thought",
        )

        assert node.status == NodeStatus.PENDING

        node.mark_completed("Done")
        assert node.status == NodeStatus.COMPLETED
        assert node.observation == "Done"

    def test_plan_tree_operations(self):
        """Test PlanTree operations."""
        tree = PlanTree()

        # Add root
        root = PlanNode(id="root", thought="Root thought")
        tree.root_id = root.id
        tree.add_node(root)

        # Add child
        child = PlanNode(id="child", thought="Child thought", parent_id="root")
        tree.add_node(child)

        # Verify structure
        assert tree.get_node("root") == root
        assert tree.get_node("child") == child
        assert tree.get_children("root") == [child]
        assert tree.get_depth("child") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
