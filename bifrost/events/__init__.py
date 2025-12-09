"""SmartCP Event Emission for Bifrost/NATS Integration.

Provides event publishing for SmartCP operations to enable:
- Tool execution event tracking
- Memory operation events
- State change events
- Performance metrics
"""

from smartcp.bifrost.events.core import (
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

__all__ = [
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
]
