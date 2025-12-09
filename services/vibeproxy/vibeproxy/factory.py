"""Factory functions for creating Vibeproxy instances and backend configurations."""

from .config import BackendConfig, BackendType, VibeproxyConfig


def create_vibeproxy(
    backends: list[BackendConfig] | None = None,
    user_id: str | None = None,
    workspace_id: str | None = None,
    **kwargs,
):
    """Create a vibeproxy instance with the given backends.

    Args:
        backends: List of backend configurations
        user_id: Optional user ID for context
        workspace_id: Optional workspace ID for context
        **kwargs: Additional config options

    Returns:
        Configured Vibeproxy instance
    """
    from .proxy import Vibeproxy

    config = VibeproxyConfig(
        backends=backends or [],
        user_id=user_id,
        workspace_id=workspace_id,
        **kwargs,
    )
    return Vibeproxy(config)


def create_smartcp_backend(
    url: str = "http://localhost:8000",
    name: str = "smartcp",
) -> BackendConfig:
    """Create a SmartCP backend configuration.

    Args:
        url: SmartCP server URL
        name: Backend name

    Returns:
        BackendConfig for SmartCP
    """
    return BackendConfig(
        name=name,
        backend_type=BackendType.SMARTCP,
        url=url,
        prefix="",  # SmartCP tools don't need prefix
        priority=10,  # High priority for local SmartCP
    )


def create_local_backend(
    command: str,
    args: list[str] | None = None,
    name: str = "local",
    env: dict[str, str] | None = None,
) -> BackendConfig:
    """Create a local subprocess backend configuration.

    Args:
        command: Command to run
        args: Command arguments
        name: Backend name
        env: Environment variables

    Returns:
        BackendConfig for local subprocess
    """
    return BackendConfig(
        name=name,
        backend_type=BackendType.LOCAL,
        command=command,
        args=args or [],
        env=env or {},
    )


def create_cloud_backend(
    url: str,
    name: str = "cloud",
) -> BackendConfig:
    """Create a cloud backend configuration.

    Args:
        url: Cloud service URL
        name: Backend name

    Returns:
        BackendConfig for cloud service
    """
    return BackendConfig(
        name=name,
        backend_type=BackendType.CLOUD,
        url=url,
    )
