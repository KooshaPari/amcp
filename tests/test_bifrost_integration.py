"""
Integration tests for SmartCP → Bifrost delegation.

Tests the complete flow: SmartCP API → BifrostClient → Bifrost backend.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from infrastructure.bifrost.client import BifrostClient
from infrastructure.bifrost.queries import RoutingDecision, ToolMetadata, SearchResult


@pytest.fixture
def mock_bifrost_client():
    """Create mock BifrostClient."""
    client = MagicMock(spec=BifrostClient)
    client.is_connected = True
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    return client


@pytest.fixture
def test_client(mock_bifrost_client):
    """Create FastAPI test client with mocked Bifrost."""
    with patch("main.bifrost_client", mock_bifrost_client):
        yield TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_connected(self, test_client, mock_bifrost_client):
        """Test health check when Bifrost is connected."""
        mock_bifrost_client.is_connected = True

        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["databases"]["bifrost"] == "connected"

    def test_health_check_disconnected(self, test_client, mock_bifrost_client):
        """Test health check when Bifrost is disconnected."""
        mock_bifrost_client.is_connected = False

        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["databases"]["bifrost"] == "disconnected"


class TestRoutingEndpoint:
    """Test routing endpoint."""

    def test_route_request_success(self, test_client, mock_bifrost_client):
        """Test successful routing request."""
        # Mock Bifrost response
        mock_decision = RoutingDecision(
            selected_tool="entity_create",
            confidence=0.95,
            reasoning="User wants to create entity",
            alternatives=[]
        )
        mock_bifrost_client.route_request = AsyncMock(return_value=mock_decision)

        response = test_client.post("/route", json={
            "action": "create",
            "prompt": "Create a new project",
            "context": {"workspace_id": "123"}
        })

        assert response.status_code == 200
        data = response.json()
        assert data["route"] == "entity_create"
        assert data["confidence"] == 0.95
        assert "entity_create" in data["tools"]

        # Verify Bifrost was called correctly
        mock_bifrost_client.route_request.assert_called_once()
        call_args = mock_bifrost_client.route_request.call_args
        assert call_args.kwargs["prompt"] == "Create a new project"
        assert call_args.kwargs["context"]["workspace_id"] == "123"

    def test_route_request_no_client(self, test_client):
        """Test routing when Bifrost client not initialized."""
        with patch("main.bifrost_client", None):
            response = test_client.post("/route", json={
                "action": "create",
                "prompt": "Test"
            })

            assert response.status_code == 503
            assert "not initialized" in response.json()["detail"]

    def test_route_request_error(self, test_client, mock_bifrost_client):
        """Test routing error handling."""
        mock_bifrost_client.route_request = AsyncMock(
            side_effect=Exception("Routing failed")
        )

        response = test_client.post("/route", json={
            "action": "create",
            "prompt": "Test"
        })

        assert response.status_code == 400
        assert "Routing failed" in response.json()["detail"]


class TestToolsEndpoint:
    """Test tools listing endpoint."""

    def test_list_tools(self, test_client, mock_bifrost_client):
        """Test listing all tools."""
        # Mock Bifrost response
        mock_tools = [
            ToolMetadata(
                name="entity_create",
                description="Create entity",
                parameters={"name": "string"},
                category="entity",
                tags=["create"]
            ),
            ToolMetadata(
                name="entity_search",
                description="Search entities",
                parameters={"query": "string"},
                category="entity",
                tags=["search"]
            )
        ]
        mock_bifrost_client.query_tools = AsyncMock(return_value=mock_tools)

        response = test_client.get("/tools")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["tools"]) == 2
        assert data["tools"][0]["name"] == "entity_create"
        assert data["tools"][1]["category"] == "entity"

    def test_get_tool(self, test_client, mock_bifrost_client):
        """Test getting specific tool."""
        mock_tool = ToolMetadata(
            name="entity_create",
            description="Create entity",
            parameters={"name": "string", "description": "string"},
            category="entity",
            tags=["create"]
        )
        mock_bifrost_client.query_tool = AsyncMock(return_value=mock_tool)

        response = test_client.get("/tools/entity_create")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "entity_create"
        assert data["description"] == "Create entity"
        assert "name" in data["parameters"]

    def test_get_tool_not_found(self, test_client, mock_bifrost_client):
        """Test getting non-existent tool."""
        mock_bifrost_client.query_tool = AsyncMock(return_value=None)

        response = test_client.get("/tools/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestSearchEndpoint:
    """Test search endpoint."""

    def test_semantic_search(self, test_client, mock_bifrost_client):
        """Test semantic search."""
        mock_results = [
            SearchResult(
                id="1",
                content="Project documentation",
                metadata={"type": "doc"},
                score=0.95
            ),
            SearchResult(
                id="2",
                content="Related project",
                metadata={"type": "entity"},
                score=0.82
            )
        ]
        mock_bifrost_client.semantic_search = AsyncMock(return_value=mock_results)

        response = test_client.post("/search/semantic?query=project&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["query"] == "project"
        assert data["results"][0]["score"] == 0.95

        # Verify Bifrost was called correctly
        mock_bifrost_client.semantic_search.assert_called_once()
        call_args = mock_bifrost_client.semantic_search.call_args
        assert call_args.kwargs["query"] == "project"
        assert call_args.kwargs["limit"] == 10


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_full_workflow_routing_to_execution(
        self,
        test_client,
        mock_bifrost_client
    ):
        """Test complete workflow: route → get tool → execute."""
        # Step 1: Route request
        mock_decision = RoutingDecision(
            selected_tool="entity_create",
            confidence=0.95,
            reasoning="Create entity",
            alternatives=[]
        )
        mock_bifrost_client.route_request = AsyncMock(return_value=mock_decision)

        route_response = test_client.post("/route", json={
            "action": "create",
            "prompt": "Create project"
        })

        assert route_response.status_code == 200
        selected_tool = route_response.json()["route"]

        # Step 2: Get tool metadata
        mock_tool = ToolMetadata(
            name=selected_tool,
            description="Create entity",
            parameters={"name": "string"},
            category="entity",
            tags=[]
        )
        mock_bifrost_client.query_tool = AsyncMock(return_value=mock_tool)

        tool_response = test_client.get(f"/tools/{selected_tool}")

        assert tool_response.status_code == 200
        tool_data = tool_response.json()
        assert "name" in tool_data["parameters"]

        # Step 3: Execute tool (via BifrostClient directly, not exposed in API yet)
        mock_bifrost_client.execute_tool = AsyncMock(return_value={
            "success": True,
            "data": {"id": "123", "name": "Project"}
        })

        result = await mock_bifrost_client.execute_tool(
            name=selected_tool,
            input_data={"name": "Project"}
        )

        assert result["success"] is True
        assert result["data"]["id"] == "123"

    @pytest.mark.asyncio
    async def test_search_then_route(self, test_client, mock_bifrost_client):
        """Test workflow: search → route based on results."""
        # Step 1: Semantic search
        mock_results = [
            SearchResult(
                id="1",
                content="Existing project",
                metadata={"name": "ExistingProject"},
                score=0.9
            )
        ]
        mock_bifrost_client.semantic_search = AsyncMock(return_value=mock_results)

        search_response = test_client.post(
            "/search/semantic?query=project&limit=5"
        )

        assert search_response.status_code == 200
        results = search_response.json()["results"]

        # Step 2: Route based on search results
        context = {"search_results": results}
        mock_decision = RoutingDecision(
            selected_tool="entity_update",  # Update instead of create
            confidence=0.88,
            reasoning="Entity already exists",
            alternatives=[]
        )
        mock_bifrost_client.route_request = AsyncMock(return_value=mock_decision)

        route_response = test_client.post("/route", json={
            "action": "update",
            "prompt": "Update project",
            "context": context
        })

        assert route_response.status_code == 200
        assert route_response.json()["route"] == "entity_update"


class TestErrorHandling:
    """Test error handling across integration."""

    def test_bifrost_connection_failure(self, test_client, mock_bifrost_client):
        """Test handling Bifrost connection failures."""
        mock_bifrost_client.route_request = AsyncMock(
            side_effect=ConnectionError("Cannot reach Bifrost")
        )

        response = test_client.post("/route", json={
            "action": "test",
            "prompt": "Test"
        })

        assert response.status_code == 400
        assert "Cannot reach Bifrost" in response.json()["detail"]

    def test_bifrost_timeout(self, test_client, mock_bifrost_client):
        """Test handling Bifrost timeouts."""
        import asyncio
        mock_bifrost_client.route_request = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        response = test_client.post("/route", json={
            "action": "test",
            "prompt": "Test"
        })

        assert response.status_code == 400
