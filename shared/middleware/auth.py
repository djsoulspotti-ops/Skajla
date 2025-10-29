"""
SKAILA Authentication & Authorization Middleware
Decorators centralizzati per gestione autenticazione e controllo ruoli
"""

from functools import wraps
from flask import session, redirect, jsonify, flash, url_for
from typing import Callable, Any, Optional, List


def require_login(f: Callable) -> Callable:
    """
    Decorator per richiedere autenticazione base
    Reindirizza a /login se user_id non in session
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login per accedere a questa pagina', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def require_auth(f: Callable) -> Callable:
    """
    Decorator per API endpoints che richiede autenticazione
    Ritorna JSON 401 se non autenticato
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Non autenticato',
                'message': 'Devi effettuare il login per accedere a questa risorsa'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def api_auth_required(f: Callable) -> Callable:
    """
    Alias di require_auth per compatibilità
    """
    return require_auth(f)


def require_role(*allowed_roles: str) -> Callable:
    """
    Decorator per controllo ruoli multipli
    
    Uso:
        @require_role('admin', 'professore')
        def my_route():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Devi effettuare il login', 'warning')
                return redirect('/login')
            
            user_role = session.get('ruolo')
            if user_role not in allowed_roles:
                flash('Accesso negato - Permessi insufficienti', 'danger')
                return redirect('/dashboard')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(f: Callable) -> Callable:
    """
    Decorator per richiedere ruolo admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login', 'warning')
            return redirect('/login')
        
        if session.get('ruolo') != 'admin':
            flash('Accesso negato - Solo amministratori', 'danger')
            return redirect('/dashboard')
        
        return f(*args, **kwargs)
    return decorated_function


def require_teacher(f: Callable) -> Callable:
    """
    Decorator per richiedere ruolo professore o dirigente
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Non autenticato'
            }), 401
        
        user_role = session.get('ruolo')
        if user_role not in ['professore', 'dirigente']:
            return jsonify({
                'success': False,
                'error': 'Accesso negato - Solo professori o dirigenti'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def require_student(f: Callable) -> Callable:
    """
    Decorator per richiedere ruolo studente
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login', 'warning')
            return redirect('/login')
        
        if session.get('ruolo') != 'studente':
            flash('Accesso negato - Solo studenti', 'danger')
            return redirect('/dashboard')
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> Optional[dict]:
    """
    Utility per ottenere dati utente corrente dalla session
    Returns None se non autenticato
    """
    if 'user_id' not in session:
        return None
    
    return {
        'id': session.get('user_id'),
        'nome': session.get('nome'),
        'cognome': session.get('cognome'),
        'email': session.get('email'),
        'ruolo': session.get('ruolo'),
        'school_id': session.get('school_id'),
        'classe_id': session.get('classe_id')
    }


def is_authenticated() -> bool:
    """
    Verifica se l'utente è autenticato
    """
    return 'user_id' in session


def has_role(role: str) -> bool:
    """
    Verifica se l'utente ha un ruolo specifico
    """
    return session.get('ruolo') == role


def has_any_role(*roles: str) -> bool:
    """
    Verifica se l'utente ha almeno uno dei ruoli specificati
    """
    return session.get('ruolo') in roles
