
"""
SKAILA - User Service
Gestione utenti e profili
"""

from database_manager import db_manager
from cache_manager import cache_manager
from datetime import datetime

class UserService:
    def __init__(self):
        self.online_users = set()

    def get_user_by_id(self, user_id: int) -> dict:
        """Ottieni utente per ID"""
        cache_key = f"user_{user_id}"
        
        # Prova cache
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Query database
        with db_manager.get_connection() as conn:
            user = conn.execute('''
                SELECT id, username, email, nome, cognome, 
                       classe, ruolo, avatar, ultimo_accesso
                FROM utenti 
                WHERE id = ? AND attivo = 1
            ''', (user_id,)).fetchone()

            if user:
                user_data = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'nome': user[3],
                    'cognome': user[4],
                    'classe': user[5],
                    'ruolo': user[6],
                    'avatar': user[7] or 'default.jpg',
                    'ultimo_accesso': user[8]
                }
                
                # Cache per 5 minuti
                cache_manager.set(cache_key, user_data, 300)
                return user_data

        return None

    def set_user_online(self, user_id: int):
        """Imposta utente come online"""
        self.online_users.add(user_id)
        
        with db_manager.get_connection() as conn:
            conn.execute('''
                UPDATE utenti 
                SET status_online = 1, ultimo_accesso = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            conn.commit()

    def set_user_offline(self, user_id: int):
        """Imposta utente come offline"""
        self.online_users.discard(user_id)
        
        with db_manager.get_connection() as conn:
            conn.execute('''
                UPDATE utenti 
                SET status_online = 0
                WHERE id = ?
            ''', (user_id,))
            conn.commit()

    def get_online_users(self, exclude_user_id: int = None) -> list:
        """Ottieni lista utenti online"""
        with db_manager.get_connection() as conn:
            query = '''
                SELECT id, nome, cognome, ruolo, avatar
                FROM utenti 
                WHERE status_online = 1 AND attivo = 1
            '''
            params = []
            
            if exclude_user_id:
                query += ' AND id != ?'
                params.append(exclude_user_id)
                
            query += ' ORDER BY nome'
            
            users = conn.execute(query, params).fetchall()
            
            return [
                {
                    'id': user[0],
                    'nome': user[1],
                    'cognome': user[2],
                    'ruolo': user[3],
                    'avatar': user[4] or 'default.jpg'
                } for user in users
            ]

    def get_users_by_class(self, classe: str) -> list:
        """Ottieni utenti per classe"""
        with db_manager.get_connection() as conn:
            users = conn.execute('''
                SELECT id, nome, cognome, ruolo, avatar, status_online
                FROM utenti 
                WHERE classe = ? AND attivo = 1
                ORDER BY nome
            ''', (classe,)).fetchall()
            
            return [
                {
                    'id': user[0],
                    'nome': user[1],
                    'cognome': user[2],
                    'ruolo': user[3],
                    'avatar': user[4] or 'default.jpg',
                    'online': bool(user[5])
                } for user in users
            ]

    def update_user_avatar(self, user_id: int, avatar_filename: str):
        """Aggiorna avatar utente"""
        with db_manager.get_connection() as conn:
            conn.execute('''
                UPDATE utenti 
                SET avatar = ?
                WHERE id = ?
            ''', (avatar_filename, user_id))
            conn.commit()
        
        # Invalida cache
        cache_manager.delete(f"user_{user_id}")

    def get_user_stats(self, user_id: int) -> dict:
        """Ottieni statistiche utente"""
        with db_manager.get_connection() as conn:
            stats = conn.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM messaggi WHERE utente_id = ?) as total_messages,
                    (SELECT COUNT(*) FROM ai_conversations WHERE utente_id = ?) as ai_interactions,
                    (SELECT COUNT(*) FROM user_achievements WHERE user_id = ?) as achievements
            ''', (user_id, user_id, user_id)).fetchone()
            
            return {
                'total_messages': stats[0] or 0,
                'ai_interactions': stats[1] or 0,
                'achievements': stats[2] or 0
            }

# Istanza globale
user_service = UserService()

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
