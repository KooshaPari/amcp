"""
PreAct Prediction-Enhanced Planning Implementation

PreAct (Prediction-Enhanced Agent with Reflection) extends ReAct by adding
a prediction step before reasoning and action, enabling:
- Outcome forecasting for strategic decision-making
- Error prevention through proactive planning
- Self-reflection via prediction comparison
- Better composability with other techniques

Flow: Prediction → Reasoning → Action → Self-Reflection

Reference: 2025 PreAct Research
Publication: Coling 2025
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Awaitable
from enum import Enum

logger = logging.getLogger(__name__)


class PredictionConfidence(str, Enum):
    """Confidence levels for predictions."""
    VERY_HIGH = "very_high"  # >0.9
    HIGH = "high"  # 0.7-0.9
    MEDIUM = "medium"  # 0.5-0.7
    LOW = "low"  # 0.3-0.5
    VERY_LOW = "very_low"  # <0.3


@dataclass
class PredictionResult:
    """Result of outcome prediction."""

    predicted_outcome: str
    confidence: float
    reasoning: str
    expected_success_rate: float
    risks: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    @property
    def confidence_level(self) -> PredictionConfidence:
        """Map confidence score to confidence level."""
        if self.confidence > 0.9:
            return PredictionConfidence.VERY_HIGH
        elif self.confidence > 0.7:
            return PredictionConfidence.HIGH
        elif self.confidence > 0.5:
            return PredictionConfidence.MEDIUM
        elif self.confidence > 0.3:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW


@dataclass
class ReflectionResult:
    """Result of self-reflection comparing prediction to actual outcome."""

    predicted_outcome: str
    actual_outcome: str
    accuracy: float
    aligned: bool
    insights: str
    lesson_learned: Optional[str] = None
    confidence_adjustment: float = 0.0
    created_at: float = field(default_factory=time.time)


@dataclass
class PreActConfig:
    """Configuration for PreAct prediction layer."""

    # Prediction parameters
    enable_prediction: bool = True
    prediction_model: str = "gpt-4-turbo"
    prediction_temperature: float = 0.3  # Lower = more deterministic
    max_prediction_tokens: int = 500

    # Reflection parameters
    enable_reflection: bool = True
    reflection_threshold: float = 0.3  # Reflect if accuracy diff > this
    store_reflections: bool = True

    # Risk assessment
    enable_risk_assessment: bool = True
    risk_detection_threshold: float = 0.5

    # Memory integration
    enable_episodic_memory: bool = True
    similar_example_count: int = 3

    # Performance
    prediction_timeout: float = 10.0
    cache_predictions: bool = True


class PreActPredictor:
    """
    PreAct prediction layer for strategic decision-making.

    Usage:
        predictor = PreActPredictor(config)

        # Make prediction for a goal
        prediction = await predictor.predict_and_plan(
            goal="Analyze the repository structure",
            context={"tools": ["list_files", "read_file"]},
            episodic_examples=[]
        )

        # Execute the planned action
        actual_outcome = await execute_tool(...)

        # Reflect on the prediction vs actual outcome
        reflection = await predictor.reflect(
            prediction=prediction,
            actual_outcome=str(actual_outcome)
        )
    """

    def __init__(self, config: PreActConfig = None):
        self.config = config or PreActConfig()
        self._prediction_cache: dict[str, PredictionResult] = {}
        self._reflections: list[ReflectionResult] = []
        self._lock = asyncio.Lock()

    async def predict_and_plan(
        self,
        goal: str,
        context: dict[str, Any],
        episodic_examples: list[dict] = None,
        tool_executor: Optional[Callable[[str, dict], Awaitable[Any]]] = None,
    ) -> PredictionResult:
        """
        Make a prediction about goal outcomes before reasoning/action.

        This is the first step in PreAct: prediction enables strategic
        decision-making by forecasting likely outcomes before committing
        to action.

        Args:
            goal: The goal to achieve
            context: Context including available tools and state
            episodic_examples: Historical examples of similar goals
            tool_executor: Optional executor to test predictions

        Returns:
            PredictionResult with confidence, risks, opportunities
        """
        # Check cache
        cache_key = f"{goal}:{str(context)}"
        if self.config.cache_predictions and cache_key in self._prediction_cache:
            logger.debug(f"Using cached prediction for goal: {goal[:50]}...")
            return self._prediction_cache[cache_key]

        logger.info(f"Making prediction for goal: {goal[:100]}...")
        start_time = time.time()

        try:
            # Generate prediction
            prediction = await self._generate_prediction(
                goal, context, episodic_examples or []
            )

            # Assess risks and opportunities
            if self.config.enable_risk_assessment:
                prediction = await self._assess_risks_and_opportunities(
                    prediction, context
                )

            # Optional: Validate prediction with quick test
            if tool_executor and self.config.enable_prediction:
                prediction = await self._validate_prediction(
                    prediction, goal, context, tool_executor
                )

            # Cache result
            if self.config.cache_predictions:
                # Enforce cache size limit
                if len(self._prediction_cache) >= 1000:  # Hard limit
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self._prediction_cache))
                    del self._prediction_cache[oldest_key]
                self._prediction_cache[cache_key] = prediction

            duration = time.time() - start_time
            logger.info(
                f"Prediction generated: confidence={prediction.confidence:.2f}, "
                f"duration={duration:.2f}s"
            )

            return prediction

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            # Return conservative prediction on error
            return PredictionResult(
                predicted_outcome=f"Error predicting: {str(e)}",
                confidence=0.1,
                reasoning="Prediction engine encountered an error",
                expected_success_rate=0.0,
                risks=[str(e)],
            )

    async def _generate_prediction(
        self,
        goal: str,
        context: dict[str, Any],
        episodic_examples: list[dict],
    ) -> PredictionResult:
        """Generate core prediction using LLM-like logic."""
        # In production, this would call an LLM with the goal and context
        # For now, we use heuristic-based prediction

        # Analyze goal complexity
        goal_tokens = len(goal.split())
        complexity_score = min(goal_tokens / 100, 1.0)  # Normalized

        # Analyze available tools
        tools = context.get("tools", [])
        tool_coverage = len(tools) / max(1, goal_tokens / 10)
        tool_coverage = min(tool_coverage, 1.0)

        # Base confidence from context
        base_confidence = (tool_coverage + (1 - complexity_score)) / 2

        # Adjust based on episodic examples
        if episodic_examples:
            avg_historical_success = sum(
                ex.get("success_rate", 0.7) for ex in episodic_examples
            ) / len(episodic_examples)
            base_confidence = (base_confidence + avg_historical_success) / 2

        # Identify potential risks
        risks = []
        if complexity_score > 0.7:
            risks.append("High goal complexity may require multiple steps")
        if tool_coverage < 0.5:
            risks.append("Limited tool availability for goal scope")
        if "error" in goal.lower() or "fail" in goal.lower():
            risks.append("Goal involves error recovery")

        # Identify opportunities
        opportunities = []
        if len(tools) > 3:
            opportunities.append("Multiple tools available for parallel execution")
        if episodic_examples:
            opportunities.append("Similar historical examples available")
        if complexity_score < 0.3:
            opportunities.append("Simple goal structure enables fast execution")

        # Generate outcome prediction
        if base_confidence > 0.7:
            predicted_outcome = f"Successfully achieve goal: {goal[:50]}..."
        elif base_confidence > 0.4:
            predicted_outcome = (
                f"Partially achieve goal with refinement: {goal[:40]}..."
            )
        else:
            predicted_outcome = f"May fail to achieve goal: {goal[:50]}... "
            "Recommend alternative approach"

        return PredictionResult(
            predicted_outcome=predicted_outcome,
            confidence=base_confidence,
            reasoning=(
                f"Tool coverage={tool_coverage:.2f}, "
                f"Complexity={complexity_score:.2f}, "
                f"Historical success={avg_historical_success:.2f}"
                if episodic_examples
                else f"Tool coverage={tool_coverage:.2f}, "
                f"Complexity={complexity_score:.2f}"
            ),
            expected_success_rate=base_confidence,
            risks=risks,
            opportunities=opportunities,
        )

    async def _assess_risks_and_opportunities(
        self,
        prediction: PredictionResult,
        context: dict[str, Any],
    ) -> PredictionResult:
        """Enhanced risk and opportunity assessment."""
        # Add context-based risks
        if context.get("time_constrained"):
            prediction.risks.append("Time constraints may limit exploration")

        if context.get("high_stakes"):
            prediction.risks.append("High-stakes environment requires caution")

        # Add context-based opportunities
        if context.get("parallel_execution"):
            prediction.opportunities.append("Parallel execution available")

        if context.get("iterative_refinement"):
            prediction.opportunities.append("Multiple refinement iterations possible")

        return prediction

    async def _validate_prediction(
        self,
        prediction: PredictionResult,
        goal: str,
        context: dict[str, Any],
        tool_executor: Callable[[str, dict], Awaitable[Any]],
    ) -> PredictionResult:
        """Optional validation of prediction with quick test."""
        try:
            # Pick first available tool for quick validation
            tools = context.get("tools", [])
            if not tools:
                return prediction

            test_tool = tools[0]
            logger.debug(f"Validating prediction with test tool: {test_tool}")

            # Execute quick test
            result = await asyncio.wait_for(
                tool_executor(test_tool, {"query": goal}),
                timeout=self.config.prediction_timeout,
            )

            # Adjust confidence based on test result
            if result:
                prediction.confidence = min(prediction.confidence + 0.1, 1.0)
                prediction.expected_success_rate = min(
                    prediction.expected_success_rate + 0.1, 1.0
                )
                logger.debug("Prediction validation succeeded")
            else:
                prediction.confidence = max(prediction.confidence - 0.2, 0.0)
                prediction.expected_success_rate = max(
                    prediction.expected_success_rate - 0.2, 0.0
                )
                logger.debug("Prediction validation showed concerns")

        except asyncio.TimeoutError:
            logger.warning("Prediction validation timed out")
        except Exception as e:
            logger.warning(f"Prediction validation failed: {e}")

        return prediction

    async def reflect(
        self,
        prediction: PredictionResult,
        actual_outcome: str,
    ) -> ReflectionResult:
        """
        Self-reflection comparing prediction to actual outcome.

        This is the final step in PreAct: reflection compares predicted
        vs actual outcomes, enabling learning and confidence adjustment.

        Args:
            prediction: Original prediction
            actual_outcome: What actually happened

        Returns:
            ReflectionResult with insights and confidence adjustment
        """
        logger.info(
            f"Reflecting on prediction: predicted={prediction.predicted_outcome[:50]}"
        )

        # Assess alignment
        aligned = self._assess_alignment(prediction, actual_outcome)
        accuracy = self._calculate_accuracy(prediction, actual_outcome)

        # Generate insights
        insights = self._generate_insights(prediction, actual_outcome, accuracy)

        # Extract lesson
        lesson = None
        if accuracy < 0.3:  # Major misalignment
            lesson = f"Predictions underestimated complexity; recommend {
                'more exploration' if prediction.confidence > 0.7
                else 'different approach'}"
        elif accuracy > 0.8:  # High accuracy
            lesson = "Prediction strategy effective; can be reused"

        # Calculate confidence adjustment
        confidence_adj = (accuracy - prediction.confidence) * 0.2

        reflection = ReflectionResult(
            predicted_outcome=prediction.predicted_outcome,
            actual_outcome=actual_outcome,
            accuracy=accuracy,
            aligned=aligned,
            insights=insights,
            lesson_learned=lesson,
            confidence_adjustment=confidence_adj,
        )

        # Store reflection
        if self.config.store_reflections:
            async with self._lock:
                # Limit reflections list size to prevent unbounded growth
                self._reflections.append(reflection)
                if len(self._reflections) > 10000:  # Keep last 10k reflections
                    self._reflections = self._reflections[-10000:]

        logger.info(
            f"Reflection complete: accuracy={accuracy:.2f}, "
            f"aligned={aligned}, adjustment={confidence_adj:.2f}"
        )

        return reflection

    def _assess_alignment(
        self,
        prediction: PredictionResult,
        actual_outcome: str,
    ) -> bool:
        """Check if actual outcome aligns with prediction."""
        prediction_lower = prediction.predicted_outcome.lower()
        actual_lower = actual_outcome.lower()

        # Simple heuristic: check for success/failure keywords
        pred_success = any(
            word in prediction_lower for word in ["success", "achieve", "complete"]
        )
        pred_failure = any(
            word in prediction_lower for word in ["fail", "error", "unable"]
        )

        actual_success = any(
            word in actual_lower for word in ["success", "complete", "done"]
        )
        actual_failure = any(
            word in actual_lower for word in ["fail", "error", "unable"]
        )

        # Check alignment
        if pred_success and actual_success:
            return True
        if pred_failure and actual_failure:
            return True
        if not pred_success and not pred_failure and actual_success:
            return True  # Neutral prediction, positive outcome

        return False

    def _calculate_accuracy(
        self,
        prediction: PredictionResult,
        actual_outcome: str,
    ) -> float:
        """Calculate prediction accuracy (0-1)."""
        # Base accuracy from alignment
        accuracy = 0.5 if self._assess_alignment(prediction, actual_outcome) else 0.0

        # Adjust based on confidence
        confidence_factor = prediction.confidence
        if prediction.expected_success_rate > 0.7:
            # High confidence prediction
            if self._assess_alignment(prediction, actual_outcome):
                accuracy = min(1.0, confidence_factor + 0.3)
            else:
                accuracy = max(0.0, confidence_factor - 0.5)
        else:
            # Low confidence prediction (more lenient)
            if self._assess_alignment(prediction, actual_outcome):
                accuracy = 0.6
            else:
                accuracy = 0.2

        # Check if risks were realized
        if "error" in actual_outcome.lower():
            if any("error" in risk for risk in prediction.risks):
                accuracy = min(1.0, accuracy + 0.2)

        return min(1.0, max(0.0, accuracy))

    def _generate_insights(
        self,
        prediction: PredictionResult,
        actual_outcome: str,
        accuracy: float,
    ) -> str:
        """Generate insights from reflection."""
        if accuracy > 0.8:
            return "High prediction accuracy; strategy effective"
        elif accuracy > 0.5:
            return "Partial prediction success; some adjustments needed"
        else:
            return "Low prediction accuracy; strategy needs revision"

    async def get_reflection_summary(self) -> dict[str, Any]:
        """Get summary of all reflections."""
        if not self._reflections:
            return {
                "total_reflections": 0,
                "average_accuracy": 0.0,
                "alignment_rate": 0.0,
                "lessons_learned": [],
            }

        total = len(self._reflections)
        avg_accuracy = sum(r.accuracy for r in self._reflections) / total
        alignment_rate = sum(
            1 for r in self._reflections if r.aligned
        ) / total
        lessons = [
            r.lesson_learned
            for r in self._reflections
            if r.lesson_learned
        ]

        return {
            "total_reflections": total,
            "average_accuracy": avg_accuracy,
            "alignment_rate": alignment_rate,
            "lessons_learned": lessons,
            "confidence_adjustments": [
                r.confidence_adjustment for r in self._reflections
            ],
        }

    def clear_cache(self) -> None:
        """Clear prediction cache."""
        self._prediction_cache.clear()
        logger.info("Prediction cache cleared")

    def clear_reflections(self) -> None:
        """Clear stored reflections."""
        self._reflections.clear()
        logger.info("Reflections cleared")


# Global predictor instance
_preact_predictor: Optional[PreActPredictor] = None


def get_preact_predictor(config: PreActConfig = None) -> PreActPredictor:
    """Get or create global PreAct predictor instance."""
    global _preact_predictor
    if _preact_predictor is None:
        _preact_predictor = PreActPredictor(config or PreActConfig())
    return _preact_predictor
