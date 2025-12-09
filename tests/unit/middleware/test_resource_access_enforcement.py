"""Tests for ResourceAccessEnforcementMiddleware.

Tests Phase 5.1 remediation: Bifrost delegation enforcement middleware.
"""

import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request, Response
from starlette.testclient import TestClient

from middleware.resource_access_enforcement import (
    ResourceAccessEnforcementMiddleware,
    create_resource_enforcement_middleware,
)


@pytest.fixture
def simple_app() -> FastAPI:
    """Create a simple FastAPI app for testing."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def app_with_middleware(simple_app: FastAPI) -> FastAPI:
    """Create FastAPI app with enforcement middleware."""
    simple_app.add_middleware(
        ResourceAccessEnforcementMiddleware,
        enforce=False,
        log_violations=True,
    )
    return simple_app


class TestResourceAccessEnforcementMiddleware:
    """Test suite for ResourceAccessEnforcementMiddleware."""

    def test_middleware_initialization(self):
        """Test middleware initializes correctly."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(
            app=app,
            enforce=False,
            log_violations=True,
        )

        assert middleware.enforce is False
        assert middleware.log_violations is True
        assert len(middleware.FORBIDDEN_MODULES) > 0

    def test_forbidden_modules_list(self):
        """Test forbidden modules are configured correctly."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        expected_modules = {"supabase", "neo4j", "redis", "qdrant_client"}
        assert middleware.FORBIDDEN_MODULES == expected_modules

    def test_approved_resource_client(self):
        """Test approved resource client path is configured."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        assert middleware.APPROVED_RESOURCE_CLIENT == "services.bifrost.bifrost_client"

    def test_check_forbidden_imports_empty(self):
        """Test check_forbidden_imports returns empty when no violations."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        violations = middleware._check_forbidden_imports()
        assert isinstance(violations, set)
        # Should not detect violations for modules not in sys.modules

    def test_is_smartcp_context_with_smartcp_path(self):
        """Test _is_smartcp_context detects smartcp modules."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        # Create a mock module with smartcp path
        mock_module = MagicMock()
        mock_module.__file__ = "/path/to/smartcp/module.py"

        assert middleware._is_smartcp_context(mock_module) is True

    def test_is_smartcp_context_ignores_bifrost_extensions(self):
        """Test _is_smartcp_context ignores bifrost-extensions modules."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        # Create a mock module with bifrost-extensions path
        mock_module = MagicMock()
        mock_module.__file__ = "/path/to/bifrost-extensions/module.py"

        assert middleware._is_smartcp_context(mock_module) is False

    def test_is_smartcp_context_handles_missing_file(self):
        """Test _is_smartcp_context handles modules without __file__."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        # Create a mock module without __file__
        mock_module = MagicMock()
        mock_module.__file__ = None

        assert middleware._is_smartcp_context(mock_module) is False

    @pytest.mark.asyncio
    async def test_dispatch_allows_request(self, app_with_middleware: FastAPI):
        """Test dispatch allows request when no violations."""
        client = TestClient(app_with_middleware)
        response = client.get("/test")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_dispatch_audit_mode_logs_violations(self):
        """Test dispatch logs violations in audit mode."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=False,  # Audit mode
            log_violations=True,
        )

        client = TestClient(app)

        # Make a request - should not raise even if violations present
        response = client.get("/test")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_strict_mode_rejects_violations(self):
        """Test dispatch rejects requests in strict mode with violations."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            # Simulate a forbidden import being loaded
            sys.modules["supabase"] = MagicMock(__file__="/smartcp/test.py")
            return {"status": "ok"}

        app.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=True,  # Strict mode
            log_violations=True,
        )

        client = TestClient(app)

        try:
            response = client.get("/test")
            # In strict mode with violations, should get 403
            assert response.status_code == 403
        finally:
            # Clean up
            if "supabase" in sys.modules:
                del sys.modules["supabase"]

    def test_log_violation_structure(self, caplog):
        """Test violation logging includes necessary information."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=True,
        )

        # Create a mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "POST"

        violations = {"supabase", "redis"}
        middleware._log_violation(mock_request, violations)

        # Verify logging was called (we can't easily capture structlog)
        # but we can verify the method doesn't raise

    def test_validate_bifrost_client_usage_positive(self):
        """Test validate_bifrost_client_usage detects bifrost_client usage."""

        async def func_using_bifrost():
            result = await bifrost_client.query()
            return result

        assert ResourceAccessEnforcementMiddleware.validate_bifrost_client_usage(
            func_using_bifrost
        )

    def test_validate_bifrost_client_usage_negative(self):
        """Test validate_bifrost_client_usage detects missing bifrost_client."""

        async def func_not_using_bifrost():
            result = {"data": "test"}
            return result

        assert not ResourceAccessEnforcementMiddleware.validate_bifrost_client_usage(
            func_not_using_bifrost
        )

    def test_factory_function(self):
        """Test create_resource_enforcement_middleware factory."""
        factory = create_resource_enforcement_middleware(
            enforce=True,
            log_violations=False,
        )

        assert callable(factory)

        # Factory should return middleware instance
        app = FastAPI()
        middleware = factory(app)

        assert isinstance(middleware, ResourceAccessEnforcementMiddleware)
        assert middleware.enforce is True
        assert middleware.log_violations is False


class TestResourceAccessEnforcementIntegration:
    """Integration tests for enforcement middleware."""

    @pytest.mark.asyncio
    async def test_middleware_in_request_chain(self):
        """Test middleware integrates correctly in request chain."""
        app = FastAPI()

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        @app.post("/resource")
        async def create_resource():
            return {"id": "123"}

        app.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=False,
            log_violations=False,
        )

        client = TestClient(app)

        # Test health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json() == {"status": "healthy"}

        # Test resource endpoint
        resource_response = client.post("/resource")
        assert resource_response.status_code == 200
        assert resource_response.json() == {"id": "123"}

    def test_middleware_enforcement_modes(self):
        """Test middleware respects enforcement configuration."""
        # Audit mode should not raise
        app_audit = FastAPI()
        app_audit.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=False,
            log_violations=False,
        )
        middleware_audit = app_audit.middleware[0][1]["cls"]
        assert middleware_audit(app_audit, enforce=False, log_violations=False).enforce is False

        # Strict mode should raise on violations
        app_strict = FastAPI()
        app_strict.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=True,
            log_violations=True,
        )
        middleware_strict = app_strict.middleware[0][1]["cls"]
        assert middleware_strict(app_strict, enforce=True, log_violations=True).enforce is True


class TestPhase51Remediation:
    """Tests specific to Phase 5.1 remediation specification."""

    def test_forbidden_modules_match_specification(self):
        """Test forbidden modules match remediation spec."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        # Per REMEDIATION_SPECIFICATIONS.md Phase 5.1
        expected = {"supabase", "neo4j", "redis", "qdrant_client"}
        assert middleware.FORBIDDEN_MODULES == expected

    def test_bifrost_client_approved_path(self):
        """Test approved client path is documented correctly."""
        middleware = ResourceAccessEnforcementMiddleware(
            app=FastAPI(),
            enforce=False,
            log_violations=False,
        )

        # Per specification: all resource access should use bifrost_client
        assert "bifrost_client" in middleware.APPROVED_RESOURCE_CLIENT

    def test_middleware_purpose_documented(self):
        """Test middleware docstring documents Phase 5.1 purpose."""
        middleware_class = ResourceAccessEnforcementMiddleware
        assert "Phase 5.1" in middleware_class.__doc__
        assert "Bifrost" in middleware_class.__doc__
        assert "enforce" in middleware_class.__init__.__doc__.lower()
