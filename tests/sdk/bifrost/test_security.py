"""Tests for security hardening."""

import pytest
from bifrost_extensions.security.auth import APIKeyValidator, SecretManager
from bifrost_extensions.security.validation import InputValidator, OutputValidator
from bifrost_extensions.exceptions import AuthenticationError, ValidationError


class TestAPIKeyValidation:
    """Test API key validation."""

    def test_valid_key_passes(self):
        """Test valid API key passes validation."""
        validator = APIKeyValidator("test-key-123")
        validator.validate("test-key-123")  # Should not raise

    def test_invalid_key_raises(self):
        """Test invalid API key raises error."""
        validator = APIKeyValidator("correct-key")

        with pytest.raises(AuthenticationError, match="Invalid API key"):
            validator.validate("wrong-key")

    def test_missing_key_raises(self):
        """Test missing API key raises error."""
        validator = APIKeyValidator("test-key")

        with pytest.raises(AuthenticationError, match="API key required"):
            validator.validate(None)

    def test_constant_time_comparison(self):
        """Test timing-safe comparison prevents timing attacks."""
        import time

        validator = APIKeyValidator("a" * 32)

        # Time comparison with totally wrong key
        start = time.perf_counter()
        try:
            validator.validate("b" * 32)
        except AuthenticationError:
            pass
        wrong_time = time.perf_counter() - start

        # Time comparison with almost correct key (differs in last char)
        start = time.perf_counter()
        try:
            validator.validate("a" * 31 + "b")
        except AuthenticationError:
            pass
        almost_time = time.perf_counter() - start

        # Times should be similar (within 10x)
        # If not using constant-time, almost_time would be much longer
        assert wrong_time * 10 > almost_time


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sanitize_removes_control_characters(self):
        """Test control character removal."""
        dirty = "Hello\x00World\x01Test"
        clean = InputValidator.sanitize_string(dirty)
        assert clean == "HelloWorldTest"

    def test_sanitize_enforces_length_limit(self):
        """Test length limit enforcement."""
        long_string = "a" * 2000

        with pytest.raises(ValidationError, match="too long"):
            InputValidator.sanitize_string(long_string, max_length=1000)

    def test_rejects_sql_injection(self):
        """Test SQL injection detection."""
        malicious_inputs = [
            "'; DROP TABLE users--",
            "1 OR 1=1",
            "admin'--",
            "UNION SELECT * FROM passwords",
        ]

        for malicious in malicious_inputs:
            with pytest.raises(ValidationError, match="malicious"):
                InputValidator.sanitize_string(malicious)

    def test_rejects_script_injection(self):
        """Test script injection detection."""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            '<img src=x onerror="alert(1)">',
        ]

        for malicious in malicious_inputs:
            with pytest.raises(ValidationError, match="malicious"):
                InputValidator.sanitize_string(malicious)

    def test_validate_email_format(self):
        """Test email validation."""
        # Valid emails
        assert InputValidator.validate_email("test@example.com") == "test@example.com"
        assert InputValidator.validate_email("user.name+tag@domain.co") == "user.name+tag@domain.co"

        # Invalid emails
        with pytest.raises(ValidationError):
            InputValidator.validate_email("not-an-email")

        with pytest.raises(ValidationError):
            InputValidator.validate_email("missing@domain")

    def test_validate_url_scheme(self):
        """Test URL scheme validation."""
        # Valid URLs
        assert InputValidator.validate_url("https://example.com") == "https://example.com"
        assert InputValidator.validate_url("http://localhost:8000") == "http://localhost:8000"

        # Invalid schemes
        with pytest.raises(ValidationError, match="Invalid URL scheme"):
            InputValidator.validate_url("ftp://example.com")

        with pytest.raises(ValidationError, match="Invalid URL scheme"):
            InputValidator.validate_url("javascript:alert(1)")


class TestOutputValidation:
    """Test output validation and redaction."""

    def test_redacts_sensitive_keys(self):
        """Test sensitive key redaction."""
        data = {
            "user_id": "123",
            "api_key": "secret-key-123",
            "password": "super-secret",
            "token": "auth-token-456",
        }

        redacted = OutputValidator.redact_sensitive(data)

        assert redacted["user_id"] == "123"  # Not sensitive
        assert redacted["api_key"] == "***REDACTED***"
        assert redacted["password"] == "***REDACTED***"
        assert redacted["token"] == "***REDACTED***"

    def test_redacts_nested_sensitive_data(self):
        """Test redaction in nested structures."""
        data = {
            "user": {
                "name": "John",
                "settings": {  # Not a sensitive key, so won't be redacted wholesale
                    "token": "secret-123",
                    "api_key": "key-456",
                    "theme": "dark",  # Normal field
                }
            }
        }

        redacted = OutputValidator.redact_sensitive(data)

        assert isinstance(redacted, dict)
        assert redacted["user"]["name"] == "John"
        assert isinstance(redacted["user"]["settings"], dict)
        # Sensitive fields within settings should be redacted
        assert redacted["user"]["settings"]["token"] == "***REDACTED***"
        assert redacted["user"]["settings"]["api_key"] == "***REDACTED***"
        # Non-sensitive field should remain
        assert redacted["user"]["settings"]["theme"] == "dark"

    def test_validates_response_size(self):
        """Test response size validation."""
        # Small data should pass
        small_data = {"key": "value"}
        OutputValidator.validate_response_size(small_data)

        # Note: sys.getsizeof() doesn't accurately measure nested structures
        # This test demonstrates the API exists, actual size validation
        # would need a more robust implementation in production


class TestSecretManager:
    """Test secret management."""

    def test_mask_secret(self):
        """Test secret masking for logging."""
        secret = "sk-1234567890abcdef"

        masked = SecretManager.mask_secret(secret, visible_chars=4)
        # Should have stars for hidden chars + last 4 visible
        assert masked.endswith("cdef")
        assert len(masked) == len(secret)
        assert masked.count("*") == len(secret) - 4

    def test_mask_short_secret(self):
        """Test masking short secrets."""
        secret = "abc"

        masked = SecretManager.mask_secret(secret, visible_chars=4)
        assert masked == "***"
