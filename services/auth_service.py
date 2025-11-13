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
from services.database.database_manager import db_manager
from shared.validators.input_validators import validator, sql_protector
from shared.logging.structured_logger import auth_logger, security_logger

# Error handling framework
from shared.error_handling import (
    AuthenticationError,
    AuthorizationError,
    SessionExpiredError,
    AccountLockedError,
    ValidationError,
    get_logger,
    log_security_event
)

# Initialize structured logger for authentication
logger = get_logger(__name__)


class SecuritySettings:
    """Security configuration constants"""
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = 900


class AuthService:

    def __init__(self):
        self.login_attempts = {}
        self.max_attempts = SecuritySettings.MAX_LOGIN_ATTEMPTS
        self.lockout_duration = SecuritySettings.LOGIN_LOCKOUT_DURATION

    def hash_password(self, password: str) -> str:
        """Hash password con bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'),
                             bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password with bcrypt (primary) and SHA-256 fallback (legacy).
        
        Security Note: SHA-256 is insecure for password hashing (no salt, fast brute-force).
        This fallback exists only for backward compatibility with legacy accounts.
        TODO: Force bcrypt migration for all users - see DEVSECOPS_SECURITY_AUDIT_2025_11_12.md
        """
        try:
            # Primary: bcrypt verification (secure)
            is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            
            if is_valid:
                logger.debug(
                    event_type='password_verify_success',
                    domain='authentication',
                    method='bcrypt'
                )
            
            return is_valid
            
        except ValueError as e:
            # bcrypt failed - likely a SHA-256 hash (legacy)
            logger.warning(
                event_type='password_verify_fallback',
                domain='authentication',
                method='sha256_legacy',
                message='Using insecure SHA-256 fallback - schedule bcrypt migration',
                error=str(e)
            )
            
            # Fallback: SHA-256 verification (INSECURE - legacy only)
            is_valid = hashlib.sha256(password.encode()).hexdigest() == hashed
            
            if is_valid:
                # TODO: Trigger async password migration to bcrypt
                logger.warning(
                    event_type='legacy_password_detected',
                    domain='security',
                    message='User authenticated with SHA-256 hash - MIGRATION REQUIRED'
                )
                
            return is_valid
            
        except Exception as e:
            # Unexpected error - log and deny
            logger.error(
                event_type='password_verify_error',
                domain='authentication',
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return False

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
        
        # Structured logging for failed attempts
        security_logger.warning("Failed login attempt",
                              email=email,
                              attempt_count=self.login_attempts[email]['count'],
                              ip=request.remote_addr if request else "unknown")

    def reset_attempts(self, email: str):
        """Reset tentativi dopo login riuscito"""
        if email in self.login_attempts:
            del self.login_attempts[email]
            
        # Structured logging for successful login
        auth_logger.info("Successful login", 
                        email=email,
                        ip=request.remote_addr if request else "unknown")

    def authenticate_user(self, email: str, password: str):
        """Autentica utente"""
        # ✅ Validazione email con validatore centralizzato
        is_valid_email, email_error = validator.validate_email(email)
        if not is_valid_email:
            return None

        # ✅ Protezione SQL injection
        if not sql_protector.is_safe(email):
            return None

        if self.is_locked_out(email):
            return None

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if db_manager.db_type == 'postgresql':
                cursor.execute(
                    '''
                    SELECT id, username, email, password_hash, nome, cognome, 
                           classe, ruolo, attivo, avatar, scuola_id, classe_id
                    FROM utenti 
                    WHERE email = %s AND attivo = true
                ''', (email, ))
            else:
                cursor.execute(
                    '''
                    SELECT id, username, email, password_hash, nome, cognome, 
                           classe, ruolo, attivo, avatar, scuola_id, classe_id
                    FROM utenti 
                    WHERE email = ? AND attivo = 1
                ''', (email, ))

            user = cursor.fetchone()

            if user and self.verify_password(password, user[3]):
                self.reset_attempts(email)

                # Aggiorna ultimo accesso
                if db_manager.db_type == 'postgresql':
                    cursor.execute(
                        '''
                        UPDATE utenti 
                        SET ultimo_accesso = CURRENT_TIMESTAMP 
                        WHERE id = %s
                    ''', (user[0], ))
                else:
                    cursor.execute(
                        '''
                        UPDATE utenti 
                        SET ultimo_accesso = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (user[0], ))
                conn.commit()

                session['user_id'] = user[0]
                session['username'] = user[1]
                session['nome'] = user[4]
                session['cognome'] = user[5]
                session['ruolo'] = user[7]
                session['classe'] = user[6] or ''
                session['school_id'] = user[10]  # FIX: Aggiungi school_id
                session.permanent = True

                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'nome': user[4],
                    'cognome': user[5],
                    'classe': user[6],
                    'ruolo': user[7],
                    'avatar': user[9] or 'default.jpg',
                    'scuola_id': user[10],
                    'classe_id': user[11]
                }
            else:
                self.record_failed_attempt(email)
                return None

    def create_user(self,
                    username: str,
                    email: str,
                    password: str,
                    nome: str,
                    cognome: str,
                    ruolo: str,
                    classe: str = '',
                    scuola_id: int | None = None,
                    classe_id: int | None = None) -> dict:
        """Crea nuovo utente"""
        # ✅ Validazione email centralizzata
        is_valid_email, email_error = validator.validate_email(email)
        if not is_valid_email:
            return {'success': False, 'message': email_error}

        # ✅ Validazione password centralizzata
        is_valid_password, password_error = validator.validate_password(
            password)
        if not is_valid_password:
            return {'success': False, 'message': password_error}

        # ✅ Validazione username centralizzata
        is_valid_username, username_error = validator.validate_username(
            username)
        if not is_valid_username:
            return {'success': False, 'message': username_error}

        # ✅ Sanitizzazione input (anti-XSS)
        nome = validator.sanitize_html(nome)
        cognome = validator.sanitize_html(cognome)

        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Verifica se email/username esistono
                if db_manager.db_type == 'postgresql':
                    cursor.execute(
                        '''
                        SELECT COUNT(*) FROM utenti 
                        WHERE email = %s OR username = %s
                    ''', (email, username))
                else:
                    cursor.execute(
                        '''
                        SELECT COUNT(*) FROM utenti 
                        WHERE email = ? OR username = ?
                    ''', (email, username))

                existing = cursor.fetchone()[0]

                if existing > 0:
                    return {
                        'success': False,
                        'message': 'Email o username già esistenti'
                    }

                # Hash password
                password_hash = self.hash_password(password)

                # Crea utente con supporto scuola
                if db_manager.db_type == 'postgresql':
                    cursor.execute(
                        '''
                        INSERT INTO utenti 
                        (username, email, password_hash, nome, cognome, classe, ruolo, scuola_id, classe_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (username, email, password_hash, nome, cognome,
                          classe, ruolo, scuola_id, classe_id))
                    user_id = cursor.fetchone()[0]
                else:
                    cursor.execute(
                        '''
                        INSERT INTO utenti 
                        (username, email, password_hash, nome, cognome, classe, ruolo, scuola_id, classe_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (username, email, password_hash, nome, cognome,
                          classe, ruolo, scuola_id, classe_id))
                    user_id = cursor.lastrowid

                conn.commit()
                return {
                    'success': True,
                    'message': 'Utente creato con successo',
                    'user_id': user_id
                }

        except Exception as e:
            return {'success': False, 'message': f'Errore: {str(e)}'}

    def rate_limit_login(self, f):
        """Rate limiting per login"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR',
                                            request.remote_addr)

            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Crea tabella se non esiste
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS login_attempts (
                            id SERIAL PRIMARY KEY,
                            email TEXT,
                            ip_address TEXT,
                            user_agent TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            success BOOLEAN
                        )
                    ''')

                    cursor.execute(
                        '''
                        SELECT COUNT(*) FROM login_attempts 
                        WHERE ip_address = %s AND timestamp > NOW() - INTERVAL '15 minutes'
                    ''', (client_ip, ))
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS login_attempts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT,
                            ip_address TEXT,
                            user_agent TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            success BOOLEAN
                        )
                    ''')

                    cursor.execute(
                        '''
                        SELECT COUNT(*) FROM login_attempts 
                        WHERE ip_address = ? AND timestamp > datetime('now', '-15 minutes')
                    ''', (client_ip, ))

                recent_attempts = cursor.fetchone()[0]

                if recent_attempts >= 10:
                    return render_template(
                        'login.html',
                        error=
                        'Troppi tentativi di login. Riprova tra 15 minuti.')

            return f(*args, **kwargs)

        return decorated_function

    def log_login_attempt(self, email, success, ip_address):
        """Log tentativi di login"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if db_manager.db_type == 'postgresql':
                cursor.execute(
                    '''
                    INSERT INTO login_attempts (email, success, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s)
                ''', (email, success, ip_address,
                      request.headers.get('User-Agent', '')))
            else:
                cursor.execute(
                    '''
                    INSERT INTO login_attempts (email, success, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s)
                ''', (email, success, ip_address,
                      request.headers.get('User-Agent', '')))
            conn.commit()

    def require_auth(self, f):
        """Decorator per route protette"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return {'error': 'Non autorizzato'}, 401
            return f(*args, **kwargs)

        return decorated_function

    def require_role(self, required_role):
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
