"""
SKAILA AI Brain Engine - Sistema Intelligente Nativo
Chatbot completamente integrato nell'ecosistema SKAILA
Zero dipendenze OpenAI - 100% personalizzato
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
from database_manager import db_manager
from gamification import gamification_system

class SKAILABrain:
    """Cervello decisionale del chatbot SKAILA"""
    
    def __init__(self):
        self.init_knowledge_base()
        
    def init_knowledge_base(self):
        """Inizializza la knowledge base SKAILA"""
        self.subjects = ['matematica', 'italiano', 'storia', 'scienze', 'inglese', 'fisica', 'chimica', 'geografia']
        
        # Pattern di riconoscimento per materie
        self.subject_keywords = {
            'matematica': ['matematica', 'algebra', 'geometria', 'calcolo', 'equazione', 'numero', 
                          'frazione', 'derivata', 'integrale', 'teorema', 'dimostrazione'],
            'italiano': ['italiano', 'grammatica', 'letteratura', 'poesia', 'romanzo', 'analisi', 
                        'verbo', 'soggetto', 'predicato', 'complemento'],
            'storia': ['storia', 'guerra', 'impero', 'rivoluzione', 'antichità', 'medioevo', 
                      'rinascimento', 'illuminismo', 'evento storico'],
            'scienze': ['scienze', 'biologia', 'chimica', 'fisica', 'cellula', 'atomo', 
                       'molecola', 'energia', 'forza'],
            'inglese': ['inglese', 'english', 'grammar', 'vocabulary', 'verb', 'tense'],
            'fisica': ['fisica', 'forza', 'energia', 'velocità', 'accelerazione', 'newton', 
                      'gravità', 'movimento'],
            'chimica': ['chimica', 'molecola', 'atomo', 'reazione', 'elemento', 'composto'],
            'geografia': ['geografia', 'continente', 'capitale', 'nazione', 'fiume', 'monte']
        }
        
        # Sentiment keywords
        self.sentiment_keywords = {
            'frustrated': ['non capisco', 'difficile', 'impossibile', 'confuso', 'bloccato', 'problema'],
            'motivated': ['voglio imparare', 'studio', 'esame', 'test', 'preparazione', 'obiettivo'],
            'curious': ['perché', 'come mai', 'cosa', 'come funziona', 'interessante', 'voglio sapere'],
            'positive': ['grazie', 'perfetto', 'ottimo', 'capito', 'chiaro', 'fantastico', 'bene'],
            'help_request': ['aiuto', 'help', 'non so', 'spiegami', 'mi serve']
        }
    
    def analyze_student_context(self, user_id: int, message: str) -> Dict[str, Any]:
        """Analizza il contesto completo dello studente"""
        
        # Profilo gamification
        gamification_data = gamification_system.get_user_dashboard(user_id)
        profile = gamification_data['profile']
        
        # Dati utente base
        user_data = db_manager.query('SELECT * FROM utenti WHERE id = ?', (user_id,), one=True)
        
        # Analisi attività oggi
        today_activity = self._get_today_activity(user_id)
        
        # Progressi per materia
        subject_progress = self._get_subject_progress(user_id)
        
        # Compagni di classe online
        classmates_online = self._get_online_classmates(user_id, user_data)
        
        # Daily challenges disponibili
        daily_challenges = []  # TODO: Implementare get_available_daily_challenges
        
        # Badge quasi sbloccati
        badges_close = self._get_badges_almost_unlocked(user_id, gamification_data)
        
        # Streak status
        streak_status = self._analyze_streak_status(profile)
        
        # Rileva materia e sentiment dal messaggio
        detected_subject = self._detect_subject(message)
        sentiment = self._detect_sentiment(message)
        
        context = {
            'user_id': user_id,
            'nome': user_data['nome'] if user_data else 'Studente',
            'livello': profile['current_level'],
            'xp_totale': profile['total_xp'],
            'streak': profile['current_streak'],
            'streak_status': streak_status,
            'classe': user_data.get('classe', '') if user_data else '',
            'today_activity': today_activity,
            'subject_progress': subject_progress,
            'classmates_online': classmates_online,
            'daily_challenges': daily_challenges,
            'badges_close': badges_close,
            'detected_subject': detected_subject,
            'sentiment': sentiment,
            'message_original': message
        }
        
        return context
    
    def generate_intelligent_response(self, context: Dict[str, Any]) -> str:
        """Genera risposta intelligente basata su contesto completo"""
        
        # PRIORITÀ 1: Emergenza Streak
        if context['streak_status']['is_emergency']:
            return self._streak_emergency_response(context)
        
        # PRIORITÀ 2: Richiesta aiuto specifica
        if 'help_request' in context['sentiment']:
            return self._help_response(context)
        
        # PRIORITÀ 3: Quiz request
        if 'quiz' in context['message_original'].lower():
            return self._quiz_suggestion_response(context)
        
        # PRIORITÀ 4: Materia specifica rilevata
        if context['detected_subject']:
            return self._subject_specific_response(context)
        
        # PRIORITÀ 5: Motivazione generale
        if context['badges_close']:
            return self._badge_motivation_response(context)
        
        # PRIORITÀ 6: Social learning
        if context['classmates_online']:
            return self._social_learning_response(context)
        
        # DEFAULT: Saluto personalizzato
        return self._personalized_greeting(context)
    
    def _get_today_activity(self, user_id: int) -> Dict[str, int]:
        """Recupera attività di oggi"""
        messages_today = db_manager.query('''
            SELECT COUNT(*) as count FROM messaggi 
            WHERE utente_id = ? AND DATE(timestamp) = DATE('now')
        ''', (user_id,), one=True)
        
        ai_today = db_manager.query('''
            SELECT COUNT(*) as count FROM ai_conversations 
            WHERE utente_id = ? AND DATE(timestamp) = DATE('now')
        ''', (user_id,), one=True)
        
        quiz_today = db_manager.query('''
            SELECT COUNT(*) as count FROM student_quiz_history 
            WHERE user_id = ? AND DATE(timestamp) = DATE('now')
        ''', (user_id,), one=True)
        
        return {
            'messages': messages_today['count'] if messages_today else 0,
            'ai_interactions': ai_today['count'] if ai_today else 0,
            'quiz_completed': quiz_today['count'] if quiz_today else 0
        }
    
    def _get_subject_progress(self, user_id: int) -> Dict[str, Any]:
        """Recupera progressi per materia"""
        progress = db_manager.query('''
            SELECT subject, total_quizzes, correct_quizzes, accuracy_percentage, 
                   total_xp, topics_weak, last_activity_date
            FROM student_subject_progress 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = {}
        for row in progress:
            result[row['subject']] = {
                'total_quizzes': row['total_quizzes'],
                'accuracy': row['accuracy_percentage'],
                'xp': row['total_xp'],
                'weak_topics': row['topics_weak'].split(',') if row['topics_weak'] else [],
                'last_activity': row['last_activity_date']
            }
        
        return result
    
    def _get_online_classmates(self, user_id: int, user_data: Dict) -> List[Dict]:
        """Trova compagni di classe online"""
        if not user_data or not user_data.get('classe'):
            return []
        
        classmates = db_manager.query('''
            SELECT id, nome, cognome FROM utenti 
            WHERE classe = ? AND id != ? AND status_online = ? 
            LIMIT 5
        ''', (user_data['classe'], user_id, True))
        
        return [{'id': c['id'], 'nome': f"{c['nome']} {c['cognome']}"} for c in classmates]
    
    def _get_badges_almost_unlocked(self, user_id: int, gamification_data: Dict) -> List[Dict]:
        """Badge quasi sbloccabili (>80% progresso)"""
        badges_close = []
        
        for badge in gamification_data.get('badges', []):
            if not badge.get('unlocked') and badge.get('progress', 0) >= 80:
                badges_close.append({
                    'id': badge['id'],
                    'name': badge['name'],
                    'progress': badge['progress'],
                    'xp_reward': badge.get('xp_reward', 100)
                })
        
        return badges_close
    
    def _analyze_streak_status(self, profile: Dict) -> Dict[str, Any]:
        """Analizza stato streak"""
        streak = profile['current_streak']
        last_activity = profile.get('last_activity_date')
        
        # Calcola se è emergenza (non attivo oggi)
        is_today = False
        if last_activity:
            last_date = datetime.strptime(last_activity, '%Y-%m-%d').date()
            is_today = last_date == datetime.now().date()
        
        return {
            'current': streak,
            'is_emergency': not is_today and streak > 5,
            'milestone_next': self._get_next_streak_milestone(streak),
            'protection_available': profile.get('streak_protection', 0) > 0
        }
    
    def _get_next_streak_milestone(self, current_streak: int) -> int:
        """Calcola prossimo milestone streak"""
        milestones = [7, 14, 30, 60, 100]
        for milestone in milestones:
            if current_streak < milestone:
                return milestone
        return 200
    
    def _detect_subject(self, message: str) -> Optional[str]:
        """Rileva materia dal messaggio"""
        message_lower = message.lower()
        
        for subject, keywords in self.subject_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return subject
        
        return None
    
    def _detect_sentiment(self, message: str) -> List[str]:
        """Rileva sentiment dal messaggio"""
        message_lower = message.lower()
        sentiments = []
        
        for sentiment_type, keywords in self.sentiment_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                sentiments.append(sentiment_type)
        
        return sentiments if sentiments else ['neutral']
    
    # ========== RESPONSE GENERATORS ==========
    
    def _streak_emergency_response(self, context: Dict) -> str:
        """Risposta emergenza streak"""
        streak = context['streak']
        nome = context['nome']
        protection = context['streak_status']['protection_available']
        
        response = f"🚨 **ALERT STREAK {nome}!**\n\n"
        response += f"Il tuo streak di **{streak} giorni** è in pericolo! 🔥\n"
        response += f"Non hai ancora fatto attività oggi!\n\n"
        
        if protection:
            response += "💎 Hai una protezione streak disponibile, ma perché sprecarla?\n\n"
        
        response += "⚡ **AZIONE RAPIDA** (5 minuti):\n"
        response += "1️⃣ Fai 1 quiz veloce → +30 XP + salva streak\n"
        response += "2️⃣ Manda 1 messaggio in chat classe → +5 XP\n"
        response += "3️⃣ Chiedi una domanda a me → +15 XP\n\n"
        
        response += f"Prossimo milestone: {context['streak_status']['milestone_next']} giorni!\n\n"
        response += "Vuoi un quiz veloce per salvare lo streak? 💪"
        
        return response
    
    def _help_response(self, context: Dict) -> str:
        """Risposta richiesta aiuto"""
        subject = context['detected_subject']
        nome = context['nome']
        
        if subject:
            # Aiuto specifico per materia
            subject_data = context['subject_progress'].get(subject, {})
            
            response = f"Ciao {nome}! 👋 Ti aiuto subito con **{subject}**!\n\n"
            
            if subject_data:
                accuracy = subject_data.get('accuracy', 0)
                weak_topics = subject_data.get('weak_topics', [])
                
                response += f"📊 Il tuo livello {subject}: {int(accuracy)}% accuracy\n\n"
                
                if weak_topics:
                    response += f"🎯 Argomenti da migliorare: {', '.join(weak_topics[:3])}\n\n"
            
            response += "💡 **Cosa vuoi fare?**\n"
            response += "A) Quiz di pratica (personalizzato per te)\n"
            response += "B) Spiegazione teorica argomento\n"
            response += "C) Chiedi aiuto a un compagno esperto\n\n"
            
            # Suggerisci compagni forti
            if context['classmates_online']:
                response += f"🤝 Compagni online ora: {', '.join([c['nome'] for c in context['classmates_online'][:3]])}\n\n"
            
            response += "Dimmi cosa preferisci! 🚀"
        else:
            # Aiuto generico
            response = f"Ciao {nome}! 😊 Come posso aiutarti?\n\n"
            response += "📚 Posso assisterti con:\n"
            response += "• Quiz personalizzati per studiare\n"
            response += "• Spiegazioni materie scolastiche\n"
            response += "• Suggerimenti studio\n"
            response += "• Connessioni con compagni di classe\n\n"
            response += "Quale materia stai studiando? 🎓"
        
        return response
    
    def _quiz_suggestion_response(self, context: Dict) -> str:
        """Risposta suggerimento quiz"""
        nome = context['nome']
        livello = context['livello']
        subject = context['detected_subject']
        
        response = f"Ottimo {nome}! 🎯 Preparati per un quiz!\n\n"
        
        if subject:
            # Quiz specifico per materia
            subject_data = context['subject_progress'].get(subject, {})
            accuracy = subject_data.get('accuracy', 50) if subject_data else 50
            
            # Determina difficoltà adattiva
            if accuracy < 60:
                difficulty = 'facile'
                xp = 30
            elif accuracy < 80:
                difficulty = 'medio'
                xp = 50
            else:
                difficulty = 'difficile'
                xp = 100
            
            response += f"📝 Quiz **{subject}** - Livello {difficulty.upper()}\n"
            response += f"🎁 Reward: +{xp} XP\n\n"
            
            # Badge vicini
            if context['badges_close']:
                badge = context['badges_close'][0]
                response += f"💫 Vicino a: Badge '{badge['name']}' ({badge['progress']}%)\n\n"
        else:
            response += f"📚 Scegli la materia per il quiz:\n"
            for subj in self.subjects[:5]:
                response += f"• {subj.capitalize()}\n"
            response += "\n"
        
        response += "Pronto a iniziare? Scrivi 'vai' per partire! 🚀"
        
        return response
    
    def _subject_specific_response(self, context: Dict) -> str:
        """Risposta specifica per materia"""
        subject = context['detected_subject']
        nome = context['nome']
        
        subject_data = context['subject_progress'].get(subject, {})
        
        response = f"📚 **{subject.upper()}** - Ciao {nome}!\n\n"
        
        if subject_data:
            xp = subject_data.get('xp', 0)
            accuracy = subject_data.get('accuracy', 0)
            total_quiz = subject_data.get('total_quizzes', 0)
            
            response += f"📊 Le tue stats {subject}:\n"
            response += f"• XP: {xp}\n"
            response += f"• Accuracy: {int(accuracy)}%\n"
            response += f"• Quiz completati: {total_quiz}\n\n"
            
            # Suggerimenti basati su performance
            if accuracy < 70:
                response += "💡 **Suggerimento**: Fai più quiz facili per consolidare le basi!\n\n"
            elif accuracy > 85:
                response += "🏆 **Ottimo livello!** Prova quiz difficili per il massimo XP!\n\n"
        
        response += "🎯 **Cosa vuoi fare?**\n"
        response += "• 'quiz' → Pratica con quiz\n"
        response += "• 'teoria' → Ripassa concetti\n"
        response += "• 'aiuto' → Chiedi a un compagno\n"
        
        return response
    
    def _badge_motivation_response(self, context: Dict) -> str:
        """Risposta motivazionale badge"""
        badge = context['badges_close'][0]
        nome = context['nome']
        
        response = f"🎊 Hey {nome}! Sei vicinissimo a un traguardo!\n\n"
        response += f"🏅 Badge: **{badge['name']}**\n"
        response += f"📈 Progresso: {badge['progress']}% completato\n"
        response += f"🎁 Reward: +{badge['xp_reward']} XP\n\n"
        response += "💪 Ancora un piccolo sforzo e lo sblocchi!\n\n"
        response += "Vuoi un quiz per raggiungerlo? 🚀"
        
        return response
    
    def _social_learning_response(self, context: Dict) -> str:
        """Risposta social learning"""
        nome = context['nome']
        classmates = context['classmates_online']
        
        response = f"👥 Ciao {nome}! I tuoi compagni sono online!\n\n"
        response += "🟢 Online ora:\n"
        for classmate in classmates[:3]:
            response += f"• {classmate['nome']}\n"
        response += "\n"
        response += "💡 **Idee per studiare insieme**:\n"
        response += "• Team quiz (2x XP bonus!)\n"
        response += "• Chat di studio di gruppo\n"
        response += "• Spiegate a vicenda gli argomenti\n\n"
        response += "Vuoi che ti metta in contatto? 🤝"
        
        return response
    
    def _personalized_greeting(self, context: Dict) -> str:
        """Saluto personalizzato"""
        nome = context['nome']
        livello = context['livello']
        streak = context['streak']
        
        greetings = [
            f"Ciao {nome}! 👋 Pronto per imparare qualcosa di nuovo?",
            f"Hey {nome}! 😊 Come posso aiutarti oggi?",
            f"Ciao {nome}! 🎓 Cosa studi oggi?"
        ]
        
        response = random.choice(greetings) + "\n\n"
        response += f"📊 Livello {livello} | Streak {streak} giorni 🔥\n\n"
        
        # Daily challenge reminder
        if context['daily_challenges']:
            challenges_left = len([c for c in context['daily_challenges'] if not c.get('completed')])
            if challenges_left > 0:
                response += f"🎯 Hai {challenges_left} daily challenges da completare!\n\n"
        
        response += "💬 Scrivi una materia o 'aiuto' per iniziare!"
        
        return response


# Inizializza sistema
skaila_brain = SKAILABrain()
print("✅ SKAILA AI Brain Engine inizializzato!")
