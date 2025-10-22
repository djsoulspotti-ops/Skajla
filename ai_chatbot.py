"""
SKAILA AI Chatbot - Coach Personale per Soft Skills
Focus esclusivo su: motivazione, organizzazione, gestione stress, obiettivi
Integrato con tutto l'ecosistema SKAILA
"""

from coaching_engine import coaching_engine
from database_manager import db_manager
from datetime import datetime
from typing import Dict, Any
import json

class AISkailaBot:
    """
    Chatbot SKAILA - Coach AI per soft skills e monitoraggio studenti
    NON risponde a domande tecniche - focus su supporto emotivo e organizzativo
    """
    
    def __init__(self):
        self.bot_name = "SKAILA Coach"
        self.bot_avatar = "🤖"
        
        # Context del sistema
        self.system_context = """
        Sei SKAILA Coach, un mentore AI personale per studenti italiani.
        
        🎯 TUO RUOLO:
        - Supporto emotivo e motivazionale
        - Gestione stress e ansia
        - Organizzazione studio e tempo
        - Definizione obiettivi SMART
        - Monitoraggio progressi
        - Miglioramento continuo
        
        ❌ NON FARE:
        - Non rispondere a domande tecniche sulle materie
        - Non spiegare concetti di matematica/fisica/etc
        - Non creare quiz o esercizi
        
        ✅ SEMPRE FARE:
        - Usare dati reali dello studente (voti, XP, streak, quiz)
        - Dare feedback costruttivo basato su fatti
        - Suggerire azioni concrete e misurabili
        - Essere empatico e incoraggiante
        - Celebrare successi (anche piccoli)
        """
        
        print("✅ SKAILA Coach inizializzato - Focus: Soft Skills & Coaching")
    
    def generate_response(self, message: str, user_name: str, user_role: str, user_id: int) -> str:
        """
        Genera risposta coaching usando il motore di coaching integrato
        """
        
        # Verifica se è una domanda tecnica e reindirizza
        if self._is_technical_question(message):
            return self._redirect_to_teachers(user_name)
        
        # Usa il coaching engine per generare risposta personalizzata
        try:
            response = coaching_engine.generate_personalized_response(message, user_name, user_id)
            
            # Salva conversazione per cronologia
            self._save_conversation(user_id, message, response)
            
            return response
        
        except Exception as e:
            print(f"❌ Errore generate_response: {e}")
            return self._fallback_supportive_message(user_name)
    
    def _is_technical_question(self, message: str) -> bool:
        """Rileva se è una domanda tecnica su materie"""
        technical_keywords = [
            'come si risolve', 'formula', 'teorema', 'equazione',
            'spiegami matematica', 'spiegami fisica', 'come funziona',
            'calcola', 'dimostrazione', 'esercizio', 'problema di',
            'cos\'è il', 'cosa è il', 'definizione di'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in technical_keywords)
    
    def _redirect_to_teachers(self, user_name: str) -> str:
        """Reindirizza domande tecniche ai professori"""
        return f"""Ciao {user_name}! 👋

Vedo che hai una domanda tecnica su una materia specifica.

🎓 **Per domande didattiche**, ti consiglio di:
1. Chiedere direttamente al tuo professore
2. Usare i materiali didattici nella sezione Materiali
3. Collaborare con i compagni nelle chat di classe

💪 **Io sono qui per aiutarti con**:
• Organizzazione dello studio 📅
• Gestione dello stress 🧘
• Motivazione e obiettivi 🎯
• Monitoraggio progressi 📊

Come posso supportarti su questi aspetti? 🤝"""
    
    def _save_conversation(self, user_id: int, message: str, response: str):
        """Salva conversazione nel database"""
        try:
            db_manager.execute('''
                INSERT INTO ai_conversations 
                (utente_id, message, response, timestamp)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, message, response, datetime.now()))
        except Exception as e:
            print(f"Errore save conversation: {e}")
    
    def _fallback_supportive_message(self, user_name: str) -> str:
        """Messaggio di fallback in caso di errore"""
        return f"""Ciao {user_name}! 👋

Mi trovo in difficoltà a risponderti in questo momento, ma sono qui per supportarti!

Posso aiutarti con:
• 📅 Organizzare il tuo studio
• 📊 Analizzare i tuoi progressi  
• 🎯 Definire obiettivi raggiungibili
• 🧘 Gestire stress e motivazione

Cosa ti preoccupa di più in questo momento? 🤝"""
    
    def get_student_dashboard_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Genera insights per la dashboard studente
        Analizza tutti i dati e fornisce suggerimenti proattivi
        """
        try:
            # Analizza ecosistema completo
            data = coaching_engine.analyze_student_ecosystem(user_id)
            
            insights = {
                'summary': self._generate_summary(data),
                'alerts': self._format_alerts(data['alerts']),
                'suggestions': self._generate_suggestions(data),
                'motivational_quote': self._get_motivational_quote(data)
            }
            
            return insights
        
        except Exception as e:
            print(f"Errore dashboard insights: {e}")
            return {
                'summary': "Continua così! Ogni giorno è un'opportunità di crescita! 🌟",
                'alerts': [],
                'suggestions': ["Fai almeno 1 quiz oggi", "Rivedi gli appunti per 15 minuti"],
                'motivational_quote': "Il successo è la somma di piccoli sforzi ripetuti giorno dopo giorno."
            }
    
    def _generate_summary(self, data: Dict) -> str:
        """Genera summary situazione studente"""
        parts = []
        
        # Trend voti
        trend = data['academic'].get('trend')
        if trend == 'improving':
            parts.append("📈 I tuoi voti stanno migliorando!")
        elif trend == 'declining':
            parts.append("📉 Attenzione: trend voti in calo")
        else:
            parts.append("📊 Performance stabile")
        
        # Engagement
        activity = data['engagement'].get('activity_level')
        if activity == 'high':
            parts.append("🔥 Ottimo engagement!")
        elif activity == 'low':
            parts.append("⚡ Aumenta l'attività quotidiana")
        
        # Streak
        streak = data['engagement']['gamification'].get('streak', 0)
        if streak >= 7:
            parts.append(f"🏆 {streak} giorni di streak!")
        elif streak == 0:
            parts.append("🎯 Ricomincia il tuo streak oggi")
        
        return ' '.join(parts)
    
    def _format_alerts(self, alerts: list) -> list:
        """Formatta alert in modo user-friendly"""
        alert_messages = {
            'grade_decline': '⚠️ I tuoi voti sono in calo - parliamone?',
            'streak_lost': '💔 Hai perso il tuo streak - ricominciamo insieme!',
            'low_engagement': '📉 Attività bassa ultimamente - tutto ok?',
            'unexcused_absences': '⚠️ Hai assenze non giustificate',
            'low_social_activity': '👥 Poca interazione sociale - ti senti isolato?'
        }
        
        return [alert_messages.get(a, a) for a in alerts]
    
    def _generate_suggestions(self, data: Dict) -> list:
        """Genera suggerimenti personalizzati"""
        suggestions = []
        
        # Materie deboli
        weak = data['academic'].get('weak_subjects', [])
        if weak:
            suggestions.append(f"📚 Focus su {weak[0]}: 30 min oggi")
        
        # Quiz
        quiz_done = data['engagement']['gamification'].get('quiz_completed', 0)
        if quiz_done < 5:
            suggestions.append("🎯 Fai almeno 1 quiz per verificare la comprensione")
        
        # Streak
        streak = data['engagement']['gamification'].get('streak', 0)
        if streak == 0:
            suggestions.append("🔥 Ricomincia il tuo streak con una piccola attività")
        
        # Sociale
        if data['social'].get('social_level') == 'low':
            suggestions.append("👥 Partecipa alle chat di classe per supporto")
        
        # Default
        if not suggestions:
            suggestions = [
                "✅ Rivedi appunti per 15 minuti",
                "🎯 Definisci 1 obiettivo per domani",
                "🧘 Prenditi una pausa se necessario"
            ]
        
        return suggestions[:3]
    
    def _get_motivational_quote(self, data: Dict) -> str:
        """Seleziona quote motivazionale basata su situazione"""
        
        quotes = {
            'improving': "Il successo non è definitivo, il fallimento non è fatale: è il coraggio di continuare che conta. 💪",
            'declining': "Le difficoltà spesso preparano persone comuni a destini straordinari. Non mollare! 🌟",
            'stable': "La costanza è la chiave del successo. Continua così! 🔑",
            'default': "Ogni giorno è un'opportunità per crescere. Cogli questa giornata! 🌅"
        }
        
        trend = data['academic'].get('trend', 'default')
        return quotes.get(trend, quotes['default'])
    
    def generate_study_plan(self, user_id: int, duration_days: int = 7) -> Dict[str, Any]:
        """
        Genera piano studio personalizzato basato su performance
        """
        try:
            data = coaching_engine.analyze_student_ecosystem(user_id)
            
            plan = {
                'duration': f'{duration_days} giorni',
                'priority_subjects': data['academic'].get('weak_subjects', [])[:3],
                'daily_schedule': self._build_daily_schedule(data),
                'goals': self._define_weekly_goals(data),
                'tips': self._get_study_tips(data)
            }
            
            # Salva piano nel database
            self._save_study_plan(user_id, plan)
            
            return plan
        
        except Exception as e:
            print(f"Errore generate_study_plan: {e}")
            return {}
    
    def _build_daily_schedule(self, data: Dict) -> list:
        """Costruisce schedule giornaliero"""
        weak_subjects = data['academic'].get('weak_subjects', [])
        
        schedule = [
            {
                'time': '15:00-15:30',
                'activity': f'Ripasso {weak_subjects[0]}' if weak_subjects else 'Studio materia prioritaria',
                'duration': '30 min'
            },
            {
                'time': '15:30-15:45',
                'activity': 'Pausa e snack',
                'duration': '15 min'
            },
            {
                'time': '15:45-16:15',
                'activity': 'Quiz e verifica comprensione',
                'duration': '30 min'
            }
        ]
        
        return schedule
    
    def _define_weekly_goals(self, data: Dict) -> list:
        """Definisce obiettivi settimanali SMART"""
        goals = []
        
        # Goal voti
        weak = data['academic'].get('weak_subjects', [])
        if weak:
            goals.append(f"Migliorare in {weak[0]}: almeno 1 voto >= 7")
        
        # Goal quiz
        quiz = data['engagement']['gamification'].get('quiz_completed', 0)
        goals.append(f"Completare {max(5, quiz + 3)} quiz totali")
        
        # Goal streak
        goals.append("Mantenere streak di 7 giorni consecutivi")
        
        return goals
    
    def _get_study_tips(self, data: Dict) -> list:
        """Consigli di studio personalizzati"""
        return [
            "🍅 Usa la tecnica Pomodoro (25 min studio + 5 min pausa)",
            "📝 Fai schemi e mappe concettuali",
            "👥 Studia in gruppo per argomenti complessi",
            "🔄 Ripassa con spaced repetition"
        ]
    
    def _save_study_plan(self, user_id: int, plan: Dict):
        """Salva piano studio nel database"""
        try:
            db_manager.execute('''
                INSERT INTO study_plans 
                (user_id, plan_type, priority_subjects, weekly_schedule, goals, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                'personalized',
                ','.join(plan.get('priority_subjects', [])),
                json.dumps(plan.get('daily_schedule', [])),
                json.dumps(plan.get('goals', [])),
                'active'
            ))
        except Exception as e:
            print(f"Errore save study plan: {e}")

# Istanza globale
ai_bot = AISkailaBot()
