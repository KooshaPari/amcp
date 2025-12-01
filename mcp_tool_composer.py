"""
MCP Tool Composer

Provides:
- Tool piping
- Tool chaining
- Output transformation
- Error handling
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolPipe:
    """Tool pipe definition."""
    source_tool: str
    target_tool: str
    transform: Optional[Callable] = None
    error_handler: Optional[Callable] = None


@dataclass
class ToolChain:
    """Tool chain definition."""
    name: str
    tools: List[str]
    pipes: List[ToolPipe]


class MCPToolComposer:
    """Compose tools."""
    
    def __init__(self):
        self.pipes: Dict[str, ToolPipe] = {}
        self.chains: Dict[str, ToolChain] = {}
        self.tools: Dict[str, Callable] = {}
    
    async def register_tool(self, name: str, tool: Callable) -> None:
        """Register tool."""
        logger.info(f"Registering tool: {name}")
        self.tools[name] = tool
    
    async def pipe_tools(self, source: str, target: str, transform: Optional[Callable] = None) -> bool:
        """Pipe tools together."""
        try:
            logger.info(f"Piping {source} -> {target}")
            
            if source not in self.tools or target not in self.tools:
                logger.error(f"Tool not found: {source} or {target}")
                return False
            
            pipe = ToolPipe(
                source_tool=source,
                target_tool=target,
                transform=transform
            )
            
            pipe_key = f"{source}:{target}"
            self.pipes[pipe_key] = pipe
            
            logger.info(f"Piped {source} -> {target}")
            return True
        
        except Exception as e:
            logger.error(f"Error piping tools: {e}")
            return False
    
    async def chain_tools(self, name: str, tools: List[str]) -> Optional[ToolChain]:
        """Chain tools together."""
        try:
            logger.info(f"Chaining tools: {name}")
            
            # Verify all tools exist
            for tool in tools:
                if tool not in self.tools:
                    logger.error(f"Tool not found: {tool}")
                    return None
            
            # Create pipes between consecutive tools
            pipes = []
            for i in range(len(tools) - 1):
                pipe = ToolPipe(
                    source_tool=tools[i],
                    target_tool=tools[i + 1]
                )
                pipes.append(pipe)
            
            chain = ToolChain(
                name=name,
                tools=tools,
                pipes=pipes
            )
            
            self.chains[name] = chain
            logger.info(f"Created chain: {name}")
            return chain
        
        except Exception as e:
            logger.error(f"Error chaining tools: {e}")
            return None
    
    async def execute_pipe(self, source: str, target: str, input_data: Any) -> Optional[Any]:
        """Execute piped tools."""
        try:
            logger.info(f"Executing pipe: {source} -> {target}")
            
            pipe_key = f"{source}:{target}"
            if pipe_key not in self.pipes:
                logger.error(f"Pipe not found: {pipe_key}")
                return None
            
            pipe = self.pipes[pipe_key]
            
            # Execute source tool
            source_tool = self.tools[source]
            intermediate = await source_tool(input_data)
            
            # Transform if needed
            if pipe.transform:
                intermediate = await pipe.transform(intermediate)
            
            # Execute target tool
            target_tool = self.tools[target]
            result = await target_tool(intermediate)
            
            logger.info(f"Pipe executed successfully")
            return result
        
        except Exception as e:
            logger.error(f"Error executing pipe: {e}")
            return None
    
    async def execute_chain(self, chain_name: str, input_data: Any) -> Optional[Any]:
        """Execute tool chain."""
        try:
            logger.info(f"Executing chain: {chain_name}")
            
            if chain_name not in self.chains:
                logger.error(f"Chain not found: {chain_name}")
                return None
            
            chain = self.chains[chain_name]
            result = input_data
            
            # Execute each tool in sequence
            for tool_name in chain.tools:
                tool = self.tools[tool_name]
                result = await tool(result)
                logger.info(f"Chain step {tool_name} completed")
            
            logger.info(f"Chain {chain_name} executed successfully")
            return result
        
        except Exception as e:
            logger.error(f"Error executing chain: {e}")
            return None
    
    async def transform_output(self, output: Any, schema: Dict[str, Any]) -> Optional[Any]:
        """Transform tool output."""
        try:
            logger.info("Transforming output")
            
            # Validate against schema
            if not self._validate_schema(output, schema):
                logger.warning("Output does not match schema")
            
            # Transform
            transformed = self._apply_schema(output, schema)
            
            logger.info("Output transformed")
            return transformed
        
        except Exception as e:
            logger.error(f"Error transforming output: {e}")
            return None
    
    def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Validate data against schema."""
        try:
            if "type" in schema:
                expected_type = schema["type"]
                if expected_type == "object" and not isinstance(data, dict):
                    return False
                if expected_type == "array" and not isinstance(data, list):
                    return False
            return True
        except:
            return False
    
    def _apply_schema(self, data: Any, schema: Dict[str, Any]) -> Any:
        """Apply schema to data."""
        if isinstance(data, dict) and "properties" in schema:
            result = {}
            for key, prop_schema in schema["properties"].items():
                if key in data:
                    result[key] = data[key]
            return result
        return data
    
    async def handle_error(self, error: Exception, fallback: Optional[Callable] = None) -> Optional[Any]:
        """Handle tool error."""
        try:
            logger.error(f"Handling error: {error}")
            
            if fallback:
                logger.info("Executing fallback")
                return await fallback()
            
            return None
        
        except Exception as e:
            logger.error(f"Error handling error: {e}")
            return None
    
    async def list_pipes(self) -> List[Dict[str, str]]:
        """List all pipes."""
        return [
            {
                "source": p.source_tool,
                "target": p.target_tool
            }
            for p in self.pipes.values()
        ]
    
    async def list_chains(self) -> List[Dict[str, Any]]:
        """List all chains."""
        return [
            {
                "name": c.name,
                "tools": c.tools,
                "pipe_count": len(c.pipes)
            }
            for c in self.chains.values()
        ]


# Global instance
_tool_composer: Optional[MCPToolComposer] = None


def get_mcp_tool_composer() -> MCPToolComposer:
    """Get or create global tool composer."""
    global _tool_composer
    if _tool_composer is None:
        _tool_composer = MCPToolComposer()
    return _tool_composer

