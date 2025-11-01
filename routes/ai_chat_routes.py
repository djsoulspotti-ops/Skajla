"""
SKAILA - AI Chat Routes
API endpoints per AI Coach
"""

from flask import Blueprint, jsonify, session, request
from ai_chatbot import ai_bot
from shared.middleware.feature_guard import check_feature_enabled, Features
from services.tenant_guard import get_current_school_id

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
    except Exception:
        pass


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
    except Exception:
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
        print(f"❌ Error in AI chat: {e}")
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
