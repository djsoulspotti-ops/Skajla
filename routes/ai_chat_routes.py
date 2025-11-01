"""
SKAILA - AI Chat Routes
API endpoints per AI Coach
"""

from flask import Blueprint, jsonify, session, request
from ai_chatbot import ai_bot
from shared.middleware.feature_guard import require_feature, Features

ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/api/ai')


@ai_chat_bp.route('/chat', methods=['POST'])
@require_feature(Features.AI_COACH)
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
