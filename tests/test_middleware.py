"""Tests for middleware/resource_access_enforcement.py."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from middleware.resource_access_enforcement import (
    ResourceAccessEnforcementMiddleware,
    create_resource_enforcement_middleware,
)


# =============================================================================
# ResourceAccessEnforcementMiddleware Tests
# =============================================================================


class TestResourceAccessEnforcementMiddleware:
    """Tests for ResourceAccessEnforcementMiddleware."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create FastAPI app with enforcement middleware."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=False,
            log_violations=True,
        )

        return app

    @pytest.fixture
    def app_with_strict_middleware(self):
        """Create FastAPI app with strict enforcement."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=True,
            log_violations=True,
        )

        return app

    def test_init_defaults(self):
        """Test middleware initialization with defaults."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app, enforce=False)

        assert middleware.enforce is False
        assert middleware.log_violations is True
        assert middleware._forbidden_modules_loaded == set()

    def test_init_custom(self):
        """Test middleware initialization with custom values."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(
            app,
            enforce=True,
            log_violations=False,
        )

        assert middleware.enforce is True
        assert middleware.log_violations is False

    def test_forbidden_modules(self):
        """Test FORBIDDEN_MODULES constant."""
        assert "supabase" in ResourceAccessEnforcementMiddleware.FORBIDDEN_MODULES
        assert "neo4j" in ResourceAccessEnforcementMiddleware.FORBIDDEN_MODULES
        assert "redis" in ResourceAccessEnforcementMiddleware.FORBIDDEN_MODULES
        assert "qdrant_client" in ResourceAccessEnforcementMiddleware.FORBIDDEN_MODULES

    def test_request_passes_no_violations(self, app_with_middleware):
        """Test that requests pass when no violations."""
        client = TestClient(app_with_middleware, raise_server_exceptions=False)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_audit_mode_logs_but_allows(self, app_with_middleware):
        """Test audit mode logs but allows requests."""
        client = TestClient(app_with_middleware, raise_server_exceptions=False)

        # Mock a forbidden module being loaded from smartcp context
        mock_module = MagicMock()
        mock_module.__file__ = "/path/to/smartcp/module.py"

        with patch.dict(sys.modules, {"supabase": mock_module}):
            response = client.get("/test")
            # Should still succeed in audit mode
            assert response.status_code == 200

    def test_check_forbidden_imports_none_loaded(self):
        """Test check when no forbidden modules loaded."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        # Ensure none of the forbidden modules are in sys.modules
        with patch.dict(sys.modules, {}, clear=False):
            for mod in middleware.FORBIDDEN_MODULES:
                if mod in sys.modules:
                    del sys.modules[mod]

            violations = middleware._check_forbidden_imports()
            assert violations == set()

    def test_check_forbidden_imports_with_violation(self):
        """Test check when forbidden module loaded from smartcp."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        mock_module = MagicMock()
        mock_module.__file__ = "/path/to/smartcp/services/db.py"

        with patch.dict(sys.modules, {"supabase": mock_module}):
            violations = middleware._check_forbidden_imports()
            assert "supabase" in violations

    def test_check_forbidden_imports_not_smartcp_context(self):
        """Test that imports from bifrost-extensions are allowed."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        mock_module = MagicMock()
        mock_module.__file__ = "/path/to/bifrost-extensions/db.py"

        with patch.dict(sys.modules, {"supabase": mock_module}):
            violations = middleware._check_forbidden_imports()
            # Should not be a violation since it's in bifrost-extensions
            assert "supabase" not in violations

    def test_is_smartcp_context_true(self):
        """Test _is_smartcp_context returns True for smartcp paths."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        mock_module = MagicMock()
        mock_module.__file__ = "/app/smartcp/services/db.py"

        assert middleware._is_smartcp_context(mock_module) is True

    def test_is_smartcp_context_false_bifrost(self):
        """Test _is_smartcp_context returns False for bifrost-extensions."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        mock_module = MagicMock()
        mock_module.__file__ = "/app/bifrost-extensions/plugins/db.py"

        assert middleware._is_smartcp_context(mock_module) is False

    def test_is_smartcp_context_no_file(self):
        """Test _is_smartcp_context handles missing __file__."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        mock_module = MagicMock()
        mock_module.__file__ = None

        assert middleware._is_smartcp_context(mock_module) is False

    def test_is_smartcp_context_exception(self):
        """Test _is_smartcp_context handles exceptions."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        mock_module = MagicMock()
        type(mock_module).__file__ = property(lambda s: (_ for _ in ()).throw(Exception()))

        # Should return False on exception
        assert middleware._is_smartcp_context(mock_module) is False

    def test_log_violation_enabled(self):
        """Test _log_violation when logging enabled."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app, log_violations=True)

        mock_request = MagicMock()
        mock_request.url.path = "/test"
        mock_request.method = "GET"

        with patch("middleware.resource_access_enforcement.logger") as mock_logger:
            middleware._log_violation(mock_request, {"supabase"})
            mock_logger.warning.assert_called_once()

    def test_log_violation_disabled(self):
        """Test _log_violation when logging disabled."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app, log_violations=False)

        mock_request = MagicMock()

        with patch("middleware.resource_access_enforcement.logger") as mock_logger:
            middleware._log_violation(mock_request, {"supabase"})
            mock_logger.warning.assert_not_called()

    def test_validate_bifrost_client_usage_true(self):
        """Test validate_bifrost_client_usage returns True."""

        def func_with_bifrost():
            bifrost_client.query()

        result = ResourceAccessEnforcementMiddleware.validate_bifrost_client_usage(
            func_with_bifrost
        )
        assert result is True

    def test_validate_bifrost_client_usage_false(self):
        """Test validate_bifrost_client_usage returns False."""

        def func_without_bifrost():
            supabase.query()

        result = ResourceAccessEnforcementMiddleware.validate_bifrost_client_usage(
            func_without_bifrost
        )
        assert result is False

    def test_validate_bifrost_client_usage_exception(self):
        """Test validate_bifrost_client_usage handles exception."""
        # Built-in functions don't have source
        result = ResourceAccessEnforcementMiddleware.validate_bifrost_client_usage(len)
        assert result is False

    def test_violations_only_logged_once(self):
        """Test that same violation is only logged once."""
        app = FastAPI()
        middleware = ResourceAccessEnforcementMiddleware(app)

        mock_module = MagicMock()
        mock_module.__file__ = "/path/to/smartcp/db.py"

        with patch.dict(sys.modules, {"supabase": mock_module}):
            # First check
            violations1 = middleware._check_forbidden_imports()
            assert "supabase" in violations1

            # Second check - should not report again
            violations2 = middleware._check_forbidden_imports()
            assert "supabase" not in violations2


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestCreateResourceEnforcementMiddleware:
    """Tests for create_resource_enforcement_middleware factory."""

    def test_create_factory_default(self):
        """Test creating factory with defaults."""
        factory = create_resource_enforcement_middleware()

        app = FastAPI()
        middleware = factory(app)

        assert isinstance(middleware, ResourceAccessEnforcementMiddleware)
        assert middleware.enforce is False
        assert middleware.log_violations is True

    def test_create_factory_strict(self):
        """Test creating factory with strict mode."""
        factory = create_resource_enforcement_middleware(
            enforce=True,
            log_violations=False,
        )

        app = FastAPI()
        middleware = factory(app)

        assert middleware.enforce is True
        assert middleware.log_violations is False

    def test_factory_returns_callable(self):
        """Test that factory returns a callable."""
        factory = create_resource_enforcement_middleware()
        assert callable(factory)
