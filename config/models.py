"""AI model names and configurations.

Consolidates hardcoded model identifiers, versions, and provider-specific
model names from services and extensions.
"""

from dataclasses import dataclass
from enum import Enum


class ModelProvider(str, Enum):
    """AI model provider types."""

    CLAUDE = "claude"
    GEMINI = "gemini"
    GPT = "gpt"
    CUSTOM = "custom"


@dataclass
class ClaudeModels:
    """Anthropic Claude model identifiers."""

    # Latest Claude versions
    OPUS_LATEST: str = "claude-opus-4.5-20251101"
    SONNET_LATEST: str = "claude-sonnet-4-20250514"
    HAIKU_LATEST: str = "claude-haiku-4-5-20251001"

    # Alternative naming
    OPUS: str = "claude-opus"
    SONNET: str = "claude-sonnet"
    HAIKU: str = "claude-haiku"

    # Default model for general use
    DEFAULT: str = "claude-opus-4.5-20251101"


@dataclass
class GeminiModels:
    """Google Gemini model identifiers."""

    # Latest Gemini versions
    PRO: str = "gemini-2.5-pro"
    FLASH: str = "gemini-2.5-flash"
    FLASH_LITE: str = "gemini-2.5-flash-lite"

    # Default model
    DEFAULT: str = "gemini-2.5-pro"


@dataclass
class OpenAIModels:
    """OpenAI GPT model identifiers."""

    # Latest GPT versions
    GPT4_TURBO: str = "gpt-4-turbo"
    GPT4_OMNI: str = "gpt-4o"
    GPT4_OMNI_MINI: str = "gpt-4o-mini"

    # Default model
    DEFAULT: str = "gpt-4o"


@dataclass
class EmbeddingModels:
    """Embedding model identifiers across providers."""

    # OpenAI embeddings
    OPENAI_3_SMALL: str = "text-embedding-3-small"
    OPENAI_3_LARGE: str = "text-embedding-3-large"

    # Voyage AI embeddings
    VOYAGE_3: str = "voyage-3"
    VOYAGE_3_LITE: str = "voyage-3-lite"

    # Default embedding model
    DEFAULT: str = "text-embedding-3-small"


@dataclass
class ModelContextWindows:
    """Context window sizes for models (in tokens)."""

    # Claude context windows
    CLAUDE_OPUS: int = 200_000
    CLAUDE_SONNET: int = 200_000
    CLAUDE_HAIKU: int = 200_000

    # Gemini context windows
    GEMINI_PRO: int = 1_000_000
    GEMINI_FLASH: int = 1_000_000

    # GPT context windows
    GPT4_TURBO: int = 128_000
    GPT4_OMNI: int = 128_000

    # Default safe window (conservative)
    DEFAULT: int = 100_000


@dataclass
class ModelCapabilities:
    """Model-specific capability flags."""

    # Code understanding
    SUPPORTS_CODE: bool = True

    # Vision capabilities
    SUPPORTS_VISION: bool = True

    # Function calling
    SUPPORTS_FUNCTIONS: bool = True

    # Streaming
    SUPPORTS_STREAMING: bool = True

    # Long context
    SUPPORTS_LONG_CONTEXT: bool = True


# Convenience instances
claude = ClaudeModels()
gemini = GeminiModels()
openai = OpenAIModels()
embeddings = EmbeddingModels()
context_windows = ModelContextWindows()
capabilities = ModelCapabilities()


def get_model_provider(model_name: str) -> ModelProvider:
    """Determine model provider from model name."""
    model_lower = model_name.lower()

    if "claude" in model_lower:
        return ModelProvider.CLAUDE
    elif "gemini" in model_lower:
        return ModelProvider.GEMINI
    elif "gpt" in model_lower or "openai" in model_lower:
        return ModelProvider.GPT

    return ModelProvider.CUSTOM


def get_context_window(model_name: str) -> int:
    """Get context window for a specific model."""
    model_lower = model_name.lower()

    # Claude models
    if "opus" in model_lower:
        return context_windows.CLAUDE_OPUS
    if "sonnet" in model_lower:
        return context_windows.CLAUDE_SONNET
    if "haiku" in model_lower:
        return context_windows.CLAUDE_HAIKU

    # Gemini models
    if "gemini" in model_lower:
        if "flash" in model_lower:
            return context_windows.GEMINI_FLASH
        return context_windows.GEMINI_PRO

    # GPT models
    if "gpt" in model_lower:
        if "turbo" in model_lower:
            return context_windows.GPT4_TURBO
        if "4o" in model_lower or "omni" in model_lower:
            return context_windows.GPT4_OMNI

    return context_windows.DEFAULT
