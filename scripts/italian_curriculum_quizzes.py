"""
SKAJLA - Database Quiz Programmi Ministeriali Italiani
Quiz allineati ai programmi del MIUR per Scuole Medie e Superiori
"""

SCUOLE_MEDIE_MATEMATICA = [
    {
        'subject': 'matematica', 'topic': 'numeri_naturali', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il risultato di 15 + 27?',
        'option_a': '42', 'option_b': '43', 'option_c': '41', 'option_d': '44',
        'correct_answer': 'A', 'explanation': '15 + 27 = 42', 'xp_reward': 25,
        'learning_objective': 'Operazioni con numeri naturali'
    },
    {
        'subject': 'matematica', 'topic': 'numeri_naturali', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il minimo comune multiplo (mcm) tra 4 e 6?',
        'option_a': '24', 'option_b': '12', 'option_c': '6', 'option_d': '2',
        'correct_answer': 'B', 'explanation': 'Il mcm di 4 e 6 è 12 (4=2², 6=2×3, mcm=2²×3=12)', 'xp_reward': 30,
        'learning_objective': 'Calcolo mcm e MCD'
    },
    {
        'subject': 'matematica', 'topic': 'potenze', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quanto vale 2³?',
        'option_a': '6', 'option_b': '8', 'option_c': '9', 'option_d': '5',
        'correct_answer': 'B', 'explanation': '2³ = 2 × 2 × 2 = 8', 'xp_reward': 25,
        'learning_objective': 'Calcolo delle potenze'
    },
    {
        'subject': 'matematica', 'topic': 'potenze', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il risultato di 10⁰?',
        'option_a': '10', 'option_b': '0', 'option_c': '1', 'option_d': '100',
        'correct_answer': 'C', 'explanation': 'Qualsiasi numero elevato a 0 è uguale a 1', 'xp_reward': 40,
        'learning_objective': 'Proprietà delle potenze'
    },
    {
        'subject': 'matematica', 'topic': 'frazioni', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quale frazione è equivalente a 2/4?',
        'option_a': '3/6', 'option_b': '2/3', 'option_c': '4/6', 'option_d': '1/2',
        'correct_answer': 'D', 'explanation': '2/4 semplificato = 1/2', 'xp_reward': 25,
        'learning_objective': 'Frazioni equivalenti'
    },
    {
        'subject': 'matematica', 'topic': 'frazioni', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quanto fa 3/4 + 1/4?',
        'option_a': '4/8', 'option_b': '1', 'option_c': '4/4', 'option_d': 'B e C sono corrette',
        'correct_answer': 'D', 'explanation': '3/4 + 1/4 = 4/4 = 1', 'xp_reward': 40,
        'learning_objective': 'Operazioni con frazioni'
    },
    {
        'subject': 'matematica', 'topic': 'numeri_decimali', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Come si scrive 1/2 in decimale?',
        'option_a': '0,2', 'option_b': '0,5', 'option_c': '0,25', 'option_d': '0,12',
        'correct_answer': 'B', 'explanation': '1/2 = 1 ÷ 2 = 0,5', 'xp_reward': 25,
        'learning_objective': 'Conversione frazioni-decimali'
    },
    {
        'subject': 'matematica', 'topic': 'geometria_piana', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quanti lati ha un pentagono?',
        'option_a': '4', 'option_b': '5', 'option_c': '6', 'option_d': '7',
        'correct_answer': 'B', 'explanation': 'Il pentagono ha 5 lati (penta = cinque)', 'xp_reward': 20,
        'learning_objective': 'Poligoni e loro proprietà'
    },
    {
        'subject': 'matematica', 'topic': 'geometria_piana', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il perimetro di un quadrato con lato 7 cm?',
        'option_a': '14 cm', 'option_b': '21 cm', 'option_c': '28 cm', 'option_d': '49 cm',
        'correct_answer': 'C', 'explanation': 'Perimetro quadrato = 4 × lato = 4 × 7 = 28 cm', 'xp_reward': 35,
        'learning_objective': 'Calcolo del perimetro'
    },
    {
        'subject': 'matematica', 'topic': 'geometria_piana', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è l\'area di un rettangolo con base 8 cm e altezza 5 cm?',
        'option_a': '13 cm²', 'option_b': '26 cm²', 'option_c': '40 cm²', 'option_d': '45 cm²',
        'correct_answer': 'C', 'explanation': 'Area rettangolo = base × altezza = 8 × 5 = 40 cm²', 'xp_reward': 40,
        'learning_objective': 'Calcolo dell\'area'
    },
    {
        'subject': 'matematica', 'topic': 'equazioni', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Risolvi: x + 5 = 12',
        'option_a': 'x = 17', 'option_b': 'x = 7', 'option_c': 'x = 5', 'option_d': 'x = 60',
        'correct_answer': 'B', 'explanation': 'x = 12 - 5 = 7', 'xp_reward': 30,
        'learning_objective': 'Equazioni di primo grado semplici'
    },
    {
        'subject': 'matematica', 'topic': 'equazioni', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Risolvi: 2x - 4 = 10',
        'option_a': 'x = 7', 'option_b': 'x = 3', 'option_c': 'x = 6', 'option_d': 'x = 14',
        'correct_answer': 'A', 'explanation': '2x = 10 + 4 = 14, quindi x = 14/2 = 7', 'xp_reward': 45,
        'learning_objective': 'Equazioni di primo grado'
    },
    {
        'subject': 'matematica', 'topic': 'equazioni', 'difficulty': 'difficile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Risolvi: 3(x + 2) = 21',
        'option_a': 'x = 5', 'option_b': 'x = 7', 'option_c': 'x = 9', 'option_d': 'x = 6',
        'correct_answer': 'A', 'explanation': '3x + 6 = 21, 3x = 15, x = 5', 'xp_reward': 80,
        'learning_objective': 'Equazioni con parentesi'
    },
    {
        'subject': 'matematica', 'topic': 'proporzioni', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'In una proporzione 2 : 3 = x : 12, quanto vale x?',
        'option_a': '6', 'option_b': '8', 'option_c': '4', 'option_d': '9',
        'correct_answer': 'B', 'explanation': 'x = (2 × 12) / 3 = 24 / 3 = 8', 'xp_reward': 45,
        'learning_objective': 'Proprietà delle proporzioni'
    },
    {
        'subject': 'matematica', 'topic': 'percentuali', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Quanto è il 50% di 80?',
        'option_a': '40', 'option_b': '50', 'option_c': '30', 'option_d': '60',
        'correct_answer': 'A', 'explanation': '50% di 80 = 80 × 0,5 = 40', 'xp_reward': 30,
        'learning_objective': 'Calcolo delle percentuali'
    },
    {
        'subject': 'matematica', 'topic': 'percentuali', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Un prodotto costa 50€ e viene scontato del 20%. Qual è il prezzo finale?',
        'option_a': '45€', 'option_b': '40€', 'option_c': '30€', 'option_d': '42€',
        'correct_answer': 'B', 'explanation': 'Sconto = 50 × 0,20 = 10€. Prezzo finale = 50 - 10 = 40€', 'xp_reward': 50,
        'learning_objective': 'Applicazione delle percentuali'
    },
    {
        'subject': 'matematica', 'topic': 'teorema_pitagora', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'In un triangolo rettangolo con cateti 3 e 4, quanto misura l\'ipotenusa?',
        'option_a': '7', 'option_b': '5', 'option_c': '6', 'option_d': '12',
        'correct_answer': 'B', 'explanation': 'Per Pitagora: c² = 3² + 4² = 9 + 16 = 25, quindi c = 5', 'xp_reward': 50,
        'learning_objective': 'Teorema di Pitagora'
    },
    {
        'subject': 'matematica', 'topic': 'teorema_pitagora', 'difficulty': 'difficile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Qual è la diagonale di un quadrato con lato 5 cm?',
        'option_a': '10 cm', 'option_b': '5√2 cm', 'option_c': '7 cm', 'option_d': '25 cm',
        'correct_answer': 'B', 'explanation': 'd = l√2 = 5√2 ≈ 7,07 cm', 'xp_reward': 80,
        'learning_objective': 'Applicazioni del teorema di Pitagora'
    },
    {
        'subject': 'matematica', 'topic': 'piano_cartesiano', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'In quale quadrante si trova il punto P(3, -2)?',
        'option_a': 'I quadrante', 'option_b': 'II quadrante', 'option_c': 'III quadrante', 'option_d': 'IV quadrante',
        'correct_answer': 'D', 'explanation': 'x positivo e y negativo = IV quadrante', 'xp_reward': 35,
        'learning_objective': 'Piano cartesiano'
    },
    {
        'subject': 'matematica', 'topic': 'statistica', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Qual è la media aritmetica di 4, 6, 8?',
        'option_a': '5', 'option_b': '6', 'option_c': '7', 'option_d': '18',
        'correct_answer': 'B', 'explanation': 'Media = (4 + 6 + 8) / 3 = 18 / 3 = 6', 'xp_reward': 30,
        'learning_objective': 'Calcolo della media'
    },
]

SCUOLE_MEDIE_ITALIANO = [
    {
        'subject': 'italiano', 'topic': 'analisi_grammaticale', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il genere del nome "libro"?',
        'option_a': 'Maschile', 'option_b': 'Femminile', 'option_c': 'Neutro', 'option_d': 'Invariabile',
        'correct_answer': 'A', 'explanation': '"Libro" è un nome maschile singolare', 'xp_reward': 20,
        'learning_objective': 'Genere dei nomi'
    },
    {
        'subject': 'italiano', 'topic': 'analisi_grammaticale', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il plurale di "uovo"?',
        'option_a': 'uovi', 'option_b': 'uove', 'option_c': 'uova', 'option_d': 'uovos',
        'correct_answer': 'C', 'explanation': '"Uovo" ha un plurale irregolare: "uova" (femminile)', 'xp_reward': 25,
        'learning_objective': 'Plurali irregolari'
    },
    {
        'subject': 'italiano', 'topic': 'verbi', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'A quale coniugazione appartiene il verbo "dormire"?',
        'option_a': 'Prima', 'option_b': 'Seconda', 'option_c': 'Terza', 'option_d': 'Quarta',
        'correct_answer': 'C', 'explanation': '"Dormire" termina in -ire, quindi è della terza coniugazione', 'xp_reward': 25,
        'learning_objective': 'Coniugazioni verbali'
    },
    {
        'subject': 'italiano', 'topic': 'verbi', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il passato remoto di "andare" (io)?',
        'option_a': 'io andai', 'option_b': 'io andavo', 'option_c': 'io sono andato', 'option_d': 'io vado',
        'correct_answer': 'A', 'explanation': 'Il passato remoto di "andare" (io) è "andai"', 'xp_reward': 40,
        'learning_objective': 'Tempi verbali'
    },
    {
        'subject': 'italiano', 'topic': 'verbi', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Qual è il congiuntivo presente di "avere" (che io)?',
        'option_a': 'che io abbia', 'option_b': 'che io avessi', 'option_c': 'che io ho', 'option_d': 'che io avrei',
        'correct_answer': 'A', 'explanation': 'Il congiuntivo presente di "avere" è "che io abbia"', 'xp_reward': 45,
        'learning_objective': 'Modo congiuntivo'
    },
    {
        'subject': 'italiano', 'topic': 'analisi_logica', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Nella frase "Maria mangia la mela", qual è il predicato?',
        'option_a': 'Maria', 'option_b': 'mangia', 'option_c': 'la mela', 'option_d': 'mangia la mela',
        'correct_answer': 'B', 'explanation': '"Mangia" è il predicato verbale', 'xp_reward': 25,
        'learning_objective': 'Elementi della frase'
    },
    {
        'subject': 'italiano', 'topic': 'analisi_logica', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': '"Ho regalato un libro a Marco": che complemento è "a Marco"?',
        'option_a': 'Complemento oggetto', 'option_b': 'Complemento di termine', 'option_c': 'Complemento di luogo', 'option_d': 'Complemento di tempo',
        'correct_answer': 'B', 'explanation': '"A Marco" risponde alla domanda "a chi?" = complemento di termine', 'xp_reward': 45,
        'learning_objective': 'Complementi indiretti'
    },
    {
        'subject': 'italiano', 'topic': 'analisi_periodo', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': '"Quando arrivi, chiamami" contiene una proposizione:',
        'option_a': 'causale', 'option_b': 'temporale', 'option_c': 'finale', 'option_d': 'consecutiva',
        'correct_answer': 'B', 'explanation': '"Quando arrivi" indica il tempo = proposizione temporale', 'xp_reward': 50,
        'learning_objective': 'Proposizioni subordinate'
    },
    {
        'subject': 'italiano', 'topic': 'letteratura', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Chi ha scritto la Divina Commedia?',
        'option_a': 'Petrarca', 'option_b': 'Boccaccio', 'option_c': 'Dante Alighieri', 'option_d': 'Manzoni',
        'correct_answer': 'C', 'explanation': 'La Divina Commedia è il capolavoro di Dante Alighieri', 'xp_reward': 25,
        'learning_objective': 'Autori della letteratura italiana'
    },
    {
        'subject': 'italiano', 'topic': 'letteratura', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'In quante cantiche è divisa la Divina Commedia?',
        'option_a': '2', 'option_b': '3', 'option_c': '4', 'option_d': '5',
        'correct_answer': 'B', 'explanation': 'La Divina Commedia è divisa in 3 cantiche: Inferno, Purgatorio, Paradiso', 'xp_reward': 40,
        'learning_objective': 'Struttura opere letterarie'
    },
    {
        'subject': 'italiano', 'topic': 'ortografia', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quale parola è scritta correttamente?',
        'option_a': 'sciensa', 'option_b': 'scienza', 'option_c': 'scensa', 'option_d': 'sienza',
        'correct_answer': 'B', 'explanation': 'La forma corretta è "scienza" con il gruppo -ie-', 'xp_reward': 20,
        'learning_objective': 'Ortografia corretta'
    },
    {
        'subject': 'italiano', 'topic': 'ortografia', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quando si usa l\'apostrofo con "un"?',
        'option_a': 'Sempre', 'option_b': 'Mai', 'option_c': 'Solo davanti a nomi femminili', 'option_d': 'Solo davanti a vocale',
        'correct_answer': 'C', 'explanation': 'Si scrive "un\'amica" (femminile) ma "un amico" (maschile)', 'xp_reward': 30,
        'learning_objective': 'Uso dell\'apostrofo'
    },
    {
        'subject': 'italiano', 'topic': 'figure_retoriche', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': '"Bianco come la neve" è:',
        'option_a': 'Una metafora', 'option_b': 'Una similitudine', 'option_c': 'Una metonimia', 'option_d': 'Un ossimoro',
        'correct_answer': 'B', 'explanation': 'È una similitudine: paragone esplicito con "come"', 'xp_reward': 45,
        'learning_objective': 'Figure retoriche'
    },
    {
        'subject': 'italiano', 'topic': 'figure_retoriche', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': '"Sei un leone" è:',
        'option_a': 'Una similitudine', 'option_b': 'Una metafora', 'option_c': 'Una personificazione', 'option_d': 'Un\'iperbole',
        'correct_answer': 'B', 'explanation': 'È una metafora: paragone implicito senza "come"', 'xp_reward': 45,
        'learning_objective': 'Figure retoriche'
    },
]

SCUOLE_MEDIE_STORIA = [
    {
        'subject': 'storia', 'topic': 'civilta_antiche', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Lungo quale fiume si sviluppò la civiltà egizia?',
        'option_a': 'Tigri', 'option_b': 'Nilo', 'option_c': 'Eufrate', 'option_d': 'Indo',
        'correct_answer': 'B', 'explanation': 'La civiltà egizia si sviluppò lungo il fiume Nilo', 'xp_reward': 25,
        'learning_objective': 'Civiltà fluviali'
    },
    {
        'subject': 'storia', 'topic': 'grecia_antica', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quale città greca era famosa per i suoi guerrieri?',
        'option_a': 'Atene', 'option_b': 'Sparta', 'option_c': 'Tebe', 'option_d': 'Corinto',
        'correct_answer': 'B', 'explanation': 'Sparta era famosa per la sua educazione militare', 'xp_reward': 25,
        'learning_objective': 'Polis greche'
    },
    {
        'subject': 'storia', 'topic': 'roma_antica', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Chi erano i due fratelli fondatori di Roma secondo la leggenda?',
        'option_a': 'Cesare e Augusto', 'option_b': 'Romolo e Remo', 'option_c': 'Enea e Ascanio', 'option_d': 'Numa e Tarquinio',
        'correct_answer': 'B', 'explanation': 'Secondo la leggenda, Roma fu fondata da Romolo e Remo', 'xp_reward': 25,
        'learning_objective': 'Origini di Roma'
    },
    {
        'subject': 'storia', 'topic': 'roma_antica', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Come si chiamava il senato romano più antico?',
        'option_a': 'Comizi centuriati', 'option_b': 'Concilio della plebe', 'option_c': 'Senato', 'option_d': 'Assemblea curiata',
        'correct_answer': 'C', 'explanation': 'Il Senato era l\'assemblea consultiva più importante di Roma', 'xp_reward': 40,
        'learning_objective': 'Istituzioni romane'
    },
    {
        'subject': 'storia', 'topic': 'medioevo', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'In che anno convenzionalmente inizia il Medioevo?',
        'option_a': '476 d.C.', 'option_b': '800 d.C.', 'option_c': '1000 d.C.', 'option_d': '1492',
        'correct_answer': 'A', 'explanation': 'Il Medioevo inizia convenzionalmente nel 476, caduta dell\'Impero Romano d\'Occidente', 'xp_reward': 30,
        'learning_objective': 'Periodizzazione storica'
    },
    {
        'subject': 'storia', 'topic': 'medioevo', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Cosa era il feudalesimo?',
        'option_a': 'Un sistema monetario', 'option_b': 'Un sistema politico-sociale basato sui feudi', 'option_c': 'Una religione', 'option_d': 'Un\'arte',
        'correct_answer': 'B', 'explanation': 'Il feudalesimo era un sistema dove i signori concedevano terre (feudi) in cambio di fedeltà', 'xp_reward': 45,
        'learning_objective': 'Sistema feudale'
    },
    {
        'subject': 'storia', 'topic': 'comuni', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Cosa erano i Comuni nel Medioevo italiano?',
        'option_a': 'Villaggi rurali', 'option_b': 'Città autonome con governo proprio', 'option_c': 'Monasteri', 'option_d': 'Castelli',
        'correct_answer': 'B', 'explanation': 'I Comuni erano città che si governavano autonomamente', 'xp_reward': 45,
        'learning_objective': 'Età comunale'
    },
    {
        'subject': 'storia', 'topic': 'rinascimento', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'In quale paese ebbe origine il Rinascimento?',
        'option_a': 'Francia', 'option_b': 'Germania', 'option_c': 'Italia', 'option_d': 'Inghilterra',
        'correct_answer': 'C', 'explanation': 'Il Rinascimento nacque in Italia, specialmente a Firenze', 'xp_reward': 30,
        'learning_objective': 'Rinascimento'
    },
    {
        'subject': 'storia', 'topic': 'scoperte_geografiche', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Chi scoprì l\'America nel 1492?',
        'option_a': 'Amerigo Vespucci', 'option_b': 'Vasco da Gama', 'option_c': 'Cristoforo Colombo', 'option_d': 'Ferdinando Magellano',
        'correct_answer': 'C', 'explanation': 'Cristoforo Colombo raggiunse le Americhe il 12 ottobre 1492', 'xp_reward': 25,
        'learning_objective': 'Scoperte geografiche'
    },
    {
        'subject': 'storia', 'topic': 'risorgimento', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'In che anno fu proclamato il Regno d\'Italia?',
        'option_a': '1848', 'option_b': '1861', 'option_c': '1870', 'option_d': '1918',
        'correct_answer': 'B', 'explanation': 'Il Regno d\'Italia fu proclamato il 17 marzo 1861', 'xp_reward': 40,
        'learning_objective': 'Unità d\'Italia'
    },
    {
        'subject': 'storia', 'topic': 'risorgimento', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Chi fu il primo re d\'Italia unita?',
        'option_a': 'Vittorio Emanuele I', 'option_b': 'Vittorio Emanuele II', 'option_c': 'Umberto I', 'option_d': 'Carlo Alberto',
        'correct_answer': 'B', 'explanation': 'Vittorio Emanuele II fu il primo re d\'Italia unita', 'xp_reward': 40,
        'learning_objective': 'Monarchia sabauda'
    },
]

SCUOLE_MEDIE_SCIENZE = [
    {
        'subject': 'scienze', 'topic': 'cellula', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è la differenza principale tra cellula animale e vegetale?',
        'option_a': 'La cellula vegetale ha la parete cellulare', 'option_b': 'La cellula animale ha la parete cellulare', 'option_c': 'Non c\'è differenza', 'option_d': 'La cellula animale ha i cloroplasti',
        'correct_answer': 'A', 'explanation': 'La cellula vegetale ha la parete cellulare e i cloroplasti, quella animale no', 'xp_reward': 30,
        'learning_objective': 'Struttura cellulare'
    },
    {
        'subject': 'scienze', 'topic': 'cellula', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Quale organulo è responsabile della respirazione cellulare?',
        'option_a': 'Ribosomi', 'option_b': 'Mitocondri', 'option_c': 'Cloroplasti', 'option_d': 'Nucleo',
        'correct_answer': 'B', 'explanation': 'I mitocondri sono le "centrali energetiche" della cellula', 'xp_reward': 45,
        'learning_objective': 'Organuli cellulari'
    },
    {
        'subject': 'scienze', 'topic': 'corpo_umano', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Quante ossa ha il corpo umano adulto?',
        'option_a': '106', 'option_b': '156', 'option_c': '206', 'option_d': '256',
        'correct_answer': 'C', 'explanation': 'Il corpo umano adulto ha 206 ossa', 'xp_reward': 25,
        'learning_objective': 'Apparato scheletrico'
    },
    {
        'subject': 'scienze', 'topic': 'corpo_umano', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Quale organo pompa il sangue nel corpo?',
        'option_a': 'Polmoni', 'option_b': 'Fegato', 'option_c': 'Cuore', 'option_d': 'Reni',
        'correct_answer': 'C', 'explanation': 'Il cuore è l\'organo che pompa il sangue in tutto il corpo', 'xp_reward': 30,
        'learning_objective': 'Apparato circolatorio'
    },
    {
        'subject': 'scienze', 'topic': 'chimica', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Qual è il simbolo chimico dell\'ossigeno?',
        'option_a': 'Os', 'option_b': 'O', 'option_c': 'Ox', 'option_d': 'Og',
        'correct_answer': 'B', 'explanation': 'Il simbolo chimico dell\'ossigeno è O', 'xp_reward': 20,
        'learning_objective': 'Simboli chimici'
    },
    {
        'subject': 'scienze', 'topic': 'chimica', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Quanti atomi di idrogeno ci sono in una molecola di acqua (H₂O)?',
        'option_a': '1', 'option_b': '2', 'option_c': '3', 'option_d': '4',
        'correct_answer': 'B', 'explanation': 'H₂O significa 2 atomi di idrogeno e 1 di ossigeno', 'xp_reward': 40,
        'learning_objective': 'Formule chimiche'
    },
    {
        'subject': 'scienze', 'topic': 'fisica', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Qual è l\'unità di misura della forza?',
        'option_a': 'Watt', 'option_b': 'Newton', 'option_c': 'Joule', 'option_d': 'Metro',
        'correct_answer': 'B', 'explanation': 'La forza si misura in Newton (N)', 'xp_reward': 30,
        'learning_objective': 'Unità di misura fisiche'
    },
    {
        'subject': 'scienze', 'topic': 'fisica', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Cosa misura la velocità?',
        'option_a': 'Il tempo impiegato', 'option_b': 'Lo spazio percorso nel tempo', 'option_c': 'La massa', 'option_d': 'L\'accelerazione',
        'correct_answer': 'B', 'explanation': 'La velocità = spazio/tempo (es. km/h)', 'xp_reward': 40,
        'learning_objective': 'Concetti di cinematica'
    },
    {
        'subject': 'scienze', 'topic': 'terra', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Qual è lo strato più esterno della Terra?',
        'option_a': 'Mantello', 'option_b': 'Nucleo', 'option_c': 'Crosta', 'option_d': 'Astenosfera',
        'correct_answer': 'C', 'explanation': 'La crosta terrestre è lo strato più esterno', 'xp_reward': 25,
        'learning_objective': 'Struttura della Terra'
    },
    {
        'subject': 'scienze', 'topic': 'ecosistemi', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Cosa sono i produttori in una catena alimentare?',
        'option_a': 'Animali erbivori', 'option_b': 'Animali carnivori', 'option_c': 'Piante e alghe', 'option_d': 'Funghi',
        'correct_answer': 'C', 'explanation': 'I produttori sono organismi che fanno la fotosintesi (piante, alghe)', 'xp_reward': 30,
        'learning_objective': 'Catene alimentari'
    },
]

SCUOLE_MEDIE_INGLESE = [
    {
        'subject': 'inglese', 'topic': 'verbs', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Which is the correct form: "She ___ a student"?',
        'option_a': 'are', 'option_b': 'is', 'option_c': 'am', 'option_d': 'be',
        'correct_answer': 'B', 'explanation': 'She/He/It uses "is" with the verb to be', 'xp_reward': 25,
        'learning_objective': 'Verb to be'
    },
    {
        'subject': 'inglese', 'topic': 'verbs', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'What is the past simple of "go"?',
        'option_a': 'goed', 'option_b': 'gone', 'option_c': 'went', 'option_d': 'going',
        'correct_answer': 'C', 'explanation': '"Go" is an irregular verb: go - went - gone', 'xp_reward': 30,
        'learning_objective': 'Irregular verbs'
    },
    {
        'subject': 'inglese', 'topic': 'present_continuous', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Complete: "I ___ studying English now"',
        'option_a': 'is', 'option_b': 'are', 'option_c': 'am', 'option_d': 'be',
        'correct_answer': 'C', 'explanation': 'Present continuous: I am + verb-ing', 'xp_reward': 30,
        'learning_objective': 'Present continuous'
    },
    {
        'subject': 'inglese', 'topic': 'vocabulary', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'What is "fratello" in English?',
        'option_a': 'Sister', 'option_b': 'Brother', 'option_c': 'Father', 'option_d': 'Uncle',
        'correct_answer': 'B', 'explanation': 'Fratello = Brother', 'xp_reward': 20,
        'learning_objective': 'Family vocabulary'
    },
    {
        'subject': 'inglese', 'topic': 'vocabulary', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'How do you say "verde" in English?',
        'option_a': 'Red', 'option_b': 'Blue', 'option_c': 'Green', 'option_d': 'Yellow',
        'correct_answer': 'C', 'explanation': 'Verde = Green', 'xp_reward': 20,
        'learning_objective': 'Colors vocabulary'
    },
    {
        'subject': 'inglese', 'topic': 'grammar', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Which sentence is correct?',
        'option_a': 'There is many books', 'option_b': 'There are many books', 'option_c': 'There be many books', 'option_d': 'There am many books',
        'correct_answer': 'B', 'explanation': '"There are" is used with plural nouns', 'xp_reward': 40,
        'learning_objective': 'There is/are'
    },
    {
        'subject': 'inglese', 'topic': 'grammar', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Complete: "She has ___ finished her homework"',
        'option_a': 'yet', 'option_b': 'already', 'option_c': 'ever', 'option_d': 'never',
        'correct_answer': 'B', 'explanation': '"Already" is used in affirmative sentences with present perfect', 'xp_reward': 45,
        'learning_objective': 'Present perfect'
    },
    {
        'subject': 'inglese', 'topic': 'comparatives', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'What is the comparative of "good"?',
        'option_a': 'gooder', 'option_b': 'more good', 'option_c': 'better', 'option_d': 'best',
        'correct_answer': 'C', 'explanation': '"Good" is irregular: good - better - best', 'xp_reward': 40,
        'learning_objective': 'Irregular comparatives'
    },
    {
        'subject': 'inglese', 'topic': 'conditionals', 'difficulty': 'difficile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Complete the first conditional: "If it rains, I ___ an umbrella"',
        'option_a': 'will take', 'option_b': 'would take', 'option_c': 'took', 'option_d': 'take',
        'correct_answer': 'A', 'explanation': 'First conditional: If + present, will + base verb', 'xp_reward': 70,
        'learning_objective': 'First conditional'
    },
    {
        'subject': 'inglese', 'topic': 'passive', 'difficulty': 'difficile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Transform to passive: "Shakespeare wrote Hamlet"',
        'option_a': 'Hamlet wrote by Shakespeare', 'option_b': 'Hamlet was written by Shakespeare', 'option_c': 'Hamlet is written by Shakespeare', 'option_d': 'Hamlet written Shakespeare',
        'correct_answer': 'B', 'explanation': 'Passive past: was/were + past participle + by agent', 'xp_reward': 80,
        'learning_objective': 'Passive voice'
    },
]

SCUOLE_MEDIE_GEOGRAFIA = [
    {
        'subject': 'geografia', 'topic': 'italia', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è il fiume più lungo d\'Italia?',
        'option_a': 'Tevere', 'option_b': 'Po', 'option_c': 'Adige', 'option_d': 'Arno',
        'correct_answer': 'B', 'explanation': 'Il Po è il fiume più lungo d\'Italia (652 km)', 'xp_reward': 25,
        'learning_objective': 'Idrografia italiana'
    },
    {
        'subject': 'geografia', 'topic': 'italia', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 1,
        'question': 'Qual è la montagna più alta d\'Italia?',
        'option_a': 'Monte Rosa', 'option_b': 'Monte Bianco', 'option_c': 'Cervino', 'option_d': 'Gran Paradiso',
        'correct_answer': 'B', 'explanation': 'Il Monte Bianco è la montagna più alta (4.808 m)', 'xp_reward': 25,
        'learning_objective': 'Orografia italiana'
    },
    {
        'subject': 'geografia', 'topic': 'europa', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Qual è la capitale della Germania?',
        'option_a': 'Monaco', 'option_b': 'Francoforte', 'option_c': 'Berlino', 'option_d': 'Amburgo',
        'correct_answer': 'C', 'explanation': 'Berlino è la capitale della Germania', 'xp_reward': 25,
        'learning_objective': 'Capitali europee'
    },
    {
        'subject': 'geografia', 'topic': 'europa', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Quanti stati fanno parte dell\'Unione Europea (2024)?',
        'option_a': '25', 'option_b': '27', 'option_c': '28', 'option_d': '30',
        'correct_answer': 'B', 'explanation': 'L\'UE conta 27 stati membri (dopo Brexit)', 'xp_reward': 40,
        'learning_objective': 'Unione Europea'
    },
    {
        'subject': 'geografia', 'topic': 'mondo', 'difficulty': 'facile',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Qual è il continente più grande?',
        'option_a': 'Africa', 'option_b': 'Europa', 'option_c': 'Asia', 'option_d': 'America',
        'correct_answer': 'C', 'explanation': 'L\'Asia è il continente più grande (44,6 milioni km²)', 'xp_reward': 25,
        'learning_objective': 'Continenti'
    },
    {
        'subject': 'geografia', 'topic': 'mondo', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Qual è l\'oceano più vasto?',
        'option_a': 'Atlantico', 'option_b': 'Indiano', 'option_c': 'Pacifico', 'option_d': 'Artico',
        'correct_answer': 'C', 'explanation': 'L\'Oceano Pacifico è il più grande (165 milioni km²)', 'xp_reward': 35,
        'learning_objective': 'Oceani'
    },
    {
        'subject': 'geografia', 'topic': 'clima', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 2,
        'question': 'Cosa caratterizza il clima mediterraneo?',
        'option_a': 'Inverni freddi e estati piovose', 'option_b': 'Estati calde e secche, inverni miti e piovosi', 'option_c': 'Temperature sempre uguali', 'option_d': 'Piogge tutto l\'anno',
        'correct_answer': 'B', 'explanation': 'Il clima mediterraneo ha estati calde-secche e inverni miti-piovosi', 'xp_reward': 45,
        'learning_objective': 'Climi'
    },
    {
        'subject': 'geografia', 'topic': 'economia', 'difficulty': 'medio',
        'grade_level': 'medie', 'grade_year': 3,
        'question': 'Cosa si intende per "settore terziario"?',
        'option_a': 'Agricoltura', 'option_b': 'Industria', 'option_c': 'Servizi', 'option_d': 'Artigianato',
        'correct_answer': 'C', 'explanation': 'Il terziario comprende i servizi (commercio, turismo, sanità...)', 'xp_reward': 40,
        'learning_objective': 'Settori economici'
    },
]

SCUOLE_SUPERIORI_MATEMATICA = [
    {
        'subject': 'matematica', 'topic': 'equazioni_secondo_grado', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Quali sono le soluzioni di x² - 5x + 6 = 0?',
        'option_a': 'x = 2 e x = 3', 'option_b': 'x = -2 e x = -3', 'option_c': 'x = 1 e x = 6', 'option_d': 'x = -1 e x = -6',
        'correct_answer': 'A', 'explanation': 'Scomponendo: (x-2)(x-3) = 0, quindi x = 2 o x = 3', 'xp_reward': 50,
        'learning_objective': 'Equazioni di secondo grado'
    },
    {
        'subject': 'matematica', 'topic': 'equazioni_secondo_grado', 'difficulty': 'difficile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Qual è il discriminante di 2x² - 4x + 2 = 0?',
        'option_a': '0', 'option_b': '8', 'option_c': '-8', 'option_d': '16',
        'correct_answer': 'A', 'explanation': 'Δ = b² - 4ac = 16 - 16 = 0 (due soluzioni coincidenti)', 'xp_reward': 80,
        'learning_objective': 'Formula del discriminante'
    },
    {
        'subject': 'matematica', 'topic': 'disequazioni', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Risolvi: 2x - 3 > 5',
        'option_a': 'x > 4', 'option_b': 'x > 1', 'option_c': 'x < 4', 'option_d': 'x > 8',
        'correct_answer': 'A', 'explanation': '2x > 8, quindi x > 4', 'xp_reward': 45,
        'learning_objective': 'Disequazioni di primo grado'
    },
    {
        'subject': 'matematica', 'topic': 'sistemi', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Risolvi il sistema: x + y = 5 e x - y = 1',
        'option_a': 'x = 3, y = 2', 'option_b': 'x = 2, y = 3', 'option_c': 'x = 4, y = 1', 'option_d': 'x = 1, y = 4',
        'correct_answer': 'A', 'explanation': 'Sommando: 2x = 6, x = 3. Sostituendo: y = 2', 'xp_reward': 50,
        'learning_objective': 'Sistemi lineari'
    },
    {
        'subject': 'matematica', 'topic': 'funzioni', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Qual è il dominio di f(x) = √(x - 2)?',
        'option_a': 'x ≥ 2', 'option_b': 'x > 2', 'option_c': 'x ≥ 0', 'option_d': 'Tutti i reali',
        'correct_answer': 'A', 'explanation': 'Il radicando deve essere ≥ 0: x - 2 ≥ 0, quindi x ≥ 2', 'xp_reward': 55,
        'learning_objective': 'Dominio di funzioni'
    },
    {
        'subject': 'matematica', 'topic': 'logaritmi', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Quanto vale log₁₀(100)?',
        'option_a': '1', 'option_b': '2', 'option_c': '10', 'option_d': '100',
        'correct_answer': 'B', 'explanation': 'log₁₀(100) = log₁₀(10²) = 2', 'xp_reward': 50,
        'learning_objective': 'Logaritmi'
    },
    {
        'subject': 'matematica', 'topic': 'esponenziali', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Risolvi: 2ˣ = 8',
        'option_a': 'x = 2', 'option_b': 'x = 3', 'option_c': 'x = 4', 'option_d': 'x = 8',
        'correct_answer': 'B', 'explanation': '2ˣ = 2³, quindi x = 3', 'xp_reward': 45,
        'learning_objective': 'Equazioni esponenziali'
    },
    {
        'subject': 'matematica', 'topic': 'trigonometria', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Quanto vale sin(90°)?',
        'option_a': '0', 'option_b': '1', 'option_c': '-1', 'option_d': '1/2',
        'correct_answer': 'B', 'explanation': 'sin(90°) = 1', 'xp_reward': 45,
        'learning_objective': 'Funzioni trigonometriche'
    },
    {
        'subject': 'matematica', 'topic': 'trigonometria', 'difficulty': 'difficile',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Qual è l\'identità fondamentale della trigonometria?',
        'option_a': 'sin²x + cos²x = 1', 'option_b': 'sin x + cos x = 1', 'option_c': 'tan x = sin x + cos x', 'option_d': 'sin x = 1/cos x',
        'correct_answer': 'A', 'explanation': 'L\'identità fondamentale è sin²x + cos²x = 1', 'xp_reward': 70,
        'learning_objective': 'Identità trigonometriche'
    },
    {
        'subject': 'matematica', 'topic': 'derivate', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Qual è la derivata di f(x) = x²?',
        'option_a': 'f\'(x) = x', 'option_b': 'f\'(x) = 2x', 'option_c': 'f\'(x) = 2', 'option_d': 'f\'(x) = x³',
        'correct_answer': 'B', 'explanation': 'Derivata di xⁿ = n·xⁿ⁻¹, quindi (x²)\' = 2x', 'xp_reward': 50,
        'learning_objective': 'Derivate fondamentali'
    },
    {
        'subject': 'matematica', 'topic': 'derivate', 'difficulty': 'difficile',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Qual è la derivata di f(x) = eˣ?',
        'option_a': 'f\'(x) = x·eˣ⁻¹', 'option_b': 'f\'(x) = eˣ', 'option_c': 'f\'(x) = e', 'option_d': 'f\'(x) = ln(x)',
        'correct_answer': 'B', 'explanation': 'La derivata di eˣ è eˣ stesso', 'xp_reward': 70,
        'learning_objective': 'Derivata esponenziale'
    },
    {
        'subject': 'matematica', 'topic': 'integrali', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'Qual è l\'integrale indefinito di f(x) = 2x?',
        'option_a': 'x² + C', 'option_b': '2 + C', 'option_c': 'x + C', 'option_d': '2x² + C',
        'correct_answer': 'A', 'explanation': '∫2x dx = x² + C', 'xp_reward': 55,
        'learning_objective': 'Integrali indefiniti'
    },
    {
        'subject': 'matematica', 'topic': 'limiti', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Quanto vale lim(x→0) sin(x)/x?',
        'option_a': '0', 'option_b': '1', 'option_c': '∞', 'option_d': 'Non esiste',
        'correct_answer': 'B', 'explanation': 'È un limite notevole: lim(x→0) sin(x)/x = 1', 'xp_reward': 60,
        'learning_objective': 'Limiti notevoli'
    },
]

SCUOLE_SUPERIORI_ITALIANO = [
    {
        'subject': 'italiano', 'topic': 'letteratura_medievale', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Chi sono le "tre corone" della letteratura italiana?',
        'option_a': 'Dante, Petrarca, Boccaccio', 'option_b': 'Manzoni, Leopardi, Foscolo', 'option_c': 'Ariosto, Tasso, Machiavelli', 'option_d': 'Carducci, Pascoli, D\'Annunzio',
        'correct_answer': 'A', 'explanation': 'Dante, Petrarca e Boccaccio sono le "tre corone" del Trecento', 'xp_reward': 30,
        'learning_objective': 'Letteratura del Trecento'
    },
    {
        'subject': 'italiano', 'topic': 'divina_commedia', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Chi guida Dante nell\'Inferno e nel Purgatorio?',
        'option_a': 'Beatrice', 'option_b': 'Virgilio', 'option_c': 'San Bernardo', 'option_d': 'Caronte',
        'correct_answer': 'B', 'explanation': 'Virgilio guida Dante in Inferno e Purgatorio, Beatrice nel Paradiso', 'xp_reward': 45,
        'learning_objective': 'Divina Commedia'
    },
    {
        'subject': 'italiano', 'topic': 'divina_commedia', 'difficulty': 'difficile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Quanti canti ha ogni cantica della Divina Commedia?',
        'option_a': '30', 'option_b': '33', 'option_c': '34', 'option_d': '100',
        'correct_answer': 'B', 'explanation': 'Ogni cantica ha 33 canti (+ 1 proemio nell\'Inferno = 100 totali)', 'xp_reward': 70,
        'learning_objective': 'Struttura Divina Commedia'
    },
    {
        'subject': 'italiano', 'topic': 'petrarca', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Come si chiama la raccolta poetica più famosa di Petrarca?',
        'option_a': 'Decameron', 'option_b': 'Canzoniere', 'option_c': 'Orlando Furioso', 'option_d': 'Gerusalemme Liberata',
        'correct_answer': 'B', 'explanation': 'Il Canzoniere (Rerum vulgarium fragmenta) è l\'opera principale di Petrarca', 'xp_reward': 45,
        'learning_objective': 'Opere di Petrarca'
    },
    {
        'subject': 'italiano', 'topic': 'boccaccio', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Quante novelle contiene il Decameron?',
        'option_a': '50', 'option_b': '100', 'option_c': '10', 'option_d': '1000',
        'correct_answer': 'B', 'explanation': 'Il Decameron contiene 100 novelle (10 narratori × 10 giorni)', 'xp_reward': 35,
        'learning_objective': 'Decameron'
    },
    {
        'subject': 'italiano', 'topic': 'machiavelli', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Qual è l\'opera politica principale di Machiavelli?',
        'option_a': 'I Discorsi', 'option_b': 'Il Principe', 'option_c': 'L\'Arte della guerra', 'option_d': 'La Mandragola',
        'correct_answer': 'B', 'explanation': 'Il Principe è il trattato politico più celebre di Machiavelli', 'xp_reward': 40,
        'learning_objective': 'Letteratura del Rinascimento'
    },
    {
        'subject': 'italiano', 'topic': 'manzoni', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Chi sono i protagonisti de "I Promessi Sposi"?',
        'option_a': 'Romeo e Giulietta', 'option_b': 'Renzo e Lucia', 'option_c': 'Paolo e Francesca', 'option_d': 'Jacopo e Teresa',
        'correct_answer': 'B', 'explanation': 'Renzo Tramaglino e Lucia Mondella sono i protagonisti', 'xp_reward': 25,
        'learning_objective': 'I Promessi Sposi'
    },
    {
        'subject': 'italiano', 'topic': 'manzoni', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'In quale anno è ambientato il romanzo "I Promessi Sposi"?',
        'option_a': '1628-1630', 'option_b': '1800-1802', 'option_c': '1500-1502', 'option_d': '1700-1702',
        'correct_answer': 'A', 'explanation': 'Il romanzo è ambientato tra il 1628 e il 1630', 'xp_reward': 45,
        'learning_objective': 'I Promessi Sposi - contesto'
    },
    {
        'subject': 'italiano', 'topic': 'leopardi', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Quale opera in prosa di Leopardi raccoglie i suoi pensieri filosofici?',
        'option_a': 'Zibaldone', 'option_b': 'Canti', 'option_c': 'Operette morali', 'option_d': 'Paralipomeni',
        'correct_answer': 'A', 'explanation': 'Lo Zibaldone è il diario di pensieri filosofici e letterari', 'xp_reward': 50,
        'learning_objective': 'Opere di Leopardi'
    },
    {
        'subject': 'italiano', 'topic': 'verismo', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Chi è il principale esponente del Verismo italiano?',
        'option_a': 'Luigi Pirandello', 'option_b': 'Giovanni Verga', 'option_c': 'Gabriele D\'Annunzio', 'option_d': 'Italo Svevo',
        'correct_answer': 'B', 'explanation': 'Giovanni Verga è il maggior rappresentante del Verismo', 'xp_reward': 45,
        'learning_objective': 'Verismo'
    },
    {
        'subject': 'italiano', 'topic': 'pirandello', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'Qual è il romanzo più famoso di Pirandello?',
        'option_a': 'Sei personaggi in cerca d\'autore', 'option_b': 'Il fu Mattia Pascal', 'option_c': 'La coscienza di Zeno', 'option_d': 'I Malavoglia',
        'correct_answer': 'B', 'explanation': 'Il fu Mattia Pascal è il romanzo più celebre di Pirandello', 'xp_reward': 45,
        'learning_objective': 'Pirandello'
    },
]

SCUOLE_SUPERIORI_FISICA = [
    {
        'subject': 'fisica', 'topic': 'cinematica', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Qual è la formula della velocità media?',
        'option_a': 'v = s × t', 'option_b': 'v = s / t', 'option_c': 'v = t / s', 'option_d': 'v = s + t',
        'correct_answer': 'B', 'explanation': 'La velocità media è spazio diviso tempo: v = s/t', 'xp_reward': 30,
        'learning_objective': 'Velocità'
    },
    {
        'subject': 'fisica', 'topic': 'cinematica', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Un\'auto viaggia a 72 km/h. Quanti m/s sono?',
        'option_a': '10 m/s', 'option_b': '20 m/s', 'option_c': '72 m/s', 'option_d': '7,2 m/s',
        'correct_answer': 'B', 'explanation': '72 km/h = 72 × 1000 / 3600 = 20 m/s', 'xp_reward': 45,
        'learning_objective': 'Conversione unità'
    },
    {
        'subject': 'fisica', 'topic': 'dinamica', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Qual è la seconda legge di Newton?',
        'option_a': 'F = m × a', 'option_b': 'F = m / a', 'option_c': 'F = m + a', 'option_d': 'F = m - a',
        'correct_answer': 'A', 'explanation': 'La seconda legge di Newton: F = m × a (forza = massa × accelerazione)', 'xp_reward': 35,
        'learning_objective': 'Leggi di Newton'
    },
    {
        'subject': 'fisica', 'topic': 'dinamica', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Quale forza mantiene in orbita i pianeti attorno al Sole?',
        'option_a': 'Forza elettrica', 'option_b': 'Forza gravitazionale', 'option_c': 'Forza magnetica', 'option_d': 'Forza nucleare',
        'correct_answer': 'B', 'explanation': 'La forza gravitazionale mantiene i pianeti in orbita', 'xp_reward': 40,
        'learning_objective': 'Gravitazione'
    },
    {
        'subject': 'fisica', 'topic': 'energia', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Qual è la formula dell\'energia cinetica?',
        'option_a': 'Ec = mgh', 'option_b': 'Ec = ½mv²', 'option_c': 'Ec = Fs', 'option_d': 'Ec = mv',
        'correct_answer': 'B', 'explanation': 'Energia cinetica: Ec = ½mv²', 'xp_reward': 35,
        'learning_objective': 'Energia cinetica'
    },
    {
        'subject': 'fisica', 'topic': 'energia', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Qual è la formula dell\'energia potenziale gravitazionale?',
        'option_a': 'Ep = ½mv²', 'option_b': 'Ep = mgh', 'option_c': 'Ep = Fs', 'option_d': 'Ep = mg',
        'correct_answer': 'B', 'explanation': 'Energia potenziale: Ep = mgh (massa × gravità × altezza)', 'xp_reward': 40,
        'learning_objective': 'Energia potenziale'
    },
    {
        'subject': 'fisica', 'topic': 'termodinamica', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'A quanti gradi Celsius corrisponde 0 Kelvin?',
        'option_a': '0°C', 'option_b': '-273,15°C', 'option_c': '273,15°C', 'option_d': '-100°C',
        'correct_answer': 'B', 'explanation': '0 K = -273,15°C (zero assoluto)', 'xp_reward': 45,
        'learning_objective': 'Scale termometriche'
    },
    {
        'subject': 'fisica', 'topic': 'elettricita', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Qual è l\'unità di misura della corrente elettrica?',
        'option_a': 'Volt', 'option_b': 'Ohm', 'option_c': 'Ampere', 'option_d': 'Watt',
        'correct_answer': 'C', 'explanation': 'La corrente elettrica si misura in Ampere (A)', 'xp_reward': 30,
        'learning_objective': 'Grandezze elettriche'
    },
    {
        'subject': 'fisica', 'topic': 'elettricita', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Qual è la legge di Ohm?',
        'option_a': 'V = R / I', 'option_b': 'V = I × R', 'option_c': 'V = I + R', 'option_d': 'V = I - R',
        'correct_answer': 'B', 'explanation': 'Legge di Ohm: V = I × R (tensione = corrente × resistenza)', 'xp_reward': 45,
        'learning_objective': 'Legge di Ohm'
    },
    {
        'subject': 'fisica', 'topic': 'onde', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Qual è la velocità della luce nel vuoto?',
        'option_a': '300.000 m/s', 'option_b': '300.000 km/s', 'option_c': '30.000 km/s', 'option_d': '3.000.000 km/s',
        'correct_answer': 'B', 'explanation': 'La velocità della luce è circa 300.000 km/s (3×10⁸ m/s)', 'xp_reward': 40,
        'learning_objective': 'Velocità della luce'
    },
]

SCUOLE_SUPERIORI_STORIA = [
    {
        'subject': 'storia', 'topic': 'rivoluzione_francese', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'In che anno iniziò la Rivoluzione Francese?',
        'option_a': '1776', 'option_b': '1789', 'option_c': '1799', 'option_d': '1815',
        'correct_answer': 'B', 'explanation': 'La Rivoluzione Francese iniziò nel 1789 con la presa della Bastiglia', 'xp_reward': 30,
        'learning_objective': 'Rivoluzione Francese'
    },
    {
        'subject': 'storia', 'topic': 'rivoluzione_francese', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Qual era il motto della Rivoluzione Francese?',
        'option_a': 'Libertà, Uguaglianza, Fraternità', 'option_b': 'Ordine e Progresso', 'option_c': 'Unità, Forza, Vittoria', 'option_d': 'Pace, Pane, Lavoro',
        'correct_answer': 'A', 'explanation': 'Liberté, Égalité, Fraternité (Libertà, Uguaglianza, Fraternità)', 'xp_reward': 40,
        'learning_objective': 'Ideali rivoluzionari'
    },
    {
        'subject': 'storia', 'topic': 'napoleone', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'In quale battaglia Napoleone fu definitivamente sconfitto?',
        'option_a': 'Austerlitz', 'option_b': 'Waterloo', 'option_c': 'Trafalgar', 'option_d': 'Lipsia',
        'correct_answer': 'B', 'explanation': 'Napoleone fu sconfitto definitivamente a Waterloo nel 1815', 'xp_reward': 45,
        'learning_objective': 'Età napoleonica'
    },
    {
        'subject': 'storia', 'topic': 'risorgimento', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Chi era il primo ministro che guidò l\'unificazione italiana?',
        'option_a': 'Mazzini', 'option_b': 'Garibaldi', 'option_c': 'Cavour', 'option_d': 'Gioberti',
        'correct_answer': 'C', 'explanation': 'Camillo Benso conte di Cavour fu l\'artefice politico dell\'unità', 'xp_reward': 45,
        'learning_objective': 'Risorgimento italiano'
    },
    {
        'subject': 'storia', 'topic': 'prima_guerra_mondiale', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'Quale evento scatenò la Prima Guerra Mondiale?',
        'option_a': 'L\'invasione del Belgio', 'option_b': 'L\'attentato di Sarajevo', 'option_c': 'L\'affondamento del Lusitania', 'option_d': 'La rivoluzione russa',
        'correct_answer': 'B', 'explanation': 'L\'assassinio dell\'arciduca Francesco Ferdinando a Sarajevo (28 giugno 1914)', 'xp_reward': 35,
        'learning_objective': 'Cause Prima Guerra Mondiale'
    },
    {
        'subject': 'storia', 'topic': 'prima_guerra_mondiale', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'Quando l\'Italia entrò nella Prima Guerra Mondiale e con chi?',
        'option_a': '1914, con la Germania', 'option_b': '1915, con Francia e Inghilterra', 'option_c': '1916, neutrale', 'option_d': '1917, con gli USA',
        'correct_answer': 'B', 'explanation': 'L\'Italia entrò nel 1915 con la Triplice Intesa (Patto di Londra)', 'xp_reward': 50,
        'learning_objective': 'Italia nella Grande Guerra'
    },
    {
        'subject': 'storia', 'topic': 'fascismo', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'In che anno Mussolini ottenne il potere con la Marcia su Roma?',
        'option_a': '1919', 'option_b': '1922', 'option_c': '1925', 'option_d': '1929',
        'correct_answer': 'B', 'explanation': 'La Marcia su Roma avvenne il 28 ottobre 1922', 'xp_reward': 45,
        'learning_objective': 'Fascismo'
    },
    {
        'subject': 'storia', 'topic': 'seconda_guerra_mondiale', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'In che anno iniziò la Seconda Guerra Mondiale?',
        'option_a': '1937', 'option_b': '1939', 'option_c': '1941', 'option_d': '1942',
        'correct_answer': 'B', 'explanation': 'La Seconda Guerra Mondiale iniziò il 1° settembre 1939', 'xp_reward': 30,
        'learning_objective': 'Seconda Guerra Mondiale'
    },
    {
        'subject': 'storia', 'topic': 'guerra_fredda', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'In che anno cadde il Muro di Berlino?',
        'option_a': '1985', 'option_b': '1989', 'option_c': '1991', 'option_d': '1995',
        'correct_answer': 'B', 'explanation': 'Il Muro di Berlino cadde il 9 novembre 1989', 'xp_reward': 40,
        'learning_objective': 'Fine Guerra Fredda'
    },
]

SCUOLE_SUPERIORI_FILOSOFIA = [
    {
        'subject': 'filosofia', 'topic': 'filosofia_greca', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Chi è considerato il padre della filosofia occidentale?',
        'option_a': 'Platone', 'option_b': 'Aristotele', 'option_c': 'Socrate', 'option_d': 'Talete',
        'correct_answer': 'C', 'explanation': 'Socrate è considerato il padre della filosofia occidentale', 'xp_reward': 30,
        'learning_objective': 'Filosofia greca'
    },
    {
        'subject': 'filosofia', 'topic': 'platone', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Cosa sono le "idee" secondo Platone?',
        'option_a': 'Pensieri personali', 'option_b': 'Modelli perfetti ed eterni delle cose', 'option_c': 'Opinioni comuni', 'option_d': 'Sensazioni fisiche',
        'correct_answer': 'B', 'explanation': 'Le Idee platoniche sono modelli perfetti ed eterni di cui le cose sono copie', 'xp_reward': 50,
        'learning_objective': 'Teoria delle Idee'
    },
    {
        'subject': 'filosofia', 'topic': 'aristotele', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 3,
        'question': 'Qual è il sillogismo aristotelico?',
        'option_a': 'Un ragionamento deduttivo con premessa maggiore, minore e conclusione', 'option_b': 'Un tipo di dialogo', 'option_c': 'Una forma di poesia', 'option_d': 'Un metodo scientifico',
        'correct_answer': 'A', 'explanation': 'Il sillogismo è un ragionamento deduttivo con tre proposizioni', 'xp_reward': 55,
        'learning_objective': 'Logica aristotelica'
    },
    {
        'subject': 'filosofia', 'topic': 'cartesio', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Quale celebre frase è attribuita a Cartesio?',
        'option_a': 'L\'uomo è la misura di tutte le cose', 'option_b': 'Cogito ergo sum', 'option_c': 'So di non sapere', 'option_d': 'La vita è sogno',
        'correct_answer': 'B', 'explanation': '"Cogito ergo sum" (Penso dunque sono) è il principio fondamentale di Cartesio', 'xp_reward': 35,
        'learning_objective': 'Razionalismo cartesiano'
    },
    {
        'subject': 'filosofia', 'topic': 'kant', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 4,
        'question': 'Qual è l\'opera principale di Kant sulla conoscenza?',
        'option_a': 'Critica della ragion pratica', 'option_b': 'Critica della ragion pura', 'option_c': 'Critica del giudizio', 'option_d': 'Fondazione della metafisica dei costumi',
        'correct_answer': 'B', 'explanation': 'La Critica della ragion pura (1781) esamina i limiti della conoscenza', 'xp_reward': 50,
        'learning_objective': 'Filosofia kantiana'
    },
    {
        'subject': 'filosofia', 'topic': 'hegel', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'Qual è il processo dialettico hegeliano?',
        'option_a': 'Tesi, antitesi, sintesi', 'option_b': 'Inizio, sviluppo, fine', 'option_c': 'Essere, divenire, nulla', 'option_d': 'Soggetto, oggetto, assoluto',
        'correct_answer': 'A', 'explanation': 'La dialettica hegeliana procede per tesi, antitesi e sintesi', 'xp_reward': 55,
        'learning_objective': 'Dialettica hegeliana'
    },
    {
        'subject': 'filosofia', 'topic': 'marx', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'Cosa intende Marx per "materialismo storico"?',
        'option_a': 'La storia è determinata dalle idee', 'option_b': 'La storia è determinata dai rapporti economici di produzione', 'option_c': 'La storia è ciclica', 'option_d': 'La storia è guidata dai grandi uomini',
        'correct_answer': 'B', 'explanation': 'Per Marx la struttura economica determina la sovrastruttura ideologica', 'xp_reward': 60,
        'learning_objective': 'Materialismo storico'
    },
    {
        'subject': 'filosofia', 'topic': 'nietzsche', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 5,
        'question': 'Cosa intende Nietzsche con "morte di Dio"?',
        'option_a': 'La fine della religione', 'option_b': 'La crisi dei valori tradizionali', 'option_c': 'L\'ateismo scientifico', 'option_d': 'La fine del mondo',
        'correct_answer': 'B', 'explanation': 'La "morte di Dio" simboleggia la crisi dei valori assoluti della tradizione', 'xp_reward': 60,
        'learning_objective': 'Nichilismo nietzschiano'
    },
]

SCUOLE_SUPERIORI_LATINO = [
    {
        'subject': 'latino', 'topic': 'grammatica', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Quante declinazioni ha il latino?',
        'option_a': '3', 'option_b': '4', 'option_c': '5', 'option_d': '6',
        'correct_answer': 'C', 'explanation': 'Il latino ha 5 declinazioni per i nomi', 'xp_reward': 25,
        'learning_objective': 'Declinazioni latine'
    },
    {
        'subject': 'latino', 'topic': 'grammatica', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Qual è il nominativo singolare di "rosa, rosae" (rosa)?',
        'option_a': 'rosam', 'option_b': 'rosae', 'option_c': 'rosa', 'option_d': 'rosarum',
        'correct_answer': 'C', 'explanation': '"Rosa" è il nominativo singolare (I declinazione)', 'xp_reward': 25,
        'learning_objective': 'Prima declinazione'
    },
    {
        'subject': 'latino', 'topic': 'grammatica', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Quale caso latino risponde alla domanda "a chi? per chi?"?',
        'option_a': 'Genitivo', 'option_b': 'Dativo', 'option_c': 'Accusativo', 'option_d': 'Ablativo',
        'correct_answer': 'B', 'explanation': 'Il dativo indica il complemento di termine', 'xp_reward': 40,
        'learning_objective': 'Casi latini'
    },
    {
        'subject': 'latino', 'topic': 'verbi', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Quante coniugazioni ha il verbo latino?',
        'option_a': '3', 'option_b': '4', 'option_c': '5', 'option_d': '2',
        'correct_answer': 'B', 'explanation': 'Il latino ha 4 coniugazioni verbali regolari', 'xp_reward': 25,
        'learning_objective': 'Coniugazioni latine'
    },
    {
        'subject': 'latino', 'topic': 'verbi', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 1,
        'question': 'Come si traduce "amo" (presente indicativo, I persona singolare)?',
        'option_a': 'Io amo', 'option_b': 'Io amavo', 'option_c': 'Io amerò', 'option_d': 'Io amai',
        'correct_answer': 'A', 'explanation': '"Amo" = io amo (presente indicativo attivo)', 'xp_reward': 35,
        'learning_objective': 'Presente indicativo'
    },
    {
        'subject': 'latino', 'topic': 'letteratura', 'difficulty': 'facile',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Chi ha scritto l\'Eneide?',
        'option_a': 'Ovidio', 'option_b': 'Orazio', 'option_c': 'Virgilio', 'option_d': 'Cicerone',
        'correct_answer': 'C', 'explanation': 'L\'Eneide è il poema epico di Publio Virgilio Marone', 'xp_reward': 30,
        'learning_objective': 'Letteratura latina'
    },
    {
        'subject': 'latino', 'topic': 'letteratura', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Chi è il protagonista dell\'Eneide?',
        'option_a': 'Ulisse', 'option_b': 'Achille', 'option_c': 'Enea', 'option_d': 'Ettore',
        'correct_answer': 'C', 'explanation': 'Enea, eroe troiano, è il protagonista dell\'Eneide', 'xp_reward': 35,
        'learning_objective': 'Eneide'
    },
    {
        'subject': 'latino', 'topic': 'sintassi', 'difficulty': 'medio',
        'grade_level': 'superiori', 'grade_year': 2,
        'question': 'Cosa introduce la congiunzione "cum" + congiuntivo?',
        'option_a': 'Solo proposizioni temporali', 'option_b': 'Proposizioni temporali, causali, concessive', 'option_c': 'Solo proposizioni causali', 'option_d': 'Proposizioni finali',
        'correct_answer': 'B', 'explanation': '"Cum" + congiuntivo introduce il cum narrativo (temporale, causale, concessivo)', 'xp_reward': 50,
        'learning_objective': 'Proposizioni subordinate'
    },
]

def get_all_quizzes():
    """Restituisce tutti i quiz organizzati per livello scolastico"""
    return {
        'scuole_medie': {
            'matematica': SCUOLE_MEDIE_MATEMATICA,
            'italiano': SCUOLE_MEDIE_ITALIANO,
            'storia': SCUOLE_MEDIE_STORIA,
            'scienze': SCUOLE_MEDIE_SCIENZE,
            'inglese': SCUOLE_MEDIE_INGLESE,
            'geografia': SCUOLE_MEDIE_GEOGRAFIA,
        },
        'scuole_superiori': {
            'matematica': SCUOLE_SUPERIORI_MATEMATICA,
            'italiano': SCUOLE_SUPERIORI_ITALIANO,
            'fisica': SCUOLE_SUPERIORI_FISICA,
            'storia': SCUOLE_SUPERIORI_STORIA,
            'filosofia': SCUOLE_SUPERIORI_FILOSOFIA,
            'latino': SCUOLE_SUPERIORI_LATINO,
        }
    }

def count_quizzes():
    """Conta il numero totale di quiz"""
    all_quizzes = get_all_quizzes()
    total = 0
    for level, subjects in all_quizzes.items():
        for subject, quizzes in subjects.items():
            total += len(quizzes)
            print(f"  {level} - {subject}: {len(quizzes)} quiz")
    return total
