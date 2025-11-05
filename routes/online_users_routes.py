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
