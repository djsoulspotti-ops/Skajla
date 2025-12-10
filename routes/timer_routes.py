"""
SKAJLA - Study Timer Routes
API endpoints per gestione timer studio
"""

from flask import Blueprint, request, session, jsonify
from services.study_timer import study_timer
from shared.middleware.auth import require_login

timer_bp = Blueprint('timer', __name__, url_prefix='/api/timer')


@timer_bp.route('/start', methods=['POST'])
@require_login
def start_timer():
    """Inizia nuova sessione studio"""
    data = request.get_json() or {}
    
    user_id = session['user_id']
    subject = data.get('subject')
    session_type = data.get('session_type', 'focus')
    
    result = study_timer.start_session(user_id, subject, session_type)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@timer_bp.route('/stop', methods=['POST'])
@require_login
def stop_timer():
    """Termina sessione studio corrente"""
    data = request.get_json() or {}
    
    user_id = session['user_id']
    notes = data.get('notes')
    
    result = study_timer.stop_session(user_id, notes)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@timer_bp.route('/pause', methods=['POST'])
@require_login
def pause_timer():
    """Mette in pausa sessione attiva"""
    user_id = session['user_id']
    
    result = study_timer.pause_session(user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@timer_bp.route('/resume', methods=['POST'])
@require_login
def resume_timer():
    """Riprende sessione in pausa"""
    user_id = session['user_id']
    
    result = study_timer.resume_session(user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@timer_bp.route('/active', methods=['GET'])
@require_login
def get_active():
    """Ottiene sessione attualmente attiva"""
    user_id = session['user_id']
    
    session_data = study_timer.get_active_session(user_id)
    
    if session_data:
        return jsonify({
            'success': True,
            'session': session_data
        }), 200
    else:
        return jsonify({
            'success': True,
            'session': None
        }), 200


@timer_bp.route('/stats', methods=['GET'])
@require_login
def get_stats():
    """Ottiene statistiche sessioni studio"""
    user_id = session['user_id']
    days = request.args.get('days', 7, type=int)
    
    stats = study_timer.get_user_stats(user_id, days)
    
    return jsonify({
        'success': True,
        'stats': stats
    }), 200


@timer_bp.route('/history', methods=['GET'])
@require_login
def get_history():
    """Ottiene storico sessioni"""
    user_id = session['user_id']
    limit = request.args.get('limit', 10, type=int)
    
    sessions = study_timer.get_recent_sessions(user_id, limit)
    
    return jsonify({
        'success': True,
        'sessions': sessions
    }), 200


@timer_bp.route('/types', methods=['GET'])
@require_login
def get_session_types():
    """Ottiene tipi di sessione disponibili"""
    return jsonify({
        'success': True,
        'types': study_timer.session_types
    }), 200
