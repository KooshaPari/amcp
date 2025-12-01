"""
MCP Security & Sandboxing

Provides:
- Process sandboxing
- Permission management
- Resource limits
- Audit logging
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class Permission(Enum):
    """MCP permissions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"


@dataclass
class ResourceLimits:
    """Resource limits."""
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    max_timeout_seconds: int = 300
    max_file_size_mb: int = 100


@dataclass
class AuditLog:
    """Audit log entry."""
    timestamp: datetime
    mcp_name: str
    action: str
    resource: str
    allowed: bool
    details: Dict[str, Any]


class MCPSandbox:
    """Sandbox MCPs."""
    
    def __init__(self):
        self.permissions: Dict[str, List[Permission]] = {}
        self.resource_limits: Dict[str, ResourceLimits] = {}
        self.audit_logs: List[AuditLog] = []
        self.sandboxed_mcps: Dict[str, bool] = {}
    
    async def sandbox_mcp(self, mcp_name: str) -> bool:
        """Sandbox MCP."""
        try:
            logger.info(f"Sandboxing MCP: {mcp_name}")
            
            # Set default permissions
            self.permissions[mcp_name] = [
                Permission.READ,
                Permission.EXECUTE
            ]
            
            # Set default resource limits
            self.resource_limits[mcp_name] = ResourceLimits()
            
            self.sandboxed_mcps[mcp_name] = True
            
            logger.info(f"Sandboxed {mcp_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error sandboxing MCP: {e}")
            return False
    
    async def set_permissions(self, mcp_name: str, permissions: List[Permission]) -> bool:
        """Set MCP permissions."""
        try:
            logger.info(f"Setting permissions for {mcp_name}: {permissions}")
            
            self.permissions[mcp_name] = permissions
            
            await self._audit_log(
                mcp_name,
                "set_permissions",
                "permissions",
                True,
                {"permissions": [p.value for p in permissions]}
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting permissions: {e}")
            return False
    
    async def limit_resources(self, mcp_name: str, limits: ResourceLimits) -> bool:
        """Limit MCP resources."""
        try:
            logger.info(f"Limiting resources for {mcp_name}")
            
            self.resource_limits[mcp_name] = limits
            
            await self._audit_log(
                mcp_name,
                "limit_resources",
                "resources",
                True,
                {
                    "max_memory_mb": limits.max_memory_mb,
                    "max_cpu_percent": limits.max_cpu_percent,
                    "max_timeout_seconds": limits.max_timeout_seconds
                }
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error limiting resources: {e}")
            return False
    
    async def check_permission(self, mcp_name: str, permission: Permission) -> bool:
        """Check MCP permission."""
        try:
            if mcp_name not in self.permissions:
                return False
            
            allowed = permission in self.permissions[mcp_name]
            
            await self._audit_log(
                mcp_name,
                "check_permission",
                permission.value,
                allowed,
                {}
            )
            
            return allowed
        
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def check_resource_limits(self, mcp_name: str, resource_usage: Dict[str, Any]) -> bool:
        """Check resource limits."""
        try:
            if mcp_name not in self.resource_limits:
                return True
            
            limits = self.resource_limits[mcp_name]
            
            # Check memory
            memory_mb = resource_usage.get("memory_mb", 0)
            if memory_mb > limits.max_memory_mb:
                logger.warning(f"Memory limit exceeded for {mcp_name}")
                return False
            
            # Check CPU
            cpu_percent = resource_usage.get("cpu_percent", 0)
            if cpu_percent > limits.max_cpu_percent:
                logger.warning(f"CPU limit exceeded for {mcp_name}")
                return False
            
            # Check timeout
            timeout_seconds = resource_usage.get("timeout_seconds", 0)
            if timeout_seconds > limits.max_timeout_seconds:
                logger.warning(f"Timeout limit exceeded for {mcp_name}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking resource limits: {e}")
            return False
    
    async def audit_execution(self, execution: Dict[str, Any]) -> None:
        """Audit MCP execution."""
        try:
            mcp_name = execution.get("mcp_name")
            action = execution.get("action")
            resource = execution.get("resource", "unknown")
            allowed = execution.get("allowed", True)
            
            await self._audit_log(
                mcp_name,
                action,
                resource,
                allowed,
                execution.get("details", {})
            )
        
        except Exception as e:
            logger.error(f"Error auditing execution: {e}")
    
    async def _audit_log(self, mcp_name: str, action: str, resource: str, allowed: bool, details: Dict[str, Any]) -> None:
        """Add audit log entry."""
        log_entry = AuditLog(
            timestamp=datetime.now(),
            mcp_name=mcp_name,
            action=action,
            resource=resource,
            allowed=allowed,
            details=details
        )
        
        self.audit_logs.append(log_entry)
        
        if not allowed:
            logger.warning(f"SECURITY: {mcp_name} denied {action} on {resource}")
    
    async def get_audit_logs(self, mcp_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit logs."""
        logs = self.audit_logs
        
        if mcp_name:
            logs = [l for l in logs if l.mcp_name == mcp_name]
        
        return [
            {
                "timestamp": l.timestamp.isoformat(),
                "mcp_name": l.mcp_name,
                "action": l.action,
                "resource": l.resource,
                "allowed": l.allowed,
                "details": l.details
            }
            for l in logs
        ]
    
    async def get_security_status(self, mcp_name: str) -> Dict[str, Any]:
        """Get MCP security status."""
        return {
            "mcp_name": mcp_name,
            "sandboxed": self.sandboxed_mcps.get(mcp_name, False),
            "permissions": [p.value for p in self.permissions.get(mcp_name, [])],
            "resource_limits": {
                "max_memory_mb": self.resource_limits.get(mcp_name, ResourceLimits()).max_memory_mb,
                "max_cpu_percent": self.resource_limits.get(mcp_name, ResourceLimits()).max_cpu_percent,
                "max_timeout_seconds": self.resource_limits.get(mcp_name, ResourceLimits()).max_timeout_seconds
            }
        }


# Global instance
_sandbox: Optional[MCPSandbox] = None


def get_mcp_sandbox() -> MCPSandbox:
    """Get or create global sandbox."""
    global _sandbox
    if _sandbox is None:
        _sandbox = MCPSandbox()
    return _sandbox

