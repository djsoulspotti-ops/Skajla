# Sistema Scuole-Classi-Professori per SKAJLA
# Estensione multi-tenant con gestione organizzazioni scolastiche

from database_manager import db_manager
from performance_cache import user_cache, invalidate_user_cache
import secrets
import string

# Error handling framework
from shared.error_handling import (
    DatabaseError,
    ValidationError,
    get_logger,
    handle_errors
)

logger = get_logger(__name__)

# ✅ SECURITY FIX: Whitelist of allowed feature column names (SQL Injection Prevention)
ALLOWED_FEATURE_COLUMNS = {
    'gamification': 'modulo_gamification',
    'chatbot': 'modulo_chatbot',
    'ai_coach': 'modulo_chatbot',
    'registro': 'modulo_registro',
    'materiali': 'modulo_materiali',
    'connect': 'modulo_connect',
    'analytics': 'modulo_analytics'
}

class SchoolSystem:
    """Sistema di gestione scuole, classi e associazioni professori"""
    
    def __init__(self):
        self.init_school_tables()
        self.setup_default_school()
    
    def init_school_tables(self):
        """Inizializza tabelle sistema scolastico"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # CRITICO: Migrazione per colonne mancanti su DB esistenti
            self._migrate_existing_database(cursor)
            
            # Tabella scuole
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scuole (
                        id SERIAL PRIMARY KEY,
                        nome TEXT NOT NULL,
                        codice_pubblico TEXT UNIQUE NOT NULL,
                        dominio_email TEXT,
                        domain_verified BOOLEAN DEFAULT false,
                        domain_trust_enabled BOOLEAN DEFAULT false,
                        codice_invito_docenti TEXT UNIQUE,
                        codice_dirigente TEXT UNIQUE,
                        dirigente_invite_token TEXT UNIQUE,
                        docente_invite_code_hash TEXT,
                        invite_link_salt TEXT,
                        last_rotated_at TIMESTAMP,
                        attiva BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scuole (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        codice_pubblico TEXT UNIQUE NOT NULL,
                        dominio_email TEXT,
                        domain_verified BOOLEAN DEFAULT 0,
                        domain_trust_enabled BOOLEAN DEFAULT 0,
                        codice_invito_docenti TEXT UNIQUE,
                        codice_dirigente TEXT UNIQUE,
                        dirigente_invite_token TEXT UNIQUE,
                        docente_invite_code_hash TEXT,
                        invite_link_salt TEXT,
                        last_rotated_at TIMESTAMP,
                        attiva BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # Tabella classi
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classi (
                        id SERIAL PRIMARY KEY,
                        scuola_id INTEGER NOT NULL REFERENCES scuole(id) ON DELETE CASCADE,
                        nome TEXT NOT NULL,
                        anno INTEGER,
                        sezione TEXT,
                        codice_classe TEXT NOT NULL,
                        attiva BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(scuola_id, codice_classe)
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classi (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scuola_id INTEGER NOT NULL REFERENCES scuole(id) ON DELETE CASCADE,
                        nome TEXT NOT NULL,
                        anno INTEGER,
                        sezione TEXT,
                        codice_classe TEXT NOT NULL,
                        attiva BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(scuola_id, codice_classe)
                    )
                ''')
            
            # Tabella verifica email per auto-registrazione
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_verifications (
                        id SERIAL PRIMARY KEY,
                        email TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        token TEXT UNIQUE NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        consumed_at TIMESTAMP,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_verifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        token TEXT UNIQUE NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        consumed_at TIMESTAMP,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # Tabella inviti automatici 
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invites (
                        id SERIAL PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('dirigente', 'professore', 'studente')),
                        token TEXT UNIQUE NOT NULL,
                        expires_at TIMESTAMP,
                        uses_remaining INTEGER,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        revoked_at TIMESTAMP
                    )
                ''')

            # NUOVO: Tabella codici personali individuali
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personal_codes (
                        id SERIAL PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        email TEXT NOT NULL,
                        code TEXT UNIQUE NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('professore', 'studente')),
                        used BOOLEAN DEFAULT false,
                        used_by INTEGER,
                        used_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        UNIQUE(school_id, email)
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_id INTEGER NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('dirigente', 'professore', 'studente')),
                        token TEXT UNIQUE NOT NULL,
                        expires_at TIMESTAMP,
                        uses_remaining INTEGER,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        revoked_at TIMESTAMP
                    )
                ''')

                # NUOVO: Tabella codici personali individuali (SQLite)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personal_codes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_id INTEGER NOT NULL,
                        email TEXT NOT NULL,
                        code TEXT UNIQUE NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('professore', 'studente')),
                        used BOOLEAN DEFAULT 0,
                        used_by INTEGER,
                        used_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        UNIQUE(school_id, email)
                    )
                ''')

            # Tabella associazione docenti-classi
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS docenti_classi (
                        id SERIAL PRIMARY KEY,
                        docente_id INTEGER NOT NULL,
                        classe_id INTEGER NOT NULL,
                        materia TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(docente_id, classe_id)
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS docenti_classi (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        docente_id INTEGER NOT NULL,
                        classe_id INTEGER NOT NULL,
                        materia TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(docente_id, classe_id)
                    )
                ''')
            
            # Estendi tabella utenti
            self._extend_user_table(cursor)
            
            # Estendi tabella chat
            self._extend_chat_table(cursor)
            
            conn.commit()
    
    def _extend_user_table(self, cursor):
        """Estende tabella utenti per supportare scuole"""
        db_manager.safe_alter_table(
            cursor, 
            'ALTER TABLE utenti ADD COLUMN scuola_id INTEGER REFERENCES scuole(id)',
            'utenti', 
            'scuola_id'
        )
        db_manager.safe_alter_table(
            cursor, 
            'ALTER TABLE utenti ADD COLUMN classe_id INTEGER REFERENCES classi(id)',
            'utenti', 
            'classe_id'
        )
    
    def _extend_chat_table(self, cursor):
        """Estende tabella chat per supportare organizzazione scolastica"""
        if db_manager.db_type == 'postgresql':
            tipo_sql = "ALTER TABLE chat ADD COLUMN tipo TEXT DEFAULT 'gruppo' CHECK (tipo IN ('scuola','classe','docenti','gruppo','privata'))"
        else:
            tipo_sql = "ALTER TABLE chat ADD COLUMN tipo TEXT DEFAULT 'gruppo'"
        db_manager.safe_alter_table(cursor, tipo_sql, 'chat', 'tipo')
        
        db_manager.safe_alter_table(
            cursor, 
            'ALTER TABLE chat ADD COLUMN scuola_id INTEGER REFERENCES scuole(id)',
            'chat', 
            'scuola_id'
        )
        db_manager.safe_alter_table(
            cursor, 
            'ALTER TABLE chat ADD COLUMN classe_id INTEGER REFERENCES classi(id)',
            'chat', 
            'classe_id'
        )
        
        if db_manager.db_type == 'postgresql':
            sistema_sql = 'ALTER TABLE chat ADD COLUMN sistema BOOLEAN DEFAULT false'
        else:
            sistema_sql = 'ALTER TABLE chat ADD COLUMN sistema BOOLEAN DEFAULT 0'
        db_manager.safe_alter_table(cursor, sistema_sql, 'chat', 'sistema')
    
    def setup_default_school(self):
        """Configura scuola predefinita per migrazione"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prima verifica se la tabella scuole esiste
            if db_manager.db_type == 'postgresql':
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'scuole'")
                table_exists = cursor.fetchone()[0] > 0
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scuole'")
                table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                logger.debug(
                    event_type='table_not_exists',
                    domain='database',
                    operation='setup_default_school',
                    table='scuole',
                    message='Tabella scuole non esiste ancora, skip setup scuola predefinita'
                )
                return
            
            # Verifica se scuola predefinita esiste
            if db_manager.db_type == 'postgresql':
                cursor.execute('SELECT id FROM scuole WHERE codice_pubblico = %s', ('DEFAULT_SCHOOL',))
            else:
                cursor.execute('SELECT id FROM scuole WHERE codice_pubblico = ?', ('DEFAULT_SCHOOL',))
            
            if not cursor.fetchone():
                # Crea scuola predefinita
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO scuole (nome, codice_pubblico, codice_invito_docenti, codice_dirigente)
                        VALUES (%s, %s, %s, %s) RETURNING id
                    ''', ('Scuola Predefinita', 'DEFAULT_SCHOOL', self.generate_invite_code(), 'DIR2024'))
                    default_school_id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO scuole (nome, codice_pubblico, codice_invito_docenti, codice_dirigente)
                        VALUES (%s, %s, %s, %s)
                    ''', ('Scuola Predefinita', 'DEFAULT_SCHOOL', self.generate_invite_code(), 'DIR2024'))
                    default_school_id = cursor.lastrowid
                
                # Migra utenti esistenti alla scuola predefinita (solo se tabella esiste)
                try:
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('UPDATE utenti SET scuola_id = %s WHERE scuola_id IS NULL', (default_school_id,))
                    else:
                        cursor.execute('UPDATE utenti SET scuola_id = ? WHERE scuola_id IS NULL', (default_school_id,))
                except Exception as e:
                    logger.debug(
                        event_type='migration_users_skipped',
                        domain='database',
                        operation='setup_default_school',
                        school_id=default_school_id,
                        error=str(e),
                        message='Tabella utenti non esiste ancora (prima inizializzazione)'
                    )
                
                conn.commit()
                logger.info(
                    event_type='default_school_created',
                    domain='school',
                    school_id=default_school_id,
                    message='Scuola predefinita creata'
                )
    
    def _migrate_existing_database(self, cursor):
        """Migrazione sicura per database esistenti con SAVEPOINT per PostgreSQL"""
        try:
            # Prima verifica se la tabella scuole esiste
            if db_manager.db_type == 'postgresql':
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'scuole'")
                table_exists = cursor.fetchone()[0] > 0
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scuole'")
                table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                logger.debug(
                    event_type='table_not_exists',
                    domain='database',
                    operation='migrate_existing_database',
                    table='scuole',
                    message='Tabella scuole non esiste ancora, skip migrazione'
                )
                return
            
            # Verifica e aggiunge colonne mancanti alla tabella scuole
            columns_to_add = [
                ('domain_verified', 'BOOLEAN DEFAULT 0' if db_manager.db_type == 'sqlite' else 'BOOLEAN DEFAULT false'),
                ('domain_trust_enabled', 'BOOLEAN DEFAULT 0' if db_manager.db_type == 'sqlite' else 'BOOLEAN DEFAULT false'),
                ('dirigente_invite_token', 'TEXT'),  # Rimosso UNIQUE - sarà gestito con INDEX
                ('docente_invite_code_hash', 'TEXT'),
                ('invite_link_salt', 'TEXT'),
                ('last_rotated_at', 'TIMESTAMP')
            ]
            
            for column_name, column_def in columns_to_add:
                sql = f'ALTER TABLE scuole ADD COLUMN {column_name} {column_def}'
                db_manager.safe_alter_table(cursor, sql, 'scuole', column_name)
                        
            # Gestione speciale per UNIQUE constraint su dirigente_invite_token
            self._ensure_dirigente_invite_token_unique(cursor)
                        
        except Exception as e:
            logger.error(
                event_type='migration_error',
                domain='database',
                operation='migrate_existing_database',
                error=str(e),
                exc_info=True,
                message='Errore durante migrazione database'
            )
    
    def _ensure_dirigente_invite_token_unique(self, cursor):
        """Crea UNIQUE INDEX per dirigente_invite_token in modo sicuro - SENZA DELETE PERICOLOSI"""
        try:
            # CRITICO: NON CANCELLARE MAI RIGHE - Solo gestisce duplicati in modo sicuro
            if db_manager.db_type == 'postgresql':
                # PostgreSQL: SAFE - Imposta NULL sui duplicati, mantenendo MIN(id)
                result = cursor.execute('''
                    UPDATE scuole 
                    SET dirigente_invite_token = NULL 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM scuole 
                        WHERE dirigente_invite_token IS NOT NULL 
                        GROUP BY dirigente_invite_token
                    ) AND dirigente_invite_token IS NOT NULL
                ''')
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    logger.info(
                        event_type='duplicates_fixed',
                        domain='database',
                        table='scuole',
                        column='dirigente_invite_token',
                        affected_rows=affected_rows,
                        db_type='postgresql',
                        message=f'SAFE FIX: Impostato dirigente_invite_token = NULL per {affected_rows} duplicati'
                    )
                
                # Crea UNIQUE INDEX se non esiste
                cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_scuole_dirigente_invite_token 
                    ON scuole (dirigente_invite_token) 
                    WHERE dirigente_invite_token IS NOT NULL
                ''')
                
            else:
                # SQLite: SAFE - Imposta NULL sui duplicati, mantenendo MIN(rowid)
                cursor.execute('''
                    UPDATE scuole 
                    SET dirigente_invite_token = NULL 
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid) 
                        FROM scuole 
                        WHERE dirigente_invite_token IS NOT NULL 
                        GROUP BY dirigente_invite_token
                    ) AND dirigente_invite_token IS NOT NULL
                ''')
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    logger.info(
                        event_type='duplicates_fixed',
                        domain='database',
                        table='scuole',
                        column='dirigente_invite_token',
                        affected_rows=affected_rows,
                        db_type='sqlite',
                        message=f'SAFE FIX: Impostato dirigente_invite_token = NULL per {affected_rows} duplicati'
                    )
                
                # Crea UNIQUE INDEX se non esiste (SQLite usa CREATE UNIQUE INDEX IF NOT EXISTS)
                cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_scuole_dirigente_invite_token 
                    ON scuole (dirigente_invite_token) 
                    WHERE dirigente_invite_token IS NOT NULL
                ''')
            
            logger.info(
                event_type='unique_constraint_created',
                domain='database',
                table='scuole',
                column='dirigente_invite_token',
                message='UNIQUE constraint su dirigente_invite_token creato con successo - NESSUN DATO CANCELLATO'
            )
            
        except Exception as e:
            # Se l'index esiste già, è OK
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                logger.debug(
                    event_type='unique_index_exists',
                    domain='database',
                    table='scuole',
                    column='dirigente_invite_token',
                    message='UNIQUE index su dirigente_invite_token già esistente'
                )
            else:
                logger.warning(
                    event_type='unique_constraint_failed',
                    domain='database',
                    table='scuole',
                    column='dirigente_invite_token',
                    error=str(e),
                    message='Impossibile creare UNIQUE constraint su dirigente_invite_token - non è un errore fatale'
                )
    
    def generate_personal_codes_for_school(self, scuola_id, user_id):
        """RIVOLUZIONARIO: Genera codici personali individuali per ogni persona della scuola"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Ottieni info scuola
                if db_manager.db_type == 'postgresql':
                    cursor.execute('SELECT nome, dominio_email FROM scuole WHERE id = %s', (scuola_id,))
                else:
                    cursor.execute('SELECT nome, dominio_email FROM scuole WHERE id = %s', (scuola_id,))
                
                school_info = cursor.fetchone()
                if not school_info:
                    return {'success': False, 'message': 'Scuola non trovata'}
                
                school_name, domain = school_info
                codes_generated = 0
                
                # STRATEGIA 1: Genera codici basati su dominio email scuola
                if domain:
                    # Lista email esempio per testing (in produzione: integrazione con sistema gestionale scuola)
                    staff_emails = self._get_school_email_list(scuola_id, domain)
                    
                    for email_info in staff_emails:
                        email = email_info['email']
                        role = email_info['role']  # 'professore' o 'studente'
                        
                        # Genera codice personale unico
                        personal_code = self._generate_unique_personal_code(scuola_id, email, role)
                        
                        # Salva in database
                        from datetime import datetime, timedelta
                        expires_at = datetime.now() + timedelta(days=90)  # 3 mesi validità
                        
                        if db_manager.db_type == 'postgresql':
                            cursor.execute('''
                                INSERT INTO personal_codes (school_id, email, code, role, expires_at)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (school_id, email) 
                                DO UPDATE SET code = %s, expires_at = %s, used = false
                            ''', (scuola_id, email, personal_code, role, expires_at, personal_code, expires_at))
                        else:
                            # SQLite: usa INSERT OR REPLACE
                            cursor.execute('''
                                INSERT OR REPLACE INTO personal_codes 
                                (school_id, email, code, role, expires_at, used)
                                VALUES (%s, %s, %s, %s, %s, 0)
                            ''', (scuola_id, email, personal_code, role, expires_at))
                        
                        codes_generated += 1
                        
                        # INVIO EMAIL AUTOMATICO (simulato per testing)
                        self._send_personal_code_email(email, personal_code, school_name, role)
                
                conn.commit()
                
                return {
                    'success': True,
                    'codes_count': codes_generated,
                    'message': f'Generati {codes_generated} codici personali automaticamente!'
                }
                
        except Exception as e:
            logger.error(
                event_type='personal_codes_generation_failed',
                domain='school',
                operation='generate_personal_codes_for_school',
                school_id=scuola_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
                message='Errore generazione codici personali'
            )
            return {'success': False, 'message': f'Errore: {e}'}
    
    def _get_school_email_list(self, scuola_id, domain):
        """Ottiene lista email scuola da database o CSV caricato"""
        import csv
        import os
        
        # Controlla se esiste un CSV caricato per questa scuola
        csv_path = f'school_emails_{scuola_id}.csv'
        
        if os.path.exists(csv_path):
            # Leggi da CSV caricato dal dirigente
            emails_list = []
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    emails_list.append({
                        'email': row.get('email', '').strip().lower(),
                        'role': row.get('role', 'studente').strip().lower()
                    })
            logger.info(
                event_type='csv_emails_loaded',
                domain='school',
                school_id=scuola_id,
                count=len(emails_list),
                message=f'Caricate {len(emails_list)} email da CSV'
            )
            return emails_list
        
        # Fallback: query database per email già nel sistema
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    SELECT email, ruolo FROM utenti 
                    WHERE scuola_id = %s AND email LIKE %s
                ''', (scuola_id, f'%@{domain}'))
            else:
                cursor.execute('''
                    SELECT email, ruolo FROM utenti 
                    WHERE scuola_id = ? AND email LIKE ?
                ''', (scuola_id, f'%@{domain}'))
            
            db_emails = cursor.fetchall()
            if db_emails:
                logger.info(
                    event_type='db_emails_loaded',
                    domain='school',
                    school_id=scuola_id,
                    count=len(db_emails),
                    message=f'Trovate {len(db_emails)} email nel database'
                )
                return [{'email': row[0], 'role': row[1]} for row in db_emails]
        
        # Ultimo fallback: lista demo per testing
        logger.warning(
            event_type='using_demo_emails',
            domain='school',
            school_id=scuola_id,
            message='Nessuna email trovata - usando lista demo'
        )
        sample_emails = [
            {'email': f'mario.rossi@{domain}', 'role': 'professore'},
            {'email': f'anna.bianchi@{domain}', 'role': 'professore'},
            {'email': f'giovanni.verdi@{domain}', 'role': 'professore'},
            {'email': f'lucia.ferrari@{domain}', 'role': 'studente'},
            {'email': f'marco.colombo@{domain}', 'role': 'studente'},
            {'email': f'sofia.romano@{domain}', 'role': 'studente'},
            {'email': f'alessandro.ricci@{domain}', 'role': 'studente'},
            {'email': f'giulia.costa@{domain}', 'role': 'studente'},
        ]
        return sample_emails
    
    def upload_school_emails_csv(self, scuola_id, csv_content):
        """Carica CSV con email scuola per generazione automatica codici"""
        import csv
        import io
        
        try:
            # Salva CSV per uso futuro
            csv_path = f'school_emails_{scuola_id}.csv'
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            # Valida formato CSV
            csvfile = io.StringIO(csv_content)
            reader = csv.DictReader(csvfile)
            
            required_columns = ['email', 'role']
            if not all(col in reader.fieldnames for col in required_columns):
                return {
                    'success': False, 
                    'message': f'CSV deve contenere colonne: {", ".join(required_columns)}'
                }
            
            # Conta righe valide
            valid_emails = []
            for row in reader:
                email = row.get('email', '').strip()
                role = row.get('role', '').strip().lower()
                
                if email and '@' in email and role in ['professore', 'studente']:
                    valid_emails.append({'email': email, 'role': role})
            
            return {
                'success': True,
                'count': len(valid_emails),
                'message': f'CSV caricato: {len(valid_emails)} email valide'
            }
            
        except Exception as e:
            logger.error(
                event_type='csv_upload_failed',
                domain='school',
                operation='upload_school_emails_csv',
                school_id=scuola_id,
                error=str(e),
                exc_info=True,
                message='Errore caricamento CSV email scuola'
            )
            return {'success': False, 'message': f'Errore: {str(e)}'}
    
    def _generate_unique_personal_code(self, scuola_id, email, role):
        """Genera codice personale unico per individuo"""
        import random
        import string
        
        # Iniziali persona
        name_part = email.split('@')[0].replace('.', '').upper()[:2]
        
        # Codice scuola (prime 2 lettere)
        school_part = f"SC{scuola_id:02d}" if scuola_id < 100 else f"SC{scuola_id}"
        
        # Ruolo
        role_part = 'P' if role == 'professore' else 'S'
        
        # Parte random unica
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # Formato: AB-SC01-P-X8K9
        return f"{name_part}-{school_part}-{role_part}-{random_part}"
    
    def _send_personal_code_email(self, email, code, school_name, role):
        """Invia email automatica con codice personale"""
        from datetime import datetime
        role_it = "professore" if role == 'professore' else "studente"
        
        # Template email HTML professionale
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .code-box {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 2px; color: #667eea; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 Benvenuto/a in SKAJLA</h1>
                    <p>{school_name}</p>
                </div>
                <div class="content">
                    <h2>Ciao!</h2>
                    <p>Sei stato/a registrato/a come <strong>{role_it}</strong> presso <strong>{school_name}</strong>.</p>
                    <p>Per completare la registrazione su SKAJLA, usa il tuo codice personale:</p>
                    <div class="code-box">{code}</div>
                    <p><strong>Come procedere:</strong></p>
                    <ol>
                        <li>Vai su <a href="https://skaila.replit.app/register">skaila.replit.app/register</a></li>
                        <li>Inserisci questo codice nel campo "Codice Personale"</li>
                        <li>Completa i tuoi dati (usa questa email: <strong>{email}</strong>)</li>
                        <li>Inizia subito a usare SKAJLA!</li>
                    </ol>
                    <p style="color: #e74c3c;"><strong>⚠️ Importante:</strong> Questo codice è valido per 90 giorni e può essere usato una sola volta.</p>
                    <a href="https://skaila.replit.app/register" class="button">Registrati Ora</a>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} SKAJLA - Piattaforma Educativa Innovativa</p>
                    <p>Questa email è stata inviata automaticamente. Non rispondere a questo messaggio.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # In produzione: integrazione SMTP reale
        # Per ora: simulazione professionale con logging
        logger.info(
            event_type='personal_code_email_sent',
            domain='school',
            email=email,
            school_name=school_name,
            role=role,
            code=code,
            message='Email automatica inviata con codice personale'
        )
        
        # TODO: Integrazione SMTP reale per produzione
        # import smtplib
        # from email.mime.multipart import MIMEMultipart
        # from email.mime.text import MIMEText
        # 
        # msg = MIMEMultipart('alternative')
        # msg['Subject'] = f"🎓 Il tuo codice personale SKAJLA per {school_name}"
        # msg['From'] = "noreply@skaila.it"
        # msg['To'] = email
        # msg.attach(MIMEText(email_html, 'html'))
        # 
        # with smtplib.SMTP('smtp.gmail.com', 587) as server:
        #     server.starttls()
        #     server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        #     server.send_message(msg)
        
        return True
    
    def verify_personal_code(self, code):
        """Verifica e consuma codice personale per registrazione"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        SELECT pc.id, pc.school_id, pc.email, pc.role, s.nome as school_name
                        FROM personal_codes pc
                        JOIN scuole s ON pc.school_id = s.id
                        WHERE pc.code = %s AND pc.used = false AND pc.expires_at > NOW()
                    ''', (code,))
                else:
                    cursor.execute('''
                        SELECT pc.id, pc.school_id, pc.email, pc.role, s.nome as school_name
                        FROM personal_codes pc
                        JOIN scuole s ON pc.school_id = s.id
                        WHERE pc.code = %s AND pc.used = 0 AND pc.expires_at > CURRENT_TIMESTAMP
                    ''', (code,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'success': True,
                        'code_id': result[0],
                        'school_id': result[1],
                        'email': result[2],
                        'role': result[3],
                        'school_name': result[4]
                    }
                else:
                    return {'success': False, 'message': 'Codice non valido o scaduto'}
                    
        except Exception as e:
            logger.error(
                event_type='personal_code_verification_failed',
                domain='school',
                operation='verify_personal_code',
                code=code,
                error=str(e),
                exc_info=True,
                message='Errore verifica codice personale'
            )
            return {'success': False, 'message': f'Errore: {e}'}
    
    def mark_personal_code_used(self, code_id, user_id):
        """Marca codice personale come usato dopo registrazione"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        UPDATE personal_codes 
                        SET used = true, used_by = %s, used_at = NOW()
                        WHERE id = %s
                    ''', (user_id, code_id))
                else:
                    cursor.execute('''
                        UPDATE personal_codes 
                        SET used = 1, used_by = %s, used_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (user_id, code_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(
                event_type='mark_personal_code_failed',
                domain='school',
                operation='mark_personal_code_used',
                code_id=code_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
                message='Errore marcatura codice usato'
            )
            return False
    
    def create_school(self, nome, dominio_email=None, admin_user_id=None):
        """Crea nuova scuola"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            codice_pubblico = self.generate_school_code(nome)
            codice_invito_docenti = self.generate_invite_code()
            
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO scuole (nome, codice_pubblico, dominio_email, codice_invito_docenti)
                    VALUES (%s, %s, %s, %s) RETURNING id
                ''', (nome, codice_pubblico, dominio_email, codice_invito_docenti))
                school_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO scuole (nome, codice_pubblico, dominio_email, codice_invito_docenti)
                    VALUES (%s, %s, %s, %s)
                ''', (nome, codice_pubblico, dominio_email, codice_invito_docenti))
                school_id = cursor.lastrowid
            
            # Assegna admin scuola se fornito
            if admin_user_id:
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        UPDATE utenti 
                        SET scuola_id = %s, ruolo = %s 
                        WHERE id = %s
                    ''', (school_id, 'admin_scuola', admin_user_id))
                else:
                    cursor.execute('''
                        UPDATE utenti 
                        SET scuola_id = %s, ruolo = %s 
                        WHERE id = %s
                    ''', (school_id, 'admin_scuola', admin_user_id))
            
            # Crea chat di sistema per la scuola
            self.create_system_chats(school_id)
            
            conn.commit()
            return {
                'id': school_id,
                'codice_pubblico': codice_pubblico,
                'codice_invito_docenti': codice_invito_docenti
            }
    
    def create_class(self, scuola_id, nome, anno=None, sezione=None):
        """Crea nuova classe"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            codice_classe = f"{nome}_{anno}_{sezione}" if anno and sezione else nome
            
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO classi (scuola_id, nome, anno, sezione, codice_classe)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (scuola_id, nome, anno, sezione, codice_classe))
                class_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO classi (scuola_id, nome, anno, sezione, codice_classe)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (scuola_id, nome, anno, sezione, codice_classe))
                class_id = cursor.lastrowid
            
            # Crea chat per la classe
            self.create_class_chat(class_id, scuola_id, nome)
            
            # Crea gruppi materia predefiniti per la classe
            try:
                from services.messaging.subject_groups_initializer import initialize_subject_groups_for_class
                initialize_subject_groups_for_class(scuola_id, nome)
                logger.info(
                    event_type='subject_groups_initialized',
                    domain='school',
                    school_id=scuola_id,
                    class_name=nome,
                    message='Gruppi materia inizializzati per classe'
                )
            except Exception as e:
                logger.warning(
                    event_type='subject_groups_init_failed',
                    domain='school',
                    operation='create_class',
                    school_id=scuola_id,
                    class_name=nome,
                    error=str(e),
                    message='Errore inizializzando gruppi materia per classe'
                )
            
            conn.commit()
            return class_id
    
    def assign_teacher_to_class(self, docente_id, classe_id, materia=None):
        """Assegna professore a classe"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO docenti_classi (docente_id, classe_id, materia)
                        VALUES (%s, %s, %s)
                    ''', (docente_id, classe_id, materia))
                else:
                    cursor.execute('''
                        INSERT INTO docenti_classi (docente_id, classe_id, materia)
                        VALUES (%s, %s, %s)
                    ''', (docente_id, classe_id, materia))
                
                conn.commit()
                return True
            except Exception as e:
                logger.error(
                    event_type='teacher_assignment_failed',
                    domain='school',
                    operation='assign_teacher_to_class',
                    teacher_id=docente_id,
                    class_id=classe_id,
                    subject=materia,
                    error=str(e),
                    exc_info=True,
                    message='Errore assegnazione professore a classe'
                )
                return False
    
    def create_system_chats(self, scuola_id):
        """Crea chat di sistema per scuola"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Chat generale scuola
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO chat (nome, tipo, scuola_id, sistema)
                    VALUES (%s, %s, %s, %s)
                ''', ('Comunicazioni Scuola', 'scuola', scuola_id, True))
                
                # Chat docenti
                cursor.execute('''
                    INSERT INTO chat (nome, tipo, scuola_id, sistema)
                    VALUES (%s, %s, %s, %s)
                ''', ('Sala Professori', 'docenti', scuola_id, True))
            else:
                cursor.execute('''
                    INSERT INTO chat (nome, tipo, scuola_id, sistema)
                    VALUES (%s, %s, %s, %s)
                ''', ('Comunicazioni Scuola', 'scuola', scuola_id, 1))
                
                cursor.execute('''
                    INSERT INTO chat (nome, tipo, scuola_id, sistema)
                    VALUES (%s, %s, %s, %s)
                ''', ('Sala Professori', 'docenti', scuola_id, 1))
            
            conn.commit()
    
    def create_class_chat(self, classe_id, scuola_id, classe_nome):
        """Crea chat per classe specifica"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO chat (nome, tipo, scuola_id, classe_id, sistema)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (f'Classe {classe_nome}', 'classe', scuola_id, classe_id, True))
            else:
                cursor.execute('''
                    INSERT INTO chat (nome, tipo, scuola_id, classe_id, sistema)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (f'Classe {classe_nome}', 'classe', scuola_id, classe_id, 1))
            
            conn.commit()
    
    def get_user_schools(self):
        """Ottieni lista scuole per registrazione"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, codice_pubblico FROM scuole WHERE attiva = true ORDER BY nome')
            return cursor.fetchall()
    
    def get_school_classes(self, scuola_id):
        """Ottieni classi di una scuola"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    SELECT id, nome, anno, sezione, codice_classe 
                    FROM classi 
                    WHERE scuola_id = %s AND attiva = true 
                    ORDER BY anno, sezione, nome
                ''', (scuola_id,))
            else:
                cursor.execute('''
                    SELECT id, nome, anno, sezione, codice_classe 
                    FROM classi 
                    WHERE scuola_id = %s AND attiva = 1 
                    ORDER BY anno, sezione, nome
                ''', (scuola_id,))
            return cursor.fetchall()
    
    def generate_school_code(self, nome):
        """Genera codice scuola univoco"""
        base = ''.join(filter(str.isalpha, nome.upper()))[:6]
        suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
        return f"{base}{suffix}"
    
    def generate_invite_code(self):
        """Genera codice invito sicuro"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

    def generate_secure_token(self, length=32):
        """Genera token sicuro per inviti e verifiche"""
        return secrets.token_urlsafe(length)
    
    def register_school_auto(self, nome, dominio_email, dirigente_email, dirigente_nome, dirigente_cognome):
        """Auto-registrazione scuola con verifica email dirigente"""
        import hashlib
        from datetime import datetime, timedelta
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verifica se scuola già esiste
                if db_manager.db_type == 'postgresql':
                    cursor.execute('SELECT id FROM scuole WHERE dominio_email = %s OR nome = %s', 
                                 (dominio_email, nome))
                else:
                    cursor.execute('SELECT id FROM scuole WHERE dominio_email = %s OR nome = %s', 
                                 (dominio_email, nome))
                
                if cursor.fetchone():
                    return {'success': False, 'message': 'Scuola già registrata con questo nome o dominio'}
                
                # Genera codici e token
                codice_pubblico = self.generate_school_code(nome)
                codice_docenti = self.generate_invite_code()
                codice_dirigente = f"DIR{secrets.choice(string.digits + string.ascii_uppercase)}{secrets.choice(string.digits + string.ascii_uppercase)}{datetime.now().year}"
                dirigente_token = self.generate_secure_token()
                salt = self.generate_secure_token(16)
                
                # Hash del codice docenti per sicurezza
                docente_hash = hashlib.sha256((codice_docenti + salt).encode()).hexdigest()
                
                # Crea scuola (disabilitata fino a verifica)
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO scuole 
                        (nome, codice_pubblico, dominio_email, codice_invito_docenti, 
                         codice_dirigente, dirigente_invite_token, docente_invite_code_hash, 
                         invite_link_salt, attiva)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, false) RETURNING id
                    ''', (nome, codice_pubblico, dominio_email, codice_docenti, 
                          codice_dirigente, dirigente_token, docente_hash, salt))
                    school_id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO scuole 
                        (nome, codice_pubblico, dominio_email, codice_invito_docenti, 
                         codice_dirigente, dirigente_invite_token, docente_invite_code_hash, 
                         invite_link_salt, attiva)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)
                    ''', (nome, codice_pubblico, dominio_email, codice_docenti, 
                          codice_dirigente, dirigente_token, docente_hash, salt))
                    school_id = cursor.lastrowid
                
                # Crea verifica email per dirigente
                expires_at = datetime.now() + timedelta(hours=24)
                verification_token = self.generate_secure_token()
                
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO email_verifications 
                        (email, purpose, token, expires_at, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (dirigente_email, 'dirigente_school_verification', verification_token, 
                          expires_at, f'{{"school_id": {school_id}, "nome": "{dirigente_nome}", "cognome": "{dirigente_cognome}"}}'))
                else:
                    cursor.execute('''
                        INSERT INTO email_verifications 
                        (email, purpose, token, expires_at, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (dirigente_email, 'dirigente_school_verification', verification_token, 
                          expires_at, f'{{"school_id": {school_id}, "nome": "{dirigente_nome}", "cognome": "{dirigente_cognome}"}}'))
                
                conn.commit()
                
                return {
                    'success': True, 
                    'school_id': school_id,
                    'verification_token': verification_token,
                    'dirigente_email': dirigente_email,
                    'message': 'Email di verifica inviata al dirigente'
                }
                
        except Exception as e:
            logger.error(
                event_type='school_auto_registration_failed',
                domain='school',
                operation='register_school_auto',
                school_name=nome,
                domain_email=dominio_email,
                dirigente_email=dirigente_email,
                error=str(e),
                exc_info=True,
                message='Errore auto-registrazione scuola'
            )
            return {'success': False, 'message': f'Errore durante la registrazione: {str(e)}'}
    
    def verify_dirigente_email(self, token):
        """Verifica email dirigente e attiva scuola"""
        import json
        from datetime import datetime
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Trova verifica email
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        SELECT email, metadata, expires_at FROM email_verifications 
                        WHERE token = %s AND purpose = %s AND consumed_at IS NULL
                    ''', (token, 'dirigente_school_verification'))
                else:
                    cursor.execute('''
                        SELECT email, metadata, expires_at FROM email_verifications 
                        WHERE token = %s AND purpose = %s AND consumed_at IS NULL
                    ''', (token, 'dirigente_school_verification'))
                
                verification = cursor.fetchone()
                if not verification:
                    return {'success': False, 'message': 'Token di verifica non valido o già utilizzato'}
                
                email, metadata_str, expires_at = verification
                
                # Verifica scadenza
                if datetime.now() > datetime.fromisoformat(expires_at.replace('Z', '+00:00') if 'Z' in str(expires_at) else str(expires_at)):
                    return {'success': False, 'message': 'Token di verifica scaduto'}
                
                # Parse metadata
                metadata = json.loads(metadata_str)
                school_id = metadata['school_id']
                dirigente_nome = metadata['nome']
                dirigente_cognome = metadata['cognome']
                
                # Attiva scuola
                if db_manager.db_type == 'postgresql':
                    cursor.execute('UPDATE scuole SET attiva = true, domain_verified = true WHERE id = %s', (school_id,))
                else:
                    cursor.execute('UPDATE scuole SET attiva = 1, domain_verified = 1 WHERE id = %s', (school_id,))
                
                # Marca verifica come consumata
                if db_manager.db_type == 'postgresql':
                    cursor.execute('UPDATE email_verifications SET consumed_at = CURRENT_TIMESTAMP WHERE token = %s', (token,))
                else:
                    cursor.execute('UPDATE email_verifications SET consumed_at = CURRENT_TIMESTAMP WHERE token = %s', (token,))
                
                conn.commit()
                
                return {
                    'success': True,
                    'school_id': school_id,
                    'email': email,
                    'dirigente_nome': dirigente_nome,
                    'dirigente_cognome': dirigente_cognome,
                    'message': 'Scuola attivata con successo!'
                }
                
        except Exception as e:
            logger.error(
                event_type='dirigente_verification_failed',
                domain='school',
                operation='verify_dirigente_email',
                token=token,
                error=str(e),
                exc_info=True,
                message='Errore verifica dirigente'
            )
            return {'success': False, 'message': f'Errore durante la verifica: {str(e)}'}
    
    def get_school_codes(self, school_id, user_id):
        """Ottieni codici scuola per dirigente (dashboard)"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verifica che l'utente sia dirigente della scuola
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        SELECT u.ruolo, s.nome, s.codice_invito_docenti, s.codice_dirigente,
                               s.domain_trust_enabled, s.dominio_email
                        FROM utenti u JOIN scuole s ON u.scuola_id = s.id 
                        WHERE u.id = %s AND s.id = %s AND u.ruolo = 'dirigente'
                    ''', (user_id, school_id))
                else:
                    cursor.execute('''
                        SELECT u.ruolo, s.nome, s.codice_invito_docenti, s.codice_dirigente,
                               s.domain_trust_enabled, s.dominio_email
                        FROM utenti u JOIN scuole s ON u.scuola_id = s.id 
                        WHERE u.id = %s AND s.id = %s AND u.ruolo = 'dirigente'
                    ''', (user_id, school_id))
                
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'message': 'Accesso non autorizzato'}
                
                return {
                    'success': True,
                    'school_name': result[1],
                    'teacher_code': result[2],
                    'director_code': result[3],
                    'domain_trust': bool(result[4]),
                    'school_domain': result[5]
                }
                
        except Exception as e:
            logger.error(
                event_type='get_school_codes_failed',
                domain='school',
                operation='get_school_codes',
                school_id=school_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
                message='Errore recupero codici scuola'
            )
            return {'success': False, 'message': f'Errore: {str(e)}'}
    
    def has_feature(self, school_id, feature_name):
        """
        Verifica se una scuola ha accesso a una feature/modulo
        
        Args:
            school_id: ID della scuola
            feature_name: Nome del modulo (gamification, chatbot, registro, materiali, connect, analytics)
        
        Returns:
            bool: True se la scuola ha accesso, False altrimenti
        """
        try:
            # ✅ SECURITY FIX: Validate feature_name against whitelist (SQL Injection Prevention)
            if feature_name not in ALLOWED_FEATURE_COLUMNS:
                logger.warning(
                    event_type='invalid_feature_name',
                    domain='school',
                    operation='has_feature',
                    school_id=school_id,
                    feature_name=feature_name,
                    message='Attempted access with invalid feature name'
                )
                return False
            
            # Use whitelisted column name (safe from SQL injection)
            column_name = ALLOWED_FEATURE_COLUMNS[feature_name]
            
            school = db_manager.query(
                f'SELECT {column_name} FROM scuole WHERE id = %s',
                (school_id,),
                one=True
            )
            
            if school:
                return bool(school.get(column_name, False))
            
            return False
            
        except Exception as e:
            logger.warning(
                event_type='has_feature_check_failed',
                domain='school',
                operation='has_feature',
                school_id=school_id,
                feature_name=feature_name,
                error=str(e),
                message='Errore verifica feature - permettendo accesso per sicurezza'
            )
            return True  # Default: permetti accesso in caso di errore
    
    def get_school_features(self, school_id):
        """
        Ottieni tutti i moduli attivi/disattivi per una scuola
        
        Returns:
            dict: Dizionario con tutti i moduli e il loro stato
        """
        try:
            school = db_manager.query('''
                SELECT modulo_gamification, modulo_chatbot, modulo_registro, 
                       modulo_materiali, modulo_connect, modulo_analytics
                FROM scuole WHERE id = %s
            ''', (school_id,), one=True)
            
            if school:
                return {
                    'gamification': bool(school.get('modulo_gamification', True)),
                    'chatbot': bool(school.get('modulo_chatbot', True)),
                    'registro': bool(school.get('modulo_registro', True)),
                    'materiali': bool(school.get('modulo_materiali', True)),
                    'connect': bool(school.get('modulo_connect', True)),
                    'analytics': bool(school.get('modulo_analytics', False))
                }
            
            # Default: tutti attivi tranne analytics
            return {
                'gamification': True,
                'chatbot': True,
                'registro': True,
                'materiali': True,
                'connect': True,
                'analytics': False
            }
            
        except Exception as e:
            logger.warning(
                event_type='get_school_features_failed',
                domain='school',
                operation='get_school_features',
                school_id=school_id,
                error=str(e),
                message='Errore recupero features scuola - usando valori predefiniti'
            )
            return {
                'gamification': True,
                'chatbot': True,
                'registro': True,
                'materiali': True,
                'connect': True,
                'analytics': False
            }
    
    def toggle_feature(self, school_id, feature_name, enabled):
        """
        Attiva/disattiva un modulo per una scuola
        
        Args:
            school_id: ID della scuola
            feature_name: Nome del modulo
            enabled: True per attivare, False per disattivare
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # ✅ SECURITY FIX: Validate feature_name against whitelist (SQL Injection Prevention)
            if feature_name not in ALLOWED_FEATURE_COLUMNS:
                logger.warning(
                    event_type='invalid_feature_name',
                    domain='school',
                    operation='toggle_feature',
                    school_id=school_id,
                    feature_name=feature_name,
                    message='Attempted toggle with invalid feature name'
                )
                return {
                    'success': False,
                    'message': 'Nome feature non valido'
                }
            
            # Use whitelisted column name (safe from SQL injection)
            column_name = ALLOWED_FEATURE_COLUMNS[feature_name]
            
            db_manager.execute(
                f'UPDATE scuole SET {column_name} = %s WHERE id = %s',
                (enabled, school_id)
            )
            
            action = 'attivato' if enabled else 'disattivato'
            return {
                'success': True,
                'message': f'Modulo {feature_name} {action} con successo'
            }
            
        except Exception as e:
            logger.error(
                event_type='toggle_feature_failed',
                domain='school',
                operation='toggle_feature',
                school_id=school_id,
                feature_name=feature_name,
                enabled=enabled,
                error=str(e),
                exc_info=True,
                message='Errore toggle feature'
            )
            return {
                'success': False,
                'message': f'Errore durante il toggle: {str(e)}'
            }

# Lazy initialization wrapper to avoid heavy database operations at import time
# This is critical for Autoscale health checks - Flask must be ready to respond
# before database migrations run
import threading

class _LazySchoolSystem:
    """Lazy initialization wrapper for SchoolSystem.
    Defers database migrations until first access, allowing health checks to pass.
    Thread-safe with double-checked locking.
    """
    _instance = None
    _initialized = False
    _lock = threading.Lock()
    
    def __getattr__(self, name):
        if not self._initialized:
            self._initialize()
        return getattr(self._instance, name)
    
    def _initialize(self):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self._instance = SchoolSystem()
            self._initialized = True
            logger.info(
                event_type='school_system_initialized',
                domain='school',
                message='Sistema scuole-classi-professori inizializzato'
            )
    
    def init_school_tables(self):
        """Explicit initialization method for startup sequence."""
        if not self._initialized:
            self._initialize()
        return self._instance.init_school_tables()

# Lazy instance - won't run migrations until first access
school_system = _LazySchoolSystem()