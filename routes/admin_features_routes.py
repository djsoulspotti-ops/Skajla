
"""
SKAJLA - Admin Features Routes
Route per presidi/admin per gestire feature abilitate
"""

from flask import Blueprint, render_template, session, request, jsonify, redirect
from services.school.school_features_manager import school_features_manager
from services.tenant_guard import get_current_school_id
from shared.middleware.auth import require_login

admin_features_bp = Blueprint('admin_features', __name__)

@admin_features_bp.route('/admin/features')
@require_login
def admin_features_page():
    """Pagina gestione feature per preside"""
    if session.get('ruolo') not in ['admin', 'dirigente']:
        return redirect('/dashboard')
    
    school_id = get_current_school_id()
    enabled_features = school_features_manager.get_school_features(school_id)
    available_features = school_features_manager.AVAILABLE_FEATURES
    
    return render_template('admin_features.html',
                         user=session,
                         enabled_features=enabled_features,
                         available_features=available_features)

@admin_features_bp.route('/api/admin/features/toggle', methods=['POST'])
@require_login
def toggle_feature():
    """Toggle feature on/off"""
    if session.get('ruolo') not in ['admin', 'dirigente']:
        return jsonify({'error': 'Non autorizzato'}), 403
    
    data = request.get_json()
    feature_name = data.get('feature_name')
    enabled = data.get('enabled', False)
    
    school_id = get_current_school_id()
    admin_id = session['user_id']
    
    if enabled:
        success = school_features_manager.enable_feature(school_id, feature_name, admin_id)
    else:
        success = school_features_manager.disable_feature(school_id, feature_name, admin_id)
    
    if success:
        return jsonify({'success': True, 'message': f'Feature {feature_name} aggiornata'})
    else:
        return jsonify({'error': 'Errore nell\'aggiornamento'}), 500

@admin_features_bp.route('/api/admin/features/gamification-only', methods=['POST'])
@require_login
def set_gamification_only():
    """Modalità 'Solo Gamification'"""
    if session.get('ruolo') not in ['admin', 'dirigente']:
        return jsonify({'error': 'Non autorizzato'}), 403
    
    school_id = get_current_school_id()
    admin_id = session['user_id']
    
    success = school_features_manager.set_gamification_only(school_id, admin_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Modalità Solo Gamification attivata'})
    else:
        return jsonify({'error': 'Errore configurazione'}), 500
