from database_manager import db_manager
from datetime import datetime

class StudyGroupsService:
    def __init__(self):
        pass
    
    def create_group(self, name, description, created_by, classe_id=None, scuola_id=None):
        try:
            result = db_manager.query("""
                INSERT INTO study_groups (name, description, created_by, classe_id, scuola_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (name, description, created_by, classe_id, scuola_id), one=True)
            
            if result:
                group_id = result['id']
                db_manager.query("""
                    INSERT INTO study_group_members (group_id, user_id, role)
                    VALUES (%s, %s, 'admin')
                """, (group_id, created_by))
                return {'success': True, 'group_id': group_id}
            return {'success': False, 'error': 'Errore creazione gruppo'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_groups(self, user_id):
        try:
            groups = db_manager.query("""
                SELECT sg.*, sgm.role as user_role,
                       (SELECT COUNT(*) FROM study_group_members WHERE group_id = sg.id) as member_count,
                       (SELECT COUNT(*) FROM study_group_messages WHERE group_id = sg.id) as message_count,
                       u.nome || ' ' || u.cognome as creator_name
                FROM study_groups sg
                JOIN study_group_members sgm ON sg.id = sgm.group_id
                LEFT JOIN utenti u ON sg.created_by = u.id
                WHERE sgm.user_id = %s AND sg.is_active = true
                ORDER BY sg.updated_at DESC
            """, (user_id,))
            return groups or []
        except Exception as e:
            print(f"Error getting user groups: {e}")
            return []
    
    def get_group_details(self, group_id, user_id):
        try:
            is_member = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id), one=True)
            
            if not is_member:
                return None
            
            group = db_manager.query("""
                SELECT sg.*, u.nome || ' ' || u.cognome as creator_name
                FROM study_groups sg
                LEFT JOIN utenti u ON sg.created_by = u.id
                WHERE sg.id = %s
            """, (group_id,), one=True)
            
            return group
        except Exception as e:
            print(f"Error getting group details: {e}")
            return None
    
    def get_group_members(self, group_id, user_id=None):
        try:
            if user_id:
                is_member = db_manager.query("""
                    SELECT id FROM study_group_members 
                    WHERE group_id = %s AND user_id = %s
                """, (group_id, user_id), one=True)
                if not is_member:
                    return []
            
            members = db_manager.query("""
                SELECT u.id, u.nome, u.cognome, u.avatar, sgm.role, sgm.joined_at
                FROM study_group_members sgm
                JOIN utenti u ON sgm.user_id = u.id
                WHERE sgm.group_id = %s
                ORDER BY sgm.role DESC, sgm.joined_at
            """, (group_id,))
            return members or []
        except Exception as e:
            print(f"Error getting group members: {e}")
            return []
    
    def is_member(self, group_id, user_id):
        try:
            result = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id), one=True)
            return result is not None
        except:
            return False
    
    def add_member(self, group_id, user_id, added_by):
        try:
            is_admin = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s AND role = 'admin'
            """, (group_id, added_by), one=True)
            
            if not is_admin:
                return {'success': False, 'error': 'Solo gli admin possono aggiungere membri'}
            
            member_count = db_manager.query("""
                SELECT COUNT(*) as count FROM study_group_members WHERE group_id = %s
            """, (group_id,), one=True)
            
            group = db_manager.query("""
                SELECT max_members FROM study_groups WHERE id = %s
            """, (group_id,), one=True)
            
            if member_count and group and member_count['count'] >= group['max_members']:
                return {'success': False, 'error': 'Gruppo pieno'}
            
            db_manager.query("""
                INSERT INTO study_group_members (group_id, user_id, role)
                VALUES (%s, %s, 'member')
                ON CONFLICT (group_id, user_id) DO NOTHING
            """, (group_id, user_id))
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def remove_member(self, group_id, user_id, removed_by):
        try:
            is_admin = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s AND role = 'admin'
            """, (group_id, removed_by), one=True)
            
            if not is_admin and user_id != removed_by:
                return {'success': False, 'error': 'Non autorizzato'}
            
            db_manager.query("""
                DELETE FROM study_group_members 
                WHERE group_id = %s AND user_id = %s AND role != 'admin'
            """, (group_id, user_id))
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_message(self, group_id, sender_id, content, message_type='text'):
        try:
            is_member = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, sender_id), one=True)
            
            if not is_member:
                return {'success': False, 'error': 'Non sei membro del gruppo'}
            
            result = db_manager.query("""
                INSERT INTO study_group_messages (group_id, sender_id, content, message_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
            """, (group_id, sender_id, content, message_type), one=True)
            
            db_manager.query("""
                UPDATE study_groups SET updated_at = CURRENT_TIMESTAMP WHERE id = %s
            """, (group_id,))
            
            if result:
                sender = db_manager.query("""
                    SELECT nome, cognome, avatar FROM utenti WHERE id = %s
                """, (sender_id,), one=True)
                
                return {
                    'success': True,
                    'message': {
                        'id': result['id'],
                        'content': content,
                        'sender_id': sender_id,
                        'sender_name': f"{sender['nome']} {sender['cognome']}" if sender else 'Utente',
                        'sender_avatar': sender.get('avatar', 'default.jpg') if sender else 'default.jpg',
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                        'message_type': message_type
                    }
                }
            return {'success': False, 'error': 'Errore invio messaggio'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_messages(self, group_id, user_id, limit=50, offset=0):
        try:
            is_member = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id), one=True)
            
            if not is_member:
                return []
            
            messages = db_manager.query("""
                SELECT sgm.*, u.nome, u.cognome, u.avatar
                FROM study_group_messages sgm
                JOIN utenti u ON sgm.sender_id = u.id
                WHERE sgm.group_id = %s
                ORDER BY sgm.created_at DESC
                LIMIT %s OFFSET %s
            """, (group_id, limit, offset))
            
            return list(reversed(messages)) if messages else []
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def add_task(self, group_id, created_by, title, description=None, due_date=None, priority='normal'):
        try:
            is_member = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, created_by), one=True)
            
            if not is_member:
                return {'success': False, 'error': 'Non sei membro del gruppo'}
            
            result = db_manager.query("""
                INSERT INTO study_group_tasks (group_id, created_by, title, description, due_date, priority)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (group_id, created_by, title, description, due_date, priority), one=True)
            
            if result:
                return {'success': True, 'task_id': result['id']}
            return {'success': False, 'error': 'Errore creazione task'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_tasks(self, group_id, user_id):
        try:
            is_member = db_manager.query("""
                SELECT id FROM study_group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id), one=True)
            
            if not is_member:
                return []
            
            tasks = db_manager.query("""
                SELECT sgt.*, 
                       u.nome || ' ' || u.cognome as creator_name,
                       cu.nome || ' ' || cu.cognome as completed_by_name
                FROM study_group_tasks sgt
                LEFT JOIN utenti u ON sgt.created_by = u.id
                LEFT JOIN utenti cu ON sgt.completed_by = cu.id
                WHERE sgt.group_id = %s
                ORDER BY sgt.is_completed, sgt.due_date, sgt.created_at DESC
            """, (group_id,))
            
            return tasks or []
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def toggle_task(self, task_id, user_id):
        try:
            task = db_manager.query("""
                SELECT sgt.*, sgm.id as member_check
                FROM study_group_tasks sgt
                JOIN study_group_members sgm ON sgt.group_id = sgm.group_id AND sgm.user_id = %s
                WHERE sgt.id = %s
            """, (user_id, task_id), one=True)
            
            if not task:
                return {'success': False, 'error': 'Task non trovato o non autorizzato'}
            
            new_status = not task['is_completed']
            
            if new_status:
                db_manager.query("""
                    UPDATE study_group_tasks 
                    SET is_completed = true, completed_by = %s, completed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (user_id, task_id))
            else:
                db_manager.query("""
                    UPDATE study_group_tasks 
                    SET is_completed = false, completed_by = NULL, completed_at = NULL
                    WHERE id = %s
                """, (task_id,))
            
            return {'success': True, 'is_completed': new_status}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_classmates(self, user_id, classe_id):
        try:
            classmates = db_manager.query("""
                SELECT id, nome, cognome, avatar
                FROM utenti
                WHERE classe_id = %s AND id != %s AND ruolo = 'studente' AND attivo = true
                ORDER BY cognome, nome
            """, (classe_id, user_id))
            return classmates or []
        except Exception as e:
            print(f"Error getting classmates: {e}")
            return []

study_groups_service = StudyGroupsService()
