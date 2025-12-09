"""Tests for Voyage AI configuration."""

import pytest
from services.embeddings import VoyageConfig, VoyageModel


class TestVoyageConfig:
    """Test Voyage AI configuration."""

    def test_default_config(self):
        """Test default config values."""
        config = VoyageConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.model == VoyageModel.VOYAGE_3
        assert config.max_tokens_per_batch == 320000
        assert config.rate_limit_rpm == 300
        assert config.max_batch_size == 128

    def test_custom_config(self):
        """Test custom config values."""
        config = VoyageConfig(
            api_key="test-key",
            model=VoyageModel.VOYAGE_3_LITE,
            max_tokens_per_batch=160000,
            rate_limit_rpm=100,
            timeout=120.0
        )

        assert config.model == VoyageModel.VOYAGE_3_LITE
        assert config.max_tokens_per_batch == 160000
        assert config.rate_limit_rpm == 100
        assert config.timeout == 120.0

    def test_config_retry_settings(self):
        """Test retry settings."""
        config = VoyageConfig(
            api_key="test-key",
            max_retries=5,
            retry_delay=2.0
        )

        assert config.max_retries == 5
        assert config.retry_delay == 2.0
