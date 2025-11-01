
"""
SKAILA - Routes Crediti
Gestione visualizzazione crediti e monete utente
"""

from flask import Blueprint, render_template, session, redirect, jsonify, flash, request
from database_manager import db_manager
from gamification import gamification_system
from shared.middleware.feature_guard import check_feature_enabled, Features
from services.tenant_guard import get_current_school_id

credits_bp = Blueprint('credits', __name__)

@credits_bp.before_request
def check_gamification_feature():
    """Verifica che Gamification sia abilitata prima di ogni request"""
    if 'user_id' not in session:
        return  # Auth middleware gestirà questo
    
    try:
        school_id = get_current_school_id()
        if not check_feature_enabled(school_id, Features.GAMIFICATION):
            # API endpoint - ritorna JSON 403
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Feature non disponibile',
                    'message': 'La Gamification non è disponibile per la tua scuola.',
                    'feature': Features.GAMIFICATION,
                    'upgrade_required': True
                }), 403
            # Web endpoint - redirect con flash
            flash('⚠️ La Gamification non è disponibile per la tua scuola.', 'warning')
            return redirect('/dashboard')
    except Exception:
        pass

@credits_bp.route('/crediti')
def view_credits():
    """Visualizza crediti utente"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    # Ottieni profilo gamification
    profile = gamification_system.get_or_create_profile(user_id)
    
    # Ottieni statistiche dettagliate
    today_xp_result = db_manager.query('''
        SELECT COALESCE(SUM(xp_earned), 0) as total
        FROM xp_activity_log 
        WHERE user_id = %s AND DATE(timestamp) = CURRENT_DATE
    ''', (user_id,), one=True)
    today_xp = today_xp_result['total'] if today_xp_result else 0
    
    week_xp_result = db_manager.query('''
        SELECT COALESCE(SUM(xp_earned), 0) as total
        FROM xp_activity_log 
        WHERE user_id = %s AND timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
    ''', (user_id,), one=True)
    week_xp = week_xp_result['total'] if week_xp_result else 0
    
    recent_activities = db_manager.query('''
        SELECT action_type, xp_earned, description, timestamp
        FROM xp_activity_log
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (user_id,)) or []
    
    # Calcola livello successivo e progresso
    current_level = profile['current_level']
    current_xp = profile['total_xp']
    
    # Trova soglia prossimo livello
    next_level_xp = None
    for level, threshold in gamification_system.level_thresholds.items():
        if level > current_level:
            next_level_xp = threshold
            break
    
    if next_level_xp:
        xp_needed = next_level_xp - current_xp
        progress_percentage = (current_xp / next_level_xp) * 100
    else:
        xp_needed = 0
        progress_percentage = 100
    
    credits_data = {
        'avatar_coins': profile['avatar_coins'],
        'total_xp': current_xp,
        'current_level': current_level,
        'level_title': gamification_system.level_titles.get(current_level, f"Livello {current_level}"),
        'xp_today': today_xp,
        'xp_this_week': week_xp,
        'xp_needed_next_level': xp_needed,
        'level_progress': round(progress_percentage, 1),
        'recent_activities': recent_activities
    }
    
    return render_template('credits_page.html', 
                         user=session, 
                         credits=credits_data)

@credits_bp.route('/api/crediti')
def api_credits():
    """API per ottenere crediti in formato JSON"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401
    
    user_id = session['user_id']
    profile = gamification_system.get_or_create_profile(user_id)
    
    return jsonify({
        'avatar_coins': profile['avatar_coins'],
        'total_xp': profile['total_xp'],
        'current_level': profile['current_level'],
        'current_streak': profile['current_streak']
    })
