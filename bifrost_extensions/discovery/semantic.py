"""
Semantic Discovery (Proposal 19)

Provides:
- Action-based discovery
- Prompt-based discovery
- Context-aware discovery
- Semantic matching
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SemanticMatch:
    """Semantic match result."""
    tool_name: str
    relevance_score: float
    match_type: str
    explanation: str


class SemanticDiscovery:
    """Semantic tool discovery."""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.embeddings: Dict[str, List[float]] = {}
    
    async def register_tool(self, name: str, description: str, actions: List[str], prompts: List[str]) -> None:
        """Register tool for semantic discovery."""
        logger.info(f"Registering tool: {name}")
        
        self.tools[name] = {
            "name": name,
            "description": description,
            "actions": actions,
            "prompts": prompts
        }
    
    async def discover_by_action(self, action: str) -> List[SemanticMatch]:
        """Discover tools by action."""
        try:
            logger.info(f"Discovering by action: {action}")
            
            matches = []
            
            for tool_name, tool_info in self.tools.items():
                for tool_action in tool_info["actions"]:
                    if action.lower() in tool_action.lower():
                        match = SemanticMatch(
                            tool_name=tool_name,
                            relevance_score=0.9,
                            match_type="action",
                            explanation=f"Tool supports {action}"
                        )
                        matches.append(match)
            
            matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Found {len(matches)} tools for action {action}")
            return matches
        
        except Exception as e:
            logger.error(f"Error discovering by action: {e}")
            return []
    
    async def discover_by_prompt(self, prompt: str) -> List[SemanticMatch]:
        """Discover tools by prompt."""
        try:
            logger.info(f"Discovering by prompt: {prompt[:50]}...")
            
            matches = []
            
            for tool_name, tool_info in self.tools.items():
                for tool_prompt in tool_info["prompts"]:
                    if any(word in prompt.lower() for word in tool_prompt.lower().split()):
                        match = SemanticMatch(
                            tool_name=tool_name,
                            relevance_score=0.85,
                            match_type="prompt",
                            explanation=f"Tool matches prompt pattern"
                        )
                        matches.append(match)
            
            matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Found {len(matches)} tools for prompt")
            return matches
        
        except Exception as e:
            logger.error(f"Error discovering by prompt: {e}")
            return []
    
    async def discover_by_context(self, context: Dict[str, Any]) -> List[SemanticMatch]:
        """Discover tools by context."""
        try:
            logger.info("Discovering by context")
            
            matches = []
            
            # Extract context information
            intent = context.get("intent", "")
            domain = context.get("domain", "")
            
            for tool_name, tool_info in self.tools.items():
                score = 0.0
                
                # Check intent match
                if intent and intent.lower() in tool_info["description"].lower():
                    score += 0.5
                
                # Check domain match
                if domain and domain.lower() in tool_info["description"].lower():
                    score += 0.5
                
                if score > 0:
                    match = SemanticMatch(
                        tool_name=tool_name,
                        relevance_score=score,
                        match_type="context",
                        explanation=f"Tool matches context"
                    )
                    matches.append(match)
            
            matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Found {len(matches)} tools for context")
            return matches
        
        except Exception as e:
            logger.error(f"Error discovering by context: {e}")
            return []
    
    async def semantic_search(self, query: str) -> List[SemanticMatch]:
        """Perform semantic search."""
        try:
            logger.info(f"Semantic search: {query}")
            
            # Try all discovery methods
            action_matches = await self.discover_by_action(query)
            prompt_matches = await self.discover_by_prompt(query)
            
            # Combine and deduplicate
            all_matches = {}
            for match in action_matches + prompt_matches:
                if match.tool_name not in all_matches:
                    all_matches[match.tool_name] = match
                else:
                    # Keep highest score
                    if match.relevance_score > all_matches[match.tool_name].relevance_score:
                        all_matches[match.tool_name] = match
            
            results = list(all_matches.values())
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Semantic search found {len(results)} tools")
            return results
        
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        return {
            "registered_tools": len(self.tools),
            "total_actions": sum(len(t["actions"]) for t in self.tools.values()),
            "total_prompts": sum(len(t["prompts"]) for t in self.tools.values())
        }


# Global instance
_semantic_discovery: Optional[SemanticDiscovery] = None


def get_semantic_discovery() -> SemanticDiscovery:
    """Get or create global semantic discovery."""
    global _semantic_discovery
    if _semantic_discovery is None:
        _semantic_discovery = SemanticDiscovery()
    return _semantic_discovery

