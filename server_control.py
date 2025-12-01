"""
Server Control & Management for SmartCP

Provides:
- Start/stop/restart
- Health checks
- Metrics collection
- Graceful shutdown
"""

import asyncio
import logging
import psutil
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """Server status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class HealthStatus:
    """Health status."""
    status: ServerStatus
    uptime: float
    memory_usage: float
    cpu_usage: float
    request_count: int
    error_count: int
    timestamp: datetime


@dataclass
class ServerMetrics:
    """Server metrics."""
    uptime: float
    memory_usage: float
    cpu_usage: float
    request_count: int
    error_count: int
    avg_response_time: float


class ServerController:
    """Server controller for lifecycle management."""
    
    def __init__(self, server_name: str = "smartcp-server"):
        self.server_name = server_name
        self.status = ServerStatus.STOPPED
        self.process: Optional[asyncio.Task] = None
        self.start_time: Optional[datetime] = None
        self.request_count = 0
        self.error_count = 0
        self.response_times: list = []
    
    async def start(self) -> bool:
        """Start server."""
        try:
            if self.status != ServerStatus.STOPPED:
                logger.warning(f"Server already running: {self.status.value}")
                return False
            
            self.status = ServerStatus.STARTING
            self.start_time = datetime.now()
            self.request_count = 0
            self.error_count = 0
            self.response_times = []
            
            logger.info(f"Starting server: {self.server_name}")
            
            # Start server process
            self.process = asyncio.create_task(self._run_server())
            
            # Wait for server to be ready
            await asyncio.sleep(1)
            
            self.status = ServerStatus.RUNNING
            logger.info(f"Server started: {self.server_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            self.status = ServerStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop server."""
        try:
            if self.status == ServerStatus.STOPPED:
                return True
            
            self.status = ServerStatus.STOPPING
            logger.info(f"Stopping server: {self.server_name}")
            
            if self.process:
                self.process.cancel()
                try:
                    await self.process
                except asyncio.CancelledError:
                    pass
            
            self.status = ServerStatus.STOPPED
            logger.info(f"Server stopped: {self.server_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            self.status = ServerStatus.ERROR
            return False
    
    async def restart(self) -> bool:
        """Restart server."""
        try:
            logger.info(f"Restarting server: {self.server_name}")
            
            if not await self.stop():
                return False
            
            await asyncio.sleep(1)
            
            return await self.start()
        
        except Exception as e:
            logger.error(f"Error restarting server: {e}")
            return False
    
    async def _run_server(self) -> None:
        """Run server process."""
        try:
            while self.status == ServerStatus.RUNNING:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    async def get_health(self) -> HealthStatus:
        """Get server health status."""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent(interval=0.1)
        except:
            memory_usage = 0.0
            cpu_usage = 0.0
        
        return HealthStatus(
            status=self.status,
            uptime=uptime,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            request_count=self.request_count,
            error_count=self.error_count,
            timestamp=datetime.now()
        )
    
    async def get_metrics(self) -> ServerMetrics:
        """Get server metrics."""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent(interval=0.1)
        except:
            memory_usage = 0.0
            cpu_usage = 0.0
        
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0.0
        
        return ServerMetrics(
            uptime=uptime,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            request_count=self.request_count,
            error_count=self.error_count,
            avg_response_time=avg_response_time
        )
    
    def record_request(self, response_time: float, success: bool = True) -> None:
        """Record request metrics."""
        self.request_count += 1
        if not success:
            self.error_count += 1
        self.response_times.append(response_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]


class HealthChecker:
    """Health checker for server."""
    
    def __init__(self, controller: ServerController, interval: int = 30):
        self.controller = controller
        self.interval = interval
        self.health_history: list = []
    
    async def start_checking(self) -> None:
        """Start health checking."""
        logger.info("Health checker started")
        
        while True:
            try:
                health = await self.controller.get_health()
                self.health_history.append(health)
                
                # Keep only last 100 health checks
                if len(self.health_history) > 100:
                    self.health_history = self.health_history[-100:]
                
                if health.status != ServerStatus.RUNNING:
                    logger.warning(f"Server health check failed: {health.status.value}")
                
                await asyncio.sleep(self.interval)
            
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(self.interval)
    
    async def get_health_history(self) -> list:
        """Get health history."""
        return self.health_history.copy()


class ServerControlManager:
    """Unified server control manager."""
    
    def __init__(self, server_name: str = "smartcp-server"):
        self.controller = ServerController(server_name)
        self.health_checker = HealthChecker(self.controller)
    
    async def start(self) -> bool:
        """Start server."""
        return await self.controller.start()
    
    async def stop(self) -> bool:
        """Stop server."""
        return await self.controller.stop()
    
    async def restart(self) -> bool:
        """Restart server."""
        return await self.controller.restart()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        health = await self.controller.get_health()
        metrics = await self.controller.get_metrics()
        
        return {
            "status": health.status.value,
            "uptime": health.uptime,
            "memory_usage_mb": health.memory_usage,
            "cpu_usage_percent": health.cpu_usage,
            "request_count": health.request_count,
            "error_count": health.error_count,
            "avg_response_time": metrics.avg_response_time,
            "timestamp": health.timestamp.isoformat()
        }
    
    async def start_health_checking(self) -> None:
        """Start health checking."""
        asyncio.create_task(self.health_checker.start_checking())


# Global instance
_server_control_manager: Optional[ServerControlManager] = None


def get_server_control_manager() -> ServerControlManager:
    """Get or create global server control manager."""
    global _server_control_manager
    if _server_control_manager is None:
        _server_control_manager = ServerControlManager()
    return _server_control_manager

