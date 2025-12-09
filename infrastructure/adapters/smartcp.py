"""
SmartCP Integration Module

Integrates all Phase 1 components:
- FastMCP 2.13 server
- Multi-transport
- Bash executor
- Authentication
"""

import logging
from typing import Optional
from fastmcp import (
    FastMCP213Server, ServerConfig, TransportType, AuthType,
    create_smartcp_server
)
from multi_transport import TransportConfig, create_transport
from bash_executor import get_bash_executor, execute_bash

logger = logging.getLogger(__name__)


class SmartCPIntegration:
    """Main SmartCP integration class."""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """Initialize SmartCP integration."""
        if config is None:
            config = ServerConfig(name="smartcp-server")
        
        self.config = config
        self.server = FastMCP213Server(config)
        self.transport = None
        self.bash_executor = get_bash_executor()
        
        logger.info(f"SmartCP Integration initialized: {config.name}")
    
    def setup_transport(self) -> "SmartCPIntegration":
        """Setup transport layer."""
        transport_config = TransportConfig(
            host=self.config.host,
            port=self.config.port,
            base_path=self.config.base_path
        )
        
        self.transport = create_transport(
            self.config.transport.value,
            transport_config
        )
        
        logger.info(f"Transport configured: {self.config.transport.value}")
        return self
    
    def setup_authentication(self) -> "SmartCPIntegration":
        """Setup authentication."""
        if self.config.auth_type != AuthType.NONE:
            # Auth provider is set in create_smartcp_server
            logger.info(f"Authentication configured: {self.config.auth_type.value}")
        return self
    
    def register_bash_tools(self) -> "SmartCPIntegration":
        """Register bash execution tools."""
        from fastmcp import Tool
        
        # Register bash execution tool
        async def bash_execute(command: str, validate: bool = True):
            """Execute bash command."""
            return await execute_bash(command, validate=validate)
        
        tool = Tool(
            name="bash_execute",
            description="Execute bash commands",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Bash command to execute"},
                    "validate": {"type": "boolean", "description": "Validate command safety"}
                },
                "required": ["command"]
            }
        )
        
        self.server.register_tool("bash_execute", tool, "Execute bash commands")
        logger.info("Bash execution tools registered")
        return self
    
    def register_job_management_tools(self) -> "SmartCPIntegration":
        """Register job management tools."""
        from fastmcp import Tool
        
        # Register job status tool
        async def get_job_status(job_id: str):
            """Get job status."""
            job = await self.bash_executor.get_job(job_id)
            if not job:
                return {"error": f"Job {job_id} not found"}
            
            return {
                "job_id": job.job_id,
                "status": job.status.value,
                "output": job.output,
                "error": job.error,
                "exit_code": job.exit_code
            }
        
        tool = Tool(
            name="get_job_status",
            description="Get job status",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "Job ID"}
                },
                "required": ["job_id"]
            }
        )
        
        self.server.register_tool("get_job_status", tool, "Get job status")
        logger.info("Job management tools registered")
        return self
    
    async def start(self) -> None:
        """Start SmartCP server."""
        logger.info("Starting SmartCP server")
        
        if self.transport is None:
            self.setup_transport()
        
        await self.transport.start()
    
    async def stop(self) -> None:
        """Stop SmartCP server."""
        logger.info("Stopping SmartCP server")
        
        if self.transport:
            await self.transport.stop()


def create_smartcp_integration(
    name: str = "smartcp-server",
    transport: TransportType = TransportType.STDIO,
    auth_type: AuthType = AuthType.NONE,
    **kwargs
) -> SmartCPIntegration:
    """Factory function to create SmartCP integration."""
    server = create_smartcp_server(
        name=name,
        transport=transport,
        auth_type=auth_type,
        **kwargs
    )
    
    integration = SmartCPIntegration(server.config)
    integration.server = server
    
    # Setup components
    integration.setup_transport()
    integration.setup_authentication()
    integration.register_bash_tools()
    integration.register_job_management_tools()
    
    return integration


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create integration
        integration = create_smartcp_integration(
            name="smartcp-demo",
            transport=TransportType.STDIO,
            auth_type=AuthType.ENV,
            env_var="SMARTCP_TOKEN"
        )
        
        # Start server
        await integration.start()
    
    asyncio.run(main())

