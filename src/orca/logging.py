"""
Structured logging for ORCA.

Provides per-run trace IDs and JSON-formatted logs for observability.
"""

import contextvars
import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from orca.config import settings

# Context var for the current trace ID
trace_id_context: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")


def generate_trace_id() -> str:
    """Generate a unique trace ID for this request."""
    return f"{settings.orca_trace_id_prefix}_{uuid4().hex[:12]}"


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current context."""
    trace_id_context.set(trace_id)


def get_trace_id() -> str:
    """Get the current trace ID."""
    return trace_id_context.get()


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with trace ID."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        log_obj: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add trace ID if available
        if trace_id := get_trace_id():
            log_obj["trace_id"] = trace_id

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)  # type: ignore

        return json.dumps(log_obj)


def configure_logging() -> None:
    """Configure structured logging for ORCA."""
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.orca_log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Suppress verbose third-party logs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


# Auto-configure on import
configure_logging()
