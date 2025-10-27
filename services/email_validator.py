"""
Email Validation Service
Validazione robusta delle email con regex RFC-compliant
"""

import re

def validate_email(email: str) -> tuple[bool, str]:
    """
    Valida formato email secondo RFC 5322 (versione semplificata).
    
    Args:
        email: Email da validare
        
    Returns:
        (is_valid, message): Tupla con esito validazione e messaggio errore
    """
    if not email:
        return False, "Email obbligatoria"
    
    email = email.strip().lower()
    
    if len(email) < 5:
        return False, "Email troppo corta"
    
    if len(email) > 254:
        return False, "Email troppo lunga (max 254 caratteri)"
    
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_regex, email):
        return False, "Formato email non valido"
    
    local_part = email.split('@')[0]
    domain_part = email.split('@')[1] if '@' in email else ''
    
    if len(local_part) > 64:
        return False, "Parte locale dell'email troppo lunga"
    
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, "Email non può iniziare o finire con un punto"
    
    if '..' in local_part:
        return False, "Email non può contenere punti consecutivi"
    
    domain_parts = domain_part.split('.')
    if any(len(part) == 0 for part in domain_parts):
        return False, "Dominio email non valido"
    
    blocked_domains = ['tempmail.com', 'throwaway.email', '10minutemail.com', 'guerrillamail.com']
    if domain_part.lower() in blocked_domains:
        return False, "Dominio email temporaneo non consentito"
    
    return True, "Email valida"


def normalize_email(email: str) -> str:
    """
    Normalizza email (lowercase, trim).
    
    Args:
        email: Email da normalizzare
        
    Returns:
        Email normalizzata
    """
    return email.strip().lower()
