"""
SKAJLA Exception Hierarchy

Domain-specific exceptions for proper error handling and user-safe error messages.
"""

from typing import Optional, Dict, Any


class BaseSkailaError(Exception):
    """
    Base exception for all SKAJLA custom errors.
    
    Attributes:
        message: Internal error message (logged server-side)
        display_message: User-safe message (shown to client)
        context: Additional error context (logged but not shown to user)
        http_status: HTTP status code for API responses
    """
    
    def __init__(
        self,
        message: str,
        display_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        http_status: int = 500
    ):
        self.message = message
        self.display_message = display_message or "Si è verificato un errore. Riprova."
        self.context = context or {}
        self.http_status = http_status
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON responses"""
        return {
            'error': self.__class__.__name__,
            'message': self.display_message,
            'status': self.http_status
        }


# ============================================================================
# DATABASE ERRORS
# ============================================================================

class DatabaseError(BaseSkailaError):
    """Base class for all database-related errors"""
    def __init__(self, message: str, display_message: str = "Errore database. Riprova.", context: Optional[Dict] = None):
        super().__init__(message, display_message, context, http_status=500)


class DatabaseTransientError(DatabaseError):
    """Transient database error (connection timeout, Neon sleep) - safe to retry"""
    def __init__(self, message: str, context: Optional[Dict] = None):
        super().__init__(
            message,
            display_message="Il server database è temporaneamente non disponibile. Riprova.",
            context=context
        )


class DatabaseConnectionError(DatabaseError):
    """Critical database connection error - cannot establish connection"""
    def __init__(self, message: str, context: Optional[Dict] = None):
        super().__init__(
            message,
            display_message="Impossibile connettersi al database. Contatta l'amministratore.",
            context=context
        )


class DatabaseQueryError(DatabaseError):
    """SQL query execution error (syntax error, constraint violation)"""
    def __init__(self, message: str, query: Optional[str] = None, context: Optional[Dict] = None):
        ctx = context or {}
        if query:
            ctx['query'] = query[:200]  # Truncate query for logging
        super().__init__(
            message,
            display_message="Errore nell'esecuzione della query database.",
            context=ctx
        )


# ============================================================================
# AUTHENTICATION & AUTHORIZATION ERRORS
# ============================================================================

class AuthError(BaseSkailaError):
    """Base class for authentication/authorization errors"""
    def __init__(self, message: str, display_message: str = "Errore di autenticazione.", context: Optional[Dict] = None):
        super().__init__(message, display_message, context, http_status=401)


class AuthenticationError(AuthError):
    """Failed authentication (invalid credentials)"""
    def __init__(self, message: str = "Invalid credentials", context: Optional[Dict] = None):
        super().__init__(
            message,
            display_message="Credenziali non valide. Riprova.",
            context=context
        )


class AuthorizationError(AuthError):
    """Failed authorization (insufficient permissions)"""
    def __init__(self, message: str = "Insufficient permissions", context: Optional[Dict] = None):
        super().__init__(
            message,
            display_message="Non hai i permessi per eseguire questa operazione.",
            context=context
        )
        self.http_status = 403


class SessionExpiredError(AuthError):
    """Session has expired"""
    def __init__(self, context: Optional[Dict] = None):
        super().__init__(
            "Session expired",
            display_message="La tua sessione è scaduta. Effettua di nuovo il login.",
            context=context
        )


class AccountLockedError(AuthError):
    """Account locked due to too many failed login attempts"""
    def __init__(self, unlock_time: Optional[str] = None, context: Optional[Dict] = None):
        msg = f"Account bloccato. Riprova dopo {unlock_time}." if unlock_time else "Account bloccato per troppi tentativi."
        super().__init__(
            "Account locked",
            display_message=msg,
            context=context
        )


# ============================================================================
# AI SERVICE ERRORS
# ============================================================================

class AIServiceError(BaseSkailaError):
    """Base class for AI service errors"""
    def __init__(self, message: str, display_message: str = "Servizio AI non disponibile.", context: Optional[Dict] = None):
        super().__init__(message, display_message, context, http_status=503)


class AIQuotaExceededError(AIServiceError):
    """AI quota/budget exceeded"""
    def __init__(self, context: Optional[Dict] = None):
        super().__init__(
            "AI quota exceeded",
            display_message="Quota AI esaurita. Utilizza la modalità mock.",
            context=context
        )


class AIResponseError(AIServiceError):
    """AI service returned invalid/unexpected response"""
    def __init__(self, message: str, context: Optional[Dict] = None):
        super().__init__(
            message,
            display_message="Il servizio AI ha restituito una risposta non valida.",
            context=context
        )


# ============================================================================
# FILE STORAGE ERRORS
# ============================================================================

class FileStorageError(BaseSkailaError):
    """Base class for file storage errors"""
    def __init__(self, message: str, display_message: str = "Errore nella gestione file.", context: Optional[Dict] = None):
        super().__init__(message, display_message, context, http_status=500)


class FileValidationError(FileStorageError):
    """File validation failed (type, size, path)"""
    def __init__(self, message: str, context: Optional[Dict] = None):
        super().__init__(
            message,
            display_message="File non valido. Verifica tipo e dimensione.",
            context=context
        )
        self.http_status = 400


class FileUploadError(FileStorageError):
    """File upload failed"""
    def __init__(self, message: str, context: Optional[Dict] = None):
        super().__init__(
            message,
            display_message="Errore durante il caricamento del file. Riprova.",
            context=context
        )


class FileNotFoundError(FileStorageError):
    """Requested file not found"""
    def __init__(self, filename: str, context: Optional[Dict] = None):
        ctx = context or {}
        ctx['filename'] = filename
        super().__init__(
            f"File not found: {filename}",
            display_message="File non trovato.",
            context=ctx
        )
        self.http_status = 404


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(BaseSkailaError):
    """Input validation error"""
    def __init__(self, message: str, field: Optional[str] = None, context: Optional[Dict] = None):
        ctx = context or {}
        if field:
            ctx['field'] = field
        super().__init__(
            message,
            display_message=f"Validazione fallita: {message}",
            context=ctx
        )
        self.http_status = 400


# ============================================================================
# EXTERNAL SERVICE ERRORS
# ============================================================================

class ExternalServiceError(BaseSkailaError):
    """Base class for external service errors (email, APIs)"""
    def __init__(self, message: str, service_name: str = "servizio esterno", context: Optional[Dict] = None):
        ctx = context or {}
        ctx['service'] = service_name
        super().__init__(
            message,
            display_message=f"{service_name.capitalize()} non disponibile. Riprova più tardi.",
            context=ctx
        )
        self.http_status = 503


class EmailServiceError(ExternalServiceError):
    """Email sending failed"""
    def __init__(self, message: str, context: Optional[Dict] = None):
        super().__init__(message, service_name="servizio email", context=context)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def map_exception(exc: Exception) -> BaseSkailaError:
    """
    Map external exceptions (psycopg2, bcrypt, etc.) to SKAJLA exceptions.
    
    Args:
        exc: External exception to map
    
    Returns:
        Mapped SKAJLA exception
    """
    # PostgreSQL exceptions
    try:
        import psycopg2
        if isinstance(exc, (psycopg2.OperationalError, psycopg2.InterfaceError)):
            error_msg = str(exc).lower()
            if any(kw in error_msg for kw in ['connection', 'timeout', 'closed', 'eof', 'ssl']):
                return DatabaseTransientError(str(exc), context={'original_error': type(exc).__name__})
            return DatabaseConnectionError(str(exc), context={'original_error': type(exc).__name__})
        elif isinstance(exc, psycopg2.Error):
            return DatabaseQueryError(str(exc), context={'original_error': type(exc).__name__})
    except ImportError:
        pass
    
    # SQLite exceptions
    try:
        import sqlite3
        if isinstance(exc, sqlite3.OperationalError):
            return DatabaseTransientError(str(exc), context={'original_error': 'sqlite3.OperationalError'})
        elif isinstance(exc, sqlite3.Error):
            return DatabaseQueryError(str(exc), context={'original_error': type(exc).__name__})
    except ImportError:
        pass
    
    # Default: wrap as BaseSkailaError
    return BaseSkailaError(
        str(exc),
        display_message="Si è verificato un errore imprevisto.",
        context={'original_error': type(exc).__name__}
    )
