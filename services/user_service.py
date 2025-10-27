"""
SKAILA - User Service
Gestione utenti e profili - PostgreSQL Edition
"""

from database_manager import db_manager
from cache_manager import cache_manager
from datetime import datetime

class UserService:
    
    @staticmethod
    def get_user_by_id(user_id, use_cache=True):
        """Ottieni utente per ID con cache"""
        if use_cache:
            cached = cache_manager.get_user_data(user_id, 'profile')
            if cached:
                return cached
        
        user = db_manager.query('''
            SELECT * FROM utenti WHERE id = %s AND attivo = true
        ''', (user_id,), one=True)
        
        if user and use_cache:
            cache_manager.cache_user_data(user_id, 'profile', user, ttl=300)
        
        return user
    
    @staticmethod
    def get_user_by_email(email):
        """Ottieni utente per email"""
        return db_manager.query('''
            SELECT * FROM utenti WHERE email = %s AND attivo = true
        ''', (email,), one=True)
    
    @staticmethod
    def update_user_status(user_id, online=True):
        """Aggiorna status online utente"""
        db_manager.execute('''
            UPDATE utenti 
            SET status_online = %s, ultimo_accesso = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (online, user_id))
    
    @staticmethod
    def get_online_users(exclude_user_id=None):
        """Ottieni utenti online"""
        if exclude_user_id:
            query = '''
                SELECT nome, cognome, ruolo, classe FROM utenti 
                WHERE status_online = true AND attivo = true AND id != %s
                ORDER BY nome
            '''
            return db_manager.query(query, (exclude_user_id,)) or []
        else:
            query = '''
                SELECT nome, cognome, ruolo, classe FROM utenti 
                WHERE status_online = true AND attivo = true
                ORDER BY nome
            '''
            return db_manager.query(query) or []
    
    @staticmethod
    def create_user(user_data):
        """Crea nuovo utente - PostgreSQL con RETURNING"""
        result = db_manager.query('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, 
                               classe, ruolo, primo_accesso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            user_data['username'],
            user_data['email'], 
            user_data['password_hash'],
            user_data['nome'],
            user_data['cognome'],
            user_data.get('classe', ''),
            user_data.get('ruolo', 'studente'),
            True
        ), one=True)
        
        return result['id'] if result else None
    
    @staticmethod
    def get_users_by_role(role, limit=None):
        """Ottieni utenti per ruolo"""
        query = '''
            SELECT * FROM utenti 
            WHERE ruolo = %s AND attivo = true
            ORDER BY nome, cognome
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        return db_manager.query(query, (role,)) or []

# Istanza globale
user_service = UserService()
