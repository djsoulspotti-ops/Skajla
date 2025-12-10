# Sistema di caching avanzato per produzione SKAJLA
# Riferimento integrazione: python_database per ottimizzazioni

import time
import json
import hashlib
from collections import OrderedDict
from threading import Lock
import logging

class ProductionCache:
    """Cache LRU ottimizzato per ambiente scolastico ad alto traffico"""
    
    def __init__(self, max_size=1000, ttl=300):  # 5 minuti TTL
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = Lock()
        self.stats = {
            'hits': 0,
            'misses': 0, 
            'evictions': 0
        }
        self.logger = logging.getLogger(__name__)
    
    def _generate_key(self, key_data):
        """Genera chiave cache consistente"""
        if isinstance(key_data, dict):
            key_str = json.dumps(key_data, sort_keys=True)
        else:
            key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key):
        """Recupera valore dalla cache con gestione TTL"""
        with self.lock:
            cache_key = self._generate_key(key)
            current_time = time.time()
            
            if cache_key in self.cache:
                # Controllo TTL
                if current_time - self.timestamps[cache_key] < self.ttl:
                    # Move to end (LRU)
                    value = self.cache.pop(cache_key)
                    self.cache[cache_key] = value
                    self.stats['hits'] += 1
                    return value
                else:
                    # Scaduto
                    del self.cache[cache_key]
                    del self.timestamps[cache_key]
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key, value):
        """Imposta valore in cache con gestione dimensione"""
        with self.lock:
            cache_key = self._generate_key(key)
            current_time = time.time()
            
            # Rimuovi se già esistente
            if cache_key in self.cache:
                del self.cache[cache_key]
            
            # Gestione dimensione massima
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
                self.stats['evictions'] += 1
            
            self.cache[cache_key] = value
            self.timestamps[cache_key] = current_time
    
    def invalidate_pattern(self, pattern):
        """Invalida cache per pattern (es. user_*, chat_*)"""
        with self.lock:
            keys_to_remove = []
            for key in self.cache.keys():
                if pattern in str(key):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.timestamps:
                    del self.timestamps[key]
    
    def get_stats(self):
        """Statistiche cache per monitoring"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate': f"{hit_rate:.1f}%",
            'entries': len(self.cache),
            'max_size': self.max_size,
            'stats': self.stats
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
    user_cache.invalidate_pattern(f"user_{user_id}")
    gamification_cache.invalidate_pattern(f"gamification_{user_id}")

def get_cache_health():
    """Stato salute sistema cache per monitoring"""
    return {
        'user_cache': user_cache.get_stats(),
        'chat_cache': chat_cache.get_stats(), 
        'message_cache': message_cache.get_stats(),
        'ai_cache': ai_cache.get_stats(),
        'gamification_cache': gamification_cache.get_stats()
    }

print("✅ Sistema caching produzione inizializzato")