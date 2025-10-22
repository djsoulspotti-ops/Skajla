
import random
import json
from datetime import datetime, timedelta
import re
import openai
import os
from typing import Dict, List, Any, Tuple
from database_manager import db_manager

class AISkailaBot:
    def __init__(self):
        # Configurazione OpenAI
        self.openai_available = False
        self.setup_openai()
        
        # Modelli disponibili
        self.models = {
            'gpt-4': {
                'name': 'gpt-4',
                'max_tokens': 8192,
                'cost_per_1k_input': 0.03,
                'cost_per_1k_output': 0.06,
                'best_for': ['complex_reasoning', 'creative_writing', 'detailed_explanations']
            },
            'gpt-3.5-turbo': {
                'name': 'gpt-3.5-turbo',
                'max_tokens': 4096,
                'cost_per_1k_input': 0.0015,
                'cost_per_1k_output': 0.002,
                'best_for': ['quick_responses', 'simple_questions', 'general_chat']
            }
        }
        
        # Sistema di personalità avanzato
        self.personality_system = {
            'core_traits': {
                'empathetic': 0.9,
                'encouraging': 0.95,
                'knowledgeable': 0.9,
                'patient': 0.95,
                'creative': 0.8,
                'motivational': 0.9
            },
            'conversation_memory': {},
            'user_preferences': {},
            'emotional_intelligence': True
        }

        # Context del sistema SKAILA
        self.system_context = """
        Sei SKAILA Assistant, un tutor AI intelligente e personalizzato per studenti italiani.
        
        PERSONALITÀ:
        - Empatico e incoraggiante
        - Esperto in pedagogia e didattica
        - Paziente e motivazionale
        - Adatta il linguaggio all'età dello studente
        - Usa emoji in modo appropriato ma non eccessivo
        
        COMPETENZE:
        - Tutte le materie scolastiche (matematica, italiano, storia, scienze, informatica, inglese, etc.)
        - Metodologie di studio personalizzate
        - Supporto emotivo e motivazionale
        - Gamification e apprendimento ludico
        
        STILE:
        - Risposte chiare e strutturate
        - Esempi pratici e relatable
        - Passo-dopo-passo per concetti complessi
        - Incoraggiamento costante
        - Linguaggio amichevole ma professionale
        
        OBIETTIVO:
        Aiutare ogni studente a raggiungere il proprio potenziale massimo attraverso apprendimento personalizzato.
        """

    def setup_openai(self):
        """Configura l'API OpenAI"""
        try:
            # Prova a caricare la chiave API da variabili d'ambiente
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                openai.api_key = api_key
                self.openai_available = True
                print("✅ OpenAI API configurata con successo!")
                
                # Test connessione
                self.test_openai_connection()
            else:
                print("⚠️ OPENAI_API_KEY non trovata - usando risposte mock avanzate")
                self.openai_available = False
        except Exception as e:
            print(f"❌ Errore configurazione OpenAI: {e}")
            self.openai_available = False

    def test_openai_connection(self):
        """Testa la connessione con OpenAI"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            print("✅ Connessione OpenAI testata con successo!")
            return True
        except Exception as e:
            print(f"❌ Test connessione OpenAI fallito: {e}")
            self.openai_available = False
            return False

    def select_optimal_model(self, message: str, user_profile: Dict) -> str:
        """Seleziona il modello OpenAI ottimale basato sul contesto"""
        message_length = len(message.split())
        complexity_keywords = ['spiega', 'analizza', 'confronta', 'dimostra', 'perché', 'come funziona']
        
        # Usa GPT-4 per richieste complesse
        if (message_length > 50 or 
            any(keyword in message.lower() for keyword in complexity_keywords) or
            user_profile.get('difficulty_preference') == 'advanced'):
            return 'gpt-4'
        
        # Usa GPT-3.5-turbo per richieste semplici
        return 'gpt-3.5-turbo'

    def build_conversation_context(self, message: str, user_name: str, user_profile: Dict, user_id: int) -> List[Dict]:
        """Costruisce il contesto della conversazione per OpenAI"""
        
        # Sistema message con personalizzazione
        system_msg = f"{self.system_context}\n\n"
        system_msg += f"STUDENTE: {user_name}\n"
        system_msg += f"PROFILO: {user_profile.get('conversation_style', 'friendly')}\n"
        system_msg += f"STILE APPRENDIMENTO: {user_profile.get('learning_preferences', 'adaptive')}\n"
        
        if user_profile.get('subject_strengths'):
            system_msg += f"PUNTI FORTI: {', '.join(user_profile.get('subject_strengths', []))}\n"
        if user_profile.get('subject_weaknesses'):
            system_msg += f"AREE DA MIGLIORARE: {', '.join(user_profile.get('subject_weaknesses', []))}\n"
            
        messages = [{"role": "system", "content": system_msg}]
        
        # Aggiungi cronologia recente (ultimi 5 messaggi)
        try:
            recent_conversations = db_manager.query('''
                SELECT message, response FROM ai_conversations 
                WHERE utente_id = %s 
                ORDER BY timestamp DESC 
                LIMIT 5
            ''', (user_id,))
            
            # Aggiungi in ordine cronologico
            for conv in reversed(recent_conversations):
                messages.append({"role": "user", "content": conv.get('message')})
                messages.append({"role": "assistant", "content": conv.get('response')})
                
        except Exception as e:
            print(f"Errore caricamento cronologia: {e}")
        
        # Aggiungi messaggio corrente
        messages.append({"role": "user", "content": message})
        
        return messages

    def generate_response(self, message: str, user_name: str, user_role: str, user_id: int) -> str:
        """Genera una risposta AI usando OpenAI o fallback intelligente"""
        
        # Carica profilo utente
        user_profile = self.load_user_profile(user_id)
        
        if self.openai_available:
            return self.generate_openai_response(message, user_name, user_profile, user_id)
        else:
            return self.generate_enhanced_fallback_response(message, user_name, user_profile, user_id)

    def generate_openai_response(self, message: str, user_name: str, user_profile: Dict, user_id: int) -> str:
        """Genera risposta usando OpenAI API"""
        try:
            # Seleziona modello ottimale
            model = self.select_optimal_model(message, user_profile)
            
            # Costruisci contesto
            messages = self.build_conversation_context(message, user_name, user_profile, user_id)
            
            # Chiamata a OpenAI
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Post-processing per migliorare la risposta
            ai_response = self.post_process_response(ai_response, user_profile)
            
            print(f"✅ Risposta OpenAI generata ({model}): {ai_response[:50]}...")
            return ai_response
            
        except Exception as e:
            print(f"❌ Errore OpenAI: {e}")
            # Fallback a risposta mock avanzata
            return self.generate_enhanced_fallback_response(message, user_name, user_profile, user_id)

    def post_process_response(self, response: str, user_profile: Dict) -> str:
        """Post-processa la risposta per migliorarla"""
        
        # Aggiungi emoji appropriati se il profilo lo richiede
        if user_profile.get('conversation_style') == 'friendly':
            if 'matematica' in response.lower() and '📊' not in response:
                response = response.replace('matematica', 'matematica 📊')
            if 'fisica' in response.lower() and '⚗️' not in response:
                response = response.replace('fisica', 'fisica ⚗️')
            if 'informatica' in response.lower() and '💻' not in response:
                response = response.replace('informatica', 'informatica 💻')
        
        # Assicurati che la risposta sia incoraggiante
        encouraging_endings = [
            "\n\nContinua così, stai facendo un ottimo lavoro! 🌟",
            "\n\nSei sulla strada giusta! 💪",
            "\n\nOttima domanda! Questo dimostra che stai pensando! 🧠"
        ]
        
        if not any(ending.strip() in response for ending in encouraging_endings):
            if len(response) > 200:  # Solo per risposte lunghe
                response += random.choice(encouraging_endings)
        
        return response

    def generate_enhanced_fallback_response(self, message: str, user_name: str, user_profile: Dict, user_id: int) -> str:
        """Genera risposta fallback avanzata quando OpenAI non è disponibile"""
        
        # Analizza il messaggio
        subject = self.detect_subject(message)
        sentiment = self.analyze_user_sentiment(message)
        learning_style = self.detect_learning_style_preference(message, user_profile)
        
        # Risposte specifiche per soggetto
        if subject == 'matematica':
            return self.generate_math_response(message, user_profile)
        elif subject == 'informatica':
            return self.generate_programming_response(message, user_profile)
        elif 'aiuto' in message.lower() or 'help' in message.lower():
            return self.generate_help_response(user_name, user_profile)
        elif self.is_greeting(message):
            return self.generate_greeting(user_name, user_profile)
        else:
            return self.generate_general_response(message, subject, user_profile)

    def generate_math_response(self, message: str, user_profile: Dict) -> str:
        """Genera risposta specifica per matematica"""
        if 'algebra' in message.lower():
            return """🔢 **Algebra** - Il linguaggio della matematica!

L'algebra usa lettere (variabili) per rappresentare numeri sconosciuti. Ecco alcuni concetti chiave:

📚 **Concetti Base:**
• Le variabili (x, y, z) sono "scatole" che contengono numeri
• Le equazioni sono "bilance" che devono restare in equilibrio
• Quello che fai a sinistra, fallo anche a destra!

💡 **Esempio Pratico:**
Se x + 5 = 12, quanto vale x?
- Sottrai 5 da entrambi i lati: x + 5 - 5 = 12 - 5
- Risultato: x = 7

🎯 **Trucco per Ricordare:**
Pensa alle equazioni come a una bilancia: mantieni sempre l'equilibrio!

Hai qualche esercizio specifico su cui lavorare? 🚀"""

        elif 'geometria' in message.lower():
            return """📐 **Geometria** - Il mondo delle forme!

La geometria studia forme, dimensioni e spazi. È ovunque intorno a noi!

🔍 **Concetti Fondamentali:**
• Punti, linee, angoli
• Triangoli, quadrati, cerchi
• Perimetri, aree, volumi

📏 **Formule Essenziali:**
• Area rettangolo = base × altezza
• Area triangolo = (base × altezza) / 2
• Circonferenza = 2 × π × raggio

💭 **Consiglio di Studio:**
Disegna sempre! La geometria si capisce meglio visualizzando.

Su quale figura geometrica vuoi concentrarti? 🎨"""
        
        return "🔢 Matematica è fantastica! Su quale argomento specifico posso aiutarti? Algebra, geometria, calcolo? Dimmi tutto! 📊"

    def generate_programming_response(self, message: str, user_profile: Dict) -> str:
        """Genera risposta specifica per programmazione"""
        return """💻 **Programmazione** - Creare il futuro con il codice!

🚀 **Concetti Base:**
• Algoritmi: ricette step-by-step per il computer
• Variabili: contenitori per i dati
• Funzioni: blocchi di codice riutilizzabili

🐍 **Esempio Python:**
```python
def saluta(nome):
    return f"Ciao {nome}! Benvenuto in SKAILA!"

print(saluta("Studente"))
```

💡 **Consiglio:**
Inizia sempre con problemi piccoli e costruisci passo dopo passo!

Su quale linguaggio o concetto vuoi lavorare? 🔧"""

    def load_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Carica il profilo AI personalizzato dell'utente"""
        try:
            profile = db_manager.query('''
                SELECT * FROM ai_profiles WHERE utente_id = %s
            ''', (user_id,), one=True)

            if not profile:
                # Crea profilo di default
                default_profile = {
                    'bot_name': 'SKAILA Assistant',
                    'bot_avatar': '🤖',
                    'conversation_style': 'friendly',
                    'learning_preferences': 'adaptive',
                    'difficulty_preference': 'adaptive',
                    'subject_strengths': [],
                    'subject_weaknesses': [],
                    'personality_traits': ['empathetic', 'supportive'],
                    'total_interactions': 0,
                    'success_rate': 0.0
                }

                # Crea profilo nel database
                try:
                    db_manager.execute('''
                        INSERT INTO ai_profiles 
                        (utente_id, bot_name, bot_avatar, conversation_style, learning_preferences, 
                         difficulty_preference, personality_traits)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (user_id, default_profile['bot_name'], default_profile['bot_avatar'],
                          default_profile['conversation_style'], default_profile['learning_preferences'],
                          default_profile['difficulty_preference'], 'empathetic,supportive'))
                except Exception:
                    pass  # Tabella potrebbe non esistere, usa profilo default
                
                return default_profile

            # Converti database row in dict
            profile_dict = {
                'bot_name': profile.get('bot_name', 'SKAILA Assistant'),
                'bot_avatar': profile.get('bot_avatar', '🤖'),
                'conversation_style': profile.get('conversation_style', 'friendly'),
                'learning_preferences': profile.get('learning_preferences', 'adaptive'),
                'difficulty_preference': profile.get('difficulty_preference', 'adaptive'),
                'subject_strengths': (profile.get('subject_strengths') or '').split(',') if profile.get('subject_strengths') else [],
                'subject_weaknesses': (profile.get('subject_weaknesses') or '').split(',') if profile.get('subject_weaknesses') else [],
                'personality_traits': (profile.get('personality_traits') or 'empathetic,supportive').split(','),
                'total_interactions': profile.get('total_interactions', 0),
                'success_rate': profile.get('success_rate', 0.0)
            }

            return profile_dict

        except Exception as e:
            print(f"Error loading user profile: {e}")
            return self.get_default_profile()

    def get_default_profile(self) -> Dict[str, Any]:
        """Restituisce un profilo di default"""
        return {
            'bot_name': 'SKAILA Assistant',
            'bot_avatar': '🤖',
            'conversation_style': 'friendly',
            'learning_preferences': 'adaptive',
            'difficulty_preference': 'adaptive',
            'subject_strengths': [],
            'subject_weaknesses': [],
            'personality_traits': ['empathetic', 'supportive'],
            'total_interactions': 0,
            'success_rate': 0.0
        }

    def detect_subject(self, message: str) -> str:
        """Rileva la materia dal messaggio dell'utente"""
        message_lower = message.lower()

        subject_keywords = {
            'matematica': ['matematica', 'algebra', 'geometria', 'calcolo', 'equazione', 'numero', 'frazione'],
            'informatica': ['informatica', 'programmazione', 'codice', 'computer', 'python', 'javascript'],
            'italiano': ['italiano', 'grammatica', 'letteratura', 'poesia', 'romanzo'],
            'storia': ['storia', 'guerra', 'impero', 'rivoluzione', 'antichità'],
            'inglese': ['inglese', 'english', 'grammar', 'vocabulary'],
            'fisica': ['fisica', 'forza', 'energia', 'velocità', 'accelerazione'],
            'chimica': ['chimica', 'molecola', 'atomo', 'reazione'],
            'biologia': ['biologia', 'cellula', 'DNA', 'evoluzione']
        }

        for subject, keywords in subject_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return subject

        return 'generale'

    def analyze_user_sentiment(self, message: str) -> List[str]:
        """Analizza il sentiment dell'utente"""
        message_lower = message.lower()
        sentiments = []

        # Sentimenti positivi
        if any(word in message_lower for word in ['grazie', 'perfetto', 'ottimo', 'bene', 'fantastico']):
            sentiments.append('positive')

        # Frustrazione
        if any(word in message_lower for word in ['non capisco', 'difficile', 'aiuto', 'problema', 'confuso']):
            sentiments.append('frustrated')

        # Curiosità
        if any(word in message_lower for word in ['perché', 'come', 'cosa', 'interessante', 'voglio sapere']):
            sentiments.append('curious')

        # Motivazione
        if any(word in message_lower for word in ['imparo', 'studio', 'esame', 'test']):
            sentiments.append('motivated')

        return sentiments if sentiments else ['neutral']

    def detect_learning_style_preference(self, message: str, user_profile: Dict) -> str:
        """Rileva lo stile di apprendimento preferito dal contesto"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['schema', 'grafico', 'immagine', 'vedo', 'mostra']):
            return 'visual'
        if any(word in message_lower for word in ['spiegami', 'raccontami', 'dimmi', 'sento']):
            return 'auditory'
        if any(word in message_lower for word in ['esempio', 'pratica', 'provo', 'faccio']):
            return 'kinesthetic'

        return user_profile.get('learning_preferences', 'adaptive')

    def is_greeting(self, message: str) -> bool:
        """Controlla se il messaggio è un saluto"""
        greetings = ['ciao', 'salve', 'buongiorno', 'buonasera', 'hey', 'hello', 'hi']
        return any(greeting in message.lower() for greeting in greetings)

    def is_question(self, message: str) -> bool:
        """Controlla se il messaggio contiene una domanda"""
        question_indicators = ['?', 'come', 'cosa', 'quando', 'dove', 'perché', 'chi', 'quale', 'quanto']
        return any(indicator in message.lower() for indicator in question_indicators)

    def generate_greeting(self, user_name: str, user_profile: Dict) -> str:
        """Genera un saluto personalizzato"""
        bot_name = user_profile.get('bot_name', 'SKAILA Assistant')
        style = user_profile.get('conversation_style', 'friendly')
        
        if style == 'friendly':
            greetings = [
                f"Ciao {user_name}! 👋 Sono {bot_name}, pronto ad aiutarti con i tuoi studi!",
                f"Hey {user_name}! 😊 È {bot_name} qui! Come posso supportarti oggi?",
                f"Salve {user_name}! 🌟 Sono {bot_name}, il tuo tutor AI personale!"
            ]
        else:
            greetings = [
                f"Buongiorno {user_name}. Sono {bot_name}, come posso assisterla?",
                f"Salve {user_name}. {bot_name} al suo servizio per l'apprendimento."
            ]
        
        return random.choice(greetings)

    def generate_help_response(self, user_name: str, user_profile: Dict) -> str:
        """Genera una risposta di aiuto personalizzata"""
        bot_name = user_profile.get('bot_name', 'SKAILA Assistant')
        
        return f"""🎓 **Ciao {user_name}! Sono {bot_name}** 

Posso aiutarti con:

📚 **MATERIE:**
• Matematica (algebra, geometria, calcolo)
• Informatica (programmazione, algoritmi)
• Italiano (grammatica, letteratura)
• Storia, Inglese, Fisica, Scienze

🎯 **MODALITÀ DI AIUTO:**
• Spiegazioni passo-dopo-passo
• Esempi pratici e esercizi
• Risoluzione di problemi
• Preparazione esami e test
• Supporto emotivo e motivazione

💡 **COME FUNZIONO:**
Mi adatto al tuo stile di apprendimento e livello. Dimmi semplicemente cosa vuoi studiare!

**Esempio:** "Aiutami con le equazioni di secondo grado" o "Non capisco la fotosintesi"

Cosa vuoi imparare oggi? 🚀"""

    def generate_general_response(self, message: str, subject: str, user_profile: Dict) -> str:
        """Genera una risposta generale contestuale"""
        responses = [
            f"Interessante domanda su {subject}! Lascia che ti aiuti a esplorare questo argomento.",
            f"Ottima curiosità! Vediamo insieme come approfondire {subject}.",
            f"Perfetto! {subject.title()} è un argomento affascinante. Come posso aiutarti?"
        ]
        
        return random.choice(responses)

    # Metodi aggiuntivi per compatibilità
    def generate_adaptive_quiz_question(self, subject: str, user_profile: Dict, difficulty: str) -> Dict[str, Any]:
        """Genera una domanda di quiz personalizzata"""
        return {
            'question': f"Dimmi cosa vorresti approfondire in {subject}?",
            'type': 'open',
            'subject': subject,
            'difficulty': difficulty,
            'personalized': True
        }

    def get_learning_analytics(self, user_id: int) -> Dict[str, Any]:
        """Ottieni analytics di apprendimento per l'utente"""
        try:
            # Conversazioni per materia
            subject_stats = db_manager.query('''
                SELECT subject_detected, COUNT(*) as count
                FROM ai_conversations 
                WHERE utente_id = %s AND subject_detected IS NOT NULL
                GROUP BY subject_detected
            ''', (user_id,))

            # Statistiche temporali
            weekly_activity_result = db_manager.query('''
                SELECT COUNT(*) as count FROM ai_conversations 
                WHERE utente_id = %s AND timestamp > NOW() - INTERVAL '7 days'
            ''', (user_id,), one=True)
            weekly_activity = weekly_activity_result.get('count', 0) if weekly_activity_result else 0

            return {
                'subject_performance': [{'subject_detected': row.get('subject_detected'), 'count': row.get('count'), 'avg_success': 0.8} for row in subject_stats],
                'progress_metrics': {
                    'weekly_activity': weekly_activity,
                    'total_sessions': sum(row.get('count', 0) for row in subject_stats),
                    'avg_success_rate': 0.75
                },
                'sentiment_analysis': [],
                'learning_insights': ['Continua così!', 'Stai migliorando costantemente']
            }

        except Exception as e:
            print(f"Error getting learning analytics: {e}")
            return {
                'subject_performance': [],
                'progress_metrics': {'weekly_activity': 0, 'total_sessions': 0, 'avg_success_rate': 0},
                'sentiment_analysis': [],
                'learning_insights': ['Inizia a fare più domande per ottenere insights!']
            }

    def generate_learning_recommendations(self, user_id: int, analytics: Dict) -> List[str]:
        """Genera raccomandazioni personalizzate"""
        return [
            "🎯 Prova a studiare almeno 3 volte a settimana",
            "📚 Diversifica le materie per un apprendimento completo", 
            "🌟 Continua con questo ritmo!"
        ]

    def generate_daily_goals(self, user_profile: Dict) -> List[str]:
        """Genera obiettivi giornalieri personalizzati"""
        return [
            "🎓 Fai almeno una domanda su una materia oggi",
            "📖 Rivedi un concetto difficile",
            "🧠 Prova un quiz in una nuova materia"
        ]
