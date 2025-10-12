"""
SKAILA Social Learning System
Peer help, study groups, collaborative learning
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from database_manager import db_manager
from gamification import gamification_system

class SocialLearningSystem:
    """Sistema apprendimento collaborativo"""
    
    def find_peer_help(self, user_id: int, subject: str, topic: Optional[str] = None) -> List[Dict]:
        """Trova compagni esperti in una materia"""
        
        # Get user class
        user = db_manager.query('SELECT classe, scuola_id FROM utenti WHERE id = ?', (user_id,), one=True)
        
        if not user or not user.get('classe'):
            return []
        
        # Find strong students in subject from same class
        query = '''
            SELECT u.id, u.nome, u.cognome, ssp.total_xp, ssp.accuracy_percentage, u.status_online
            FROM utenti u
            JOIN student_subject_progress ssp ON u.id = ssp.user_id
            WHERE u.classe = ? AND u.scuola_id = ? AND u.id != ? 
            AND ssp.subject = ? AND ssp.accuracy_percentage >= 75
            ORDER BY ssp.total_xp DESC, u.status_online DESC
            LIMIT 5
        '''
        
        helpers = db_manager.query(query, (user['classe'], user['scuola_id'], user_id, subject))
        
        result = []
        for helper in helpers:
            result.append({
                'user_id': helper['id'],
                'nome': f"{helper['nome']} {helper['cognome']}",
                'xp': helper['total_xp'],
                'accuracy': round(helper['accuracy_percentage'], 1),
                'is_online': helper['status_online'],
                'subject': subject
            })
        
        return result
    
    def request_peer_help(self, requester_id: int, helper_id: int, subject: str, topic: str, question: str) -> int:
        """Crea richiesta aiuto peer"""
        
        cursor = db_manager.execute('''
            INSERT INTO peer_help_requests 
            (requester_id, helper_id, subject, topic, question, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (requester_id, helper_id, subject, topic, question))
        
        # Notifica helper (TODO: implementare sistema notifiche)
        
        return cursor.lastrowid if hasattr(cursor, 'lastrowid') else 0
    
    def complete_peer_help(self, request_id: int, helper_id: int) -> Dict:
        """Completa sessione peer help"""
        
        # Update request
        db_manager.execute('''
            UPDATE peer_help_requests 
            SET status = 'completed', resolved_at = ?
            WHERE id = ? AND helper_id = ?
        ''', (datetime.now(), request_id, helper_id))
        
        # Get request data
        request = db_manager.query('''
            SELECT * FROM peer_help_requests WHERE id = ?
        ''', (request_id,), one=True)
        
        if not request:
            return {'error': 'Request not found'}
        
        # Award XP to both
        # Helper gets more XP
        gamification_system.award_xp(helper_id, 'help_classmate', 1.0, 
            f"Aiuto peer {request['subject']}")
        
        # Requester gets participation XP
        gamification_system.award_xp(request['requester_id'], 'join_study_group', 1.0,
            "Aiuto ricevuto da compagno")
        
        return {
            'success': True,
            'helper_xp': 60,
            'requester_xp': 30
        }
    
    def create_study_group(self, creator_id: int, name: str, subject: str, max_members: int = 6) -> int:
        """Crea gruppo di studio"""
        
        # Get creator class
        user = db_manager.query('SELECT classe FROM utenti WHERE id = ?', (creator_id,), one=True)
        classe = user['classe'] if user else None
        
        # Create group
        cursor = db_manager.execute('''
            INSERT INTO study_groups (name, subject, class, creator_id, max_members)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, subject, classe, creator_id, max_members))
        
        group_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else 0
        
        # Auto-join creator
        self.join_study_group(group_id, creator_id)
        
        # Award XP for creating
        gamification_system.award_xp(creator_id, 'create_study_group', 1.0,
            f"Gruppo studio '{name}' creato")
        
        return group_id
    
    def join_study_group(self, group_id: int, user_id: int) -> Dict:
        """Unisciti a gruppo studio"""
        
        # Check if group exists and has space
        group = db_manager.query('''
            SELECT sg.*, COUNT(sgm.id) as current_members
            FROM study_groups sg
            LEFT JOIN study_group_members sgm ON sg.id = sgm.group_id
            WHERE sg.id = ?
            GROUP BY sg.id
        ''', (group_id,), one=True)
        
        if not group:
            return {'error': 'Gruppo non trovato'}
        
        if group['current_members'] >= group['max_members']:
            return {'error': 'Gruppo pieno'}
        
        # Check if already member
        existing = db_manager.query('''
            SELECT id FROM study_group_members 
            WHERE group_id = ? AND user_id = ?
        ''', (group_id, user_id), one=True)
        
        if existing:
            return {'error': 'Già membro del gruppo'}
        
        # Join
        db_manager.execute('''
            INSERT INTO study_group_members (group_id, user_id)
            VALUES (?, ?)
        ''', (group_id, user_id))
        
        # Award XP
        gamification_system.award_xp(user_id, 'join_study_group', 1.0,
            f"Unito a '{group['name']}'")
        
        return {'success': True, 'group_name': group['name']}
    
    def get_study_groups(self, user_class: Optional[str] = None, subject: Optional[str] = None) -> List[Dict]:
        """Lista gruppi di studio disponibili"""
        
        query = '''
            SELECT sg.*, COUNT(sgm.id) as current_members,
                   u.nome as creator_name, u.cognome as creator_surname
            FROM study_groups sg
            LEFT JOIN study_group_members sgm ON sg.id = sgm.group_id
            LEFT JOIN utenti u ON sg.creator_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if user_class:
            query += ' AND sg.class = ?'
            params.append(user_class)
        
        if subject:
            query += ' AND sg.subject = ?'
            params.append(subject)
        
        query += ' GROUP BY sg.id ORDER BY sg.created_at DESC'
        
        groups = db_manager.query(query, tuple(params) if params else ())
        
        result = []
        for group in groups:
            result.append({
                'id': group['id'],
                'name': group['name'],
                'subject': group['subject'],
                'creator': f"{group['creator_name']} {group['creator_surname']}",
                'current_members': group['current_members'],
                'max_members': group['max_members'],
                'has_space': group['current_members'] < group['max_members']
            })
        
        return result
    
    def get_user_study_groups(self, user_id: int) -> List[Dict]:
        """Gruppi studio dell'utente"""
        
        groups = db_manager.query('''
            SELECT sg.*, COUNT(sgm2.id) as total_members
            FROM study_group_members sgm
            JOIN study_groups sg ON sgm.group_id = sg.id
            LEFT JOIN study_group_members sgm2 ON sg.id = sgm2.group_id
            WHERE sgm.user_id = ?
            GROUP BY sg.id
        ''', (user_id,))
        
        result = []
        for group in groups:
            result.append({
                'id': group['id'],
                'name': group['name'],
                'subject': group['subject'],
                'members_count': group['total_members']
            })
        
        return result
    
    def award_group_study_xp(self, group_id: int, session_duration_minutes: int):
        """Assegna XP a tutti i membri del gruppo per sessione studio"""
        
        members = db_manager.query('''
            SELECT user_id FROM study_group_members WHERE group_id = ?
        ''', (group_id,))
        
        # XP basato su durata
        xp_base = min(session_duration_minutes * 2, 120)  # Max 120 XP (60 min)
        
        for member in members:
            gamification_system.award_xp(member['user_id'], 'study_session_15min', 
                session_duration_minutes / 15,  # Multiplier
                f"Sessione studio gruppo ({session_duration_minutes} min)")
            
            # Update member stats
            db_manager.execute('''
                UPDATE study_group_members 
                SET xp_earned = xp_earned + ?
                WHERE group_id = ? AND user_id = ?
            ''', (xp_base, group_id, member['user_id']))


# Initialize system
social_learning = SocialLearningSystem()
print("✅ Social Learning System inizializzato!")
