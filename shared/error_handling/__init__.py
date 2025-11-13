"""
SKAILA Error Handling Framework

Centralized error handling with typed exceptions, decorators, and structured logging.
Replaces 250+ bare except: blocks across the codebase with proper error management.

Architecture:
- Typed exception hierarchy (BaseSkailaError -> domain-specific errors)
- Reusable decorators for routes and services
- Structured JSON logging
- Safe user-facing error messages (no stack trace exposure)
- Retry logic for transient failures

Usage:
    from shared.error_handling import (
        DatabaseError, AuthError, handle_errors, retry_on
    )
    
    @handle_errors(api=True)
    @retry_on(DatabaseTransientError, max_retries=3)
    def my_function():
        ...
"""

from .exceptions import (
    BaseSkailaError,
    DatabaseError,
    DatabaseTransientError,
    DatabaseConnectionError,
    AuthError,
    AuthenticationError,
    AuthorizationError,
    AIServiceError,
    AIQuotaExceededError,
    FileStorageError,
    FileValidationError,
    ValidationError,
    ExternalServiceError,
)

from .decorators import (
    handle_errors,
    retry_on,
    log_errors,
)

from .structured_logger import (
    get_logger,
    StructuredLogger,
)

__all__ = [
    # Exceptions
    'BaseSkailaError',
    'DatabaseError',
    'DatabaseTransientError',
    'DatabaseConnectionError',
    'AuthError',
    'AuthenticationError',
    'AuthorizationError',
    'AIServiceError',
    'AIQuotaExceededError',
    'FileStorageError',
    'FileValidationError',
    'ValidationError',
    'ExternalServiceError',
    # Decorators
    'handle_errors',
    'retry_on',
    'log_errors',
    # Logging
    'get_logger',
    'StructuredLogger',
]
