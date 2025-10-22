"""
Routes per Dashboard Admin e Calendario
"""

from flask import Blueprint, render_template, jsonify, request, session
from functools import wraps
from admin_dashboard import admin_dashboard
from calendario_integration import calendario
from coaching_engine import coaching_engine

admin_calendar_bp = Blueprint('admin_calendar', __name__)

def admin_required(f):
    """Decorator per proteggere routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Non autorizzato'}), 401
        
        user_role = session.get('ruolo')
        if user_role not in ['dirigente', 'professore', 'admin']:
            return jsonify({'error': 'Accesso riservato a dirigenti/professori'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Decorator per proteggere routes che richiedono login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login richiesto'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# DASHBOARD ADMIN ROUTES
# ============================================================================

@admin_calendar_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard_page():
    """Pagina dashboard amministrativa"""
    return render_template('dashboard_admin.html')

@admin_calendar_bp.route('/api/admin/overview')
@admin_required
def get_admin_overview():
    """API: Ottiene overview completo dashboard"""
    try:
        days = request.args.get('days', 30, type=int)
        overview = admin_dashboard.get_dashboard_overview(days)
        return jsonify(overview)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/admin/alerts')
@admin_required
def get_active_alerts_api():
    """API: Ottiene alert attivi studenti"""
    try:
        alerts = admin_dashboard.get_active_alerts()
        return jsonify({'alerts': alerts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/admin/statistics')
@admin_required
def get_statistics_api():
    """API: Statistiche generali coaching"""
    try:
        days = request.args.get('days', 30, type=int)
        stats = admin_dashboard.get_coaching_statistics(days)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/admin/top-issues')
@admin_required
def get_top_issues_api():
    """API: Problemi più frequenti"""
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 5, type=int)
        issues = admin_dashboard.get_top_issues(days, limit)
        return jsonify({'issues': issues})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/admin/sentiment')
@admin_required
def get_sentiment_distribution_api():
    """API: Distribuzione sentiment studenti"""
    try:
        days = request.args.get('days', 30, type=int)
        sentiment = admin_dashboard.get_sentiment_distribution(days)
        return jsonify(sentiment)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/admin/students-at-risk')
@admin_required
def get_students_at_risk_api():
    """API: Studenti a rischio"""
    try:
        limit = request.args.get('limit', 10, type=int)
        students = admin_dashboard.get_students_at_risk(limit)
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CALENDARIO ROUTES
# ============================================================================

@admin_calendar_bp.route('/calendario')
@login_required
def calendario_page():
    """Pagina calendario studente"""
    return render_template('calendario.html')

@admin_calendar_bp.route('/api/calendario/events')
@login_required
def get_upcoming_events():
    """API: Ottiene eventi prossimi per studente"""
    try:
        user_id = session.get('user_id')
        days = request.args.get('days', 14, type=int)
        
        events = calendario.get_upcoming_events(user_id, days)
        return jsonify({'events': events})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/calendario/deadlines')
@login_required
def get_critical_deadlines():
    """API: Ottiene scadenze critiche"""
    try:
        user_id = session.get('user_id')
        days = request.args.get('days', 7, type=int)
        
        deadlines = calendario.get_critical_deadlines(user_id, days)
        return jsonify({'deadlines': deadlines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/calendario/study-load')
@login_required
def get_study_load():
    """API: Calcola carico studio"""
    try:
        user_id = session.get('user_id')
        load = calendario.calculate_study_load(user_id)
        return jsonify(load)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/calendario/smart-schedule')
@login_required
def generate_smart_schedule():
    """API: Genera schedule studio intelligente"""
    try:
        user_id = session.get('user_id')
        
        # Ottieni dati studente dal coaching engine
        student_data = coaching_engine.analyze_student_ecosystem(user_id)
        
        # Genera schedule
        schedule = calendario.generate_smart_schedule(user_id, student_data)
        return jsonify(schedule)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/calendario/add-event', methods=['POST'])
@login_required
def add_event():
    """API: Aggiunge evento al calendario"""
    try:
        user_id = session.get('user_id')
        data = request.json
        
        # Aggiungi user_id all'evento
        data['studente_id'] = user_id
        
        success = calendario.add_event(data)
        
        if success:
            return jsonify({'success': True, 'message': 'Evento aggiunto'})
        else:
            return jsonify({'success': False, 'error': 'Errore aggiunta evento'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_calendar_bp.route('/api/calendario/complete-event/<int:event_id>', methods=['POST'])
@login_required
def complete_event(event_id):
    """API: Marca evento come completato"""
    try:
        user_id = session.get('user_id')
        success = calendario.mark_completed(event_id, user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Evento completato'})
        else:
            return jsonify({'success': False, 'error': 'Errore completamento'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
