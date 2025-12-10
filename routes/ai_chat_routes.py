"""
SKAJLA - AI Chat Routes
API endpoints per AI Coach with Gemini + Gamification
"""

from flask import Blueprint, jsonify, session, request
from services.ai.gemini_chatbot import gemini_chatbot
from shared.middleware.feature_guard import check_feature_enabled, Features
from services.tenant_guard import get_current_school_id
from shared.error_handling.structured_logger import get_logger
from services.telemetry.telemetry_engine import telemetry_engine

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
    """Endpoint per chattare con AI Coach - Gemini + Gamification"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
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
    
    try:
        result = gemini_chatbot.generate_response(
            message=message,
            user_id=session['user_id'],
            user_name=session.get('nome', 'Studente'),
            user_role=session.get('ruolo', 'studente')
        )
        
        try:
            telemetry_engine.track_event(
                user_id=session['user_id'],
                event_type='ai_intervention',
                context={
                    'message_length': len(message),
                    'response_length': len(result.get('response', '')),
                    'xp_awarded': result.get('xp_awarded', 0),
                    'ai_mode': result.get('ai_mode', 'unknown'),
                    'user_role': session.get('ruolo', 'studente'),
                    'source': 'server'
                },
                duration_seconds=None,
                accuracy_score=None
            )
        except Exception as telemetry_error:
            logger.warning(
                event_type='ai_telemetry_failed',
                domain='ai_chat',
                error=str(telemetry_error)
            )
        
        return jsonify({
            'success': True,
            'response': result.get('response', ''),
            'xp_awarded': result.get('xp_awarded', 0),
            'rank_up': result.get('rank_up', False),
            'new_rank': result.get('new_rank'),
            'gamification': result.get('gamification', {}),
            'ai_mode': result.get('ai_mode', 'mock'),
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
    """Ottieni suggerimenti personalizzati basati su gamification"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    suggestions = gemini_chatbot.get_study_suggestions(session['user_id'])
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })
