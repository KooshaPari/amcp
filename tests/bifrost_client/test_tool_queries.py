"""
Tests for tool-related query operations.

Tests querying tools metadata and tool discovery functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch

from infrastructure.bifrost.queries import ToolMetadata


class TestToolQueries:
    """Test tool-related queries."""

    @pytest.mark.asyncio
    async def test_query_tools(self, bifrost_client_instance):
        """Test querying available tools."""
        client = bifrost_client_instance
        mock_data = {
            "tools": [
                {
                    "name": "entity_create",
                    "description": "Create entity",
                    "parameters": {"name": "string"},
                    "category": "entity",
                    "tags": ["create", "entity"]
                },
                {
                    "name": "entity_search",
                    "description": "Search entities",
                    "parameters": {"query": "string"},
                    "category": "entity",
                    "tags": ["search", "entity"]
                }
            ]
        }

        with patch.object(client, "query", AsyncMock(return_value=mock_data)):
            tools = await client.query_tools(
                filters={"category": "entity"},
                limit=10
            )

            assert len(tools) == 2
            assert isinstance(tools[0], ToolMetadata)
            assert tools[0].name == "entity_create"
            assert tools[0].category == "entity"
            assert "create" in tools[0].tags

    @pytest.mark.asyncio
    async def test_query_tool(self, bifrost_client_instance):
        """Test querying specific tool."""
        client = bifrost_client_instance
        mock_data = {
            "tool": {
                "name": "entity_create",
                "description": "Create entity",
                "parameters": {"name": "string"},
                "category": "entity",
                "tags": ["create"]
            }
        }

        with patch.object(client, "query", AsyncMock(return_value=mock_data)):
            tool = await client.query_tool("entity_create")

            assert tool is not None
            assert isinstance(tool, ToolMetadata)
            assert tool.name == "entity_create"
            assert tool.description == "Create entity"

    @pytest.mark.asyncio
    async def test_query_tool_not_found(self, bifrost_client_instance):
        """Test querying non-existent tool."""
        client = bifrost_client_instance
        mock_data = {"tool": None}

        with patch.object(client, "query", AsyncMock(return_value=mock_data)):
            tool = await client.query_tool("nonexistent")
            assert tool is None
