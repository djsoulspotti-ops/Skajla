
"""
SKAILA - Authentication Service
Logica business per autenticazione e sicurezza
"""

import bcrypt
import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, render_template
from database_manager import db_manager

class AuthService:
    
    @staticmethod
    def hash_password(password):
        """Hash sicuro con salt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verifica password con fallback"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return hashlib.sha256(password.encode()).hexdigest() == hashed
    
    @staticmethod
    def rate_limit_login(f):
        """Rate limiting per login"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            with db_manager.get_connection() as conn:
                # Crea tabella se non esiste
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS login_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ip_address TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN
                    )
                ''')
                
                recent_attempts = conn.execute('''
                    SELECT COUNT(*) FROM login_attempts 
                    WHERE ip_address = ? AND timestamp > datetime('now', '-15 minutes')
                ''', (client_ip,)).fetchone()[0]
                
                if recent_attempts >= 10:
                    return render_template('login.html', 
                        error='Troppi tentativi di login. Riprova tra 15 minuti.')
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def log_login_attempt(email, success, ip_address):
        """Log tentativi di login"""
        with db_manager.get_connection() as conn:
            conn.execute('''
                INSERT INTO login_attempts (email, success, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (email, success, ip_address, request.headers.get('User-Agent', '')))
    
    @staticmethod
    def create_user_session(user_data):
        """Crea sessione utente sicura"""
        session.permanent = True
        session['user_id'] = user_data['id']
        session['username'] = user_data['username']
        session['nome'] = user_data['nome']
        session['cognome'] = user_data['cognome']
        session['ruolo'] = user_data['ruolo']
        session['email'] = user_data['email']
        session['classe'] = user_data['classe']
    
    @staticmethod
    def require_auth(f):
        """Decorator per route protette"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return {'error': 'Non autorizzato'}, 401
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def require_role(required_role):
        """Decorator per controllo ruoli"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    return {'error': 'Non autorizzato'}, 401
                if session.get('ruolo') != required_role:
                    return {'error': 'Ruolo insufficiente'}, 403
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# Istanza globale
auth_service = AuthService()
