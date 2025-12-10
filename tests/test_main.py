"""Tests for main.py - FastAPI application endpoints."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main


# =============================================================================
# Mock Response Classes
# =============================================================================


@dataclass
class MockRoutingDecision:
    selected_tool: str
    confidence: float


@dataclass
class MockToolMetadata:
    name: str
    description: str
    category: str
    tags: list
    parameters: dict = None


@dataclass
class MockSearchResult:
    id: str
    content: str
    metadata: dict
    score: float


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_bifrost_client():
    """Create a mock Bifrost client."""
    client = MagicMock()
    client.is_connected = True
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.health = AsyncMock(return_value=True)
    return client


@pytest.fixture
def app_client(mock_bifrost_client):
    """Create test client with mocked bifrost client."""
    main.bifrost_client = mock_bifrost_client
    return TestClient(main.app, raise_server_exceptions=False)


# =============================================================================
# Health Endpoint Tests
# =============================================================================


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_connected(self, app_client, mock_bifrost_client):
        """Test health check when connected."""
        mock_bifrost_client.is_connected = True

        response = app_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["databases"]["bifrost"] == "connected"

    def test_health_disconnected(self, app_client, mock_bifrost_client):
        """Test health check when disconnected."""
        mock_bifrost_client.is_connected = False

        response = app_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["databases"]["bifrost"] == "disconnected"

    def test_health_no_client(self, app_client):
        """Test health check with no client."""
        main.bifrost_client = None

        response = app_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


# =============================================================================
# Route Endpoint Tests
# =============================================================================


class TestRouteEndpoint:
    """Tests for /route endpoint."""

    def test_route_success(self, app_client, mock_bifrost_client):
        """Test successful routing."""
        mock_bifrost_client.route_request = AsyncMock(
            return_value=MockRoutingDecision(
                selected_tool="code_execute",
                confidence=0.95,
            )
        )

        response = app_client.post(
            "/route",
            json={"action": "execute", "prompt": "run code", "context": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["route"] == "code_execute"
        assert data["confidence"] == 0.95

    def test_route_no_client(self, app_client):
        """Test routing with no client."""
        main.bifrost_client = None

        response = app_client.post(
            "/route",
            json={"action": "execute", "prompt": "run code"},
        )
        assert response.status_code == 503

    def test_route_error(self, app_client, mock_bifrost_client):
        """Test routing with error."""
        mock_bifrost_client.route_request = AsyncMock(
            side_effect=Exception("Routing failed")
        )

        response = app_client.post(
            "/route",
            json={"action": "execute", "prompt": "run code"},
        )
        assert response.status_code == 400


# =============================================================================
# Tools Endpoint Tests
# =============================================================================


class TestToolsEndpoint:
    """Tests for /tools endpoints."""

    def test_list_tools(self, app_client, mock_bifrost_client):
        """Test listing tools."""
        mock_bifrost_client.query_tools = AsyncMock(
            return_value=[
                MockToolMetadata(
                    name="execute",
                    description="Execute code",
                    category="execution",
                    tags=["code"],
                ),
            ]
        )

        response = app_client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["tools"][0]["name"] == "execute"

    def test_list_tools_no_client(self, app_client):
        """Test listing tools with no client."""
        main.bifrost_client = None

        response = app_client.get("/tools")
        assert response.status_code == 503

    def test_list_tools_error(self, app_client, mock_bifrost_client):
        """Test listing tools with error."""
        mock_bifrost_client.query_tools = AsyncMock(
            side_effect=Exception("Query failed")
        )

        response = app_client.get("/tools")
        assert response.status_code == 500

    def test_get_tool(self, app_client, mock_bifrost_client):
        """Test getting a specific tool."""
        mock_bifrost_client.query_tool = AsyncMock(
            return_value=MockToolMetadata(
                name="execute",
                description="Execute code",
                category="execution",
                tags=["code"],
                parameters={"code": "string"},
            )
        )

        response = app_client.get("/tools/execute")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "execute"

    def test_get_tool_not_found(self, app_client, mock_bifrost_client):
        """Test getting a tool that doesn't exist."""
        mock_bifrost_client.query_tool = AsyncMock(return_value=None)

        response = app_client.get("/tools/nonexistent")
        assert response.status_code == 404

    def test_get_tool_no_client(self, app_client):
        """Test getting tool with no client."""
        main.bifrost_client = None

        response = app_client.get("/tools/execute")
        assert response.status_code == 503

    def test_get_tool_error(self, app_client, mock_bifrost_client):
        """Test getting tool with error."""
        mock_bifrost_client.query_tool = AsyncMock(
            side_effect=Exception("Query failed")
        )

        response = app_client.get("/tools/execute")
        assert response.status_code == 500


# =============================================================================
# Search Endpoint Tests
# =============================================================================


class TestSearchEndpoint:
    """Tests for /search/semantic endpoint."""

    def test_semantic_search(self, app_client, mock_bifrost_client):
        """Test semantic search."""
        mock_bifrost_client.semantic_search = AsyncMock(
            return_value=[
                MockSearchResult(
                    id="result-1",
                    content="Found content",
                    metadata={"source": "test"},
                    score=0.9,
                ),
            ]
        )

        response = app_client.post("/search/semantic?query=test&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert data["count"] == 1
        assert data["results"][0]["score"] == 0.9

    def test_semantic_search_no_client(self, app_client):
        """Test semantic search with no client."""
        main.bifrost_client = None

        response = app_client.post("/search/semantic?query=test")
        assert response.status_code == 503

    def test_semantic_search_error(self, app_client, mock_bifrost_client):
        """Test semantic search with error."""
        mock_bifrost_client.semantic_search = AsyncMock(
            side_effect=Exception("Search failed")
        )

        response = app_client.post("/search/semantic?query=test")
        assert response.status_code == 400


# =============================================================================
# Lifespan Tests
# =============================================================================


class TestLifespan:
    """Tests for application lifespan."""

    @pytest.mark.asyncio
    async def test_lifespan_success(self):
        """Test successful lifespan startup and shutdown."""
        with patch("main.BifrostClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_client_class.return_value = mock_client

            async with main.lifespan(main.app):
                assert main.bifrost_client is not None
                mock_client.connect.assert_called_once()

            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_startup_error(self):
        """Test lifespan with startup error."""
        with patch("main.BifrostClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                async with main.lifespan(main.app):
                    pass

            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_error(self):
        """Test lifespan with shutdown error (should not raise)."""
        with patch("main.BifrostClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock()
            mock_client.disconnect = AsyncMock(side_effect=Exception("Disconnect failed"))
            mock_client_class.return_value = mock_client

            # Should not raise even if disconnect fails
            async with main.lifespan(main.app):
                pass


# =============================================================================
# Health Check Error Path
# =============================================================================


class TestHealthCheckError:
    """Tests for health check error handling."""

    def test_health_exception(self, app_client, mock_bifrost_client):
        """Test health check when exception occurs."""
        # Mock is_connected to raise
        type(mock_bifrost_client).is_connected = property(
            lambda self: (_ for _ in ()).throw(Exception("Connection error"))
        )

        response = app_client.get("/health")
        assert response.status_code == 500
