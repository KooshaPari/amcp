"""
Tool Lifecycle Management for SmartCP

Provides:
- Dynamic tool registration
- Tool composition
- Live reload
- Tool versioning
"""

import logging
import asyncio
import importlib
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Tool status."""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


@dataclass
class ToolMetadata:
    """Tool metadata."""
    name: str
    version: str
    description: str
    author: str
    status: ToolStatus = ToolStatus.REGISTERED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ComposedTool:
    """Composed tool combining multiple tools."""
    name: str
    description: str
    tools: List[str]
    executor: Callable
    metadata: ToolMetadata = None


class ToolRegistry:
    """Tool registry for lifecycle management."""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.metadata: Dict[str, ToolMetadata] = {}
        self.composed_tools: Dict[str, ComposedTool] = {}
        self.lock = asyncio.Lock()
    
    async def register(
        self,
        name: str,
        tool: Any,
        metadata: ToolMetadata
    ) -> bool:
        """Register tool."""
        async with self.lock:
            if name in self.tools:
                logger.warning(f"Tool already registered: {name}")
                return False
            
            self.tools[name] = tool
            self.metadata[name] = metadata
            logger.info(f"Tool registered: {name} v{metadata.version}")
            return True
    
    async def unregister(self, name: str) -> bool:
        """Unregister tool."""
        async with self.lock:
            if name not in self.tools:
                return False
            
            del self.tools[name]
            del self.metadata[name]
            logger.info(f"Tool unregistered: {name}")
            return True
    
    async def get_tool(self, name: str) -> Optional[Any]:
        """Get tool."""
        return self.tools.get(name)
    
    async def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata."""
        return self.metadata.get(name)
    
    async def list_tools(self) -> List[str]:
        """List all tools."""
        return list(self.tools.keys())
    
    async def update_status(self, name: str, status: ToolStatus) -> bool:
        """Update tool status."""
        async with self.lock:
            if name not in self.metadata:
                return False
            
            self.metadata[name].status = status
            self.metadata[name].updated_at = datetime.now()
            logger.info(f"Tool status updated: {name} -> {status.value}")
            return True
    
    async def deprecate(self, name: str, replacement: Optional[str] = None) -> bool:
        """Deprecate tool."""
        success = await self.update_status(name, ToolStatus.DEPRECATED)
        if success and replacement:
            logger.info(f"Tool {name} deprecated, use {replacement} instead")
        return success


class ToolComposer:
    """Tool composer for creating composed tools."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.composed_tools: Dict[str, ComposedTool] = {}
    
    async def compose(
        self,
        name: str,
        description: str,
        tools: List[str],
        executor: Callable
    ) -> bool:
        """Compose multiple tools into one."""
        try:
            # Verify all tools exist
            for tool_name in tools:
                if not await self.registry.get_tool(tool_name):
                    logger.error(f"Tool not found: {tool_name}")
                    return False
            
            metadata = ToolMetadata(
                name=name,
                version="1.0.0",
                description=description,
                author="SmartCP",
                dependencies=tools
            )
            
            composed = ComposedTool(
                name=name,
                description=description,
                tools=tools,
                executor=executor,
                metadata=metadata
            )
            
            self.composed_tools[name] = composed
            logger.info(f"Tool composed: {name} from {tools}")
            return True
        
        except Exception as e:
            logger.error(f"Error composing tool: {e}")
            return False
    
    async def execute_composed(self, name: str, **kwargs) -> Optional[Any]:
        """Execute composed tool."""
        if name not in self.composed_tools:
            return None
        
        composed = self.composed_tools[name]
        
        # Gather results from component tools
        results = {}
        for tool_name in composed.tools:
            tool = await self.registry.get_tool(tool_name)
            if tool:
                results[tool_name] = tool
        
        # Execute composed tool
        return await composed.executor(results, **kwargs)


class ToolReloader:
    """Tool reloader for live reload."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.module_cache: Dict[str, Any] = {}
    
    async def reload_tool(self, name: str, module_path: str) -> bool:
        """Reload tool from module."""
        try:
            logger.info(f"Reloading tool: {name} from {module_path}")
            
            # Reload module
            if module_path in self.module_cache:
                module = self.module_cache[module_path]
                importlib.reload(module)
            else:
                module = importlib.import_module(module_path)
                self.module_cache[module_path] = module
            
            # Get tool from module
            if hasattr(module, name):
                tool = getattr(module, name)
                
                # Update in registry
                metadata = await self.registry.get_metadata(name)
                if metadata:
                    metadata.updated_at = datetime.now()
                    self.registry.tools[name] = tool
                    logger.info(f"Tool reloaded: {name}")
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error reloading tool: {e}")
            return False
    
    async def watch_and_reload(
        self,
        name: str,
        module_path: str,
        interval: int = 5
    ) -> None:
        """Watch module and reload on changes."""
        import os
        import time
        
        last_mtime = 0
        
        while True:
            try:
                module_file = importlib.util.find_spec(module_path).origin
                if module_file:
                    mtime = os.path.getmtime(module_file)
                    if mtime > last_mtime:
                        await self.reload_tool(name, module_path)
                        last_mtime = mtime
            except Exception as e:
                logger.error(f"Error watching module: {e}")
            
            await asyncio.sleep(interval)


class ToolLifecycleManager:
    """Unified tool lifecycle manager."""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self.composer = ToolComposer(self.registry)
        self.reloader = ToolReloader(self.registry)
    
    async def register_tool(
        self,
        name: str,
        tool: Any,
        version: str = "1.0.0",
        description: str = "",
        author: str = "SmartCP"
    ) -> bool:
        """Register tool."""
        metadata = ToolMetadata(
            name=name,
            version=version,
            description=description,
            author=author
        )
        return await self.registry.register(name, tool, metadata)
    
    async def compose_tools(
        self,
        name: str,
        description: str,
        tools: List[str],
        executor: Callable
    ) -> bool:
        """Compose tools."""
        return await self.composer.compose(name, description, tools, executor)
    
    async def reload_tool(self, name: str, module_path: str) -> bool:
        """Reload tool."""
        return await self.reloader.reload_tool(name, module_path)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools with metadata."""
        tools = []
        for name in await self.registry.list_tools():
            metadata = await self.registry.get_metadata(name)
            if metadata:
                tools.append({
                    "name": name,
                    "version": metadata.version,
                    "status": metadata.status.value,
                    "description": metadata.description
                })
        return tools


# Global instance
_tool_lifecycle_manager: Optional[ToolLifecycleManager] = None


def get_tool_lifecycle_manager() -> ToolLifecycleManager:
    """Get or create global tool lifecycle manager."""
    global _tool_lifecycle_manager
    if _tool_lifecycle_manager is None:
        _tool_lifecycle_manager = ToolLifecycleManager()
    return _tool_lifecycle_manager

