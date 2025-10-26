"""
Password Validation Service
Validazione robusta delle password con policy di sicurezza
"""

import re

# Lista password comuni da bloccare
COMMON_PASSWORDS = {
    'password', 'password123', '12345678', 'qwerty', 'abc123', 'monkey',
    'letmein', 'trustno1', 'dragon', 'baseball', 'iloveyou', 'master',
    'sunshine', 'ashley', 'bailey', 'passw0rd', 'shadow', 'superman',
    'qazwsx', 'welcome', 'admin', 'admin123', 'root', 'toor', 'pass',
    'test', 'guest', 'info', 'adm', 'mysql', 'user', 'administrator',
    'oracle', 'ftp', 'pi', 'puppet', 'ansible', 'ec2-user', 'vagrant',
    'azureuser', 'skaila', 'skaila123', 'scuola', 'studente'
}

def validate_password(password: str) -> tuple[bool, str]:
    """
    Valida la robustezza della password secondo policy di sicurezza.
    
    Policy:
    - Minimo 8 caratteri
    - Almeno una lettera maiuscola
    - Almeno una lettera minuscola
    - Almeno un numero
    - Almeno un carattere speciale
    - Non deve essere una password comune
    
    Args:
        password: Password da validare
        
    Returns:
        (is_valid, message): Tupla con esito validazione e messaggio errore
    """
    # Lunghezza minima
    if len(password) < 8:
        return False, "La password deve essere di almeno 8 caratteri"
    
    # Lunghezza massima (prevenzione DoS)
    if len(password) > 128:
        return False, "La password non può superare 128 caratteri"
    
    # Almeno una lettera maiuscola
    if not re.search(r'[A-Z]', password):
        return False, "La password deve contenere almeno una lettera maiuscola"
    
    # Almeno una lettera minuscola
    if not re.search(r'[a-z]', password):
        return False, "La password deve contenere almeno una lettera minuscola"
    
    # Almeno un numero
    if not re.search(r'\d', password):
        return False, "La password deve contenere almeno un numero"
    
    # Almeno un carattere speciale
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', password):
        return False, "La password deve contenere almeno un carattere speciale (!@#$%^&*...)"
    
    # Controllo password comuni (case-insensitive)
    if password.lower() in COMMON_PASSWORDS:
        return False, "Password troppo comune. Scegli una password più sicura"
    
    # Controllo pattern sequenziali
    if has_sequential_pattern(password):
        return False, "La password contiene pattern sequenziali troppo semplici"
    
    return True, "Password valida"

def has_sequential_pattern(password: str) -> bool:
    """
    Controlla se la password contiene pattern sequenziali ovvi.
    
    Es: 'abcd', '1234', 'qwerty', ecc.
    """
    password_lower = password.lower()
    
    # Sequenze numeriche
    sequences = ['0123', '1234', '2345', '3456', '4567', '5678', '6789']
    for seq in sequences:
        if seq in password_lower or seq[::-1] in password_lower:
            return True
    
    # Sequenze alfabetiche
    alpha_sequences = ['abcd', 'bcde', 'cdef', 'defg', 'efgh', 'fghi', 
                      'ghij', 'hijk', 'ijkl', 'jklm', 'klmn', 'lmno',
                      'mnop', 'nopq', 'opqr', 'pqrs', 'qrst', 'rstu',
                      'stuv', 'tuvw', 'uvwx', 'vwxy', 'wxyz']
    for seq in alpha_sequences:
        if seq in password_lower or seq[::-1] in password_lower:
            return True
    
    # Sequenze tastiera
    keyboard_sequences = ['qwerty', 'asdfgh', 'zxcvbn', 'qwertz', 'azerty']
    for seq in keyboard_sequences:
        if seq in password_lower:
            return True
    
    return False

def get_password_strength(password: str) -> dict:
    """
    Calcola la forza della password (0-100).
    
    Returns:
        {
            'score': int (0-100),
            'level': str ('Debole', 'Media', 'Forte', 'Molto Forte'),
            'feedback': list[str]
        }
    """
    score = 0
    feedback = []
    
    # Lunghezza (max 30 punti)
    if len(password) >= 8:
        score += 10
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10
    
    # Varietà caratteri (max 40 punti)
    if re.search(r'[a-z]', password):
        score += 10
    else:
        feedback.append("Aggiungi lettere minuscole")
    
    if re.search(r'[A-Z]', password):
        score += 10
    else:
        feedback.append("Aggiungi lettere maiuscole")
    
    if re.search(r'\d', password):
        score += 10
    else:
        feedback.append("Aggiungi numeri")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', password):
        score += 10
    else:
        feedback.append("Aggiungi caratteri speciali")
    
    # Complessità (max 30 punti)
    unique_chars = len(set(password))
    if unique_chars >= 8:
        score += 10
    if unique_chars >= 12:
        score += 10
    if not has_sequential_pattern(password):
        score += 10
    else:
        feedback.append("Evita sequenze semplici")
    
    # Determina livello
    if score < 40:
        level = 'Debole'
    elif score < 70:
        level = 'Media'
    elif score < 90:
        level = 'Forte'
    else:
        level = 'Molto Forte'
    
    return {
        'score': score,
        'level': level,
        'feedback': feedback
    }
