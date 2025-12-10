"""
SKAJLA - AI Insights Engine
Sistema intelligente con ML e statistica avanzata per suggerimenti personalizzati
"""

import statistics
from datetime import datetime, timedelta
from database_manager import db_manager
from typing import Dict, List, Tuple
import math

class AIInsightsEngine:
    """Motore AI per generare insights personalizzati basati su dati reali dello studente"""
    
    def __init__(self):
        self.performance_weights = {
            'grade_trend': 0.35,      # Andamento voti
            'attendance': 0.20,        # Presenza
            'engagement': 0.25,        # Partecipazione (XP, AI usage)
            'consistency': 0.20        # Costanza studio
        }
    
    def generate_insights(self, student_id: int) -> List[Dict]:
        """Genera insights personalizzati per lo studente"""
        insights = []
        
        # 1. Analisi andamento voti (Regressione lineare semplificata)
        grade_insight = self._analyze_grade_trends(student_id)
        if grade_insight:
            insights.append(grade_insight)
        
        # 2. Analisi presenza e pattern comportamentali
        attendance_insight = self._analyze_attendance_patterns(student_id)
        if attendance_insight:
            insights.append(attendance_insight)
        
        # 3. Analisi gamification e obiettivi
        gamification_insight = self._analyze_gamification_progress(student_id)
        if gamification_insight:
            insights.append(gamification_insight)
        
        # 4. Suggerimenti AI-driven basati su weak subjects
        subject_insight = self._analyze_weak_subjects(student_id)
        if subject_insight:
            insights.append(subject_insight)
        
        # 5. Predizione performance futura (ML-based)
        prediction_insight = self._predict_future_performance(student_id)
        if prediction_insight:
            insights.append(prediction_insight)
        
        # Ordina per priorità (calcola score per ogni insight)
        insights.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return insights[:3]  # Top 3 insights più importanti
    
    def _analyze_grade_trends(self, student_id: int) -> Dict:
        """Analizza trend dei voti con regressione lineare semplificata"""
        voti = db_manager.query('''
            SELECT voto, data, materia
            FROM voti 
            WHERE studente_id = ? 
            ORDER BY data DESC 
            LIMIT 10
        ''', (student_id,))
        
        if not voti or len(voti) < 3:
            return None
        
        # Calcola trend usando regressione lineare
        # Gestisci sia dict che tuple
        grades = [float(v['voto'] if isinstance(v, dict) else v[0]) for v in voti]
        n = len(grades)
        x = list(range(n))
        
        # y = mx + b (formula regressione)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(grades)
        
        # Calcola slope (m)
        numerator = sum((x[i] - mean_x) * (grades[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        
        # Analizza materia con più voti
        subject_counts = {}
        for v in voti:
            subject = v['materia'] if isinstance(v, dict) else v[2]
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        
        main_subject = max(subject_counts, key=subject_counts.get) if subject_counts else "generale"
        
        # Genera insight basato su slope
        if slope > 0.15:  # Miglioramento significativo
            return {
                'icon': '📈',
                'title': 'Performance in Crescita',
                'message': f'Ottimo! I tuoi voti in {main_subject} stanno migliorando costantemente. Trend: +{abs(slope):.1f} punti.',
                'priority': 85,
                'type': 'positive'
            }
        elif slope < -0.15:  # Peggioramento
            return {
                'icon': '⚠️',
                'title': 'Attenzione: Calo Performance',
                'message': f'I tuoi voti in {main_subject} stanno calando. Dedica più tempo allo studio e chiedi aiuto al tutor AI.',
                'priority': 95,
                'type': 'warning'
            }
        else:  # Stabile
            avg = statistics.mean(grades)
            return {
                'icon': '📊',
                'title': 'Performance Stabile',
                'message': f'Mantieni una media costante di {avg:.1f} in {main_subject}. Continua così!',
                'priority': 60,
                'type': 'neutral'
            }
    
    def _analyze_attendance_patterns(self, student_id: int) -> Dict:
        """Analizza pattern di presenza con statistiche avanzate"""
        presenze = db_manager.query('''
            SELECT presente, ritardo, data
            FROM presenze 
            WHERE studente_id = ? 
            ORDER BY data DESC 
            LIMIT 30
        ''', (student_id,))
        
        if not presenze or len(presenze) < 5:
            return None
        
        total_days = len(presenze)
        present_days = sum(1 for p in presenze if (p['presente'] if isinstance(p, dict) else p[0]))
        late_days = sum(1 for p in presenze if (p['ritardo'] if isinstance(p, dict) else p[1]) and (p['ritardo'] if isinstance(p, dict) else p[1]) > 0)
        
        attendance_rate = (present_days / total_days) * 100
        late_rate = (late_days / total_days) * 100
        
        if attendance_rate >= 95:
            return {
                'icon': '🏆',
                'title': 'Presenza Eccellente',
                'message': f'Presenza del {attendance_rate:.0f}%! Sei tra i migliori della classe.',
                'priority': 70,
                'type': 'positive'
            }
        elif attendance_rate < 80:
            return {
                'icon': '🚨',
                'title': 'Presenza Critica',
                'message': f'Presenza solo del {attendance_rate:.0f}%. Rischio bocciatura. Contatta il coordinatore.',
                'priority': 100,
                'type': 'critical'
            }
        elif late_rate > 20:
            return {
                'icon': '⏰',
                'title': 'Troppi Ritardi',
                'message': f'{late_rate:.0f}% di ritardi. Organizza meglio il tuo tempo mattutino.',
                'priority': 75,
                'type': 'warning'
            }
        
        return None
    
    def _analyze_gamification_progress(self, student_id: int) -> Dict:
        """Analizza progresso gamification e obiettivi"""
        profile = db_manager.query('''
            SELECT total_xp, current_level, current_streak, 
                   (SELECT COUNT(*) FROM user_badges WHERE utente_id = ?) as badges_count
            FROM gamification_profiles 
            WHERE utente_id = ?
        ''', (student_id, student_id), one=True)
        
        if not profile:
            return None
        
        xp, level, streak, badges = profile
        
        # Calcola XP mancanti per livello successivo
        next_level_xp = 100 * (level + 1)  # Formula semplificata
        xp_needed = next_level_xp - xp
        
        if streak >= 7:
            return {
                'icon': '🔥',
                'title': f'Streak di {streak} giorni!',
                'message': f'Incredibile costanza! Sei a {xp_needed} XP dal livello {level + 1}. Non fermarti!',
                'priority': 80,
                'type': 'achievement'
            }
        elif xp_needed < 100:
            return {
                'icon': '🎯',
                'title': 'Prossimo al Level Up!',
                'message': f'Solo {xp_needed} XP per raggiungere il livello {level + 1}! Completa un quiz o chiedi aiuto all\'AI.',
                'priority': 85,
                'type': 'goal'
            }
        
        return None
    
    def _analyze_weak_subjects(self, student_id: int) -> Dict:
        """Identifica materie deboli con clustering statistico"""
        medie = db_manager.query('''
            SELECT materia, AVG(voto) as media, COUNT(*) as num_voti
            FROM voti
            WHERE studente_id = ?
            GROUP BY materia
            HAVING COUNT(*) >= 2
        ''', (student_id,))
        
        if not medie or len(medie) < 2:
            return None
        
        # Calcola statistiche distribuzione
        all_averages = [float(m['media'] if isinstance(m, dict) else m[1]) for m in medie]
        overall_avg = statistics.mean(all_averages)
        std_dev = statistics.stdev(all_averages) if len(all_averages) > 1 else 0
        
        # Trova materie sotto la media
        weak_subjects = []
        for m in medie:
            materia = m['materia'] if isinstance(m, dict) else m[0]
            media = float(m['media'] if isinstance(m, dict) else m[1])
            if media < overall_avg - (0.5 * std_dev):  # Sotto media - 0.5 deviazioni standard
                weak_subjects.append((materia, media))
        
        if weak_subjects:
            weakest = min(weak_subjects, key=lambda x: x[1])
            return {
                'icon': '💡',
                'title': 'Focus su Materia Debole',
                'message': f'{weakest[0]} (media {weakest[1]:.1f}) necessita attenzione. Chiedi aiuto al tutor AI o studia con i compagni.',
                'priority': 90,
                'type': 'improvement'
            }
        
        return None
    
    def _predict_future_performance(self, student_id: int) -> Dict:
        """Predice performance futura con modello statistico"""
        voti = db_manager.query('''
            SELECT voto, data
            FROM voti 
            WHERE studente_id = ? 
            ORDER BY data DESC 
            LIMIT 15
        ''', (student_id,))
        
        if not voti or len(voti) < 5:
            return None
        
        recent_grades = [float(v['voto'] if isinstance(v, dict) else v[0]) for v in voti[:5]]  # Ultimi 5 voti
        older_grades = [float(v['voto'] if isinstance(v, dict) else v[0]) for v in voti[5:]]   # Voti precedenti
        
        recent_avg = statistics.mean(recent_grades)
        older_avg = statistics.mean(older_grades) if older_grades else recent_avg
        
        # Calcola momentum (differenza tra media recente e vecchia)
        momentum = recent_avg - older_avg
        
        # Predizione lineare semplice
        predicted_next = recent_avg + momentum
        predicted_next = max(1, min(10, predicted_next))  # Clamp tra 1 e 10
        
        if momentum > 0.5:
            return {
                'icon': '🚀',
                'title': 'Predizione Positiva',
                'message': f'Se mantieni il ritmo, il prossimo voto sarà circa {predicted_next:.1f}. Continua a studiare!',
                'priority': 75,
                'type': 'prediction'
            }
        elif momentum < -0.5:
            return {
                'icon': '📉',
                'title': 'Predizione: Serve Impegno',
                'message': f'Trend negativo. Rischio voto {predicted_next:.1f}. Aumenta lo studio ADESSO.',
                'priority': 92,
                'type': 'warning'
            }
        
        return None
    
    def get_study_recommendations(self, student_id: int) -> Dict:
        """Genera raccomandazioni di studio personalizzate"""
        # Analizza AI usage per capire dove lo studente ha più difficoltà
        ai_subjects = db_manager.query('''
            SELECT message, COUNT(*) as count
            FROM ai_conversations
            WHERE utente_id = ?
            GROUP BY message
            ORDER BY count DESC
            LIMIT 5
        ''', (student_id,))
        
        # Analizza voti bassi
        low_grades = db_manager.query('''
            SELECT materia, AVG(voto) as media
            FROM voti
            WHERE studente_id = ? AND voto < 6
            GROUP BY materia
            ORDER BY media ASC
            LIMIT 3
        ''', (student_id,))
        
        recommendations = {
            'focus_subjects': [lg[0] for lg in (low_grades or [])],
            'ai_help_needed': bool(ai_subjects),
            'study_hours_recommended': self._calculate_study_hours(student_id)
        }
        
        return recommendations
    
    def _calculate_study_hours(self, student_id: int) -> int:
        """Calcola ore di studio consigliate basate su performance"""
        media_generale = db_manager.query('''
            SELECT AVG(voto) as media
            FROM voti
            WHERE studente_id = ?
        ''', (student_id,), one=True)
        
        if not media_generale or not media_generale[0]:
            return 10  # Default
        
        avg = float(media_generale[0])
        
        # Formula: più bassa la media, più ore servono
        if avg < 6:
            return 20  # Rischio bocciatura
        elif avg < 7:
            return 15
        elif avg < 8:
            return 12
        else:
            return 10  # Eccellenza

# Istanza globale
ai_insights_engine = AIInsightsEngine()
