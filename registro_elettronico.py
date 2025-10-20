"""
SKAILA Registro Elettronico
Sistema completo per gestione presenze, voti, note, calendario lezioni
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from database_manager import db_manager

class RegistroElettronico:
    """Sistema registro elettronico"""
    
    # ========== PRESENZE ==========
    
    def mark_attendance(self, student_id: int, date: date, status: str, 
                       teacher_id: int, note: Optional[str] = None) -> Dict:
        """Segna presenza/assenza"""
        
        valid_statuses = ['presente', 'assente', 'ritardo', 'uscita_anticipata']
        if status not in valid_statuses:
            return {'error': f'Status non valido. Usa: {", ".join(valid_statuses)}'}
        
        # Get student class
        student = db_manager.query('SELECT classe FROM utenti WHERE id = %s', (student_id,), one=True)
        if not student:
            return {'error': 'Studente non trovato'}
        
        # Upsert attendance
        existing = db_manager.query('''
            SELECT id FROM registro_presenze WHERE student_id = ? AND date = ?
        ''', (student_id, date), one=True)
        
        if existing:
            db_manager.execute('''
                UPDATE registro_presenze 
                SET status = ?, note = ?, teacher_id = ?
                WHERE student_id = ? AND date = ?
            ''', (status, note, teacher_id, student_id, date))
        else:
            db_manager.execute('''
                INSERT INTO registro_presenze 
                (student_id, class, date, status, note, teacher_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (student_id, student['classe'], date, status, note, teacher_id))
        
        # If absence, create justification entry
        if status == 'assente':
            db_manager.execute('''
                INSERT INTO registro_assenze_giustificate (student_id, absence_date)
                VALUES (%s, %s)
                ON CONFLICT (student_id, absence_date) DO NOTHING
            ''', (student_id, date))
        
        return {'success': True, 'status': status}
    
    def mark_class_attendance(self, class_name: str, date: date, teacher_id: int,
                             attendance_list: List[Dict]) -> Dict:
        """Segna presenze per tutta la classe"""
        
        marked = 0
        errors = []
        
        for record in attendance_list:
            result = self.mark_attendance(
                record['student_id'],
                date,
                record['status'],
                teacher_id,
                record.get('note')
            )
            
            if result.get('success'):
                marked += 1
            else:
                errors.append(f"Student {record['student_id']}: {result.get('error')}")
        
        return {
            'success': True,
            'marked': marked,
            'total': len(attendance_list),
            'errors': errors
        }
    
    def get_student_attendance(self, student_id: int, start_date: Optional[date] = None,
                               end_date: Optional[date] = None) -> List[Dict]:
        """Ottieni presenze studente"""
        
        query = 'SELECT * FROM registro_presenze WHERE student_id = %s'
        params = [student_id]
        
        if start_date:
            query += ' AND date >= %s'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= %s'
            params.append(end_date)
        
        query += ' ORDER BY date DESC'
        
        records = db_manager.query(query, tuple(params))
        
        return [
            {
                'date': str(r['date']),
                'status': r['status'],
                'note': r['note']
            }
            for r in records
        ]
    
    def get_attendance_statistics(self, student_id: int, months: int = 3) -> Dict:
        """Statistiche presenze studente"""
        
        start_date = date.today() - timedelta(days=months * 30)
        
        stats = db_manager.query('''
            SELECT 
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'presente' THEN 1 ELSE 0 END) as presenti,
                SUM(CASE WHEN status = 'assente' THEN 1 ELSE 0 END) as assenze,
                SUM(CASE WHEN status = 'ritardo' THEN 1 ELSE 0 END) as ritardi,
                SUM(CASE WHEN status = 'uscita_anticipata' THEN 1 ELSE 0 END) as uscite_anticipate
            FROM registro_presenze
            WHERE student_id = ? AND date >= ?
        ''', (student_id, start_date), one=True)
        
        # Unjustified absences
        unjustified = db_manager.query('''
            SELECT COUNT(*) as count FROM registro_assenze_giustificate
            WHERE student_id = ? AND absence_date >= ? AND justified_by_parent = FALSE
        ''', (student_id, start_date), one=True)
        
        return {
            'total_days': stats['total_days'] if stats else 0,
            'presenti': stats['presenti'] if stats else 0,
            'assenze': stats['assenze'] if stats else 0,
            'ritardi': stats['ritardi'] if stats else 0,
            'uscite_anticipate': stats['uscite_anticipate'] if stats else 0,
            'assenze_non_giustificate': unjustified['count'] if unjustified else 0,
            'percentuale_presenza': round((stats['presenti'] / stats['total_days'] * 100), 1) if stats and stats['total_days'] > 0 else 0
        }
    
    # ========== VOTI ==========
    
    def insert_grade(self, student_id: int, teacher_id: int, subject: str,
                    voto: float, tipo: str, description: str, date: date, 
                    peso: float = 1.0) -> Dict:
        """Inserisci voto"""
        
        # Validate grade (Italian scale 1-10)
        if not (1 <= voto <= 10):
            return {'error': 'Voto deve essere tra 1 e 10'}
        
        cursor = db_manager.execute('''
            INSERT INTO registro_voti 
            (student_id, teacher_id, subject, voto, tipo, description, date, peso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (student_id, teacher_id, subject, voto, tipo, description, date, peso))
        
        grade_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else 0
        
        return {
            'success': True,
            'grade_id': grade_id,
            'voto': voto
        }
    
    def get_student_grades(self, student_id: int, subject: Optional[str] = None,
                          start_date: Optional[date] = None) -> List[Dict]:
        """Ottieni voti studente"""
        
        query = '''
            SELECT rv.*, u.nome as teacher_name, u.cognome as teacher_surname
            FROM registro_voti rv
            JOIN utenti u ON rv.teacher_id = u.id
            WHERE rv.student_id = ?
        '''
        params = [student_id]
        
        if subject:
            query += ' AND rv.subject = %s'
            params.append(subject)
        
        if start_date:
            query += ' AND rv.date >= %s'
            params.append(start_date)
        
        query += ' ORDER BY rv.date DESC'
        
        grades = db_manager.query(query, tuple(params))
        
        return [
            {
                'id': g['id'],
                'subject': g['subject'],
                'voto': float(g['voto']),
                'tipo': g['tipo'],
                'description': g['description'],
                'date': str(g['date']),
                'peso': float(g['peso']),
                'teacher': f"{g['teacher_name']} {g['teacher_surname']}"
            }
            for g in grades
        ]
    
    def calculate_average(self, student_id: int, subject: str) -> Tuple[float, int]:
        """Calcola media ponderata per materia"""
        
        grades = db_manager.query('''
            SELECT voto, peso FROM registro_voti
            WHERE student_id = ? AND subject = ?
        ''', (student_id, subject))
        
        if not grades:
            return 0.0, 0
        
        total_weighted = sum(float(g['voto']) * float(g['peso']) for g in grades)
        total_weight = sum(float(g['peso']) for g in grades)
        
        average = total_weighted / total_weight if total_weight > 0 else 0
        
        return round(average, 2), len(grades)
    
    def get_subject_averages(self, student_id: int) -> List[Dict]:
        """Ottieni medie per tutte le materie"""
        
        subjects = db_manager.query('''
            SELECT DISTINCT subject FROM registro_voti WHERE student_id = ?
        ''', (student_id,))
        
        averages = []
        for subj in subjects:
            avg, count = self.calculate_average(student_id, subj['subject'])
            averages.append({
                'subject': subj['subject'],
                'average': avg,
                'grade_count': count,
                'status': self._get_grade_status(avg)
            })
        
        return sorted(averages, key=lambda x: x['average'], reverse=True)
    
    # ========== NOTE DISCIPLINARI ==========
    
    def insert_disciplinary_note(self, student_id: int, teacher_id: int,
                                 note_type: str, description: str, 
                                 severity: str = 'lieve', date: date = None) -> Dict:
        """Inserisci nota disciplinare"""
        
        if date is None:
            date = datetime.now().date()
        
        valid_severities = ['lieve', 'media', 'grave']
        if severity not in valid_severities:
            severity = 'lieve'
        
        cursor = db_manager.execute('''
            INSERT INTO registro_note_disciplinari
            (student_id, teacher_id, note_type, description, severity, date)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (student_id, teacher_id, note_type, description, severity, date))
        
        note_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else 0
        
        return {
            'success': True,
            'note_id': note_id,
            'severity': severity
        }
    
    def get_disciplinary_notes(self, student_id: int) -> List[Dict]:
        """Ottieni note disciplinari studente"""
        
        notes = db_manager.query('''
            SELECT rnd.*, u.nome as teacher_name, u.cognome as teacher_surname
            FROM registro_note_disciplinari rnd
            JOIN utenti u ON rnd.teacher_id = u.id
            WHERE rnd.student_id = ?
            ORDER BY rnd.date DESC
        ''', (student_id,))
        
        return [
            {
                'id': n['id'],
                'note_type': n['note_type'],
                'description': n['description'],
                'severity': n['severity'],
                'date': str(n['date']),
                'teacher': f"{n['teacher_name']} {n['teacher_surname']}"
            }
            for n in notes
        ]
    
    # ========== GIUSTIFICAZIONI ==========
    
    def justify_absence(self, student_id: int, absence_date: date,
                       justification_note: str, parent_id: Optional[int] = None) -> Dict:
        """Giustifica assenza"""
        
        # Check if absence exists
        absence = db_manager.query('''
            SELECT * FROM registro_assenze_giustificate
            WHERE student_id = ? AND absence_date = ?
        ''', (student_id, absence_date), one=True)
        
        if not absence:
            return {'error': 'Assenza non trovata'}
        
        db_manager.execute('''
            UPDATE registro_assenze_giustificate
            SET justification_date = ?, justification_note = ?, 
                justified_by_parent = TRUE, parent_id = ?
            WHERE student_id = ? AND absence_date = ?
        ''', (datetime.now().date(), justification_note, parent_id, student_id, absence_date))
        
        return {'success': True, 'message': 'Assenza giustificata'}
    
    def get_unjustified_absences(self, student_id: int) -> List[Dict]:
        """Ottieni assenze non giustificate"""
        
        absences = db_manager.query('''
            SELECT * FROM registro_assenze_giustificate
            WHERE student_id = ? AND justified_by_parent = FALSE
            ORDER BY absence_date DESC
        ''', (student_id,))
        
        return [{'date': str(a['absence_date'])} for a in absences]
    
    # ========== CALENDARIO LEZIONI ==========
    
    def add_lesson(self, teacher_id: int, class_name: str, subject: str,
                  lesson_date: date, lesson_time: str, topic: str,
                  homework: Optional[str] = None, materials_used: Optional[str] = None) -> Dict:
        """Aggiungi lezione al calendario"""
        
        cursor = db_manager.execute('''
            INSERT INTO registro_calendario_lezioni
            (teacher_id, class, subject, lesson_date, lesson_time, topic, homework, materials_used)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (teacher_id, class_name, subject, lesson_date, lesson_time, topic, homework, materials_used))
        
        lesson_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else 0
        
        return {
            'success': True,
            'lesson_id': lesson_id
        }
    
    def get_class_lessons(self, class_name: str, subject: Optional[str] = None,
                         start_date: Optional[date] = None) -> List[Dict]:
        """Ottieni lezioni classe"""
        
        query = '''
            SELECT rcl.*, u.nome as teacher_name, u.cognome as teacher_surname
            FROM registro_calendario_lezioni rcl
            JOIN utenti u ON rcl.teacher_id = u.id
            WHERE rcl.class = ?
        '''
        params = [class_name]
        
        if subject:
            query += ' AND rcl.subject = %s'
            params.append(subject)
        
        if start_date:
            query += ' AND rcl.lesson_date >= %s'
            params.append(start_date)
        
        query += ' ORDER BY rcl.lesson_date DESC, rcl.lesson_time DESC'
        
        lessons = db_manager.query(query, tuple(params))
        
        return [
            {
                'id': l['id'],
                'subject': l['subject'],
                'date': str(l['lesson_date']),
                'time': l['lesson_time'],
                'topic': l['topic'],
                'homework': l['homework'],
                'teacher': f"{l['teacher_name']} {l['teacher_surname']}"
            }
            for l in lessons
        ]
    
    # ========== UTILITIES ==========
    
    def _get_grade_status(self, average: float) -> str:
        """Status voto"""
        if average >= 8:
            return 'ottimo'
        elif average >= 6:
            return 'sufficiente'
        elif average >= 5:
            return 'insufficiente'
        else:
            return 'gravemente_insufficiente'
    
    def get_student_report(self, student_id: int, months: int = 1) -> Dict:
        """Report completo studente"""
        
        start_date = date.today() - timedelta(days=months * 30)
        
        # Attendance
        attendance = self.get_attendance_statistics(student_id, months)
        
        # Grades
        averages = self.get_subject_averages(student_id)
        
        # Disciplinary
        notes = self.get_disciplinary_notes(student_id)
        recent_notes = [n for n in notes if datetime.strptime(n['date'], '%Y-%m-%d').date() >= start_date]
        
        # Unjustified absences
        unjustified = self.get_unjustified_absences(student_id)
        
        return {
            'student_id': student_id,
            'period': f'{months} mesi',
            'attendance': attendance,
            'subject_averages': averages,
            'disciplinary_notes': len(recent_notes),
            'unjustified_absences': len(unjustified),
            'overall_status': self._calculate_overall_status(attendance, averages, recent_notes)
        }
    
    def _calculate_overall_status(self, attendance: Dict, averages: List[Dict], 
                                  notes: List[Dict]) -> str:
        """Calcola status generale studente"""
        
        # Check attendance
        if attendance['percentuale_presenza'] < 75 or attendance['assenze_non_giustificate'] > 5:
            return 'critico'
        
        # Check grades
        failing_subjects = sum(1 for a in averages if a['average'] < 6)
        if failing_subjects > 2:
            return 'a_rischio'
        
        # Check discipline
        severe_notes = sum(1 for n in notes if n['severity'] == 'grave')
        if severe_notes > 0:
            return 'a_rischio'
        
        # Check excellence
        excellent_subjects = sum(1 for a in averages if a['average'] >= 8)
        if excellent_subjects >= len(averages) * 0.7 and attendance['percentuale_presenza'] >= 95:
            return 'eccellente'
        
        return 'regolare'


# Initialize
registro = RegistroElettronico()
print("✅ Registro Elettronico inizializzato!")
