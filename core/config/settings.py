"""
SKAILA - Configurazioni Centralizzate (SSoT)
Single Source of Truth per tutte le configurazioni del sistema
"""

import os
from typing import Dict, Any

class AppSettings:
    """Configurazioni applicazione"""
    
    APP_NAME = "SKAILA"
    VERSION = "2.0.0"
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    DEBUG = ENVIRONMENT == 'development'
    TESTING = False
    
    SECRET_KEY_FILE = '.env.secrets'
    
    HOST = '0.0.0.0'
    PORT = 5000
    
    ALLOWED_HOSTS = ['*']
    
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

class DatabaseSettings:
    """Configurazioni database"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    DB_POOL_SIZE = 10
    DB_MAX_OVERFLOW = 20
    DB_POOL_TIMEOUT = 30
    DB_POOL_RECYCLE = 3600
    
    ENABLE_QUERY_LOGGING = False

class SecuritySettings:
    """Configurazioni sicurezza"""
    
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    PERMANENT_SESSION_LIFETIME = 2592000
    NON_PERMANENT_SESSION_LIFETIME = 86400
    
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = 300
    
    BCRYPT_LOG_ROUNDS = 12
    
    CSRF_ENABLED = True
    
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_DEFAULT = "200 per hour"
    RATE_LIMIT_LOGIN = "5 per minute"

class CacheSettings:
    """Configurazioni caching"""
    
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    REDIS_URL = os.getenv('REDIS_URL')
    
    ENABLE_QUERY_CACHE = True
    QUERY_CACHE_TTL = 300
    
    ENABLE_USER_CACHE = True
    USER_CACHE_TTL = 600

class FileUploadSettings:
    """Configurazioni upload file"""
    
    UPLOAD_FOLDER = 'static/uploads'
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    ALLOWED_EXTENSIONS = {
        'documents': {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx'},
        'images': {'jpg', 'jpeg', 'png', 'gif', 'svg'},
        'videos': {'mp4', 'avi', 'mov', 'wmv'},
        'archives': {'zip', 'rar', '7z'}
    }
    
    @classmethod
    def is_allowed_file(cls, filename: str, file_type: str = None) -> bool:
        """Verifica se il file è consentito"""
        if '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        
        if file_type:
            return ext in cls.ALLOWED_EXTENSIONS.get(file_type, set())
        
        all_allowed = set()
        for exts in cls.ALLOWED_EXTENSIONS.values():
            all_allowed.update(exts)
        return ext in all_allowed

class EmailSettings:
    """Configurazioni email"""
    
    SMTP_SERVER = os.getenv('SMTP_SERVER', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    FROM_EMAIL = 'noreply@skaila.edu'
    FROM_NAME = 'SKAILA Platform'

class UISettings:
    """Configurazioni UI/UX"""
    
    THEME_PRIMARY_COLOR = '#667eea'
    THEME_SECONDARY_COLOR = '#764ba2'
    THEME_ACCENT_COLOR = '#f093fb'
    
    ITEMS_PER_PAGE = 20
    MAX_SEARCH_RESULTS = 100
    
    DATE_FORMAT = '%d/%m/%Y'
    DATETIME_FORMAT = '%d/%m/%Y %H:%M'
    TIME_FORMAT = '%H:%M'

settings = {
    'app': AppSettings,
    'database': DatabaseSettings,
    'security': SecuritySettings,
    'cache': CacheSettings,
    'upload': FileUploadSettings,
    'email': EmailSettings,
    'ui': UISettings
}

def get_setting(category: str, key: str, default: Any = None) -> Any:
    """Helper per ottenere una configurazione"""
    try:
        return getattr(settings[category], key)
    except (KeyError, AttributeError):
        return default
