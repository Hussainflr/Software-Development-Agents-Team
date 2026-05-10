"""
Production-ready error handling and recovery mechanisms.

Provides structured exception handling, retry logic, and error tracking.
"""

from enum import Enum
from typing import Any, Callable, TypeVar

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from logging_config import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for prioritization."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AgentException(Exception):
    """Base exception for agent-related errors."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = False,
        context: dict[str, Any] | None = None,
    ):
        self.message = message
        self.severity = severity
        self.recoverable = recoverable
        self.context = context or {}
        super().__init__(self.message)


class ToolExecutionError(AgentException):
    """Raised when a tool execution fails."""
    pass


class ArtifactGenerationError(AgentException):
    """Raised when artifact generation fails."""
    pass


class ParsingError(AgentException):
    """Raised when output parsing fails."""
    pass


class ValidationError(AgentException):
    """Raised when validation fails."""
    pass


class ConfigurationError(AgentException):
    """Raised when configuration is invalid."""
    pass


class RetryableError(AgentException):
    """Raised for errors that should trigger a retry."""
    
    def __init__(
        self,
        message: str,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        **kwargs: Any,
    ):
        super().__init__(
            message,
            severity=ErrorSeverity.WARNING,
            recoverable=True,
            **kwargs,
        )
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor


F = TypeVar('F', bound=Callable[..., Any])


def with_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    recoverable_exceptions: tuple[type[Exception], ...] = (RetryableError, TimeoutError),
) -> Callable[[F], F]:
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff factor
        recoverable_exceptions: Exception types to retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=backoff_factor ** max_attempts),
            retry=retry_if_exception_type(recoverable_exceptions),
            reraise=True,
        )
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except RetryError as e:
                logger.error(
                    "max_retries_exceeded",
                    function=func.__name__,
                    max_attempts=max_attempts,
                )
                raise
            except Exception as e:
                logger.warning(
                    "retry_handler_caught_exception",
                    function=func.__name__,
                    exception_type=type(e).__name__,
                )
                raise
        
        return wrapper  # type: ignore
    return decorator


class ErrorRecoveryStrategy:
    """Defines how to handle different error types."""
    
    def __init__(self):
        self.handlers: dict[type[Exception], Callable] = {
            ToolExecutionError: self._handle_tool_error,
            ParsingError: self._handle_parsing_error,
            ValidationError: self._handle_validation_error,
            ConfigurationError: self._handle_config_error,
        }
    
    def handle(self, error: Exception, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Handle error and return recovery action."""
        context = context or {}
        handler = self.handlers.get(type(error), self._handle_generic_error)
        
        logger.error(
            "error_recovery",
            error_type=type(error).__name__,
            error_message=str(error),
            **context,
        )
        
        return handler(error, context)
    
    @staticmethod
    def _handle_tool_error(error: Exception, context: dict[str, Any]) -> dict[str, Any]:
        """Handle tool execution errors."""
        return {
            "action": "retry_tool",
            "recommendation": "Retry the tool execution with different parameters",
            "fallback": "Use cached results if available",
        }
    
    @staticmethod
    def _handle_parsing_error(error: Exception, context: dict[str, Any]) -> dict[str, Any]:
        """Handle output parsing errors."""
        return {
            "action": "fallback_parse",
            "recommendation": "Use fuzzy matching to extract intent from output",
            "fallback": "Generate default output structure",
        }
    
    @staticmethod
    def _handle_validation_error(error: Exception, context: dict[str, Any]) -> dict[str, Any]:
        """Handle validation errors."""
        return {
            "action": "request_correction",
            "recommendation": "Request agent to fix validation errors",
            "fallback": "Skip validation and proceed with caution",
        }
    
    @staticmethod
    def _handle_config_error(error: Exception, context: dict[str, Any]) -> dict[str, Any]:
        """Handle configuration errors."""
        return {
            "action": "use_defaults",
            "recommendation": "Use default configuration values",
            "fallback": "Abort execution",
        }
    
    @staticmethod
    def _handle_generic_error(error: Exception, context: dict[str, Any]) -> dict[str, Any]:
        """Handle unknown errors."""
        return {
            "action": "abort",
            "recommendation": "Check logs for detailed error information",
            "fallback": "Stop execution and report failure",
        }


class ErrorTracker:
    """Tracks errors for monitoring and analysis."""
    
    def __init__(self):
        self.errors: list[dict[str, Any]] = []
        self.error_counts: dict[str, int] = {}
    
    def track_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Track an error occurrence."""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        self.errors.append({
            "type": error_type,
            "message": str(error),
            "context": context or {},
            "count": self.error_counts[error_type],
        })
    
    def get_summary(self) -> dict[str, Any]:
        """Get error tracking summary."""
        return {
            "total_errors": len(self.errors),
            "unique_error_types": len(self.error_counts),
            "error_counts": self.error_counts,
            "recent_errors": self.errors[-5:],
        }


# Global error recovery strategy
_error_recovery = ErrorRecoveryStrategy()
_error_tracker = ErrorTracker()


def get_error_recovery() -> ErrorRecoveryStrategy:
    """Get global error recovery strategy."""
    return _error_recovery


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker."""
    return _error_tracker
