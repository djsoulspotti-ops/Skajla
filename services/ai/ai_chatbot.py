"""
SKAILA AI Chatbot POTENZIATO - Coach Intelligente Multi-Funzione
✅ Soft skills coaching (stress, motivazione, organizzazione)
✅ Consigli studio per materie (metodi, tecniche, organizzazione)
✅ Piani d'azione personalizzati dettagliati
✅ Risposte intelligenti basate su pattern e contesto
"""

from services.ai.coaching_engine import coaching_engine
from services.ai.skaila_ai_brain import skaila_brain
from database_manager import db_manager
from datetime import datetime
from typing import Dict, Any, List
import json
import re

class AISkailaBot:
    """
    Chatbot SKAILA Potenziato - Coach AI intelligente per studenti
    Supporta: Soft skills + Consigli studio + Piani d'azione personalizzati
    """
    
    def __init__(self):
        self.bot_name = "SKAILA Coach"
        self.bot_avatar = "🤖"
        self.openai_available = False
        
        # Knowledge base estesa per materie
        self.subject_knowledge = self._init_subject_knowledge()
        
        # Soft skills action plans templates
        self.soft_skills_plans = self._init_soft_skills_plans()
        
        print("✅ SKAILA Coach Potenziato inizializzato - Multi-funzione AI")
    
    def _init_subject_knowledge(self) -> Dict[str, Any]:
        """Knowledge base dettagliata per ogni materia"""
        return {
            'matematica': {
                'study_tips': [
                    "📐 Fai MOLTI esercizi pratici, non solo teoria",
                    "📝 Riscrivi le formule a mano per memorizzarle",
                    "🔄 Ripassa i concetti base prima di avanzare",
                    "👥 Spiega i concetti a un compagno (metodo Feynman)",
                    "🎯 Focus su un argomento alla volta, non mescolare"
                ],
                'common_difficulties': {
                    'equazioni': "Per le equazioni: 1) Isola l'incognita 2) Semplifica step by step 3) Verifica sempre il risultato",
                    'geometria': "Per geometria: 1) Disegna sempre la figura 2) Scrivi i dati 3) Identifica formule applicabili",
                    'frazioni': "Per le frazioni: 1) Trova denominatore comune 2) Semplifica SEMPRE 3) Controlla il risultato",
                    'derivate': "Per derivate: 1) Impara le regole base a memoria 2) Pratica con esercizi semplici 3) Poi passa a composte"
                },
                'recommended_resources': [
                    "Khan Academy (video gratuiti in italiano)",
                    "Youmath (spiegazioni ed esercizi)",
                    "GeoGebra (visualizzazione geometria)"
                ]
            },
            'italiano': {
                'study_tips': [
                    "📖 Leggi TANTO - romanzi, articoli, poesie",
                    "✍️ Scrivi riassunti con parole tue",
                    "🎭 Analizza i personaggi e le loro motivazioni",
                    "📝 Fai schemi visivi per letteratura",
                    "🗣️ Discuti i testi con compagni"
                ],
                'common_difficulties': {
                    'analisi_testo': "Per analisi del testo: 1) Leggi 2 volte 2) Sottolinea parole chiave 3) Identifica tema principale 4) Analizza figure retoriche",
                    'grammatica': "Per grammatica: 1) Impara regole con esempi 2) Fai esercizi quotidiani 3) Rileggi sempre ciò che scrivi",
                    'tema': "Per scrivere temi: 1) Scaletta SEMPRE 2) Introduzione-Sviluppo-Conclusione 3) Rileggi per errori",
                    'letteratura': "Per letteratura: 1) Contestualizza periodo storico 2) Collega autori tra loro 3) Memorizza opere principali"
                },
                'recommended_resources': [
                    "Treccani (dizionario e enciclopedia)",
                    "Zanichelli (grammatica online)",
                    "Audiolibri per migliorare comprensione"
                ]
            },
            'storia': {
                'study_tips': [
                    "📅 Crea linee temporali visuali",
                    "🗺️ Usa mappe concettuali per collegare eventi",
                    "🎬 Guarda documentari per contestualizzare",
                    "📝 Fai schemi causa-effetto",
                    "🔗 Collega eventi storici tra loro"
                ],
                'common_difficulties': {
                    'date': "Per memorizzare date: 1) Associa a eventi importanti 2) Usa acronimi 3) Ripeti con flashcard",
                    'cause_conseguenze': "Per causa-effetto: 1) Disegna diagrammi 2) Identifica fattori multipli 3) Scrivi cronologia",
                    'collegamenti': "Per collegamenti: 1) Trova pattern ricorrenti 2) Compara epoche diverse 3) Analizza similitudini"
                },
                'recommended_resources': [
                    "Focus Storia (rivista e online)",
                    "RaiStoria (documentari)",
                    "Timeline interattive online"
                ]
            },
            'scienze': {
                'study_tips': [
                    "🔬 Collega teoria a esempi pratici reali",
                    "🎨 Disegna diagrammi cellule/atomi",
                    "📹 Guarda esperimenti video",
                    "🔄 Ripassa cicli (cellulare, acqua, ecc)",
                    "📝 Usa analogie per capire concetti complessi"
                ],
                'common_difficulties': {
                    'biologia': "Per biologia: 1) Memorizza strutture con disegni 2) Capisci PERCHÉ succede 3) Usa mnemoniche",
                    'chimica': "Per chimica: 1) Bilancia equazioni step-by-step 2) Tavola periodica sempre a portata 3) Pratica stechiometria",
                    'fisica': "Per fisica: 1) Capisci il concetto prima della formula 2) Disegna schemi forze 3) Usa unità di misura corrette"
                },
                'recommended_resources': [
                    "Focus (rivista divulgazione)",
                    "Crash Course (video YouTube)",
                    "Simulazioni PhET (esperimenti interattivi)"
                ]
            },
            'inglese': {
                'study_tips': [
                    "🎧 Ascolta podcast e musica in inglese",
                    "🎬 Guarda serie TV con sottotitoli inglesi",
                    "✍️ Scrivi un diario in inglese",
                    "🗣️ Parla ad alta voce (anche da solo!)",
                    "📱 Cambia lingua smartphone in inglese"
                ],
                'common_difficulties': {
                    'grammatica': "Per grammatica: 1) Impara tempi verbali con esempi 2) Pratica speaking daily 3) Leggi molto",
                    'vocabolario': "Per vocabolario: 1) App Anki per flashcard 2) Impara frasi intere non singole parole 3) Usa parole nuove in contesto",
                    'listening': "Per listening: 1) Inizia con slow speed 2) Usa sottotitoli inglesi 3) Ripeti ad alta voce ciò che senti"
                },
                'recommended_resources': [
                    "Duolingo (app gratuita)",
                    "BBC Learning English",
                    "TED Talks con trascrizione"
                ]
            },
            'fisica': {
                'study_tips': [
                    "📐 Disegna SEMPRE il problema prima di risolverlo",
                    "🔢 Impara unità di misura e conversioni",
                    "🎯 Focus su principi base (Newton, energia)",
                    "📝 Scrivi dati, incognite, formule",
                    "🔄 Verifica dimensionale della soluzione"
                ],
                'common_difficulties': {
                    'meccanica': "Per meccanica: 1) Identifica forze 2) Disegna vettori 3) Applica leggi Newton passo-passo",
                    'energia': "Per energia: 1) Capisci conservazione energia 2) Identifica tipo energia 3) Usa bilancio energetico",
                    'elettricità': "Per elettricità: 1) Disegna circuito 2) Legge di Ohm sempre 3) Serie vs parallelo chiaro"
                },
                'recommended_resources': [
                    "Khan Academy Physics",
                    "Youmath fisica",
                    "Simulatori PhET"
                ]
            }
        }
    
    def _init_soft_skills_plans(self) -> Dict[str, Any]:
        """Template piani d'azione soft skills dettagliati"""
        return {
            'stress': {
                'title': "Piano Anti-Stress Personalizzato",
                'duration': "7 giorni",
                'steps': [
                    {
                        'day': 1,
                        'focus': "Identificazione trigger",
                        'actions': [
                            "📝 Scrivi cosa ti stressa di più (esami, tempo, voti)",
                            "⏰ Identifica momenti di picco stress (mattina/sera)",
                            "💭 Annota pensieri negativi ricorrenti"
                        ]
                    },
                    {
                        'day': 2,
                        'focus': "Tecniche respirazione",
                        'actions': [
                            "🧘 Impara respirazione 4-7-8 (4 sec inspira, 7 trattieni, 8 espira)",
                            "⏱️ Pratica 5 min mattina e sera",
                            "📱 Usa app (Calm, Headspace) per guidarti"
                        ]
                    },
                    {
                        'day': 3,
                        'focus': "Riorganizzazione tempo",
                        'actions': [
                            "📅 Crea planning settimanale realistico",
                            "🎯 Prioritizza: urgente vs importante",
                            "⏰ Aggiungi buffer time (imprevisti)"
                        ]
                    },
                    {
                        'day': 4,
                        'focus': "Pause strategiche",
                        'actions': [
                            "🍅 Applica Pomodoro (25 min lavoro + 5 pausa)",
                            "🚶 Cammina 10 min ogni 2 ore studio",
                            "📵 Disattiva notifiche durante studio"
                        ]
                    },
                    {
                        'day': 5,
                        'focus': "Support system",
                        'actions': [
                            "👥 Parla con qualcuno di fiducia",
                            "🤝 Chiedi aiuto quando serve",
                            "💬 Usa chat SKAILA per supporto compagni"
                        ]
                    },
                    {
                        'day': 6,
                        'focus': "Abitudini sane",
                        'actions': [
                            "😴 Dormi 7-8 ore (non studiare fino a tardi!)",
                            "🥗 Mangia sano e regolare",
                            "🏃 Attività fisica 20 min (anche camminata)"
                        ]
                    },
                    {
                        'day': 7,
                        'focus': "Valutazione e aggiustamenti",
                        'actions': [
                            "📊 Valuta cosa ha funzionato",
                            "✅ Identifica tecniche preferite",
                            "🔄 Continua le abitudini positive"
                        ]
                    }
                ]
            },
            'motivazione': {
                'title': "Piano Rilancio Motivazione",
                'duration': "7 giorni",
                'steps': [
                    {
                        'day': 1,
                        'focus': "Riscopri il PERCHÉ",
                        'actions': [
                            "💭 Scrivi perché studi (sogni, obiettivi futuri)",
                            "🎯 Visualizza te stesso tra 5 anni",
                            "📝 Lista 3 motivi personali per impegnarti"
                        ]
                    },
                    {
                        'day': 2,
                        'focus': "Micro-obiettivi vincenti",
                        'actions': [
                            "🎯 Definisci 1 obiettivo PICCOLO oggi (es: 15 min studio)",
                            "✅ Completalo e celebra",
                            "🏆 Crea momentum con piccoli successi"
                        ]
                    },
                    {
                        'day': 3,
                        'focus': "Ambiente motivante",
                        'actions': [
                            "📚 Riordina spazio studio",
                            "🎵 Crea playlist focus (strumentale)",
                            "🖼️ Aggiungi visual obiettivi (poster, foto)"
                        ]
                    },
                    {
                        'day': 4,
                        'focus': "Reward system",
                        'actions': [
                            "🎁 Definisci premio ogni obiettivo (film, uscita)",
                            "📊 Usa SKAILA XP come motivazione visibile",
                            "🏅 Celebra anche piccoli progressi"
                        ]
                    },
                    {
                        'day': 5,
                        'focus': "Modelli ispiratori",
                        'actions': [
                            "👤 Trova role model (studente, personaggio)",
                            "📖 Leggi storie successo",
                            "💪 Ricorda: loro ce l'hanno fatta, anche tu puoi"
                        ]
                    },
                    {
                        'day': 6,
                        'focus': "Cambia routine",
                        'actions': [
                            "🔄 Prova metodo studio nuovo",
                            "📍 Studia in posto diverso (biblioteca, parco)",
                            "👥 Prova studio gruppo se studi solo (o viceversa)"
                        ]
                    },
                    {
                        'day': 7,
                        'focus': "Momentum costante",
                        'actions': [
                            "🔥 Mantieni streak SKAILA",
                            "📈 Traccia progressi visualmente",
                            "🎯 Fissa obiettivo prossima settimana"
                        ]
                    }
                ]
            },
            'organizzazione': {
                'title': "Piano Organizzazione Studio Efficace",
                'duration': "7 giorni",
                'steps': [
                    {
                        'day': 1,
                        'focus': "Audit tempo attuale",
                        'actions': [
                            "⏰ Traccia TUTTO ciò che fai oggi (ora per ora)",
                            "📊 Identifica 'ladri di tempo'",
                            "💡 Scopri quando sei più produttivo"
                        ]
                    },
                    {
                        'day': 2,
                        'focus': "Sistema planning",
                        'actions': [
                            "📅 Scegli tool (agenda carta, Google Calendar, SKAILA)",
                            "🗓️ Pianifica settimana prossima",
                            "⏰ Time-block: assegna slot fissi per materie"
                        ]
                    },
                    {
                        'day': 3,
                        'focus': "Prioritization matrix",
                        'actions': [
                            "🎯 Usa Eisenhower Matrix (urgente/importante)",
                            "1️⃣ Fai prima: urgente E importante",
                            "2️⃣ Pianifica: importante ma non urgente",
                            "❌ Elimina: né urgente né importante"
                        ]
                    },
                    {
                        'day': 4,
                        'focus': "Sistema note efficace",
                        'actions': [
                            "📝 Prova Cornell Notes (appunti strutturati)",
                            "🗂️ Organizza per materia (cartelle/quaderni)",
                            "🔖 Usa colori e highlight strategicamente"
                        ]
                    },
                    {
                        'day': 5,
                        'focus': "Digital organization",
                        'actions': [
                            "📁 Crea cartelle chiare (Materia > Anno > Argomento)",
                            "☁️ Backup cloud (Google Drive, OneDrive)",
                            "📱 App utili: Forest (focus), Notion (note)"
                        ]
                    },
                    {
                        'day': 6,
                        'focus': "Weekly review habit",
                        'actions': [
                            "📊 Ogni domenica: rivedi settimana",
                            "✅ Cosa hai fatto bene?",
                            "🔄 Cosa migliorare settimana prossima?",
                            "🎯 Pianifica priorità nuova settimana"
                        ]
                    },
                    {
                        'day': 7,
                        'focus': "Sistema mantenimento",
                        'actions': [
                            "🔄 Rendi planning un'abitudine (stesso orario)",
                            "⏰ 15 min sera: prepara giorno dopo",
                            "📈 Monitora progressi organizzazione"
                        ]
                    }
                ]
            },
            'obiettivi': {
                'title': "Piano Definizione Obiettivi SMART",
                'duration': "7 giorni",
                'steps': [
                    {
                        'day': 1,
                        'focus': "Vision long-term",
                        'actions': [
                            "🔮 Dove vuoi essere tra 1 anno?",
                            "🎓 Obiettivi scolastici (media, voti, esami)",
                            "💭 Obiettivi personali (skills, hobby, social)"
                        ]
                    },
                    {
                        'day': 2,
                        'focus': "SMART goals definition",
                        'actions': [
                            "S - Specifico: 'Voglio 8 in matematica'",
                            "M - Misurabile: 'Almeno 3 voti >= 8'",
                            "A - Achievable: 'Con 1h studio/giorno'",
                            "R - Rilevante: 'Per media generale'",
                            "T - Time-bound: 'Entro fine quadrimestre'"
                        ]
                    },
                    {
                        'day': 3,
                        'focus': "Break down in steps",
                        'actions': [
                            "📊 Dividi obiettivo grande in piccoli step",
                            "📅 Assegna deadline a ogni step",
                            "✅ Crea checklist azioni concrete"
                        ]
                    },
                    {
                        'day': 4,
                        'focus': "Accountability system",
                        'actions': [
                            "👥 Condividi obiettivo con qualcuno",
                            "📱 Usa SKAILA per tracking",
                            "📊 Check progress settimanale"
                        ]
                    },
                    {
                        'day': 5,
                        'focus': "Obstacle planning",
                        'actions': [
                            "🚧 Identifica ostacoli possibili",
                            "💡 Plan B per ogni ostacolo",
                            "🛡️ Preparati mentalmente alle difficoltà"
                        ]
                    },
                    {
                        'day': 6,
                        'focus': "Visualizzazione successo",
                        'actions': [
                            "🎯 Chiudi occhi, visualizza obiettivo raggiunto",
                            "😊 Come ti sentirai?",
                            "🏆 Cosa farai dopo averlo raggiunto?"
                        ]
                    },
                    {
                        'day': 7,
                        'focus': "Action plan finale",
                        'actions': [
                            "📝 Scrivi piano completo",
                            "🗓️ Aggiungi tutto al calendario",
                            "🚀 INIZIA: fai prima azione oggi stesso!"
                        ]
                    }
                ]
            }
        }
    
    def generate_response(self, message: str, user_name: str, user_role: str, user_id: int) -> str:
        """
        Genera risposta intelligente usando sistema multi-livello:
        1. Check se è richiesta piano d'azione soft skills
        2. Check se è domanda su metodo studio materia
        3. Check se è domanda tecnica (redirect)
        4. Usa coaching engine per soft skills generiche
        5. Usa SKAILA brain per info generali
        """
        
        message_lower = message.lower()
        
        # LIVELLO 1: Richiesta piano d'azione soft skills
        if any(keyword in message_lower for keyword in ['piano', 'action plan', 'aiutami a', 'come posso', 'voglio migliorare']):
            plan_response = self._generate_action_plan_response(message, user_name, user_id)
            if plan_response:
                self._save_conversation(user_id, message, plan_response)
                return plan_response
        
        # LIVELLO 2: Domande su metodo studio / consigli materia
        if any(subject in message_lower for subject in ['matematica', 'italiano', 'storia', 'scienze', 'inglese', 'fisica', 'chimica']):
            subject_response = self._handle_subject_question(message, user_name, user_id)
            if subject_response:
                self._save_conversation(user_id, message, subject_response)
                return subject_response
        
        # LIVELLO 3: Domande tecniche specifiche -> redirect
        if self._is_technical_question(message):
            return self._redirect_to_teachers(user_name)
        
        # LIVELLO 4: Soft skills coaching con template
        if any(keyword in message_lower for keyword in ['stress', 'ansia', 'motivazione', 'demotivato', 'organizzazione', 'tempo', 'obiettivi']):
            try:
                response = coaching_engine.generate_personalized_response(message, user_name, user_id)
                self._save_conversation(user_id, message, response)
                return response
            except Exception as e:
                print(f"Errore coaching engine: {e}")
        
        # LIVELLO 5: Info generali SKAILA
        try:
            context = skaila_brain.analyze_student_context(user_id, message)
            response = skaila_brain.generate_intelligent_response(context)
            self._save_conversation(user_id, message, response)
            return response
        except Exception as e:
            print(f"Errore SKAILA brain: {e}")
            return self._fallback_supportive_message(user_name)
    
    def _generate_action_plan_response(self, message: str, user_name: str, user_id: int) -> str:
        """Genera piano d'azione dettagliato per soft skills"""
        message_lower = message.lower()
        
        # Identifica categoria
        plan_category = None
        if any(keyword in message_lower for keyword in ['stress', 'ansia', 'preoccupato', 'stressato']):
            plan_category = 'stress'
        elif any(keyword in message_lower for keyword in ['motivazione', 'demotivato', 'voglia', 'motivare']):
            plan_category = 'motivazione'
        elif any(keyword in message_lower for keyword in ['organizzazione', 'organizzare', 'tempo', 'planning', 'pianificare']):
            plan_category = 'organizzazione'
        elif any(keyword in message_lower for keyword in ['obiettivi', 'obiettivo', 'goal', 'traguardo']):
            plan_category = 'obiettivi'
        
        if not plan_category:
            return None
        
        # Ottieni piano template
        plan = self.soft_skills_plans.get(plan_category)
        if not plan:
            return None
        
        # Analizza contesto studente
        try:
            student_data = coaching_engine.analyze_student_ecosystem(user_id)
        except:
            student_data = {}
        
        # Genera risposta personalizzata con piano
        response = f"""Ciao {user_name}! 🎯
        
Ho creato per te un **{plan['title']}** personalizzato!

📅 **Durata:** {plan['duration']}

"""
        
        # Aggiungi analisi situazione se disponibile
        if student_data:
            weak_subjects = student_data.get('academic', {}).get('weak_subjects', [])
            xp = student_data.get('engagement', {}).get('gamification', {}).get('xp', 0)
            streak = student_data.get('engagement', {}).get('gamification', {}).get('streak', 0)
            
            response += f"""📊 **La tua situazione attuale:**
• Livello XP: {xp}
• Streak: {streak} giorni
"""
            if weak_subjects:
                response += f"• Materie da migliorare: {', '.join(weak_subjects[:2])}\n"
            
            response += "\n"
        
        response += "🗺️ **Il tuo piano giorno per giorno:**\n\n"
        
        # Aggiungi ogni giorno del piano
        for step in plan['steps']:
            response += f"**Giorno {step['day']}: {step['focus']}**\n"
            for action in step['actions']:
                response += f"   {action}\n"
            response += "\n"
        
        response += """💪 **Come seguire il piano:**
✅ Segna ogni giorno completato
✅ Adatta le azioni alla tua situazione
✅ Non ti preoccupare se salti un giorno, riprendi
✅ Condividi progressi con qualcuno di fiducia

📈 **Tracking progressi:**
Scrivi "progressi {categoria}" per vedere quanto sei avanzato!

Sei pronto a iniziare? 🚀
""".format(categoria=plan_category)
        
        return response
    
    def _handle_subject_question(self, message: str, user_name: str, user_id: int) -> str:
        """Gestisce domande su metodi studio per materie"""
        message_lower = message.lower()
        
        # Identifica materia
        subject = None
        for subj in self.subject_knowledge.keys():
            if subj in message_lower:
                subject = subj
                break
        
        if not subject:
            return None
        
        knowledge = self.subject_knowledge[subject]
        
        # Analizza contesto studente
        try:
            student_data = coaching_engine.analyze_student_ecosystem(user_id)
            voti_summary = student_data.get('academic', {}).get('voti_summary', {})
            subject_grade = voti_summary.get(subject, {}).get('media', 0)
        except:
            subject_grade = 0
        
        # Costruisci risposta
        response = f"""Ciao {user_name}! 📚

Ecco i miei consigli per **{subject.upper()}**:

"""
        
        # Aggiungi stato attuale se disponibile
        if subject_grade > 0:
            response += f"📊 **La tua media attuale:** {subject_grade}/10\n\n"
        
        # Check se messaggio chiede specificamente una difficoltà
        difficulty_found = None
        for diff_key, diff_advice in knowledge.get('common_difficulties', {}).items():
            if diff_key in message_lower or diff_key.replace('_', ' ') in message_lower:
                difficulty_found = (diff_key, diff_advice)
                break
        
        if difficulty_found:
            response += f"💡 **{difficulty_found[0].replace('_', ' ').title()}:**\n{difficulty_found[1]}\n\n"
        
        # Aggiungi study tips
        response += "🎯 **Metodi di studio efficaci:**\n"
        for tip in knowledge['study_tips'][:4]:
            response += f"{tip}\n"
        
        response += "\n"
        
        # Aggiungi difficoltà comuni se non già mostrata
        if not difficulty_found and knowledge.get('common_difficulties'):
            response += "❓ **Difficoltà comuni e soluzioni:**\n"
            for diff_key, diff_advice in list(knowledge['common_difficulties'].items())[:2]:
                response += f"• **{diff_key.replace('_', ' ').title()}**: {diff_advice}\n"
            response += "\n"
        
        # Aggiungi risorse
        if knowledge.get('recommended_resources'):
            response += "📖 **Risorse consigliate:**\n"
            for resource in knowledge['recommended_resources']:
                response += f"• {resource}\n"
            response += "\n"
        
        # Consigli personalizzati basati su voto
        if subject_grade > 0:
            if subject_grade < 6:
                response += "💪 **Per te consiglio:**\n"
                response += "1. Ripassa le basi prima di andare avanti\n"
                response += "2. Chiedi aiuto al professore per chiarire dubbi\n"
                response += "3. Fai quiz SKAILA per verificare comprensione\n"
            elif subject_grade >= 8:
                response += "🏆 **Sei già bravo! Per eccellere:**\n"
                response += "1. Approfondisci argomenti avanzati\n"
                response += "2. Aiuta i compagni (miglior modo per imparare!)\n"
                response += "3. Sfida te stesso con esercizi difficili\n"
            else:
                response += "📈 **Per migliorare ulteriormente:**\n"
                response += "1. Pratica costante (meglio 30min/giorno che 3h una volta)\n"
                response += "2. Focalizzati sugli errori comuni\n"
                response += "3. Usa quiz SKAILA per monitorare progressi\n"
        
        response += "\nHai altre domande su questa materia? 🤝"
        
        return response
    
    def _is_technical_question(self, message: str) -> bool:
        """Rileva se è una domanda tecnica specifica da professore"""
        technical_patterns = [
            r'come si risolve.*(equazione|problema|esercizio)',
            r'(formula|calcola|dimostra|risolvi)',
            r'quanto fa \d+',
            r'spiega(mi)?.*(teorema|legge di|principio)',
            r'cos[\'è] (il|la|lo).*(in termini|definizione)',
            r'perché.*(formula|legge)',
            r'dimostrazione di'
        ]
        
        message_lower = message.lower()
        for pattern in technical_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _redirect_to_teachers(self, user_name: str) -> str:
        """Reindirizza domande tecniche specifiche"""
        return f"""Ciao {user_name}! 👋

Vedo che hai una domanda tecnica molto specifica!

🎓 **Per domande didattiche dettagliate**, il tuo professore è la persona migliore!

Puoi anche:
1. 📚 Controllare i Materiali Didattici caricati dai prof
2. 💬 Chiedere nella chat di classe ai compagni
3. 🔍 Cercare su risorse online (Khan Academy, Youmath)

💪 **Io posso aiutarti con:**
• Come **studiare** una materia (metodi, tecniche)
• Come **organizzare** il tempo di studio
• Come **gestire** stress e motivazione
• Come **migliorare** in generale

Vuoi consigli su come studiare meglio questa materia? 🤝"""
    
    def _save_conversation(self, user_id: int, message: str, response: str):
        """Salva conversazione nel database"""
        try:
            sentiment = coaching_engine.detect_sentiment(message)
            
            category = 'generale'
            for cat in ['stress', 'motivazione', 'organizzazione', 'obiettivi', 'burnout', 'sociale']:
                if cat in message.lower():
                    category = cat
                    break
            
            db_manager.execute('''
                INSERT INTO coaching_interactions
                (user_id, message, detected_category, detected_sentiment, response, user_data_snapshot)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, message, category, ','.join(sentiment), response, json.dumps({'timestamp': datetime.now().isoformat()})))
        except Exception as e:
            print(f"Errore save conversation: {e}")
    
    def _fallback_supportive_message(self, user_name: str) -> str:
        """Messaggio di fallback"""
        return f"""Ciao {user_name}! 👋

Sono qui per aiutarti! Posso supportarti con:

📚 **Studio & Materie:**
• Consigli su come studiare matematica, italiano, storia, scienze, inglese, fisica
• Metodi di studio efficaci
• Risorse utili per ogni materia

🎯 **Soft Skills:**
• Gestione stress e ansia
• Motivazione e obiettivi
• Organizzazione tempo e studio
• Piani d'azione personalizzati

💬 **Esempi domande:**
• "Come posso migliorare in matematica?"
• "Aiutami a gestire lo stress"
• "Voglio un piano per organizzare meglio lo studio"
• "Consigli per motivarmi"

Cosa ti serve? 🤝"""

    def get_student_dashboard_insights(self, user_id: int) -> Dict[str, Any]:
        """Genera insights per dashboard studente"""
        try:
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
                'summary': "Continua così! 🌟",
                'alerts': [],
                'suggestions': ["Fai 1 quiz oggi", "Ripassa 15 minuti"],
                'motivational_quote': "Il successo è la somma di piccoli sforzi ripetuti."
            }
    
    def _generate_summary(self, data: Dict) -> str:
        """Genera summary situazione"""
        parts = []
        
        trend = data['academic'].get('trend')
        if trend == 'improving':
            parts.append("📈 Voti in miglioramento!")
        elif trend == 'declining':
            parts.append("📉 Attenzione: trend voti in calo")
        else:
            parts.append("📊 Performance stabile")
        
        activity = data['engagement'].get('activity_level')
        if activity == 'high':
            parts.append("🔥 Ottimo engagement!")
        elif activity == 'low':
            parts.append("⚡ Aumenta attività")
        
        streak = data['engagement']['gamification'].get('streak', 0)
        if streak >= 7:
            parts.append(f"🏆 {streak} giorni streak!")
        
        return ' '.join(parts)
    
    def _format_alerts(self, alerts: list) -> list:
        """Formatta alert"""
        alert_messages = {
            'grade_decline': '⚠️ Voti in calo - parliamone?',
            'streak_lost': '💔 Streak perso - ricominciamo!',
            'low_engagement': '📉 Attività bassa - tutto ok?',
            'unexcused_absences': '⚠️ Assenze non giustificate',
            'low_social_activity': '👥 Poca interazione - ti senti isolato?'
        }
        return [alert_messages.get(a, a) for a in alerts]
    
    def _generate_suggestions(self, data: Dict) -> list:
        """Genera suggerimenti"""
        suggestions = []
        
        weak = data['academic'].get('weak_subjects', [])
        if weak:
            suggestions.append(f"📚 Focus {weak[0]}: 30 min oggi")
        
        quiz = data['engagement']['gamification'].get('quiz_completed', 0)
        if quiz < 5:
            suggestions.append("🎯 Fai 1 quiz oggi")
        
        if not suggestions:
            suggestions = ["✅ Ripassa 15 min", "🎯 Definisci obiettivo domani"]
        
        return suggestions[:3]
    
    def _get_motivational_quote(self, data: Dict) -> str:
        """Quote motivazionale"""
        quotes = {
            'improving': "Il successo non è definitivo: è il coraggio di continuare che conta! 💪",
            'declining': "Le difficoltà preparano persone comuni a destini straordinari! 🌟",
            'stable': "La costanza è la chiave del successo! 🔑",
            'default': "Ogni giorno è un'opportunità per crescere! 🌅"
        }
        trend = data['academic'].get('trend', 'default')
        return quotes.get(trend, quotes['default'])

# Istanza globale
ai_bot = AISkailaBot()
