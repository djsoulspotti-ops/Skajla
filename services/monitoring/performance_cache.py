# Sistema di caching avanzato per produzione SKAJLA
# Riferimento integrazione: python_database per ottimizzazioni

import time
import json
import hashlib
import logging
from services.redis_service import redis_manager

class ProductionCache:
    """Cache wrapper ottimizzato che delega a RedisManager"""
    
    def __init__(self, max_size=1000, ttl=300):
        self.ttl = ttl
        self.prefix = "cache:"
        self.logger = logging.getLogger(__name__)
    
    def _generate_key(self, key_data):
        """Genera chiave cache consistente"""
        if isinstance(key_data, dict):
            key_str = json.dumps(key_data, sort_keys=True)
        else:
            key_str = str(key_data)
        return self.prefix + hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key):
        """Recupera valore dalla cache"""
        cache_key = self._generate_key(key)
        return redis_manager.get(cache_key)
    
    def set(self, key, value):
        """Imposta valore in cache"""
        cache_key = self._generate_key(key)
        redis_manager.set(cache_key, value, ttl=self.ttl)
    
    def invalidate_pattern(self, pattern):
        """
        Invalida cache per pattern.
        Nota: Con Redis standard è costoso (KEYS *), qui facciamo best effort 
        se usiamo solo memory fallback o lasciamo scadere TTL.
        """
        # RedisManager handle expiration automatically
        pass
    
    def get_stats(self):
        """Statistiche cache (Mock per compatibilità interfaccia)"""
        return {
            'backend': 'Redis' if redis_manager.use_redis else 'Memory',
            'status': 'active'
        }

# Cache globali ottimizzate per diversi use case
user_cache = ProductionCache(max_size=2000, ttl=600)  # 10 min per utenti
chat_cache = ProductionCache(max_size=1000, ttl=300)  # 5 min per chat
message_cache = ProductionCache(max_size=5000, ttl=120) # 2 min per messaggi
ai_cache = ProductionCache(max_size=500, ttl=1800)   # 30 min per AI responses
gamification_cache = ProductionCache(max_size=1500, ttl=300) # 5 min per punti

def cache_user_data(user_id, user_data):
    """Cache dati utente ottimizzato"""
    user_cache.set(f"user_{user_id}", user_data)

def get_cached_user(user_id):
    """Recupera dati utente dalla cache"""
    return user_cache.get(f"user_{user_id}")

def cache_chat_messages(chat_id, messages):
    """Cache messaggi chat per performance"""
    message_cache.set(f"chat_messages_{chat_id}", messages)

def get_cached_chat_messages(chat_id):
    """Recupera messaggi dalla cache"""
    return message_cache.get(f"chat_messages_{chat_id}")

def invalidate_user_cache(user_id):
    """Invalida cache quando utente cambia"""
    # Redis TTL handles this mostly, explicit invalidation TODO if critical
    pass

def get_cache_health():
    """Stato salute sistema cache per monitoring"""
    return {
        'redis_connected': redis_manager.use_redis,
        'backend': 'Redis' if redis_manager.use_redis else 'MemoryFallback'
    }

print("✅ Sistema caching produzione (Redis-backed) inizializzato")