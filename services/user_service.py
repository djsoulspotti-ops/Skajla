
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
        user = db_manager.query('''
            SELECT id, username, email, nome, cognome, 
                   classe, ruolo, avatar, ultimo_accesso
            FROM utenti 
            WHERE id = ? AND attivo = ?
        ''', (user_id, True), one=True)

        if user:
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'classe': user['classe'],
                'ruolo': user['ruolo'],
                'avatar': user['avatar'] or 'default.jpg',
                'ultimo_accesso': user['ultimo_accesso']
            }
            
            # Cache per 5 minuti
            cache_manager.set(cache_key, user_data, 300)
            return user_data

        return None

    def set_user_online(self, user_id: int):
        """Imposta utente come online"""
        self.online_users.add(user_id)
        
        db_manager.execute('''
            UPDATE utenti 
            SET status_online = ?, ultimo_accesso = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (True, user_id))

    def set_user_offline(self, user_id: int):
        """Imposta utente come offline"""
        self.online_users.discard(user_id)
        
        db_manager.execute('''
            UPDATE utenti 
            SET status_online = ?
            WHERE id = ?
        ''', (False, user_id))

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
        """Crea nuovo utente"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO utenti (username, email, password_hash, nome, cognome, 
                                   classe, ruolo, primo_accesso)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
