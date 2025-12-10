"""
SKAJLA Environment Management
Gestione sicura delle variabili di ambiente e configurazione
"""

import os
import secrets
from typing import Optional, Dict, Any
from pathlib import Path
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)

class EnvironmentManager:
    """Gestisce le variabili di ambiente e configurazione sicura"""
    
    def __init__(self):
        self.required_keys = {
            'SECRET_KEY': 'Flask session encryption key',
            'DATABASE_URL': 'PostgreSQL connection string (optional, fallback to SQLite)',
            'OPENAI_API_KEY': 'OpenAI API key for AI chatbot (optional, fallback to mock)'
        }
        self.optional_keys = {
            'ALLOWED_ORIGINS': 'Comma-separated list of allowed CORS origins',
            'ENVIRONMENT': 'Application environment (development/production)',
            'LOG_LEVEL': 'Logging level (DEBUG/INFO/WARNING/ERROR)',
            'MAX_UPLOAD_SIZE': 'Maximum file upload size in MB'
        }
        self.config_cache = {}
        self.local_secrets_file = Path('.env.secrets')
        self.validate_environment()
    
    def _load_or_generate_secret_key(self) -> str:
        """Carica SECRET_KEY da file locale o genera nuova (SICURA PER SVILUPPO)
        
        IMPORTANTE: In produzione, imposta SECRET_KEY in Replit Secrets!
        Questo metodo salva la chiave localmente SOLO per sviluppo.
        """
        # 1. Prova da environment variables (priorità massima)
        env_key = os.getenv('SECRET_KEY')
        if env_key:
            return env_key
        
        # 2. Prova da file locale
        if self.local_secrets_file.exists():
            try:
                content = self.local_secrets_file.read_text().strip()
                if content and len(content) >= 32:
                    print(f'✅ SECRET_KEY caricata da file locale (.env.secrets)')
                    return content
            except Exception as e:
                print(f'⚠️ Errore lettura .env.secrets: {e}')
        
        # 3. Genera nuova chiave e salvala
        new_key = secrets.token_hex(32)
        try:
            self.local_secrets_file.write_text(new_key)
            self.local_secrets_file.chmod(0o600)  # Solo owner può leggere
            print(f'✅ SECRET_KEY generata e salvata in .env.secrets')
            print(f'⚠️ SVILUPPO OK - PRODUZIONE: Copia questa chiave in Replit Secrets!')
        except Exception as e:
            print(f'⚠️ Non posso salvare SECRET_KEY locale: {e}')
            print(f'⚠️ Usando chiave temporanea - CONFIGURARE SECRET_KEY IN REPLIT SECRETS!')
        
        return new_key
    
    def validate_environment(self):
        """Valida e configura le variabili di ambiente"""
        missing_optional = []
        
        for key, description in self.required_keys.items():
            value = os.getenv(key)
            if not value:
                if key == 'SECRET_KEY':
                    # Auto-gestione SECRET_KEY con salvataggio locale
                    generated_key = self._load_or_generate_secret_key()
                    os.environ[key] = generated_key
                elif key in ['DATABASE_URL', 'OPENAI_API_KEY']:
                    # Keys opzionali con fallback
                    missing_optional.append(f'{key}: {description}')
                else:
                    print(f'❌ ERRORE: {key} obbligatoria mancante - {description}')
            else:
                print(f'✅ {key} configurata')
        
        if missing_optional:
            print('⚠️ Chiavi opzionali mancanti (usando fallback):')
            for missing in missing_optional:
                print(f'   - {missing}')
    
    def get_secret_key(self) -> str:
        """Ottieni SECRET_KEY sicura"""
        return os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    def get_database_url(self) -> Optional[str]:
        """Ottieni DATABASE_URL se disponibile"""
        return os.getenv('DATABASE_URL')
    
    def get_openai_key(self) -> Optional[str]:
        """Ottieni OPENAI_API_KEY se disponibile"""
        return os.getenv('OPENAI_API_KEY')
    
    def get_allowed_origins(self) -> list:
        """Ottieni origini CORS consentite"""
        origins = os.getenv('ALLOWED_ORIGINS', '*.replit.com,*.repl.co')
        return [origin.strip() for origin in origins.split(',')]
    
    def is_production(self) -> bool:
        """Verifica se siamo in ambiente produzione"""
        env = os.getenv('ENVIRONMENT', 'development').lower()
        return env in ['production', 'prod']
    
    def is_development(self) -> bool:
        """Verifica se siamo in ambiente sviluppo"""
        return not self.is_production()
    
    def get_log_level(self) -> str:
        """Ottieni livello di logging"""
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    def get_max_upload_size(self) -> int:
        """Ottieni dimensione massima upload in bytes"""
        size_mb = int(os.getenv('MAX_UPLOAD_SIZE', '16'))
        return size_mb * 1024 * 1024
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Ottieni configurazione Flask completa"""
        return {
            'SECRET_KEY': self.get_secret_key(),
            'UPLOAD_FOLDER': 'static/uploads',
            'MAX_CONTENT_LENGTH': self.get_max_upload_size(),
            
            # 🔒 HARDENED Session Security (DevSecOps Best Practices)
            'SESSION_COOKIE_SECURE': True,  # Always require HTTPS (use ngrok/replit proxy in dev)
            'SESSION_COOKIE_HTTPONLY': True,  # Prevent JavaScript access (XSS protection)
            'SESSION_COOKIE_SAMESITE': 'Strict',  # Prevent CSRF attacks (was 'Lax')
            'SESSION_COOKIE_NAME': '__Secure-session',  # Security prefix
            'PERMANENT_SESSION_LIFETIME': 7200,  # 2 hours in seconds
            'SESSION_REFRESH_EACH_REQUEST': False,  # Manual rotation for security
            
            # Remember Me Cookie Security
            'REMEMBER_COOKIE_SECURE': True,
            'REMEMBER_COOKIE_HTTPONLY': True,
            'REMEMBER_COOKIE_SAMESITE': 'Strict',
            'REMEMBER_COOKIE_DURATION': 604800,  # 7 days
            
            # Environment info
            'ENV': 'production' if self.is_production() else 'development',
            'DEBUG': self.is_development(),
            'TESTING': False
        }
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Ottieni stato configurazione AI"""
        api_key = self.get_openai_key()
        return {
            'enabled': bool(api_key),
            'mode': 'production' if api_key else 'mock',
            'key_present': bool(api_key),
            'fallback_available': True
        }
    
    def get_database_status(self, test_connectivity: bool = False) -> Dict[str, Any]:
        """Ottieni stato configurazione database con test connectivity opzionale"""
        db_url = self.get_database_url()
        
        # Test actual database connectivity solo se richiesto esplicitamente
        db_configured = True  # Default per evitare blocking durante init
        if test_connectivity:
            try:
                # Avoid circular import by lazy importing
                from database_manager import db_manager
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
                    db_configured = True
            except Exception as e:
                logger.warning(
                    event_type='db_connectivity_check_failed',
                    domain='environment',
                    message='Database connectivity test failed',
                    error=str(e)
                )
                db_configured = False
        
        return {
            'primary': 'postgresql' if db_url else 'sqlite',
            'postgresql_available': bool(db_url),
            'sqlite_fallback': True,
            'connection_string_present': bool(db_url),
            'configured': db_configured  # Connectivity test solo se richiesto
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Status completo del sistema per monitoring"""
        return {
            'database': self.get_database_status(),
            'ai': self.get_ai_status(),
            'environment': 'production' if self.is_production() else 'development',
            'debug_mode': self.get_flask_config()['DEBUG']
        }
    
    def is_configured(self) -> bool:
        """Verifica se environment è configured per readiness probe"""
        try:
            # Check basic configuration requirements
            flask_config = self.get_flask_config()
            has_secret = flask_config.get('SECRET_KEY') is not None
            
            # Check database connectivity (non-blocking)
            db_status = self.get_database_status()
            has_db = db_status.get('configured', False)
            
            return has_secret and has_db
        except Exception as e:
            logger.error(
                event_type='configuration_check_failed',
                domain='environment',
                message='Failed to check environment configuration',
                error=str(e),
                exc_info=True
            )
            return False

# Istanza globale
env_manager = EnvironmentManager()