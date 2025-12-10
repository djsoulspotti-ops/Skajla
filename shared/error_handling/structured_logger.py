"""
SKAJLA Structured Logging

JSON-formatted logging for production observability and debugging.
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from flask import has_request_context, request, session


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs.
    
    Includes automatic context enrichment (user_id, request_id, etc.)
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Add JSON formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get automatic context from Flask request"""
        context: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Add request context if available
        if has_request_context():
            context['request_id'] = getattr(request, 'id', None)
            context['endpoint'] = request.endpoint
            context['method'] = request.method
            context['path'] = request.path
            context['ip'] = request.remote_addr
            
            # Add user_id from session if available (SAFE - no sensitive data)
            if session and 'user_id' in session:
                context['user_id'] = session['user_id']
            
            # Add school_id if available
            if session and 'scuola_id' in session:
                context['school_id'] = session['scuola_id']
        
        return context
    
    def _log(
        self,
        level: int,
        event_type: str,
        message: str = '',
        domain: str = 'general',
        exc_info: bool = False,
        **kwargs
    ):
        """Internal log method with context enrichment"""
        log_data = self._get_context()
        log_data.update({
            'event_type': event_type,
            'domain': domain,
            'message': message,
            **kwargs
        })
        
        # Add stack trace if exception info requested
        if exc_info:
            log_data['traceback'] = traceback.format_exc()
        
        # Log as JSON string
        self.logger.log(level, json.dumps(log_data, default=str))
    
    def debug(self, event_type: str = 'debug', message: str = '', domain: str = 'general', **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, event_type, message, domain, **kwargs)
    
    def info(self, event_type: str = 'info', message: str = '', domain: str = 'general', **kwargs):
        """Log info message"""
        self._log(logging.INFO, event_type, message, domain, **kwargs)
    
    def warning(self, event_type: str = 'warning', message: str = '', domain: str = 'general', **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, event_type, message, domain, **kwargs)
    
    def error(
        self,
        event_type: str = 'error',
        message: str = '',
        domain: str = 'general',
        exc_info: bool = False,
        **kwargs
    ):
        """Log error message"""
        self._log(logging.ERROR, event_type, message, domain, exc_info=exc_info, **kwargs)
    
    def critical(
        self,
        event_type: str = 'critical',
        message: str = '',
        domain: str = 'general',
        exc_info: bool = False,
        **kwargs
    ):
        """Log critical message"""
        self._log(logging.CRITICAL, event_type, message, domain, exc_info=exc_info, **kwargs)


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        # If message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            # Not JSON - format as JSON
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
            }
            
            # Add exception info if present
            if record.exc_info:
                log_data['traceback'] = self.formatException(record.exc_info)
            
            return json.dumps(log_data, default=str)


# ============================================================================
# GLOBAL LOGGER FACTORY
# ============================================================================

_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """
    Get or create a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
    
    Returns:
        StructuredLogger instance
    
    Usage:
        logger = get_logger(__name__)
        logger.info(event_type='user_login', user_id=123, success=True)
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]


# ============================================================================
# CONVENIENCE LOGGING FUNCTIONS
# ============================================================================

def log_security_event(
    event_type: str,
    user_id: Optional[int] = None,
    success: bool = True,
    **kwargs
):
    """
    Log security-related events (login, logout, permission changes, etc.)
    
    Args:
        event_type: Type of security event
        user_id: User ID involved
        success: Whether event was successful
        **kwargs: Additional context
    """
    logger = get_logger('security')
    logger.info(
        event_type=event_type,
        domain='security',
        user_id=user_id,
        success=success,
        **kwargs
    )


def log_database_query(
    query_type: str,
    table: str,
    duration_ms: float,
    success: bool = True,
    **kwargs
):
    """
    Log database query performance
    
    Args:
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration_ms: Query duration in milliseconds
        success: Whether query succeeded
        **kwargs: Additional context
    """
    logger = get_logger('database')
    
    level = 'info' if success else 'error'
    log_method = getattr(logger, level)
    
    log_method(
        event_type='database_query',
        domain='database',
        query_type=query_type,
        table=table,
        duration_ms=duration_ms,
        success=success,
        **kwargs
    )


def log_ai_request(
    model: str,
    tokens_used: int,
    cost_usd: float,
    duration_ms: float,
    success: bool = True,
    **kwargs
):
    """
    Log AI API requests for cost tracking
    
    Args:
        model: AI model used
        tokens_used: Number of tokens consumed
        cost_usd: Estimated cost in USD
        duration_ms: Request duration in milliseconds
        success: Whether request succeeded
        **kwargs: Additional context
    """
    logger = get_logger('ai_service')
    logger.info(
        event_type='ai_request',
        domain='ai',
        model=model,
        tokens_used=tokens_used,
        cost_usd=cost_usd,
        duration_ms=duration_ms,
        success=success,
        **kwargs
    )
