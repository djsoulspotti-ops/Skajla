
"""
SKAILA - User Service
Gestione utenti e profili
"""

from database_manager import db_manager
from cache_manager import cache_manager

class UserService:
    
    @staticmethod
    def get_user_by_id(user_id, use_cache=True):
        """Ottieni utente per ID con cache"""
        if use_cache:
            cached = cache_manager.get_user_data(user_id, 'profile')
            if cached:
                return cached
        
        with db_manager.get_connection() as conn:
            user = conn.execute('''
                SELECT * FROM utenti WHERE id = ? AND attivo = 1
            ''', (user_id,)).fetchone()
            
            if user and use_cache:
                user_dict = dict(user)
                cache_manager.cache_user_data(user_id, 'profile', user_dict, ttl=300)
                return user_dict
            
            return dict(user) if user else None
    
    @staticmethod
    def get_user_by_email(email):
        """Ottieni utente per email"""
        with db_manager.get_connection() as conn:
            user = conn.execute('''
                SELECT * FROM utenti WHERE email = ? AND attivo = 1
            ''', (email,)).fetchone()
            return dict(user) if user else None
    
    @staticmethod
    def update_user_status(user_id, online=True):
        """Aggiorna status online utente"""
        with db_manager.get_connection() as conn:
            conn.execute('''
                UPDATE utenti 
                SET status_online = ?, ultimo_accesso = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (1 if online else 0, user_id))
    
    @staticmethod
    def get_online_users(exclude_user_id=None):
        """Ottieni utenti online"""
        with db_manager.get_connection() as conn:
            query = '''
                SELECT nome, cognome, ruolo, classe FROM utenti 
                WHERE status_online = 1 AND attivo = 1
            '''
            params = []
            
            if exclude_user_id:
                query += ' AND id != ?'
                params.append(exclude_user_id)
            
            query += ' ORDER BY nome'
            
            return [dict(user) for user in conn.execute(query, params).fetchall()]
    
    @staticmethod
    def create_user(user_data):
        """Crea nuovo utente"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO utenti (username, email, password_hash, nome, cognome, 
                                   classe, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['username'],
                user_data['email'], 
                user_data['password_hash'],
                user_data['nome'],
                user_data['cognome'],
                user_data.get('classe', ''),
                user_data.get('ruolo', 'studente'),
                True
            ))
            
            return cursor.lastrowid
    
    @staticmethod
    def get_users_by_role(role, limit=None):
        """Ottieni utenti per ruolo"""
        with db_manager.get_connection() as conn:
            query = '''
                SELECT * FROM utenti 
                WHERE ruolo = ? AND attivo = 1
                ORDER BY nome, cognome
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            return [dict(user) for user in conn.execute(query, (role,)).fetchall()]

# Istanza globale
user_service = UserService()
