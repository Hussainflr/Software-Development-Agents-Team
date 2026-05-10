"""
Production-ready structured logging configuration.

Uses structlog for consistent, context-aware logging across the application.
"""

import logging
import sys
from typing import Any

import structlog

from config import get_config


def setup_logging() -> None:
    """Configure structured logging for the application."""
    config = get_config()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso") if config.logging.include_timestamps else structlog.processors.PassthroughFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if config.logging.format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.logging.level),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance with optional context binding."""
    return structlog.get_logger(name)


class LogContext:
    """Context manager for binding request/execution context to logs."""

    def __init__(self, **context: Any):
        """Initialize with context variables."""
        self.context = context
        self.logger = get_logger("context")

    def __enter__(self) -> "LogContext":
        """Bind context on entry."""
        for key, value in self.context.items():
            self.logger = self.logger.bind(**{key: value})
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up on exit."""
        pass


# Module-level logger
logger = get_logger(__name__)
