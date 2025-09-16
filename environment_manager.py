"""
SKAILA Environment Management
Gestione sicura delle variabili di ambiente e configurazione
"""

import os
import secrets
from typing import Optional, Dict, Any

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
        self.validate_environment()
    
    def validate_environment(self):
        """Valida e configura le variabili di ambiente"""
        missing_optional = []
        
        for key, description in self.required_keys.items():
            value = os.getenv(key)
            if not value:
                if key == 'SECRET_KEY':
                    # Genera SECRET_KEY sicura se mancante
                    generated_key = secrets.token_hex(32)
                    os.environ[key] = generated_key
                    print(f'⚠️ {key} generata automaticamente (temporanea)')
                    print(f'⚠️ PRODUZIONE: Imposta {key} permanente nelle variabili ambiente!')
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
            
            # Sicurezza cookies
            'SESSION_COOKIE_SECURE': self.is_production(),
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'REMEMBER_COOKIE_SECURE': self.is_production(),
            'REMEMBER_COOKIE_HTTPONLY': True,
            
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
    
    def get_database_status(self) -> Dict[str, Any]:
        """Ottieni stato configurazione database"""
        db_url = self.get_database_url()
        return {
            'primary': 'postgresql' if db_url else 'sqlite',
            'postgresql_available': bool(db_url),
            'sqlite_fallback': True,
            'connection_string_present': bool(db_url)
        }

# Istanza globale
env_manager = EnvironmentManager()