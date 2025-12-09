"""SmartCP Infrastructure Package.

Runtime expectation: all resource access is delegated via Bifrost.
The Supabase adapter remains for legacy/back-compat only and should not be
used in new code paths. Prefer adapters in smartcp.infrastructure.state (Bifrost-backed).
"""

from smartcp.infrastructure.supabase_adapter import (
    SupabaseAdapter,
    SupabaseConfig,
    create_supabase_adapter,
)
from smartcp.infrastructure.state import (
    StateAdapter,
    BifrostStateAdapter,
    create_state_adapter,
)

__all__ = [
    # Supabase (legacy, do not use in new code)
    "SupabaseAdapter",
    "SupabaseConfig",
    "create_supabase_adapter",
    # State management (Bifrost-backed)
    "StateAdapter",
    "BifrostStateAdapter",
    "create_state_adapter",
]
