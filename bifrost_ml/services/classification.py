"""Unified Classification Service - Wraps MLX router for prompt classification."""
import sys
import os
from typing import Dict, List, Tuple, Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mlx_router import MLXRouter, RouterPrediction


class UnifiedClassifier:
    """Unified classifier for prompt classification."""

    def __init__(self):
        """Initialize classifier."""
        self.router = MLXRouter()

    async def initialize(self) -> bool:
        """Initialize the classifier."""
        return await self.router.initialize()

    async def classify(
        self,
        prompt: str,
        context: Optional[Dict[str, any]] = None,
    ) -> RouterPrediction:
        """Classify prompt to determine tool/intent."""
        # Use router's intent routing
        prediction = await self.router.route_intent(prompt)
        if prediction:
            return prediction

        # Fallback to tool classification
        tool_name = await self.router.classify_tool(prompt)
        if tool_name:
            return RouterPrediction(
                tool_name=tool_name,
                confidence=0.85,
                alternatives=[]
            )

        # Default fallback
        return RouterPrediction(
            tool_name="unknown",
            confidence=0.0,
            alternatives=[]
        )

    async def get_top_tools(
        self,
        prompt: str,
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """Get top K tools for prompt."""
        return await self.router.get_top_tools(prompt, top_k)

    async def register_tool(
        self,
        name: str,
        description: str,
        keywords: List[str],
    ) -> None:
        """Register a tool for classification."""
        await self.router.register_tool(name, description, keywords)


# Global instance
_classifier: Optional[UnifiedClassifier] = None


def get_unified_classifier() -> UnifiedClassifier:
    """Get or create global classifier."""
    global _classifier
    if _classifier is None:
        _classifier = UnifiedClassifier()
    return _classifier
