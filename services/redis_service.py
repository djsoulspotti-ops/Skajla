"""
SKAJLA - Redis Service Wrapper
Robust Redis connection handling with automatic in-memory fallback
"""

import redis
import json
import time
import logging
from config import config

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Wrapper per Redis con fallback in memoria.
    Garantisce che l'app funzioni anche senza Redis (es. dev locale)
    """
    
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        self.memory_store = {}  # Fallback
        self.connect()

    def connect(self):
        """Tenta connessione a Redis"""
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                socket_connect_timeout=config.REDIS_CONNECT_TIMEOUT,
                socket_timeout=config.REDIS_SOCKET_TIMEOUT,
                decode_responses=True  # Ritorna stringhe non bytes
            )
            self.redis_client.ping()
            self.use_redis = True
            logger.info("✅ Redis connected successfully")
        except redis.ConnectionError:
            self.use_redis = False
            logger.warning("⚠️ Redis connection failed. Using in-memory fallback.")
        except Exception as e:
            self.use_redis = False
            logger.error(f"⚠️ Redis generic error: {e}")

    # ================== GENERIC CACHE ==================

    def get(self, key):
        """Ottieni valore (stringa o dict convertito)"""
        try:
            if self.use_redis:
                val = self.redis_client.get(key)
                if val is None: return None
                try:
                    return json.loads(val)
                except TypeError:
                    return val
                except json.JSONDecodeError:
                    return val
            else:
                # Memory fallback
                item = self.memory_store.get(key)
                if not item: return None
                # Check expiration for memory store
                if item['expire'] and time.time() > item['expire']:
                    del self.memory_store[key]
                    return None
                return item['value']
        except Exception:
            return None

    def set(self, key, value, ttl=300):
        """Imposta valore con TTL (default 5 min)"""
        try:
            json_val = value if isinstance(value, str) else json.dumps(value)
            
            if self.use_redis:
                self.redis_client.setex(key, ttl, json_val)
            else:
                self.memory_store[key] = {
                    'value': value,
                    'expire': time.time() + ttl
                }
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def delete(self, key):
        if self.use_redis:
            self.redis_client.delete(key)
        elif key in self.memory_store:
            del self.memory_store[key]

    # ================== PRESENCE SYSTEM (OPTIMIZED) ==================

    def set_presence(self, user_id, is_online: bool, school_id=None):
        """Imposta stato online utente (ottimizzato con Redis Sets)"""
        try:
            timestamp = int(time.time())
            
            if self.use_redis:
                # 1. Update chiave singolo utente (per query veloci one-to-one)
                self.redis_client.setex(f"user:online:{user_id}", 300, "1" if is_online else "0")
                
                # 2. Update Set scuola (per lista "chi è online")
                if school_id:
                    key = f"school:presence:{school_id}"
                    if is_online:
                        self.redis_client.zadd(key, {str(user_id): timestamp})
                        # Scade dopo 1 ora di inattività totale della scuola
                        self.redis_client.expire(key, 3600) 
                    else:
                        self.redis_client.zrem(key, str(user_id))
            else:
                # Memory Fallback (semplificato)
                self.memory_store[f"user:online:{user_id}"] = {'value': is_online, 'expire': time.time() + 300}
        except Exception as e:
            logger.error(f"Presence error: {e}")

    def get_online_users(self, school_id):
        """Recupera lista ID utenti online nella scuola (Molto veloce con Redis)"""
        if not self.use_redis:
            return [] # Fallback complesso da implementare in memoria, meglio lista vuota in dev
        
        try:
            # 1. Pulisci utenti "dormienti" (ghost connections vecchie di 10 min)
            cutoff = int(time.time()) - 600
            key = f"school:presence:{school_id}"
            self.redis_client.zremrangebyscore(key, 0, cutoff)
            
            # 2. Ritorna range completo
            return self.redis_client.zrange(key, 0, -1)
        except Exception:
            return []

    # ================== RATE LIMITING (ATOMIC) ==================

    def check_rate_limit(self, key, limit=10, window=60):
        """
        Ritorna True se sotto il limite, False se bloccato.
        Usa Redis atomic increments.
        """
        if not self.use_redis:
            return True # In dev (senza Redis) permetti tutto
            
        try:
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, window)
            
            return current <= limit
        except Exception:
            return True

# Singleton instance
redis_manager = RedisManager()
