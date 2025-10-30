"""
SKAILA Study Timer Service
Sistema timer Pomodoro integrato con gamification
"""

from database_manager import db_manager
from gamification import gamification_system
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

class StudyTimerService:
    """Gestisce timer studio e tracking sessioni"""
    
    def __init__(self):
        self.xp_per_minute = 2
        self.bonus_xp_long_session = 50
        self.long_session_threshold = 25 * 60
        
        self.session_types = {
            'focus': {
                'name': 'Sessione Focus',
                'icon': '🎯',
                'xp_multiplier': 1.0,
                'recommended_duration': 25
            },
            'pomodoro': {
                'name': 'Pomodoro',
                'icon': '🍅',
                'xp_multiplier': 1.2,
                'recommended_duration': 25
            },
            'deep_work': {
                'name': 'Deep Work',
                'icon': '🧠',
                'xp_multiplier': 1.5,
                'recommended_duration': 90
            },
            'review': {
                'name': 'Ripasso',
                'icon': '📚',
                'xp_multiplier': 0.8,
                'recommended_duration': 15
            }
        }
    
    def start_session(self, user_id: int, subject: str = None, session_type: str = 'focus') -> Dict[str, Any]:
        """Inizia nuova sessione studio"""
        try:
            existing = db_manager.query(
                'SELECT id FROM study_sessions WHERE user_id = %s AND status = %s',
                (user_id, 'active'),
                one=True
            )
            
            if existing:
                return {
                    'success': False,
                    'error': 'Hai già una sessione attiva. Completala prima di iniziarne una nuova.'
                }
            
            session_id = db_manager.execute(
                '''INSERT INTO study_sessions 
                   (user_id, subject, session_type, start_time, status)
                   VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
                   RETURNING id''',
                (user_id, subject, session_type, 'active'),
                return_id=True
            )
            
            return {
                'success': True,
                'session_id': session_id,
                'start_time': datetime.now().isoformat(),
                'session_type': session_type,
                'subject': subject,
                'message': f"Sessione {self.session_types[session_type]['name']} iniziata! 🚀"
            }
        
        except Exception as e:
            print(f"Errore start_session: {e}")
            return {'success': False, 'error': str(e)}
    
    def pause_session(self, user_id: int) -> Dict[str, Any]:
        """Mette in pausa sessione attiva"""
        try:
            session = db_manager.query(
                'SELECT id FROM study_sessions WHERE user_id = %s AND status = %s',
                (user_id, 'active'),
                one=True
            )
            
            if not session:
                return {'success': False, 'error': 'Nessuna sessione attiva'}
            
            pause_start = datetime.now()
            db_manager.execute(
                'UPDATE study_sessions SET status = %s, notes = %s WHERE id = %s',
                ('paused', pause_start.isoformat(), session['id'])
            )
            
            return {
                'success': True,
                'message': 'Sessione in pausa ⏸️'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def resume_session(self, user_id: int) -> Dict[str, Any]:
        """Riprende sessione in pausa"""
        try:
            session = db_manager.query(
                'SELECT id, notes, paused_duration FROM study_sessions WHERE user_id = %s AND status = %s',
                (user_id, 'paused'),
                one=True
            )
            
            if not session:
                return {'success': False, 'error': 'Nessuna sessione in pausa'}
            
            pause_start_iso = session.get('notes', '')
            current_paused = session.get('paused_duration', 0) or 0
            
            if pause_start_iso:
                try:
                    pause_start = datetime.fromisoformat(pause_start_iso)
                    pause_duration = int((datetime.now() - pause_start).total_seconds())
                    new_paused_duration = current_paused + pause_duration
                except (ValueError, TypeError):
                    new_paused_duration = current_paused
            else:
                new_paused_duration = current_paused
            
            db_manager.execute(
                'UPDATE study_sessions SET status = %s, paused_duration = %s, notes = NULL WHERE id = %s',
                ('active', new_paused_duration, session['id'])
            )
            
            return {
                'success': True,
                'message': 'Sessione ripresa ▶️'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_session(self, user_id: int, notes: str = None) -> Dict[str, Any]:
        """Termina sessione e calcola XP"""
        try:
            session = db_manager.query(
                '''SELECT id, subject, session_type, start_time, paused_duration, status, notes
                   FROM study_sessions 
                   WHERE user_id = %s AND status IN (%s, %s)
                   ORDER BY start_time DESC LIMIT 1''',
                (user_id, 'active', 'paused'),
                one=True
            )
            
            if not session:
                return {'success': False, 'error': 'Nessuna sessione attiva'}
            
            end_time = datetime.now()
            start_time = session['start_time']
            
            total_seconds = int((end_time - start_time).total_seconds())
            paused_duration = session.get('paused_duration', 0) or 0
            
            if session['status'] == 'paused' and session.get('notes'):
                try:
                    pause_start = datetime.fromisoformat(session['notes'])
                    current_pause_duration = int((end_time - pause_start).total_seconds())
                    paused_duration += current_pause_duration
                except (ValueError, TypeError):
                    pass
            
            active_seconds = max(0, total_seconds - paused_duration)
            
            active_minutes = active_seconds / 60
            session_type_data = self.session_types.get(session['session_type'], self.session_types['focus'])
            
            base_xp = int(active_minutes * self.xp_per_minute)
            multiplier_xp = int(base_xp * session_type_data['xp_multiplier'])
            
            bonus_xp = 0
            if active_seconds >= self.long_session_threshold:
                bonus_xp = self.bonus_xp_long_session
            
            total_xp = multiplier_xp + bonus_xp
            
            db_manager.execute(
                '''UPDATE study_sessions 
                   SET end_time = %s, duration_seconds = %s, 
                       status = %s, xp_earned = %s, notes = %s
                   WHERE id = %s''',
                (end_time, active_seconds, 'completed', total_xp, notes, session['id'])
            )
            
            if total_xp > 0:
                gamification_system.award_xp(
                    user_id, 
                    total_xp, 
                    f"study_session_{session['session_type']}", 
                    f"Sessione studio {session['subject'] or 'generale'}"
                )
            
            duration_formatted = self._format_duration(active_seconds)
            
            return {
                'success': True,
                'duration': active_seconds,
                'duration_formatted': duration_formatted,
                'xp_earned': total_xp,
                'subject': session['subject'],
                'session_type': session['session_type'],
                'bonus_applied': bonus_xp > 0,
                'message': f"Sessione completata! +{total_xp} XP guadagnati! 🎉"
            }
        
        except Exception as e:
            print(f"Errore stop_session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_active_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Ottiene sessione attualmente attiva"""
        try:
            session = db_manager.query(
                '''SELECT id, subject, session_type, start_time, status, paused_duration, notes
                   FROM study_sessions 
                   WHERE user_id = %s AND status IN (%s, %s)
                   ORDER BY start_time DESC LIMIT 1''',
                (user_id, 'active', 'paused'),
                one=True
            )
            
            if not session:
                return None
            
            elapsed_seconds = int((datetime.now() - session['start_time']).total_seconds())
            paused_duration = session.get('paused_duration', 0) or 0
            
            if session['status'] == 'paused' and session.get('notes'):
                try:
                    pause_start = datetime.fromisoformat(session['notes'])
                    current_pause_duration = int((datetime.now() - pause_start).total_seconds())
                    paused_duration += current_pause_duration
                except (ValueError, TypeError):
                    pass
            
            active_seconds = max(0, elapsed_seconds - paused_duration)
            
            return {
                'id': session['id'],
                'subject': session['subject'],
                'session_type': session['session_type'],
                'status': session['status'],
                'start_time': session['start_time'].isoformat(),
                'elapsed_seconds': elapsed_seconds,
                'active_seconds': active_seconds,
                'is_paused': session['status'] == 'paused'
            }
        
        except Exception as e:
            print(f"Errore get_active_session: {e}")
            return None
    
    def get_user_stats(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Ottiene statistiche sessioni utente"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            stats = db_manager.query(
                '''SELECT 
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(duration_seconds), 0) as total_seconds,
                    COALESCE(SUM(xp_earned), 0) as total_xp,
                    COALESCE(AVG(duration_seconds), 0) as avg_duration,
                    COUNT(DISTINCT DATE(start_time)) as active_days
                   FROM study_sessions
                   WHERE user_id = %s AND status = %s AND start_time >= %s''',
                (user_id, 'completed', since_date),
                one=True
            )
            
            sessions_by_subject = db_manager.query(
                '''SELECT subject, COUNT(*) as count, SUM(duration_seconds) as total_time
                   FROM study_sessions
                   WHERE user_id = %s AND status = %s AND start_time >= %s AND subject IS NOT NULL
                   GROUP BY subject
                   ORDER BY count DESC
                   LIMIT 5''',
                (user_id, 'completed', since_date)
            )
            
            total_hours = stats['total_seconds'] / 3600
            avg_minutes = stats['avg_duration'] / 60
            
            return {
                'total_sessions': stats['total_sessions'],
                'total_hours': round(total_hours, 1),
                'total_minutes': int(stats['total_seconds'] / 60),
                'total_xp': stats['total_xp'],
                'avg_duration_minutes': int(avg_minutes),
                'active_days': stats['active_days'],
                'sessions_by_subject': [
                    {
                        'subject': s['subject'],
                        'count': s['count'],
                        'hours': round(s['total_time'] / 3600, 1)
                    }
                    for s in sessions_by_subject
                ]
            }
        
        except Exception as e:
            print(f"Errore get_user_stats: {e}")
            return {
                'total_sessions': 0,
                'total_hours': 0,
                'total_minutes': 0,
                'total_xp': 0,
                'avg_duration_minutes': 0,
                'active_days': 0,
                'sessions_by_subject': []
            }
    
    def get_recent_sessions(self, user_id: int, limit: int = 10) -> list:
        """Ottiene sessioni recenti"""
        try:
            sessions = db_manager.query(
                '''SELECT id, subject, session_type, start_time, end_time, 
                          duration_seconds, xp_earned, notes, status
                   FROM study_sessions
                   WHERE user_id = %s
                   ORDER BY start_time DESC
                   LIMIT %s''',
                (user_id, limit)
            )
            
            return [
                {
                    'id': s['id'],
                    'subject': s['subject'],
                    'session_type': s['session_type'],
                    'session_type_name': self.session_types.get(s['session_type'], {}).get('name', s['session_type']),
                    'session_type_icon': self.session_types.get(s['session_type'], {}).get('icon', '📚'),
                    'start_time': s['start_time'].strftime('%d/%m/%Y %H:%M'),
                    'duration_formatted': self._format_duration(s['duration_seconds']) if s['duration_seconds'] else '-',
                    'xp_earned': s['xp_earned'],
                    'notes': s['notes'],
                    'status': s['status']
                }
                for s in sessions
            ]
        
        except Exception as e:
            print(f"Errore get_recent_sessions: {e}")
            return []
    
    def _format_duration(self, seconds: int) -> str:
        """Formatta durata in formato leggibile"""
        if seconds < 60:
            return f"{seconds}s"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            return f"{minutes}min {remaining_seconds}s" if remaining_seconds > 0 else f"{minutes}min"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        return f"{hours}h {remaining_minutes}min"

study_timer = StudyTimerService()
print("✅ Study Timer Service inizializzato")
