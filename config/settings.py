"""
SmartCP configuration settings for Vibeproxy bundling.

Provides Pydantic-based configuration for:
- HTTP stateless transport settings
- User-scoped state management
- Supabase persistence
- Code execution sandbox
- Tool registration

Uses YAML config files with environment variable substitution.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class PersistenceSettings(BaseModel):
    """Supabase persistence configuration."""

    type: str = Field(default="supabase", description="Persistence backend type")
    url: str = Field(default="", description="Supabase project URL")
    anon_key: str = Field(default="", description="Supabase anonymous key")
    service_key: str = Field(default="", description="Supabase service role key")

    # Connection settings
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Query timeout")

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable in-memory cache")
    cache_ttl_seconds: int = Field(default=300, ge=0, le=3600, description="Cache TTL")
    cache_max_size: int = Field(default=1000, ge=0, le=100000, description="Max cache entries")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate persistence type."""
        valid_types = ["supabase", "sqlite", "memory"]
        if v not in valid_types:
            raise ValueError(f"Persistence type must be one of {valid_types}")
        return v


class SandboxSettings(BaseModel):
    """Code execution sandbox configuration."""

    enabled: bool = Field(default=True, description="Enable code execution")
    max_execution_time_seconds: int = Field(
        default=300, ge=1, le=3600, description="Max execution time"
    )
    max_memory_mb: int = Field(default=512, ge=64, le=4096, description="Max memory")
    max_output_size_bytes: int = Field(
        default=1048576, ge=1024, le=104857600, description="Max output size (1MB default)"
    )

    # Allowed languages
    allowed_languages: list[str] = Field(
        default=["python", "typescript", "bash", "go"],
        description="Languages allowed for code execution",
    )

    # Per-user isolation
    per_user_sandbox: bool = Field(
        default=True, description="Create separate sandbox per user"
    )
    sandbox_base_dir: str = Field(
        default="/tmp/smartcp/sandboxes", description="Base directory for sandboxes"
    )

    # Resource limits
    max_processes: int = Field(default=10, ge=1, le=100, description="Max concurrent processes")
    max_file_size_mb: int = Field(default=100, ge=1, le=1024, description="Max file size")

    @field_validator("allowed_languages")
    @classmethod
    def validate_languages(cls, v: list[str]) -> list[str]:
        """Validate allowed languages."""
        valid_languages = {"python", "typescript", "bash", "go", "rust", "javascript"}
        for lang in v:
            if lang not in valid_languages:
                raise ValueError(f"Unknown language: {lang}. Valid: {valid_languages}")
        return v


class ToolSettings(BaseModel):
    """MCP tool configuration."""

    code_execution: bool = Field(default=True, description="Enable code execution tool")
    semantic_memory: bool = Field(default=True, description="Enable semantic memory tool")
    learning_system: bool = Field(default=True, description="Enable learning system tool")
    file_operations: bool = Field(default=False, description="Enable file operations tool")

    # Tool-specific limits
    memory_max_entries_per_user: int = Field(
        default=10000, ge=100, le=1000000, description="Max memory entries per user"
    )
    learning_max_patterns_per_user: int = Field(
        default=1000, ge=10, le=100000, description="Max learning patterns per user"
    )


class AuthSettings(BaseModel):
    """Authentication configuration."""

    enabled: bool = Field(default=True, description="Enable authentication")
    require_bearer_token: bool = Field(default=True, description="Require bearer token")

    # Token validation
    validate_jwt: bool = Field(default=True, description="Validate JWT tokens")
    jwt_issuer: str = Field(default="", description="Expected JWT issuer")
    jwt_audience: str = Field(default="", description="Expected JWT audience")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(
        default=100, ge=1, le=10000, description="Requests per minute per user"
    )


class ServerSettings(BaseModel):
    """MCP server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # HTTP stateless mode (CRITICAL for Vibeproxy bundling)
    stateless: bool = Field(
        default=True, description="Run in HTTP stateless mode (required for Vibeproxy)"
    )
    transport: str = Field(default="http", description="Transport protocol")

    # Worker settings
    workers: int = Field(default=4, ge=1, le=32, description="Number of workers")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout")

    # Observability
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(default=True, description="Enable request tracing")
    log_level: str = Field(default="INFO", description="Log level")

    @field_validator("transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate transport type."""
        valid_transports = ["http", "stdio", "sse"]
        if v not in valid_transports:
            raise ValueError(f"Transport must be one of {valid_transports}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper


class BifrostSettings(BaseModel):
    """Bifrost orchestration endpoint configuration."""

    url: str = Field(
        default="http://localhost:8080/graphql", description="Bifrost GraphQL endpoint"
    )
    api_key: str = Field(default="", description="Bifrost API key (if required)")
    timeout_seconds: float = Field(
        default=30.0, ge=1.0, le=120.0, description="Bifrost request timeout"
    )


class SmartCPSettings(BaseModel):
    """Root SmartCP configuration."""

    # Feature toggle
    enabled: bool = Field(default=True, description="Enable SmartCP MCP server")

    # Sub-configurations
    server: ServerSettings = Field(default_factory=ServerSettings)
    persistence: PersistenceSettings = Field(default_factory=PersistenceSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    tools: ToolSettings = Field(default_factory=ToolSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    bifrost: BifrostSettings = Field(default_factory=BifrostSettings)

    # Metadata
    version: str = Field(default="2.0.0", description="SmartCP version")
    environment: str = Field(default="development", description="Environment name")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "staging", "production", "test"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v


class SmartCPConfig:
    """SmartCP configuration manager.

    Loads configuration from YAML files with environment variable substitution.
    Follows Vibeproxy config patterns for consistency.
    """

    def __init__(
        self,
        config_path: Path | None = None,
        secrets_path: Path | None = None,
    ):
        """Initialize configuration.

        Args:
            config_path: Path to config.yml file
            secrets_path: Path to secrets.yml file
        """
        self.project_root = Path.cwd()
        self.config_path = config_path or (self.project_root / "config" / "smartcp.yml")
        self.secrets_path = secrets_path or (self.project_root / "config" / "secrets.yml")

        self._settings: SmartCPSettings | None = None

    @property
    def settings(self) -> SmartCPSettings:
        """Get settings, loading if needed."""
        if self._settings is None:
            self._settings = self._load_settings()
        return self._settings

    def _load_settings(self) -> SmartCPSettings:
        """Load settings from YAML files."""
        config_data = self._load_yaml(self.config_path)
        secrets_data = self._load_yaml(self.secrets_path)

        # Merge config and secrets
        merged = self._merge_config(config_data, secrets_data)

        # Extract SmartCP section if present
        smartcp_data = merged.get("smartcp", merged)

        return SmartCPSettings.model_validate(smartcp_data)

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load YAML file with environment variable substitution."""
        import os

        if not path.exists():
            return {}

        try:
            with open(path) as f:
                content = f.read()

            # Substitute environment variables: ${VAR_NAME} or ${VAR_NAME:default}
            import re

            def replace_env_var(match: re.Match) -> str:
                var_expr = match.group(1)
                if ":" in var_expr:
                    var_name, default = var_expr.split(":", 1)
                    return os.environ.get(var_name, default)
                return os.environ.get(var_expr, match.group(0))

            content = re.sub(r"\$\{([^}]+)\}", replace_env_var, content)

            return yaml.safe_load(content) or {}

        except Exception as e:
            print(f"Error loading {path}: {e}")
            return {}

    def _merge_config(
        self, config: dict[str, Any], secrets: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge config and secrets."""

        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(config, secrets.get("secrets", secrets))

    def reload(self) -> SmartCPSettings:
        """Reload settings from files."""
        self._settings = self._load_settings()
        return self._settings

    def to_dict_safe(self) -> dict[str, Any]:
        """Get settings as dict without secrets."""
        return {
            "enabled": self.settings.enabled,
            "version": self.settings.version,
            "environment": self.settings.environment,
            "server": {
                "host": self.settings.server.host,
                "port": self.settings.server.port,
                "stateless": self.settings.server.stateless,
                "transport": self.settings.server.transport,
            },
            "persistence": {
                "type": self.settings.persistence.type,
                "cache_enabled": self.settings.persistence.cache_enabled,
                "has_url": bool(self.settings.persistence.url),
                "has_keys": bool(self.settings.persistence.service_key),
            },
            "sandbox": {
                "enabled": self.settings.sandbox.enabled,
                "allowed_languages": self.settings.sandbox.allowed_languages,
                "per_user_sandbox": self.settings.sandbox.per_user_sandbox,
            },
            "tools": {
                "code_execution": self.settings.tools.code_execution,
                "semantic_memory": self.settings.tools.semantic_memory,
                "learning_system": self.settings.tools.learning_system,
            },
            "auth": {
                "enabled": self.settings.auth.enabled,
                "require_bearer_token": self.settings.auth.require_bearer_token,
                "rate_limit_enabled": self.settings.auth.rate_limit_enabled,
            },
        }


# Global configuration instance
_config: SmartCPConfig | None = None


def get_config() -> SmartCPConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = SmartCPConfig()
    return _config


def get_settings() -> SmartCPSettings:
    """Get settings from global configuration."""
    return get_config().settings


def reload_config() -> SmartCPSettings:
    """Reload global configuration."""
    return get_config().reload()


def set_config(config: SmartCPConfig) -> None:
    """Set global configuration instance (for testing)."""
    global _config
    _config = config
