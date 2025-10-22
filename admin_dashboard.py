"""
Dashboard Admin - Analytics e Monitoraggio Coaching Studenti
Per dirigenti scolastici e professori
"""

from database_manager import db_manager
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class AdminDashboard:
    """
    Genera analytics e statistiche per dashboard amministrativa
    """
    
    def __init__(self):
        self.sentiment_scores = {
            'proud': 1.0,
            'motivated': 0.8,
            'curious': 0.6,
            'neutral': 0.5,
            'confused': 0.3,
            'frustrated': 0.2,
            'insecure': 0.1,
            'anxious': -0.2,
            'overwhelmed': -0.4,
            'demotivated': -0.6,
            'exhausted': -0.8
        }
    
    def get_dashboard_overview(self, days: int = 30) -> Dict[str, Any]:
        """
        Genera overview completo dashboard admin
        """
        overview = {
            'period': f'Ultimi {days} giorni',
            'alerts': self.get_active_alerts(),
            'statistics': self.get_coaching_statistics(days),
            'top_issues': self.get_top_issues(days),
            'sentiment_distribution': self.get_sentiment_distribution(days),
            'effectiveness': self.get_coaching_effectiveness(days),
            'students_at_risk': self.get_students_at_risk()
        }
        
        return overview
    
    def get_active_alerts(self) -> List[Dict]:
        """Ottiene alert attivi sugli studenti"""
        alerts = []
        
        try:
            # Alert da interazioni coaching
            interactions = db_manager.query('''
                SELECT DISTINCT ON (user_id)
                    user_id, detected_category, detected_sentiment, 
                    user_data_snapshot, timestamp
                FROM coaching_interactions
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
                AND detected_category IN ('stress', 'burnout', 'motivazione')
                AND detected_sentiment LIKE '%demotivated%' 
                    OR detected_sentiment LIKE '%exhausted%'
                    OR detected_sentiment LIKE '%overwhelmed%'
                ORDER BY user_id, timestamp DESC
                LIMIT 20
            ''')
            
            for interaction in interactions:
                user = db_manager.query(
                    'SELECT nome, cognome FROM utenti WHERE id = %s',
                    (interaction['user_id'],), one=True
                )
                
                if user:
                    snapshot = interaction.get('user_data_snapshot')
                    if isinstance(snapshot, str):
                        snapshot = json.loads(snapshot)
                    
                    alerts.append({
                        'user_id': interaction['user_id'],
                        'user_name': f"{user['nome']} {user['cognome']}",
                        'type': interaction['detected_category'],
                        'sentiment': interaction['detected_sentiment'],
                        'active_alerts': snapshot.get('alerts', []) if snapshot else [],
                        'timestamp': interaction['timestamp']
                    })
        
        except Exception as e:
            print(f"Errore get_active_alerts: {e}")
        
        return alerts
    
    def get_coaching_statistics(self, days: int) -> Dict[str, Any]:
        """Statistiche generali coaching"""
        stats = {
            'total_interactions': 0,
            'daily_average': 0,
            'active_students': 0,
            'total_students': 0,
            'engagement_rate': 0
        }
        
        try:
            # Totale interazioni
            result = db_manager.query('''
                SELECT COUNT(*) as count FROM coaching_interactions
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ''' % days, one=True)
            
            stats['total_interactions'] = result['count'] if result else 0
            stats['daily_average'] = round(stats['total_interactions'] / days, 1)
            
            # Studenti attivi
            active = db_manager.query('''
                SELECT COUNT(DISTINCT user_id) as count 
                FROM coaching_interactions
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ''' % days, one=True)
            
            stats['active_students'] = active['count'] if active else 0
            
            # Totale studenti
            total = db_manager.query(
                "SELECT COUNT(*) as count FROM utenti WHERE ruolo='studente'",
                one=True
            )
            
            stats['total_students'] = total['count'] if total else 0
            
            if stats['total_students'] > 0:
                stats['engagement_rate'] = round(
                    (stats['active_students'] / stats['total_students']) * 100, 1
                )
        
        except Exception as e:
            print(f"Errore get_coaching_statistics: {e}")
        
        return stats
    
    def get_top_issues(self, days: int, limit: int = 5) -> List[Dict]:
        """Problemi più frequenti richiesti dagli studenti"""
        try:
            issues = db_manager.query('''
                SELECT detected_category, COUNT(*) as count
                FROM coaching_interactions
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND detected_category IS NOT NULL
                GROUP BY detected_category
                ORDER BY count DESC
                LIMIT %s
            ''' % (days, limit))
            
            category_labels = {
                'stress': '😰 Stress e ansia',
                'motivazione': '💪 Bassa motivazione',
                'organizzazione': '📅 Difficoltà organizzazione',
                'burnout': '🔥 Burnout',
                'obiettivi': '🎯 Definizione obiettivi',
                'sociale': '👥 Problemi sociali'
            }
            
            return [
                {
                    'category': i['detected_category'],
                    'label': category_labels.get(i['detected_category'], i['detected_category']),
                    'count': i['count']
                }
                for i in issues
            ]
        
        except Exception as e:
            print(f"Errore get_top_issues: {e}")
            return []
    
    def get_sentiment_distribution(self, days: int) -> Dict[str, Any]:
        """Distribuzione sentiment generale studenti"""
        distribution = {
            'positive': 0,
            'neutral': 0,
            'negative': 0,
            'average_score': 0.0
        }
        
        try:
            interactions = db_manager.query('''
                SELECT detected_sentiment FROM coaching_interactions
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND detected_sentiment IS NOT NULL
            ''' % days)
            
            if not interactions:
                return distribution
            
            scores = []
            for interaction in interactions:
                sentiments = interaction['detected_sentiment'].split(',')
                
                for sentiment in sentiments:
                    sentiment = sentiment.strip()
                    score = self.sentiment_scores.get(sentiment, 0.5)
                    scores.append(score)
                    
                    if score >= 0.5:
                        distribution['positive'] += 1
                    elif score >= 0:
                        distribution['neutral'] += 1
                    else:
                        distribution['negative'] += 1
            
            total = len(scores)
            if total > 0:
                distribution['average_score'] = round(sum(scores) / total, 2)
                distribution['positive'] = round((distribution['positive'] / total) * 100, 1)
                distribution['neutral'] = round((distribution['neutral'] / total) * 100, 1)
                distribution['negative'] = round((distribution['negative'] / total) * 100, 1)
        
        except Exception as e:
            print(f"Errore get_sentiment_distribution: {e}")
        
        return distribution
    
    def get_coaching_effectiveness(self, days: int) -> Dict[str, Any]:
        """Valuta efficacia coaching (studenti migliorati dopo interazione)"""
        effectiveness = {
            'improvement_rate': 0,
            'plans_created': 0,
            'plans_followed': 0,
            'avg_rating': 0.0
        }
        
        try:
            # Piani studio creati
            plans = db_manager.query('''
                SELECT COUNT(*) as count FROM study_plans
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ''' % days, one=True)
            
            effectiveness['plans_created'] = plans['count'] if plans else 0
            
            # Piani completati
            completed = db_manager.query('''
                SELECT COUNT(*) as count FROM study_plans
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND status = 'completed'
            ''' % days, one=True)
            
            effectiveness['plans_followed'] = completed['count'] if completed else 0
            
            # Calcola improvement rate (semplificato)
            # In un sistema reale, confronterebbe performance pre/post coaching
            if effectiveness['plans_created'] > 0:
                effectiveness['improvement_rate'] = round(
                    (effectiveness['plans_followed'] / effectiveness['plans_created']) * 100, 1
                )
        
        except Exception as e:
            print(f"Errore get_coaching_effectiveness: {e}")
        
        return effectiveness
    
    def get_students_at_risk(self, limit: int = 10) -> List[Dict]:
        """Identifica studenti a rischio che necessitano attenzione"""
        at_risk = []
        
        try:
            # Studenti con multiple interazioni negative recenti
            students = db_manager.query('''
                SELECT user_id, COUNT(*) as interaction_count,
                       string_agg(DISTINCT detected_category, ', ') as issues
                FROM coaching_interactions
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '14 days'
                AND (detected_sentiment LIKE '%demotivated%' 
                     OR detected_sentiment LIKE '%exhausted%'
                     OR detected_sentiment LIKE '%overwhelmed%'
                     OR detected_category = 'burnout')
                GROUP BY user_id
                HAVING COUNT(*) >= 2
                ORDER BY interaction_count DESC
                LIMIT %s
            ''', (limit,))
            
            for student in students:
                user = db_manager.query(
                    'SELECT nome, cognome FROM utenti WHERE id = %s',
                    (student['user_id'],), one=True
                )
                
                if user:
                    # Ottieni dati aggiuntivi
                    last_interaction = db_manager.query('''
                        SELECT user_data_snapshot FROM coaching_interactions
                        WHERE user_id = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    ''', (student['user_id'],), one=True)
                    
                    snapshot = {}
                    if last_interaction and last_interaction['user_data_snapshot']:
                        try:
                            snapshot = json.loads(last_interaction['user_data_snapshot'])
                        except:
                            pass
                    
                    at_risk.append({
                        'user_id': student['user_id'],
                        'name': f"{user['nome']} {user['cognome']}",
                        'negative_interactions': student['interaction_count'],
                        'issues': student['issues'],
                        'grade_trend': snapshot.get('academic', {}).get('trend', 'unknown'),
                        'alerts': snapshot.get('alerts', [])
                    })
        
        except Exception as e:
            print(f"Errore get_students_at_risk: {e}")
        
        return at_risk
    
    def get_class_overview(self, classe_id: int) -> Dict[str, Any]:
        """Overview classe specifica"""
        overview = {
            'class_id': classe_id,
            'total_students': 0,
            'avg_grade': 0.0,
            'avg_xp': 0,
            'coaching_usage': 0,
            'top_issues': []
        }
        
        try:
            # Studenti classe
            students = db_manager.query(
                'SELECT id FROM utenti WHERE classe_id = %s AND ruolo = %s',
                (classe_id, 'studente')
            )
            
            overview['total_students'] = len(students) if students else 0
            
            # Media voti classe
            avg = db_manager.query('''
                SELECT AVG(voto::float) as media
                FROM voti
                WHERE studente_id IN (
                    SELECT id FROM utenti WHERE classe_id = %s
                )
            ''', (classe_id,), one=True)
            
            overview['avg_grade'] = round(avg['media'], 1) if avg and avg['media'] else 0
            
        except Exception as e:
            print(f"Errore get_class_overview: {e}")
        
        return overview

# Istanza globale
admin_dashboard = AdminDashboard()
