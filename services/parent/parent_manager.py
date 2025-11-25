"""
SKAILA Parent Dashboard - Parent Manager Service
Handles parent-student linking and data access with zero-friction onboarding
"""

import random
import string
from datetime import datetime
from typing import Optional, List, Dict, Any
from services.database.database_manager import DatabaseManager
from shared.error_handling import get_logger

logger = get_logger(__name__)
db_manager = DatabaseManager()


class ParentManager:
    """Manages parent-student relationships and data access"""
    
    def __init__(self):
        """Initialize Parent Manager and ensure database tables exist"""
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create necessary tables for parent dashboard system"""
        try:
            # Add identification_code column to utenti table if not exists
            db_manager.execute('''
                ALTER TABLE utenti 
                ADD COLUMN IF NOT EXISTS identification_code VARCHAR(20) UNIQUE
            ''')
            
            # Create parent_student_links table
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS parent_student_links (
                    id SERIAL PRIMARY KEY,
                    parent_id INTEGER NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
                    student_id INTEGER NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
                    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    linked_by VARCHAR(50) DEFAULT 'self',
                    is_active BOOLEAN DEFAULT TRUE,
                    UNIQUE(parent_id, student_id)
                )
            ''')
            
            # Create index for faster lookups
            db_manager.execute('''
                CREATE INDEX IF NOT EXISTS idx_parent_student_parent 
                ON parent_student_links(parent_id, is_active)
            ''')
            
            db_manager.execute('''
                CREATE INDEX IF NOT EXISTS idx_parent_student_student 
                ON parent_student_links(student_id, is_active)
            ''')
            
            # Auto-generate identification codes for existing students without codes
            self._generate_missing_codes()
            
            logger.info(
                event_type='parent_tables_initialized',
                domain='parent',
                message='Parent dashboard tables created successfully'
            )
            
        except Exception as e:
            logger.error(
                event_type='parent_tables_creation_failed',
                domain='parent',
                error=str(e),
                exc_info=True
            )
    
    def _generate_student_code(self) -> str:
        """Generate unique student identification code (format: STU-2024-XXXXX)"""
        year = datetime.now().year
        random_part = ''.join(random.choices(string.digits, k=5))
        return f"STU-{year}-{random_part}"
    
    def _generate_missing_codes(self):
        """Auto-generate identification codes for students who don't have one"""
        try:
            # Find students without identification codes
            students_without_codes = db_manager.query('''
                SELECT id FROM utenti 
                WHERE ruolo = 'studente' 
                AND (identification_code IS NULL OR identification_code = '')
            ''') or []
            
            if not students_without_codes:
                return
            
            logger.info(
                event_type='generating_student_codes',
                domain='parent',
                count=len(students_without_codes),
                message=f'Generating codes for {len(students_without_codes)} students'
            )
            
            for student in students_without_codes:
                # Generate unique code with retry logic
                attempts = 0
                while attempts < 10:
                    code = self._generate_student_code()
                    
                    # Check if code already exists
                    existing = db_manager.query('''
                        SELECT id FROM utenti WHERE identification_code = %s
                    ''', (code,), one=True)
                    
                    if not existing:
                        # Code is unique, assign it
                        db_manager.execute('''
                            UPDATE utenti 
                            SET identification_code = %s 
                            WHERE id = %s
                        ''', (code, student['id']))
                        break
                    
                    attempts += 1
            
            logger.info(
                event_type='student_codes_generated',
                domain='parent',
                message='Student identification codes generated successfully'
            )
            
        except Exception as e:
            logger.warning(
                event_type='code_generation_failed',
                domain='parent',
                error=str(e),
                message='Failed to generate student codes (non-critical)'
            )
    
    def get_student_code(self, student_id: int) -> Optional[str]:
        """Get or generate identification code for a student"""
        try:
            student = db_manager.query('''
                SELECT identification_code FROM utenti 
                WHERE id = %s AND ruolo = 'studente'
            ''', (student_id,), one=True)
            
            if not student:
                return None
            
            # If student doesn't have code, generate one
            if not student.get('identification_code'):
                code = self._generate_student_code()
                db_manager.execute('''
                    UPDATE utenti 
                    SET identification_code = %s 
                    WHERE id = %s
                ''', (code, student_id))
                return code
            
            return student['identification_code']
            
        except Exception as e:
            logger.error(
                event_type='get_student_code_failed',
                domain='parent',
                student_id=student_id,
                error=str(e)
            )
            return None
    
    def link_parent_to_student(self, parent_id: int, student_code: str) -> Dict[str, Any]:
        """
        Link parent to student using student's identification code
        
        Args:
            parent_id: ID of parent user
            student_code: Student's unique identification code
            
        Returns:
            Dict with success status and message
        """
        try:
            # Verify parent exists and has correct role
            parent = db_manager.query('''
                SELECT id, ruolo FROM utenti WHERE id = %s
            ''', (parent_id,), one=True)
            
            if not parent or parent['ruolo'] != 'genitore':
                return {
                    'success': False,
                    'error': 'Invalid Parent',
                    'message': 'Account genitore non valido'
                }
            
            # Find student by identification code
            student = db_manager.query('''
                SELECT id, nome, cognome, classe, scuola_id 
                FROM utenti 
                WHERE identification_code = %s AND ruolo = 'studente'
            ''', (student_code.strip().upper(),), one=True)
            
            if not student:
                return {
                    'success': False,
                    'error': 'Student Not Found',
                    'message': 'Codice studente non trovato. Verifica il codice e riprova.'
                }
            
            # Check if link already exists
            existing_link = db_manager.query('''
                SELECT id, is_active FROM parent_student_links 
                WHERE parent_id = %s AND student_id = %s
            ''', (parent_id, student['id']), one=True)
            
            if existing_link:
                if existing_link['is_active']:
                    return {
                        'success': False,
                        'error': 'Already Linked',
                        'message': 'Questo studente è già collegato al tuo account'
                    }
                else:
                    # Reactivate existing link
                    db_manager.execute('''
                        UPDATE parent_student_links 
                        SET is_active = TRUE, linked_at = CURRENT_TIMESTAMP 
                        WHERE id = %s
                    ''', (existing_link['id'],))
            else:
                # Create new link
                db_manager.execute('''
                    INSERT INTO parent_student_links 
                    (parent_id, student_id, linked_by, is_active) 
                    VALUES (%s, %s, 'self', TRUE)
                ''', (parent_id, student['id']))
            
            logger.info(
                event_type='parent_student_linked',
                domain='parent',
                parent_id=parent_id,
                student_id=student['id'],
                student_code=student_code
            )
            
            return {
                'success': True,
                'message': f"Collegamento effettuato con {student['nome']} {student['cognome']}",
                'student': {
                    'id': student['id'],
                    'nome': student['nome'],
                    'cognome': student['cognome'],
                    'classe': student['classe']
                }
            }
            
        except Exception as e:
            logger.error(
                event_type='link_parent_failed',
                domain='parent',
                parent_id=parent_id,
                student_code=student_code,
                error=str(e),
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Server Error',
                'message': 'Errore durante il collegamento. Riprova.'
            }
    
    def get_linked_children(self, parent_id: int) -> List[Dict[str, Any]]:
        """Get all children linked to a parent account"""
        try:
            children = db_manager.query('''
                SELECT 
                    u.id,
                    u.nome,
                    u.cognome,
                    u.classe,
                    u.avatar,
                    u.identification_code,
                    psl.linked_at,
                    s.nome as scuola_nome
                FROM parent_student_links psl
                JOIN utenti u ON psl.student_id = u.id
                LEFT JOIN scuole s ON u.scuola_id = s.id
                WHERE psl.parent_id = %s AND psl.is_active = TRUE
                ORDER BY psl.linked_at DESC
            ''', (parent_id,)) or []
            
            return children
            
        except Exception as e:
            logger.error(
                event_type='get_children_failed',
                domain='parent',
                parent_id=parent_id,
                error=str(e)
            )
            return []
    
    def get_child_overview(self, parent_id: int, student_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive overview of a child's academic data
        (Grades, Attendance, Behavior Notes) - READ ONLY for parents
        """
        try:
            # Verify parent has access to this student
            link = db_manager.query('''
                SELECT id FROM parent_student_links 
                WHERE parent_id = %s AND student_id = %s AND is_active = TRUE
            ''', (parent_id, student_id), one=True)
            
            if not link:
                logger.warning(
                    event_type='unauthorized_child_access',
                    domain='parent',
                    parent_id=parent_id,
                    student_id=student_id
                )
                return None
            
            # Get student basic info
            student = db_manager.query('''
                SELECT id, nome, cognome, classe, avatar, email 
                FROM utenti WHERE id = %s
            ''', (student_id,), one=True)
            
            if not student:
                return None
            
            # Get recent grades from registro_voti
            grades = db_manager.query('''
                SELECT 
                    materia,
                    voto,
                    tipo_valutazione,
                    data_voto,
                    note
                FROM registro_voti 
                WHERE studente_id = %s 
                ORDER BY data_voto DESC 
                LIMIT 10
            ''', (student_id,)) or []
            
            # Get attendance summary
            attendance = db_manager.query('''
                SELECT 
                    COUNT(*) FILTER (WHERE stato = 'assente') as assenze,
                    COUNT(*) FILTER (WHERE stato = 'ritardo') as ritardi,
                    COUNT(*) FILTER (WHERE stato = 'presente') as presenze
                FROM registro_presenze 
                WHERE studente_id = %s 
                AND data >= CURRENT_DATE - INTERVAL '30 days'
            ''', (student_id,), one=True) or {'assenze': 0, 'ritardi': 0, 'presenze': 0}
            
            # Get teacher notes (behavior/observations)
            notes = db_manager.query('''
                SELECT 
                    note,
                    data_voto as data_nota,
                    materia
                FROM registro_voti 
                WHERE studente_id = %s 
                AND note IS NOT NULL 
                AND note != ''
                ORDER BY data_voto DESC 
                LIMIT 5
            ''', (student_id,)) or []
            
            # Calculate average grade
            avg_grade = db_manager.query('''
                SELECT ROUND(AVG(voto::numeric), 2) as media 
                FROM registro_voti 
                WHERE studente_id = %s 
                AND voto IS NOT NULL
            ''', (student_id,), one=True)
            
            return {
                'student': student,
                'grades': grades,
                'attendance': attendance,
                'notes': notes,
                'average_grade': avg_grade['media'] if avg_grade and avg_grade['media'] else None
            }
            
        except Exception as e:
            logger.error(
                event_type='get_child_overview_failed',
                domain='parent',
                parent_id=parent_id,
                student_id=student_id,
                error=str(e),
                exc_info=True
            )
            return None
    
    def unlink_child(self, parent_id: int, student_id: int) -> bool:
        """Remove link between parent and student"""
        try:
            db_manager.execute('''
                UPDATE parent_student_links 
                SET is_active = FALSE 
                WHERE parent_id = %s AND student_id = %s
            ''', (parent_id, student_id))
            
            logger.info(
                event_type='child_unlinked',
                domain='parent',
                parent_id=parent_id,
                student_id=student_id
            )
            return True
            
        except Exception as e:
            logger.error(
                event_type='unlink_child_failed',
                domain='parent',
                parent_id=parent_id,
                student_id=student_id,
                error=str(e)
            )
            return False
