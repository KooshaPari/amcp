"""SmartCP Bifrost Integration.

Provides integration with Bifrost gateway for:
- Tool registration and discovery
- Event emission to NATS
- Control plane integration
"""

from smartcp.bifrost.plugin import (
    SmartCPBifrostPlugin,
    PluginConfig,
    RegistrationResult,
    ToolSchema,
    ParameterSchema,
    create_bifrost_plugin,
)
from smartcp.bifrost.registry import (
    ToolRegistry,
    SMARTCP_TOOLS,
)
from smartcp.bifrost.events import (
    SmartCPEventPublisher,
    SmartCPEventType,
    SmartCPEvent,
    ToolExecutionEvent,
    MemoryEvent,
    CodeExecutionEvent,
    EventPublisherConfig,
    get_event_publisher,
    init_event_publisher,
    close_event_publisher,
)
from smartcp.bifrost.control_plane import (
    SmartCPControlPlane,
    ControlPlaneConfig,
    ServerStatus,
    ServerCapability,
    ServerHealth,
    CapabilityType,
    ProgressUpdate,
    get_control_plane,
    init_control_plane,
    close_control_plane,
)

__all__ = [
    # Plugin
    "SmartCPBifrostPlugin",
    "PluginConfig",
    "RegistrationResult",
    "ToolSchema",
    "ParameterSchema",
    "create_bifrost_plugin",
    # Registry
    "ToolRegistry",
    "SMARTCP_TOOLS",
    # Events
    "SmartCPEventPublisher",
    "SmartCPEventType",
    "SmartCPEvent",
    "ToolExecutionEvent",
    "MemoryEvent",
    "CodeExecutionEvent",
    "EventPublisherConfig",
    "get_event_publisher",
    "init_event_publisher",
    "close_event_publisher",
    # Control Plane
    "SmartCPControlPlane",
    "ControlPlaneConfig",
    "ServerStatus",
    "ServerCapability",
    "ServerHealth",
    "CapabilityType",
    "ProgressUpdate",
    "get_control_plane",
    "init_control_plane",
    "close_control_plane",
]
