"""
SKAJLA - Report Generator
Sistema automatico per generazione report settimanali e mensili
"""

from database_manager import db_manager
from datetime import datetime, timedelta
import json

class ReportGenerator:
    """Genera report aziendali con statistiche SKAJLA"""
    
    def __init__(self):
        self.db = db_manager
    
    def generate_weekly_report(self, school_id=None):
        """
        Genera report settimanale (lunedì-domenica)
        
        Returns:
            dict: Dizionario con tutte le statistiche settimanali
        """
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())  # Lunedì
        week_end = week_start + timedelta(days=6)  # Domenica
        
        report = {
            'type': 'weekly',
            'period': f"{week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')}",
            'generated_at': today.strftime('%d/%m/%Y %H:%M'),
            'statistics': {}
        }
        
        # 1. Statistiche Utenti
        report['statistics']['users'] = self._get_user_stats(week_start, week_end, school_id)
        
        # 2. Statistiche Engagement
        report['statistics']['engagement'] = self._get_engagement_stats(week_start, week_end, school_id)
        
        # 3. Statistiche Gamification
        report['statistics']['gamification'] = self._get_gamification_stats(week_start, week_end, school_id)
        
        # 4. Statistiche AI Coach
        report['statistics']['ai_coach'] = self._get_ai_coach_stats(week_start, week_end, school_id)
        
        # 5. Statistiche Accademiche
        report['statistics']['academic'] = self._get_academic_stats(week_start, week_end, school_id)
        
        # 6. Top Performers
        report['statistics']['top_performers'] = self._get_top_performers(week_start, week_end, school_id)
        
        # 7. Alerts e Criticità
        report['statistics']['alerts'] = self._get_alerts(week_start, week_end, school_id)
        
        return report
    
    def generate_monthly_report(self, school_id=None):
        """
        Genera report mensile (1° - ultimo giorno del mese)
        
        Returns:
            dict: Dizionario con tutte le statistiche mensili
        """
        today = datetime.now()
        month_start = today.replace(day=1)
        
        # Calcola ultimo giorno del mese
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        report = {
            'type': 'monthly',
            'period': f"{month_start.strftime('%B %Y')}",
            'generated_at': today.strftime('%d/%m/%Y %H:%M'),
            'statistics': {}
        }
        
        # Stesse statistiche ma su periodo mensile
        report['statistics']['users'] = self._get_user_stats(month_start, month_end, school_id)
        report['statistics']['engagement'] = self._get_engagement_stats(month_start, month_end, school_id)
        report['statistics']['gamification'] = self._get_gamification_stats(month_start, month_end, school_id)
        report['statistics']['ai_coach'] = self._get_ai_coach_stats(month_start, month_end, school_id)
        report['statistics']['academic'] = self._get_academic_stats(month_start, month_end, school_id)
        report['statistics']['top_performers'] = self._get_top_performers(month_start, month_end, school_id)
        report['statistics']['alerts'] = self._get_alerts(month_start, month_end, school_id)
        
        # Statistiche aggiuntive per report mensile
        report['statistics']['trends'] = self._get_monthly_trends(month_start, month_end, school_id)
        report['statistics']['comparison'] = self._get_month_comparison(school_id)
        
        return report
    
    def _get_user_stats(self, start_date, end_date, school_id=None):
        """Statistiche utenti"""
        try:
            filter_school = "AND scuola_id = %s" if school_id else ""
            params = [start_date, end_date] + ([school_id] if school_id else [])
            
            # Nuovi registrati
            new_users = self.db.query(f'''
                SELECT COUNT(*) as count 
                FROM utenti 
                WHERE data_creazione >= %s AND data_creazione <= %s {filter_school}
            ''', tuple(params), one=True)
            
            # Utenti attivi (hanno fatto almeno un'azione)
            active_users = self.db.query(f'''
                SELECT COUNT(DISTINCT user_id) as count
                FROM user_gamification
                WHERE last_activity >= %s AND last_activity <= %s
                {filter_school.replace('scuola_id', 'scuola_id')}
            ''', tuple(params), one=True)
            
            # Totale utenti
            total_users = self.db.query(f'''
                SELECT COUNT(*) as count FROM utenti WHERE 1=1 {filter_school}
            ''', (school_id,) if school_id else (), one=True)
            
            # Utenti per ruolo
            users_by_role = self.db.query(f'''
                SELECT ruolo, COUNT(*) as count 
                FROM utenti 
                WHERE 1=1 {filter_school}
                GROUP BY ruolo
            ''', (school_id,) if school_id else ())
            
            return {
                'new_registrations': new_users['count'] or 0,
                'active_users': active_users['count'] or 0,
                'total_users': total_users['count'] or 0,
                'by_role': {row['ruolo']: row['count'] for row in users_by_role},
                'activity_rate': round((active_users['count'] or 0) / max(total_users['count'], 1) * 100, 1)
            }
        except Exception as e:
            print(f"Errore _get_user_stats: {e}")
            return {'new_registrations': 0, 'active_users': 0, 'total_users': 0, 'by_role': {}, 'activity_rate': 0}
    
    def _get_engagement_stats(self, start_date, end_date, school_id=None):
        """Statistiche engagement piattaforma"""
        try:
            filter_school = "AND c.scuola_id = %s" if school_id else ""
            params = [start_date, end_date] + ([school_id] if school_id else [])
            
            # Messaggi inviati
            messages_sent = self.db.query(f'''
                SELECT COUNT(*) as count 
                FROM messaggi m
                JOIN chat c ON m.chat_id = c.id
                WHERE m.timestamp >= %s AND m.timestamp <= %s {filter_school}
            ''', tuple(params), one=True)
            
            # Login giornalieri medi
            avg_daily_logins = self.db.query(f'''
                SELECT COUNT(DISTINCT user_id) / 7.0 as avg_logins
                FROM user_gamification
                WHERE last_activity >= %s AND last_activity <= %s
            ''', (start_date, end_date), one=True)
            
            return {
                'messages_sent': messages_sent['count'] or 0,
                'avg_daily_logins': round(avg_daily_logins['avg_logins'] or 0, 1),
                'engagement_score': self._calculate_engagement_score(start_date, end_date, school_id)
            }
        except Exception as e:
            print(f"Errore _get_engagement_stats: {e}")
            return {'messages_sent': 0, 'avg_daily_logins': 0, 'engagement_score': 0}
    
    def _get_gamification_stats(self, start_date, end_date, school_id=None):
        """Statistiche gamification"""
        try:
            # XP totali guadagnati nel periodo
            total_xp = self.db.query('''
                SELECT COALESCE(SUM(xp_earned), 0) as total_xp
                FROM daily_analytics
                WHERE date >= %s AND date <= %s
            ''', (start_date, end_date), one=True)
            
            # Media XP per studente
            avg_xp = self.db.query('''
                SELECT COALESCE(AVG(total_xp), 0) as avg_xp
                FROM user_gamification
            ''', one=True)
            
            # Studenti con streak attivo > 3 giorni
            active_streaks = self.db.query('''
                SELECT COUNT(*) as count
                FROM user_gamification
                WHERE current_streak >= 3
            ''', one=True)
            
            # Badge assegnati nel periodo
            badges_earned = self.db.query('''
                SELECT COUNT(*) as count
                FROM user_badges
                WHERE earned_at >= %s AND earned_at <= %s
            ''', (start_date, end_date), one=True)
            
            return {
                'total_xp_earned': int(total_xp['total_xp'] or 0),
                'avg_xp_per_student': round(avg_xp['avg_xp'] or 0, 1),
                'active_streaks': active_streaks['count'] or 0,
                'badges_earned': badges_earned['count'] or 0
            }
        except Exception as e:
            print(f"Errore _get_gamification_stats: {e}")
            return {'total_xp_earned': 0, 'avg_xp_per_student': 0, 'active_streaks': 0, 'badges_earned': 0}
    
    def _get_ai_coach_stats(self, start_date, end_date, school_id=None):
        """Statistiche AI Coach"""
        try:
            # Interazioni totali
            total_interactions = self.db.query('''
                SELECT COUNT(*) as count
                FROM coaching_interactions
                WHERE timestamp >= %s AND timestamp <= %s
            ''', (start_date, end_date), one=True)
            
            # Categorie più richieste
            top_categories = self.db.query('''
                SELECT category, COUNT(*) as count
                FROM coaching_interactions
                WHERE timestamp >= %s AND timestamp <= %s
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            ''', (start_date, end_date))
            
            # Sentiment distribution
            sentiment_dist = self.db.query('''
                SELECT sentiment, COUNT(*) as count
                FROM coaching_interactions
                WHERE timestamp >= %s AND timestamp <= %s
                GROUP BY sentiment
            ''', (start_date, end_date))
            
            return {
                'total_interactions': total_interactions['count'] or 0,
                'top_categories': [{'category': row['category'], 'count': row['count']} for row in top_categories],
                'sentiment_distribution': {row['sentiment']: row['count'] for row in sentiment_dist}
            }
        except Exception as e:
            print(f"Errore _get_ai_coach_stats: {e}")
            return {'total_interactions': 0, 'top_categories': [], 'sentiment_distribution': {}}
    
    def _get_academic_stats(self, start_date, end_date, school_id=None):
        """Statistiche accademiche"""
        try:
            # Media voti del periodo
            avg_grade = self.db.query('''
                SELECT COALESCE(AVG(voto), 0) as avg_grade
                FROM voti
                WHERE data >= %s AND data <= %s
            ''', (start_date, end_date), one=True)
            
            # Voti registrati
            grades_count = self.db.query('''
                SELECT COUNT(*) as count
                FROM voti
                WHERE data >= %s AND data <= %s
            ''', (start_date, end_date), one=True)
            
            # Tasso di presenza
            attendance = self.db.query('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN presente = true THEN 1 ELSE 0 END) as present
                FROM presenze
                WHERE data >= %s AND data <= %s
            ''', (start_date, end_date), one=True)
            
            attendance_rate = 0
            if attendance and attendance['total'] > 0:
                attendance_rate = round((attendance['present'] / attendance['total']) * 100, 1)
            
            return {
                'avg_grade': round(avg_grade['avg_grade'] or 0, 2),
                'grades_recorded': grades_count['count'] or 0,
                'attendance_rate': attendance_rate
            }
        except Exception as e:
            print(f"Errore _get_academic_stats: {e}")
            return {'avg_grade': 0, 'grades_recorded': 0, 'attendance_rate': 0}
    
    def _get_top_performers(self, start_date, end_date, school_id=None):
        """Top 10 studenti per XP"""
        try:
            top_students = self.db.query('''
                SELECT 
                    u.nome || ' ' || u.cognome as name,
                    ug.total_xp,
                    ug.current_level,
                    ug.current_streak
                FROM user_gamification ug
                JOIN utenti u ON ug.user_id = u.id
                WHERE u.ruolo = 'studente'
                ORDER BY ug.total_xp DESC
                LIMIT 10
            ''')
            
            return [
                {
                    'name': row['name'],
                    'xp': row['total_xp'],
                    'level': row['current_level'],
                    'streak': row['current_streak']
                }
                for row in top_students
            ]
        except Exception as e:
            print(f"Errore _get_top_performers: {e}")
            return []
    
    def _get_alerts(self, start_date, end_date, school_id=None):
        """Alert e criticità"""
        try:
            alerts = []
            
            # Studenti con sentiment negativo ricorrente
            negative_sentiment = self.db.query('''
                SELECT 
                    u.nome || ' ' || u.cognome as name,
                    COUNT(*) as neg_count
                FROM coaching_interactions ci
                JOIN utenti u ON ci.user_id = u.id
                WHERE ci.sentiment IN ('anxious', 'stressed', 'overwhelmed')
                  AND ci.timestamp >= %s AND ci.timestamp <= %s
                GROUP BY u.id, u.nome, u.cognome
                HAVING COUNT(*) >= 3
                ORDER BY neg_count DESC
                LIMIT 5
            ''', (start_date, end_date))
            
            for row in negative_sentiment:
                alerts.append({
                    'type': 'emotional_support_needed',
                    'student': row['name'],
                    'details': f"{row['neg_count']} interazioni con sentiment negativo"
                })
            
            # Studenti con bassa presenza
            low_attendance = self.db.query('''
                SELECT 
                    u.nome || ' ' || u.cognome as name,
                    COUNT(CASE WHEN p.presente = false THEN 1 END) as absences
                FROM presenze p
                JOIN utenti u ON p.studente_id = u.id
                WHERE p.data >= %s AND p.data <= %s
                GROUP BY u.id, u.nome, u.cognome
                HAVING COUNT(CASE WHEN p.presente = false THEN 1 END) >= 3
                LIMIT 5
            ''', (start_date, end_date))
            
            for row in low_attendance:
                alerts.append({
                    'type': 'low_attendance',
                    'student': row['name'],
                    'details': f"{row['absences']} assenze nel periodo"
                })
            
            return alerts
        except Exception as e:
            print(f"Errore _get_alerts: {e}")
            return []
    
    def _get_monthly_trends(self, month_start, month_end, school_id=None):
        """Trend mensili (solo per report mensile)"""
        try:
            # XP trend settimanale
            weekly_xp = self.db.query('''
                SELECT 
                    EXTRACT(WEEK FROM date) as week,
                    SUM(xp_earned) as total_xp
                FROM daily_analytics
                WHERE date >= %s AND date <= %s
                GROUP BY EXTRACT(WEEK FROM date)
                ORDER BY week
            ''', (month_start, month_end))
            
            return {
                'weekly_xp_trend': [{'week': int(row['week']), 'xp': int(row['total_xp'])} for row in weekly_xp]
            }
        except Exception as e:
            print(f"Errore _get_monthly_trends: {e}")
            return {'weekly_xp_trend': []}
    
    def _get_month_comparison(self, school_id=None):
        """Confronto con mese precedente"""
        try:
            current_month_start = datetime.now().replace(day=1)
            prev_month_end = current_month_start - timedelta(days=1)
            prev_month_start = prev_month_end.replace(day=1)
            
            # XP mese corrente
            current_xp = self.db.query('''
                SELECT COALESCE(SUM(xp_earned), 0) as total
                FROM daily_analytics
                WHERE date >= %s
            ''', (current_month_start,), one=True)
            
            # XP mese precedente
            prev_xp = self.db.query('''
                SELECT COALESCE(SUM(xp_earned), 0) as total
                FROM daily_analytics
                WHERE date >= %s AND date <= %s
            ''', (prev_month_start, prev_month_end), one=True)
            
            growth = 0
            if prev_xp['total'] > 0:
                growth = round(((current_xp['total'] - prev_xp['total']) / prev_xp['total']) * 100, 1)
            
            return {
                'xp_growth': growth,
                'current_month_xp': int(current_xp['total']),
                'previous_month_xp': int(prev_xp['total'])
            }
        except Exception as e:
            print(f"Errore _get_month_comparison: {e}")
            return {'xp_growth': 0, 'current_month_xp': 0, 'previous_month_xp': 0}
    
    def _calculate_engagement_score(self, start_date, end_date, school_id=None):
        """Calcola punteggio engagement (0-100)"""
        try:
            # Fattori: login rate, messaggi, AI interactions, XP guadagnati
            total_users = self.db.query('SELECT COUNT(*) as count FROM utenti WHERE ruolo=\'studente\'', one=True)
            active_users = self.db.query('''
                SELECT COUNT(DISTINCT user_id) as count
                FROM user_gamification
                WHERE last_activity >= %s
            ''', (start_date,), one=True)
            
            if total_users['count'] == 0:
                return 0
            
            activity_rate = (active_users['count'] / total_users['count']) * 100
            
            # Semplice scoring basato su activity rate
            return round(min(activity_rate, 100), 1)
        except Exception as e:
            print(f"Errore _calculate_engagement_score: {e}")
            return 0
    
    def save_report(self, report_data, recipient_email):
        """Salva report nel database"""
        try:
            self.db.execute('''
                INSERT INTO business_reports 
                (report_type, period, data, recipient_email, generated_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                report_data['type'],
                report_data['period'],
                json.dumps(report_data),
                recipient_email,
                datetime.now()
            ))
            print(f"✅ Report {report_data['type']} salvato con successo")
        except Exception as e:
            print(f"Errore save_report: {e}")

# Istanza globale
report_generator = ReportGenerator()
