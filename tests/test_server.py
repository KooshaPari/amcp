"""Tests for server.py - SmartCP MCP Server."""

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config.settings import SmartCPSettings, ServerSettings, BifrostSettings, AuthSettings
from server import SmartCPServer, create_server, create_app


# =============================================================================
# SmartCPServer Tests
# =============================================================================


class TestSmartCPServer:
    """Tests for SmartCPServer class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for server."""
        settings = SmartCPSettings(
            version="1.0.0",
            environment="test",
            server=ServerSettings(port=8000),
            bifrost=BifrostSettings(url="http://localhost:8080/graphql"),
            auth=AuthSettings(enabled=True),
        )

        mock_mcp = MagicMock()
        mock_mcp.http_app.return_value = FastAPI()

        mock_bifrost = MagicMock()
        mock_bifrost.health = AsyncMock(return_value=True)

        mock_validator = MagicMock()

        return settings, mock_mcp, mock_bifrost, mock_validator

    def test_init(self, mock_dependencies):
        """Test server initialization."""
        settings, mcp, bifrost, validator = mock_dependencies

        server = SmartCPServer(
            settings=settings,
            mcp=mcp,
            bifrost_client=bifrost,
            token_validator=validator,
        )

        assert server.settings == settings
        assert server.mcp == mcp
        assert server.bifrost_client == bifrost
        assert server.token_validator == validator

    def test_create_fastapi_app(self, mock_dependencies):
        """Test FastAPI app creation."""
        settings, mcp, bifrost, validator = mock_dependencies

        server = SmartCPServer(
            settings=settings,
            mcp=mcp,
            bifrost_client=bifrost,
            token_validator=validator,
        )

        app = server.create_fastapi_app()
        assert app is not None
        assert app.title == "SmartCP MCP Server"

    def test_health_endpoint(self, mock_dependencies):
        """Test health check endpoint."""
        settings, mcp, bifrost, validator = mock_dependencies

        server = SmartCPServer(
            settings=settings,
            mcp=mcp,
            bifrost_client=bifrost,
            token_validator=validator,
        )

        app = server.create_fastapi_app()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_healthz_endpoint(self, mock_dependencies):
        """Test healthz endpoint (alternate)."""
        settings, mcp, bifrost, validator = mock_dependencies

        server = SmartCPServer(
            settings=settings,
            mcp=mcp,
            bifrost_client=bifrost,
            token_validator=validator,
        )

        app = server.create_fastapi_app()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/healthz")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ready_endpoint_connected(self, mock_dependencies):
        """Test readiness endpoint when backend is connected."""
        settings, mcp, bifrost, validator = mock_dependencies
        bifrost.health = AsyncMock(return_value=True)

        server = SmartCPServer(
            settings=settings,
            mcp=mcp,
            bifrost_client=bifrost,
            token_validator=validator,
        )

        app = server.create_fastapi_app()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["backend"] == "connected"

    @pytest.mark.asyncio
    async def test_ready_endpoint_disconnected(self, mock_dependencies):
        """Test readiness endpoint when backend is disconnected."""
        settings, mcp, bifrost, validator = mock_dependencies
        bifrost.health = AsyncMock(return_value=False)

        server = SmartCPServer(
            settings=settings,
            mcp=mcp,
            bifrost_client=bifrost,
            token_validator=validator,
        )

        app = server.create_fastapi_app()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["backend"] == "disconnected"

    @pytest.mark.asyncio
    async def test_ready_endpoint_no_bifrost(self, mock_dependencies):
        """Test readiness endpoint when no bifrost client."""
        settings, mcp, _, validator = mock_dependencies

        server = SmartCPServer(
            settings=settings,
            mcp=mcp,
            bifrost_client=None,
            token_validator=validator,
        )

        app = server.create_fastapi_app()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["backend"] == "not_configured"


# =============================================================================
# Factory Functions Tests
# =============================================================================


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_server_default(self):
        """Test create_server with defaults."""
        mock_settings = SmartCPSettings(
            environment="test",
            bifrost=BifrostSettings(url=""),
            auth=AuthSettings(),
        )

        mock_mcp_instance = MagicMock()

        with patch("server.get_settings", return_value=mock_settings):
            with patch.object(
                sys.modules.get("server") or __import__("server"),
                "FastMCP" if hasattr(__import__("server"), "FastMCP") else "_",
                mock_mcp_instance,
                create=True,
            ):
                # Import fresh to get the patched version
                with patch.dict(os.environ, {"JWT_SECRET": "test-secret"}):
                    with patch("fastmcp.FastMCP", return_value=mock_mcp_instance):
                        server = create_server(settings=mock_settings)

        assert isinstance(server, SmartCPServer)
        assert server.settings == mock_settings

    def test_create_server_with_bifrost(self):
        """Test create_server with bifrost configured."""
        mock_settings = SmartCPSettings(
            environment="test",
            bifrost=BifrostSettings(url="http://localhost:8080/graphql"),
            auth=AuthSettings(),
        )

        mock_mcp_instance = MagicMock()

        with patch.dict(os.environ, {"JWT_SECRET": "test-secret"}):
            with patch("fastmcp.FastMCP", return_value=mock_mcp_instance):
                server = create_server(settings=mock_settings)

        assert server.bifrost_client is not None

    def test_create_server_custom_settings(self):
        """Test create_server with custom settings."""
        custom_settings = SmartCPSettings(
            version="2.0.0",
            environment="production",
        )

        mock_mcp_instance = MagicMock()

        with patch.dict(os.environ, {"JWT_SECRET": "test-secret"}):
            with patch("fastmcp.FastMCP", return_value=mock_mcp_instance):
                server = create_server(settings=custom_settings)

        assert server.settings == custom_settings
        assert server.settings.version == "2.0.0"

    def test_create_app(self):
        """Test create_app function."""
        mock_server = MagicMock()
        mock_app = MagicMock()
        mock_server.create_fastapi_app.return_value = mock_app

        with patch("server.create_server", return_value=mock_server):
            app = create_app()

        assert app == mock_app
        mock_server.create_fastapi_app.assert_called_once()

    def test_create_server_no_fastmcp(self):
        """Test create_server when FastMCP not installed."""
        settings = SmartCPSettings()

        with patch("fastmcp.FastMCP", side_effect=ImportError("No module")):
            with patch.dict(os.environ, {"JWT_SECRET": "test"}):
                with pytest.raises(ImportError):
                    create_server(settings=settings)


# =============================================================================
# Server Run Tests
# =============================================================================


class TestServerRun:
    """Tests for server run method."""

    def test_run_defaults(self):
        """Test run with default parameters."""
        settings = SmartCPSettings(version="1.0.0")
        mock_mcp = MagicMock()
        mock_mcp.http_app.return_value = FastAPI()

        server = SmartCPServer(
            settings=settings,
            mcp=mock_mcp,
            bifrost_client=None,
            token_validator=MagicMock(),
        )

        with patch("uvicorn.run") as mock_uvicorn_run:
            server.run()
            mock_uvicorn_run.assert_called_once()
            call_kwargs = mock_uvicorn_run.call_args.kwargs
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["reload"] is False

    def test_run_custom_params(self):
        """Test run with custom parameters."""
        settings = SmartCPSettings(version="1.0.0")
        mock_mcp = MagicMock()
        mock_mcp.http_app.return_value = FastAPI()

        server = SmartCPServer(
            settings=settings,
            mcp=mock_mcp,
            bifrost_client=None,
            token_validator=MagicMock(),
        )

        with patch("uvicorn.run") as mock_uvicorn_run:
            server.run(host="127.0.0.1", port=3000, reload=True)
            call_kwargs = mock_uvicorn_run.call_args.kwargs
            assert call_kwargs["host"] == "127.0.0.1"
            assert call_kwargs["port"] == 3000
            assert call_kwargs["reload"] is True

    def test_create_server_default_settings(self):
        """Test create_server loads default settings when None provided."""
        mock_mcp_instance = MagicMock()

        with patch.dict(os.environ, {"JWT_SECRET": "test-secret"}):
            with patch("fastmcp.FastMCP", return_value=mock_mcp_instance):
                with patch("server.get_settings") as mock_get_settings:
                    mock_settings = SmartCPSettings(
                        environment="test",
                        bifrost=BifrostSettings(url=""),
                        auth=AuthSettings(),
                    )
                    mock_get_settings.return_value = mock_settings

                    server = create_server()

                    assert server.settings == mock_settings
                    mock_get_settings.assert_called_once()
