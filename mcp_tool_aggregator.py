"""
MCP Tool Aggregator

Provides:
- Multi-MCP tool aggregation
- Conflict resolution
- Namespace management
- Capability merging
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AggregatedTool:
    """Aggregated tool from multiple MCPs."""
    name: str
    namespace: str
    description: str
    mcp_source: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    version: str


class ToolConflict:
    """Tool conflict information."""
    
    def __init__(self, tool_name: str, sources: List[str]):
        self.tool_name = tool_name
        self.sources = sources
        self.resolution = None


class MCPToolAggregator:
    """Aggregate tools from multiple MCPs."""
    
    def __init__(self):
        self.tools: Dict[str, AggregatedTool] = {}
        self.conflicts: List[ToolConflict] = []
        self.namespaces: Dict[str, List[str]] = {}
    
    async def aggregate_tools(self, mcp_tools: Dict[str, Dict[str, Any]]) -> Dict[str, AggregatedTool]:
        """Aggregate tools from multiple MCPs."""
        try:
            logger.info(f"Aggregating tools from {len(mcp_tools)} MCPs")
            
            self.tools = {}
            self.conflicts = []
            self.namespaces = {}
            
            for mcp_name, tools in mcp_tools.items():
                for tool_name, tool_spec in tools.items():
                    await self._add_tool(mcp_name, tool_name, tool_spec)
            
            logger.info(f"Aggregated {len(self.tools)} tools")
            return self.tools
        
        except Exception as e:
            logger.error(f"Error aggregating tools: {e}")
            return {}
    
    async def _add_tool(self, mcp_name: str, tool_name: str, tool_spec: Dict[str, Any]) -> None:
        """Add tool to aggregation."""
        try:
            # Check for conflicts
            if tool_name in self.tools:
                conflict = ToolConflict(tool_name, [self.tools[tool_name].mcp_source, mcp_name])
                self.conflicts.append(conflict)
                
                # Resolve conflict by namespacing
                namespaced_name = f"{mcp_name}:{tool_name}"
            else:
                namespaced_name = tool_name
            
            # Create aggregated tool
            aggregated = AggregatedTool(
                name=tool_name,
                namespace=mcp_name,
                description=tool_spec.get("description", ""),
                mcp_source=mcp_name,
                input_schema=tool_spec.get("input_schema", {}),
                output_schema=tool_spec.get("output_schema", {}),
                version=tool_spec.get("version", "1.0.0")
            )
            
            self.tools[namespaced_name] = aggregated
            
            # Track namespace
            if mcp_name not in self.namespaces:
                self.namespaces[mcp_name] = []
            self.namespaces[mcp_name].append(namespaced_name)
        
        except Exception as e:
            logger.error(f"Error adding tool: {e}")
    
    async def resolve_conflicts(self, strategy: str = "namespace") -> List[ToolConflict]:
        """Resolve tool conflicts."""
        try:
            logger.info(f"Resolving {len(self.conflicts)} conflicts using {strategy}")
            
            for conflict in self.conflicts:
                if strategy == "namespace":
                    # Already handled in _add_tool
                    conflict.resolution = "namespaced"
                elif strategy == "priority":
                    # Keep first source
                    conflict.resolution = f"kept_{conflict.sources[0]}"
                elif strategy == "merge":
                    # Merge capabilities
                    conflict.resolution = "merged"
            
            return self.conflicts
        
        except Exception as e:
            logger.error(f"Error resolving conflicts: {e}")
            return []
    
    async def merge_capabilities(self, mcp_names: List[str]) -> Dict[str, Any]:
        """Merge capabilities from multiple MCPs."""
        try:
            logger.info(f"Merging capabilities from {mcp_names}")
            
            merged = {
                "tools": [],
                "resources": [],
                "prompts": [],
                "total_tools": 0
            }
            
            for mcp_name in mcp_names:
                if mcp_name in self.namespaces:
                    tools = self.namespaces[mcp_name]
                    merged["tools"].extend(tools)
                    merged["total_tools"] += len(tools)
            
            return merged
        
        except Exception as e:
            logger.error(f"Error merging capabilities: {e}")
            return {}
    
    async def create_namespaces(self, mcp_names: List[str]) -> Dict[str, List[str]]:
        """Create tool namespaces."""
        try:
            logger.info(f"Creating namespaces for {mcp_names}")
            
            namespaces = {}
            for mcp_name in mcp_names:
                if mcp_name in self.namespaces:
                    namespaces[mcp_name] = self.namespaces[mcp_name]
            
            return namespaces
        
        except Exception as e:
            logger.error(f"Error creating namespaces: {e}")
            return {}
    
    async def get_tool(self, name: str) -> Optional[AggregatedTool]:
        """Get aggregated tool."""
        return self.tools.get(name)
    
    async def list_tools(self, mcp_name: Optional[str] = None) -> List[AggregatedTool]:
        """List aggregated tools."""
        if mcp_name:
            return [t for t in self.tools.values() if t.mcp_source == mcp_name]
        return list(self.tools.values())
    
    async def get_conflicts(self) -> List[ToolConflict]:
        """Get tool conflicts."""
        return self.conflicts
    
    async def get_namespaces(self) -> Dict[str, List[str]]:
        """Get tool namespaces."""
        return self.namespaces


# Global instance
_tool_aggregator: Optional[MCPToolAggregator] = None


def get_mcp_tool_aggregator() -> MCPToolAggregator:
    """Get or create global tool aggregator."""
    global _tool_aggregator
    if _tool_aggregator is None:
        _tool_aggregator = MCPToolAggregator()
    return _tool_aggregator

