"""
Learning System (Proposal 20)

Provides:
- Usage pattern learning
- Performance optimization
- Recommendation engine
- Adaptive routing
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class UsagePattern:
    """Usage pattern."""
    tool_name: str
    action: str
    success_count: int
    failure_count: int
    avg_latency_ms: float
    last_used: str


class LearningSystem:
    """Learn from usage patterns."""
    
    def __init__(self):
        self.usage_patterns: Dict[str, UsagePattern] = {}
        self.tool_scores: Dict[str, float] = defaultdict(float)
        self.recommendations: Dict[str, List[str]] = defaultdict(list)
    
    async def record_usage(self, tool_name: str, action: str, success: bool, latency_ms: float) -> None:
        """Record tool usage."""
        try:
            logger.info(f"Recording usage: {tool_name} - {action} - {'success' if success else 'failure'}")
            
            key = f"{tool_name}:{action}"
            
            if key not in self.usage_patterns:
                self.usage_patterns[key] = UsagePattern(
                    tool_name=tool_name,
                    action=action,
                    success_count=0,
                    failure_count=0,
                    avg_latency_ms=0.0,
                    last_used=""
                )
            
            pattern = self.usage_patterns[key]
            
            if success:
                pattern.success_count += 1
            else:
                pattern.failure_count += 1
            
            # Update average latency
            total = pattern.success_count + pattern.failure_count
            pattern.avg_latency_ms = (pattern.avg_latency_ms * (total - 1) + latency_ms) / total
            
            # Update tool score
            success_rate = pattern.success_count / total if total > 0 else 0
            self.tool_scores[tool_name] = success_rate * (1000 / (pattern.avg_latency_ms + 1))
        
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
    
    async def get_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Get tool recommendations."""
        try:
            logger.info("Getting recommendations")
            
            # Sort tools by score
            sorted_tools = sorted(
                self.tool_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            recommendations = [tool for tool, score in sorted_tools[:5]]
            
            logger.info(f"Recommended {len(recommendations)} tools")
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def optimize_routing(self, tool_name: str) -> Optional[str]:
        """Optimize tool routing."""
        try:
            logger.info(f"Optimizing routing for {tool_name}")
            
            # Find best performing alternative
            best_alternative = None
            best_score = self.tool_scores.get(tool_name, 0)
            
            for alt_tool, score in self.tool_scores.items():
                if alt_tool != tool_name and score > best_score:
                    best_alternative = alt_tool
                    best_score = score
            
            if best_alternative:
                logger.info(f"Routing {tool_name} to {best_alternative}")
                return best_alternative
            
            return None
        
        except Exception as e:
            logger.error(f"Error optimizing routing: {e}")
            return None
    
    async def predict_success(self, tool_name: str, action: str) -> float:
        """Predict success probability."""
        try:
            key = f"{tool_name}:{action}"
            
            if key not in self.usage_patterns:
                return 0.5  # Default
            
            pattern = self.usage_patterns[key]
            total = pattern.success_count + pattern.failure_count
            
            if total == 0:
                return 0.5
            
            return pattern.success_count / total
        
        except Exception as e:
            logger.error(f"Error predicting success: {e}")
            return 0.5
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        total_uses = sum(
            p.success_count + p.failure_count
            for p in self.usage_patterns.values()
        )
        
        total_successes = sum(
            p.success_count
            for p in self.usage_patterns.values()
        )
        
        return {
            "total_patterns": len(self.usage_patterns),
            "total_uses": total_uses,
            "total_successes": total_successes,
            "success_rate": total_successes / total_uses if total_uses > 0 else 0,
            "tracked_tools": len(self.tool_scores)
        }
    
    async def export_model(self) -> Dict[str, Any]:
        """Export learned model."""
        return {
            "usage_patterns": {
                k: {
                    "tool": v.tool_name,
                    "action": v.action,
                    "success_count": v.success_count,
                    "failure_count": v.failure_count,
                    "avg_latency_ms": v.avg_latency_ms
                }
                for k, v in self.usage_patterns.items()
            },
            "tool_scores": dict(self.tool_scores)
        }


# Global instance
_learning_system: Optional[LearningSystem] = None


def get_learning_system() -> LearningSystem:
    """Get or create global learning system."""
    global _learning_system
    if _learning_system is None:
        _learning_system = LearningSystem()
    return _learning_system

