"""SmartCP configuration module.

Provides centralized configuration via settings.py and environment variables.
"""

from config.settings import SmartCPSettings, get_settings

__all__ = [
    "SmartCPSettings",
    "get_settings",
]
