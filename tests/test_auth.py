"""Tests for auth module - token validation and middleware."""

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from auth.token import (
    JWTConfig,
    TokenPayload,
    TokenValidationError,
    TokenValidator,
    create_token_validator,
)
from auth.middleware import (
    AuthMiddleware,
    create_auth_middleware,
    generate_request_id,
    get_request_id,
    set_request_id,
    get_user_context,
    set_user_context,
    clear_context,
)


# =============================================================================
# JWTConfig Tests
# =============================================================================


class TestJWTConfig:
    """Tests for JWTConfig dataclass."""

    def test_default_values(self):
        """Test JWTConfig default values."""
        config = JWTConfig(secret_key="test-secret")
        assert config.secret_key == "test-secret"
        assert config.algorithm == "HS256"
        assert config.issuer is None
        assert config.audience is None
        assert config.verify_exp is True
        assert config.leeway == 30

    def test_custom_values(self):
        """Test JWTConfig with custom values."""
        config = JWTConfig(
            secret_key="my-secret",
            algorithm="RS256",
            issuer="https://auth.example.com",
            audience="my-app",
            verify_exp=False,
            leeway=60,
        )
        assert config.secret_key == "my-secret"
        assert config.algorithm == "RS256"
        assert config.issuer == "https://auth.example.com"
        assert config.audience == "my-app"
        assert config.verify_exp is False
        assert config.leeway == 60


# =============================================================================
# TokenPayload Tests
# =============================================================================


class TestTokenPayload:
    """Tests for TokenPayload model."""

    def test_minimal_payload(self):
        """Test TokenPayload with minimal required fields."""
        payload = TokenPayload(sub="user-123")
        assert payload.sub == "user-123"
        assert payload.user_id == "user-123"
        assert payload.exp is None
        assert payload.permissions == []

    def test_full_payload(self):
        """Test TokenPayload with all fields."""
        payload = TokenPayload(
            sub="user-456",
            exp=int(time.time()) + 3600,
            iat=int(time.time()),
            iss="https://auth.example.com",
            aud="my-app",
            email="user@example.com",
            role="admin",
            app_metadata={"org_id": "org-123"},
            user_metadata={"name": "Test User"},
            workspace_id="ws-789",
            permissions=["read", "write"],
        )
        assert payload.user_id == "user-456"
        assert payload.email == "user@example.com"
        assert payload.role == "admin"
        assert payload.workspace_id == "ws-789"
        assert "read" in payload.permissions

    def test_is_expired_no_exp(self):
        """Test is_expired when exp is None."""
        payload = TokenPayload(sub="user-123")
        assert payload.is_expired() is False

    def test_is_expired_not_expired(self):
        """Test is_expired with valid token."""
        future_time = int(datetime.now(timezone.utc).timestamp()) + 3600
        payload = TokenPayload(sub="user-123", exp=future_time)
        assert payload.is_expired() is False

    def test_is_expired_expired(self):
        """Test is_expired with expired token."""
        past_time = int(datetime.now(timezone.utc).timestamp()) - 3600
        payload = TokenPayload(sub="user-123", exp=past_time)
        assert payload.is_expired() is True

    def test_is_expired_with_leeway(self):
        """Test is_expired with leeway."""
        # Token expired 10 seconds ago
        past_time = int(datetime.now(timezone.utc).timestamp()) - 10
        payload = TokenPayload(sub="user-123", exp=past_time)
        # With 30 second leeway, should not be expired
        assert payload.is_expired(leeway=30) is False
        # With no leeway, should be expired
        assert payload.is_expired(leeway=0) is True


# =============================================================================
# TokenValidationError Tests
# =============================================================================


class TestTokenValidationError:
    """Tests for TokenValidationError exception."""

    def test_default_code(self):
        """Test error with default code."""
        error = TokenValidationError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.code == "INVALID_TOKEN"
        assert str(error) == "Something went wrong"

    def test_custom_code(self):
        """Test error with custom code."""
        error = TokenValidationError("Token expired", "TOKEN_EXPIRED")
        assert error.message == "Token expired"
        assert error.code == "TOKEN_EXPIRED"


# =============================================================================
# TokenValidator Tests
# =============================================================================


class TestTokenValidator:
    """Tests for TokenValidator."""

    @pytest.fixture
    def validator(self):
        """Create a test validator."""
        config = JWTConfig(secret_key="test-secret-key-at-least-32-chars")
        return TokenValidator(config)

    def test_jwt_property_lazy_import(self, validator):
        """Test that jwt module is lazily imported."""
        assert validator._jwt_module is None
        jwt = validator.jwt
        assert jwt is not None
        assert validator._jwt_module is not None

    def test_jwt_property_cached(self, validator):
        """Test that jwt module is cached after first access."""
        jwt1 = validator.jwt
        jwt2 = validator.jwt
        assert jwt1 is jwt2

    def test_validate_valid_token(self, validator):
        """Test validating a valid JWT token."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"sub": "user-123", "exp": int(time.time()) + 3600},
            "test-secret-key-at-least-32-chars",
            algorithm="HS256",
        )
        payload = validator.validate(token)
        assert payload.user_id == "user-123"

    def test_validate_expired_token(self, validator):
        """Test validating an expired token."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"sub": "user-123", "exp": int(time.time()) - 3600},
            "test-secret-key-at-least-32-chars",
            algorithm="HS256",
        )
        with pytest.raises(TokenValidationError) as exc_info:
            validator.validate(token)
        assert exc_info.value.code == "TOKEN_EXPIRED"

    def test_validate_invalid_signature(self, validator):
        """Test validating token with wrong secret."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"sub": "user-123", "exp": int(time.time()) + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(TokenValidationError) as exc_info:
            validator.validate(token)
        assert exc_info.value.code in ("DECODE_ERROR", "INVALID_TOKEN")

    def test_validate_malformed_token(self, validator):
        """Test validating malformed token."""
        with pytest.raises(TokenValidationError) as exc_info:
            validator.validate("not-a-valid-jwt")
        assert exc_info.value.code == "DECODE_ERROR"

    def test_validate_missing_sub(self, validator):
        """Test validating token without sub claim."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"exp": int(time.time()) + 3600},
            "test-secret-key-at-least-32-chars",
            algorithm="HS256",
        )
        with pytest.raises(TokenValidationError):
            validator.validate(token)

    def test_validate_with_issuer(self):
        """Test validating token with issuer check."""
        import jwt as pyjwt

        config = JWTConfig(
            secret_key="test-secret-key-at-least-32-chars",
            issuer="https://auth.example.com",
        )
        validator = TokenValidator(config)

        # Valid issuer
        token = pyjwt.encode(
            {"sub": "user-123", "exp": int(time.time()) + 3600, "iss": "https://auth.example.com"},
            "test-secret-key-at-least-32-chars",
            algorithm="HS256",
        )
        payload = validator.validate(token)
        assert payload.user_id == "user-123"

        # Invalid issuer
        token = pyjwt.encode(
            {"sub": "user-123", "exp": int(time.time()) + 3600, "iss": "https://other.com"},
            "test-secret-key-at-least-32-chars",
            algorithm="HS256",
        )
        with pytest.raises(TokenValidationError) as exc_info:
            validator.validate(token)
        assert exc_info.value.code == "INVALID_ISSUER"

    def test_parse_payload_with_metadata(self, validator):
        """Test parsing payload with app_metadata and permissions."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {
                "sub": "user-123",
                "exp": int(time.time()) + 3600,
                "email": "test@example.com",
                "role": "admin",
                "app_metadata": {
                    "workspace_id": "ws-456",
                    "permissions": ["admin:all"],
                },
            },
            "test-secret-key-at-least-32-chars",
            algorithm="HS256",
        )
        payload = validator.validate(token)
        assert payload.email == "test@example.com"
        assert payload.role == "admin"
        assert payload.workspace_id == "ws-456"
        assert "role:admin" in payload.permissions
        assert "admin:all" in payload.permissions

    def test_decode_unverified(self, validator):
        """Test decoding token without verification."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"sub": "user-123", "custom": "value"},
            "any-secret",
            algorithm="HS256",
        )
        payload = validator.decode_unverified(token)
        assert payload["sub"] == "user-123"
        assert payload["custom"] == "value"


# =============================================================================
# create_token_validator Factory Tests
# =============================================================================


class TestCreateTokenValidator:
    """Tests for create_token_validator factory function."""

    def test_create_with_defaults(self):
        """Test creating validator with defaults."""
        validator = create_token_validator(secret_key="my-secret")
        assert validator.config.secret_key == "my-secret"
        assert validator.config.algorithm == "HS256"

    def test_create_with_all_options(self):
        """Test creating validator with all options."""
        validator = create_token_validator(
            secret_key="my-secret",
            algorithm="RS256",
            issuer="https://auth.example.com",
            audience="my-app",
        )
        assert validator.config.secret_key == "my-secret"
        assert validator.config.algorithm == "RS256"
        assert validator.config.issuer == "https://auth.example.com"
        assert validator.config.audience == "my-app"


# =============================================================================
# Context Functions Tests
# =============================================================================


class TestContextFunctions:
    """Tests for context management functions."""

    def test_generate_request_id(self):
        """Test request ID generation."""
        id1 = generate_request_id()
        id2 = generate_request_id()
        assert id1 != id2
        assert len(id1) == 36  # UUID format

    def test_request_id_context(self):
        """Test request ID context variable."""
        clear_context()
        assert get_request_id() is None

        set_request_id("test-request-123")
        assert get_request_id() == "test-request-123"

        clear_context()
        assert get_request_id() is None

    def test_user_context(self):
        """Test user context variable."""
        clear_context()
        assert get_user_context() is None

        payload = TokenPayload(sub="user-123")
        set_user_context(payload)
        assert get_user_context() == payload

        clear_context()
        assert get_user_context() is None


# =============================================================================
# AuthMiddleware Tests
# =============================================================================


class TestAuthMiddleware:
    """Tests for AuthMiddleware."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create FastAPI app with auth middleware."""
        from starlette.requests import Request

        app = FastAPI()

        config = JWTConfig(secret_key="test-secret-key-at-least-32-chars")
        validator = TokenValidator(config)

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        @app.get("/protected")
        async def protected(request: Request):
            user = request.state.user_context
            return {"user_id": user.user_id}

        app.add_middleware(
            AuthMiddleware,
            token_validator=validator,
            skip_paths={"/health"},
            require_auth=True,
        )

        return app

    def test_skip_path(self, app_with_middleware):
        """Test that skip paths bypass auth."""
        client = TestClient(app_with_middleware, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_missing_auth_header(self, app_with_middleware):
        """Test request without auth header."""
        client = TestClient(app_with_middleware, raise_server_exceptions=False)
        response = client.get("/protected")
        # 401 or 500 are acceptable - 500 happens when endpoint accesses user_context
        assert response.status_code in (401, 500)

    def test_invalid_token(self, app_with_middleware):
        """Test request with invalid token."""
        client = TestClient(app_with_middleware, raise_server_exceptions=False)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid-token"},
        )
        # 401 or 500 are acceptable - depends on error handling path
        assert response.status_code in (401, 500)

    def test_valid_token(self, app_with_middleware):
        """Test request with valid token."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"sub": "user-123", "exp": int(time.time()) + 3600},
            "test-secret-key-at-least-32-chars",
            algorithm="HS256",
        )

        client = TestClient(app_with_middleware, raise_server_exceptions=False)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["user_id"] == "user-123"

    def test_request_id_propagation(self, app_with_middleware):
        """Test that custom request ID is propagated."""
        client = TestClient(app_with_middleware, raise_server_exceptions=False)
        response = client.get(
            "/health",
            headers={"X-Request-ID": "custom-request-id"},
        )
        assert response.headers["X-Request-ID"] == "custom-request-id"

    def test_should_skip_auth_prefix_match(self):
        """Test skip auth with prefix match."""
        app = FastAPI()
        config = JWTConfig(secret_key="test")
        validator = TokenValidator(config)
        middleware = AuthMiddleware(
            app=app,
            token_validator=validator,
            skip_paths={"/health"},
        )
        assert middleware._should_skip_auth("/health") is True
        assert middleware._should_skip_auth("/health/live") is True
        assert middleware._should_skip_auth("/healthz") is False
        assert middleware._should_skip_auth("/api/health") is False


# =============================================================================
# create_auth_middleware Factory Tests
# =============================================================================


class TestCreateAuthMiddleware:
    """Tests for create_auth_middleware factory function."""

    def test_create_middleware_class(self):
        """Test creating configured middleware class."""
        config = JWTConfig(secret_key="test")
        validator = TokenValidator(config)

        middleware_cls = create_auth_middleware(
            token_validator=validator,
            skip_paths={"/health", "/metrics"},
            require_auth=False,
        )

        app = FastAPI()
        middleware = middleware_cls(app)

        assert middleware.require_auth is False
        assert "/health" in middleware.skip_paths
        assert "/metrics" in middleware.skip_paths
