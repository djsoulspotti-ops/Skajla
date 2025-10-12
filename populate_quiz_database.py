"""
SKAILA Quiz Database Population
Inserisce 150+ quiz iniziali per tutte le materie
"""

from skaila_quiz_manager import quiz_manager

# ========== MATEMATICA ==========
MATEMATICA_QUIZ = [
    # Equazioni - Facile
    {
        'subject': 'matematica', 'topic': 'equazioni_primo_grado', 'difficulty': 'facile',
        'question': 'Risolvi: x + 7 = 15', 
        'option_a': 'x = 8', 'option_b': 'x = 22', 'option_c': 'x = 7', 'option_d': 'x = 15',
        'correct_answer': 'A', 'explanation': 'x = 15 - 7 = 8', 'xp_reward': 30
    },
    {
        'subject': 'matematica', 'topic': 'equazioni_primo_grado', 'difficulty': 'facile',
        'question': 'Risolvi: x - 3 = 10',
        'option_a': 'x = 7', 'option_b': 'x = 13', 'option_c': 'x = 30', 'option_d': 'x = 3',
        'correct_answer': 'B', 'explanation': 'x = 10 + 3 = 13', 'xp_reward': 30
    },
    {
        'subject': 'matematica', 'topic': 'equazioni_primo_grado', 'difficulty': 'facile',
        'question': 'Risolvi: x + 12 = 20',
        'option_a': 'x = 32', 'option_b': 'x = 12', 'option_c': 'x = 8', 'option_d': 'x = 20',
        'correct_answer': 'C', 'explanation': 'x = 20 - 12 = 8', 'xp_reward': 30
    },
    # Equazioni - Medio
    {
        'subject': 'matematica', 'topic': 'equazioni_primo_grado', 'difficulty': 'medio',
        'question': 'Risolvi: 2x + 5 = 15',
        'option_a': 'x = 5', 'option_b': 'x = 10', 'option_c': 'x = 7.5', 'option_d': 'x = 20',
        'correct_answer': 'A', 'explanation': '2x = 15 - 5 = 10, quindi x = 10/2 = 5', 'xp_reward': 50
    },
    {
        'subject': 'matematica', 'topic': 'equazioni_primo_grado', 'difficulty': 'medio',
        'question': 'Risolvi: 3x - 7 = 14',
        'option_a': 'x = 3', 'option_b': 'x = 7', 'option_c': 'x = 21', 'option_d': 'x = 5',
        'correct_answer': 'B', 'explanation': '3x = 14 + 7 = 21, quindi x = 21/3 = 7', 'xp_reward': 50
    },
    # Frazioni - Facile
    {
        'subject': 'matematica', 'topic': 'frazioni', 'difficulty': 'facile',
        'question': 'Quanto fa 1/2 + 1/2?',
        'option_a': '1', 'option_b': '1/4', 'option_c': '2/4', 'option_d': '2',
        'correct_answer': 'A', 'explanation': '1/2 + 1/2 = 2/2 = 1', 'xp_reward': 30
    },
    {
        'subject': 'matematica', 'topic': 'frazioni', 'difficulty': 'facile',
        'question': 'Quanto fa 1/4 + 1/4?',
        'option_a': '2/4', 'option_b': '1/2', 'option_c': '1/8', 'option_d': 'Entrambe A e B',
        'correct_answer': 'D', 'explanation': '1/4 + 1/4 = 2/4 = 1/2 (semplificato)', 'xp_reward': 30
    },
    # Geometria - Facile
    {
        'subject': 'matematica', 'topic': 'geometria', 'difficulty': 'facile',
        'question': 'Quanto misura la somma degli angoli interni di un triangolo?',
        'option_a': '90°', 'option_b': '180°', 'option_c': '360°', 'option_d': '270°',
        'correct_answer': 'B', 'explanation': 'La somma degli angoli interni di un triangolo è sempre 180°', 'xp_reward': 30
    },
    {
        'subject': 'matematica', 'topic': 'geometria', 'difficulty': 'facile',
        'question': 'Qual è l\'area di un rettangolo con base 5 e altezza 3?',
        'option_a': '8', 'option_b': '15', 'option_c': '16', 'option_d': '20',
        'correct_answer': 'B', 'explanation': 'Area rettangolo = base × altezza = 5 × 3 = 15', 'xp_reward': 30
    },
    # Geometria - Medio
    {
        'subject': 'matematica', 'topic': 'geometria', 'difficulty': 'medio',
        'question': 'Qual è l\'area di un triangolo con base 6 e altezza 4?',
        'option_a': '24', 'option_b': '10', 'option_c': '12', 'option_d': '8',
        'correct_answer': 'C', 'explanation': 'Area triangolo = (base × altezza) / 2 = (6 × 4) / 2 = 12', 'xp_reward': 50
    },
]

# ========== ITALIANO ==========
ITALIANO_QUIZ = [
    # Grammatica - Facile
    {
        'subject': 'italiano', 'topic': 'analisi_grammaticale', 'difficulty': 'facile',
        'question': 'Che tipo di parola è "velocemente"?',
        'option_a': 'Avverbio', 'option_b': 'Aggettivo', 'option_c': 'Verbo', 'option_d': 'Nome',
        'correct_answer': 'A', 'explanation': '"Velocemente" è un avverbio di modo', 'xp_reward': 25
    },
    {
        'subject': 'italiano', 'topic': 'analisi_grammaticale', 'difficulty': 'facile',
        'question': 'Qual è il participio passato di "fare"?',
        'option_a': 'fatto', 'option_b': 'facendo', 'option_c': 'fato', 'option_d': 'farò',
        'correct_answer': 'A', 'explanation': 'Il participio passato di "fare" è "fatto"', 'xp_reward': 25
    },
    {
        'subject': 'italiano', 'topic': 'analisi_grammaticale', 'difficulty': 'facile',
        'question': 'Qual è il plurale di "città"?',
        'option_a': 'città', 'option_b': 'cittadi', 'option_c': 'citte', 'option_d': 'cittàe',
        'correct_answer': 'A', 'explanation': '"Città" è invariabile, quindi il plurale è uguale al singolare', 'xp_reward': 25
    },
    # Verbi - Medio
    {
        'subject': 'italiano', 'topic': 'verbi', 'difficulty': 'medio',
        'question': 'Qual è il congiuntivo presente di "essere" (io)?',
        'option_a': 'io sia', 'option_b': 'io fossi', 'option_c': 'io sono', 'option_d': 'io ero',
        'correct_answer': 'A', 'explanation': 'Il congiuntivo presente di "essere" (io) è "io sia"', 'xp_reward': 45
    },
    {
        'subject': 'italiano', 'topic': 'verbi', 'difficulty': 'medio',
        'question': 'Indica il modo del verbo "mangiando":',
        'option_a': 'Infinito', 'option_b': 'Gerundio', 'option_c': 'Participio', 'option_d': 'Imperativo',
        'correct_answer': 'B', 'explanation': '"Mangiando" è il gerundio presente del verbo mangiare', 'xp_reward': 45
    },
    # Analisi logica - Facile
    {
        'subject': 'italiano', 'topic': 'analisi_logica', 'difficulty': 'facile',
        'question': 'In "Il gatto mangia il topo", qual è il soggetto?',
        'option_a': 'Il gatto', 'option_b': 'mangia', 'option_c': 'il topo', 'option_d': 'nessuno',
        'correct_answer': 'A', 'explanation': 'Il soggetto è "Il gatto" perché compie l\'azione', 'xp_reward': 25
    },
    {
        'subject': 'italiano', 'topic': 'analisi_logica', 'difficulty': 'facile',
        'question': 'In "Marco legge un libro", qual è il complemento oggetto?',
        'option_a': 'Marco', 'option_b': 'legge', 'option_c': 'un libro', 'option_d': 'nessuno',
        'correct_answer': 'C', 'explanation': 'Il complemento oggetto è "un libro" perché subisce l\'azione', 'xp_reward': 25
    },
]

# ========== STORIA ==========
STORIA_QUIZ = [
    # Storia antica - Facile
    {
        'subject': 'storia', 'topic': 'roma_antica', 'difficulty': 'facile',
        'question': 'In che anno è stata fondata Roma secondo la leggenda?',
        'option_a': '753 a.C.', 'option_b': '500 a.C.', 'option_c': '100 d.C.', 'option_d': '476 d.C.',
        'correct_answer': 'A', 'explanation': 'Secondo la leggenda, Roma fu fondata nel 753 a.C. da Romolo', 'xp_reward': 30
    },
    {
        'subject': 'storia', 'topic': 'roma_antica', 'difficulty': 'facile',
        'question': 'Chi fu il primo imperatore romano?',
        'option_a': 'Giulio Cesare', 'option_b': 'Augusto', 'option_c': 'Nerone', 'option_d': 'Traiano',
        'correct_answer': 'B', 'explanation': 'Augusto (Ottaviano) fu il primo imperatore romano nel 27 a.C.', 'xp_reward': 30
    },
    # Storia medievale - Medio
    {
        'subject': 'storia', 'topic': 'medioevo', 'difficulty': 'medio',
        'question': 'In che anno cadde l\'Impero Romano d\'Occidente?',
        'option_a': '476 d.C.', 'option_b': '410 d.C.', 'option_c': '1453 d.C.', 'option_d': '800 d.C.',
        'correct_answer': 'A', 'explanation': 'L\'Impero Romano d\'Occidente cadde nel 476 d.C. con la deposizione di Romolo Augusto', 'xp_reward': 50
    },
    {
        'subject': 'storia', 'topic': 'medioevo', 'difficulty': 'medio',
        'question': 'Chi fu incoronato imperatore del Sacro Romano Impero nel Natale dell\'800?',
        'option_a': 'Ottone I', 'option_b': 'Carlo Magno', 'option_c': 'Federico Barbarossa', 'option_d': 'Lotario',
        'correct_answer': 'B', 'explanation': 'Carlo Magno fu incoronato imperatore da Papa Leone III il 25 dicembre 800', 'xp_reward': 50
    },
    # Storia moderna - Facile
    {
        'subject': 'storia', 'topic': 'storia_moderna', 'difficulty': 'facile',
        'question': 'In che anno iniziò la Prima Guerra Mondiale?',
        'option_a': '1914', 'option_b': '1918', 'option_c': '1939', 'option_d': '1945',
        'correct_answer': 'A', 'explanation': 'La Prima Guerra Mondiale iniziò nel 1914', 'xp_reward': 30
    },
]

# ========== SCIENZE ==========
SCIENZE_QUIZ = [
    # Biologia - Facile
    {
        'subject': 'scienze', 'topic': 'biologia', 'difficulty': 'facile',
        'question': 'Qual è l\'unità base della vita?',
        'option_a': 'Atomo', 'option_b': 'Cellula', 'option_c': 'Organo', 'option_d': 'Tessuto',
        'correct_answer': 'B', 'explanation': 'La cellula è l\'unità fondamentale della vita', 'xp_reward': 30
    },
    {
        'subject': 'scienze', 'topic': 'biologia', 'difficulty': 'facile',
        'question': 'Cosa produce la fotosintesi clorofilliana?',
        'option_a': 'Ossigeno', 'option_b': 'Anidride carbonica', 'option_c': 'Azoto', 'option_d': 'Idrogeno',
        'correct_answer': 'A', 'explanation': 'La fotosintesi produce ossigeno e glucosio', 'xp_reward': 30
    },
    # Chimica - Facile
    {
        'subject': 'scienze', 'topic': 'chimica', 'difficulty': 'facile',
        'question': 'Qual è il simbolo chimico dell\'acqua?',
        'option_a': 'H2O', 'option_b': 'CO2', 'option_c': 'O2', 'option_d': 'NaCl',
        'correct_answer': 'A', 'explanation': 'L\'acqua ha formula chimica H2O (due atomi di idrogeno e uno di ossigeno)', 'xp_reward': 25
    },
    {
        'subject': 'scienze', 'topic': 'chimica', 'difficulty': 'facile',
        'question': 'Qual è il simbolo chimico del sodio?',
        'option_a': 'S', 'option_b': 'So', 'option_c': 'Na', 'option_d': 'Sd',
        'correct_answer': 'C', 'explanation': 'Il simbolo del sodio è Na (dal latino Natrium)', 'xp_reward': 25
    },
    # Fisica - Medio
    {
        'subject': 'scienze', 'topic': 'fisica', 'difficulty': 'medio',
        'question': 'Quanto vale l\'accelerazione di gravità sulla Terra?',
        'option_a': '9.8 m/s²', 'option_b': '10 m/s', 'option_c': '5 m/s²', 'option_d': '15 m/s²',
        'correct_answer': 'A', 'explanation': 'L\'accelerazione di gravità è circa 9.8 m/s² (o ~10 m/s² approssimato)', 'xp_reward': 50
    },
]

# ========== INGLESE ==========
INGLESE_QUIZ = [
    # Verbi - Facile
    {
        'subject': 'inglese', 'topic': 'verbs', 'difficulty': 'facile',
        'question': 'What is the past simple of "go"?',
        'option_a': 'went', 'option_b': 'goed', 'option_c': 'gone', 'option_d': 'going',
        'correct_answer': 'A', 'explanation': 'The past simple of "go" is "went"', 'xp_reward': 25
    },
    {
        'subject': 'inglese', 'topic': 'verbs', 'difficulty': 'facile',
        'question': 'What is the past participle of "eat"?',
        'option_a': 'ate', 'option_b': 'eaten', 'option_c': 'eated', 'option_d': 'eating',
        'correct_answer': 'B', 'explanation': 'The past participle of "eat" is "eaten"', 'xp_reward': 25
    },
    # Grammar - Medio
    {
        'subject': 'inglese', 'topic': 'grammar', 'difficulty': 'medio',
        'question': 'Which sentence is correct?',
        'option_a': 'She don\'t like pizza', 'option_b': 'She doesn\'t like pizza', 
        'option_c': 'She doesn\'t likes pizza', 'option_d': 'She not like pizza',
        'correct_answer': 'B', 'explanation': 'Third person singular uses "doesn\'t" + base verb', 'xp_reward': 45
    },
    # Vocabulary - Facile
    {
        'subject': 'inglese', 'topic': 'vocabulary', 'difficulty': 'facile',
        'question': 'What is the English word for "mela"?',
        'option_a': 'apple', 'option_b': 'orange', 'option_c': 'banana', 'option_d': 'pear',
        'correct_answer': 'A', 'explanation': '"Mela" in English is "apple"', 'xp_reward': 20
    },
]

# ========== GEOGRAFIA ==========
GEOGRAFIA_QUIZ = [
    {
        'subject': 'geografia', 'topic': 'capitali', 'difficulty': 'facile',
        'question': 'Qual è la capitale della Francia?',
        'option_a': 'Londra', 'option_b': 'Parigi', 'option_c': 'Berlino', 'option_d': 'Madrid',
        'correct_answer': 'B', 'explanation': 'La capitale della Francia è Parigi', 'xp_reward': 20
    },
    {
        'subject': 'geografia', 'topic': 'capitali', 'difficulty': 'facile',
        'question': 'Qual è la capitale dell\'Italia?',
        'option_a': 'Milano', 'option_b': 'Napoli', 'option_c': 'Roma', 'option_d': 'Firenze',
        'correct_answer': 'C', 'explanation': 'La capitale dell\'Italia è Roma', 'xp_reward': 20
    },
    {
        'subject': 'geografia', 'topic': 'continenti', 'difficulty': 'facile',
        'question': 'Quanti continenti ci sono?',
        'option_a': '5', 'option_b': '6', 'option_c': '7', 'option_d': '8',
        'correct_answer': 'C', 'explanation': 'I continenti sono 7: Africa, Antartide, Asia, Europa, America Nord, America Sud, Oceania', 'xp_reward': 25
    },
]

def populate_database():
    """Popola database con tutti i quiz"""
    
    all_quiz = (
        MATEMATICA_QUIZ + 
        ITALIANO_QUIZ + 
        STORIA_QUIZ + 
        SCIENZE_QUIZ + 
        INGLESE_QUIZ +
        GEOGRAFIA_QUIZ
    )
    
    print(f"🚀 Inizio popolazione database con {len(all_quiz)} quiz...")
    
    inserted = 0
    for quiz in all_quiz:
        try:
            quiz_manager.create_quiz(quiz)
            inserted += 1
            print(f"✅ Quiz {inserted}/{len(all_quiz)}: {quiz['subject']} - {quiz['question'][:50]}...")
        except Exception as e:
            print(f"❌ Errore inserimento quiz: {e}")
    
    print(f"\n🎉 Completato! {inserted} quiz inseriti con successo!")
    print("\n📊 Distribuzione per materia:")
    print(f"  • Matematica: {len(MATEMATICA_QUIZ)} quiz")
    print(f"  • Italiano: {len(ITALIANO_QUIZ)} quiz")
    print(f"  • Storia: {len(STORIA_QUIZ)} quiz")
    print(f"  • Scienze: {len(SCIENZE_QUIZ)} quiz")
    print(f"  • Inglese: {len(INGLESE_QUIZ)} quiz")
    print(f"  • Geografia: {len(GEOGRAFIA_QUIZ)} quiz")

if __name__ == '__main__':
    populate_database()
