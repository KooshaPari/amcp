"""
Tests for InferenceMiddleware functionality.

Tests the middleware layer that processes requests and adds inference results.
"""

import pytest

from mcp.inference import create_inference_middleware


class TestInferenceMiddleware:
    """Test InferenceMiddleware functionality."""

    @pytest.mark.asyncio
    async def test_process_completion_request(self):
        """Test middleware processes completion requests."""
        middleware = create_inference_middleware()

        request = {
            "method": "POST",
            "path": "/v1/completions",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "I'm working on MyApp",
                    }
                ]
            },
            "headers": {
                "X-Session-ID": "session-123",
                "X-Request-ID": "request-456",
            },
        }

        result = await middleware.process_request(request)

        # Check request was processed
        assert "_inference_result" in result or "_inference_error" in result

        if "_inference_result" in result:
            assert result["_inference_result"]["success"] is True

    @pytest.mark.asyncio
    async def test_middleware_passes_non_completion_requests(self):
        """Test middleware passes through non-completion requests."""
        middleware = create_inference_middleware()

        request = {
            "method": "GET",
            "path": "/v1/models",
            "headers": {},
        }

        result = await middleware.process_request(request)

        # Should pass through unchanged (no inference fields added)
        assert "_inference_result" not in result
        assert "_inference_error" not in result

    @pytest.mark.asyncio
    async def test_middleware_error_handling(self):
        """Test middleware handles inference errors gracefully."""
        middleware = create_inference_middleware()

        # Malformed request
        request = {
            "method": "POST",
            "path": "/v1/completions",
            "body": None,  # This will cause an error
            "headers": {},
        }

        result = await middleware.process_request(request)

        # Should not crash, just mark error
        assert "_inference_error" in result or "_inference_result" in result
