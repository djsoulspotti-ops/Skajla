# -*- coding: utf-8 -*-
"""
CSRF Protection Module
Sistema di protezione contro Cross-Site Request Forgery
"""

import secrets
import functools
from flask import session, request, flash, redirect


def generate_csrf_token():
    """Genera un nuovo CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']


def validate_csrf_token(token):
    """Valida CSRF token"""
    return token and session.get('csrf_token') == token


def csrf_protect(f):
    """Decorator per protezione CSRF sui POST endpoints"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token')
            if not validate_csrf_token(token):
                flash('Token di sicurezza non valido. Riprova.', 'error')
                return redirect(request.referrer or '/')
        return f(*args, **kwargs)
    return decorated_function


def inject_csrf_token():
    """Context processor per aggiungere CSRF token ai template"""
    return dict(csrf_token=generate_csrf_token)