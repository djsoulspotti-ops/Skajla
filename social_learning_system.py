"""
SKAILA Social Learning System
Peer help, study groups, collaborative learning
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from database_manager import db_manager, CursorProxy
from gamification import gamification_system

class SocialLearningSystem:
    """Sistema apprendimento collaborativo"""
    
    def find_peer_help(self, user_id: int, subject: str, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Trova compagni esperti in una materia"""
        
        # Get user class
        user = db_manager.query('SELECT classe, scuola_id FROM utenti WHERE id = %s', (user_id,), one=True)
        
        if not user or not user.get('classe'):
            return []
        
        # Find strong students in subject from same class
        query = '''
            SELECT u.id, u.nome, u.cognome, ssp.total_xp, ssp.accuracy_percentage, u.status_online
            FROM utenti u
            JOIN student_subject_progress ssp ON u.id = ssp.user_id
            WHERE u.classe = %s AND u.scuola_id = %s AND u.id != %s 
            AND ssp.subject = %s AND ssp.accuracy_percentage >= 75
            ORDER BY ssp.total_xp DESC, u.status_online DESC
            LIMIT 5
        '''
        
        helpers = db_manager.query(query, (user['classe'], user['scuola_id'], user_id, subject)) or []
        
        result: List[Dict[str, Any]] = []
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
        
        result = db_manager.execute('''
            INSERT INTO peer_help_requests 
            (requester_id, helper_id, subject, topic, question, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
        ''', (requester_id, helper_id, subject, topic, question))
        
        # Notifica helper (TODO: implementare sistema notifiche)
        
        if isinstance(result, CursorProxy):
            return result.lastrowid or 0
        elif hasattr(result, 'lastrowid'):
            return result.lastrowid or 0
        return 0
    
    def complete_peer_help(self, request_id: int, helper_id: int) -> Dict[str, Any]:
        """Completa sessione peer help"""
        
        # Update request
        db_manager.execute('''
            UPDATE peer_help_requests 
            SET status = 'completed', resolved_at = %s
            WHERE id = %s AND helper_id = %s
        ''', (datetime.now(), request_id, helper_id))
        
        # Get request data
        request = db_manager.query('''
            SELECT * FROM peer_help_requests WHERE id = %s
        ''', (request_id,), one=True)
        
        if not request:
            return {'error': 'Request not found'}
        
        # Award XP to both
        # Helper gets more XP
        gamification_system.award_xp(helper_id, 'help_classmate', 1.0, 
            f"Aiuto peer {request.get('subject', 'Unknown')}")
        
        # Requester gets participation XP
        gamification_system.award_xp(request.get('requester_id', 0), 'join_study_group', 1.0,
            "Aiuto ricevuto da compagno")
        
        return {
            'success': True,
            'helper_xp': 60,
            'requester_xp': 30
        }
    
    def create_study_group(self, creator_id: int, name: str, subject: str, max_members: int = 6) -> int:
        """Crea gruppo di studio"""
        
        # Get creator class
        user = db_manager.query('SELECT classe FROM utenti WHERE id = %s', (creator_id,), one=True)
        classe = user.get('classe') if user else None
        
        # Create group
        result = db_manager.execute('''
            INSERT INTO study_groups (name, subject, class, creator_id, max_members)
            VALUES (%s, %s, %s, %s, %s)
        ''', (name, subject, classe, creator_id, max_members))
        
        group_id = 0
        if isinstance(result, CursorProxy):
            group_id = result.lastrowid or 0
        elif hasattr(result, 'lastrowid'):
            group_id = result.lastrowid or 0
        
        # Auto-join creator
        if group_id > 0:
            self.join_study_group(group_id, creator_id)
        
        # Award XP for creating
        gamification_system.award_xp(creator_id, 'create_study_group', 1.0,
            f"Gruppo studio '{name}' creato")
        
        return group_id
    
    def join_study_group(self, group_id: int, user_id: int) -> Dict[str, Any]:
        """Unisciti a gruppo studio"""
        
        # Check if group exists and has space
        group = db_manager.query('''
            SELECT sg.*, COUNT(sgm.id) as current_members
            FROM study_groups sg
            LEFT JOIN study_group_members sgm ON sg.id = sgm.group_id
            WHERE sg.id = %s
            GROUP BY sg.id
        ''', (group_id,), one=True)
        
        if not group:
            return {'error': 'Gruppo non trovato'}
        
        if group.get('current_members', 0) >= group.get('max_members', 0):
            return {'error': 'Gruppo pieno'}
        
        # Check if already member
        existing = db_manager.query('''
            SELECT id FROM study_group_members 
            WHERE group_id = %s AND user_id = %s
        ''', (group_id, user_id), one=True)
        
        if existing:
            return {'error': 'Già membro del gruppo'}
        
        # Join
        db_manager.execute('''
            INSERT INTO study_group_members (group_id, user_id)
            VALUES (%s, %s)
        ''', (group_id, user_id))
        
        # Award XP
        gamification_system.award_xp(user_id, 'join_study_group', 1.0,
            f"Unito a '{group.get('name', 'gruppo')}'")
        
        return {'success': True, 'group_name': group.get('name', 'gruppo')}
    
    def get_study_groups(self, user_class: Optional[str] = None, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista gruppi di studio disponibili"""
        
        query = '''
            SELECT sg.*, COUNT(sgm.id) as current_members,
                   u.nome as creator_name, u.cognome as creator_surname
            FROM study_groups sg
            LEFT JOIN study_group_members sgm ON sg.id = sgm.group_id
            LEFT JOIN utenti u ON sg.creator_id = u.id
            WHERE 1=1
        '''
        params: List[str] = []
        
        if user_class:
            query += ' AND sg.class = %s'
            params.append(user_class)
        
        if subject:
            query += ' AND sg.subject = %s'
            params.append(subject)
        
        query += ' GROUP BY sg.id ORDER BY sg.created_at DESC'
        
        groups = db_manager.query(query, tuple(params) if params else ()) or []
        
        result: List[Dict[str, Any]] = []
        for group in groups:
            result.append({
                'id': group.get('id'),
                'name': group.get('name'),
                'subject': group.get('subject'),
                'creator': f"{group.get('creator_name', '')} {group.get('creator_surname', '')}",
                'current_members': group.get('current_members', 0),
                'max_members': group.get('max_members', 0),
                'has_space': group.get('current_members', 0) < group.get('max_members', 0)
            })
        
        return result
    
    def get_user_study_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Gruppi studio dell'utente"""
        
        groups = db_manager.query('''
            SELECT sg.*, COUNT(sgm2.id) as total_members
            FROM study_group_members sgm
            JOIN study_groups sg ON sgm.group_id = sg.id
            LEFT JOIN study_group_members sgm2 ON sg.id = sgm2.group_id
            WHERE sgm.user_id = %s
            GROUP BY sg.id
        ''', (user_id,)) or []
        
        result: List[Dict[str, Any]] = []
        for group in groups:
            result.append({
                'id': group.get('id'),
                'name': group.get('name'),
                'subject': group.get('subject'),
                'members_count': group.get('total_members', 0)
            })
        
        return result
    
    def award_group_study_xp(self, group_id: int, session_duration_minutes: int) -> None:
        """Assegna XP a tutti i membri del gruppo per sessione studio"""
        
        members = db_manager.query('''
            SELECT user_id FROM study_group_members WHERE group_id = %s
        ''', (group_id,)) or []
        
        # XP basato su durata
        xp_base = min(session_duration_minutes * 2, 120)  # Max 120 XP (60 min)
        
        for member in members:
            gamification_system.award_xp(member.get('user_id', 0), 'study_session_15min', 
                session_duration_minutes / 15,  # Multiplier
                f"Sessione studio gruppo ({session_duration_minutes} min)")
            
            # Update member stats
            db_manager.execute('''
                UPDATE study_group_members 
                SET xp_earned = xp_earned + %s
                WHERE group_id = %s AND user_id = %s
            ''', (xp_base, group_id, member.get('user_id', 0)))


# Initialize system
social_learning = SocialLearningSystem()
print("✅ Social Learning System inizializzato!")
