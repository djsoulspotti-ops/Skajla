"""
SKAJLA CSRF Middleware - Global CSRF Protection
Enforces CSRF token validation on all state-changing requests (POST, PUT, DELETE, PATCH)
"""

import functools
from flask import request, jsonify, session, g
from services.security.csrf_protection import validate_csrf_token, generate_csrf_token


class CSRFMiddleware:
    """Global CSRF protection middleware"""
    
    EXEMPT_PATHS = [
        '/api/auth/login',
        '/api/auth/refresh',
        '/socket.io',
    ]
    
    EXEMPT_PREFIXES = [
        '/static/',
        '/api/docs',
    ]
    
    STATE_CHANGING_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH']
    
    @staticmethod
    def is_exempt(path):
        """Check if path is exempt from CSRF protection"""
        if path in CSRFMiddleware.EXEMPT_PATHS:
            return True
        
        for prefix in CSRFMiddleware.EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    @staticmethod
    def is_api_request():
        """Check if request is JSON API (uses JWT authentication)"""
        return (
            request.is_json or 
            request.headers.get('Content-Type', '').startswith('application/json') or
            request.headers.get('Authorization', '').startswith('Bearer ')
        )
    
    @staticmethod
    def validate_request():
        """Validate CSRF token for state-changing requests"""
        if request.method not in CSRFMiddleware.STATE_CHANGING_METHODS:
            return True
        
        if CSRFMiddleware.is_exempt(request.path):
            return True
        
        if CSRFMiddleware.is_api_request():
            return True
        
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        
        if not validate_csrf_token(token):
            return False
        
        return True
    
    @staticmethod
    def handle_csrf_failure():
        """Handle CSRF validation failure"""
        if request.is_json or CSRFMiddleware.is_api_request():
            return jsonify({
                'success': False,
                'error': 'CSRF validation failed',
                'message': 'Invalid or missing CSRF token'
            }), 403
        
        from flask import flash, redirect
        flash('Token di sicurezza non valido. Riprova.', 'error')
        return redirect(request.referrer or '/'), 403


# Set of endpoints exempt from CSRF (registered by @csrf_exempt decorator)
_csrf_exempt_endpoints = set()


def csrf_exempt(f):
    """Decorator to exempt a route from CSRF protection"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    
    # Mark the function as CSRF exempt using an attribute
    decorated._csrf_exempt = True
    return decorated


def init_csrf_protection(app):
    """Initialize global CSRF protection"""
    
    @app.before_request
    def check_csrf():
        """Global CSRF validation before each request"""
        # Check if endpoint is exempt by endpoint name
        if request.endpoint:
            # Get the view function
            view_func = app.view_functions.get(request.endpoint)
            if view_func and getattr(view_func, '_csrf_exempt', False):
                return None
        
        if not CSRFMiddleware.validate_request():
            return CSRFMiddleware.handle_csrf_failure()
    
    @app.context_processor
    def inject_csrf():
        """Inject CSRF token into all templates"""
        return dict(csrf_token=generate_csrf_token)
    
    print("✅ Global CSRF protection enabled")


__all__ = ['CSRFMiddleware', 'csrf_exempt', 'init_csrf_protection']
