"""
MCP Registry Integration for SmartCP

Provides:
- Registry client
- Auto-installation
- Dependency resolution
- Tool discovery
"""

import logging
import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PackageManager(Enum):
    """Package managers."""
    NPM = "npm"
    PIP = "pip"
    GO = "go"
    CARGO = "cargo"


@dataclass
class MCPPackage:
    """MCP package metadata."""
    name: str
    version: str
    description: str
    author: str
    repository: str
    package_manager: PackageManager
    dependencies: Dict[str, str]
    tools: List[str]
    resources: List[str]


class RegistryClient:
    """MCP Registry client."""
    
    def __init__(self, registry_url: str = "https://registry.mcp.io"):
        self.registry_url = registry_url
        self.cache: Dict[str, MCPPackage] = {}
    
    async def search(self, query: str) -> List[MCPPackage]:
        """Search registry for packages."""
        try:
            # Simulated search - in production would call registry API
            logger.info(f"Searching registry for: {query}")
            
            # Mock results
            results = [
                MCPPackage(
                    name=f"mcp-{query}",
                    version="1.0.0",
                    description=f"MCP package for {query}",
                    author="SmartCP",
                    repository=f"https://github.com/smartcp/mcp-{query}",
                    package_manager=PackageManager.NPM,
                    dependencies={},
                    tools=[f"{query}_tool"],
                    resources=[f"{query}_resource"]
                )
            ]
            
            return results
        except Exception as e:
            logger.error(f"Error searching registry: {e}")
            return []
    
    async def get_package(self, name: str, version: str = "latest") -> Optional[MCPPackage]:
        """Get package from registry."""
        try:
            cache_key = f"{name}@{version}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            logger.info(f"Fetching package: {name}@{version}")
            
            # Mock package - in production would call registry API
            package = MCPPackage(
                name=name,
                version=version,
                description=f"MCP package: {name}",
                author="SmartCP",
                repository=f"https://github.com/smartcp/{name}",
                package_manager=PackageManager.NPM,
                dependencies={},
                tools=[f"{name}_tool"],
                resources=[f"{name}_resource"]
            )
            
            self.cache[cache_key] = package
            return package
        except Exception as e:
            logger.error(f"Error fetching package: {e}")
            return None


class DependencyResolver:
    """Dependency resolver for MCP packages."""
    
    def __init__(self, registry_client: RegistryClient):
        self.registry = registry_client
        self.resolved: Dict[str, str] = {}
    
    async def resolve(self, package_name: str, version: str = "latest") -> Dict[str, str]:
        """Resolve package dependencies."""
        try:
            package = await self.registry.get_package(package_name, version)
            if not package:
                return {}
            
            resolved = {package_name: version}
            
            # Recursively resolve dependencies
            for dep_name, dep_version in package.dependencies.items():
                dep_resolved = await self.resolve(dep_name, dep_version)
                resolved.update(dep_resolved)
            
            self.resolved = resolved
            return resolved
        except Exception as e:
            logger.error(f"Error resolving dependencies: {e}")
            return {}


class PackageInstaller:
    """Package installer for MCP packages."""
    
    async def install(
        self,
        package_name: str,
        version: str = "latest",
        package_manager: PackageManager = PackageManager.NPM
    ) -> bool:
        """Install MCP package."""
        try:
            logger.info(f"Installing {package_name}@{version} using {package_manager.value}")
            
            if package_manager == PackageManager.NPM:
                cmd = ["npm", "install", f"{package_name}@{version}"]
            elif package_manager == PackageManager.PIP:
                cmd = ["pip", "install", f"{package_name}=={version}"]
            elif package_manager == PackageManager.GO:
                cmd = ["go", "get", f"github.com/smartcp/{package_name}@{version}"]
            elif package_manager == PackageManager.CARGO:
                cmd = ["cargo", "add", f"{package_name}@{version}"]
            else:
                return False
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully installed {package_name}")
                return True
            else:
                logger.error(f"Installation failed: {stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"Error installing package: {e}")
            return False
    
    async def uninstall(
        self,
        package_name: str,
        package_manager: PackageManager = PackageManager.NPM
    ) -> bool:
        """Uninstall MCP package."""
        try:
            logger.info(f"Uninstalling {package_name} using {package_manager.value}")
            
            if package_manager == PackageManager.NPM:
                cmd = ["npm", "uninstall", package_name]
            elif package_manager == PackageManager.PIP:
                cmd = ["pip", "uninstall", "-y", package_name]
            elif package_manager == PackageManager.GO:
                cmd = ["go", "get", "-u", f"github.com/smartcp/{package_name}@none"]
            elif package_manager == PackageManager.CARGO:
                cmd = ["cargo", "remove", package_name]
            else:
                return False
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully uninstalled {package_name}")
                return True
            else:
                logger.error(f"Uninstallation failed: {stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"Error uninstalling package: {e}")
            return False


class MCPRegistry:
    """Unified MCP Registry system."""
    
    def __init__(self, registry_url: str = "https://registry.mcp.io"):
        self.client = RegistryClient(registry_url)
        self.resolver = DependencyResolver(self.client)
        self.installer = PackageInstaller()
        self.installed_packages: Dict[str, str] = {}
    
    async def search(self, query: str) -> List[MCPPackage]:
        """Search for packages."""
        return await self.client.search(query)
    
    async def install(
        self,
        package_name: str,
        version: str = "latest",
        auto_resolve: bool = True
    ) -> bool:
        """Install package with optional dependency resolution."""
        try:
            if auto_resolve:
                dependencies = await self.resolver.resolve(package_name, version)
                logger.info(f"Resolved dependencies: {dependencies}")
            
            package = await self.client.get_package(package_name, version)
            if not package:
                return False
            
            success = await self.installer.install(
                package_name,
                version,
                package.package_manager
            )
            
            if success:
                self.installed_packages[package_name] = version
            
            return success
        except Exception as e:
            logger.error(f"Error installing package: {e}")
            return False
    
    async def uninstall(self, package_name: str) -> bool:
        """Uninstall package."""
        try:
            package = await self.client.get_package(package_name)
            if not package:
                return False
            
            success = await self.installer.uninstall(
                package_name,
                package.package_manager
            )
            
            if success and package_name in self.installed_packages:
                del self.installed_packages[package_name]
            
            return success
        except Exception as e:
            logger.error(f"Error uninstalling package: {e}")
            return False
    
    async def list_installed(self) -> Dict[str, str]:
        """List installed packages."""
        return self.installed_packages.copy()


# Global instance
_mcp_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    """Get or create global MCP registry."""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPRegistry()
    return _mcp_registry

