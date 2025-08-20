
import redis
import json
import os
from datetime import datetime, timedelta

class ScalableSessionManager:
    """Gestione sessioni scalabile per 30+ utenti simultanei"""
    
    def __init__(self):
        # Se disponibile, usa Redis, altrimenti fallback a dizionario in memoria
        self.use_redis = False
        self.memory_sessions = {}
        
        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                self.use_redis = True
                print("✅ Redis disponibile per sessioni scalabili")
        except:
            print("⚠️ Redis non disponibile - usando memoria locale")
    
    def set_session(self, session_id, user_data, expiry_hours=24):
        """Salva sessione utente"""
        expiry = datetime.now() + timedelta(hours=expiry_hours)
        session_data = {
            'user_data': user_data,
            'expires_at': expiry.isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        if self.use_redis:
            self.redis_client.setex(
                f"session:{session_id}", 
                timedelta(hours=expiry_hours), 
                json.dumps(session_data)
            )
        else:
            self.memory_sessions[session_id] = session_data
    
    def get_session(self, session_id):
        """Recupera sessione utente"""
        if self.use_redis:
            data = self.redis_client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        else:
            session = self.memory_sessions.get(session_id)
            if session:
                # Controlla scadenza
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.now() > expires_at:
                    del self.memory_sessions[session_id]
                    return None
            return session
    
    def delete_session(self, session_id):
        """Elimina sessione"""
        if self.use_redis:
            self.redis_client.delete(f"session:{session_id}")
        else:
            self.memory_sessions.pop(session_id, None)
    
    def get_active_users_count(self):
        """Conta utenti attivi"""
        if self.use_redis:
            return len(self.redis_client.keys("session:*"))
        else:
            now = datetime.now()
            active = 0
            for session in self.memory_sessions.values():
                expires_at = datetime.fromisoformat(session['expires_at'])
                if now < expires_at:
                    active += 1
            return active

# Istanza globale
session_manager = ScalableSessionManager()
