"""SmartCP Bifrost Integration.

Tool registration, event emission, and control plane integration.
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
