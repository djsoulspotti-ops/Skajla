"""
SKAILA Error Handling Decorators

Reusable decorators for consistent error handling across routes and services.
"""

import functools
import time
from typing import Callable, Type, Tuple, Optional
from flask import jsonify, render_template, request

from .exceptions import BaseSkailaError, map_exception, DatabaseTransientError
from .structured_logger import get_logger

logger = get_logger(__name__)


def handle_errors(api: bool = False, fallback_template: Optional[str] = None):
    """
    Decorator for consistent error handling in routes and services.
    
    Args:
        api: If True, return JSON responses. If False, render error templates.
        fallback_template: Template to render for web errors (defaults to 500.html)
    
    Usage:
        @handle_errors(api=True)
        def my_api_route():
            ...
        
        @handle_errors(api=False, fallback_template='error.html')
        def my_web_route():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except BaseSkailaError as e:
                # SKAILA exception - already has safe display message
                logger.error(
                    event_type='skaila_error',
                    domain=e.__class__.__name__,
                    message=e.message,
                    context=e.context,
                    endpoint=request.endpoint if hasattr(request, 'endpoint') else None
                )
                
                if api:
                    # API response - return JSON
                    return jsonify(e.to_dict()), e.http_status
                else:
                    # Web response - render template
                    template = fallback_template or '500.html'
                    return render_template(template, error=e.display_message), e.http_status
            
            except Exception as e:
                # Unexpected exception - map and handle safely
                mapped_error = map_exception(e)
                
                logger.error(
                    event_type='unexpected_error',
                    domain='unknown',
                    message=str(e),
                    error_type=type(e).__name__,
                    context=mapped_error.context,
                    endpoint=request.endpoint if hasattr(request, 'endpoint') else None,
                    exc_info=True  # Include stack trace in logs
                )
                
                if api:
                    return jsonify(mapped_error.to_dict()), mapped_error.http_status
                else:
                    template = fallback_template or '500.html'
                    return render_template(template, error=mapped_error.display_message), mapped_error.http_status
        
        return wrapper
    return decorator


def retry_on(
    exceptions: Tuple[Type[Exception], ...] = (DatabaseTransientError,),
    max_retries: int = 3,
    backoff_multiplier: float = 0.5,
    max_backoff: float = 5.0
):
    """
    Decorator for retrying operations on transient failures.
    
    Uses exponential backoff with jitter for optimal retry behavior.
    
    Args:
        exceptions: Tuple of exception types to catch and retry
        max_retries: Maximum number of retry attempts
        backoff_multiplier: Base backoff time (seconds)
        max_backoff: Maximum backoff time (seconds)
    
    Usage:
        @retry_on((DatabaseTransientError, ConnectionError), max_retries=5)
        def query_database():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate backoff with exponential growth + jitter
                        backoff = min(
                            backoff_multiplier * (2 ** attempt),
                            max_backoff
                        )
                        
                        logger.warning(
                            event_type='retry_attempt',
                            domain=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            backoff_seconds=backoff,
                            error=str(e)
                        )
                        
                        time.sleep(backoff)
                    else:
                        # Final attempt failed
                        logger.error(
                            event_type='retry_exhausted',
                            domain=func.__name__,
                            max_retries=max_retries,
                            final_error=str(e)
                        )
            
            # All retries exhausted - raise last exception
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def log_errors(domain: str = 'general'):
    """
    Decorator for logging errors without changing function behavior.
    
    Useful for monitoring critical functions without intercepting errors.
    
    Args:
        domain: Domain/category for logging
    
    Usage:
        @log_errors(domain='authentication')
        def verify_password(password, hash):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    event_type='function_error',
                    domain=domain,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise  # Re-raise exception
        
        return wrapper
    return decorator


# ============================================================================
# SPECIALIZED DECORATORS FOR COMMON PATTERNS
# ============================================================================

def safe_database_operation(max_retries: int = 3):
    """
    Specialized decorator for database operations with automatic retry.
    
    Combines retry_on and handle_errors for database operations.
    """
    def decorator(func: Callable) -> Callable:
        @retry_on((DatabaseTransientError,), max_retries=max_retries)
        @log_errors(domain='database')
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_ai_operation(fallback_value=None):
    """
    Specialized decorator for AI operations with fallback.
    
    Args:
        fallback_value: Value to return if AI operation fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    event_type='ai_operation_failed',
                    domain='ai_service',
                    function=func.__name__,
                    error=str(e),
                    fallback_used=True
                )
                return fallback_value
        return wrapper
    return decorator
