"""
SKAJLA Parent Dashboard - API Routes
Provides endpoints for parent-student linking and child monitoring
"""

from flask import Blueprint, request, jsonify, session, render_template
from services.parent.parent_manager import ParentManager
from shared.middleware.auth import require_login, require_role
from shared.error_handling import get_logger

logger = get_logger(__name__)
parent_bp = Blueprint('parent', __name__)
parent_manager = ParentManager()


@parent_bp.route('/parent/dashboard')
@require_login
@require_role('genitore')
def parent_dashboard():
    """
    Main Parent Dashboard - Mission Control for monitoring children
    """
    user_id = session.get('user_id')
    
    # Get all linked children
    children = parent_manager.get_linked_children(user_id)
    
    # Check if this is first time (no children linked yet)
    is_onboarding = len(children) == 0
    
    return render_template('parent_dashboard.html',
                         user=session,
                         children=children,
                         is_onboarding=is_onboarding)


@parent_bp.route('/parent/onboarding')
@require_login
@require_role('genitore')
def parent_onboarding():
    """
    Onboarding screen for parents to link their first child
    """
    return render_template('parent_onboarding.html', user=session)


# ==================== API ENDPOINTS ====================

@parent_bp.route('/api/parent/link-child', methods=['POST'])
@require_login
@require_role('genitore')
def link_child():
    """
    Link parent to student using student's identification code
    
    POST Body:
        {
            "student_code": "STU-2024-12345"
        }
    
    Returns:
        {
            "success": true,
            "message": "Collegamento effettuato con Mario Rossi",
            "student": { ... }
        }
    """
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        student_code = data.get('student_code', '').strip()
        
        if not student_code:
            return jsonify({
                'success': False,
                'error': 'Missing Code',
                'message': 'Inserisci il codice identificativo dello studente'
            }), 400
        
        # Link parent to student
        result = parent_manager.link_parent_to_student(user_id, student_code)
        
        if result['success']:
            logger.info(
                event_type='parent_child_linked',
                domain='parent',
                parent_id=user_id,
                student_code=student_code
            )
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(
            event_type='link_child_api_failed',
            domain='parent',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore durante il collegamento. Riprova.'
        }), 500


@parent_bp.route('/api/parent/children', methods=['GET'])
@require_login
@require_role('genitore')
def get_children():
    """
    Get all children linked to this parent account
    
    Returns:
        {
            "success": true,
            "children": [
                {
                    "id": 123,
                    "nome": "Mario",
                    "cognome": "Rossi",
                    "classe": "3A",
                    "avatar": "/static/avatars/default.png",
                    "identification_code": "STU-2024-12345"
                }
            ]
        }
    """
    try:
        user_id = session.get('user_id')
        children = parent_manager.get_linked_children(user_id)
        
        return jsonify({
            'success': True,
            'children': children
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='get_children_api_failed',
            domain='parent',
            error=str(e)
        )
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore nel caricamento dei figli'
        }), 500


@parent_bp.route('/api/parent/child/<int:student_id>/overview', methods=['GET'])
@require_login
@require_role('genitore')
def get_child_overview(student_id):
    """
    Get comprehensive overview of a specific child
    (Grades, Attendance, Teacher Notes)
    
    Returns:
        {
            "success": true,
            "data": {
                "student": { ... },
                "grades": [ ... ],
                "attendance": { "assenze": 2, "ritardi": 1, "presenze": 25 },
                "notes": [ ... ],
                "average_grade": 7.5
            }
        }
    """
    try:
        user_id = session.get('user_id')
        
        # Get child overview (with authorization check)
        overview = parent_manager.get_child_overview(user_id, student_id)
        
        if not overview:
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': 'Non hai accesso ai dati di questo studente'
            }), 403
        
        return jsonify({
            'success': True,
            'data': overview
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='get_child_overview_api_failed',
            domain='parent',
            student_id=student_id,
            error=str(e)
        )
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore nel caricamento dei dati'
        }), 500


@parent_bp.route('/api/parent/child/<int:student_id>/unlink', methods=['POST'])
@require_login
@require_role('genitore')
def unlink_child(student_id):
    """
    Remove link between parent and student
    
    Returns:
        {
            "success": true,
            "message": "Collegamento rimosso"
        }
    """
    try:
        user_id = session.get('user_id')
        
        success = parent_manager.unlink_child(user_id, student_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Collegamento rimosso con successo'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Unlink Failed',
                'message': 'Errore durante la rimozione del collegamento'
            }), 400
            
    except Exception as e:
        logger.error(
            event_type='unlink_child_api_failed',
            domain='parent',
            student_id=student_id,
            error=str(e)
        )
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore durante la rimozione del collegamento'
        }), 500


@parent_bp.route('/api/parent/student/<int:student_id>/code', methods=['GET'])
@require_login
def get_student_code(student_id):
    """
    Get identification code for a student (for sharing with parents)
    Only accessible by the student themselves or school admin
    """
    try:
        user_id = session.get('user_id')
        ruolo = session.get('ruolo')
        
        # Only student themselves or admin can see the code
        if ruolo == 'studente' and user_id != student_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': 'Non autorizzato'
            }), 403
        
        if ruolo not in ['studente', 'dirigente', 'docente']:
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': 'Non autorizzato'
            }), 403
        
        code = parent_manager.get_student_code(student_id)
        
        if not code:
            return jsonify({
                'success': False,
                'error': 'Not Found',
                'message': 'Codice non trovato'
            }), 404
        
        return jsonify({
            'success': True,
            'code': code,
            'message': 'Condividi questo codice con i tuoi genitori'
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='get_student_code_api_failed',
            domain='parent',
            student_id=student_id,
            error=str(e)
        )
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore nel recupero del codice'
        }), 500
