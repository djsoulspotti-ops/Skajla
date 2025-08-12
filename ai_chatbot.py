
import random
import json
from datetime import datetime, timedelta
import sqlite3
import re

class AISkailaBot:
    def __init__(self):
        # Base responses per materia
        self.subject_responses = {
            'matematica': {
                'intro': [
                    "🔢 Perfetto! La matematica è logica pura. Su quale argomento vuoi lavorare?",
                    "📊 Ottima scelta! Dimmi quale concetto matematico ti sta dando problemi.",
                    "🧮 La matematica può sembrare difficile, ma insieme la renderemo semplice!"
                ],
                'encouragement': [
                    "Ottimo ragionamento matematico! 🎯",
                    "Stai pensando come un vero matematico! 📐",
                    "Perfetto! Il tuo approccio logico è impeccabile! ✨"
                ],
                'hints': [
                    "💡 Prova a scomporre il problema in passaggi più piccoli",
                    "🔍 Ricorda: spesso la soluzione è più semplice di quanto sembri",
                    "⚡ Usa le proprietà che conosci per semplificare l'espressione"
                ]
            },
            'informatica': {
                'intro': [
                    "💻 L'informatica è il futuro! Su quale linguaggio vuoi concentrarti?",
                    "🚀 Fantastico! Programmare è risolvere problemi creativamente.",
                    "⚡ Perfetto! Quale sfida di coding vuoi affrontare oggi?"
                ],
                'encouragement': [
                    "Codice pulito ed elegante! 👨‍💻",
                    "Stai pensando come un vero programmatore! 🔧",
                    "Ottimo debugging! Il problema è risolto! 🐛"
                ],
                'hints': [
                    "💡 Ricorda: divide et impera - spezza il problema",
                    "🔍 Controlla sempre i casi limite del tuo algoritmo",
                    "⚡ Debug passo per passo, stampa i valori intermedi"
                ]
            },
            'italiano': {
                'intro': [
                    "📚 La lingua italiana è bellissima! Grammatica, letteratura o scrittura?",
                    "✍️ Perfetto! L'italiano è la base di ogni comunicazione efficace.",
                    "🎭 Che bello esplorare la ricchezza della nostra lingua!"
                ],
                'encouragement': [
                    "Espressione perfetta! Molto chiaro! 📝",
                    "Stai scrivendo con grande eleganza! ✨",
                    "Ottimo uso della lingua italiana! 🇮🇹"
                ],
                'hints': [
                    "💡 Ricorda: soggetto, verbo, complemento - la struttura base",
                    "🔍 Rileggi sempre ad alta voce per sentire il ritmo",
                    "⚡ Usa sinonimi per arricchire il tuo vocabolario"
                ]
            },
            'storia': {
                'intro': [
                    "🏛️ La storia ci insegna tutto! Quale periodo ti affascina?",
                    "📜 Ottima scelta! Ogni epoca ha le sue lezioni da imparare.",
                    "⚔️ Viaggiamo nel tempo insieme! Quale civiltà esploriamo?"
                ],
                'encouragement': [
                    "Analisi storica eccellente! 🎓",
                    "Stai collegando gli eventi come un vero storico! 📚",
                    "Perfetto! Hai colto il senso dell'epoca! 🕰️"
                ],
                'hints': [
                    "💡 Ricorda: causa ed effetto sono sempre collegati",
                    "🔍 Contestualizza sempre gli eventi nel loro periodo",
                    "⚡ Cerca i parallelismi con eventi contemporanei"
                ]
            },
            'fisica': {
                'intro': [
                    "⚛️ La fisica spiega come funziona l'universo! Che fenomeno studiamo?",
                    "🌌 Fantastico! La fisica è matematica applicata alla realtà.",
                    "⚡ Perfetto! Quale forza della natura vuoi comprendere?"
                ],
                'encouragement': [
                    "Ragionamento fisico impeccabile! 🔬",
                    "Stai pensando come un vero scienziato! 🧪",
                    "Ottima intuizione scientifica! 🌟"
                ],
                'hints': [
                    "💡 Visualizza sempre il fenomeno fisico nel tuo mente",
                    "🔍 Identifica le forze in gioco nel sistema",
                    "⚡ Controlla sempre le unità di misura"
                ]
            },
            'inglese': {
                'intro': [
                    "🇬🇧 English opens doors to the world! What shall we practice?",
                    "🌍 Perfect! English is the global language of communication.",
                    "📖 Great choice! Let's improve your English skills together!"
                ],
                'encouragement': [
                    "Excellent English expression! 🎯",
                    "Your grammar is getting better! 📚",
                    "Perfect pronunciation focus! 🗣️"
                ],
                'hints': [
                    "💡 Practice makes perfect - speak every day!",
                    "🔍 Read English content to expand vocabulary",
                    "⚡ Don't be afraid to make mistakes while learning"
                ]
            }
        }

        # Stili di conversazione personalizzabili
        self.conversation_styles = {
            'friendly': {
                'greeting': ["Ciao {name}! 😊", "Hey {name}! 👋", "Salve {name}! ✨"],
                'encouragement': ["Bravo!", "Ottimo lavoro!", "Stai andando alla grande!"],
                'tone': 'informale e amichevole'
            },
            'supportive': {
                'greeting': ["Ciao {name}, sono qui per te! 💪", "Hey {name}, affrontiamo insieme questa sfida! 🤝"],
                'encouragement': ["Non mollare!", "Ce la puoi fare!", "Ogni passo conta!"],
                'tone': 'incoraggiante e motivante'
            },
            'professional': {
                'greeting': ["Buongiorno {name}.", "Salve {name}, come posso assisterla?"],
                'encouragement': ["Eccellente lavoro.", "Analisi precisa.", "Approccio metodico."],
                'tone': 'formale e professionale'
            },
            'motivational': {
                'greeting': ["Forza {name}! 🚀", "Oggi conquistiamo nuovi traguardi {name}! ⭐"],
                'encouragement': ["Sei un campione!", "Nulla può fermarti!", "Obiettivo centrato!"],
                'tone': 'energico e motivazionale'
            }
        }

        # Sistema di adattamento basato su difficoltà
        self.difficulty_patterns = {
            'easy': {
                'explanation_style': 'step_by_step',
                'vocabulary': 'simple',
                'examples': 'concrete',
                'pace': 'slow'
            },
            'medium': {
                'explanation_style': 'structured',
                'vocabulary': 'standard',
                'examples': 'mixed',
                'pace': 'normal'
            },
            'hard': {
                'explanation_style': 'conceptual',
                'vocabulary': 'advanced',
                'examples': 'abstract',
                'pace': 'fast'
            },
            'adaptive': {
                'explanation_style': 'dynamic',
                'vocabulary': 'contextual',
                'examples': 'personalized',
                'pace': 'user_responsive'
            }
        }

        # Analisi sentimento e comprensione
        self.sentiment_keywords = {
            'confused': ['non capisco', 'confuso', 'difficile', 'aiuto', 'non riesco'],
            'frustrated': ['difficile', 'impossibile', 'non funziona', 'sbagliato', 'errore'],
            'confident': ['capisco', 'facile', 'chiaro', 'perfetto', 'riuscito'],
            'curious': ['perché', 'come mai', 'interessante', 'voglio sapere', 'spiegami'],
            'motivated': ['imparo', 'studio', 'voglio', 'proverò', 'facciamo']
        }

        # Database per apprendimento adattivo
        self.learning_patterns = {}
        self.user_progress = {}
        self.interaction_history = {}
        
        self.encouragements = [
            "Ottimo lavoro! 👏",
            "Stai andando benissimo! 🌟",
            "Perfetto! Continua così! 💪",
            "Bravissimo! 🎉",
            "Eccellente! 🚀"
        ]
        
        self.study_tips = {
            'general': [
                "💡 Ricorda di fare delle pause ogni 45 minuti di studio!",
                "📚 Prova a spiegare quello che hai imparato a qualcun altro.",
                "🎯 Dividi gli argomenti complessi in parti più piccole.",
                "⏰ Studia negli orari in cui ti senti più concentrato.",
                "✍️ Prendi appunti a mano per memorizzare meglio."
            ],
            'visual': [
                "🎨 Crea mappe mentali colorate per visualizzare i concetti",
                "📊 Usa diagrammi e grafici per organizzare le informazioni",
                "🖼️ Associa immagini ai concetti per memorizzarli meglio"
            ],
            'auditory': [
                "🎵 Leggi ad alta voce per memorizzare meglio",
                "🎧 Ascolta podcast o audiolibri sull'argomento",
                "👥 Studia in gruppo e discuti i concetti"
            ],
            'kinesthetic': [
                "🏃 Muoviti mentre ripeti i concetti",
                "✋ Usa oggetti concreti per rappresentare idee astratte",
                "🔧 Applica subito quello che impari con esercizi pratici"
            ]
        }

    def load_user_profile(self, user_id):
        """Carica il profilo di apprendimento dell'utente dal database"""
        try:
            conn = sqlite3.connect('skaila.db')
            cursor = conn.cursor()
            
            profile = cursor.execute('''
                SELECT bot_name, conversation_style, learning_preferences, 
                       subject_strengths, subject_weaknesses, last_updated
                FROM ai_profiles WHERE utente_id = ?
            ''', (user_id,)).fetchone()
            
            if profile:
                return {
                    'bot_name': profile[0],
                    'conversation_style': profile[1] or 'friendly',
                    'learning_preferences': profile[2] or 'visual',
                    'subject_strengths': (profile[3] or '').split(',') if profile[3] else [],
                    'subject_weaknesses': (profile[4] or '').split(',') if profile[4] else [],
                    'last_updated': profile[5]
                }
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Errore caricamento profilo: {e}")
        
        return self.get_default_profile()

    def get_default_profile(self):
        """Profilo di default per nuovi utenti"""
        return {
            'bot_name': 'SKAILA Assistant',
            'conversation_style': 'friendly',
            'learning_preferences': 'adaptive',
            'subject_strengths': [],
            'subject_weaknesses': [],
            'last_updated': None
        }

    def analyze_user_sentiment(self, message):
        """Analizza il sentimento del messaggio dell'utente"""
        message_lower = message.lower()
        detected_sentiments = []
        
        for sentiment, keywords in self.sentiment_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_sentiments.append(sentiment)
        
        return detected_sentiments if detected_sentiments else ['neutral']

    def detect_subject(self, message):
        """Rileva la materia dal messaggio"""
        message_lower = message.lower()
        
        subject_keywords = {
            'matematica': ['matematica', 'mate', 'numeri', 'calcolo', 'equazione', 'algebra', 'geometria'],
            'informatica': ['informatica', 'programmazione', 'coding', 'computer', 'python', 'javascript', 'html'],
            'italiano': ['italiano', 'grammatica', 'letteratura', 'poesia', 'scrittore', 'analisi'],
            'storia': ['storia', 'storico', 'guerra', 'impero', 'rivoluzione', 'medioevo', 'rinascimento'],
            'fisica': ['fisica', 'forza', 'energia', 'movimento', 'newton', 'gravità', 'elettrico'],
            'inglese': ['inglese', 'english', 'grammar', 'vocabulary', 'verbi', 'inglese']
        }
        
        for subject, keywords in subject_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return subject
        
        return 'general'

    def adapt_difficulty(self, user_profile, subject, user_sentiment):
        """Adatta la difficoltà basandosi su profilo e sentimento"""
        base_difficulty = 'medium'
        
        # Adatta basandosi sui punti di forza/debolezza
        if subject in user_profile.get('subject_strengths', []):
            base_difficulty = 'hard'
        elif subject in user_profile.get('subject_weaknesses', []):
            base_difficulty = 'easy'
        
        # Adatta basandosi sul sentimento
        if 'confused' in user_sentiment or 'frustrated' in user_sentiment:
            base_difficulty = 'easy'
        elif 'confident' in user_sentiment and 'curious' in user_sentiment:
            base_difficulty = 'hard'
        
        return base_difficulty

    def generate_response(self, message, user_name, user_role, user_id=None, conversation_style='friendly'):
        """Genera una risposta completamente personalizzata e adattiva"""
        
        # Carica profilo utente
        user_profile = self.load_user_profile(user_id) if user_id else self.get_default_profile()
        
        # Analisi del messaggio
        detected_subject = self.detect_subject(message)
        user_sentiment = self.analyze_user_sentiment(message)
        adapted_difficulty = self.adapt_difficulty(user_profile, detected_subject, user_sentiment)
        
        # Personalizza stile conversazione
        style = user_profile.get('conversation_style', conversation_style)
        if style not in self.conversation_styles:
            style = 'friendly'
        
        # Genera saluto personalizzato
        greeting_template = random.choice(self.conversation_styles[style]['greeting'])
        greeting = greeting_template.format(name=user_name)
        
        # Gestisci casi speciali
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['aiuto', 'help', 'non capisco']):
            return self.generate_help_response(user_name, user_sentiment, style, detected_subject)
        
        elif any(word in message_lower for word in ['grazie', 'thanks']):
            return self.generate_thanks_response(user_name, style)
        
        elif any(word in message_lower for word in ['quiz', 'test', 'verifica']):
            return self.generate_quiz_response(user_name, detected_subject, adapted_difficulty, style)
        
        elif any(word in message_lower for word in ['come stai', 'come va']):
            return self.generate_status_response(user_name, style)
        
        elif any(word in message_lower for word in ['consigli', 'suggerimenti', 'tips']):
            return self.generate_personalized_tips(user_name, user_profile, detected_subject, style)
        
        # Risposta principale basata su materia
        if detected_subject != 'general' and detected_subject in self.subject_responses:
            subject_data = self.subject_responses[detected_subject]
            base_response = random.choice(subject_data['intro'])
            
            # Adatta la risposta alla difficoltà
            adapted_response = self.adapt_response_complexity(base_response, adapted_difficulty)
            
            # Aggiungi incoraggiamento se l'utente è frustrato
            if 'frustrated' in user_sentiment or 'confused' in user_sentiment:
                encouragement = random.choice(subject_data.get('hints', []))
                adapted_response += f"\n\n{encouragement}"
            
            # Aggiungi suggerimento personalizzato
            if random.random() < 0.4:  # 40% probabilità
                tip = self.get_personalized_tip(user_profile, detected_subject)
                adapted_response += f"\n\n{tip}"
            
            return f"{greeting} {adapted_response}"
        
        # Risposta generale personalizzata
        return self.generate_general_response(user_name, message, user_profile, style, user_sentiment)

    def generate_help_response(self, user_name, sentiment, style, subject):
        """Genera risposta di aiuto personalizzata"""
        if 'confused' in sentiment:
            return f"Non preoccuparti {user_name}! 😊 È normale sentirsi confusi all'inizio. Facciamo un passo alla volta e tutto diventerà chiaro! Su quale argomento specifico hai difficoltà?"
        elif 'frustrated' in sentiment:
            return f"Capisco la tua frustrazione {user_name} 💪 Ma ricorda: ogni grande esperto è stato principiante! Prendiamoci il tempo necessario e risolviamo insieme questo problema. Di cosa hai bisogno?"
        else:
            return f"Ciao {user_name}! 🌟 Sono qui per supportarti in ogni passo del tuo apprendimento. Dimmi quale materia ti sta dando problemi e ti spiegherò tutto con esempi chiari e pratici!"

    def generate_thanks_response(self, user_name, style):
        """Genera risposta di ringraziamento personalizzata"""
        responses = {
            'friendly': f"Di niente {user_name}! 😊 È stato un piacere aiutarti! Torna quando vuoi, sono sempre qui! ✨",
            'supportive': f"Sono felice di averti aiutato {user_name}! 🤝 Ricorda che insieme possiamo superare ogni sfida! 💪",
            'professional': f"Prego {user_name}. È mio dovere assisterla nel suo percorso di apprendimento. Per qualsiasi necessità, rimango a disposizione.",
            'motivational': f"Fantastico {user_name}! 🚀 Continua così e raggiungerai traguardi incredibili! Sono orgoglioso dei tuoi progressi! ⭐"
        }
        return responses.get(style, responses['friendly'])

    def generate_quiz_response(self, user_name, subject, difficulty, style):
        """Genera risposta per richiesta quiz"""
        subject_name = {
            'matematica': 'matematica',
            'informatica': 'informatica', 
            'italiano': 'italiano',
            'storia': 'storia',
            'fisica': 'fisica',
            'inglese': 'inglese'
        }.get(subject, 'generale')
        
        difficulty_desc = {
            'easy': 'livello base',
            'medium': 'livello intermedio',
            'hard': 'livello avanzato',
            'adaptive': 'livello adattivo'
        }.get(difficulty, 'livello personalizzato')
        
        return f"Perfetto {user_name}! 📝 Creerò un quiz di {subject_name} a {difficulty_desc} personalizzato per te. Preparati a mettere alla prova le tue conoscenze! 🎯\n\nIl quiz sarà pronto tra poco... Nel frattempo, ripassa velocemente i concetti principali!"

    def generate_status_response(self, user_name, style):
        """Genera risposta sullo stato del bot"""
        responses = {
            'friendly': f"Sto benissimo {user_name}! 😊 Sono carico e pronto ad aiutarti con qualsiasi sfida di apprendimento! Tu come stai? Come posso supportarti oggi?",
            'supportive': f"Sono qui e in forma {user_name}! 💪 La mia energia è tutta dedicata al tuo successo. Come ti senti? Su cosa vuoi lavorare?",
            'professional': f"Tutti i miei sistemi sono operativi {user_name}. Sono pronto ad assisterla con la massima efficienza nel suo percorso educativo.",
            'motivational': f"Sono al massimo delle mie capacità {user_name}! 🚀 Pronto a conquistare insieme nuovi obiettivi di apprendimento! Che sfida affrontiamo oggi? ⭐"
        }
        return responses.get(style, responses['friendly'])

    def generate_personalized_tips(self, user_name, user_profile, subject, style):
        """Genera consigli personalizzati basati sul profilo"""
        learning_style = user_profile.get('learning_preferences', 'general')
        tips = self.study_tips.get(learning_style, self.study_tips['general'])
        
        if subject in self.study_tips:
            subject_tips = self.study_tips[subject]
            tip = random.choice(subject_tips + tips)
        else:
            tip = random.choice(tips)
        
        intro = f"Ottima domanda {user_name}! 💡 Basandomi sul tuo stile di apprendimento, ti consiglio:"
        return f"{intro}\n\n{tip}\n\nQuesto approccio dovrebbe essere perfetto per te! Provalo e dimmi come va! 🌟"

    def adapt_response_complexity(self, response, difficulty):
        """Adatta la complessità della risposta alla difficoltà"""
        if difficulty == 'easy':
            # Semplifica il linguaggio
            response = response.replace('argomento', 'cosa')
            response = response.replace('concentrarti', 'lavorare')
            response += " Iniziamo dalle basi! 🌱"
        elif difficulty == 'hard':
            # Usa linguaggio più tecnico
            response += " Possiamo anche esplorare aspetti avanzati e connessioni interdisciplinari. 🔬"
        
        return response

    def get_personalized_tip(self, user_profile, subject):
        """Ottieni un suggerimento personalizzato"""
        learning_style = user_profile.get('learning_preferences', 'general')
        
        if learning_style == 'visual' and subject == 'matematica':
            return "💡 Prova a disegnare il problema! Le immagini rendono la matematica più chiara."
        elif learning_style == 'auditory' and subject == 'italiano':
            return "💡 Leggi ad alta voce - sentirai la musicalità della lingua italiana!"
        elif learning_style == 'kinesthetic' and subject == 'informatica':
            return "💡 Scrivi il codice a mano prima di digitarlo - aiuta la memorizzazione!"
        
        return random.choice(self.study_tips['general'])

    def generate_general_response(self, user_name, message, user_profile, style, sentiment):
        """Genera risposta generale personalizzata"""
        greetings = self.conversation_styles[style]['greeting']
        greeting = random.choice(greetings).format(name=user_name)
        
        if 'curious' in sentiment:
            base = "Vedo che sei molto curioso! 🤔 Questa è la qualità più importante per imparare."
        elif 'motivated' in sentiment:
            base = "Adoro il tuo entusiasmo! 🔥 Con questa motivazione puoi raggiungere qualsiasi obiettivo!"
        elif 'confident' in sentiment:
            base = "Perfetto! La tua sicurezza è già metà del successo! 😎"
        else:
            base = "Sono qui per aiutarti in qualsiasi cosa tu voglia imparare! 📚"
        
        encouragement = random.choice(self.conversation_styles[style]['encouragement'])
        
        return f"{greeting} {base} {encouragement}\n\nSu cosa vuoi lavorare oggi? Posso aiutarti con qualsiasi materia! 🌟"

    def get_personalized_suggestion(self, user_profile, current_subject=None):
        """Genera suggerimenti personalizzati basati sul profilo"""
        suggestions = []
        learning_style = user_profile.get('learning_preferences', 'adaptive')
        strengths = user_profile.get('subject_strengths', [])
        weaknesses = user_profile.get('subject_weaknesses', [])
        
        # Suggerimenti basati sui punti deboli
        if weaknesses:
            weak_subject = random.choice(weaknesses)
            suggestions.append(f"💪 Che ne dici di rafforzare {weak_subject}? Posso aiutarti con esercizi mirati!")
        
        # Suggerimenti basati sui punti forti
        if strengths:
            strong_subject = random.choice(strengths)
            suggestions.append(f"🌟 Visto che sei bravo in {strong_subject}, possiamo esplorare argomenti più avanzati!")
        
        # Suggerimenti generali personalizzati
        if learning_style == 'visual':
            suggestions.append("🎨 Creiamo delle mappe mentali colorate per visualizzare meglio i concetti!")
        elif learning_style == 'auditory':
            suggestions.append("🎵 Che ne dici di trasformare le lezioni in rime o canzoni memorabili?")
        elif learning_style == 'kinesthetic':
            suggestions.append("🏃 Facciamo qualche esercizio pratico e interattivo!")
        
        # Suggerimenti interdisciplinari
        if len(strengths) >= 2:
            suggestions.append(f"🔗 Proviamo a collegare {strengths[0]} e {strengths[1]} per una comprensione più profonda!")
        
        return random.choice(suggestions) if suggestions else "📚 Dimmi su cosa vuoi lavorare oggi!"

    def generate_adaptive_quiz_question(self, subject, user_profile, difficulty='adaptive'):
        """Genera domande di quiz adattive basate sul profilo utente"""
        
        # Determina difficoltà dinamica
        if difficulty == 'adaptive':
            if subject in user_profile.get('subject_strengths', []):
                actual_difficulty = 'hard'
            elif subject in user_profile.get('subject_weaknesses', []):
                actual_difficulty = 'easy'
            else:
                actual_difficulty = 'medium'
        else:
            actual_difficulty = difficulty

        # Database domande esteso e personalizzato
        questions = {
            'matematica': {
                'easy': [
                    {
                        "domanda": "🔢 Quanto fa 15 + 27?",
                        "risposta": "42",
                        "spiegazione": "Sommiamo: 15 + 27 = 42",
                        "hint": "Prova a spezzare: 15 + 20 + 7 = 35 + 7 = 42"
                    },
                    {
                        "domanda": "🧮 Qual è il risultato di 8 × 7?",
                        "risposta": "56",
                        "spiegazione": "8 × 7 = 56 (ricorda: 8 × 7 = 8 × (5+2) = 40 + 16 = 56)",
                        "hint": "Pensa alle tabelline: 8 × 7 = ?"
                    }
                ],
                'medium': [
                    {
                        "domanda": "📐 Risolvi l'equazione: 2x + 5 = 15",
                        "risposta": "x = 5",
                        "spiegazione": "2x + 5 = 15 → 2x = 15 - 5 → 2x = 10 → x = 5",
                        "hint": "Isola prima il termine con x, poi dividi per il coefficiente"
                    }
                ],
                'hard': [
                    {
                        "domanda": "🌟 Trova il limite: lim(x→0) (sin(x)/x)",
                        "risposta": "1",
                        "spiegazione": "Questo è un limite notevole fondamentale: lim(x→0) (sin(x)/x) = 1",
                        "hint": "Ricorda i limiti notevoli delle funzioni trigonometriche"
                    }
                ]
            },
            'informatica': {
                'easy': [
                    {
                        "domanda": "💻 Cosa significa HTML?",
                        "risposta": "HyperText Markup Language",
                        "spiegazione": "HTML significa HyperText Markup Language - il linguaggio per strutturare pagine web",
                        "hint": "Pensa a 'HyperText Markup Language'"
                    }
                ],
                'medium': [
                    {
                        "domanda": "🐍 Cosa stampa: print(len('Hello World'))?",
                        "risposta": "11",
                        "spiegazione": "len() conta i caratteri: H-e-l-l-o-[spazio]-W-o-r-l-d = 11 caratteri",
                        "hint": "Ricorda di contare anche gli spazi!"
                    }
                ],
                'hard': [
                    {
                        "domanda": "🔧 Qual è la complessità temporale del quicksort nel caso medio?",
                        "risposta": "O(n log n)",
                        "spiegazione": "Nel caso medio, quicksort ha complessità O(n log n) grazie alla divisione bilanciata",
                        "hint": "Pensa alla divisione ricorsiva dell'array"
                    }
                ]
            },
            'italiano': {
                'easy': [
                    {
                        "domanda": "📚 Qual è il participio passato di 'vedere'?",
                        "risposta": "visto",
                        "spiegazione": "Il participio passato di 'vedere' è 'visto' (verbo irregolare)",
                        "hint": "È un verbo irregolare, non segue la regola -uto"
                    }
                ],
                'medium': [
                    {
                        "domanda": "✍️ Analizza grammaticalmente: 'Il gatto dorme'",
                        "risposta": "Il = articolo det., gatto = nome comune, dorme = verbo intrans.",
                        "spiegazione": "'Il' è articolo determinativo, 'gatto' nome comune maschile, 'dorme' verbo intransitivo",
                        "hint": "Identifica: articolo, nome, verbo"
                    }
                ],
                'hard': [
                    {
                        "domanda": "🎭 Chi è l'autore della 'Divina Commedia'?",
                        "risposta": "Dante Alighieri",
                        "spiegazione": "Dante Alighieri (1265-1321) è l'autore del capolavoro della letteratura italiana",
                        "hint": "Il sommo poeta fiorentino del Medioevo"
                    }
                ]
            }
        }
        
        # Seleziona domanda appropriata
        if subject in questions and actual_difficulty in questions[subject]:
            question_data = random.choice(questions[subject][actual_difficulty])
            
            # Personalizza la domanda in base allo stile di apprendimento
            learning_style = user_profile.get('learning_preferences', 'visual')
            if learning_style == 'visual' and 'hint' in question_data:
                question_data['visual_hint'] = "🎨 Prova a visualizzare il problema mentalmente!"
            elif learning_style == 'auditory':
                question_data['audio_hint'] = "🎵 Prova a ripetere la domanda ad alta voce!"
            
            return question_data
        
        return {
            "domanda": f"📖 Dimmi quale argomento di {subject} vuoi approfondire!",
            "risposta": "Personalizzazione in corso...",
            "spiegazione": "Aiutami a conoscerti meglio per crearti domande su misura!"
        }

    def update_user_learning_pattern(self, user_id, subject, difficulty, success_rate):
        """Aggiorna i pattern di apprendimento dell'utente"""
        try:
            conn = sqlite3.connect('skaila.db')
            cursor = conn.cursor()
            
            # Registra l'interazione
            cursor.execute('''
                INSERT INTO ai_conversations (utente_id, message, response, feedback_rating)
                VALUES (?, ?, ?, ?)
            ''', (user_id, f"Quiz {subject} - {difficulty}", f"Success rate: {success_rate}", success_rate))
            
            conn.commit()
            conn.close()
            
            # Aggiorna pattern locali
            if user_id not in self.learning_patterns:
                self.learning_patterns[user_id] = {}
            
            if subject not in self.learning_patterns[user_id]:
                self.learning_patterns[user_id][subject] = {'attempts': 0, 'success': 0}
            
            self.learning_patterns[user_id][subject]['attempts'] += 1
            if success_rate > 0.7:  # 70% successo
                self.learning_patterns[user_id][subject]['success'] += 1
            
        except Exception as e:
            print(f"❌ Errore aggiornamento pattern: {e}")

    def get_learning_analytics(self, user_id):
        """Genera analytics di apprendimento per l'utente"""
        try:
            conn = sqlite3.connect('skaila.db')
            cursor = conn.cursor()
            
            # Recupera conversazioni recenti
            conversations = cursor.execute('''
                SELECT message, response, timestamp, feedback_rating
                FROM ai_conversations 
                WHERE utente_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''', (user_id,)).fetchall()
            
            conn.close()
            
            # Analizza i dati
            analytics = {
                'total_interactions': len(conversations),
                'subjects_practiced': [],
                'average_satisfaction': 0,
                'learning_trends': {},
                'recommendations': [],
                'progress_metrics': {
                    'weekly_activity': 0,
                    'consistency': 0,
                    'overall_progress': 0
                }
            }
            
            if conversations:
                # Calcola metriche
                total_rating = sum(conv[3] or 3 for conv in conversations)
                analytics['average_satisfaction'] = total_rating / len(conversations)
                
                # Identifica materie praticate
                for conv in conversations:
                    message = conv[0].lower()
                    for subject in ['matematica', 'informatica', 'italiano', 'storia', 'fisica']:
                        if subject in message and subject not in analytics['subjects_practiced']:
                            analytics['subjects_practiced'].append(subject)
                
                # Genera raccomandazioni
                analytics['recommendations'] = self.generate_learning_recommendations(user_id, analytics)
                
                # Calcola metriche di progresso
                analytics['progress_metrics']['overall_progress'] = min(len(conversations) * 5, 100)
                analytics['progress_metrics']['consistency'] = min(len(conversations) * 3, 100)
                analytics['progress_metrics']['weekly_activity'] = len([c for c in conversations if (datetime.now() - datetime.fromisoformat(c[2].replace('Z', '+00:00'))).days <= 7])
            
            return analytics
            
        except Exception as e:
            print(f"❌ Errore analytics: {e}")
            return {'error': str(e)}

    def generate_learning_recommendations(self, user_id, analytics):
        """Genera raccomandazioni personalizzate basate sull'analisi"""
        recommendations = []
        
        total_interactions = analytics['total_interactions']
        subjects_practiced = analytics['subjects_practiced']
        
        if total_interactions < 5:
            recommendations.append("🌱 Inizia con sessioni di studio brevi ma regolari")
            recommendations.append("📚 Esplora diverse materie per trovare i tuoi interessi")
        elif total_interactions < 20:
            recommendations.append("🎯 Concentrati su 2-3 materie principali per approfondire")
            recommendations.append("💪 Aumenta gradualmente la difficoltà degli esercizi")
        else:
            recommendations.append("🚀 Ottimo progresso! Prova sfide interdisciplinari")
            recommendations.append("🎓 Considera argomenti avanzati nelle tue materie forti")
        
        # Raccomandazioni specifiche per materie
        if 'matematica' in subjects_practiced:
            recommendations.append("📐 In matematica: alterna teoria e pratica quotidianamente")
        if 'informatica' in subjects_practiced:
            recommendations.append("💻 In informatica: crea piccoli progetti per applicare le conoscenze")
        
        return recommendations

    def generate_daily_goals(self, user_profile):
        """Genera obiettivi giornalieri personalizzati"""
        goals = []
        
        learning_style = user_profile.get('learning_preferences', 'adaptive')
        weaknesses = user_profile.get('subject_weaknesses', [])
        strengths = user_profile.get('subject_strengths', [])
        
        # Obiettivi basati sui punti deboli
        if weaknesses:
            subject = random.choice(weaknesses)
            goals.append(f"Dedica 15 minuti a {subject} oggi")
        
        # Obiettivi basati sullo stile di apprendimento
        if learning_style == 'visual':
            goals.append("Crea una mappa mentale per un argomento nuovo")
        elif learning_style == 'auditory':
            goals.append("Spiega un concetto ad alta voce o a qualcuno")
        elif learning_style == 'kinesthetic':
            goals.append("Applica una conoscenza teorica con un esercizio pratico")
        
        # Obiettivi generali
        goals.extend([
            "Fai almeno una domanda di approfondimento",
            "Rivedi brevemente quello che hai imparato ieri",
            "Connetti un nuovo concetto a qualcosa che già sai"
        ])
        
        return goals[:3]  # Massimo 3 obiettivi al giorno
