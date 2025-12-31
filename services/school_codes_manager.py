"""
Sistema Modulare Gestione Codici Scuole
Generazione e assegnazione automatica codici per le prime 10 scuole
"""

from database_manager import db_manager
from school_system import school_system
import secrets
import string

class SchoolCodesManager:
    """Gestisce la generazione e assegnazione modulare dei codici scuola"""
    
    INITIAL_SCHOOLS_COUNT = 10
    
    def __init__(self):
        self.init_codes_table()
    
    def init_codes_table(self):
        """Inizializza tabella per codici scuola pre-generati"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS school_activation_codes (
                        id SERIAL PRIMARY KEY,
                        school_name VARCHAR(100) NOT NULL,
                        school_code VARCHAR(20) UNIQUE NOT NULL,
                        teacher_invite_code VARCHAR(20) UNIQUE NOT NULL,
                        director_code VARCHAR(30) UNIQUE NOT NULL,
                        assigned BOOLEAN DEFAULT false,
                        assigned_to_school_id INTEGER REFERENCES scuole(id),
                        assigned_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS school_activation_codes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_name TEXT NOT NULL,
                        school_code TEXT UNIQUE NOT NULL,
                        teacher_invite_code TEXT UNIQUE NOT NULL,
                        director_code TEXT UNIQUE NOT NULL,
                        assigned INTEGER DEFAULT 0,
                        assigned_to_school_id INTEGER REFERENCES scuole(id),
                        assigned_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                ''')
            
            conn.commit()
    
    def generate_premium_school_code(self, numero_scuola):
        """Genera codice scuola premium per le prime 10"""
        return f"SKAIL{numero_scuola:02d}{secrets.randbelow(1000):03d}"
    
    def generate_premium_teacher_code(self, numero_scuola):
        """Genera codice docenti premium"""
        return f"PROF{numero_scuola:02d}{''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))}"
    
    def generate_premium_director_code(self, numero_scuola):
        """Genera codice dirigente premium"""
        return f"DIR{numero_scuola:02d}{''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))}"
    
    def generate_initial_codes(self, force_regenerate=False):
        """Genera i codici per le prime 10 scuole"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM school_activation_codes')
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0 and not force_regenerate:
                print(f"✅ Codici già esistenti: {existing_count}")
                return {'success': True, 'message': f'Codici già generati: {existing_count}'}
            
            if force_regenerate:
                cursor.execute('DELETE FROM school_activation_codes WHERE assigned = false OR assigned = 0')
                print("🔄 Codici non assegnati eliminati")
            
            generated_codes = []
            
            for i in range(1, self.INITIAL_SCHOOLS_COUNT + 1):
                school_name = f"Scuola Partner {i}"
                school_code = self.generate_premium_school_code(i)
                teacher_code = self.generate_premium_teacher_code(i)
                director_code = self.generate_premium_director_code(i)
                
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO school_activation_codes 
                        (school_name, school_code, teacher_invite_code, director_code, notes)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (school_code) DO NOTHING
                    ''', (school_name, school_code, teacher_code, director_code, 
                          f'Codice premium per scuola partner #{i}'))
                else:
                    cursor.execute('''
                        INSERT OR IGNORE INTO school_activation_codes 
                        (school_name, school_code, teacher_invite_code, director_code, notes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (school_name, school_code, teacher_code, director_code,
                          f'Codice premium per scuola partner #{i}'))
                
                generated_codes.append({
                    'numero': i,
                    'nome': school_name,
                    'school_code': school_code,
                    'teacher_code': teacher_code,
                    'director_code': director_code
                })
            
            conn.commit()
            print(f"✅ Generati {len(generated_codes)} codici scuola premium")
            
            return {
                'success': True,
                'count': len(generated_codes),
                'codes': generated_codes
            }
    
    def get_all_codes(self, include_assigned=True):
        """Ottiene tutti i codici generati"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if include_assigned:
                query = '''
                    SELECT 
                        id, school_name, school_code, teacher_invite_code, 
                        director_code, assigned, assigned_to_school_id, 
                        assigned_at, notes, created_at
                    FROM school_activation_codes
                    ORDER BY id
                '''
            else:
                if db_manager.db_type == 'postgresql':
                    query = '''
                        SELECT 
                            id, school_name, school_code, teacher_invite_code, 
                            director_code, assigned, assigned_to_school_id, 
                            assigned_at, notes, created_at
                        FROM school_activation_codes
                        WHERE assigned = false
                        ORDER BY id
                    '''
                else:
                    query = '''
                        SELECT 
                            id, school_name, school_code, teacher_invite_code, 
                            director_code, assigned, assigned_to_school_id, 
                            assigned_at, notes, created_at
                        FROM school_activation_codes
                        WHERE assigned = 0
                        ORDER BY id
                    '''
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            codes = []
            for row in rows:
                codes.append({
                    'id': row[0],
                    'school_name': row[1],
                    'school_code': row[2],
                    'teacher_code': row[3],
                    'director_code': row[4],
                    'assigned': bool(row[5]),
                    'assigned_to_school_id': row[6],
                    'assigned_at': row[7],
                    'notes': row[8],
                    'created_at': row[9]
                })
            
            return codes
    
    def get_available_codes_count(self):
        """Conta codici disponibili non ancora assegnati"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if db_manager.db_type == 'postgresql':
                cursor.execute('SELECT COUNT(*) as count FROM school_activation_codes WHERE assigned = false')
            else:
                cursor.execute('SELECT COUNT(*) as count FROM school_activation_codes WHERE assigned = 0')
            
            return cursor.fetchone()[0]
    
    def assign_code_to_school(self, code_id, school_id):
        """Assegna un codice a una scuola esistente"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    UPDATE school_activation_codes 
                    SET assigned = true, assigned_to_school_id = %s, assigned_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND assigned = false
                ''', (school_id, code_id))
            else:
                cursor.execute('''
                    UPDATE school_activation_codes 
                    SET assigned = 1, assigned_to_school_id = %s, assigned_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND assigned = 0
                ''', (school_id, code_id))
            
            affected = cursor.rowcount
            conn.commit()
            
            return affected > 0
    
    def export_codes_for_distribution(self):
        """Esporta codici in formato leggibile per distribuzione"""
        codes = self.get_all_codes(include_assigned=False)
        
        export_text = "=" * 70 + "\n"
        export_text += "SKAJLA - CODICI SCUOLE PARTNER (PRIME 10 SCUOLE)\n"
        export_text += "=" * 70 + "\n\n"
        
        for idx, code in enumerate(codes, 1):
            export_text += f"SCUOLA #{idx}: {code['school_name']}\n"
            export_text += f"{'─' * 70}\n"
            export_text += f"📚 Codice Scuola:     {code['school_code']}\n"
            export_text += f"👨‍🏫 Codice Docenti:     {code['teacher_code']}\n"
            export_text += f"🎯 Codice Dirigente:   {code['director_code']}\n"
            export_text += f"\n💡 Note: {code['notes']}\n"
            export_text += f"{'═' * 70}\n\n"
        
        return export_text

school_codes_manager = SchoolCodesManager()

print("✅ Sistema gestione codici scuole inizializzato")
