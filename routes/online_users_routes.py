"""
SKAILA - Online Users API
Real-time online presence tracking for circulating avatars
"""

from flask import Blueprint, jsonify, session
from database_manager import db_manager
from services.tenant_guard import get_current_school_id, TenantGuardException
from shared.middleware.auth import require_auth

online_users_bp = Blueprint('online_users', __name__)

@online_users_bp.route('/api/online-users', methods=['GET'])
@require_auth
def get_online_users():
    """
    Get list of currently online users in the same school
    Returns user IDs, names, and avatar data for circulating animation
    """
    try:
        school_id = get_current_school_id()
        current_user_id = session.get('user_id')
        
        # Query online users from same school (exclude current user)
        online_users = db_manager.query('''
            SELECT 
                id,
                nome,
                cognome,
                ruolo,
                email
            FROM utenti
            WHERE scuola_id = %s 
            AND status_online = TRUE
            AND id != %s
            ORDER BY RANDOM()
            LIMIT 7
        ''', (school_id, current_user_id))
        
        if not online_users:
            return jsonify({'users': []})
        
        # Format response with avatar initials
        formatted_users = []
        for user in online_users:
            formatted_users.append({
                'id': user['id'],
                'name': f"{user['nome']} {user['cognome']}",
                'initials': f"{user['nome'][0]}{user['cognome'][0]}".upper(),
                'role': user['ruolo'],
                'avatar_color': generate_avatar_color(user['id'])
            })
        
        return jsonify({'users': formatted_users})
    
    except TenantGuardException:
        return jsonify({'error': 'School ID not found'}), 403
    except Exception as e:
        print(f"❌ Error fetching online users: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@online_users_bp.route('/api/online-classmates', methods=['GET'])
@require_auth
def get_online_classmates():
    """
    Get list of currently online users in the SAME CLASS (class-level privacy)
    CRITICAL: Only returns users sharing the exact same classe_id as the logged-in user
    Returns user IDs, names, and avatar data for spiral visualization
    """
    try:
        school_id = get_current_school_id()
        current_user_id = session.get('user_id')
        
        # Get current user's class ID
        current_user = db_manager.query('''
            SELECT classe_id 
            FROM utenti 
            WHERE id = %s
        ''', (current_user_id,), one=True)
        
        if not current_user or not current_user.get('classe_id'):
            return jsonify({'classmates': [], 'message': 'User has no class assigned'})
        
        classe_id = current_user['classe_id']
        
        # Query online classmates: SAME school + SAME class + online + exclude self
        online_classmates = db_manager.query('''
            SELECT 
                id,
                nome,
                cognome,
                ruolo,
                classe_id
            FROM utenti
            WHERE scuola_id = %s 
            AND classe_id = %s
            AND status_online = TRUE
            AND id != %s
            ORDER BY nome, cognome
            LIMIT 20
        ''', (school_id, classe_id, current_user_id))
        
        if not online_classmates:
            return jsonify({'classmates': [], 'total': 0})
        
        # Format response with avatar initials
        formatted_classmates = []
        for classmate in online_classmates:
            formatted_classmates.append({
                'id': classmate['id'],
                'name': f"{classmate['nome']} {classmate['cognome']}",
                'initials': f"{classmate['nome'][0]}{classmate['cognome'][0]}".upper(),
                'role': classmate['ruolo'],
                'avatar_color': generate_avatar_color(classmate['id'])
            })
        
        return jsonify({
            'classmates': formatted_classmates, 
            'total': len(formatted_classmates),
            'classe_id': classe_id
        })
    
    except TenantGuardException:
        return jsonify({'error': 'School ID not found'}), 403
    except Exception as e:
        print(f"❌ Error fetching online classmates: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def generate_avatar_color(user_id):
    """Generate consistent color for user avatar based on ID"""
    colors = [
        '#003B73',  # Navy blue
        '#0074D9',  # Blue
        '#7FDBFF',  # Light blue
        '#39CCCC',  # Teal
        '#3D9970',  # Olive
        '#2ECC40',  # Green
        '#FF851B',  # Orange
        '#FF4136',  # Red
        '#85144b',  # Maroon
        '#F012BE',  # Fuchsia
        '#B10DC9',  # Purple
    ]
    return colors[user_id % len(colors)]
