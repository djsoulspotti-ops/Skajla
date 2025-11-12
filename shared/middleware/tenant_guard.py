"""
SKAILA Tenant Isolation Middleware
Enforces multi-tenant data isolation to prevent cross-school data access
"""

import functools
from flask import session, g, jsonify, request
from typing import Optional, Callable


class TenantGuard:
    """Enforces tenant (school) isolation across all database queries"""
    
    @staticmethod
    def get_current_tenant_id() -> Optional[int]:
        """Get current tenant (school) ID from session or JWT"""
        scuola_id = session.get('scuola_id')
        
        if not scuola_id:
            scuola_id = getattr(g, 'scuola_id', None)
        
        return scuola_id
    
    @staticmethod
    def set_tenant_context(scuola_id: int):
        """Set tenant context for current request"""
        g.scuola_id = scuola_id
        g.tenant_validated = True
    
    @staticmethod
    def require_tenant():
        """Ensure tenant context exists for current request"""
        tenant_id = TenantGuard.get_current_tenant_id()
        
        if not tenant_id:
            return None
        
        if not hasattr(g, 'tenant_validated'):
            TenantGuard.set_tenant_context(tenant_id)
        
        return tenant_id
    
    @staticmethod
    def validate_tenant_access(resource_scuola_id: int) -> bool:
        """Validate that current user has access to resource's tenant"""
        current_tenant = TenantGuard.get_current_tenant_id()
        
        if not current_tenant:
            return False
        
        return current_tenant == resource_scuola_id


def require_tenant_context(f: Callable):
    """Decorator to ensure tenant context exists"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        tenant_id = TenantGuard.require_tenant()
        
        if not tenant_id:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required',
                    'message': 'No school context found in session'
                }), 403
            
            from flask import flash, redirect
            flash('Sessione non valida. Effettua nuovamente il login.', 'error')
            return redirect('/login')
        
        return f(*args, **kwargs)
    
    return decorated


def validate_tenant_resource(resource_scuola_id: int):
    """Validate that current tenant has access to a resource"""
    if not TenantGuard.validate_tenant_access(resource_scuola_id):
        raise TenantAccessViolation(
            f"Attempted cross-tenant access: current={TenantGuard.get_current_tenant_id()}, "
            f"resource={resource_scuola_id}"
        )


class TenantAccessViolation(Exception):
    """Raised when cross-tenant access is attempted"""
    pass


def init_tenant_guard(app):
    """Initialize tenant guard middleware"""
    
    @app.before_request
    def set_tenant_context():
        """Set tenant context from session before each request"""
        if request.endpoint and not request.endpoint.startswith('static'):
            scuola_id = session.get('scuola_id')
            if scuola_id:
                g.scuola_id = scuola_id
    
    @app.errorhandler(TenantAccessViolation)
    def handle_tenant_violation(error):
        """Handle tenant access violations"""
        from shared.logging.structured_logger import security_logger
        security_logger.critical(
            "Tenant isolation violation detected",
            extra={
                'error': str(error),
                'user_id': session.get('user_id'),
                'session_tenant': session.get('scuola_id'),
                'path': request.path,
                'method': request.method
            }
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'Unauthorized tenant access'
            }), 403
        
        from flask import flash, redirect
        flash('Accesso negato.', 'error')
        return redirect('/dashboard')
    
    print("✅ Tenant isolation guard enabled")


__all__ = [
    'TenantGuard',
    'require_tenant_context',
    'validate_tenant_resource',
    'TenantAccessViolation',
    'init_tenant_guard'
]
