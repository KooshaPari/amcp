"""
Tool Type System (Proposal 12)

Provides:
- Pre-typed tool signatures
- Type validation
- Tool piping support
- Composition safety
"""

import logging
from typing import Dict, Any, Optional, List, Type, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Tool type categories."""
    READER = "reader"
    WRITER = "writer"
    PROCESSOR = "processor"
    TRANSFORMER = "transformer"
    AGGREGATOR = "aggregator"
    FILTER = "filter"


@dataclass
class TypeSchema:
    """Type schema for tool I/O."""
    name: str
    type_name: str
    required_fields: Dict[str, str]
    optional_fields: Dict[str, str]
    description: str


@dataclass
class TypedTool:
    """Typed tool definition."""
    name: str
    tool_type: ToolType
    input_schema: TypeSchema
    output_schema: TypeSchema
    implementation: Callable
    version: str = "1.0.0"


class ToolTypeSystem:
    """Manage tool types and signatures."""
    
    def __init__(self):
        self.tools: Dict[str, TypedTool] = {}
        self.type_registry: Dict[str, Type] = {}
        self.compatibility_matrix: Dict[str, List[str]] = {}
    
    async def register_tool(self, tool: TypedTool) -> bool:
        """Register typed tool."""
        try:
            logger.info(f"Registering typed tool: {tool.name}")
            
            self.tools[tool.name] = tool
            
            # Build compatibility matrix
            await self._update_compatibility(tool)
            
            logger.info(f"Registered {tool.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error registering tool: {e}")
            return False
    
    async def _update_compatibility(self, tool: TypedTool) -> None:
        """Update compatibility matrix."""
        try:
            output_type = tool.output_schema.type_name
            
            if output_type not in self.compatibility_matrix:
                self.compatibility_matrix[output_type] = []
            
            # Find compatible tools
            for other_name, other_tool in self.tools.items():
                if other_tool.input_schema.type_name == output_type:
                    self.compatibility_matrix[output_type].append(other_name)
        
        except Exception as e:
            logger.error(f"Error updating compatibility: {e}")
    
    async def validate_type(self, data: Any, schema: TypeSchema) -> bool:
        """Validate data against type schema."""
        try:
            if not isinstance(data, dict):
                return False
            
            # Check required fields
            for field, field_type in schema.required_fields.items():
                if field not in data:
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating type: {e}")
            return False
    
    async def can_pipe(self, source_tool: str, target_tool: str) -> bool:
        """Check if tools can be piped."""
        try:
            if source_tool not in self.tools or target_tool not in self.tools:
                return False
            
            source = self.tools[source_tool]
            target = self.tools[target_tool]
            
            # Check type compatibility
            return source.output_schema.type_name == target.input_schema.type_name
        
        except Exception as e:
            logger.error(f"Error checking pipe compatibility: {e}")
            return False
    
    async def get_compatible_tools(self, tool_name: str) -> List[str]:
        """Get tools compatible with output."""
        try:
            if tool_name not in self.tools:
                return []
            
            tool = self.tools[tool_name]
            output_type = tool.output_schema.type_name
            
            return self.compatibility_matrix.get(output_type, [])
        
        except Exception as e:
            logger.error(f"Error getting compatible tools: {e}")
            return []
    
    async def get_tool_signature(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool signature."""
        try:
            if tool_name not in self.tools:
                return None
            
            tool = self.tools[tool_name]
            
            return {
                "name": tool.name,
                "type": tool.tool_type.value,
                "input": {
                    "type": tool.input_schema.type_name,
                    "required": tool.input_schema.required_fields,
                    "optional": tool.input_schema.optional_fields
                },
                "output": {
                    "type": tool.output_schema.type_name,
                    "fields": tool.output_schema.required_fields
                },
                "version": tool.version
            }
        
        except Exception as e:
            logger.error(f"Error getting signature: {e}")
            return None
    
    async def list_tools_by_type(self, tool_type: ToolType) -> List[str]:
        """List tools by type."""
        return [
            name for name, tool in self.tools.items()
            if tool.tool_type == tool_type
        ]
    
    async def get_type_compatibility_report(self) -> Dict[str, Any]:
        """Get type compatibility report."""
        return {
            "total_tools": len(self.tools),
            "compatibility_matrix": self.compatibility_matrix,
            "tools_by_type": {
                t.value: await self.list_tools_by_type(t)
                for t in ToolType
            }
        }


# Global instance
_type_system: Optional[ToolTypeSystem] = None


def get_tool_type_system() -> ToolTypeSystem:
    """Get or create global type system."""
    global _type_system
    if _type_system is None:
        _type_system = ToolTypeSystem()
    return _type_system

