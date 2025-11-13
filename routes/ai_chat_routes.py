"""
SKAILA - AI Chat Routes
API endpoints per AI Coach
"""

from flask import Blueprint, jsonify, session, request
from ai_chatbot import ai_bot
from shared.middleware.feature_guard import check_feature_enabled, Features
from services.tenant_guard import get_current_school_id
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)

ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/api/ai')

@ai_chat_bp.before_request
def check_ai_coach_feature():
    """Verifica che AI Coach sia abilitato prima di ogni request"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    try:
        school_id = get_current_school_id()
        if not check_feature_enabled(school_id, Features.AI_COACH):
            return jsonify({
                'error': 'Feature non disponibile',
                'message': 'AI Coach non è disponibile per la tua scuola.',
                'feature': Features.AI_COACH,
                'upgrade_required': True
            }), 403
    except Exception as e:
        logger.error(
            event_type='feature_check_failed',
            domain='ai_chat',
            message='Failed to check AI Coach feature availability',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            'error': 'Errore di sistema',
            'message': 'Impossibile verificare disponibilità feature. Riprova più tardi.'
        }), 500


@ai_chat_bp.route('/chat', methods=['POST'])
def chat_with_ai():
    """Endpoint per chattare con AI Coach"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    # Defensive handling per JSON malformato
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Payload vuoto'}), 400
    except Exception as e:
        logger.warning(
            event_type='invalid_json_payload',
            domain='ai_chat',
            message='Invalid JSON payload received',
            error=str(e)
        )
        return jsonify({'error': 'JSON non valido'}), 400
    
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Messaggio vuoto'}), 400
    
    # Genera risposta AI personalizzata
    try:
        response = ai_bot.generate_response(
            message=message,
            user_name=session.get('nome', 'Studente'),
            user_role=session.get('ruolo', 'studente'),
            user_id=session['user_id']
        )
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': 'now'
        })
    
    except Exception as e:
        logger.error(
            event_type='ai_chat_error',
            domain='ai_chat',
            message='Error generating AI chat response',
            user_id=session.get('user_id'),
            error=str(e),
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'Errore nel generare risposta'
        }), 500


@ai_chat_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """Ottieni suggerimenti intelligenti per l'utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    suggestions = [
        "Come posso migliorare il mio metodo di studio?",
        "Dammi consigli per gestire lo stress pre-esame",
        "Come posso organizzare meglio il mio tempo?",
        "Aiutami a definire obiettivi di studio chiari"
    ]
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })
