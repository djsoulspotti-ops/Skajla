"""
SKAILA - Validatori Input Centralizzati
Validazione e sanitizzazione input utente per sicurezza
"""

import re
from typing import Optional, List, Tuple
from html import escape

class InputValidator:
    """Validatore centralizzato per input utente"""
    
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    SCHOOL_CODE_REGEX = re.compile(r'^[A-Z0-9]{6,12}$')
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Valida email"""
        if not email or not isinstance(email, str):
            return False, "Email richiesta"
        
        email = email.strip().lower()
        
        if not InputValidator.EMAIL_REGEX.match(email):
            return False, "Formato email non valido"
        
        if len(email) > 254:
            return False, "Email troppo lunga"
        
        return True, None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Optional[str]]:
        """Valida password con requisiti sicurezza"""
        if not password or not isinstance(password, str):
            return False, "Password richiesta"
        
        if len(password) < 8:
            return False, "Password deve essere almeno 8 caratteri"
        
        if len(password) > 128:
            return False, "Password troppo lunga"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password deve contenere maiuscole, minuscole e numeri"
        
        return True, None
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str]]:
        """Valida username"""
        if not username or not isinstance(username, str):
            return False, "Username richiesto"
        
        username = username.strip()
        
        if not InputValidator.USERNAME_REGEX.match(username):
            return False, "Username può contenere solo lettere, numeri, - e _"
        
        if len(username) < 3:
            return False, "Username deve essere almeno 3 caratteri"
        
        if len(username) > 30:
            return False, "Username troppo lungo"
        
        return True, None
    
    @staticmethod
    def validate_school_code(code: str) -> Tuple[bool, Optional[str]]:
        """Valida codice scuola"""
        if not code or not isinstance(code, str):
            return False, "Codice scuola richiesto"
        
        code = code.strip().upper()
        
        if not InputValidator.SCHOOL_CODE_REGEX.match(code):
            return False, "Codice scuola non valido"
        
        return True, None
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitizza input HTML (previene XSS)"""
        if not text:
            return ""
        return escape(str(text))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizza nome file"""
        if not filename:
            return ""
        
        filename = str(filename).strip()
        
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        filename = re.sub(r'\.{2,}', '.', filename)
        
        if filename.startswith('.'):
            filename = filename[1:]
        
        return filename[:255]
    
    @staticmethod
    def validate_integer(value, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Tuple[bool, Optional[int]]:
        """Valida e converte a intero"""
        try:
            int_val = int(value)
            
            if min_val is not None and int_val < min_val:
                return False, None
            
            if max_val is not None and int_val > max_val:
                return False, None
            
            return True, int_val
        except (ValueError, TypeError):
            return False, None
    
    @staticmethod
    def validate_grade(grade) -> Tuple[bool, Optional[float]]:
        """Valida voto scolastico (1-10 scala italiana)"""
        try:
            grade_val = float(grade)
            
            if grade_val < 1 or grade_val > 10:
                return False, None
            
            grade_val = round(grade_val, 2)
            
            return True, grade_val
        except (ValueError, TypeError):
            return False, None
    
    @staticmethod
    def validate_subject(subject: str, allowed_subjects: List[str]) -> Tuple[bool, Optional[str]]:
        """Valida materia scolastica"""
        if not subject or not isinstance(subject, str):
            return False, None
        
        subject = subject.strip().lower()
        
        if subject not in allowed_subjects:
            return False, None
        
        return True, subject

class SQLInjectionProtector:
    """Protezione contro SQL injection"""
    
    DANGEROUS_PATTERNS = [
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)"
    ]
    
    @classmethod
    def is_safe(cls, input_str: str) -> bool:
        """Controlla se l'input contiene pattern SQL pericolosi"""
        if not input_str:
            return True
        
        input_upper = str(input_str).upper()
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                return False
        
        return True
    
    @classmethod
    def sanitize_for_like(cls, input_str: str) -> str:
        """Sanitizza input per query LIKE"""
        if not input_str:
            return ""
        
        sanitized = str(input_str).replace('%', '\\%').replace('_', '\\_')
        return sanitized

validator = InputValidator()
sql_protector = SQLInjectionProtector()
