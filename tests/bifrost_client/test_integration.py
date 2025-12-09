"""
Tests for integration workflows.

Tests complete workflows combining multiple operations.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestIntegration:
    """Integration tests with mock Bifrost server."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, bifrost_client_instance):
        """Test complete workflow: query tools -> route -> execute."""
        client = bifrost_client_instance

        # Mock responses
        tools_data = {
            "tools": [
                {
                    "name": "entity_create",
                    "description": "Create entity",
                    "parameters": {"name": "string"},
                    "category": "entity",
                    "tags": []
                }
            ]
        }

        route_data = {
            "route": {
                "selectedTool": "entity_create",
                "confidence": 0.95,
                "reasoning": "User wants to create",
                "alternatives": []
            }
        }

        execute_data = {
            "executeTool": {
                "success": True,
                "data": {"id": "123"},
                "error": None,
                "metadata": None
            }
        }

        # Setup mocks
        query_mock = AsyncMock()
        query_mock.side_effect = [tools_data, route_data]
        mutate_mock = AsyncMock(return_value=execute_data)

        with patch.object(client, "query", query_mock), \
             patch.object(client, "mutate", mutate_mock):

            # 1. Query tools
            tools = await client.query_tools()
            assert len(tools) == 1

            # 2. Route request
            decision = await client.route_request("Create project")
            assert decision.selected_tool == "entity_create"

            # 3. Execute tool
            result = await client.execute_tool(
                name=decision.selected_tool,
                input_data={"name": "Project"}
            )
            assert result["success"] is True
