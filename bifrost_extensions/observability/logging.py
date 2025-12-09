"""Structured logging using python-json-logger."""

import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Optional

from pythonjsonlogger import jsonlogger
from opentelemetry import trace

__all__ = [
    "StructuredLogger",
    "JSONFormatter",
    "AuditLogger",
    "get_logger",
    "setup_logging",
]


class StructuredLogger:
    """Structured JSON logger for production.

    Outputs logs in JSON format for easy parsing by log aggregation systems.
    Uses python-json-logger under the hood.
    """

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        output: Any = sys.stdout,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Logging level
            output: Output stream
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add JSON formatter using python-json-logger
        handler = logging.StreamHandler(output)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

        # Don't propagate to root logger
        self.logger.propagate = False

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, kwargs)

    def error(
        self,
        message: str,
        exc_info: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        """Log error message with optional exception."""
        self._log(logging.ERROR, message, kwargs, exc_info=exc_info)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, kwargs)

    def _log(
        self,
        level: int,
        message: str,
        extra: dict,
        exc_info: Optional[Exception] = None,
    ) -> None:
        """Internal log method."""
        # Add trace context if available
        try:
            span = trace.get_current_span()
            if span and span.is_recording():
                ctx = span.get_span_context()
                extra["trace_id"] = format(ctx.trace_id, "032x")
                extra["span_id"] = format(ctx.span_id, "016x")
        except Exception:
            pass  # OpenTelemetry not available or span not active

        # Log with structured data
        self.logger.log(level, message, extra=extra, exc_info=exc_info)

    @contextmanager
    def operation(self, operation_name: str, **context: Any):
        """Context manager for operation logging.

        Args:
            operation_name: Name of operation
            **context: Additional context

        Yields:
            Logger instance

        Example:
            >>> with logger.operation("fetch_data", user_id="123"):
            >>>     data = await fetch_data()
        """
        start_time = time.perf_counter()
        self.info(f"{operation_name}.started", **context)

        try:
            yield self
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.info(
                f"{operation_name}.completed",
                duration_ms=duration_ms,
                **context,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.error(
                f"{operation_name}.failed",
                exc_info=e,
                duration_ms=duration_ms,
                error=str(e),
                **context,
            )
            raise


class JSONFormatter(jsonlogger.JsonFormatter):
    """JSON log formatter using python-json-logger.

    Formats log records as JSON for structured logging.
    """

    def __init__(self):
        """Initialize JSON formatter with custom format."""
        super().__init__(
            fmt=(
                "%(timestamp)s %(level)s %(logger)s %(message)s "
                "%(exception)s"
            )
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Ensure standard fields are present
        if not hasattr(record, "timestamp"):
            record.timestamp = self.formatTime(record, self.datefmt)

        # Call parent formatter
        return super().format(record)


# Global logger instance
_loggers: dict[str, StructuredLogger] = {}


def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """Get or create structured logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    output: Any = sys.stdout,
) -> None:
    """Setup global logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Format type (json or text)
        output: Output stream
    """
    log_level = getattr(logging, level.upper())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Add handler
    handler = logging.StreamHandler(output)
    if format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    root_logger.addHandler(handler)


class AuditLogger:
    """Audit logger for security-sensitive operations.

    Logs authentication, authorization, and data access events.
    """

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """Initialize audit logger."""
        self.logger = logger or get_logger("audit", level=logging.INFO)

    def log_auth_success(
        self,
        user_id: str,
        method: str,
        ip_address: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log successful authentication."""
        self.logger.info(
            "auth.success",
            event_type="authentication",
            user_id=user_id,
            auth_method=method,
            ip_address=ip_address,
            **context,
        )

    def log_auth_failure(
        self,
        reason: str,
        ip_address: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log failed authentication."""
        self.logger.warning(
            "auth.failure",
            event_type="authentication",
            reason=reason,
            ip_address=ip_address,
            **context,
        )

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        **context: Any,
    ) -> None:
        """Log data access."""
        self.logger.info(
            "data.access",
            event_type="data_access",
            user_id=user_id,
            resource=resource,
            action=action,
            **context,
        )

    def log_permission_denied(
        self,
        user_id: str,
        resource: str,
        action: str,
        **context: Any,
    ) -> None:
        """Log permission denial."""
        self.logger.warning(
            "permission.denied",
            event_type="authorization",
            user_id=user_id,
            resource=resource,
            action=action,
            **context,
        )
