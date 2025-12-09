"""
MCP Lifecycle Manager

Provides:
- Process management
- Health monitoring
- Auto-restart
- Resource management
"""

import asyncio
import logging
import subprocess
import psutil
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MCPProcessInfo:
    """MCP process information."""
    name: str
    pid: Optional[int] = None
    process: Optional[subprocess.Popen] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


class MCPLifecycleManager:
    """Manage MCP server lifecycle."""
    
    def __init__(self, max_restarts: int = 3, restart_delay: int = 5):
        self.processes: Dict[str, MCPProcessInfo] = {}
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.monitoring = False
    
    async def start_mcp(self, name: str, command: List[str]) -> bool:
        """Start MCP server."""
        try:
            logger.info(f"Starting MCP server: {name}")
            
            if name in self.processes and self.processes[name].process:
                logger.warning(f"MCP already running: {name}")
                return False
            
            # Start process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            process_info = MCPProcessInfo(
                name=name,
                pid=process.pid,
                process=process,
                start_time=datetime.now()
            )
            
            self.processes[name] = process_info
            logger.info(f"Started {name} with PID {process.pid}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting MCP: {e}")
            return False
    
    async def stop_mcp(self, name: str) -> bool:
        """Stop MCP server."""
        try:
            logger.info(f"Stopping MCP server: {name}")
            
            if name not in self.processes:
                return False
            
            process_info = self.processes[name]
            
            if process_info.process:
                process_info.process.terminate()
                
                try:
                    process_info.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process_info.process.kill()
                
                process_info.process = None
                process_info.pid = None
                logger.info(f"Stopped {name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error stopping MCP: {e}")
            return False
    
    async def restart_mcp(self, name: str, command: List[str]) -> bool:
        """Restart MCP server."""
        try:
            logger.info(f"Restarting MCP server: {name}")
            
            await self.stop_mcp(name)
            await asyncio.sleep(self.restart_delay)
            
            if name in self.processes:
                self.processes[name].restart_count += 1
                self.processes[name].last_restart = datetime.now()
            
            return await self.start_mcp(name, command)
        
        except Exception as e:
            logger.error(f"Error restarting MCP: {e}")
            return False
    
    async def monitor_health(self, name: str) -> bool:
        """Monitor MCP server health."""
        try:
            if name not in self.processes:
                return False
            
            process_info = self.processes[name]
            
            if not process_info.process:
                return False
            
            # Check if process is still running
            if process_info.process.poll() is not None:
                logger.warning(f"MCP process died: {name}")
                return False
            
            # Get resource usage
            try:
                proc = psutil.Process(process_info.pid)
                process_info.memory_usage = proc.memory_info().rss / 1024 / 1024
                process_info.cpu_usage = proc.cpu_percent(interval=0.1)
            except:
                pass
            
            return True
        
        except Exception as e:
            logger.error(f"Error monitoring health: {e}")
            return False
    
    async def handle_failure(self, name: str, command: List[str]) -> bool:
        """Handle MCP server failure."""
        try:
            logger.warning(f"Handling failure for {name}")
            
            if name not in self.processes:
                return False
            
            process_info = self.processes[name]
            
            # Check restart limit
            if process_info.restart_count >= self.max_restarts:
                logger.error(f"Max restarts exceeded for {name}")
                return False
            
            # Restart
            return await self.restart_mcp(name, command)
        
        except Exception as e:
            logger.error(f"Error handling failure: {e}")
            return False
    
    async def start_monitoring(self, check_interval: int = 10) -> None:
        """Start health monitoring."""
        logger.info("Starting MCP health monitoring")
        self.monitoring = True
        
        while self.monitoring:
            try:
                for name in list(self.processes.keys()):
                    health = await self.monitor_health(name)
                    
                    if not health:
                        logger.warning(f"Health check failed for {name}")
                
                await asyncio.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        logger.info("Stopping MCP health monitoring")
        self.monitoring = False
    
    async def get_status(self, name: str) -> Optional[Dict]:
        """Get MCP status."""
        if name not in self.processes:
            return None
        
        process_info = self.processes[name]
        
        return {
            "name": name,
            "pid": process_info.pid,
            "running": process_info.process is not None,
            "start_time": process_info.start_time.isoformat() if process_info.start_time else None,
            "restart_count": process_info.restart_count,
            "memory_usage_mb": process_info.memory_usage,
            "cpu_usage_percent": process_info.cpu_usage
        }
    
    async def list_processes(self) -> List[Dict]:
        """List all MCP processes."""
        statuses = []
        for name in self.processes.keys():
            status = await self.get_status(name)
            if status:
                statuses.append(status)
        return statuses


# Global instance
_mcp_lifecycle: Optional[MCPLifecycleManager] = None


def get_mcp_lifecycle_manager() -> MCPLifecycleManager:
    """Get or create global MCP lifecycle manager."""
    global _mcp_lifecycle
    if _mcp_lifecycle is None:
        _mcp_lifecycle = MCPLifecycleManager()
    return _mcp_lifecycle

