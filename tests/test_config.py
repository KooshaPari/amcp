"""Tests for config/settings.py - SmartCP configuration."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from config.settings import (
    PersistenceSettings,
    SandboxSettings,
    ToolSettings,
    AuthSettings,
    ServerSettings,
    BifrostSettings,
    SmartCPSettings,
    SmartCPConfig,
    get_config,
    get_settings,
    reload_config,
    set_config,
)


# =============================================================================
# PersistenceSettings Tests
# =============================================================================


class TestPersistenceSettings:
    """Tests for PersistenceSettings model."""

    def test_default_values(self):
        """Test default persistence settings."""
        settings = PersistenceSettings()
        assert settings.type == "supabase"
        assert settings.url == ""
        assert settings.pool_size == 10
        assert settings.cache_enabled is True
        assert settings.cache_ttl_seconds == 300

    def test_validate_type_valid(self):
        """Test valid persistence types."""
        for ptype in ["supabase", "sqlite", "memory"]:
            settings = PersistenceSettings(type=ptype)
            assert settings.type == ptype

    def test_validate_type_invalid(self):
        """Test invalid persistence type."""
        with pytest.raises(ValueError) as exc_info:
            PersistenceSettings(type="invalid")
        assert "must be one of" in str(exc_info.value)

    def test_pool_size_bounds(self):
        """Test pool size validation."""
        settings = PersistenceSettings(pool_size=50)
        assert settings.pool_size == 50

        with pytest.raises(ValueError):
            PersistenceSettings(pool_size=0)

        with pytest.raises(ValueError):
            PersistenceSettings(pool_size=200)


# =============================================================================
# SandboxSettings Tests
# =============================================================================


class TestSandboxSettings:
    """Tests for SandboxSettings model."""

    def test_default_values(self):
        """Test default sandbox settings."""
        settings = SandboxSettings()
        assert settings.enabled is True
        assert settings.max_execution_time_seconds == 300
        assert settings.max_memory_mb == 512
        assert "python" in settings.allowed_languages

    def test_validate_languages_valid(self):
        """Test valid language list."""
        settings = SandboxSettings(allowed_languages=["python", "typescript"])
        assert settings.allowed_languages == ["python", "typescript"]

    def test_validate_languages_invalid(self):
        """Test invalid language in list."""
        with pytest.raises(ValueError) as exc_info:
            SandboxSettings(allowed_languages=["python", "invalid_lang"])
        assert "Unknown language" in str(exc_info.value)

    def test_resource_limits(self):
        """Test resource limit validation."""
        settings = SandboxSettings(
            max_execution_time_seconds=60,
            max_memory_mb=256,
            max_processes=5,
        )
        assert settings.max_execution_time_seconds == 60
        assert settings.max_memory_mb == 256
        assert settings.max_processes == 5


# =============================================================================
# ToolSettings Tests
# =============================================================================


class TestToolSettings:
    """Tests for ToolSettings model."""

    def test_default_values(self):
        """Test default tool settings."""
        settings = ToolSettings()
        assert settings.code_execution is True
        assert settings.semantic_memory is True
        assert settings.learning_system is True
        assert settings.file_operations is False

    def test_custom_limits(self):
        """Test custom limit values."""
        settings = ToolSettings(
            memory_max_entries_per_user=5000,
            learning_max_patterns_per_user=500,
        )
        assert settings.memory_max_entries_per_user == 5000
        assert settings.learning_max_patterns_per_user == 500


# =============================================================================
# AuthSettings Tests
# =============================================================================


class TestAuthSettings:
    """Tests for AuthSettings model."""

    def test_default_values(self):
        """Test default auth settings."""
        settings = AuthSettings()
        assert settings.enabled is True
        assert settings.require_bearer_token is True
        assert settings.validate_jwt is True
        assert settings.rate_limit_enabled is True

    def test_rate_limit_bounds(self):
        """Test rate limit validation."""
        settings = AuthSettings(rate_limit_requests_per_minute=500)
        assert settings.rate_limit_requests_per_minute == 500


# =============================================================================
# ServerSettings Tests
# =============================================================================


class TestServerSettings:
    """Tests for ServerSettings model."""

    def test_default_values(self):
        """Test default server settings."""
        settings = ServerSettings()
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.stateless is True
        assert settings.transport == "http"
        assert settings.log_level == "INFO"

    def test_validate_transport_valid(self):
        """Test valid transport types."""
        for transport in ["http", "stdio", "sse"]:
            settings = ServerSettings(transport=transport)
            assert settings.transport == transport

    def test_validate_transport_invalid(self):
        """Test invalid transport type."""
        with pytest.raises(ValueError) as exc_info:
            ServerSettings(transport="websocket")
        assert "must be one of" in str(exc_info.value)

    def test_validate_log_level_valid(self):
        """Test valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = ServerSettings(log_level=level)
            assert settings.log_level == level

    def test_validate_log_level_case_insensitive(self):
        """Test log level is case-insensitive."""
        settings = ServerSettings(log_level="debug")
        assert settings.log_level == "DEBUG"

    def test_validate_log_level_invalid(self):
        """Test invalid log level."""
        with pytest.raises(ValueError):
            ServerSettings(log_level="TRACE")

    def test_port_bounds(self):
        """Test port validation."""
        settings = ServerSettings(port=3000)
        assert settings.port == 3000

        with pytest.raises(ValueError):
            ServerSettings(port=0)

        with pytest.raises(ValueError):
            ServerSettings(port=70000)


# =============================================================================
# BifrostSettings Tests
# =============================================================================


class TestBifrostSettings:
    """Tests for BifrostSettings model."""

    def test_default_values(self):
        """Test default bifrost settings."""
        settings = BifrostSettings()
        assert settings.url == "http://localhost:8080/graphql"
        assert settings.api_key == ""
        assert settings.timeout_seconds == 30.0

    def test_custom_values(self):
        """Test custom bifrost settings."""
        settings = BifrostSettings(
            url="http://bifrost:9000/graphql",
            api_key="secret-key",
            timeout_seconds=60.0,
        )
        assert settings.url == "http://bifrost:9000/graphql"
        assert settings.api_key == "secret-key"
        assert settings.timeout_seconds == 60.0


# =============================================================================
# SmartCPSettings Tests
# =============================================================================


class TestSmartCPSettings:
    """Tests for SmartCPSettings model."""

    def test_default_values(self):
        """Test default root settings."""
        settings = SmartCPSettings()
        assert settings.enabled is True
        assert settings.version == "2.0.0"
        assert settings.environment == "development"
        assert isinstance(settings.server, ServerSettings)
        assert isinstance(settings.auth, AuthSettings)

    def test_validate_environment_valid(self):
        """Test valid environments."""
        for env in ["development", "staging", "production", "test"]:
            settings = SmartCPSettings(environment=env)
            assert settings.environment == env

    def test_validate_environment_invalid(self):
        """Test invalid environment."""
        with pytest.raises(ValueError) as exc_info:
            SmartCPSettings(environment="invalid")
        assert "must be one of" in str(exc_info.value)

    def test_nested_settings(self):
        """Test nested settings initialization."""
        settings = SmartCPSettings(
            server=ServerSettings(port=3000),
            auth=AuthSettings(enabled=False),
        )
        assert settings.server.port == 3000
        assert settings.auth.enabled is False


# =============================================================================
# SmartCPConfig Tests
# =============================================================================


class TestSmartCPConfig:
    """Tests for SmartCPConfig manager."""

    def test_init_default_paths(self):
        """Test config initialization with default paths."""
        config = SmartCPConfig()
        assert config.config_path.name == "smartcp.yml"
        assert config.secrets_path.name == "secrets.yml"

    def test_init_custom_paths(self):
        """Test config initialization with custom paths."""
        config = SmartCPConfig(
            config_path=Path("/custom/config.yml"),
            secrets_path=Path("/custom/secrets.yml"),
        )
        assert config.config_path == Path("/custom/config.yml")
        assert config.secrets_path == Path("/custom/secrets.yml")

    def test_settings_lazy_load(self):
        """Test settings are lazily loaded."""
        config = SmartCPConfig()
        assert config._settings is None

        settings = config.settings
        assert settings is not None
        assert config._settings is settings

    def test_load_yaml_nonexistent(self):
        """Test loading nonexistent YAML file returns empty dict."""
        config = SmartCPConfig(
            config_path=Path("/nonexistent/config.yml"),
        )
        result = config._load_yaml(Path("/nonexistent/file.yml"))
        assert result == {}

    def test_load_yaml_with_env_substitution(self):
        """Test YAML loading with environment variable substitution."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("url: ${TEST_URL:http://default}")
            f.flush()
            config = SmartCPConfig()

            # Test default value
            with patch.dict(os.environ, {}, clear=True):
                result = config._load_yaml(Path(f.name))
                assert result["url"] == "http://default"

            # Test env override
            with patch.dict(os.environ, {"TEST_URL": "http://custom"}):
                result = config._load_yaml(Path(f.name))
                assert result["url"] == "http://custom"

            os.unlink(f.name)

    def test_merge_config(self):
        """Test deep merge of config and secrets."""
        config = SmartCPConfig()

        base = {
            "server": {"host": "0.0.0.0", "port": 8000},
            "auth": {"enabled": True},
        }
        secrets = {
            "secrets": {
                "server": {"port": 9000},
                "auth": {"jwt_secret": "secret-key"},
            }
        }

        result = config._merge_config(base, secrets)
        assert result["server"]["host"] == "0.0.0.0"
        assert result["server"]["port"] == 9000
        assert result["auth"]["enabled"] is True
        assert result["auth"]["jwt_secret"] == "secret-key"

    def test_reload(self):
        """Test config reload."""
        config = SmartCPConfig()
        settings1 = config.settings
        settings2 = config.reload()

        assert settings1 is not settings2

    def test_to_dict_safe(self):
        """Test safe dict export without secrets."""
        config = SmartCPConfig()
        safe_dict = config.to_dict_safe()

        assert "enabled" in safe_dict
        assert "version" in safe_dict
        assert "server" in safe_dict
        assert "persistence" in safe_dict

        # Should not contain actual secrets
        assert "service_key" not in str(safe_dict)
        assert safe_dict["persistence"]["has_keys"] is False


# =============================================================================
# Module-Level Functions Tests
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level configuration functions."""

    def test_get_config(self):
        """Test get_config returns singleton."""
        # Reset global
        import config.settings as settings_module
        settings_module._config = None

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_settings(self):
        """Test get_settings returns settings."""
        settings = get_settings()
        assert isinstance(settings, SmartCPSettings)

    def test_reload_config(self):
        """Test reload_config refreshes settings."""
        settings1 = get_settings()
        settings2 = reload_config()
        # Should be different instances
        assert settings1 is not settings2

    def test_set_config(self):
        """Test set_config for testing."""
        import config.settings as settings_module

        original = settings_module._config
        custom = SmartCPConfig()

        set_config(custom)
        assert settings_module._config is custom

        # Restore
        settings_module._config = original
