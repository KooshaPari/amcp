"""SmartCP Tool Registry for Bifrost Integration.

Defines the tool registry system with schemas for registration
with the Bifrost gateway. Tool definitions are imported from tools.py.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ParameterSchema:
    """Schema for a tool parameter."""

    name: str
    type: str  # "string", "integer", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None
    properties: dict[str, Any] | None = None  # For object types


@dataclass
class ToolSchema:
    """Schema for a SmartCP tool."""

    name: str
    description: str
    parameters: list[ParameterSchema]
    category: str
    tags: list[str] = field(default_factory=list)
    returns_description: str = ""

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format for Bifrost registration."""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }

            if param.default is not None:
                prop["default"] = param.default

            if param.enum:
                prop["enum"] = param.enum

            if param.properties:
                prop["properties"] = param.properties

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }


class ToolRegistry:
    """Registry for SmartCP tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSchema] = {}

    def register(self, tool: ToolSchema) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get(self, name: str) -> ToolSchema | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def all(self) -> list[ToolSchema]:
        """Get all registered tools."""
        return list(self._tools.values())

    def by_category(self, category: str) -> list[ToolSchema]:
        """Get tools by category."""
        return [t for t in self._tools.values() if t.category == category]


def _tool_def_to_schema(tool_def: dict) -> ToolSchema:
    """Convert a tool definition dict to ToolSchema."""
    params = [
        ParameterSchema(**p) for p in tool_def.get("parameters", [])
    ]
    return ToolSchema(
        name=tool_def["name"],
        description=tool_def["description"],
        parameters=params,
        category=tool_def["category"],
        tags=tool_def.get("tags", []),
        returns_description=tool_def.get("returns_description", ""),
    )


def create_registry() -> ToolRegistry:
    """Create and populate the SmartCP tool registry."""
    from smartcp.bifrost.tools import ALL_TOOL_DEFS

    registry = ToolRegistry()
    for tool_def in ALL_TOOL_DEFS:
        tool = _tool_def_to_schema(tool_def)
        registry.register(tool)

    logger.info(f"SmartCP tool registry initialized with {len(registry.all())} tools")
    return registry


# Global registry instance
SMARTCP_TOOLS = create_registry()

# Create individual tool exports for backward compatibility
_tools_by_name = {t.name: t for t in SMARTCP_TOOLS.all()}

EXECUTE_CODE_TOOL = _tools_by_name["execute_code"]
GET_VARIABLES_TOOL = _tools_by_name["get_variables"]
SET_VARIABLE_TOOL = _tools_by_name["set_variable"]
DELETE_VARIABLE_TOOL = _tools_by_name["delete_variable"]
CLEAR_VARIABLES_TOOL = _tools_by_name["clear_variables"]
STORE_MEMORY_TOOL = _tools_by_name["store_memory"]
RETRIEVE_MEMORY_TOOL = _tools_by_name["retrieve_memory"]
DELETE_MEMORY_TOOL = _tools_by_name["delete_memory"]
LIST_MEMORY_KEYS_TOOL = _tools_by_name["list_memory_keys"]
CLEAR_MEMORY_TOOL = _tools_by_name["clear_memory"]
GET_MEMORY_STATS_TOOL = _tools_by_name["get_memory_stats"]
STATE_GET_TOOL = _tools_by_name["state_get"]
STATE_SET_TOOL = _tools_by_name["state_set"]
STATE_DELETE_TOOL = _tools_by_name["state_delete"]
STATE_EXISTS_TOOL = _tools_by_name["state_exists"]
STATE_LIST_KEYS_TOOL = _tools_by_name["state_list_keys"]
STATE_CLEAR_TOOL = _tools_by_name["state_clear"]
