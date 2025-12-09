"""
MCP Agent-Driven Discovery

Provides:
- Intent-based discovery
- Capability matching
- Recommendations
- Learning
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MCPIntent:
    """MCP intent."""
    intent: str
    keywords: List[str]
    required_capabilities: List[str]
    optional_capabilities: List[str]


@dataclass
class DiscoveryResult:
    """Discovery result."""
    mcp_name: str
    match_score: float
    matched_capabilities: List[str]
    missing_capabilities: List[str]


class MCPAgentDiscovery:
    """Agent-driven MCP discovery."""
    
    def __init__(self):
        self.intents: Dict[str, MCPIntent] = {}
        self.mcp_registry: Dict[str, Dict[str, Any]] = {}
        self.usage_history: Dict[str, int] = defaultdict(int)
        self.learning_data: Dict[str, List[str]] = defaultdict(list)
    
    async def register_intent(self, intent: MCPIntent) -> None:
        """Register intent."""
        logger.info(f"Registering intent: {intent.intent}")
        self.intents[intent.intent] = intent
    
    async def register_mcp(self, name: str, capabilities: Dict[str, Any]) -> None:
        """Register MCP."""
        logger.info(f"Registering MCP: {name}")
        self.mcp_registry[name] = capabilities
    
    async def discover_by_intent(self, intent: str) -> List[DiscoveryResult]:
        """Discover MCPs by intent."""
        try:
            logger.info(f"Discovering by intent: {intent}")
            
            if intent not in self.intents:
                logger.warning(f"Intent not found: {intent}")
                return []
            
            intent_spec = self.intents[intent]
            results = []
            
            # Score each MCP
            for mcp_name, capabilities in self.mcp_registry.items():
                score = await self._calculate_match_score(
                    intent_spec,
                    capabilities
                )
                
                if score > 0:
                    matched = [
                        c for c in intent_spec.required_capabilities
                        if c in capabilities.get("capabilities", [])
                    ]
                    missing = [
                        c for c in intent_spec.required_capabilities
                        if c not in capabilities.get("capabilities", [])
                    ]
                    
                    result = DiscoveryResult(
                        mcp_name=mcp_name,
                        match_score=score,
                        matched_capabilities=matched,
                        missing_capabilities=missing
                    )
                    results.append(result)
            
            # Sort by score
            results.sort(key=lambda r: r.match_score, reverse=True)
            
            logger.info(f"Found {len(results)} MCPs for intent {intent}")
            return results
        
        except Exception as e:
            logger.error(f"Error discovering by intent: {e}")
            return []
    
    async def discover_by_capability(self, capability: str) -> List[str]:
        """Discover MCPs by capability."""
        try:
            logger.info(f"Discovering by capability: {capability}")
            
            results = []
            for mcp_name, capabilities in self.mcp_registry.items():
                if capability in capabilities.get("capabilities", []):
                    results.append(mcp_name)
            
            logger.info(f"Found {len(results)} MCPs with capability {capability}")
            return results
        
        except Exception as e:
            logger.error(f"Error discovering by capability: {e}")
            return []
    
    async def _calculate_match_score(self, intent: MCPIntent, capabilities: Dict[str, Any]) -> float:
        """Calculate match score."""
        score = 0.0
        mcp_caps = capabilities.get("capabilities", [])
        
        # Required capabilities (weight: 0.7)
        required_matched = sum(
            1 for c in intent.required_capabilities if c in mcp_caps
        )
        required_score = (required_matched / len(intent.required_capabilities)) * 0.7 if intent.required_capabilities else 0
        
        # Optional capabilities (weight: 0.3)
        optional_matched = sum(
            1 for c in intent.optional_capabilities if c in mcp_caps
        )
        optional_score = (optional_matched / len(intent.optional_capabilities)) * 0.3 if intent.optional_capabilities else 0
        
        score = required_score + optional_score
        
        return score
    
    async def recommend_mcps(self, context: Dict[str, Any]) -> List[str]:
        """Recommend MCPs based on context."""
        try:
            logger.info("Recommending MCPs")
            
            # Extract intent from context
            intent = context.get("intent", "general")
            
            # Get discovery results
            results = await self.discover_by_intent(intent)
            
            # Filter by usage history (prefer frequently used)
            recommendations = []
            for result in results:
                if result.match_score > 0.5:
                    recommendations.append(result.mcp_name)
            
            # Sort by usage
            recommendations.sort(
                key=lambda m: self.usage_history[m],
                reverse=True
            )
            
            logger.info(f"Recommended {len(recommendations)} MCPs")
            return recommendations
        
        except Exception as e:
            logger.error(f"Error recommending MCPs: {e}")
            return []
    
    async def learn_from_usage(self, usage: Dict[str, Any]) -> None:
        """Learn from usage."""
        try:
            logger.info("Learning from usage")
            
            mcp_name = usage.get("mcp_name")
            intent = usage.get("intent")
            success = usage.get("success", False)
            
            if mcp_name:
                self.usage_history[mcp_name] += 1
            
            if intent and mcp_name and success:
                self.learning_data[intent].append(mcp_name)
                logger.info(f"Learned: {intent} -> {mcp_name}")
        
        except Exception as e:
            logger.error(f"Error learning from usage: {e}")
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        return {
            "total_intents": len(self.intents),
            "total_mcps": len(self.mcp_registry),
            "usage_history": dict(self.usage_history),
            "learning_data": dict(self.learning_data)
        }


# Global instance
_agent_discovery: Optional[MCPAgentDiscovery] = None


def get_mcp_agent_discovery() -> MCPAgentDiscovery:
    """Get or create global agent discovery."""
    global _agent_discovery
    if _agent_discovery is None:
        _agent_discovery = MCPAgentDiscovery()
    return _agent_discovery

