"""
Tests for tool execution operations.

Tests tool execution, registration, and related functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestToolExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, bifrost_client_instance):
        """Test successful tool execution."""
        client = bifrost_client_instance
        mock_data = {
            "executeTool": {
                "success": True,
                "data": {"entity_id": "123", "name": "Project"},
                "error": None,
                "metadata": {
                    "duration": 150,
                    "model": "claude-sonnet-4",
                    "tokens": 42
                }
            }
        }

        with patch.object(client, "mutate", AsyncMock(return_value=mock_data)):
            result = await client.execute_tool(
                name="entity_create",
                input_data={"name": "Project", "description": "Test"}
            )

            assert result["success"] is True
            assert result["data"]["entity_id"] == "123"
            assert result["metadata"]["model"] == "claude-sonnet-4"

    @pytest.mark.asyncio
    async def test_execute_tool_failure(self, bifrost_client_instance):
        """Test tool execution failure."""
        client = bifrost_client_instance
        mock_data = {
            "executeTool": {
                "success": False,
                "data": None,
                "error": "Validation failed: name required",
                "metadata": None
            }
        }

        with patch.object(client, "mutate", AsyncMock(return_value=mock_data)):
            result = await client.execute_tool(
                name="entity_create",
                input_data={}
            )

            assert result["success"] is False
            assert "Validation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_register_tool(self, bifrost_client_instance):
        """Test registering new tool."""
        client = bifrost_client_instance
        mock_data = {
            "registerTool": {
                "success": True,
                "message": "Tool registered successfully"
            }
        }

        with patch.object(client, "mutate", AsyncMock(return_value=mock_data)):
            success = await client.register_tool(
                name="custom_tool",
                description="Custom tool",
                parameters={"input": "string"},
                category="custom",
                tags=["test"]
            )

            assert success is True
