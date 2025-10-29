"""
SKAILA - Custom Exceptions
Professional error handling with specific, contextual exceptions
"""

class SKAILABaseException(Exception):
    """Base exception for all SKAILA custom exceptions"""
    def __init__(self, message: str, context: dict = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class DatabaseConnectionError(SKAILABaseException):
    """Raised when database connection fails"""
    pass


class DatabaseOperationError(SKAILABaseException):
    """Raised when a database operation fails"""
    pass


class ValidationError(SKAILABaseException):
    """Raised when data validation fails"""
    pass


class ResourceNotFoundError(SKAILABaseException):
    """Raised when a requested resource doesn't exist"""
    pass


class DuplicateResourceError(SKAILABaseException):
    """Raised when attempting to create a duplicate resource"""
    pass


class AuthorizationError(SKAILABaseException):
    """Raised when user lacks permission for an operation"""
    pass


class BusinessLogicError(SKAILABaseException):
    """Raised when business rules are violated"""
    pass


__all__ = [
    'SKAILABaseException',
    'DatabaseConnectionError',
    'DatabaseOperationError',
    'ValidationError',
    'ResourceNotFoundError',
    'DuplicateResourceError',
    'AuthorizationError',
    'BusinessLogicError'
]
