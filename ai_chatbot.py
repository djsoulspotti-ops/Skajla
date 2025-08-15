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

        # Aggiunta di metodi da ai_chatbot.py (snippet editato)
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
            },
            'motivational': {
                'greeting': ['Pronto per imparare? 💪', 'Facciamo grandi cose oggi!', 'Ogni domanda è un passo avanti! 🌟'],
                'encouragement': ['Fantastico! 🎉', 'Sei un campione!', 'Incredibile progresso! ⭐'],
                'tone': 'energico e motivante',
                'emoji_usage': 'molto alto'
            },
            'patient': {
                'greeting': ['Prendiamoci tutto il tempo necessario', 'Non c\'è fretta, andiamo passo dopo passo', 'Insieme risolveremo tutto 🤗'],
                'encouragement': ['Tranquillo, stai migliorando', 'Ogni errore è una lezione', 'Piano piano ci arriviamo'],
                'tone': 'calmo e comprensivo',
                'emoji_usage': 'medio'
            },
            'humorous': {
                'greeting': ['Ciao! Pronto per qualche risata... dico, lezione? 😄', 'Eccomi! Il tuo tutor preferito è arrivato!', 'Hey! Studiamo divertendoci! 🎭'],
                'encouragement': ['Bravissimo! Meriti una standing ovation! 👏', 'Wow! Einstein sarebbe geloso!', 'Perfetto! Hai appena fatto un goal accademico! ⚽'],
                'tone': 'divertente e leggero',
                'emoji_usage': 'molto alto'
            }
        }

        self.learning_preferences = {
            'visual': 'preferisce diagrammi, schemi e rappresentazioni grafiche',
            'auditory': 'apprende meglio attraverso spiegazioni verbali e discussioni',
            'kinesthetic': 'preferisce esempi pratici e applicazioni concrete',
            'reading_writing': 'predilige testi, liste e materiali scritti',
            'adaptive': 'si adatta al contesto e mescola diversi stili'
        }

        self.difficulty_levels = {
            'beginner': 'spiegazioni base con molti esempi',
            'intermediate': 'concetti più complessi con applicazioni',
            'advanced': 'teorie avanzate e collegamenti interdisciplinari',
            'expert': 'approfondimenti specialistici e ricerca',
            'adaptive': 'si adatta al livello mostrato dall\'utente'
        }

        self.personality_traits = {
            'empathetic': 'comprensivo e sensibile alle difficoltà',
            'analytical': 'logico e metodico nelle spiegazioni',
            'creative': 'usa approcci innovativi e creativi',
            'practical': 'focalizzato su applicazioni concrete',
            'theoretical': 'approfondisce i concetti teorici',
            'supportive': 'incoraggia costantemente lo studente',
            'challenging': 'propone sfide stimolanti',
            'collaborative': 'lavora insieme allo studente',
            'independent': 'incoraggia l\'apprendimento autonomo'
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

    def generate_intelligent_response(self, message, user_name, user_role, user_id=None):
        """Sistema di generazione risposte completamente rinnovato"""
        
        # Carica profilo utente avanzato
        user_profile = self.load_advanced_user_profile(user_id) if user_id else self.get_default_profile()
        
        # Analisi avanzata del messaggio
        message_analysis = self.advanced_message_analysis(message, user_profile)
        
        # Se OpenAI è disponibile, usa l'API per risposte più sofisticate
        if self.openai_available and message_analysis['complexity'] > 0.7:
            try:
                return self.generate_openai_response(message, user_name, user_profile, message_analysis)
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
            'learning_style': self.detect_learning_style_preference(message_lower, user_profile), # Corretto per usare il metodo da ai_chatbot.py
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
            return self.generate_help_response(user_profile) # Modificato per usare la versione da ai_chatbot.py
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

    def generate_openai_response(self, message, user_name, user_profile, analysis):
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
            
            response = openai.ChatCompletion.create(
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

    def load_advanced_user_profile(self, user_id=None):
        """Carica profilo utente avanzato con analytics"""
        if user_id is None:
            return self.get_default_profile()
            
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
                    'success_rate': profile.get(7, 0.0),
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

    # --- Metodi aggiunti o modificati da ai_chatbot.py ---

    def load_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Carica il profilo AI personalizzato dell'utente"""
        try:
            conn = sqlite3.connect('skaila.db')
            conn.row_factory = sqlite3.Row

            profile = conn.execute('''
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
                    'subject_strengths': '',
                    'subject_weaknesses': '',
                    'personality_traits': 'empathetic,supportive',
                    'total_interactions': 0,
                    'success_rate': 0.0
                }

                conn.execute('''
                    INSERT INTO ai_profiles 
                    (utente_id, bot_name, bot_avatar, conversation_style, learning_preferences, 
                     difficulty_preference, personality_traits)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, default_profile['bot_name'], default_profile['bot_avatar'],
                      default_profile['conversation_style'], default_profile['learning_preferences'],
                      default_profile['difficulty_preference'], default_profile['personality_traits']))
                conn.commit()
                conn.close()
                return default_profile

            conn.close()
            return {
                'bot_name': profile['bot_name'] or 'SKAILA Assistant',
                'bot_avatar': profile['bot_avatar'] or '🤖',
                'conversation_style': profile['conversation_style'] or 'friendly',
                'learning_preferences': profile['learning_preferences'] or 'adaptive',
                'difficulty_preference': profile['difficulty_preference'] or 'adaptive',
                'subject_strengths': (profile['subject_strengths'] or '').split(',') if profile['subject_strengths'] else [],
                'subject_weaknesses': (profile['subject_weaknesses'] or '').split(',') if profile['subject_weaknesses'] else [],
                'personality_traits': (profile['personality_traits'] or 'empathetic,supportive').split(','),
                'total_interactions': profile.get('total_interactions', 0),
                'success_rate': profile.get('success_rate', 0.0)
            }

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
            'matematica': ['matematica', 'algebra', 'geometria', 'calcolo', 'equazione', 'funzione', 'derivata', 'integrale', 'numero', 'frazione', 'percentuale', 'grafico'],
            'fisica': ['fisica', 'forza', 'energia', 'velocità', 'accelerazione', 'massa', 'peso', 'gravità', 'elettricità', 'magnetismo', 'onda', 'frequenza'],
            'chimica': ['chimica', 'molecola', 'atomo', 'elemento', 'composto', 'reazione', 'acido', 'base', 'pH', 'legame', 'ossidazione'],
            'informatica': ['informatica', 'programmazione', 'codice', 'algoritmo', 'computer', 'software', 'hardware', 'database', 'rete', 'internet'],
            'inglese': ['inglese', 'english', 'grammar', 'vocabulary', 'verb', 'tense', 'pronunciation', 'literature'],
            'italiano': ['italiano', 'grammatica', 'letteratura', 'dante', 'manzoni', 'verbo', 'sostantivo', 'aggettivo', 'analisi'],
            'storia': ['storia', 'guerra', 'impero', 'rivoluzione', 'secolo', 'medioevo', 'rinascimento', 'fascismo', 'democrazia'],
            'filosofia': ['filosofia', 'platone', 'aristotele', 'kant', 'nietzsche', 'etica', 'logica', 'metafisica', 'esistenzialismo'],
            'scienze': ['biologia', 'cellula', 'DNA', 'evoluzione', 'ecosistema', 'geografia', 'clima', 'continente']
        }

        for subject, keywords in subject_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return subject

        return 'general'

    def analyze_user_sentiment(self, message: str) -> List[str]:
        """Analizza il sentiment e lo stato emotivo dell'utente"""
        message_lower = message.lower()
        sentiments = []

        # Sentimenti positivi
        positive_indicators = ['grazie', 'perfetto', 'ottimo', 'bene', 'fantastico', 'chiaro', 'ho capito', 'comprendo']
        if any(word in message_lower for word in positive_indicators):
            sentiments.append('positive')

        # Frustrazione/difficoltà
        negative_indicators = ['non capisco', 'difficile', 'confuso', 'aiuto', 'sbaglio', 'errore', 'problema', 'non riesco']
        if any(word in message_lower for word in negative_indicators):
            sentiments.append('frustrated')

        # Curiosità/interesse
        curiosity_indicators = ['perché', 'come', 'cosa', 'quando', 'dove', 'interessante', 'voglio sapere']
        if any(word in message_lower for word in curiosity_indicators):
            sentiments.append('curious')

        # Urgenza
        urgent_indicators = ['urgente', 'presto', 'subito', 'domani', 'esame', 'verifica', 'compito in classe']
        if any(word in message_lower for word in urgent_indicators):
            sentiments.append('urgent')

        return sentiments if sentiments else ['neutral']

    def detect_learning_style_preference(self, message: str, user_profile: Dict) -> str:
        """Rileva lo stile di apprendimento preferito dal contesto"""
        message_lower = message.lower()

        # Indicatori di stile visuale
        visual_indicators = ['schema', 'grafico', 'immagine', 'diagramma', 'tabella', 'mappa', 'disegno']
        if any(word in message_lower for word in visual_indicators):
            return 'visual'

        # Indicatori di stile uditivo
        auditory_indicators = ['spiegami', 'raccontami', 'dimmi', 'ascoltare', 'sentire']
        if any(word in message_lower for word in auditory_indicators):
            return 'auditory'

        # Indicatori di stile cinestetico
        kinesthetic_indicators = ['esempio', 'pratica', 'provo', 'faccio', 'applico', 'concreto']
        if any(word in message_lower for word in kinesthetic_indicators):
            return 'kinesthetic'

        # Indicatori di lettura/scrittura
        reading_indicators = ['scrivi', 'lista', 'punti', 'riassunto', 'testo', 'leggo']
        if any(word in message_lower for word in reading_indicators):
            return 'reading_writing'

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
            elif self.is_question(message):
                return self.generate_educational_response(message, subject, sentiment, learning_style, style_config, user_profile)
            elif 'aiuto' in message.lower() or 'help' in message.lower():
                return self.generate_help_response(style_config, user_profile)
            else:
                return self.generate_contextual_response(message, subject, sentiment, style_config, user_profile)

        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "Mi dispiace, ho avuto un piccolo problema tecnico. Puoi riprovare a farmi la domanda? 🤖"

    def is_greeting(self, message: str) -> bool:
        """Controlla se il messaggio è un saluto"""
        greetings = ['ciao', 'salve', 'buongiorno', 'buonasera', 'hey', 'ehi', 'hello']
        return any(greeting in message.lower() for greeting in greetings)

    def is_question(self, message: str) -> bool:
        """Controlla se il messaggio contiene una domanda"""
        question_indicators = ['?', 'come', 'cosa', 'quando', 'dove', 'perché', 'chi', 'quale', 'quanto']
        return any(indicator in message.lower() for indicator in question_indicators)

    def generate_greeting(self, user_name: str, style_config: Dict, user_profile: Dict) -> str:
        """Genera un saluto personalizzato"""
        greeting = random.choice(style_config['greeting'])
        bot_name = user_profile.get('bot_name', 'SKAILA Assistant')

        personalized_messages = [
            f"{greeting} Sono {bot_name}, il tuo assistente di apprendimento personalizzato!",
            f"{greeting} {user_name}! Come posso aiutarti oggi con i tuoi studi?",
            f"{greeting} Benvenuto! Sono qui per supportarti nel tuo percorso di apprendimento!"
        ]

        return random.choice(personalized_messages)

    def generate_educational_response(self, message: str, subject: str, sentiment: List[str], 
                                   learning_style: str, style_config: Dict, user_profile: Dict) -> str:
        """Genera una risposta educativa personalizzata"""

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
        elif 'urgent' in sentiment:
            response = f"Andiamo subito al sodo per aiutarti! {response}"

        # Aggiungi incoraggiamento basato sul profilo
        personality = user_profile.get('personality_traits', ['supportive'])
        if 'supportive' in personality:
            response += f" {random.choice(style_config['encouragement'])}"

        return response

    def get_subject_specific_response(self, message: str, subject: str, learning_style: str) -> str:
        """Genera risposte specifiche per materia"""
        responses = {
            'matematica': {
                'visual': "Ti creo un grafico/schema per visualizzare meglio il concetto.",
                'auditory': "Lascia che ti spieghi passo dopo passo questo argomento.",
                'kinesthetic': "Vediamo questo problema con un esempio pratico che puoi 'toccare con mano'.",
                'reading_writing': "Ecco una spiegazione scritta dettagliata con i punti chiave."
            },
            'fisica': {
                'visual': "Immagina questa situazione fisica... ti aiuto a visualizzarla.",
                'auditory': "Ascolta come funziona questo fenomeno fisico...",
                'kinesthetic': "Prova a pensare a quando hai vissuto questa situazione nella vita reale...",
                'reading_writing': "Ecco le leggi e formule che governano questo fenomeno."
            },
            'inglese': {
                'visual': "Creiamo una mappa mentale delle regole grammaticali.",
                'auditory': "Pronunciamo insieme e ascoltiamo la differenza.",
                'kinesthetic': "Mettiamo in pratica con esercizi interattivi.",
                'reading_writing': "Leggiamo alcuni esempi e scriviamo delle frasi insieme."
            }
        }

        subject_responses = responses.get(subject, {})
        style_response = subject_responses.get(learning_style, "Vediamo insieme questo argomento nel modo più adatto a te.")

        return style_response

    def generate_help_response(self, style_config: Dict, user_profile: Dict) -> str:
        """Genera una risposta di aiuto personalizzata"""
        help_options = [
            "🎓 **Cosa posso fare per te:**",
            "",
            "📚 **Materie:** Matematica, Fisica, Chimica, Informatica, Inglese, Italiano, Storia, Filosofia, Scienze",
            "🤖 **Modalità:** Spiegazioni, esercizi, quiz, riassunti, mappe concettuali",
            "🎯 **Stili:** Adatto le spiegazioni al tuo modo di apprendere",
            "💡 **Aiuto:** Risoluzione problemi, preparazione esami, chiarimenti",
            "",
            "Dimmi semplicemente cosa vuoi studiare o di cosa hai bisogno!"
        ]

        return "\n".join(help_options)

    def generate_contextual_response(self, message: str, subject: str, sentiment: List[str], 
                                   style_config: Dict, user_profile: Dict) -> str:
        """Genera una risposta contestuale generale"""

        contextual_responses = [
            "Interessante punto! Come posso approfondire questo argomento per te?",
            "Ho capito cosa intendi. Lascia che ti aiuti a sviluppare meglio questo concetto.",
            "Ottima osservazione! Vediamo insieme come esplorare questo tema.",
            "Capisco perfettamente. Ti supporto nel chiarire questo aspetto."
        ]

        response = random.choice(contextual_responses)

        # Aggiungi suggerimenti specifici basati sulla materia
        if subject != 'general':
            response += f" Dato che stiamo parlando di {subject}, posso offrirti spiegazioni, esempi pratici o esercizi. Cosa preferisci?"

        return response

    def generate_adaptive_quiz_question(self, subject: str, user_profile: Dict, difficulty: str) -> Dict[str, Any]:
        """Genera una domanda di quiz personalizzata"""

        quiz_templates = {
            'matematica': {
                'beginner': {
                    'question': "Risolvi: 2x + 5 = 13. Quanto vale x?",
                    'options': ['x = 4', 'x = 6', 'x = 8', 'x = 9'],
                    'correct': 0,
                    'explanation': "Per risolvere: 2x + 5 = 13, sottrai 5 da entrambi i lati: 2x = 8, poi dividi per 2: x = 4"
                },
                'intermediate': {
                    'question': "Calcola la derivata di f(x) = 3x² + 2x - 1",
                    'options': ["f'(x) = 6x + 2", "f'(x) = 3x + 2", "f'(x) = 6x - 1", "f'(x) = 3x - 1"],
                    'correct': 0,
                    'explanation': "La derivata di 3x² è 6x, la derivata di 2x è 2, la derivata di -1 è 0. Quindi f'(x) = 6x + 2"
                }
            },
            'fisica': {
                'beginner': {
                    'question': "Un oggetto cade da fermo. Dopo 2 secondi, quale sarà la sua velocità? (g = 10 m/s²)",
                    'options': ['10 m/s', '20 m/s', '5 m/s', '40 m/s'],
                    'correct': 1,
                    'explanation': "Velocità = accelerazione × tempo = g × t = 10 × 2 = 20 m/s"
                }
            }
        }

        # Seleziona una domanda appropriata
        subject_questions = quiz_templates.get(subject, {})
        difficulty_questions = subject_questions.get(difficulty, {})

        if not difficulty_questions:
            # Domanda generica se non disponibile
            return {
                'question': f"Dimmi cosa vorresti approfondire in {subject}?",
                'type': 'open',
                'subject': subject,
                'difficulty': difficulty,
                'personalized': True
            }

        return {
            **difficulty_questions,
            'subject': subject,
            'difficulty': difficulty,
            'personalized': True,
            'adapted_to_user': True
        }

    def get_learning_analytics(self, user_id: int) -> Dict[str, Any]:
        """Ottieni analytics di apprendimento per l'utente"""
        try:
            conn = sqlite3.connect('skaila.db')
            conn.row_factory = sqlite3.Row

            # Conversazioni per materia
            subject_stats = conn.execute('''
                SELECT subject_detected, COUNT(*) as count, AVG(success_metric) as avg_success
                FROM ai_conversations 
                WHERE utente_id = ? AND subject_detected IS NOT NULL
                GROUP BY subject_detected
            ''', (user_id,)).fetchall()

            # Statistiche temporali
            weekly_activity = conn.execute('''
                SELECT COUNT(*) FROM ai_conversations 
                WHERE utente_id = ? AND timestamp > datetime('now', '-7 days')
            ''', (user_id,)).fetchone()[0]

            # Sentiment trends
            sentiment_trends = conn.execute('''
                SELECT sentiment_analysis, COUNT(*) as frequency
                FROM ai_conversations 
                WHERE utente_id = ? AND timestamp > datetime('now', '-30 days')
                GROUP BY sentiment_analysis
            ''', (user_id,)).fetchall()

            conn.close()

            return {
                'subject_performance': [dict(row) for row in subject_stats],
                'progress_metrics': {
                    'weekly_activity': weekly_activity,
                    'total_sessions': sum(row[1] for row in subject_stats),
                    'avg_success_rate': sum(row[2] or 0 for row in subject_stats) / len(subject_stats) if subject_stats else 0
                },
                'sentiment_analysis': [dict(row) for row in sentiment_trends],
                'learning_insights': self.generate_learning_insights(subject_stats, weekly_activity)
            }

        except Exception as e:
            print(f"Error getting learning analytics: {e}")
            return {'error': str(e)}

    def generate_learning_insights(self, subject_stats: List, weekly_activity: int) -> List[str]:
        """Genera insights personalizzati sull'apprendimento"""
        insights = []

        if not subject_stats:
            insights.append("Inizia a fare più domande per ottenere insights personalizzati!")
            return insights

        # Materia più studiata
        top_subject = max(subject_stats, key=lambda x: x[1])
        insights.append(f"La tua materia preferita sembra essere {top_subject[0]} con {top_subject[1]} conversazioni!")

        # Attività settimanale
        if weekly_activity > 5:
            insights.append("Sei molto attivo questa settimana! Ottima costanza nello studio 📚")
        elif weekly_activity > 2:
            insights.append("Buon ritmo di studio questa settimana! 👍")
        else:
            insights.append("Prova a studiare con me più spesso per migliorare i risultati! 🎯")

        # Suggerimenti di miglioramento
        if len(subject_stats) < 3:
            insights.append("Diversifica le materie per un apprendimento più completo!")

        return insights

    def generate_learning_recommendations(self, user_id: int, analytics: Dict) -> List[str]:
        """Genera raccomandazioni personalizzate di apprendimento"""
        recommendations = []

        # Analisi performance
        subject_performance = analytics.get('subject_performance', [])
        weekly_activity = analytics.get('progress_metrics', {}).get('weekly_activity', 0)

        if weekly_activity < 3:
            recommendations.append("🎯 Prova a studiare almeno 3 volte a settimana per risultati ottimali")

        if len(subject_performance) < 2:
            recommendations.append("📚 Diversifica le materie per un apprendimento più completo")

        # Raccomandazioni specifiche per materia
        for subject_data in subject_performance:
            if subject_data['avg_success'] and subject_data['avg_success'] < 0.7:
                recommendations.append(f"💡 Dedica più tempo a {subject_data['subject_detected']} per migliorare")

        if not recommendations:
            recommendations.append("🌟 Stai andando molto bene! Continua con questo ritmo")

        return recommendations[:5]  # Limita a 5 raccomandazioni

    def generate_daily_goals(self, user_profile: Dict) -> List[str]:
        """Genera obiettivi giornalieri personalizzati"""
        goals = [
            "🎓 Fai almeno una domanda su una materia che studi oggi",
            "📖 Rivedi un concetto che hai trovato difficile ieri",
            "🧠 Prova un quiz in una nuova materia",
            "💪 Dedica 15 minuti extra alla tua materia più debole",
            "🎯 Completa un esercizio pratico"
        ]

        # Personalizza in base alle debolezze
        weak_subjects = user_profile.get('subject_weaknesses', [])
        if weak_subjects:
            subject = random.choice(weak_subjects)
            goals.insert(0, f"📚 Focus extra su {subject} oggi - è il momento di migliorare!")

        return goals[:3]  # Restituisci 3 obiettivi giornalieri


    def generate_help_response(self, user_profile: Dict) -> str:
        """Genera una risposta di aiuto personalizzata"""
        help_options = [
            "🎓 **Cosa posso fare per te:**",
            "",
            "📚 **Materie:** Matematica, Fisica, Chimica, Informatica, Inglese, Italiano, Storia, Filosofia, Scienze",
            "🤖 **Modalità:** Spiegazioni, esercizi, quiz, riassunti, mappe concettuali",
            "🎯 **Stili:** Adatto le spiegazioni al tuo modo di apprendere",
            "💡 **Aiuto:** Risoluzione problemi, preparazione esami, chiarimenti",
            "",
            "Dimmi semplicemente cosa vuoi studiare o di cosa hai bisogno!"
        ]

        return "\n".join(help_options)


    def generate_explanation_response(self, message: str, subject: str, user_profile: Dict, analysis: Dict) -> str:
        """Genera una risposta di spiegazione basata sulla materia e l'analisi"""
        if subject not in self.knowledge_base:
            return "Per quale materia vorresti una spiegazione? Offro supporto per Matematica, Fisica, Chimica, Informatica, Inglese, Italiano, Storia, Filosofia e Scienze."

        subject_data = self.knowledge_base[subject]
        response = f"Certo! Parliamo di {subject}.\n\n"

        # Cerca un concetto specifico nel messaggio
        found_concept = False
        for concept_key, concept_details in subject_data.items():
            if isinstance(concept_details, dict): # Se è un dizionario di concetti
                if concept_key.lower() in message.lower():
                    response += f"Parliamo di **{concept_key.title()}**: {concept_details}\n\n"
                    found_concept = True
                    break # Prendi il primo concetto trovato
            elif isinstance(concept_details, str) and concept_key.lower() in message.lower(): # Se è una stringa (descrizione materia)
                response += f"In generale, {subject} riguarda: {concept_details}\n\n"
                found_concept = True
                break
        
        if not found_concept:
            response += f"Cosa ti incuriosisce di più riguardo a {subject}? Hai un argomento specifico in mente?\n"

        # Aggiungi suggerimenti basati sullo stile di apprendimento
        learning_style = user_profile.get('learning_preferences', 'adaptive')
        if learning_style == 'visual':
            response += "Posso creare schemi o grafici per aiutarti a visualizzare meglio! 📊\n"
        elif learning_style == 'auditory':
            response += "Posso spiegarti il concetto vocalmente o tramite esempi audio! 🗣️\n"
        elif learning_style == 'kinesthetic':
            response += "Possiamo fare un esempio pratico per rendere tutto più concreto! 🧑‍🔬\n"
        elif learning_style == 'reading_writing':
            response += "Ti fornirò una spiegazione dettagliata con punti chiave scritti! ✍️\n"
        
        return response


    def generate_motivation_response(self, user_name: str, sentiment: List[str], user_profile: Dict) -> str:
        """Genera una risposta motivazionale"""
        motivational_messages = [
            f"Non mollare ora, {user_name}! Sei più vicino al successo di quanto pensi. 💪",
            "Ricorda perché hai iniziato questo percorso! La perseveranza è la chiave. 🔑",
            "Ogni passo avanti, anche piccolo, è un progresso. Continua così! ✨",
            "Sei capace di superare questa sfida. Credi in te stesso! 🔥",
            "Lo studio può essere faticoso, ma i risultati ripagano ogni sforzo. 🚀"
        ]

        if 'frustrated' in sentiment:
            motivational_messages.append("La frustrazione è normale, ma non lasciare che ti fermi. Sei più forte di questo! 💪")
        if 'tired' in sentiment:
            motivational_messages.append("Prenditi una piccola pausa, poi torna con più energia! Il tuo cervello ti ringrazierà. 😴")

        return random.choice(motivational_messages)

    def check_for_achievements(self, user_profile: Dict, analysis: Dict) -> Dict:
        """Verifica se l'utente ha sbloccato un achievement (placeholder)"""
        # Questa è una funzione placeholder. In una implementazione reale,
        # confronteresti i dati di 'analysis' e 'user_profile' con le regole
        # degli achievements in self.gamification['achievements'].
        if random.random() < 0.1: # Simula sblocco achievement casuale
            return random.choice(list(self.gamification['achievements'].values()))
        return {}


    def analyze_emotional_state(self, message: str) -> str:
        """Analizza lo stato emotivo generale del messaggio"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['non capisco', 'aiuto', 'difficile', 'confuso']):
            return 'confused'
        if any(word in message_lower for word in ['grazie', 'perfetto', 'ottimo', 'ho capito']):
            return 'confident'
        if any(word in message_lower for word in ['sono stanco', 'pausa']):
            return 'tired'
        if any(word in message_lower for word in ['wow', 'fantastico', 'incredibile']):
            return 'excited'
        if any(word in message_lower for word in ['perché', 'come', 'interessante']):
            return 'curious'
        
        return 'neutral'

    def detect_urgency(self, message: str) -> str:
        """Rileva l'urgenza del messaggio"""
        message_lower = message.lower()
        if any(word in message_lower for word in ['urgente', 'subito', 'domani', 'esame', 'verifica', 'scadenza']):
            return 'high'
        if any(word in message_lower for word in ['presto', 'tra poco']):
            return 'medium'
        return 'low'

    def analyze_topic_depth(self, message: str) -> str:
        """Analizza la profondità del topic del messaggio"""
        message_lower = message.lower()
        if any(word in message_lower for word in ['spiegami bene', 'approfondire', 'in dettaglio', 'concetti base', 'teoria completa']):
            return 'deep'
        if any(word in message_lower for word in ['brevemente', 'in sintesi', 'cosa è']):
            return 'shallow'
        return 'medium'
        
    # --- Metodi originali mantenuti ---
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