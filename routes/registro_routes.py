"""
SKAILA - Routes API Registro Elettronico
Gestione voti, presenze, note disciplinari, calendario lezioni
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, date
from registro_elettronico import registro
from database_manager import db_manager
from services.tenant_guard import get_current_school_id
from shared.validators.input_validators import validator, sql_protector
from shared.middleware.auth import require_auth, require_teacher

registro_bp = Blueprint('registro_api', __name__)

# ============== PRESENZE ==============

@registro_bp.route('/api/registro/presenze/segna', methods=['POST'])
@require_auth
@require_teacher
def segna_presenza():
    """Segna presenza/assenza singolo studente"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        date_str = data.get('date')  # YYYY-MM-DD
        status = data.get('status')  # presente, assente, ritardo, uscita_anticipata
        note = data.get('note', '')
        
        # Validazione
        if not all([student_id, date_str, status]):
            return jsonify({'error': 'Parametri mancanti'}), 400
        
        # Parse date
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Verifica che studente appartenga alla scuola
        school_id = get_current_school_id()
        student = db_manager.query('''
            SELECT id FROM utenti 
            WHERE id = %s AND scuola_id = %s AND ruolo = %s
        ''', (student_id, school_id, 'studente'), one=True)
        
        if not student:
            return jsonify({'error': 'Studente non trovato'}), 404
        
        # Segna presenza
        result = registro.mark_attendance(
            student_id, 
            attendance_date, 
            status, 
            session['user_id'],
            note
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f'Presenza segnata: {status}'
            }), 200
        else:
            return jsonify({'error': result.get('error')}), 400
            
    except Exception as e:
        print(f"❌ Errore segna_presenza: {e}")
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/presenze/classe', methods=['POST'])
@require_auth
@require_teacher
def segna_presenze_classe():
    """Segna presenze per tutta la classe"""
    try:
        data = request.get_json()
        classe = data.get('classe')
        date_str = data.get('date')
        attendance_list = data.get('attendance_list')  # [{"student_id": 1, "status": "presente", "note": ""}]
        
        if not all([classe, date_str, attendance_list]):
            return jsonify({'error': 'Parametri mancanti'}), 400
        
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        result = registro.mark_class_attendance(
            classe,
            attendance_date,
            session['user_id'],
            attendance_list
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Errore segna_presenze_classe: {e}")
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/presenze/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_presenze_studente(student_id):
    """Ottieni storico presenze studente"""
    try:
        # Verifica permessi: studente può vedere solo le sue, prof/dirigente tutte
        if session.get('ruolo') == 'studente' and session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato'}), 403
        
        # Verifica tenant isolation
        school_id = get_current_school_id()
        student = db_manager.query('''
            SELECT id FROM utenti WHERE id = %s AND scuola_id = %s
        ''', (student_id, school_id), one=True)
        
        if not student:
            return jsonify({'error': 'Studente non trovato'}), 404
        
        presenze = registro.get_student_attendance(student_id, months=3)
        stats = registro.get_attendance_statistics(student_id)
        
        return jsonify({
            'presenze': presenze,
            'statistiche': stats
        }), 200
        
    except Exception as e:
        print(f"❌ Errore get_presenze_studente: {e}")
        return jsonify({'error': str(e)}), 500

# ============== VOTI ==============

@registro_bp.route('/api/registro/voti/inserisci', methods=['POST'])
@require_auth
@require_teacher
def inserisci_voto():
    """Inserisci voto per uno studente"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        subject = data.get('subject')
        grade = data.get('grade')  # 1-10
        evaluation_type = data.get('evaluation_type', 'scritto')  # scritto/orale
        description = data.get('description', '')
        date_str = data.get('date')
        
        # Validazione
        if not all([student_id, subject, grade]):
            return jsonify({'error': 'Parametri mancanti'}), 400
        
        # Validazione voto (scala italiana 1-10)
        try:
            grade_value = float(grade)
            if grade_value < 1 or grade_value > 10:
                return jsonify({'error': 'Voto deve essere tra 1 e 10'}), 400
        except ValueError:
            return jsonify({'error': 'Voto non valido'}), 400
        
        # Parse date
        grade_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
        
        # Verifica tenant isolation
        school_id = get_current_school_id()
        student = db_manager.query('''
            SELECT id FROM utenti WHERE id = %s AND scuola_id = %s AND ruolo = %s
        ''', (student_id, school_id, 'studente'), one=True)
        
        if not student:
            return jsonify({'error': 'Studente non trovato'}), 404
        
        # Inserisci voto
        result = registro.insert_grade(
            student_id,
            subject,
            grade_value,
            grade_date,
            evaluation_type,
            session['user_id'],
            description
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Voto inserito con successo'
            }), 201
        else:
            return jsonify({'error': result.get('error')}), 400
            
    except Exception as e:
        print(f"❌ Errore inserisci_voto: {e}")
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/voti/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_voti_studente(student_id):
    """Ottieni voti studente"""
    try:
        # Verifica permessi
        if session.get('ruolo') == 'studente' and session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato'}), 403
        
        # Verifica tenant
        school_id = get_current_school_id()
        student = db_manager.query('''
            SELECT id FROM utenti WHERE id = %s AND scuola_id = %s
        ''', (student_id, school_id), one=True)
        
        if not student:
            return jsonify({'error': 'Studente non trovato'}), 404
        
        voti = registro.get_student_grades(student_id, months=6)
        medie = registro.get_subject_averages(student_id)
        
        return jsonify({
            'voti': voti,
            'medie': medie
        }), 200
        
    except Exception as e:
        print(f"❌ Errore get_voti_studente: {e}")
        return jsonify({'error': str(e)}), 500

# ============== NOTE DISCIPLINARI ==============

@registro_bp.route('/api/registro/note/inserisci', methods=['POST'])
@require_auth
@require_teacher
def inserisci_nota():
    """Inserisci nota disciplinare"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        description = data.get('description')
        severity = data.get('severity', 'lieve')  # lieve/media/grave
        date_str = data.get('date')
        
        if not all([student_id, description]):
            return jsonify({'error': 'Parametri mancanti'}), 400
        
        # Sanitizza input
        description = validator.sanitize_html(description)
        
        if not sql_protector.is_safe(description):
            return jsonify({'error': 'Descrizione contiene caratteri non validi'}), 400
        
        note_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
        
        # Verifica tenant
        school_id = get_current_school_id()
        student = db_manager.query('''
            SELECT id FROM utenti WHERE id = %s AND scuola_id = %s
        ''', (student_id, school_id), one=True)
        
        if not student:
            return jsonify({'error': 'Studente non trovato'}), 404
        
        result = registro.insert_disciplinary_note(
            student_id,
            note_date,
            description,
            severity,
            session['user_id']
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Nota inserita'
            }), 201
        else:
            return jsonify({'error': result.get('error')}), 400
            
    except Exception as e:
        print(f"❌ Errore inserisci_nota: {e}")
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/note/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_note_studente(student_id):
    """Ottieni note disciplinari studente"""
    try:
        # Verifica permessi
        if session.get('ruolo') == 'studente' and session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato'}), 403
        
        # Verifica tenant
        school_id = get_current_school_id()
        student = db_manager.query('''
            SELECT id FROM utenti WHERE id = %s AND scuola_id = %s
        ''', (student_id, school_id), one=True)
        
        if not student:
            return jsonify({'error': 'Studente non trovato'}), 404
        
        note = registro.get_disciplinary_notes(student_id)
        
        return jsonify({'note': note}), 200
        
    except Exception as e:
        print(f"❌ Errore get_note_studente: {e}")
        return jsonify({'error': str(e)}), 500

# ============== CALENDARIO LEZIONI ==============

@registro_bp.route('/api/registro/lezioni/aggiungi', methods=['POST'])
@require_auth
@require_teacher
def aggiungi_lezione():
    """Aggiungi lezione al calendario classe"""
    try:
        data = request.get_json()
        classe = data.get('class')
        subject = data.get('subject')
        topic = data.get('topic')
        homework = data.get('homework', '')
        lesson_date_str = data.get('lesson_date')
        
        if not all([classe, subject, topic, lesson_date_str]):
            return jsonify({'error': 'Parametri mancanti'}), 400
        
        lesson_date = datetime.strptime(lesson_date_str, '%Y-%m-%d').date()
        
        result = registro.add_lesson(
            classe,
            subject,
            topic,
            lesson_date,
            session['user_id'],
            homework
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Lezione aggiunta'
            }), 201
        else:
            return jsonify({'error': result.get('error')}), 400
            
    except Exception as e:
        print(f"❌ Errore aggiungi_lezione: {e}")
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/lezioni/classe/<classe>', methods=['GET'])
@require_auth
def get_lezioni_classe(classe):
    """Ottieni calendario lezioni classe"""
    try:
        # Verifica che utente appartenga alla classe (studenti) o sia prof/dirigente
        user_class = session.get('classe', '')
        ruolo = session.get('ruolo')
        
        if ruolo == 'studente' and user_class != classe:
            return jsonify({'error': 'Accesso negato'}), 403
        
        lezioni = registro.get_class_lessons(classe, months=1)
        
        return jsonify({'lezioni': lezioni}), 200
        
    except Exception as e:
        print(f"❌ Errore get_lezioni_classe: {e}")
        return jsonify({'error': str(e)}), 500

# ============== STATISTICHE ==============

@registro_bp.route('/api/registro/statistiche/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_statistiche_studente(student_id):
    """Ottieni report completo studente"""
    try:
        # Verifica permessi
        if session.get('ruolo') == 'studente' and session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato'}), 403
        
        # Verifica tenant
        school_id = get_current_school_id()
        student = db_manager.query('''
            SELECT id FROM utenti WHERE id = %s AND scuola_id = %s
        ''', (student_id, school_id), one=True)
        
        if not student:
            return jsonify({'error': 'Studente non trovato'}), 404
        
        report = registro.get_student_report(student_id, months=3)
        
        return jsonify(report), 200
        
    except Exception as e:
        print(f"❌ Errore get_statistiche_studente: {e}")
        return jsonify({'error': str(e)}), 500
