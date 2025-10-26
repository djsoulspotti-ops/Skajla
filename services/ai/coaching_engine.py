"""
SKAILA Coaching Engine - AI Coach per Soft Skills e Monitoraggio Studenti
Integrato con tutto l'ecosistema SKAILA
"""

from database_manager import db_manager
from gamification import gamification_system
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import re

# Import calendario dopo definizione classe per evitare circular import
calendario_module = None

class SkailaCoachingEngine:
    """
    Motore di coaching intelligente che analizza dati da tutti i servizi SKAILA
    e fornisce supporto personalizzato su soft skills, motivazione e organizzazione
    """
    
    def __init__(self):
        global calendario_module
        if calendario_module is None:
            try:
                from calendario_integration import calendario
                calendario_module = calendario
            except ImportError:
                pass
        self.categories = ['stress', 'motivazione', 'organizzazione', 'obiettivi', 'burnout', 'sociale']
        self.sentiment_keywords = {
            'anxious': ['stressato', 'ansia', 'paura', 'preoccupato', 'nervoso', 'agitato'],
            'overwhelmed': ['troppo', 'non ce la faccio', 'sovraccarico', 'troppi', 'impossibile'],
            'demotivated': ['demotivato', 'stufo', 'noia', 'non ho voglia', 'inutile', 'perché studiare'],
            'proud': ['ho preso', 'bene', 'ottimo', 'felice', 'riuscito', 'orgoglioso'],
            'exhausted': ['esausto', 'stanco', 'bruciato', 'non reggo', 'finito'],
            'confused': ['non capisco', 'confuso', 'perso', 'difficile', 'complicato'],
            'insecure': ['altri meglio', 'inferiore', 'non sono bravo', 'peggio'],
            'frustrated': ['frustrato', 'arrabbiato', 'non funziona', 'sempre sbaglio'],
            'curious': ['come', 'perché', 'spiegami', 'voglio sapere', 'interessante'],
            'motivated': ['voglio', 'obiettivo', 'migliorare', 'impegno', 'ce la farò']
        }
    
    def analyze_student_ecosystem(self, user_id: int) -> Dict[str, Any]:
        """
        Analizza TUTTI i dati dello studente dall'ecosistema SKAILA
        """
        data = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'academic': {},
            'engagement': {},
            'social': {},
            'career': {},
            'alerts': []
        }
        
        # 1. DATI ACCADEMICI (Voti + Presenze)
        data['academic'] = self._analyze_academic_performance(user_id)
        
        # 2. ENGAGEMENT (Gamification + Quiz)
        data['engagement'] = self._analyze_engagement(user_id)
        
        # 3. SOCIALE (Messaggistica + Collaborazione)
        data['social'] = self._analyze_social_activity(user_id)
        
        # 4. CARRIERA (SKAILA Connect)
        data['career'] = self._analyze_career_activity(user_id)
        
        # 5. RILEVAMENTO ALERT
        data['alerts'] = self._detect_alerts(data)
        
        return data
    
    def _analyze_academic_performance(self, user_id: int) -> Dict[str, Any]:
        """Analizza performance accademica da registro voti e presenze"""
        academic = {
            'voti_summary': {},
            'presenze_summary': {},
            'trend': 'neutral',
            'weak_subjects': [],
            'strong_subjects': []
        }
        
        try:
            # Voti per materia
            voti = db_manager.query('''
                SELECT materia, AVG(voto::float) as media, COUNT(*) as num_voti,
                       MAX(data) as ultimo_voto
                FROM voti 
                WHERE studente_id = %s
                GROUP BY materia
                ORDER BY media DESC
            ''', (user_id,))
            
            if voti:
                academic['voti_summary'] = {
                    v['materia']: {
                        'media': round(v['media'], 1),
                        'num_voti': v['num_voti'],
                        'ultimo': v['ultimo_voto'].strftime('%d/%m/%Y') if v['ultimo_voto'] else None
                    }
                    for v in voti
                }
                
                # Identifica materie forti e deboli
                for v in voti:
                    if v['media'] >= 8:
                        academic['strong_subjects'].append(v['materia'])
                    elif v['media'] < 6.5:
                        academic['weak_subjects'].append(v['materia'])
                
                # Calcola trend (ultimi 30 giorni vs precedenti)
                academic['trend'] = self._calculate_grade_trend(user_id)
            
            # Presenze
            presenze = db_manager.query('''
                SELECT COUNT(*) as totale,
                       SUM(CASE WHEN presente THEN 1 ELSE 0 END) as presenze,
                       SUM(CASE WHEN NOT presente AND giustificato THEN 1 ELSE 0 END) as assenze_giustificate,
                       SUM(CASE WHEN NOT presente AND NOT giustificato THEN 1 ELSE 0 END) as assenze_non_giustificate
                FROM presenze
                WHERE studente_id = %s AND data >= CURRENT_DATE - INTERVAL '30 days'
            ''', (user_id,), one=True)
            
            if presenze and presenze['totale'] > 0:
                academic['presenze_summary'] = {
                    'percentuale': round((presenze['presenze'] / presenze['totale']) * 100, 1),
                    'assenze_non_giustificate': presenze['assenze_non_giustificate']
                }
        
        except Exception as e:
            print(f"Errore analisi academic: {e}")
        
        return academic
    
    def _calculate_grade_trend(self, user_id: int) -> str:
        """Calcola trend voti (miglioramento, stabile, peggioramento)"""
        try:
            recent = db_manager.query('''
                SELECT AVG(voto::float) as media FROM voti
                WHERE studente_id = %s AND data >= CURRENT_DATE - INTERVAL '30 days'
            ''', (user_id,), one=True)
            
            previous = db_manager.query('''
                SELECT AVG(voto::float) as media FROM voti
                WHERE studente_id = %s 
                AND data < CURRENT_DATE - INTERVAL '30 days'
                AND data >= CURRENT_DATE - INTERVAL '60 days'
            ''', (user_id,), one=True)
            
            if recent and previous and recent['media'] and previous['media']:
                diff = recent['media'] - previous['media']
                if diff > 0.5:
                    return 'improving'
                elif diff < -0.5:
                    return 'declining'
            
            return 'stable'
        except:
            return 'neutral'
    
    def _analyze_engagement(self, user_id: int) -> Dict[str, Any]:
        """Analizza engagement da gamification e quiz"""
        engagement = {
            'gamification': {},
            'quiz': {},
            'activity_level': 'medium'
        }
        
        try:
            # Gamification
            gam_data = gamification_system.get_user_dashboard(user_id)
            profile = gam_data.get('profile', {})
            
            engagement['gamification'] = {
                'xp': profile.get('total_xp', 0),
                'level': profile.get('current_level', 1),
                'streak': profile.get('current_streak', 0),
                'longest_streak': profile.get('longest_streak', 0),
                'quiz_completed': profile.get('quizzes_completed', 0)
            }
            
            # Attività recente XP
            daily_xp = db_manager.query('''
                SELECT date, xp_earned FROM daily_analytics
                WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY date DESC
            ''', (user_id,))
            
            if daily_xp:
                avg_xp = sum(d['xp_earned'] for d in daily_xp) / len(daily_xp)
                if avg_xp > 50:
                    engagement['activity_level'] = 'high'
                elif avg_xp < 20:
                    engagement['activity_level'] = 'low'
            
            # Quiz performance
            quiz_stats = db_manager.query('''
                SELECT materia, COUNT(*) as completati, AVG(punteggio) as media_punteggio
                FROM user_quiz_history
                WHERE user_id = %s
                GROUP BY materia
            ''', (user_id,))
            
            if quiz_stats:
                engagement['quiz'] = {
                    q['materia']: {
                        'completati': q['completati'],
                        'media': round(q['media_punteggio'], 1)
                    }
                    for q in quiz_stats
                }
        
        except Exception as e:
            print(f"Errore analisi engagement: {e}")
        
        return engagement
    
    def _analyze_social_activity(self, user_id: int) -> Dict[str, Any]:
        """Analizza attività sociale (messaggi, collaborazione)"""
        social = {
            'messages_sent': 0,
            'last_activity': None,
            'social_level': 'medium'
        }
        
        try:
            # Messaggi inviati ultimi 7 giorni
            messages = db_manager.query('''
                SELECT COUNT(*) as count, MAX(timestamp) as last_msg
                FROM (
                    SELECT timestamp FROM direct_messages WHERE sender_id = %s
                    UNION ALL
                    SELECT timestamp FROM group_messages WHERE user_id = %s
                ) AS all_messages
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            ''', (user_id, user_id), one=True)
            
            if messages:
                social['messages_sent'] = messages['count']
                social['last_activity'] = messages['last_msg']
                
                if messages['count'] > 20:
                    social['social_level'] = 'high'
                elif messages['count'] < 5:
                    social['social_level'] = 'low'
        
        except Exception as e:
            print(f"Errore analisi social: {e}")
        
        return social
    
    def _analyze_career_activity(self, user_id: int) -> Dict[str, Any]:
        """Analizza attività SKAILA Connect"""
        career = {
            'applications': 0,
            'sectors_interest': [],
            'career_readiness': 'exploring'
        }
        
        try:
            apps = db_manager.query('''
                SELECT COUNT(*) as total, 
                       string_agg(DISTINCT sc.settore, ', ') as settori
                FROM candidature c
                JOIN skaila_connect_companies sc ON c.company_id = sc.id
                WHERE c.utente_id = %s
            ''', (user_id,), one=True)
            
            if apps:
                career['applications'] = apps['total']
                if apps['settori']:
                    career['sectors_interest'] = apps['settori'].split(', ')
                
                if apps['total'] > 5:
                    career['career_readiness'] = 'active'
                elif apps['total'] > 0:
                    career['career_readiness'] = 'interested'
        
        except Exception as e:
            print(f"Errore analisi career: {e}")
        
        return career
    
    def _detect_alerts(self, data: Dict) -> List[str]:
        """Rileva segnali di alert (burnout, demotivazione, calo performance)"""
        alerts = []
        
        # Alert voti in calo
        if data['academic'].get('trend') == 'declining':
            alerts.append('grade_decline')
        
        # Alert streak perso
        streak = data['engagement']['gamification'].get('streak', 0)
        longest = data['engagement']['gamification'].get('longest_streak', 0)
        if longest > 7 and streak == 0:
            alerts.append('streak_lost')
        
        # Alert bassa attività
        if data['engagement'].get('activity_level') == 'low':
            alerts.append('low_engagement')
        
        # Alert assenze non giustificate
        presenze = data['academic'].get('presenze_summary', {})
        if presenze.get('assenze_non_giustificate', 0) > 3:
            alerts.append('unexcused_absences')
        
        # Alert isolamento sociale
        if data['social'].get('social_level') == 'low':
            alerts.append('low_social_activity')
        
        return alerts
    
    def detect_sentiment(self, message: str) -> List[str]:
        """Rileva sentiment dal messaggio"""
        message_lower = message.lower()
        detected = []
        
        for sentiment, keywords in self.sentiment_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected.append(sentiment)
        
        return detected if detected else ['neutral']
    
    def find_matching_template(self, message: str, sentiment: List[str]) -> Dict[str, Any]:
        """Trova template di risposta migliore dal database"""
        try:
            # Carica tutti i template ordinati per priorità
            templates = db_manager.query('''
                SELECT * FROM chatbot_coaching 
                ORDER BY priority DESC
            ''')
            
            message_lower = message.lower()
            best_match = None
            best_score = 0
            
            for template in templates:
                score = 0
                keywords = template['pattern_keywords'].split(',')
                
                # Match keywords
                keyword_matches = sum(1 for kw in keywords if kw.strip() in message_lower)
                score += keyword_matches * 2
                
                # Match sentiment
                if template['sentiment_target'] in sentiment:
                    score += 3
                
                # Priority weight
                score += template['priority'] * 0.5
                
                if score > best_score:
                    best_score = score
                    best_match = template
            
            return best_match if best_score > 1 else None
        
        except Exception as e:
            print(f"Errore find_matching_template: {e}")
            return None
    
    def generate_personalized_response(self, message: str, user_name: str, user_id: int) -> str:
        """Genera risposta coaching personalizzata"""
        
        # 1. Analizza ecosistema studente
        student_data = self.analyze_student_ecosystem(user_id)
        
        # 2. Rileva sentiment
        sentiment = self.detect_sentiment(message)
        
        # 3. Trova template migliore
        template = self.find_matching_template(message, sentiment)
        
        if not template:
            return self._generate_default_supportive_response(user_name, student_data)
        
        # 4. Personalizza template con dati reali
        response = self._personalize_template(template, student_data, user_name, sentiment)
        
        # 5. Salva interazione per tracking
        self._save_interaction(user_id, message, template['categoria'], sentiment, response, student_data)
        
        return response
    
    def _personalize_template(self, template: Dict, data: Dict, user_name: str, sentiment: List[str]) -> str:
        """Personalizza template con dati reali studente"""
        response = template['response_template']
        
        # Sostituzioni base
        response = response.replace('{user_name}', user_name)
        response = response.replace('{sentiment}', sentiment[0] if sentiment else 'preoccupato')
        
        # Analisi situazione
        analysis = self._build_analysis_text(data)
        response = response.replace('{analysis}', analysis)
        response = response.replace('{current_situation}', analysis)
        
        # Dati di progresso
        progress = self._build_progress_text(data)
        response = response.replace('{progress_data}', progress)
        response = response.replace('{stats}', progress)
        
        # Achievement specifici
        achievements = self._build_achievements_text(data)
        response = response.replace('{specific_achievements}', achievements)
        response = response.replace('{achievement}', achievements)
        
        # Piano azione
        action_plan = self._build_action_plan(data, template.get('actions_suggestions', ''))
        response = response.replace('{action_plan}', action_plan)
        response = response.replace('{optimized_schedule}', action_plan)
        response = response.replace('{personalized_schedule}', action_plan)
        
        # Altri placeholder
        response = response.replace('{event_type}', 'questa sfida')
        response = response.replace('{your_strengths}', self._build_strengths_text(data))
        
        return response
    
    def _build_analysis_text(self, data: Dict) -> str:
        """Costruisce testo analisi situazione"""
        parts = []
        
        # Voti
        if data['academic'].get('voti_summary'):
            media_generale = sum(v['media'] for v in data['academic']['voti_summary'].values()) / len(data['academic']['voti_summary'])
            parts.append(f"📊 Media generale: {media_generale:.1f}")
        
        # Presenze
        if data['academic'].get('presenze_summary'):
            perc = data['academic']['presenze_summary']['percentuale']
            parts.append(f"✅ Presenze: {perc}%")
        
        # Engagement
        xp = data['engagement']['gamification'].get('xp', 0)
        streak = data['engagement']['gamification'].get('streak', 0)
        parts.append(f"🎮 XP: {xp} | Streak: {streak} giorni")
        
        return '\n'.join(parts) if parts else "Sto analizzando i tuoi dati..."
    
    def _build_progress_text(self, data: Dict) -> str:
        """Costruisce testo progressi"""
        parts = []
        
        trend = data['academic'].get('trend')
        if trend == 'improving':
            parts.append("📈 I tuoi voti sono in MIGLIORAMENTO!")
        elif trend == 'stable':
            parts.append("📊 Performance stabile e costante")
        
        xp = data['engagement']['gamification'].get('xp', 0)
        level = data['engagement']['gamification'].get('level', 1)
        parts.append(f"🎮 Livello {level} con {xp} XP")
        
        quiz = data['engagement']['gamification'].get('quiz_completed', 0)
        if quiz > 0:
            parts.append(f"✅ {quiz} quiz completati")
        
        return '\n'.join(parts)
    
    def _build_achievements_text(self, data: Dict) -> str:
        """Costruisce testo achievement recenti"""
        achievements = []
        
        # Materie forti
        strong = data['academic'].get('strong_subjects', [])
        if strong:
            achievements.append(f"💪 Eccellente in: {', '.join(strong[:2])}")
        
        # Streak
        streak = data['engagement']['gamification'].get('streak', 0)
        if streak >= 7:
            achievements.append(f"🔥 {streak} giorni di streak consecutivo!")
        
        # Applicazioni career
        apps = data['career'].get('applications', 0)
        if apps > 0:
            achievements.append(f"🚀 {apps} candidature inviate")
        
        return '\n'.join(achievements) if achievements else "Continua così, ogni piccolo passo conta! 🌟"
    
    def _build_action_plan(self, data: Dict, suggestions: str) -> str:
        """Costruisce piano azione personalizzato INTEGRATO CON CALENDARIO"""
        actions = []
        
        # Integra calendario se disponibile
        if calendario_module:
            user_id = data.get('user_id')
            calendar_summary = calendario_module.get_calendar_summary(user_id)
            if calendar_summary and 'Nessuna scadenza' not in calendar_summary:
                actions.append(f"📅 {calendar_summary.split(chr(10))[1]}")  # Prima scadenza
        
        # Priorità materie deboli
        weak = data['academic'].get('weak_subjects', [])
        if weak and len(actions) < 3:
            actions.append(f"1️⃣ Focus su {weak[0]}: 30 min/giorno")
        
        # Mantenimento streak
        streak = data['engagement']['gamification'].get('streak', 0)
        if len(actions) < 3:
            if streak > 0:
                actions.append(f"2️⃣ Mantieni streak: 1 quiz/giorno")
            else:
                actions.append("2️⃣ Ricomincia streak: 1 piccola attività oggi")
        
        # Engagement basso
        if data['engagement'].get('activity_level') == 'low' and len(actions) < 3:
            actions.append("3️⃣ 20 min studio + esercizi interattivi")
        
        # Default
        if not actions:
            actions = [
                "1️⃣ Rivedi appunti (15 min)",
                "2️⃣ Fai 1 quiz per verifica",
                "3️⃣ Pausa e ricarica energie"
            ]
        
        return '\n'.join(actions[:3])
    
    def _build_strengths_text(self, data: Dict) -> str:
        """Costruisce testo punti di forza"""
        strengths = []
        
        strong_subjects = data['academic'].get('strong_subjects', [])
        if strong_subjects:
            strengths.append(f"✨ Sei forte in {', '.join(strong_subjects)}")
        
        level = data['engagement']['gamification'].get('level', 1)
        if level >= 5:
            strengths.append(f"🎯 Hai raggiunto livello {level}")
        
        return '\n'.join(strengths) if strengths else "Hai grandi potenzialità da esprimere! 🌟"
    
    def _generate_default_supportive_response(self, user_name: str, data: Dict) -> str:
        """Risposta di supporto generica quando non match template"""
        return f"""Ciao {user_name}! 👋
        
Sono qui per supportarti. Vedo che:

{self._build_analysis_text(data)}

Come posso aiutarti oggi? Posso:
• Aiutarti a organizzare lo studio 📅
• Analizzare i tuoi progressi 📊
• Darti consigli per gestire lo stress 🧘
• Aiutarti a fissare obiettivi 🎯

Dimmi cosa ti serve! 🤝"""
    
    def _save_interaction(self, user_id: int, message: str, category: str, 
                         sentiment: List[str], response: str, student_data: Dict):
        """Salva interazione per analytics"""
        try:
            db_manager.execute('''
                INSERT INTO coaching_interactions
                (user_id, message, detected_category, detected_sentiment, response, user_data_snapshot)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, message, category, ','.join(sentiment), response, json.dumps(student_data)))
        except Exception as e:
            print(f"Errore save interaction: {e}")

# Istanza globale
coaching_engine = SkailaCoachingEngine()
