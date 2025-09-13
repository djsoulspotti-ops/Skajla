# Sistema Scuole-Classi-Professori per SKAILA
# Estensione multi-tenant con gestione organizzazioni scolastiche

from database_manager import db_manager
from performance_cache import user_cache, invalidate_user_cache
import secrets
import string

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
                        school_id INTEGER NOT NULL REFERENCES scuole(id) ON DELETE CASCADE,
                        role TEXT NOT NULL CHECK (role IN ('dirigente', 'professore', 'studente')),
                        token TEXT UNIQUE NOT NULL,
                        expires_at TIMESTAMP,
                        uses_remaining INTEGER,
                        created_by INTEGER REFERENCES utenti(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        revoked_at TIMESTAMP
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_id INTEGER NOT NULL REFERENCES scuole(id) ON DELETE CASCADE,
                        role TEXT NOT NULL CHECK (role IN ('dirigente', 'professore', 'studente')),
                        token TEXT UNIQUE NOT NULL,
                        expires_at TIMESTAMP,
                        uses_remaining INTEGER,
                        created_by INTEGER REFERENCES utenti(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        revoked_at TIMESTAMP
                    )
                ''')

            # Tabella associazione docenti-classi
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS docenti_classi (
                        id SERIAL PRIMARY KEY,
                        docente_id INTEGER NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
                        classe_id INTEGER NOT NULL REFERENCES classi(id) ON DELETE CASCADE,
                        materia TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(docente_id, classe_id)
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS docenti_classi (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        docente_id INTEGER NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
                        classe_id INTEGER NOT NULL REFERENCES classi(id) ON DELETE CASCADE,
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
        try:
            cursor.execute('ALTER TABLE utenti ADD COLUMN scuola_id INTEGER REFERENCES scuole(id)')
        except Exception:
            pass  # Colonna già esistente
            
        try:
            cursor.execute('ALTER TABLE utenti ADD COLUMN classe_id INTEGER REFERENCES classi(id)')
        except Exception:
            pass  # Colonna già esistente
    
    def _extend_chat_table(self, cursor):
        """Estende tabella chat per supportare organizzazione scolastica"""
        try:
            if db_manager.db_type == 'postgresql':
                cursor.execute("ALTER TABLE chat ADD COLUMN tipo TEXT DEFAULT 'gruppo' CHECK (tipo IN ('scuola','classe','docenti','gruppo','privata'))")
            else:
                cursor.execute("ALTER TABLE chat ADD COLUMN tipo TEXT DEFAULT 'gruppo'")
        except Exception:
            pass
            
        try:
            cursor.execute('ALTER TABLE chat ADD COLUMN scuola_id INTEGER REFERENCES scuole(id)')
        except Exception:
            pass
            
        try:
            cursor.execute('ALTER TABLE chat ADD COLUMN classe_id INTEGER REFERENCES classi(id)')  
        except Exception:
            pass
            
        try:
            if db_manager.db_type == 'postgresql':
                cursor.execute('ALTER TABLE chat ADD COLUMN sistema BOOLEAN DEFAULT false')
            else:
                cursor.execute('ALTER TABLE chat ADD COLUMN sistema BOOLEAN DEFAULT 0')
        except Exception:
            pass
    
    def setup_default_school(self):
        """Configura scuola predefinita per migrazione"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
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
                        VALUES (?, ?, ?, ?)
                    ''', ('Scuola Predefinita', 'DEFAULT_SCHOOL', self.generate_invite_code(), 'DIR2024'))
                    default_school_id = cursor.lastrowid
                
                # Migra utenti esistenti alla scuola predefinita
                if db_manager.db_type == 'postgresql':
                    cursor.execute('UPDATE utenti SET scuola_id = %s WHERE scuola_id IS NULL', (default_school_id,))
                else:
                    cursor.execute('UPDATE utenti SET scuola_id = ? WHERE scuola_id IS NULL', (default_school_id,))
                
                conn.commit()
                print(f"✅ Scuola predefinita creata (ID: {default_school_id})")
    
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
                    VALUES (?, ?, ?, ?)
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
                        SET scuola_id = ?, ruolo = ? 
                        WHERE id = ?
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
                    VALUES (?, ?, ?, ?, ?)
                ''', (scuola_id, nome, anno, sezione, codice_classe))
                class_id = cursor.lastrowid
            
            # Crea chat per la classe
            self.create_class_chat(class_id, scuola_id, nome)
            
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
                        VALUES (?, ?, ?)
                    ''', (docente_id, classe_id, materia))
                
                conn.commit()
                return True
            except Exception as e:
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
                    VALUES (?, ?, ?, ?)
                ''', ('Comunicazioni Scuola', 'scuola', scuola_id, 1))
                
                cursor.execute('''
                    INSERT INTO chat (nome, tipo, scuola_id, sistema)
                    VALUES (?, ?, ?, ?)
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
                    VALUES (?, ?, ?, ?, ?)
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
                    WHERE scuola_id = ? AND attiva = 1 
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
                    cursor.execute('SELECT id FROM scuole WHERE dominio_email = ? OR nome = ?', 
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
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
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
                        VALUES (?, ?, ?, ?, ?)
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
            print(f"Errore auto-registrazione scuola: {e}")
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
                        WHERE token = ? AND purpose = ? AND consumed_at IS NULL
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
                    cursor.execute('UPDATE scuole SET attiva = 1, domain_verified = 1 WHERE id = ?', (school_id,))
                
                # Marca verifica come consumata
                if db_manager.db_type == 'postgresql':
                    cursor.execute('UPDATE email_verifications SET consumed_at = CURRENT_TIMESTAMP WHERE token = %s', (token,))
                else:
                    cursor.execute('UPDATE email_verifications SET consumed_at = CURRENT_TIMESTAMP WHERE token = ?', (token,))
                
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
            print(f"Errore verifica dirigente: {e}")
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
                        WHERE u.id = ? AND s.id = ? AND u.ruolo = 'dirigente'
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
            print(f"Errore recupero codici: {e}")
            return {'success': False, 'message': f'Errore: {str(e)}'}

# Istanza globale sistema scolastico
school_system = SchoolSystem()

print("✅ Sistema scuole-classi-professori inizializzato")