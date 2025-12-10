"""
SKAJLA - Routes API Registro Elettronico
Gestione voti, presenze, note disciplinari, calendario lezioni
"""

from flask import Blueprint, request, jsonify, session, redirect, flash
from datetime import datetime, date
from registro_elettronico import registro
from database_manager import db_manager
from services.tenant_guard import get_current_school_id
from shared.validators.input_validators import validator, sql_protector
from shared.middleware.auth import require_auth, require_teacher
from shared.middleware.feature_guard import check_feature_enabled, Features
from shared.error_handling import (
    DatabaseError,
    ValidationError,
    AuthenticationError,
    get_logger
)

logger = get_logger(__name__)

registro_bp = Blueprint('registro_api', __name__)

@registro_bp.before_request
def check_registro_feature():
    """Verifica che il modulo Registro sia abilitato prima di ogni request"""
    if 'user_id' not in session:
        return  # Auth middleware gestirà questo
    
    try:
        school_id = get_current_school_id()
        if not check_feature_enabled(school_id, Features.REGISTRO):
            logger.info(
                event_type='feature_check_blocked',
                domain='registro',
                message='Registro feature not enabled for school',
                school_id=school_id,
                route=request.path
            )
            # API endpoint - ritorna JSON 403
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Feature non disponibile',
                    'message': 'Il Registro Elettronico non è disponibile per la tua scuola.',
                    'feature': Features.REGISTRO,
                    'upgrade_required': True
                }), 403
            # Web endpoint - redirect con flash
            flash('⚠️ Il Registro Elettronico non è disponibile per la tua scuola.', 'warning')
            return redirect('/dashboard')
    except Exception as e:
        logger.error(
            event_type='feature_check_error',
            domain='registro',
            message='Error checking registro feature availability',
            error=str(e),
            route=request.path,
            exc_info=True
        )
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Errore di sistema',
                'message': 'Impossibile verificare disponibilità feature. Riprova più tardi.'
            }), 500
        flash('⚠️ Errore nel verificare le funzionalità disponibili.', 'error')
        return redirect('/dashboard')

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
        logger.error(
            event_type='mark_attendance_error',
            domain='registro',
            message='Failed to mark student attendance',
            user_id=session.get('user_id'),
            student_id=data.get('student_id') if 'data' in locals() else None,
            route=request.path,
            error=str(e),
            exc_info=True
        )
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
        logger.error(
            event_type='mark_class_attendance_error',
            domain='registro',
            message='Failed to mark class attendance',
            user_id=session.get('user_id'),
            classe=data.get('classe') if 'data' in locals() else None,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/presenze/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_presenze_studente(student_id):
    """Ottieni storico presenze studente - SOLO LO STUDENTE STESSO"""
    try:
        # 🔒 PRIVACY: Solo lo studente può vedere i propri dati
        if session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato: puoi vedere solo i tuoi dati'}), 403
        
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
        logger.error(
            event_type='get_attendance_error',
            domain='registro',
            message='Failed to retrieve student attendance',
            user_id=session.get('user_id'),
            student_id=student_id,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500

# ============== VOTI ==============

@registro_bp.route('/api/registro/voti/inserisci', methods=['POST'])
@require_auth
@require_teacher
def inserisci_voto():
    """Inserisci voto per uno studente - SOLO PER LE PROPRIE MATERIE"""
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
        
        # 🔒 PRIVACY: Verifica che il professore insegni questa materia
        teacher_id = session['user_id']
        teacher_subjects = db_manager.query('''
            SELECT materie_insegnate FROM utenti WHERE id = %s
        ''', (teacher_id,), one=True)
        
        if teacher_subjects and teacher_subjects.get('materie_insegnate'):
            allowed_subjects = [s.strip() for s in teacher_subjects['materie_insegnate'].split(',')]
            if subject not in allowed_subjects:
                return jsonify({
                    'error': f'Non sei autorizzato a inserire voti per {subject}. Materie assegnate: {", ".join(allowed_subjects)}'
                }), 403
        
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
        logger.error(
            event_type='insert_grade_error',
            domain='registro',
            message='Failed to insert grade',
            user_id=session.get('user_id'),
            student_id=data.get('student_id') if 'data' in locals() else None,
            subject=data.get('subject') if 'data' in locals() else None,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/voti/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_voti_studente(student_id):
    """Ottieni voti studente - SOLO LO STUDENTE STESSO"""
    try:
        # 🔒 PRIVACY: Solo lo studente può vedere i propri voti
        if session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato: puoi vedere solo i tuoi voti'}), 403
        
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
        logger.error(
            event_type='get_grades_error',
            domain='registro',
            message='Failed to retrieve student grades',
            user_id=session.get('user_id'),
            student_id=student_id,
            route=request.path,
            error=str(e),
            exc_info=True
        )
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
        logger.error(
            event_type='insert_disciplinary_note_error',
            domain='registro',
            message='Failed to insert disciplinary note',
            user_id=session.get('user_id'),
            student_id=data.get('student_id') if 'data' in locals() else None,
            severity=data.get('severity') if 'data' in locals() else None,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500

@registro_bp.route('/api/registro/note/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_note_studente(student_id):
    """Ottieni note disciplinari studente - SOLO LO STUDENTE STESSO"""
    try:
        # 🔒 PRIVACY: Solo lo studente può vedere le proprie note
        if session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato: puoi vedere solo le tue note'}), 403
        
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
        logger.error(
            event_type='get_disciplinary_notes_error',
            domain='registro',
            message='Failed to retrieve disciplinary notes',
            user_id=session.get('user_id'),
            student_id=student_id,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500



# ============== VOTI PER MATERIA INSEGNATA ==============

@registro_bp.route('/api/registro/voti/mia-materia/<materia>', methods=['GET'])
@require_auth
@require_teacher
def get_voti_mia_materia(materia):
    """Ottieni voti studenti SOLO per la materia che insegni"""
    try:
        teacher_id = session['user_id']
        school_id = get_current_school_id()
        
        # 🔒 PRIVACY: Verifica che il prof insegni questa materia
        teacher = db_manager.query('''
            SELECT materie_insegnate, classe FROM utenti WHERE id = %s
        ''', (teacher_id,), one=True)
        
        if not teacher:
            return jsonify({'error': 'Professore non trovato'}), 404
        
        allowed_subjects = []
        if teacher.get('materie_insegnate'):
            allowed_subjects = [s.strip() for s in teacher['materie_insegnate'].split(',')]
        
        if materia not in allowed_subjects:
            return jsonify({
                'error': f'Non sei autorizzato a vedere voti per {materia}'
            }), 403
        
        # Ottieni voti SOLO per questa materia
        voti = db_manager.query('''
            SELECT 
                rv.id, rv.voto, rv.tipo, rv.description, rv.date,
                u.nome, u.cognome, u.id as student_id
            FROM registro_voti rv
            JOIN utenti u ON rv.student_id = u.id
            WHERE rv.subject = %s 
            AND u.classe = %s 
            AND u.scuola_id = %s
            ORDER BY rv.date DESC
        ''', (materia, teacher['classe'], school_id))
        
        return jsonify({
            'materia': materia,
            'voti': voti
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='get_subject_grades_error',
            domain='registro',
            message='Failed to retrieve grades for subject',
            user_id=session.get('user_id'),
            materia=materia,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500


# ============== STATISTICHE AGGREGATE CLASSE (Prof/Dirigenti) ==============

@registro_bp.route('/api/registro/statistiche/classe/<classe>', methods=['GET'])
@require_auth
@require_teacher
def get_statistiche_classe(classe):
    """Ottieni statistiche AGGREGATE della classe (senza dati individuali)"""
    try:
        school_id = get_current_school_id()
        teacher_id = session['user_id']
        
        # 🔒 PRIVACY: Se è professore, filtra per sue materie
        teacher = db_manager.query('''
            SELECT materie_insegnate, ruolo FROM utenti WHERE id = %s
        ''', (teacher_id,), one=True)
        
        # Conta studenti
        total_students = db_manager.query('''
            SELECT COUNT(*) as count FROM utenti
            WHERE classe = %s AND scuola_id = %s AND ruolo = 'studente'
        ''', (classe, school_id), one=True)
        
        # Media voti classe (aggregata) - SOLO per materie del professore
        if teacher and teacher['ruolo'] == 'professore' and teacher.get('materie_insegnate'):
            allowed_subjects = [s.strip() for s in teacher['materie_insegnate'].split(',')]
            placeholders = ','.join(['%s'] * len(allowed_subjects))
            
            avg_grades = db_manager.query(f'''
                SELECT AVG(voto) as media_classe
                FROM registro_voti rv
                JOIN utenti u ON rv.student_id = u.id
                WHERE u.classe = %s AND u.scuola_id = %s
                AND rv.subject IN ({placeholders})
            ''', tuple([classe, school_id] + allowed_subjects), one=True)
        else:
            # Dirigente vede tutte le materie
            avg_grades = db_manager.query('''
                SELECT AVG(voto) as media_classe
                FROM registro_voti rv
                JOIN utenti u ON rv.student_id = u.id
                WHERE u.classe = %s AND u.scuola_id = %s
            ''', (classe, school_id), one=True)
        
        # Tasso presenze classe (aggregato)
        attendance_rate = db_manager.query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'presente' THEN 1 ELSE 0 END) as presenti
            FROM registro_presenze rp
            JOIN utenti u ON rp.student_id = u.id
            WHERE u.classe = %s AND u.scuola_id = %s
        ''', (classe, school_id), one=True)
        
        presenza_percentuale = 0
        if attendance_rate and attendance_rate['total'] > 0:
            presenza_percentuale = round((attendance_rate['presenti'] / attendance_rate['total']) * 100, 1)
        
        # Note disciplinari totali (senza nomi)
        total_notes = db_manager.query('''
            SELECT COUNT(*) as count
            FROM registro_note_disciplinari rnd
            JOIN utenti u ON rnd.student_id = u.id
            WHERE u.classe = %s AND u.scuola_id = %s
        ''', (classe, school_id), one=True)
        
        return jsonify({
            'classe': classe,
            'totale_studenti': total_students['count'] if total_students else 0,
            'media_voti_classe': round(avg_grades['media_classe'], 2) if avg_grades and avg_grades['media_classe'] else 0,
            'tasso_presenze': presenza_percentuale,
            'note_disciplinari_totali': total_notes['count'] if total_notes else 0
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='get_class_statistics_error',
            domain='registro',
            message='Failed to retrieve class statistics',
            user_id=session.get('user_id'),
            classe=classe,
            route=request.path,
            error=str(e),
            exc_info=True
        )
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
        logger.error(
            event_type='add_lesson_error',
            domain='registro',
            message='Failed to add lesson',
            user_id=session.get('user_id'),
            classe=data.get('class') if 'data' in locals() else None,
            subject=data.get('subject') if 'data' in locals() else None,
            route=request.path,
            error=str(e),
            exc_info=True
        )
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
        logger.error(
            event_type='get_class_lessons_error',
            domain='registro',
            message='Failed to retrieve class lessons',
            user_id=session.get('user_id'),
            classe=classe,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500

# ============== STATISTICHE ==============

@registro_bp.route('/api/registro/statistiche/studente/<int:student_id>', methods=['GET'])
@require_auth
def get_statistiche_studente(student_id):
    """Ottieni report completo studente - SOLO LO STUDENTE STESSO"""
    try:
        # 🔒 PRIVACY: Solo lo studente può vedere il proprio report completo
        if session.get('user_id') != student_id:
            return jsonify({'error': 'Accesso negato: puoi vedere solo il tuo report'}), 403
        
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
        logger.error(
            event_type='get_student_statistics_error',
            domain='registro',
            message='Failed to retrieve student statistics',
            user_id=session.get('user_id'),
            student_id=student_id,
            route=request.path,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': str(e)}), 500
