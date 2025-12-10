"""
SKAJLA Dashboard Service
Centralizza logica business e query per dashboard multi-ruolo
"""

from typing import Dict, List, Optional, Any
from database_manager import db_manager
from datetime import datetime, timedelta


class DashboardService:
    """Service layer per consolidare query dashboard e logica business"""
    
    @staticmethod
    def get_user_daily_stats(user_id: int) -> Dict[str, int]:
        """
        Ottieni statistiche giornaliere per un utente
        Returns: {messages_today, ai_interactions_today}
        """
        messages_result = db_manager.query('''
            SELECT COUNT(*) as count FROM messaggi 
            WHERE utente_id = %s AND DATE(timestamp) = CURRENT_DATE
        ''', (user_id,), one=True)
        
        ai_result = db_manager.query('''
            SELECT COUNT(*) as count FROM ai_conversations 
            WHERE utente_id = %s AND DATE(timestamp) = CURRENT_DATE
        ''', (user_id,), one=True)
        
        return {
            'messages_today': messages_result.get('count') if messages_result else 0,
            'ai_interactions_today': ai_result.get('count') if ai_result else 0
        }
    
    @staticmethod
    def get_recent_achievements(user_id: int, limit: int = 3) -> List[Dict]:
        """Ottieni achievement recenti per un utente"""
        return db_manager.query('''
            SELECT achievement_id, xp_earned, unlocked_at
            FROM user_achievements
            WHERE user_id = %s
            ORDER BY unlocked_at DESC
            LIMIT %s
        ''', (user_id, limit)) or []
    
    @staticmethod
    def get_daily_analytics(user_id: int, days: int = 7) -> List[Dict]:
        """Ottieni analytics giornaliere per gli ultimi N giorni"""
        return db_manager.query('''
            SELECT date, quizzes_completed, messages_sent, ai_interactions, xp_earned
            FROM daily_analytics
            WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY date DESC
            LIMIT %s
        ''', (user_id, days, days)) or []
    
    @staticmethod
    def get_student_grades(user_id: int, limit: int = 50) -> Dict[str, Any]:
        """
        Ottieni voti e statistiche per uno studente
        Returns: {grades, grade_averages}
        """
        # Voti recenti
        grades = db_manager.query('''
            SELECT materia, voto, tipo_valutazione, data, note 
            FROM voti 
            WHERE studente_id = %s 
            ORDER BY data DESC 
            LIMIT %s
        ''', (user_id, limit)) or []
        
        # Medie per materia
        averages = db_manager.query('''
            SELECT materia, AVG(voto) as media, COUNT(*) as num_voti
            FROM voti
            WHERE studente_id = %s
            GROUP BY materia
        ''', (user_id,)) or []
        
        return {
            'grades': grades,
            'grade_averages': averages
        }
    
    @staticmethod
    def get_class_recent_activity(classe: str, school_id: int, limit: int = 10) -> List[Dict]:
        """Ottieni attività recente per una classe"""
        return db_manager.query('''
            SELECT u.nome, u.cognome, m.contenuto, m.timestamp
            FROM messaggi m
            JOIN utenti u ON m.utente_id = u.id
            JOIN chat c ON m.chat_id = c.id
            WHERE u.classe = %s AND u.scuola_id = %s AND c.scuola_id = %s 
            AND DATE(m.timestamp) = CURRENT_DATE
            ORDER BY m.timestamp DESC
            LIMIT %s
        ''', (classe, school_id, school_id, limit)) or []
    
    @staticmethod
    def get_school_stats(school_id: int) -> Dict[str, Any]:
        """
        Ottieni statistiche aggregate per una scuola (admin dashboard)
        Returns: {messages_today, users_by_role, active_chats}
        """
        # Messaggi oggi
        messages_result = db_manager.query('''
            SELECT COUNT(*) as count FROM messaggi m
            JOIN chat c ON m.chat_id = c.id
            WHERE c.scuola_id = %s AND DATE(m.timestamp) = CURRENT_DATE
        ''', (school_id,), one=True)
        
        # Utenti per ruolo
        role_stats = db_manager.query('''
            SELECT ruolo, COUNT(*) as count 
            FROM utenti 
            WHERE scuola_id = %s AND attivo = %s 
            GROUP BY ruolo
        ''', (school_id, True)) or []
        
        # Chat attive
        active_chats_result = db_manager.query('''
            SELECT COUNT(DISTINCT c.id) as count
            FROM chat c
            JOIN messaggi m ON c.id = m.chat_id
            WHERE c.scuola_id = %s AND DATE(m.timestamp) = CURRENT_DATE
        ''', (school_id,), one=True)
        
        return {
            'messages_today': messages_result.get('count') if messages_result else 0,
            'users_by_role': {r.get('ruolo'): r.get('count') for r in role_stats},
            'active_chats_today': active_chats_result.get('count') if active_chats_result else 0
        }
    
    @staticmethod
    def get_student_attendance(user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Ottieni statistiche presenze per uno studente
        Returns: {attendance_records, summary}
        """
        records = db_manager.query('''
            SELECT data, stato, note
            FROM presenze
            WHERE studente_id = %s AND data >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY data DESC
        ''', (user_id, days)) or []
        
        # Calcola summary
        total = len(records)
        presente = sum(1 for r in records if r.get('stato') == 'presente')
        assente = sum(1 for r in records if r.get('stato') == 'assente')
        
        return {
            'records': records,
            'summary': {
                'total_days': total,
                'presente': presente,
                'assente': assente,
                'percentage_presente': round((presente / total * 100) if total > 0 else 0, 1)
            }
        }
    
    @staticmethod
    def get_teacher_classes_summary(teacher_id: int, school_id: int) -> List[Dict]:
        """Ottieni sommario classi per un professore"""
        return db_manager.query('''
            SELECT DISTINCT c.nome as classe_nome, c.id as classe_id,
                   COUNT(DISTINCT u.id) as studenti_count
            FROM classi c
            LEFT JOIN utenti u ON u.classe_id = c.id AND u.ruolo = 'studente'
            WHERE c.scuola_id = %s AND c.professore_id = %s
            GROUP BY c.id, c.nome
            ORDER BY c.nome
        ''', (school_id, teacher_id)) or []


# Istanza globale
dashboard_service = DashboardService()
