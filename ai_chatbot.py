
import random
import json
from datetime import datetime

class AIChestBot:
    def __init__(self):
        self.responses = {
            'matematica': [
                "Perfetto! La matematica è una delle mie materie preferite. Su quale argomento vuoi lavorare?",
                "Ottima scelta! Dimmi quale concetto matematico ti sta dando problemi.",
                "La matematica può sembrare difficile, ma insieme la renderemo semplice! Cosa vuoi studiare?"
            ],
            'informatica': [
                "L'informatica è il futuro! Su quale linguaggio o concetto vuoi concentrarti?",
                "Fantastico! L'informatica è una materia che amo spiegare. Dimmi di cosa hai bisogno.",
                "Programmare è come risolvere puzzle! Quale argomento informatico ti interessa?"
            ],
            'italiano': [
                "La lingua italiana è bellissima! Vuoi lavorare su grammatica, letteratura o scrittura?",
                "Perfetto! L'italiano è fondamentale. Su cosa vuoi concentrarti oggi?",
                "Che bello studiare l'italiano! Dimmi quale aspetto della lingua vuoi approfondire."
            ],
            'storia': [
                "La storia ci insegna tanto! Quale periodo o evento storico ti interessa?",
                "Ottima scelta! La storia è piena di storie affascinanti. Di cosa vuoi parlare?",
                "Viaggiamo nel tempo insieme! Quale epoca storica vuoi esplorare?"
            ],
            'default': [
                "Sono qui per aiutarti! Dimmi pure di cosa hai bisogno.",
                "Ciao! Come posso supportarti nel tuo apprendimento oggi?",
                "Eccomi! Sono pronto ad aiutarti con qualsiasi materia."
            ]
        }
        
        self.encouragements = [
            "Ottimo lavoro! 👏",
            "Stai andando benissimo! 🌟",
            "Perfetto! Continua così! 💪",
            "Bravissimo! 🎉",
            "Eccellente! 🚀"
        ]
        
        self.study_tips = [
            "💡 Ricorda di fare delle pause ogni 45 minuti di studio!",
            "📚 Prova a spiegare quello che hai imparato a qualcun altro.",
            "🎯 Dividi gli argomenti complessi in parti più piccole.",
            "⏰ Studia negli orari in cui ti senti più concentrato.",
            "✍️ Prendi appunti a mano per memorizzare meglio."
        ]

    def generate_response(self, message, user_name, user_role, conversation_style='friendly'):
        message_lower = message.lower()
        
        # Analizza il messaggio per parole chiave
        if any(word in message_lower for word in ['matematica', 'mate', 'numeri', 'calcolo']):
            subject = 'matematica'
        elif any(word in message_lower for word in ['informatica', 'programmazione', 'coding', 'computer']):
            subject = 'informatica'
        elif any(word in message_lower for word in ['italiano', 'grammatica', 'letteratura']):
            subject = 'italiano'
        elif any(word in message_lower for word in ['storia', 'storico', 'guerra', 'impero']):
            subject = 'storia'
        elif any(word in message_lower for word in ['aiuto', 'help', 'non capisco']):
            return f"Ciao {user_name}! 😊 Capisco che hai bisogno di aiuto. Dimmi quale materia ti sta dando problemi e ti spiegherò tutto passo per passo!"
        elif any(word in message_lower for word in ['grazie', 'thanks']):
            return f"Prego {user_name}! 😊 Sono felice di poterti aiutare. Se hai altre domande, sono sempre qui!"
        elif any(word in message_lower for word in ['quiz', 'test', 'verifica']):
            return f"Perfetto {user_name}! 📝 Vuoi che ti prepari un quiz personalizzato? Dimmi su quale materia e ti creerò delle domande su misura per te!"
        else:
            subject = 'default'
        
        # Scegli una risposta base
        base_response = random.choice(self.responses[subject])
        
        # Personalizza in base al ruolo
        if user_role == 'professore':
            if conversation_style == 'formal':
                greeting = f"Professore {user_name},"
            else:
                greeting = f"Ciao Prof. {user_name}!"
        else:
            greeting = f"Ciao {user_name}!"
        
        # Aggiungi consigli casuali
        if random.random() < 0.3:  # 30% di probabilità
            tip = random.choice(self.study_tips)
            return f"{greeting} {base_response}\n\n{tip}"
        
        return f"{greeting} {base_response}"

    def get_personalized_suggestion(self, user_subjects, user_difficulty):
        suggestions = []
        
        if 'matematica' in user_subjects:
            if user_difficulty == 'facile':
                suggestions.append("🔢 Proviamo con le operazioni di base e le frazioni!")
            else:
                suggestions.append("📊 Che ne dici di lavorare su equazioni e funzioni?")
        
        if 'informatica' in user_subjects:
            if user_difficulty == 'facile':
                suggestions.append("💻 Iniziamo con i concetti base della programmazione!")
            else:
                suggestions.append("🚀 Esploriamo algoritmi e strutture dati avanzate!")
        
        return random.choice(suggestions) if suggestions else "📚 Dimmi su cosa vuoi lavorare oggi!"

    def generate_quiz_question(self, subject, difficulty='medio'):
        questions = {
            'matematica': {
                'facile': [
                    {"domanda": "Quanto fa 15 + 27?", "risposta": "42"},
                    {"domanda": "Qual è il risultato di 8 × 7?", "risposta": "56"},
                    {"domanda": "Quanto fa 100 - 36?", "risposta": "64"}
                ],
                'medio': [
                    {"domanda": "Risolvi: 2x + 5 = 15", "risposta": "x = 5"},
                    {"domanda": "Qual è l'area di un rettangolo 8×5?", "risposta": "40"},
                    {"domanda": "Calcola la radice quadrata di 144", "risposta": "12"}
                ]
            },
            'informatica': {
                'facile': [
                    {"domanda": "Cosa significa HTML?", "risposta": "HyperText Markup Language"},
                    {"domanda": "Quale linguaggio si usa per le pagine web dinamiche?", "risposta": "JavaScript"},
                    {"domanda": "Cosa significa CPU?", "risposta": "Central Processing Unit"}
                ],
                'medio': [
                    {"domanda": "Cosa stampa questo codice Python: print(len('Hello'))?", "risposta": "5"},
                    {"domanda": "In che linguaggio è scritto il kernel Linux?", "risposta": "C"},
                    {"domanda": "Cosa significa API?", "risposta": "Application Programming Interface"}
                ]
            }
        }
        
        if subject in questions and difficulty in questions[subject]:
            return random.choice(questions[subject][difficulty])
        
        return {"domanda": "Dimmi quale argomento vuoi approfondire!", "risposta": "Aiutami a capirti meglio!"}
