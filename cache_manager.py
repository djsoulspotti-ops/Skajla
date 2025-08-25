
import time
import threading
from collections import defaultdict, OrderedDict
import hashlib
import json

class CacheManager:
    """Sistema di cache multi-livello per alta performance"""
    
    def __init__(self, max_size=1000, ttl_seconds=300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        # Cache multi-livello
        self.memory_cache = OrderedDict()  # LRU Cache
        self.user_cache = defaultdict(dict)  # Cache per utente
        self.query_cache = {}  # Cache query frequenti
        
        # Metadata cache
        self.cache_hits = 0
        self.cache_misses = 0
        self.lock = threading.RLock()
        
        # Auto-cleanup
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _generate_key(self, *args):
        """Genera chiave cache consistente"""
        key_str = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, category, key, default=None):
        """Recupera valore dalla cache"""
        with self.lock:
            cache_key = self._generate_key(category, key)
            
            if cache_key in self.memory_cache:
                value, timestamp = self.memory_cache[cache_key]
                
                # Controlla TTL
                if time.time() - timestamp < self.ttl_seconds:
                    # Sposta in testa (LRU)
                    self.memory_cache.move_to_end(cache_key)
                    self.cache_hits += 1
                    return value
                else:
                    # Scaduto
                    del self.memory_cache[cache_key]
            
            self.cache_misses += 1
            return default
    
    def set(self, category, key, value, ttl=None):
        """Imposta valore in cache"""
        with self.lock:
            cache_key = self._generate_key(category, key)
            timestamp = time.time()
            
            # Usa TTL personalizzato o default
            if ttl:
                timestamp_with_ttl = timestamp - (self.ttl_seconds - ttl)
            else:
                timestamp_with_ttl = timestamp
            
            self.memory_cache[cache_key] = (value, timestamp_with_ttl)
            
            # Mantieni dimensione cache
            if len(self.memory_cache) > self.max_size:
                # Rimuovi item più vecchio (LRU)
                self.memory_cache.popitem(last=False)
    
    def cache_user_data(self, user_id, data_type, data, ttl=60):
        """Cache specifica per utente (sessioni, profili, etc.)"""
        with self.lock:
            if user_id not in self.user_cache:
                self.user_cache[user_id] = {}
            
            self.user_cache[user_id][data_type] = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl
            }
    
    def get_user_data(self, user_id, data_type, default=None):
        """Recupera dati utente dalla cache"""
        with self.lock:
            if user_id in self.user_cache and data_type in self.user_cache[user_id]:
                cached_item = self.user_cache[user_id][data_type]
                
                if time.time() - cached_item['timestamp'] < cached_item['ttl']:
                    self.cache_hits += 1
                    return cached_item['data']
                else:
                    # Scaduto
                    del self.user_cache[user_id][data_type]
            
            self.cache_misses += 1
            return default
    
    def invalidate_user(self, user_id):
        """Invalida cache utente"""
        with self.lock:
            if user_id in self.user_cache:
                del self.user_cache[user_id]
    
    def cache_query_result(self, query, params, result, ttl=120):
        """Cache risultati query complesse"""
        query_key = self._generate_key(query, str(params))
        self.set('query_cache', query_key, result, ttl)
    
    def get_query_result(self, query, params):
        """Recupera risultato query dalla cache"""
        query_key = self._generate_key(query, str(params))
        return self.get('query_cache', query_key)
    
    def _cleanup_worker(self):
        """Worker per pulizia cache scaduta"""
        while True:
            time.sleep(60)  # Cleanup ogni minuto
            self._cleanup_expired()
    
    def _cleanup_expired(self):
        """Rimuove item scaduti dalla cache"""
        with self.lock:
            current_time = time.time()
            
            # Cleanup memory cache
            expired_keys = []
            for key, (value, timestamp) in self.memory_cache.items():
                if current_time - timestamp >= self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Cleanup user cache
            for user_id in list(self.user_cache.keys()):
                expired_data_types = []
                for data_type, cached_item in self.user_cache[user_id].items():
                    if current_time - cached_item['timestamp'] >= cached_item['ttl']:
                        expired_data_types.append(data_type)
                
                for data_type in expired_data_types:
                    del self.user_cache[user_id][data_type]
                
                # Rimuovi utenti senza dati
                if not self.user_cache[user_id]:
                    del self.user_cache[user_id]
    
    def get_stats(self):
        """Statistiche cache per monitoring"""
        with self.lock:
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hit_rate': hit_rate,
                'total_requests': total_requests,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'memory_cache_size': len(self.memory_cache),
                'user_cache_count': len(self.user_cache),
                'memory_usage_mb': self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self):
        """Stima utilizzo memoria (approssimativo)"""
        import sys
        
        total_size = 0
        total_size += sys.getsizeof(self.memory_cache)
        total_size += sys.getsizeof(self.user_cache)
        
        # Stima contenuto cache
        for key, (value, timestamp) in self.memory_cache.items():
            total_size += sys.getsizeof(key) + sys.getsizeof(value) + sys.getsizeof(timestamp)
        
        return total_size / (1024 * 1024)  # MB

# Istanza globale
cache_manager = CacheManager(max_size=2000, ttl_seconds=300)
