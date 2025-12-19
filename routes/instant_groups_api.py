"""
Instant Groups API Routes
API endpoints per gestione gruppi istantanei
"""

from flask import Blueprint, request, jsonify, session
from shared.middleware.auth import require_login
from services.tenant_guard import get_current_school_id
from services.messaging.instant_groups_service import instant_groups_service
from gamification import gamification_system
import logging

logger = logging.getLogger(__name__)

instant_groups_api_bp = Blueprint('instant_groups_api', __name__, url_prefix='/api/chat/instant')


@instant_groups_api_bp.route('/create', methods=['POST'])
@require_login
def create_instant_group():
    """
    Crea nuovo gruppo istantaneo
    
    Body:
    {
        "nome": "Studio Matematica",
        "argomento": "matematica",
        "descrizione": "Ripasso per esame",
        "durata_ore": 24,
        "pubblico": false,
        "invitati": [user_id1, user_id2, ...]
    }
    """
    try:
        data = request.get_json()
        user_id = session['user_id']
        school_id = get_current_school_id()
        
        # Validazioni
        if not data.get('nome'):
            return jsonify({'success': False, 'error': 'Nome richiesto'}), 400
        
        if not data.get('argomento'):
            return jsonify({'success': False, 'error': 'Argomento richiesto'}), 400
        
        # Crea gruppo
        result = instant_groups_service.create_instant_group(
            nome=data['nome'],
            creatore_id=user_id,
            school_id=school_id,
            argomento=data['argomento'],
            descrizione=data.get('descrizione', ''),
            durata_ore=data.get('durata_ore', 24),
            pubblico=data.get('pubblico', False),
            invitati=data.get('invitati', [])
        )
        
        # Award XP per creazione gruppo
        gamification_system.award_xp(
            user_id=user_id,
            amount=10,
            reason=f"Creato gruppo istantaneo: {data['nome']}"
        )
        
        logger.info(f"Gruppo istantaneo creato da user {user_id}: {result['chat_id']}")
        
        return jsonify({
            'success': True,
            'gruppo': result
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Errore creazione gruppo istantaneo: {e}")
        return jsonify({'success': False, 'error': 'Errore server'}), 500


@instant_groups_api_bp.route('/list', methods=['GET'])
@require_login
def list_instant_groups():
    """
    Lista gruppi istantanei disponibili
    
    Returns:
    {
        "miei_gruppi": [...],
        "gruppi_partecipante": [...],
        "gruppi_pubblici": [...]
    }
    """
    try:
        user_id = session['user_id']
        school_id = get_current_school_id()
        
        gruppi = instant_groups_service.get_instant_groups(user_id, school_id)
        
        return jsonify({
            'success': True,
            **gruppi
        }), 200
        
    except Exception as e:
        logger.error(f"Errore lista gruppi istantanei: {e}")
        return jsonify({'success': False, 'error': 'Errore server'}), 500


@instant_groups_api_bp.route('/join/<int:chat_id>', methods=['POST'])
@require_login
def join_instant_group(chat_id):
    """Unisciti a gruppo pubblico"""
    try:
        user_id = session['user_id']
        
        instant_groups_service.join_instant_group(chat_id, user_id)
        
        # Award XP per partecipazione
        gamification_system.award_xp(
            user_id=user_id,
            amount=5,
            reason=f"Unito a gruppo istantaneo"
        )
        
        return jsonify({
            'success': True,
            'message': 'Unito al gruppo con successo'
        }), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Errore join gruppo: {e}")
        return jsonify({'success': False, 'error': 'Errore server'}), 500


@instant_groups_api_bp.route('/leave/<int:chat_id>', methods=['POST'])
@require_login
def leave_instant_group(chat_id):
    """Lascia gruppo istantaneo"""
    try:
        user_id = session['user_id']
        
        instant_groups_service.leave_instant_group(chat_id, user_id)
        
        return jsonify({
            'success': True,
            'message': 'Hai lasciato il gruppo'
        }), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Errore leave gruppo: {e}")
        return jsonify({'success': False, 'error': 'Errore server'}), 500


@instant_groups_api_bp.route('/delete/<int:chat_id>', methods=['DELETE'])
@require_login
def delete_instant_group(chat_id):
    """Elimina gruppo istantaneo (solo creatore)"""
    try:
        user_id = session['user_id']
        
        instant_groups_service.delete_instant_group(chat_id, user_id)
        
        return jsonify({
            'success': True,
            'message': 'Gruppo eliminato con successo'
        }), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Errore delete gruppo: {e}")
        return jsonify({'success': False, 'error': 'Errore server'}), 500


@instant_groups_api_bp.route('/invite', methods=['POST'])
@require_login
def invite_to_instant_group():
    """
    Invita utenti a gruppo privato
    
    Body:
    {
        "chat_id": 123,
        "user_ids": [456, 789]
    }
    """
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        chat_id = data.get('chat_id')
        user_ids = data.get('user_ids', [])
        
        if not chat_id or not user_ids:
            return jsonify({'success': False, 'error': 'chat_id e user_ids richiesti'}), 400
        
        # TODO: Implementa logica inviti
        # Per ora placeholder
        
        return jsonify({
            'success': True,
            'message': f'{len(user_ids)} inviti inviati'
        }), 200
        
    except Exception as e:
        logger.error(f"Errore inviti gruppo: {e}")
        return jsonify({'success': False, 'error': 'Errore server'}), 500


@instant_groups_api_bp.route('/cleanup', methods=['POST'])
@require_login
def manual_cleanup():
    """
    Cleanup manuale gruppi scaduti (solo admin)
    """
    try:
        if session.get('ruolo') != 'admin':
            return jsonify({'success': False, 'error': 'Non autorizzato'}), 403
        
        expired = instant_groups_service.cleanup_expired_groups()
        inactive = instant_groups_service.cleanup_inactive_groups()
        
        return jsonify({
            'success': True,
            'gruppi_scaduti_eliminati': expired,
            'gruppi_inattivi_eliminati': inactive
        }), 200
        
    except Exception as e:
        logger.error(f"Errore cleanup: {e}")
        return jsonify({'success': False, 'error': 'Errore server'}), 500
