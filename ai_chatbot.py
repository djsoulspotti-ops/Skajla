
import random
import json
from datetime import datetime, timedelta
import sqlite3
import re
import openai
import os

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
                    },
                    'calcolo': {
                        'spiegazione': "Il calcolo studia come le cose cambiano - derivate per la velocità di cambio, integrali per l'area sotto le curve.",
                        'esempi': ["La derivata di x² è 2x", "L'integrale di 2x è x² + C"],
                        'trucchi': ["Pensa alle derivate come 'quanto velocemente cresce' e agli integrali come 'quanto si accumula'"],
                        'difficolta_comune': "Non memorizzare le regole a caso - capisce il significato geometrico!"
                    }
                },
                'strategie_studio': [
                    "Pratica ogni giorno 15-20 minuti invece di studiare 3 ore una volta a settimana",
                    "Spiega i concetti a voce alta o a un amico - se non riesci a spiegarlo, non l'hai capito",
                    "Usa esempi concreti prima di passare all'astratto",
                    "Collega sempre nuovi concetti a quello che già sai"
                ]
            },
            'informatica': {
                'concetti': {
                    'programmazione': {
                        'spiegazione': "Programmare è come scrivere ricette molto precise per il computer.",
                        'esempi': [
                            "print('Ciao mondo!') dice al computer di mostrare un messaggio",
                            "if x > 5: print('grande') è come dire 'se il numero è maggiore di 5, dì grande'"
                        ],
                        'trucchi': [
                            "Inizia sempre con problemi piccoli e costruisci passo dopo passo",
                            "Il debugging è normale - anche i programmatori esperti passano ore a correggere errori!",
                            "Commenta il tuo codice come se dovessi spiegarlo a te stesso tra 6 mesi"
                        ],
                        'linguaggi': {
                            'python': "Perfetto per iniziare - sintassi semplice e molto potente",
                            'javascript': "Il linguaggio del web - indispensabile per siti interattivi",
                            'html_css': "Le fondamenta del web - HTML per la struttura, CSS per lo stile"
                        }
                    },
                    'algoritmi': {
                        'spiegazione': "Gli algoritmi sono sequenze di passi per risolvere problemi, come una ricetta di cucina.",
                        'esempi': [
                            "Algoritmo per fare il tè: 1) Metti acqua nel bollitore 2) Accendi il fuoco 3) Aspetta che bolle...",
                            "Ordinamento: come mettere in ordine alfabetico una lista di nomi"
                        ],
                        'trucchi': [
                            "Pensa sempre: input → elaborazione → output",
                            "Spezza problemi complessi in sottoproblemi più piccoli",
                            "Testa il tuo algoritmo con esempi semplici prima"
                        ]
                    }
                },
                'progetti_pratici': [
                    "Crea una calcolatrice semplice per praticare input/output",
                    "Fai un quiz interattivo per ripassare mentre programmi",
                    "Costruisci un generatore di password casuali",
                    "Crea un tracker per i tuoi voti scolastici"
                ]
            },
            'italiano': {
                'concetti': {
                    'grammatica': {
                        'analisi_logica': {
                            'spiegazione': "L'analisi logica studia le funzioni delle parole nella frase - chi fa cosa a chi.",
                            'trucchi': [
                                "Il soggetto è chi compie l'azione - chiedi 'chi?' al verbo",
                                "Il predicato è l'azione o lo stato - è il cuore della frase",
                                "I complementi rispondono a domande: dove? quando? come? perché?"
                            ]
                        },
                        'analisi_grammaticale': {
                            'spiegazione': "Analizza ogni singola parola e la sua categoria grammaticale.",
                            'trucchi': [
                                "I nomi indicano persone, animali, cose, concetti",
                                "Gli aggettivi 'decorano' i nomi aggiungendo qualità",
                                "I verbi esprimono azioni, stati, esistenza"
                            ]
                        }
                    },
                    'letteratura': {
                        'spiegazione': "La letteratura è l'arte di raccontare storie e esprimere emozioni con le parole.",
                        'periodi': {
                            'medioevo': "Età di cavalieri, dame e grandi ideali religiosi",
                            'rinascimento': "Riscoperta dell'arte classica e dell'umanesimo",
                            'romanticismo': "Emozioni, natura e ribellione contro le convenzioni"
                        },
                        'trucchi': [
                            "Ogni opera riflette il suo tempo storico - contestualizza sempre",
                            "Cerca temi universali: amore, morte, potere, crescita",
                            "Non aver paura di interpretare - la letteratura parla a ognuno diversamente"
                        ]
                    }
                },
                'scrittura': {
                    'temi': [
                        "Inizia sempre con una scaletta - introduzione, sviluppo, conclusione",
                        "Usa esempi concreti per sostenere le tue idee",
                        "Rileggi sempre ad alta voce - l'orecchio cattura errori che l'occhio perde"
                    ],
                    'stile': [
                        "Varia la lunghezza delle frasi per creare ritmo",
                        "Usa sinonimi per evitare ripetizioni",
                        "Ogni paragrafo deve sviluppare un'idea principale"
                    ]
                }
            },
            'storia': {
                'metodo_studio': [
                    "Crea linee del tempo visive per collegare eventi",
                    "Studia cause ed effetti - la storia è una catena di conseguenze",
                    "Usa mappe concettuali per collegare personaggi, luoghi, eventi",
                    "Racconta la storia come se fossi un testimone oculare"
                ],
                'periodi': {
                    'antica': "Dalle prime civiltà alla caduta dell'Impero Romano",
                    'medievale': "Dal 476 d.C. al 1492 - età di mezzo ricca di trasformazioni",
                    'moderna': "Dalle scoperte geografiche alla Rivoluzione Francese",
                    'contemporanea': "Dal 1800 ad oggi - l'età delle rivoluzioni"
                }
            },
            'inglese': {
                'grammar': {
                    'tenses': {
                        'present_simple': "I study English every day - azioni abituali",
                        'present_continuous': "I am studying now - azioni in corso",
                        'past_simple': "I studied yesterday - azioni completate nel passato"
                    },
                    'tricks': [
                        "Think in English, don't translate word by word!",
                        "Watch movies with English subtitles",
                        "Practice speaking even when alone - talk to yourself!",
                        "Learn phrases, not just individual words"
                    ]
                },
                'vocabulary': [
                    "Learn 5 new words every day and use them in sentences",
                    "Group words by themes: family, school, hobbies",
                    "Use flashcards with images, not translations",
                    "Read simple books and articles daily"
                ]
            },
            'fisica': {
                'concetti_base': {
                    'meccanica': {
                        'spiegazione': "La meccanica studia il movimento degli oggetti e le forze che li causano.",
                        'esempi': [
                            "Una palla che cade accelera a 9.8 m/s² per gravità",
                            "Newton: F = ma (Forza = massa × accelerazione)"
                        ],
                        'trucchi': [
                            "Visualizza sempre il problema - disegna diagrammi delle forze",
                            "Identifica tutte le forze che agiscono sull'oggetto",
                            "Usa le unità di misura corrette - controlla sempre!"
                        ]
                    },
                    'energia': {
                        'spiegazione': "L'energia è la capacità di compiere lavoro - si trasforma ma non si crea né si distrugge.",
                        'tipi': [
                            "Cinetica: energia del movimento (1/2 mv²)",
                            "Potenziale: energia di posizione (mgh)",
                            "Termica: energia delle particelle in movimento"
                        ]
                    }
                },
                'problem_solving': [
                    "Leggi il problema 3 volte prima di iniziare",
                    "Identifica cosa ti chiede e cosa ti dà",
                    "Disegna sempre uno schema o diagramma",
                    "Scrivi le formule che potrebbero servire",
                    "Controlla se il risultato ha senso fisico"
                ]
            }
        }

        # Risposte emotive e motivazionali avanzate
        self.emotional_responses = {
            'frustrated': [
                "Capisco perfettamente la tua frustrazione! 😤 È normale sentirsi così quando si affronta qualcosa di nuovo. Ricorda: ogni esperto è stato un principiante!",
                "La frustrazione è il segnale che stai sfidando te stesso! 💪 È così che cresci. Facciamo un passo indietro e affrontiamo questo insieme, con calma.",
                "Hey, respira! 🌸 Anche Einstein aveva momenti difficili. La differenza tra chi riesce e chi si arrende è la perseveranza. Ci sono qui per te!"
            ],
            'confused': [
                "Non preoccuparti, la confusione è l'inizio della comprensione! 🤔 Significa che la tua mente sta elaborando nuove informazioni. Scomponiamo tutto passo per passo.",
                "È perfettamente normale sentirsi confusi! 🌟 Il cervello ha bisogno di tempo per creare nuove connessioni. Andiamo piano e chiariamo tutto insieme.",
                "La confusione è come la nebbia - sembra tutto offuscato, ma poi si dirada! ☁️ Facciamo luce su questo argomento insieme!"
            ],
            'confident': [
                "Wow! Sento la tua sicurezza e mi piace! 🔥 Questa energia positiva ti porterà lontano. Continua così!",
                "Eccellente! Quando sei sicuro di te, il tuo cervello lavora al meglio! 🧠✨ Usiamo questa motivazione per andare ancora oltre!",
                "Fantastico! La fiducia in se stessi è metà del successo! 🚀 Ora che hai questa base solida, esploriamo argomenti più sfidanti!"
            ],
            'curious': [
                "Adoro la tua curiosità! 🤓 Le domande sono il motore dell'apprendimento. Continua a chiederti 'perché' e 'come'!",
                "La curiosità è il superpotere degli studenti! ⚡ Chi fa domande impara di più. Esploriamo insieme questo mondo affascinante!",
                "Bellissima domanda! 🎯 La curiosità è ciò che trasforma lo studio da obbligo in avventura. Andiamo a scoprire!"
            ],
            'motivated': [
                "La tua motivazione è contagiosa! 🔋 Quando hai questa energia, tutto è possibile. Sfruttiamo questo momento!",
                "Sento la tua determinazione! 💪 Questo atteggiamento ti porterà al successo. Tracciamo insieme il percorso verso i tuoi obiettivi!",
                "Che energia fantastica! ⚡ La motivazione è come il vento nelle vele - ti spinge verso il successo!"
            ],
            'tired': [
                "Sento che sei stanco/a... 😴 È importante riposare! Il cervello consolida le informazioni durante il riposo. Che ne dici di una pausa?",
                "La stanchezza è il segnale che hai lavorato sodo! 🌙 Ricorda: la qualità dello studio è più importante della quantità. Riposati quando serve.",
                "Il cervello stanco non apprende bene... 🧠💤 Prenditi una pausa, fai una passeggiata, torna quando ti senti ricaricato!"
            ],
            'excited': [
                "La tua eccitazione è elettrizzante! ⚡ Quando ti diverti studiando, impari molto di più. Cavalchiamo quest'onda!",
                "Che energia positiva! 🌟 L'entusiasmo è il miglior catalizzatore per l'apprendimento. Andiamo all'avventura!",
                "Adoro questo entusiasmo! 🎉 Quando studio diventa divertimento, i risultati sono straordinari!"
            ]
        }

        # Sistema di personalizzazione avanzato
        self.personalization_engines = {
            'learning_style_detector': {
                'visual': ['vedo', 'guarda', 'mostra', 'immagine', 'colore', 'schema', 'disegno'],
                'auditory': ['sento', 'ascolto', 'suona', 'voce', 'musica', 'ritmo', 'spiegami'],
                'kinesthetic': ['tocco', 'muovo', 'faccio', 'pratico', 'esperimento', 'attivo', 'costruisco'],
                'reading': ['leggo', 'scrivo', 'testo', 'libro', 'articolo', 'appunti', 'lista']
            },
            'personality_detector': {
                'analytical': ['perché', 'come', 'analisi', 'logica', 'ragione', 'prova', 'dimostra'],
                'creative': ['idea', 'immagino', 'creo', 'invento', 'arte', 'fantasia', 'originale'],
                'social': ['insieme', 'gruppo', 'amici', 'condivido', 'racconto', 'discussione'],
                'independent': ['da solo', 'individuale', 'personale', 'autonomo', 'privato']
            }
        }

        # Sistema di gamification avanzato
        self.gamification = {
            'achievements': {
                'first_question': {'name': '🌱 Primo Passo', 'description': 'Prima domanda posta!'},
                'curious_cat': {'name': '🐱 Gatto Curioso', 'description': '10 domande in un giorno!'},
                'night_owl': {'name': '🦉 Gufo Nottuno', 'description': 'Studio dopo le 22:00!'},
                'early_bird': {'name': '🐦 Allodola Mattiniera', 'description': 'Studio prima delle 7:00!'},
                'streak_master': {'name': '🔥 Maestro della Costanza', 'description': '7 giorni consecutivi!'},
                'subject_explorer': {'name': '🗺️ Esploratore', 'description': '5 materie diverse!'},
                'deep_diver': {'name': '🤿 Sommozzatore', 'description': '50+ domande in una materia!'},
                'social_learner': {'name': '👥 Apprendimento Sociale', 'description': 'Studia con altri!'},
                'problem_solver': {'name': '🧩 Risolutore', 'description': 'Risolve problemi complessi!'}
            },
            'levels': {
                1: {'name': 'Apprendista', 'requirement': 0},
                2: {'name': 'Studioso', 'requirement': 50},
                3: {'name': 'Ricercatore', 'requirement': 150},
                4: {'name': 'Esperto', 'requirement': 300},
                5: {'name': 'Maestro', 'requirement': 500}
            }
        }

    async def generate_intelligent_response(self, message, user_name, user_role, user_id=None):
        """Sistema di generazione risposte completamente rinnovato"""
        
        # Carica profilo utente avanzato
        user_profile = self.load_advanced_user_profile(user_id) if user_id else self.get_default_profile()
        
        # Analisi avanzata del messaggio
        message_analysis = self.advanced_message_analysis(message, user_profile)
        
        # Se OpenAI è disponibile, usa l'API per risposte più sofisticate
        if self.openai_available and message_analysis['complexity'] > 0.7:
            try:
                return await self.generate_openai_response(message, user_name, user_profile, message_analysis)
            except Exception as e:
                print(f"⚠️ OpenAI fallback: {e}")
        
        # Sistema di risposta avanzato integrato
        return self.generate_enhanced_local_response(message, user_name, user_profile, message_analysis)

    def advanced_message_analysis(self, message, user_profile):
        """Analisi avanzata del messaggio con AI locale"""
        message_lower = message.lower()
        
        analysis = {
            'sentiment': self.detect_advanced_sentiment(message_lower),
            'subject': self.detect_subject_advanced(message_lower),
            'learning_style': self.detect_learning_style_preference(message_lower),
            'complexity': self.calculate_complexity(message_lower),
            'intent': self.detect_user_intent(message_lower),
            'emotional_state': self.analyze_emotional_state(message_lower),
            'urgency': self.detect_urgency(message_lower),
            'topic_depth': self.analyze_topic_depth(message_lower)
        }
        
        return analysis

    def detect_advanced_sentiment(self, message):
        """Analisi sentiment più sofisticata"""
        sentiments = []
        
        # Pattern emotivi avanzati
        emotion_patterns = {
            'frustrated': ['non capisco niente', 'è impossibile', 'non ci riesco', 'difficilissimo', 'mi arrendo'],
            'excited': ['figaro!', 'fantastico!', 'wow', 'incredibile!', 'sono gasato'],
            'confused': ['cosa significa', 'non capisco come', 'spiegami meglio', 'sono perso'],
            'confident': ['ho capito', 'è facile', 'ci riesco', 'so come fare'],
            'curious': ['mi interessa', 'voglio sapere', 'come mai', 'perché succede'],
            'tired': ['sono stanco', 'non ce la faccio più', 'pausa', 'stop'],
            'motivated': ['voglio imparare', 'sono pronto', 'andiamo!', 'facciamo']
        }
        
        for emotion, patterns in emotion_patterns.items():
            if any(pattern in message for pattern in patterns):
                sentiments.append(emotion)
        
        return sentiments if sentiments else ['neutral']

    def detect_subject_advanced(self, message):
        """Rilevamento materie più preciso"""
        subject_indicators = {
            'matematica': {
                'keywords': ['matematica', 'mate', 'calcolo', 'equazione', 'geometria', 'algebra', 'numeri', 'formula'],
                'symbols': ['+', '-', '*', '/', '=', 'x', 'y', '²', '√'],
                'topics': ['derivata', 'integrale', 'funzione', 'teorema', 'dimostrazione']
            },
            'informatica': {
                'keywords': ['programmazione', 'coding', 'computer', 'software', 'app', 'sito', 'html', 'css', 'javascript'],
                'symbols': ['{', '}', '()', '[];', '//'],
                'topics': ['algoritmo', 'database', 'ai', 'machine learning', 'python', 'java']
            },
            'italiano': {
                'keywords': ['grammatica', 'letteratura', 'poesia', 'romanzo', 'scrittore', 'tema', 'analisi'],
                'topics': ['dante', 'manzoni', 'leopardi', 'verga', 'pirandello', 'analisi logica']
            },
            'storia': {
                'keywords': ['storia', 'guerra', 'impero', 'rivoluzione', 'medioevo', 'rinascimento'],
                'topics': ['napoleone', 'roma', 'fascismo', 'risorgimento', 'prima guerra mondiale']
            },
            'inglese': {
                'keywords': ['inglese', 'english', 'grammar', 'vocabulary', 'present', 'past'],
                'topics': ['phrasal verbs', 'tenses', 'conditional', 'passive']
            },
            'fisica': {
                'keywords': ['fisica', 'forza', 'energia', 'velocità', 'accelerazione', 'newton'],
                'symbols': ['F=ma', 'E=mc²', 'm/s', 'kg', 'N'],
                'topics': ['meccanica', 'termodinamica', 'elettromagnetismo']
            }
        }
        
        subject_scores = {}
        for subject, indicators in subject_indicators.items():
            score = 0
            for keyword in indicators['keywords']:
                score += message.count(keyword) * 2
            if 'symbols' in indicators:
                for symbol in indicators['symbols']:
                    score += message.count(symbol)
            if 'topics' in indicators:
                for topic in indicators['topics']:
                    score += message.count(topic) * 3
            subject_scores[subject] = score
        
        if max(subject_scores.values()) > 0:
            return max(subject_scores.items(), key=lambda x: x[1])[0]
        return 'generale'

    def generate_enhanced_local_response(self, message, user_name, user_profile, analysis):
        """Generatore di risposte avanzato locale"""
        
        subject = analysis['subject']
        sentiment = analysis['sentiment']
        intent = analysis['intent']
        
        # Personalizza saluto basato su ora e profilo
        greeting = self.get_personalized_greeting(user_name, user_profile)
        
        # Gestisci intenti specifici
        if intent == 'help_request':
            return self.generate_help_response(message, user_name, user_profile, analysis)
        elif intent == 'explanation_request':
            return self.generate_explanation_response(message, subject, user_profile, analysis)
        elif intent == 'practice_request':
            return self.generate_practice_response(subject, user_profile)
        elif intent == 'motivation_needed':
            return self.generate_motivation_response(user_name, sentiment, user_profile)
        
        # Risposta basata su materia e stato emotivo
        response_parts = []
        
        # Saluto personalizzato
        response_parts.append(greeting)
        
        # Risposta emotiva se necessaria
        if any(emotion in ['frustrated', 'confused', 'tired'] for emotion in sentiment):
            emotional_response = random.choice(self.emotional_responses[sentiment[0]])
            response_parts.append(emotional_response)
        
        # Contenuto principale basato su materia
        if subject in self.knowledge_base:
            main_response = self.generate_subject_specific_response(message, subject, user_profile, analysis)
            response_parts.append(main_response)
        else:
            main_response = self.generate_general_educational_response(message, user_profile, analysis)
            response_parts.append(main_response)
        
        # Suggerimento personalizzato
        if random.random() < 0.6:  # 60% delle volte
            suggestion = self.generate_personalized_suggestion(user_profile, subject, analysis)
            response_parts.append(f"\n\n💡 **Suggerimento personalizzato**: {suggestion}")
        
        # Gamification element
        if random.random() < 0.3:  # 30% delle volte
            achievement = self.check_for_achievements(user_profile, analysis)
            if achievement:
                response_parts.append(f"\n\n🏆 **{achievement['name']}** - {achievement['description']}")
        
        return "\n\n".join(response_parts)

    def get_personalized_greeting(self, user_name, user_profile):
        """Saluto personalizzato basato su ora e profilo"""
        now = datetime.now()
        hour = now.hour
        
        time_greetings = {
            'morning': ['Buongiorno', 'Good morning', 'Che bella giornata'],
            'afternoon': ['Buon pomeriggio', 'Ciao', 'Hey'],
            'evening': ['Buonasera', 'Ciao', 'Sera'],
            'night': ['Notte fonda, eh?', 'Studio notturno?', 'Gufo nottuno']
        }
        
        if 6 <= hour < 12:
            period = 'morning'
        elif 12 <= hour < 18:
            period = 'afternoon' 
        elif 18 <= hour < 23:
            period = 'evening'
        else:
            period = 'night'
        
        base_greeting = random.choice(time_greetings[period])
        
        # Personalizza basato su stile conversazione
        style = user_profile.get('conversation_style', 'friendly')
        if style == 'motivational':
            return f"{base_greeting} {user_name}! 🚀 Pronto a conquistare nuovi traguardi?"
        elif style == 'supportive':
            return f"{base_greeting} {user_name}! 🤝 Sono qui per supportarti!"
        elif style == 'professional':
            return f"{base_greeting} {user_name}. Come posso assisterla oggi?"
        else:  # friendly
            return f"{base_greeting} {user_name}! 😊 Come va lo studio?"

    def generate_subject_specific_response(self, message, subject, user_profile, analysis):
        """Genera risposta specifica per materia"""
        if subject not in self.knowledge_base:
            return "Interessante argomento! Dimmi di più su cosa ti serve."
        
        subject_data = self.knowledge_base[subject]
        message_lower = message.lower()
        
        # Cerca argomenti specifici nel messaggio
        for concept_key, concept_data in subject_data.get('concetti', {}).items():
            if concept_key in message_lower or any(keyword in message_lower for keyword in concept_data.get('keywords', [])):
                
                response = f"📚 **{concept_key.title()}**\n\n"
                response += concept_data['spiegazione'] + "\n\n"
                
                # Aggiungi esempi se disponibili
                if 'esempi' in concept_data:
                    response += "🎯 **Esempi pratici**:\n"
                    for esempio in concept_data['esempi'][:2]:  # Max 2 esempi
                        response += f"• {esempio}\n"
                    response += "\n"
                
                # Aggiungi trucchi basati su stile apprendimento
                if 'trucchi' in concept_data:
                    learning_style = user_profile.get('learning_style', 'visual')
                    response += f"💡 **Trucco per studenti {learning_style}**:\n"
                    response += random.choice(concept_data['trucchi'])
                
                return response
        
        # Risposta generale per la materia
        if 'strategie_studio' in subject_data:
            strategy = random.choice(subject_data['strategie_studio'])
            return f"Per {subject}, ti consiglio: {strategy} 📈\n\nSu quale argomento specifico ti serve aiuto?"
        
        return f"Ottima scelta {subject}! 🎯 Su quale argomento specifico vorresti lavorare?"

    def generate_practice_response(self, subject, user_profile):
        """Genera esercizi pratici personalizzati"""
        practice_exercises = {
            'matematica': [
                "🧮 **Esercizio Flash**: Risolvi x + 7 = 15. Sai dirmi anche perché sottrai 7 da entrambi i lati?",
                "📐 **Sfida Geometrica**: Se un triangolo ha angoli di 60° e 70°, quanto misura il terzo? (Hint: i triangoli hanno sempre 180° totali!)",
                "⚡ **Quick Math**: Calcola 15% di 80. Trucco: 10% è facile, poi aggiungi la metà!"
            ],
            'informatica': [
                "💻 **Coding Challenge**: Scrivi una funzione che stampi 'Ciao' 5 volte. Quale loop useresti?",
                "🐍 **Python Quick**: Come faresti a verificare se un numero è pari? (Hint: operatore %)",
                "🌐 **Web Challenge**: Crea un bottone HTML che cambia colore quando ci clicchi sopra!"
            ],
            'italiano': [
                "✍️ **Analisi Express**: Analizza la frase 'Il gatto dorme sul divano'. Chi è il soggetto?",
                "📖 **Creatività**: Scrivi una frase che contenga una metafora sulla scuola!",
                "🎭 **Letteratura**: Cita un personaggio famoso della letteratura italiana e dimmi perché ti colpisce!"
            ],
            'inglese': [
                "🇬🇧 **Grammar Check**: Trasforma in negativo: 'She plays piano'. Sai perché si aggiunge 'does'?",
                "💬 **Speaking Practice**: Descrivi la tua giornata usando il Present Continuous!",
                "📝 **Vocabulary**: Usa queste parole in una frase: amazing, definitely, successful!"
            ]
        }
        
        if subject in practice_exercises:
            exercise = random.choice(practice_exercises[subject])
            return f"{exercise}\n\nRispondi quando vuoi, sono qui per aiutarti! 🌟"
        
        return f"Creiamo insieme un esercizio per {subject}! Dimmi quale argomento vuoi praticare! 🎯"

    def detect_user_intent(self, message):
        """Rileva l'intenzione dell'utente"""
        intent_patterns = {
            'help_request': ['aiuto', 'help', 'non riesco', 'non capisco', 'spiegami', 'come si fa'],
            'explanation_request': ['cos\'è', 'cosa significa', 'perché', 'come funziona', 'spiegazione'],
            'practice_request': ['esercizio', 'problema', 'quiz', 'test', 'pratica', 'allenamento'],
            'motivation_needed': ['non ho voglia', 'è difficile', 'mi arrendo', 'non serve', 'boring'],
            'gratitude': ['grazie', 'thanks', 'perfetto', 'ottimo', 'bravissimo'],
            'casual_chat': ['come stai', 'che fai', 'ciao', 'hello', 'buongiorno']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in message for pattern in patterns):
                return intent
        
        return 'general_question'

    def generate_personalized_suggestion(self, user_profile, subject, analysis):
        """Genera suggerimenti personalizzati"""
        learning_style = user_profile.get('learning_style', 'visual')
        suggestions = {
            'visual': [
                "Prova a creare una mappa mentale colorata per questo argomento! 🎨",
                "Disegna diagrammi e schemi - aiutano molto la memoria visiva! 📊",
                "Usa evidenziatori di colori diversi per categorie diverse! 🌈"
            ],
            'auditory': [
                "Registrati mentre spieghi l'argomento e riascoltati! 🎙️",
                "Studia con della musica strumentale di sottofondo! 🎵",
                "Ripeti ad alta voce - l'orecchio aiuta la memoria! 🗣️"
            ],
            'kinesthetic': [
                "Cammina mentre ripeti - il movimento aiuta la concentrazione! 🚶‍♂️",
                "Usa oggetti fisici per rappresentare concetti astratti! 🧩",
                "Fai pause attive ogni 25 minuti di studio! ⏰"
            ],
            'reading': [
                "Prendi appunti a mano - aiuta la memorizzazione! ✍️",
                "Crea liste e riassunti strutturati! 📝",
                "Leggi ad alta voce per attivare più sensi! 👀"
            ]
        }
        
        style_suggestions = suggestions.get(learning_style, suggestions['visual'])
        return random.choice(style_suggestions)

    async def generate_openai_response(self, message, user_name, user_profile, analysis):
        """Genera risposta usando OpenAI per casi complessi"""
        try:
            system_prompt = f"""
            Sei SKAILA Assistant, un tutor AI avanzato per studenti italiani. 
            Caratteristiche della tua personalità:
            - Empatico e incoraggiante
            - Esperto in tutte le materie scolastiche
            - Usi emoji e esempi pratici
            - Ti adatti allo stile di apprendimento dell'utente
            
            Profilo utente:
            - Nome: {user_name}
            - Stile apprendimento: {user_profile.get('learning_style', 'adattivo')}
            - Materie forti: {', '.join(user_profile.get('subject_strengths', []))}
            - Stato emotivo rilevato: {', '.join(analysis['sentiment'])}
            
            Rispondi in italiano, sii coinvolgente e educativo!
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return self.generate_enhanced_local_response(message, user_name, user_profile, analysis)

    def load_advanced_user_profile(self, user_id):
        """Carica profilo utente avanzato con analytics"""
        try:
            conn = sqlite3.connect('skaila.db')
            cursor = conn.cursor()
            
            # Profilo base
            profile = cursor.execute('''
                SELECT bot_name, bot_avatar, conversation_style, learning_preferences, 
                       subject_strengths, subject_weaknesses, total_interactions, success_rate
                FROM ai_profiles WHERE utente_id = ?
            ''', (user_id,)).fetchone()
            
            # Analytics conversazioni
            recent_subjects = cursor.execute('''
                SELECT subject_detected, COUNT(*) as count 
                FROM ai_conversations 
                WHERE utente_id = ? AND timestamp > datetime('now', '-7 days')
                GROUP BY subject_detected 
                ORDER BY count DESC
            ''', (user_id,)).fetchall()
            
            # Pattern di utilizzo
            usage_patterns = cursor.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM ai_conversations 
                WHERE utente_id = ? 
                GROUP BY hour 
                ORDER BY count DESC
            ''', (user_id,)).fetchall()
            
            conn.close()
            
            if profile:
                return {
                    'bot_name': profile[0] or 'SKAILA Assistant',
                    'bot_avatar': profile[1] or '🤖',
                    'conversation_style': profile[2] or 'friendly',
                    'learning_style': profile[3] or 'visual',
                    'subject_strengths': profile[4].split(',') if profile[4] else [],
                    'subject_weaknesses': profile[5].split(',') if profile[5] else [],
                    'total_interactions': profile[6] or 0,
                    'success_rate': profile[7] or 0.0,
                    'recent_subjects': dict(recent_subjects),
                    'preferred_hours': [row[0] for row in usage_patterns[:3]]
                }
            
        except Exception as e:
            print(f"❌ Errore caricamento profilo avanzato: {e}")
        
        return self.get_default_profile()

    def calculate_complexity(self, message):
        """Calcola complessità del messaggio"""
        complexity_indicators = {
            'length': len(message.split()) / 100,  # Normalizzato
            'technical_terms': len([word for word in message.split() if len(word) > 10]) / 20,
            'question_depth': message.count('perché') + message.count('come mai') * 0.3,
            'subject_specific': any(subject in message.lower() for subject in self.knowledge_base.keys()) * 0.2
        }
        
        return min(sum(complexity_indicators.values()), 1.0)

    # Mantieni tutti i metodi originali necessari...
    def get_default_profile(self):
        return {
            'bot_name': 'SKAILA Assistant',
            'conversation_style': 'friendly',
            'learning_style': 'visual',
            'subject_strengths': [],
            'subject_weaknesses': [],
            'total_interactions': 0
        }

    def generate_response(self, message, user_name, user_role, user_id=None):
        """Metodo principale per compatibilità con il sistema esistente"""
        import asyncio
        return asyncio.run(self.generate_intelligent_response(message, user_name, user_role, user_id))
