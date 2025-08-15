import random
import json
from datetime import datetime, timedelta
import sqlite3
import re
import openai
import os
from typing import Dict, List, Any, Tuple

class AISkailaBot:
    def __init__(self):
        # Configurazione OpenAI (se disponibile)
        self.openai_available = False
        try:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if openai.api_key:
                self.openai_available = True
                print("✅ OpenAI API configured")
        except:
            print("⚠️ OpenAI API not configured - using enhanced mock responses")

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

        # Database di conoscenze espanso
        self.knowledge_base = {
            'matematica': {
                'concetti': {
                    'algebra': {
                        'spiegazione': "L'algebra è il linguaggio della matematica che usa lettere per rappresentare numeri sconosciuti.",
                        'esempi': ["Se x + 5 = 12, allora x = 7", "2y = 10 significa y = 5"],
                        'trucchi': ["Ricorda: quello che fai a sinistra dell'uguale, fallo anche a destra!", "Le lettere sono solo numeri misteriosi che aspettano di essere scoperti!"],
                        'difficolta_comune': "Molti studenti confondono le operazioni inverse - ricorda che addizione e sottrazione sono opposte!"
                    },
                    'geometria': {
                        'spiegazione': "La geometria studia le forme, le dimensioni e le proprietà dello spazio.",
                        'esempi': ["Un triangolo ha sempre angoli che sommano 180°", "L'area del rettangolo = base × altezza"],
                        'trucchi': ["Visualizza sempre! Disegna la figura per capire meglio", "Ogni teorema ha una storia - cerca di capire il 'perché'"],
                        'difficolta_comune': "Le dimostrazioni sembrano difficili, ma sono solo una conversazione logica!"
                    }
                },
                'strategie_studio': [
                    "Pratica ogni giorno 15-20 minuti invece di studiare 3 ore una volta a settimana",
                    "Spiega i concetti a voce alta o a un amico - se non riesci a spiegarlo, non l'hai capito"
                ]
            },
            'informatica': {
                'concetti': {
                    'programmazione': {
                        'spiegazione': "Programmare è come scrivere ricette molto precise per il computer.",
                        'esempi': [
                            "print('Ciao mondo!') dice al computer di mostrare un messaggio"
                        ],
                        'trucchi': [
                            "Inizia sempre con problemi piccoli e costruisci passo dopo passo"
                        ]
                    }
                }
            },
            'generale': {
                'concetti': {
                    'studio': {
                        'spiegazione': "Lo studio efficace richiede metodo e costanza.",
                        'trucchi': ["Organizza il tempo", "Fai pause regolari"]
                    }
                }
            }
        }

        # Stili di conversazione
        self.conversation_styles = {
            'friendly': {
                'greeting': ['Ciao! 👋', 'Ehi! Come posso aiutarti?', 'Salve! Sono qui per te! 😊'],
                'encouragement': ['Ottimo lavoro!', 'Stai andando benissimo!', 'Continua così! 🚀'],
                'tone': 'casual e amichevole',
                'emoji_usage': 'alto'
            },
            'professional': {
                'greeting': ['Buongiorno', 'Salve, come posso assisterla?', 'Benvenuto'],
                'encouragement': ['Eccellente', 'Molto bene', 'Ottimo progresso'],
                'tone': 'formale e rispettoso',
                'emoji_usage': 'basso'
            }
        }

        # Risposte emotive
        self.emotional_responses = {
            'frustrated': [
                "Capisco perfettamente la tua frustrazione! 😤 È normale sentirsi così quando si affronta qualcosa di nuovo.",
                "La frustrazione è il segnale che stai sfidando te stesso! 💪 Facciamo un passo indietro e affrontiamo questo insieme."
            ],
            'confused': [
                "Non preoccuparti, la confusione è l'inizio della comprensione! 🤔 Scomponiamo tutto passo per passo.",
                "È normale sentirsi confusi! 🌟 Andiamo piano e chiariamo tutto insieme."
            ],
            'confident': [
                "Wow! Sento la tua sicurezza! 🔥 Continua così!",
                "Fantastico! La fiducia in se stessi è metà del successo! 🚀"
            ]
        }

    def load_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Carica il profilo AI personalizzato dell'utente"""
        try:
            conn = sqlite3.connect('skaila.db')
            cursor = conn.cursor()

            profile = cursor.execute('''
                SELECT * FROM ai_profiles WHERE utente_id = ?
            ''', (user_id,)).fetchone()

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

                cursor.execute('''
                    INSERT INTO ai_profiles 
                    (utente_id, bot_name, bot_avatar, conversation_style, learning_preferences, 
                     difficulty_preference, personality_traits)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, default_profile['bot_name'], default_profile['bot_avatar'],
                      default_profile['conversation_style'], default_profile['learning_preferences'],
                      default_profile['difficulty_preference'], 'empathetic,supportive'))
                conn.commit()
                conn.close()
                return default_profile

            conn.close()

            # Converti Row in dict manualmente
            profile_dict = {
                'bot_name': profile[1] if len(profile) > 1 else 'SKAILA Assistant',
                'bot_avatar': profile[2] if len(profile) > 2 else '🤖',
                'conversation_style': profile[3] if len(profile) > 3 else 'friendly',
                'learning_preferences': profile[4] if len(profile) > 4 else 'adaptive',
                'difficulty_preference': profile[5] if len(profile) > 5 else 'adaptive',
                'subject_strengths': (profile[6] or '').split(',') if len(profile) > 6 and profile[6] else [],
                'subject_weaknesses': (profile[7] or '').split(',') if len(profile) > 7 and profile[7] else [],
                'personality_traits': (profile[8] or 'empathetic,supportive').split(',') if len(profile) > 8 else ['empathetic', 'supportive'],
                'total_interactions': profile[11] if len(profile) > 11 else 0,
                'success_rate': profile[12] if len(profile) > 12 else 0.0
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
            'matematica': ['matematica', 'algebra', 'geometria', 'calcolo', 'equazione'],
            'informatica': ['informatica', 'programmazione', 'codice', 'computer'],
            'italiano': ['italiano', 'grammatica', 'letteratura'],
            'storia': ['storia', 'guerra', 'impero'],
            'inglese': ['inglese', 'english', 'grammar'],
            'fisica': ['fisica', 'forza', 'energia']
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
        if any(word in message_lower for word in ['grazie', 'perfetto', 'ottimo', 'bene']):
            sentiments.append('positive')

        # Frustrazione
        if any(word in message_lower for word in ['non capisco', 'difficile', 'aiuto', 'problema']):
            sentiments.append('frustrated')

        # Curiosità
        if any(word in message_lower for word in ['perché', 'come', 'cosa', 'interessante']):
            sentiments.append('curious')

        return sentiments if sentiments else ['neutral']

    def detect_learning_style_preference(self, message: str, user_profile: Dict) -> str:
        """Rileva lo stile di apprendimento preferito dal contesto"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['schema', 'grafico', 'immagine']):
            return 'visual'
        if any(word in message_lower for word in ['spiegami', 'raccontami', 'dimmi']):
            return 'auditory'
        if any(word in message_lower for word in ['esempio', 'pratica', 'provo']):
            return 'kinesthetic'

        return user_profile.get('learning_preferences', 'adaptive')

    def generate_response(self, message: str, user_name: str, user_role: str, user_id: int) -> str:
        """Genera una risposta AI personalizzata e intelligente"""
        try:
            # Carica profilo utente
            user_profile = self.load_user_profile(user_id)

            # Analizza il messaggio
            subject = self.detect_subject(message)
            sentiment = self.analyze_user_sentiment(message)
            learning_style = self.detect_learning_style_preference(message, user_profile)

            # Seleziona stile di conversazione
            conv_style = user_profile.get('conversation_style', 'friendly')
            style_config = self.conversation_styles.get(conv_style, self.conversation_styles['friendly'])

            # Genera risposta basata sul contenuto
            if self.is_greeting(message):
                return self.generate_greeting(user_name, style_config, user_profile)
            elif self.is_question(message) or 'dimmi' in message.lower():
                return self.generate_educational_response(message, subject, sentiment, learning_style, style_config, user_profile)
            elif 'aiuto' in message.lower() or 'help' in message.lower():
                return self.generate_help_response()
            else:
                return self.generate_contextual_response(message, subject, sentiment, style_config, user_profile)

        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "Mi dispiace, ho avuto un piccolo problema tecnico. Puoi riprovare a farmi la domanda? 🤖"

    def is_greeting(self, message: str) -> bool:
        """Controlla se il messaggio è un saluto"""
        greetings = ['ciao', 'salve', 'buongiorno', 'buonasera', 'hey', 'hello']
        return any(greeting in message.lower() for greeting in greetings)

    def is_question(self, message: str) -> bool:
        """Controlla se il messaggio contiene una domanda"""
        question_indicators = ['?', 'come', 'cosa', 'quando', 'dove', 'perché', 'chi', 'quale', 'quanto']
        return any(indicator in message.lower() for indicator in question_indicators)

    def generate_greeting(self, user_name: str, style_config: Dict, user_profile: Dict) -> str:
        """Genera un saluto personalizzato"""
        greeting = random.choice(style_config['greeting'])
        bot_name = user_profile.get('bot_name', 'SKAILA Assistant')

        return f"{greeting} Sono {bot_name}, il tuo assistente di apprendimento personalizzato! Come posso aiutarti oggi con i tuoi studi?"

    def generate_educational_response(self, message: str, subject: str, sentiment: List[str], 
                                   learning_style: str, style_config: Dict, user_profile: Dict) -> str:
        """Genera una risposta educativa personalizzata"""

        # Risposta specifica per richieste generali
        if any(word in message.lower() for word in ['cosa puoi fare', 'dimmi tutto', 'tutte le cose']):
            return self.generate_capabilities_response(user_profile)

        # Base della risposta basata sulla materia
        if subject in self.knowledge_base:
            response = self.get_subject_specific_response(message, subject, learning_style)
        else:
            response = "È una domanda interessante! Vediamo come posso aiutarti a comprenderla meglio."

        # Adatta il tono al sentiment
        if 'frustrated' in sentiment:
            response = f"Capisco che possa sembrare complicato, non preoccuparti! {response}"
        elif 'curious' in sentiment:
            response = f"Ottima domanda! La curiosità è la chiave dell'apprendimento. {response}"

        # Aggiungi incoraggiamento
        if 'supportive' in user_profile.get('personality_traits', []):
            response += f" {random.choice(style_config['encouragement'])}"

        return response

    def generate_capabilities_response(self, user_profile: Dict) -> str:
        """Genera una risposta completa sulle capacità del bot"""
        bot_name = user_profile.get('bot_name', 'SKAILA Assistant')

        capabilities = [
            f"Ciao! Sono {bot_name} 🤖 e posso aiutarti in tantissimi modi:",
            "",
            "📚 **MATERIE SUPPORTATE:**",
            "• Matematica (algebra, geometria, calcolo)",
            "• Informatica (programmazione, algoritmi)",
            "• Italiano (grammatica, letteratura)",
            "• Storia, Inglese, Fisica e altre materie",
            "",
            "🎯 **COSA POSSO FARE:**",
            "• Spiegazioni personalizzate per il tuo stile di apprendimento",
            "• Esercizi e quiz su misura",
            "• Risoluzione di problemi passo dopo passo",
            "• Suggerimenti di studio efficaci",
            "• Motivazione e supporto emotivo",
            "• Analisi dei tuoi progressi",
            "",
            "💡 **STILI DI APPRENDIMENTO:**",
            "• Visuale (schemi, grafici, mappe)",
            "• Uditivo (spiegazioni vocali, discussioni)",
            "• Cinestetico (esempi pratici, esperimenti)",
            "• Lettura/Scrittura (testi, riassunti)",
            "",
            "🚀 **CARATTERISTICHE SPECIALI:**",
            "• Mi adatto al tuo livello di conoscenza",
            "• Ricordo le tue preferenze e punti deboli",
            "• Offro incoraggiamento quando ne hai bisogno",
            "• Creo piani di studio personalizzati",
            "",
            "Dimmi semplicemente su cosa vuoi lavorare e come posso aiutarti! 😊"
        ]

        return "\n".join(capabilities)

    def get_subject_specific_response(self, message: str, subject: str, learning_style: str) -> str:
        """Genera risposte specifiche per materia"""
        if subject not in self.knowledge_base:
            return "Vediamo insieme questo argomento nel modo più adatto a te."

        subject_data = self.knowledge_base[subject]
        response = f"Parliamo di {subject}! "

        # Cerca concetti specifici
        for concept_key, concept_data in subject_data.get('concetti', {}).items():
            if concept_key in message.lower():
                response += f"\n\n📚 **{concept_key.title()}**: {concept_data['spiegazione']}"
                if 'esempi' in concept_data and concept_data['esempi']:
                    response += f"\n\n🎯 **Esempio**: {concept_data['esempi'][0]}"
                if 'trucchi' in concept_data and concept_data['trucchi']:
                    response += f"\n\n💡 **Trucco**: {concept_data['trucchi'][0]}"
                return response

        # Risposta generale per la materia
        if 'strategie_studio' in subject_data and subject_data['strategie_studio']:
            strategy = random.choice(subject_data['strategie_studio'])
            response += f"Ti consiglio: {strategy}"

        return response

    def generate_help_response(self) -> str:
        """Genera una risposta di aiuto"""
        return """🎓 **Cosa posso fare per te:**

📚 **Materie**: Matematica, Informatica, Italiano, Storia, Inglese, Fisica, Scienze
🤖 **Modalità**: Spiegazioni, esercizi, quiz, riassunti, mappe concettuali  
🎯 **Stili**: Adatto le spiegazioni al tuo modo di apprendere
💡 **Aiuto**: Risoluzione problemi, preparazione esami, chiarimenti

Dimmi semplicemente cosa vuoi studiare o di cosa hai bisogno!"""

    def generate_contextual_response(self, message: str, subject: str, sentiment: List[str], 
                                   style_config: Dict, user_profile: Dict) -> str:
        """Genera una risposta contestuale generale"""
        contextual_responses = [
            "Interessante! Come posso approfondire questo argomento per te?",
            "Ho capito. Lascia che ti aiuti a sviluppare meglio questo concetto.",
            "Ottima osservazione! Vediamo insieme come esplorare questo tema."
        ]

        response = random.choice(contextual_responses)

        if subject != 'generale':
            response += f" Dato che parliamo di {subject}, posso offrirti spiegazioni, esempi o esercizi. Cosa preferisci?"

        return response

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
            conn = sqlite3.connect('skaila.db')
            cursor = conn.cursor()

            # Conversazioni per materia
            subject_stats = cursor.execute('''
                SELECT subject_detected, COUNT(*) as count
                FROM ai_conversations 
                WHERE utente_id = ? AND subject_detected IS NOT NULL
                GROUP BY subject_detected
            ''', (user_id,)).fetchall()

            # Statistiche temporali
            weekly_activity = cursor.execute('''
                SELECT COUNT(*) FROM ai_conversations 
                WHERE utente_id = ? AND timestamp > datetime('now', '-7 days')
            ''', (user_id,)).fetchone()[0]

            conn.close()

            return {
                'subject_performance': [{'subject_detected': row[0], 'count': row[1], 'avg_success': 0.8} for row in subject_stats],
                'progress_metrics': {
                    'weekly_activity': weekly_activity,
                    'total_sessions': sum(row[1] for row in subject_stats),
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