"""
SKAILA - Centralized Configuration
Production-grade configuration management for all modules
"""

import os
from datetime import timedelta

class Config:
    """Base configuration - shared across all environments"""
    
    # ============== SECURITY ==============
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    LOGIN_LOCKOUT_DURATION = int(os.getenv('LOGIN_LOCKOUT_DURATION', '900'))  # 15 minutes
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '2592000'))  # 30 days in seconds
    
    # ============== DATABASE ==============
    DB_POOL_MIN_SIZE = int(os.getenv('DB_POOL_MIN', '5'))
    DB_POOL_MAX_SIZE = int(os.getenv('DB_POOL_MAX', '50'))
    DB_QUERY_TIMEOUT = int(os.getenv('DB_QUERY_TIMEOUT', '30'))  # seconds
    
    # ============== STORAGE ==============
    MAX_STORAGE_GB = float(os.getenv('MAX_STORAGE_GB', '9.5'))  # 10 GB - buffer
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))  # 10 MB per file
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE', '16'))
    RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '730'))  # 2 years
    
    # ============== CACHING ==============
    CACHE_TTL_USER = int(os.getenv('CACHE_TTL_USER', '300'))  # 5 minutes
    CACHE_TTL_SCHOOL = int(os.getenv('CACHE_TTL_SCHOOL', '600'))  # 10 minutes
    CACHE_TTL_FEATURES = int(os.getenv('CACHE_TTL_FEATURES', '3600'))  # 1 hour
    CACHE_MAX_ITEMS = int(os.getenv('CACHE_MAX_ITEMS', '10000'))
    
    # ============== API LIMITS ==============
    API_RATE_LIMIT_LOGIN = os.getenv('API_RATE_LIMIT_LOGIN', '5 per minute')
    API_RATE_LIMIT_API = os.getenv('API_RATE_LIMIT_API', '100 per hour')
    API_PAGINATION_DEFAULT = int(os.getenv('API_PAGINATION_DEFAULT', '20'))
    API_PAGINATION_MAX = int(os.getenv('API_PAGINATION_MAX', '100'))
    
    # ============== GAMIFICATION ==============
    GAMIFICATION_MAX_DAILY_XP = int(os.getenv('GAMIFICATION_MAX_DAILY_XP', '500'))
    GAMIFICATION_LEVEL_MULTIPLIER = float(os.getenv('GAMIFICATION_LEVEL_MULTIPLIER', '1.1'))
    
    # ============== FEATURES ==============
    FEATURE_CACHE_TTL = int(os.getenv('FEATURE_CACHE_TTL', '3600'))  # 1 hour
    
    # ============== REDIS ==============
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_CONNECT_TIMEOUT = int(os.getenv('REDIS_CONNECT_TIMEOUT', '2'))
    REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
    
    # ============== MONITORING ==============
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
    METRICS_BATCH_SIZE = int(os.getenv('METRICS_BATCH_SIZE', '100'))
    
    # ============== EMAIL ==============
    EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', '50'))
    EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '30'))
    
    # ============== ALLOWED FEATURES (WHITELIST) ==============
    ALLOWED_FEATURES = {
        'gamification': 'modulo_gamification',
        'chatbot': 'modulo_chatbot',
        'ai_coach': 'modulo_chatbot',
        'registro': 'modulo_registro',
        'materiali': 'modulo_materiali',
        'connect': 'modulo_connect',
        'analytics': 'modulo_analytics'
    }
    
    # ============== QUERY LIMITS ==============
    DASHBOARD_RECENT_ACTIVITIES_LIMIT = int(os.getenv('DASHBOARD_ACTIVITIES_LIMIT', '10'))
    DASHBOARD_COMPANIES_LIMIT = int(os.getenv('DASHBOARD_COMPANIES_LIMIT', '3'))
    ACHIEVEMENTS_LIMIT = int(os.getenv('ACHIEVEMENTS_LIMIT', '3'))
    DAILY_STATS_DAYS = int(os.getenv('DAILY_STATS_DAYS', '7'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Production overrides
    CACHE_TTL_USER = 600  # 10 minutes in production
    CACHE_TTL_SCHOOL = 1800  # 30 minutes in production


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    # Testing overrides
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_LOCKOUT_DURATION = 60


# Factory function to get config based on environment
def get_config(env=None):
    """Get configuration object based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    config_map = {
        'production': ProductionConfig,
        'development': DevelopmentConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(env, DevelopmentConfig)()


# Default config instance
config = get_config()
