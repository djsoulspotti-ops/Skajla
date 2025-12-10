"""
SKAJLA Subject Progress Analytics
Tracking dettagliato progressi per materia, analytics, insights
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from database_manager import db_manager
import json

class SubjectProgressAnalytics:
    """Analytics progressi materie"""
    
    def get_subject_overview(self, user_id: int, subject: str) -> Dict:
        """Overview completo materia"""
        
        # Progress generale
        progress = db_manager.query('''
            SELECT * FROM student_subject_progress 
            WHERE user_id = ? AND subject = ?
        ''', (user_id, subject), one=True)
        
        if not progress:
            return self._create_empty_progress(subject)
        
        # Quiz recenti (ultimi 10)
        recent_quiz = db_manager.query('''
            SELECT topic, difficulty, is_correct, time_taken, timestamp
            FROM student_quiz_history
            WHERE user_id = ? AND subject = ?
            ORDER BY timestamp DESC LIMIT 10
        ''', (user_id, subject))
        
        # Calcola trend
        trend = self._calculate_trend(recent_quiz)
        
        # Topic analytics
        topic_stats = self._get_topic_statistics(user_id, subject)
        
        # XP history (ultimi 30 giorni)
        xp_history = self._get_xp_history(user_id, subject, days=30)
        
        return {
            'subject': subject,
            'total_quizzes': progress['total_quizzes'],
            'correct_quizzes': progress['correct_quizzes'],
            'accuracy': round(progress['accuracy_percentage'], 1),
            'total_xp': progress['total_xp'],
            'current_level': self._xp_to_level(progress['total_xp']),
            'xp_to_next_level': self._xp_to_next_level(progress['total_xp']),
            'trend': trend,  # 'improving', 'stable', 'declining'
            'topics': topic_stats,
            'xp_history': xp_history,
            'weak_topics': progress['topics_weak'].split(',') if progress['topics_weak'] else [],
            'strong_topics': progress['topics_strong'].split(',') if progress['topics_strong'] else [],
            'last_activity': progress['last_activity_date']
        }
    
    def get_all_subjects_summary(self, user_id: int) -> List[Dict]:
        """Summary tutti i soggetti"""
        
        subjects = db_manager.query('''
            SELECT * FROM student_subject_progress 
            WHERE user_id = ?
            ORDER BY total_xp DESC
        ''', (user_id,))
        
        result = []
        for subj in subjects:
            # Get recent performance
            recent = db_manager.query('''
                SELECT is_correct FROM student_quiz_history
                WHERE user_id = ? AND subject = ?
                ORDER BY timestamp DESC LIMIT 5
            ''', (user_id, subj['subject']))
            
            recent_accuracy = (sum(1 for r in recent if r['is_correct']) / len(recent) * 100) if recent else 0
            
            result.append({
                'subject': subj['subject'],
                'total_xp': subj['total_xp'],
                'accuracy': round(subj['accuracy_percentage'], 1),
                'recent_accuracy': round(recent_accuracy, 1),
                'total_quizzes': subj['total_quizzes'],
                'level': self._xp_to_level(subj['total_xp']),
                'needs_attention': recent_accuracy < 60
            })
        
        return result
    
    def get_weak_areas(self, user_id: int, subject: str) -> List[Dict]:
        """Identifica aree deboli per focus"""
        
        # Topic con bassa accuracy
        weak_topics = db_manager.query('''
            SELECT 
                topic,
                COUNT(*) as attempts,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                AVG(time_taken) as avg_time
            FROM student_quiz_history
            WHERE user_id = ? AND subject = ?
            GROUP BY topic
            HAVING COUNT(*) >= 3 AND (SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) < 70
            ORDER BY (SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) ASC
        ''', (user_id, subject))
        
        result = []
        for topic in weak_topics:
            accuracy = (topic['correct'] / topic['attempts']) * 100
            result.append({
                'topic': topic['topic'],
                'attempts': topic['attempts'],
                'accuracy': round(accuracy, 1),
                'avg_time': int(topic['avg_time']),
                'priority': 'alta' if accuracy < 50 else 'media'
            })
        
        return result
    
    def get_improvement_suggestions(self, user_id: int, subject: str) -> List[str]:
        """Suggerimenti personalizzati miglioramento"""
        
        suggestions = []
        
        # Get overview
        overview = self.get_subject_overview(user_id, subject)
        
        # Accuracy bassa
        if overview['accuracy'] < 60:
            suggestions.append(f"📚 La tua precisione in {subject} è bassa ({overview['accuracy']}%). Concentrati sulle basi!")
        
        # Trend negativo
        if overview['trend'] == 'declining':
            suggestions.append(f"📉 Le tue performance in {subject} stanno calando. Ripassa gli argomenti recenti.")
        
        # Topic deboli
        if overview['weak_topics']:
            topics_str = ', '.join(overview['weak_topics'][:3])
            suggestions.append(f"🎯 Focus su: {topics_str}. Fai più quiz su questi argomenti!")
        
        # Pochi quiz
        if overview['total_quizzes'] < 10:
            suggestions.append(f"💪 Fai più pratica! Hai completato solo {overview['total_quizzes']} quiz in {subject}.")
        
        # Suggerisci peer help se disponibile
        from social_learning_system import social_learning
        helpers = social_learning.find_peer_help(user_id, subject)
        if helpers and overview['accuracy'] < 70:
            suggestions.append(f"👥 {helpers[0]['nome']} è forte in {subject}! Chiedi aiuto.")
        
        # Default positive se tutto ok
        if not suggestions:
            suggestions.append(f"🌟 Ottimo lavoro in {subject}! Mantieni questo ritmo!")
        
        return suggestions
    
    def get_learning_path(self, user_id: int, subject: str) -> List[Dict]:
        """Percorso apprendimento personalizzato"""
        
        # Get weak areas
        weak_areas = self.get_weak_areas(user_id, subject)
        
        # Get all topics statistics
        all_topics = self._get_topic_statistics(user_id, subject)
        
        # Create learning path
        path = []
        
        # 1. Review weak topics first
        for weak in weak_areas[:3]:  # Top 3 weak
            path.append({
                'step': len(path) + 1,
                'action': 'review',
                'topic': weak['topic'],
                'difficulty': 'facile',
                'reason': f"Accuracy bassa ({weak['accuracy']}%)",
                'estimated_quizzes': 5
            })
        
        # 2. Practice medium topics
        medium_topics = [t for t in all_topics if 70 <= t['accuracy'] < 85]
        for topic in medium_topics[:2]:
            path.append({
                'step': len(path) + 1,
                'action': 'practice',
                'topic': topic['topic'],
                'difficulty': 'medio',
                'reason': "Consolida conoscenze",
                'estimated_quizzes': 3
            })
        
        # 3. Challenge on strong topics
        strong_topics = [t for t in all_topics if t['accuracy'] >= 85]
        for topic in strong_topics[:2]:
            path.append({
                'step': len(path) + 1,
                'action': 'challenge',
                'topic': topic['topic'],
                'difficulty': 'difficile',
                'reason': "Raggiungi l'eccellenza!",
                'estimated_quizzes': 2
            })
        
        return path
    
    def _get_topic_statistics(self, user_id: int, subject: str) -> List[Dict]:
        """Statistiche per topic"""
        
        topics = db_manager.query('''
            SELECT 
                topic,
                COUNT(*) as total,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                AVG(time_taken) as avg_time
            FROM student_quiz_history
            WHERE user_id = ? AND subject = ?
            GROUP BY topic
            ORDER BY topic
        ''', (user_id, subject))
        
        result = []
        for topic in topics:
            accuracy = (topic['correct'] / topic['total']) * 100 if topic['total'] > 0 else 0
            result.append({
                'topic': topic['topic'],
                'total_quizzes': topic['total'],
                'accuracy': round(accuracy, 1),
                'avg_time': int(topic['avg_time']) if topic['avg_time'] else 0
            })
        
        return result
    
    def _calculate_trend(self, recent_quiz: List[Dict]) -> str:
        """Calcola trend performance"""
        
        if len(recent_quiz) < 5:
            return 'insufficient_data'
        
        # Split in two halves
        mid = len(recent_quiz) // 2
        recent_half = recent_quiz[:mid]
        older_half = recent_quiz[mid:]
        
        recent_acc = sum(1 for q in recent_half if q['is_correct']) / len(recent_half) * 100
        older_acc = sum(1 for q in older_half if q['is_correct']) / len(older_half) * 100
        
        diff = recent_acc - older_acc
        
        if diff > 10:
            return 'improving'
        elif diff < -10:
            return 'declining'
        else:
            return 'stable'
    
    def _get_xp_history(self, user_id: int, subject: str, days: int = 30) -> List[Dict]:
        """XP history ultimi N giorni"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        history = db_manager.query('''
            SELECT 
                DATE(timestamp) as date,
                SUM(xp_earned) as daily_xp,
                COUNT(*) as quiz_count
            FROM student_quiz_history
            WHERE user_id = ? AND subject = ? AND timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        ''', (user_id, subject, cutoff_date))
        
        result = []
        for day in history:
            result.append({
                'date': str(day['date']),
                'xp': day['daily_xp'],
                'quizzes': day['quiz_count']
            })
        
        return result
    
    def _xp_to_level(self, xp: int) -> int:
        """Converti XP in livello"""
        # Progressione: 0-100 (L1), 100-250 (L2), 250-500 (L3), etc
        if xp < 100: return 1
        elif xp < 250: return 2
        elif xp < 500: return 3
        elif xp < 1000: return 4
        elif xp < 2000: return 5
        elif xp < 3500: return 6
        elif xp < 5500: return 7
        elif xp < 8000: return 8
        elif xp < 11000: return 9
        else: return 10
    
    def _xp_to_next_level(self, xp: int) -> int:
        """XP mancanti per prossimo livello"""
        thresholds = [100, 250, 500, 1000, 2000, 3500, 5500, 8000, 11000, 15000]
        for threshold in thresholds:
            if xp < threshold:
                return threshold - xp
        return 0  # Max level
    
    def _create_empty_progress(self, subject: str) -> Dict:
        """Progress vuoto per nuova materia"""
        return {
            'subject': subject,
            'total_quizzes': 0,
            'correct_quizzes': 0,
            'accuracy': 0,
            'total_xp': 0,
            'current_level': 1,
            'xp_to_next_level': 100,
            'trend': 'new',
            'topics': [],
            'xp_history': [],
            'weak_topics': [],
            'strong_topics': [],
            'last_activity': None
        }


# Initialize
progress_analytics = SubjectProgressAnalytics()
print("✅ Subject Progress Analytics inizializzato!")
