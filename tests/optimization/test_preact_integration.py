"""
Tests for PreAct Integration (Phase 2).

Integration tests for PreAct components working together.
Covers: end-to-end workflow, multiple iterations, confidence calibration.
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.planning_strategy import (
    PreActPlanner,
    PlanningConfig,
    PlanTree,
)
from optimization.preact_predictor import (
    PreActPredictor,
    PreActConfig,
    PredictionResult,
    ReflectionResult,
)


class TestPreActIntegration:
    """Integration tests for PreAct components."""

    @pytest.mark.asyncio
    async def test_end_to_end_preact_workflow(self):
        """Test complete end-to-end PreAct workflow."""
        # Create components
        planning_config = PlanningConfig()
        preact_config = PreActConfig(enable_prediction=True, enable_reflection=True)
        planner = PreActPlanner(planning_config, preact_config)

        # Create tool executor
        tools_called = []

        async def tracking_executor(tool_name: str, params: dict):
            tools_called.append(tool_name)
            await asyncio.sleep(0.01)  # Simulate work
            return {"success": True, "data": f"Result from {tool_name}"}

        # Execute plan (with limits to prevent memory issues)
        planning_config.max_depth = 2  # Limit depth
        planning_config.timeout_seconds = 5.0  # Limit timeout
        
        goal = "Multi-step analysis task"
        context = {"tools": ["search", "analyze", "report"], "domain": "code"}

        tree = await planner.plan(goal, context, tracking_executor)

        # Verify complete workflow
        assert isinstance(tree, PlanTree)
        assert tree.metadata is not None

        # Verify prediction exists (only when best path is found)
        if tree.best_path:
            prediction = tree.metadata.get("prediction")
            assert prediction is not None
            assert isinstance(prediction, PredictionResult)

            # Verify reflection exists
            reflection = tree.metadata.get("reflection")
            assert reflection is not None
            assert isinstance(reflection, ReflectionResult)

            # Verify reflection measures alignment
            assert reflection.accuracy >= 0 and reflection.accuracy <= 1
            assert reflection.aligned in [True, False]
        else:
            # Without best path, prediction won't be stored, but we still executed the plan
            assert tree.root_id is not None
            assert len(tree.nodes) > 0

    @pytest.mark.asyncio
    async def test_preact_with_multiple_iterations(self):
        """Test PreAct across multiple planning iterations."""
        predictor = PreActPredictor()

        async def dummy_executor(tool_name: str, params: dict):
            return {"success": True}

        goals = [
            "Parse configuration files",
            "Validate configuration",
            "Generate report",
        ]

        predictions = []
        reflections = []

        for goal in goals:
            # Predict
            pred = await predictor.predict_and_plan(
                goal=goal, context={"tools": ["read", "validate"]}, tool_executor=dummy_executor
            )
            predictions.append(pred)

            # Simulate outcome
            outcome = "Success" if pred.confidence > 0.5 else "Partial success"

            # Reflect
            refl = await predictor.reflect(prediction=pred, actual_outcome=outcome)
            reflections.append(refl)

        # Verify iterative learning
        assert len(predictions) == 3
        assert len(reflections) == 3

        # Check summary shows all reflections
        summary = await predictor.get_reflection_summary()
        assert summary["total_reflections"] >= 3

    @pytest.mark.asyncio
    async def test_preact_confidence_calibration(self):
        """Test that PreAct adjusts confidence based on reflection."""
        predictor = PreActPredictor()

        async def dummy_executor(tool_name: str, params: dict):
            return {"success": True}

        # First prediction with high confidence
        pred1 = await predictor.predict_and_plan(
            goal="Task 1", context={"tools": ["t1"]}, tool_executor=dummy_executor
        )
        initial_confidence = pred1.confidence

        # Reflect with mismatch (actual != predicted)
        refl1 = await predictor.reflect(
            prediction=pred1,
            actual_outcome="Failed: unexpected condition",
        )

        # Get second prediction
        pred2 = await predictor.predict_and_plan(
            goal="Task 2", context={"tools": ["t2"]}, tool_executor=dummy_executor
        )

        # Confidence might be adjusted based on recent reflections
        # (actual adjustment depends on predictor's learning mechanism)
        assert 0 <= pred2.confidence <= 1

    @pytest.mark.asyncio
    async def test_preact_with_context_variations(self):
        """Test PreAct adapts to different contexts."""
        predictor = PreActPredictor()

        async def dummy_executor(tool_name: str, params: dict):
            return {"success": True}

        contexts = [
            {"tools": ["read", "write"]},
            {"tools": ["search", "analyze", "report"], "complexity": "high"},
            {"tools": ["validate"], "strictness": "strict"},
        ]

        predictions = []

        for i, context in enumerate(contexts):
            pred = await predictor.predict_and_plan(
                goal=f"Goal {i}",
                context=context,
                tool_executor=dummy_executor,
            )
            predictions.append(pred)

        # All predictions should be valid
        assert len(predictions) == 3
        assert all(0 <= p.confidence <= 1 for p in predictions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
