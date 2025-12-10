"""
SKAJLA Shared Middleware
Middleware centralizzati per autenticazione, autorizzazione e gestione errori
"""

from .auth import (
    require_login,
    require_auth,
    require_role,
    require_admin,
    require_teacher,
    require_student,
    api_auth_required
)

__all__ = [
    'require_login',
    'require_auth',
    'require_role',
    'require_admin',
    'require_teacher',
    'require_student',
    'api_auth_required'
]
