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
            
            # Tabella scuole
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scuole (
                        id SERIAL PRIMARY KEY,
                        nome TEXT NOT NULL,
                        codice_pubblico TEXT UNIQUE NOT NULL,
                        dominio_email TEXT,
                        codice_invito_docenti TEXT UNIQUE,
                        codice_dirigente TEXT UNIQUE,
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
                        codice_invito_docenti TEXT UNIQUE,
                        codice_dirigente TEXT UNIQUE,
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

# Istanza globale sistema scolastico
school_system = SchoolSystem()

print("✅ Sistema scuole-classi-professori inizializzato")