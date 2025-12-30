"""
SKAJLA AI Brain Engine - Sistema Intelligente Nativo
Chatbot completamente integrato nell'ecosistema SKAJLA
Zero dipendenze OpenAI - 100% personalizzato
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
from database_manager import db_manager
from gamification import gamification_system

class SKAJLABrain:
    """Cervello decisionale del chatbot SKAJLA"""

    def __init__(self):
        self.init_knowledge_base()

    def init_knowledge_base(self):
        """Inizializza la knowledge base SKAJLA"""
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

        # Knowledge Base per servizi SKAJLA
        self.skaila_services_kb = {
            'help': {
                'info': """SKAJLA è una piattaforma di apprendimento innovativa che integra didattica, gamification e social learning.
                Ecco cosa puoi fare:
                📚 **Studio Personalizzato**: Accedi a materiali didattici, quiz interattivi e spiegazioni dettagliate per ogni materia.
                🏆 **Gamification**: Guadagna XP, sali di livello, sblocca badge e mantieni la tua streak per rendere lo studio più divertente e motivante.
                📊 **Registro Elettronico**: Tieni traccia dei tuoi voti, assenze e progressi in tempo reale.
                👨‍🏫 **Funzionalità Docenti**: Carica facilmente materiali, gestisci le tue classi e monitora l'andamento degli studenti.
                👪 **Report Genitori**: Ricevi aggiornamenti chiari sui progressi dei tuoi figli.
                💬 **Chat e Social Learning**: Interagisci con compagni e docenti, collabora su progetti e impara insieme.

                Scrivi 'quiz [materia]' per iniziare a studiare, o chiedimi 'come funziona' per più dettagli su una funzionalità specifica! 😊"""
            },
            'didattica': {
                'info': """Il sistema didattico di SKAJLA offre una vasta gamma di risorse per ogni materia scolastica.
                Puoi accedere a:
                - 📖 Lezioni complete con spiegazioni dettagliate.
                - 📝 Esercizi interattivi e quiz di autovalutazione.
                - 🧠 Approfondimenti su argomenti specifici.
                - 💡 Suggerimenti personalizzati basati sui tuoi progressi.

                Inizia un quiz scrivendo 'quiz [materia]' (es. 'quiz matematica')."""
            },
            'gamification': {
                'info': """La gamification in SKAJLA trasforma lo studio in un gioco!
                - **XP (Experience Points)**: Guadagni XP completando quiz, partecipando a discussioni e raggiungendo obiettivi.
                - **Livelli**: Accumulando XP, sali di livello sbloccando nuove funzionalità e ricompense.
                - **Badge**: Ottieni badge per traguardi speciali (es. 'Knowledge Master', 'Streak Warrior').
                - **Streak**: Mantieni la tua sequenza di giorni attivi per massimizzare i bonus XP e la motivazione.

                Tieni d'occhio la tua streak e punta a nuovi badge! Scrivi 'mio livello' per vedere i tuoi progressi. 😉"""
            },
            'registro': {
                'info': """Il Registro Elettronico di SKAJLA ti permette di monitorare facilmente i tuoi risultati accademici.
                Puoi visualizzare:
                - 💯 Voti per ogni materia e compito.
                - 📅 Dettaglio delle assenze e puntualità.
                - 📝 Note e feedback dai docenti.
                - 📈 Statistiche sui tuoi progressi generali.

                Scrivi 'miei voti' per un riepilogo, o 'voti [materia]' per dettagli specifici."""
            },
            'funzionalita_professori': {
                'info': """Per i docenti, SKAJLA offre strumenti potenti per la gestione della classe e dei materiali didattici:
                - 📤 **Caricamento Materiali**: Carica facilmente PDF, video, presentazioni e altri contenuti per le tue lezioni.
                - 🧑‍🏫 **Gestione Classi**: Organizza studenti, crea gruppi e monitora l'andamento didattico.
                - 📝 **Creazione Quiz**: Genera quiz personalizzati per valutare la comprensione degli studenti.
                - 📊 **Report Studenti**: Accedi a report dettagliati sui progressi individuali e di classe.

                La gestione della didattica non è mai stata così semplice! """
            },
            'report_genitori': {
                'info': """I genitori possono seguire i progressi dei propri figli attraverso report chiari e dettagliati.
                - 📈 **Dashboard Progressi**: Visualizza le performance accademiche, i voti e le aree di miglioramento.
                - 📅 **Attività Giornaliera**: Tieni traccia dell'impegno dello studente sulla piattaforma.
                - 🏆 **Obiettivi Gamification**: Monitora i livelli e i badge sbloccati dal figlio.

                Rimani sempre aggiornato sull'educazione dei tuoi figli con SKAJLA."""
            },
            'sistema_scuole': {
                'info': """SKAJLA supporta anche la gestione amministrativa delle scuole:
                - 🏫 **Anagrafica Scolastica**: Gestione di codici identificativi, indirizzi e contatti.
                - 🧑‍🎓 **Gestione Classi e Alunni**: Organizzazione degli studenti per anno e classe.
                - 👨‍💼 **Ruoli Dirigenziali**: Accesso a dati aggregati e reportistica per dirigenti scolastici.

                Semplifica l'amministrazione scolastica con SKAJLA."""
            },
            'chat_social': {
                'info': """La sezione Chat e Social Learning di SKAJLA favorisce la collaborazione e la comunicazione:
                - 💬 **Chat di Classe**: Interagisci con i tuoi compagni e docenti su argomenti di studio.
                - 🤝 **Gruppi di Studio**: Crea o unisciti a gruppi per progetti collaborativi.
                - ❓ **Q&A Forum**: Poni domande e ottieni risposte dalla community.

                Impara meglio insieme agli altri! Scrivi 'compagni online' per vedere chi è disponibile."""
            }
        }


    def analyze_student_context(self, user_id: int, message: str) -> Dict[str, Any]:
        """Analizza il contesto completo dello studente"""

        # Profilo gamification
        gamification_data = gamification_system.get_user_dashboard(user_id)
        profile = gamification_data['profile']

        # Dati utente base
        user_data = db_manager.query('SELECT * FROM utenti WHERE id = %s', (user_id,), one=True)

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

        # DEFAULT: Saluto personalizzato / Risposte rapide info servizi
        return self._personalized_greeting(context)

    def _get_today_activity(self, user_id: int) -> Dict[str, int]:
        """Recupera attività di oggi"""
        messages_today = db_manager.query('''
            SELECT COUNT(*) as count FROM messaggi
            WHERE utente_id = %s AND DATE(timestamp) = CURRENT_DATE
        ''', (user_id,), one=True)

        ai_today = db_manager.query('''
            SELECT COUNT(*) as count FROM ai_conversations
            WHERE utente_id = %s AND DATE(timestamp) = CURRENT_DATE
        ''', (user_id,), one=True)

        quiz_today = db_manager.query('''
            SELECT COUNT(*) as count FROM student_quiz_history
            WHERE user_id = %s AND DATE(timestamp) = CURRENT_DATE
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
            WHERE user_id = %s
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
            WHERE classe = %s AND id != %s AND status_online = %s
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

        is_today = False
        if last_activity:
            if isinstance(last_activity, str):
                last_date = datetime.strptime(last_activity, '%Y-%m-%d').date()
            elif hasattr(last_activity, 'date'):
                last_date = last_activity.date() if callable(getattr(last_activity, 'date', None)) else last_activity
            else:
                last_date = last_activity
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

    def _personalized_greeting(self, context: Dict[str, Any]) -> str:
        """Saluto personalizzato e risposte rapide info servizi"""
        nome = context['nome']
        livello = context['livello']
        streak = context['streak']
        message = context['message_original'].lower()

        # Risposte rapide per info specifiche sui servizi SKAJLA
        if 'materiali didattici' in message or 'lezioni' in message or 'dispense' in message:
            return self.skaila_services_kb['didattica']['info']
        if 'gamification' in message or 'xp' in message or 'livelli' in message or 'badge' in message or 'streak' in message or 'achievement' in message:
            return self.skaila_services_kb['gamification']['info']
        if 'voti' in message or 'registro' in message or 'assenze' in message or 'media' in message:
            return self.skaila_services_kb['registro']['info']
        if 'professori' in message or 'docenti' in message or 'insegnanti' in message or 'carica materiale' in message:
            return self.skaila_services_kb['funzionalita_professori']['info']
        if 'genitori' in message or 'report figli' in message or 'progressi figli' in message:
            return self.skaila_services_kb['report_genitori']['info']
        if 'scuola' in message or 'istituto' in message or 'dirigente' in message:
            return self.skaila_services_kb['sistema_scuole']['info']
        if 'chat' in message or 'social' in message or 'compagni' in message or 'gruppo studio' in message:
            return self.skaila_services_kb['chat_social']['info']


        # Risposte rapide per info utente
        if 'mio livello' in message or 'miei progressi' in message:
            return self._show_user_progress(context)

        if 'miei badge' in message or 'achievement' in message:
            return self._show_user_badges(context)

        if 'miei voti' in message or 'registro' in message:
            return self._show_user_grades(context)

        if 'come funziona' in message or 'cosa posso fare' in message or 'aiuto generale' in message:
            return self.skaila_services_kb['help']['info']

        # Saluto standard
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

        response += "💬 **Comandi rapidi:**\n"
        response += "• 'quiz [materia]' → Pratica\n"
        response += "• 'mio livello' → Progressi\n"
        response += "• 'come funziona' → Guida\n"
        response += "• 'materiali' → Info materiali didattici\n"
        response += "• 'voti' → Registro Elettronico\n"
        response += "• 'badge' → I tuoi achievement\n"
        response += "• 'chat' → Social Learning\n"


        return response

    def _show_user_progress(self, context: Dict[str, Any]) -> str:
        """Mostra progressi utente dettagliati"""
        nome = context['nome']
        livello = context['livello']
        xp = context['xp_totale']
        streak = context['streak']

        response = f"📊 **PROGRESSI DI {nome.upper()}**\n\n"
        response += f"⭐ Livello: **{livello}**\n"
        response += f"💎 XP Totale: **{xp}**\n"
        response += f"🔥 Streak: **{streak} giorni**\n\n"

        # Progressi per materia
        if context['subject_progress']:
            response += "📚 **Performance per Materia:**\n"
            # Mostra solo le prime 3 materie per brevità
            for subject, data in list(context['subject_progress'].items())[:3]:
                response += f"• {subject.title()}: {int(data.get('accuracy', 0))}% accuracy, {data.get('xp', 0)} XP\n"
            if len(context['subject_progress']) > 3:
                response += "• ...e altre materie!\n"
            response += "\n"

        # Attività oggi
        if context['today_activity']:
            act = context['today_activity']
            response += "📅 **Oggi hai:**\n"
            response += f"• {act.get('quiz_completed', 0)} quiz completati\n"
            response += f"• {act.get('ai_interactions', 0)} domande AI\n"
            response += f"• {act.get('messages', 0)} messaggi chat\n\n"

        response += "Continua così! 💪 Scrivi 'miei badge' per vedere gli achievement!"
        return response

    def _show_user_badges(self, context: Dict[str, Any]) -> str:
        """Mostra badge utente"""
        response = "🏆 **I TUOI ACHIEVEMENT**\n\n"

        # Mostra badge quasi sbloccati
        if context['badges_close']:
            response += "🔓 **Badge Quasi Sbloccati:**\n"
            for badge in context['badges_close'][:3]: # Mostra i primi 3
                response += f"• {badge['name']} ({badge['progress']}%) - +{badge['xp_reward']} XP\n"
            response += "\n"

        # Esempi di badge e come sbloccarli (placeholder)
        response += "💡 **Come Sbloccare Badge:**\n"
        response += "• Knowledge Master → 100 quiz corretti\n"
        response += "• Speed Demon → Quiz in <30 secondi\n"
        response += "• Streak Warrior → 30 giorni consecutivi\n"
        response += "• Social Star → 500 messaggi chat\n\n"

        response += "Fai più quiz e interagisci per sbloccarli! 🚀"
        return response

    def _show_user_grades(self, context: Dict[str, Any]) -> str:
        """Mostra info voti (placeholder - richiede integrazione registro)"""
        nome = context['nome']
        response = f"📊 **REGISTRO DI {nome.upper()}**\n\n"
        response += "Per visualizzare i tuoi voti dettagliati, accedi alla sezione:\n"
        response += "➡️ **Registro Elettronico** nel menu principale.\n\n"
        response += "Oppure chiedimi:\n"
        response += "• 'voti [materia]' → Voti specifici per materia\n"
        response += "• 'mia media' → Calcolo della media generale\n"
        response += "• 'assenze' → Dettaglio presenze\n"
        return response


# Inizializza sistema
skaila_brain = SKAJLABrain()
print("✅ SKAJLA AI Brain Engine inizializzato!")