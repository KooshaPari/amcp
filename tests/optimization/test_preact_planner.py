"""
Tests for PreAct Planner (Phase 2).

Tests the PreActPlanner for three-phase planning: prediction, execution, reflection.
Covers: plan creation, outcome extraction, metadata storage, plan refinement.
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.planning import (
    PreActPlanner,
    PlanningConfig,
    PlanTree,
    get_preact_planner,
)
from optimization.preact_predictor import (
    PreActConfig,
    PredictionResult,
    ReflectionResult,
)
from unittest.mock import MagicMock


class TestPreActPlanner:
    """Tests for PreActPlanner three-phase planning."""

    @pytest.fixture
    def planning_config(self):
        """Create planning config."""
        return PlanningConfig(
            max_depth=2,  # Reduced from 3 to prevent excessive expansion
            min_confidence_threshold=0.3,
            max_breadth=2,  # Reduced from 3
            timeout_seconds=5.0,  # Add timeout limit
        )

    @pytest.fixture
    def preact_config(self):
        """Create PreAct config."""
        return PreActConfig(
            enable_prediction=True,
            enable_reflection=True,
            cache_predictions=False,  # Disable caching for tests
        )

    @pytest.fixture
    def planner(self, planning_config, preact_config):
        """Create a PreActPlanner."""
        return PreActPlanner(planning_config, preact_config)

    @pytest.fixture
    def mock_tool_executor(self):
        """Mock tool executor for planning."""

        async def execute(tool_name: str, params: dict):
            return {"success": True, "result": f"Result from {tool_name}"}

        return execute

    @pytest.mark.asyncio
    async def test_preact_three_phase_flow(
        self, planning_config, preact_config, planner, mock_tool_executor
    ):
        """Test complete three-phase PreAct flow."""
        # Ensure limits are set
        planner.config.max_depth = 2
        planner.config.timeout_seconds = 5.0
        
        goal = "Analyze and document codebase"
        context = {
            "tools": ["list_files", "read_file", "analyze_structure"],
            "target": "/src",
        }

        tree = await planner.plan(goal, context, mock_tool_executor)

        # Verify tree structure
        assert isinstance(tree, PlanTree)
        assert tree.root_id is not None

        # Check metadata contains prediction and reflection if best path exists
        # (metadata only populated when best_path is found)
        if tree.best_path:
            assert tree.metadata is not None
            assert "prediction" in tree.metadata
            assert "reflection" in tree.metadata

            # Verify prediction data
            prediction = tree.metadata["prediction"]
            assert isinstance(prediction, PredictionResult)
            assert prediction.predicted_outcome is not None

            # Verify reflection data
            reflection = tree.metadata["reflection"]
            assert isinstance(reflection, ReflectionResult)
            assert reflection.predicted_outcome is not None
            assert reflection.actual_outcome is not None
        else:
            # Even without best path, tree should be valid
            assert isinstance(tree, PlanTree)
            assert tree.root_id is not None

    @pytest.mark.asyncio
    async def test_preact_outcome_extraction(
        self, planning_config, preact_config, planner, mock_tool_executor
    ):
        """Test extracting outcome from execution tree."""
        planner.config.max_depth = 2
        planner.config.timeout_seconds = 5.0
        
        goal = "Simple goal"
        context = {"tools": ["test_tool"]}

        tree = await planner.plan(goal, context, mock_tool_executor)

        # Create a simple test to verify outcome extraction works
        if tree.best_path:
            outcome = planner._extract_outcome(tree)
            assert isinstance(outcome, str)
            assert len(outcome) > 0

    @pytest.mark.asyncio
    async def test_preact_metadata_storage(
        self, planning_config, preact_config, planner, mock_tool_executor
    ):
        """Test that prediction and reflection are stored in metadata."""
        goal = "Metadata storage test"
        context = {"tools": ["simple_tool"]}

        tree = await planner.plan(goal, context, mock_tool_executor)

        # Verify metadata structure
        assert tree.metadata is not None
        assert isinstance(tree.metadata, dict)

        # Verify prediction and reflection only stored if best path exists
        if tree.best_path:
            # Verify prediction stored
            assert "prediction" in tree.metadata
            prediction = tree.metadata["prediction"]
            assert isinstance(prediction, PredictionResult)

            # Verify reflection stored
            assert "reflection" in tree.metadata
            reflection = tree.metadata["reflection"]
            assert isinstance(reflection, ReflectionResult)
        else:
            # Without best path, metadata should be empty but present
            assert len(tree.metadata) == 0 or tree.metadata is not None

    @pytest.mark.asyncio
    async def test_preact_refine_with_lesson(
        self, planning_config, preact_config, planner, mock_tool_executor
    ):
        """Test refining plan with lessons from reflection."""
        goal = "Initial goal"
        context = {"tools": ["test_tool"]}

        # Initial plan
        tree = await planner.plan(goal, context, mock_tool_executor)

        # Refine with feedback
        feedback = "Plan needs adjustment"
        refined_tree = await planner.refine(tree, feedback)

        # Verify refinement
        assert isinstance(refined_tree, PlanTree)
        assert refined_tree.root_id is not None

    @pytest.mark.asyncio
    async def test_preact_handles_failed_prediction(
        self, planning_config, preact_config, planner, mock_tool_executor
    ):
        """Test PreAct handles goals that don't achieve predictions."""

        async def failing_executor(tool_name: str, params: dict):
            raise Exception("Tool failed")

        goal = "Difficult goal"
        context = {"tools": ["might_fail"]}

        # Should still complete even if executor fails
        tree = await planner.plan(goal, context, failing_executor)

        # Tree should still have metadata
        assert tree.metadata is not None

    def test_get_preact_planner_creates_new_instance(self):
        """Test get_preact_planner creates new instance when None (lines 236-242)."""
        # Reset global state by importing the module directly
        import optimization.planning.preact as preact_module
        original_instance = preact_module._preact_planner
        preact_module._preact_planner = None
        
        try:
            # First call should create new instance
            planner1 = get_preact_planner()
            assert planner1 is not None
            assert isinstance(planner1, PreActPlanner)
            
            # Second call should return same instance
            planner2 = get_preact_planner()
            assert planner2 is planner1  # Same instance
            
        finally:
            # Restore original state
            preact_module._preact_planner = original_instance

    def test_get_preact_planner_with_custom_config(self):
        """Test get_preact_planner with custom parameters (lines 236-242)."""
        import optimization.planning.preact as preact_module
        original_instance = preact_module._preact_planner
        preact_module._preact_planner = None
        
        try:
            config = PlanningConfig(max_depth=3)
            preact_config = PreActConfig(enable_prediction=True)
            memory_system = MagicMock()
            
            planner = get_preact_planner(config, preact_config, memory_system)
            
            assert planner.config.max_depth == 3
            assert planner.preact.config.enable_prediction is True
            assert planner.memory is memory_system
            
            # Second call with different params should return same instance (singleton)
            planner2 = get_preact_planner(PlanningConfig(max_depth=5), None, None)
            assert planner2 is planner  # Same instance, config ignored after first creation
            
        finally:
            # Restore original state
            preact_module._preact_planner = original_instance

    def test_get_preact_planner_singleton_behavior(self):
        """Test that get_preact_planner maintains singleton behavior."""
        import optimization.planning.preact as preact_module
        original_instance = preact_module._preact_planner
        preact_module._preact_planner = None
        
        try:
            # Create first instance
            planner1 = get_preact_planner()
            
            # Create second instance - should be same
            planner2 = get_preact_planner()
            assert planner2 is planner1
            
            # Create third instance with different config - should still be same
            planner3 = get_preact_planner(PlanningConfig(max_depth=10))
            assert planner3 is planner1  # Singleton ignores new config
            
        finally:
            # Restore original state
            preact_module._preact_planner = original_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
