"""
Tests for Phase 1 Implementation

Tests for:
- FastMCP 2.13 server
- Multi-transport
- Bash executor
- Authentication
"""

import pytest
import asyncio
from fastmcp_2_13_server import (
    FastMCP213Server, ServerConfig, TransportType, AuthType,
    OAuthProvider, BearerTokenProvider, EnvAuthProvider,
    create_smartcp_server
)
from multi_transport import (
    StdioTransport, SSETransport, HTTPTransport, TransportConfig,
    create_transport
)
from bash_executor import (
    BashExecutor, CommandValidator, JobStatus, execute_bash
)


class TestFastMCP213Server:
    """Tests for FastMCP 2.13 server."""
    
    def test_server_creation(self):
        """Test server creation."""
        config = ServerConfig(name="test-server")
        server = FastMCP213Server(config)
        assert server.config.name == "test-server"
        assert server.mcp is not None
    
    def test_server_composition(self):
        """Test server composition pattern."""
        server = create_smartcp_server("test", transport=TransportType.STDIO)
        assert server.config.name == "test"
        assert server.config.transport == TransportType.STDIO
    
    def test_middleware_stack(self):
        """Test middleware stack."""
        server = FastMCP213Server(ServerConfig(name="test"))
        
        def middleware(request):
            request['processed'] = True
            return request
        
        server.add_middleware(middleware)
        assert len(server.middleware_stack.middlewares) == 1


class TestAuthentication:
    """Tests for authentication providers."""
    
    @pytest.mark.asyncio
    async def test_oauth_provider(self):
        """Test OAuth provider."""
        provider = OAuthProvider(
            client_id="test",
            client_secret="secret",
            provider_url="https://oauth.example.com"
        )
        result = await provider.authenticate({"user": "test"})
        assert result is True
    
    @pytest.mark.asyncio
    async def test_bearer_token_provider(self):
        """Test bearer token provider."""
        provider = BearerTokenProvider(valid_tokens=["token123"])
        result = await provider.authenticate({"token": "token123"})
        assert result is True
        
        result = await provider.authenticate({"token": "invalid"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_env_auth_provider(self):
        """Test environment auth provider."""
        import os
        os.environ['TEST_TOKEN'] = 'secret123'
        
        provider = EnvAuthProvider(env_var='TEST_TOKEN')
        result = await provider.authenticate({"token": "secret123"})
        assert result is True


class TestMultiTransport:
    """Tests for multi-transport."""
    
    def test_transport_creation(self):
        """Test transport creation."""
        config = TransportConfig()
        
        stdio = create_transport("stdio", config)
        assert isinstance(stdio, StdioTransport)
        
        sse = create_transport("sse", config)
        assert isinstance(sse, SSETransport)
        
        http = create_transport("http", config)
        assert isinstance(http, HTTPTransport)
    
    def test_transport_handler_registration(self):
        """Test handler registration."""
        config = TransportConfig()
        transport = create_transport("stdio", config)
        
        def handler(params):
            return {"result": "ok"}
        
        transport.register_handler("test_method", handler)
        assert "test_method" in transport.handlers


class TestBashExecutor:
    """Tests for bash executor."""
    
    def test_command_validation_safe(self):
        """Test validation of safe commands."""
        is_valid, error = CommandValidator.validate("ls -la")
        assert is_valid is True
        assert error is None
    
    def test_command_validation_dangerous(self):
        """Test validation of dangerous commands."""
        is_valid, error = CommandValidator.validate("rm -rf /")
        assert is_valid is False
        assert error is not None
    
    def test_command_validation_not_allowed(self):
        """Test validation of not allowed commands."""
        is_valid, error = CommandValidator.validate("malicious_command")
        assert is_valid is False
        assert error is not None
    
    @pytest.mark.asyncio
    async def test_bash_execution(self):
        """Test bash command execution."""
        executor = BashExecutor()
        job = await executor.execute("echo 'hello'")
        
        # Wait for completion
        while job.status == JobStatus.RUNNING:
            await asyncio.sleep(0.1)
        
        assert job.status == JobStatus.COMPLETED
        assert "hello" in job.output
    
    @pytest.mark.asyncio
    async def test_bash_execution_error(self):
        """Test bash command execution with error."""
        executor = BashExecutor()
        job = await executor.execute("ls /nonexistent")
        
        # Wait for completion
        while job.status == JobStatus.RUNNING:
            await asyncio.sleep(0.1)
        
        assert job.status == JobStatus.FAILED
        assert job.exit_code != 0
    
    @pytest.mark.asyncio
    async def test_job_management(self):
        """Test job management."""
        executor = BashExecutor()
        job = await executor.execute("sleep 1")
        
        # Get job
        retrieved = await executor.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id
        
        # List jobs
        jobs = await executor.list_jobs()
        assert len(jobs) > 0


class TestIntegration:
    """Integration tests."""
    
    def test_full_server_setup(self):
        """Test full server setup."""
        server = create_smartcp_server(
            name="integration-test",
            transport=TransportType.HTTP,
            auth_type=AuthType.BEARER,
            bearer_tokens=["test-token"]
        )
        
        assert server.config.name == "integration-test"
        assert server.auth_provider is not None
        assert isinstance(server.auth_provider, BearerTokenProvider)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

