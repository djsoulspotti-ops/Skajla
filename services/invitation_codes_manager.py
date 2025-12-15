"""
Gestione Codici Invito SKAJLA
Sistema per autorizzazione iscrizione studenti e professori
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from database.db_manager import db_manager


class InvitationCodesManager:
    """Gestisce la generazione e validazione dei codici invito per studenti e professori"""
    
    CODE_PREFIX_STUDENT = "STU"
    CODE_PREFIX_TEACHER = "DOC"
    CODE_LENGTH = 8
    DEFAULT_EXPIRY_DAYS = 30
    
    def __init__(self):
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Assicura che le tabelle esistano"""
        pass
    
    def _generate_code(self, role: str = 'studente') -> str:
        """Genera un codice univoco"""
        prefix = self.CODE_PREFIX_STUDENT if role == 'studente' else self.CODE_PREFIX_TEACHER
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(self.CODE_LENGTH))
        return f"{prefix}{random_part}"
    
    def _generate_temp_password(self, length: int = 12) -> str:
        """Genera una password temporanea sicura"""
        chars = string.ascii_letters + string.digits + "!@#$%"
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(length))
            if (any(c.isupper() for c in password) and
                any(c.islower() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%" for c in password)):
                return password
    
    def create_license_package(
        self,
        school_id: int,
        package_name: str,
        total_licenses: int,
        role: str = 'studente',
        created_by: int = None,
        expires_days: int = 365,
        notes: str = None
    ) -> Dict[str, Any]:
        """Crea un nuovo pacchetto licenze per una scuola"""
        expires_at = datetime.now() + timedelta(days=expires_days)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO license_packages 
                (school_id, package_name, total_licenses, role, created_by, expires_at, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (school_id, package_name, total_licenses, role, created_by, expires_at, notes))
            
            package_id = cursor.fetchone()[0]
            conn.commit()
            
            return {
                'success': True,
                'package_id': package_id,
                'package_name': package_name,
                'total_licenses': total_licenses,
                'role': role,
                'expires_at': expires_at.isoformat()
            }
    
    def generate_invitation_codes(
        self,
        school_id: int,
        count: int,
        role: str = 'studente',
        created_by: int = None,
        package_name: str = None,
        expires_days: int = None
    ) -> Dict[str, Any]:
        """Genera N codici invito per una scuola"""
        if expires_days is None:
            expires_days = self.DEFAULT_EXPIRY_DAYS
            
        expires_at = datetime.now() + timedelta(days=expires_days)
        generated_codes = []
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            for _ in range(count):
                code = self._generate_code(role)
                temp_password = self._generate_temp_password()
                
                for attempt in range(5):
                    try:
                        cursor.execute('''
                            INSERT INTO invitation_codes 
                            (code, school_id, role, temp_password, package_name, created_by, expires_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        ''', (code, school_id, role, temp_password, package_name, created_by, expires_at))
                        
                        code_id = cursor.fetchone()[0]
                        generated_codes.append({
                            'id': code_id,
                            'code': code,
                            'temp_password': temp_password,
                            'role': role
                        })
                        break
                    except Exception:
                        code = self._generate_code(role)
                        continue
            
            conn.commit()
            
            return {
                'success': True,
                'count': len(generated_codes),
                'codes': generated_codes,
                'expires_at': expires_at.isoformat()
            }
    
    def assign_code_to_email(
        self,
        code: str,
        email: str
    ) -> Dict[str, Any]:
        """Assegna un codice a un indirizzo email specifico"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE invitation_codes 
                SET email = %s, status = 'assigned'
                WHERE code = %s AND status = 'pending'
                RETURNING id, code, temp_password, role, school_id
            ''', (email.lower(), code.upper()))
            
            result = cursor.fetchone()
            
            if not result:
                return {'success': False, 'error': 'Codice non trovato o già utilizzato'}
            
            conn.commit()
            
            return {
                'success': True,
                'code_id': result[0],
                'code': result[1],
                'temp_password': result[2],
                'role': result[3],
                'school_id': result[4],
                'email': email
            }
    
    def validate_invitation_code(self, code: str) -> Dict[str, Any]:
        """Valida un codice invito e restituisce i dettagli"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ic.id, ic.code, ic.school_id, ic.role, ic.email, 
                       ic.temp_password, ic.status, ic.expires_at,
                       s.nome as school_name
                FROM invitation_codes ic
                JOIN scuole s ON ic.school_id = s.id
                WHERE ic.code = %s
            ''', (code.upper(),))
            
            result = cursor.fetchone()
            
            if not result:
                return {'valid': False, 'error': 'Codice non valido'}
            
            code_id, code_val, school_id, role, email, temp_pwd, status, expires_at, school_name = result
            
            if status == 'used':
                return {'valid': False, 'error': 'Codice già utilizzato'}
            
            if expires_at and datetime.now() > expires_at:
                return {'valid': False, 'error': 'Codice scaduto'}
            
            return {
                'valid': True,
                'code_id': code_id,
                'code': code_val,
                'school_id': school_id,
                'school_name': school_name,
                'role': role,
                'email': email,
                'temp_password': temp_pwd
            }
    
    def use_invitation_code(self, code: str, user_id: int) -> Dict[str, Any]:
        """Segna un codice come utilizzato dopo la registrazione"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE invitation_codes 
                SET status = 'used', used_by = %s, used_at = CURRENT_TIMESTAMP
                WHERE code = %s AND status IN ('pending', 'assigned')
                RETURNING id, school_id, role
            ''', (user_id, code.upper()))
            
            result = cursor.fetchone()
            
            if not result:
                return {'success': False, 'error': 'Codice non valido o già utilizzato'}
            
            cursor.execute('''
                UPDATE license_packages 
                SET used_licenses = used_licenses + 1
                WHERE school_id = %s AND role = %s
            ''', (result[1], result[2]))
            
            conn.commit()
            
            return {
                'success': True,
                'code_id': result[0],
                'school_id': result[1],
                'role': result[2]
            }
    
    def get_school_invitation_codes(
        self,
        school_id: int,
        status: str = None,
        role: str = None
    ) -> List[Dict[str, Any]]:
        """Ottiene tutti i codici invito di una scuola"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT id, code, role, email, status, created_at, 
                       used_at, expires_at, package_name
                FROM invitation_codes
                WHERE school_id = %s
            '''
            params = [school_id]
            
            if status:
                query += ' AND status = %s'
                params.append(status)
            
            if role:
                query += ' AND role = %s'
                params.append(role)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [{
                'id': row[0],
                'code': row[1],
                'role': row[2],
                'email': row[3],
                'status': row[4],
                'created_at': row[5].isoformat() if row[5] else None,
                'used_at': row[6].isoformat() if row[6] else None,
                'expires_at': row[7].isoformat() if row[7] else None,
                'package_name': row[8]
            } for row in rows]
    
    def get_school_license_stats(self, school_id: int) -> Dict[str, Any]:
        """Ottiene statistiche licenze per una scuola"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT role, 
                       SUM(total_licenses) as total,
                       SUM(used_licenses) as used
                FROM license_packages
                WHERE school_id = %s
                GROUP BY role
            ''', (school_id,))
            
            rows = cursor.fetchall()
            
            stats = {}
            for row in rows:
                stats[row[0]] = {
                    'total': row[1] or 0,
                    'used': row[2] or 0,
                    'available': (row[1] or 0) - (row[2] or 0)
                }
            
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM invitation_codes
                WHERE school_id = %s
                GROUP BY status
            ''', (school_id,))
            
            code_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                'licenses': stats,
                'codes': code_stats
            }
    
    def send_invitation_email(
        self,
        email: str,
        code: str,
        temp_password: str,
        school_name: str,
        role: str
    ) -> Dict[str, Any]:
        """Invia email con codice invito e password temporanea"""
        from services.email_service import email_service
        
        role_name = "Studente" if role == 'studente' else "Docente"
        
        subject = f"SKAJLA - Invito registrazione {role_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #003B73, #005AA7); padding: 30px; border-radius: 10px; text-align: center; color: white;">
                <h1 style="margin: 0;">SKAJLA</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Enterprise Education Platform</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                <h2 style="color: #003B73; margin-top: 0;">Benvenuto in SKAJLA!</h2>
                
                <p>Sei stato invitato a registrarti come <strong>{role_name}</strong> presso:</p>
                <p style="background: #e3f2fd; padding: 15px; border-radius: 8px; font-size: 18px; text-align: center;">
                    <strong>{school_name}</strong>
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #003B73;">
                    <h3 style="color: #003B73; margin-top: 0;">Le tue credenziali:</h3>
                    
                    <p><strong>Codice di registrazione:</strong></p>
                    <p style="background: #003B73; color: white; padding: 15px; border-radius: 8px; font-size: 24px; text-align: center; letter-spacing: 2px; font-family: monospace;">
                        {code}
                    </p>
                    
                    <p><strong>Password temporanea:</strong></p>
                    <p style="background: #f0f0f0; padding: 15px; border-radius: 8px; font-size: 18px; text-align: center; font-family: monospace;">
                        {temp_password}
                    </p>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; color: #856404;">
                        <strong>Importante:</strong> Al primo accesso ti verrà chiesto di impostare una nuova password personale.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://skajla.replit.app/register?code={code}" 
                       style="background: #003B73; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-size: 16px; display: inline-block;">
                        Registrati ora
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
                <p>&copy; 2025 SKAJLA - Enterprise Education Platform</p>
                <p>Questa email è stata inviata automaticamente. Non rispondere a questo messaggio.</p>
            </div>
        </body>
        </html>
        """
        
        try:
            result = email_service.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content
            )
            return {'success': True, 'message': 'Email inviata con successo'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


invitation_codes_manager = InvitationCodesManager()
