
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
    def __init__(self):
        self.login_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minuti

    def hash_password(self, password: str) -> str:
        """Hash password con bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica password"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def is_locked_out(self, email: str) -> bool:
        """Controlla se account è bloccato"""
        if email not in self.login_attempts:
            return False
        
        attempts = self.login_attempts[email]
        if attempts['count'] >= self.max_attempts:
            time_diff = time.time() - attempts['last_attempt']
            return time_diff < self.lockout_duration
        
        return False

    def record_failed_attempt(self, email: str):
        """Registra tentativo fallito"""
        if email not in self.login_attempts:
            self.login_attempts[email] = {'count': 0, 'last_attempt': 0}
        
        self.login_attempts[email]['count'] += 1
        self.login_attempts[email]['last_attempt'] = time.time()

    def reset_attempts(self, email: str):
        """Reset tentativi dopo login riuscito"""
        if email in self.login_attempts:
            del self.login_attempts[email]

    def authenticate_user(self, email: str, password: str) -> dict:
        """Autentica utente"""
        if self.is_locked_out(email):
            return None

        with db_manager.get_connection() as conn:
            user = conn.execute('''
                SELECT id, username, email, password_hash, nome, cognome, 
                       classe, ruolo, attivo, avatar
                FROM utenti 
                WHERE email = ? AND attivo = 1
            ''', (email,)).fetchone()

            if user and self.verify_password(password, user[3]):
                self.reset_attempts(email)
                
                # Aggiorna ultimo accesso
                conn.execute('''
                    UPDATE utenti 
                    SET ultimo_accesso = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user[0],))
                conn.commit()

                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'nome': user[4],
                    'cognome': user[5],
                    'classe': user[6],
                    'ruolo': user[7],
                    'avatar': user[9] or 'default.jpg'
                }
            else:
                self.record_failed_attempt(email)
                return None

    def create_user(self, username: str, email: str, password: str, 
                   nome: str, cognome: str, ruolo: str, classe: str = '') -> dict:
        """Crea nuovo utente"""
        try:
            with db_manager.get_connection() as conn:
                # Verifica se email/username esistono
                existing = conn.execute('''
                    SELECT COUNT(*) FROM utenti 
                    WHERE email = ? OR username = ?
                ''', (email, username)).fetchone()[0]

                if existing > 0:
                    return {'success': False, 'message': 'Email o username già esistenti'}

                # Hash password
                password_hash = self.hash_password(password)

                # Crea utente
                conn.execute('''
                    INSERT INTO utenti 
                    (username, email, password_hash, nome, cognome, classe, ruolo)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (username, email, password_hash, nome, cognome, classe, ruolo))
                
                conn.commit()
                return {'success': True, 'message': 'Utente creato con successo'}

        except Exception as e:
            return {'success': False, 'message': f'Errore: {str(e)}'}

# Istanza globale
auth_service = AuthService()

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
