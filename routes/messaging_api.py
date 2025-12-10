"""
SKAJLA - Messaging API Routes
API endpoints per sistema messaggistica
"""

from flask import Blueprint, jsonify, session
from database_manager import db_manager

messaging_api_bp = Blueprint('messaging_api', __name__, url_prefix='/api')


@messaging_api_bp.route('/chat/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    """Ottieni messaggi di una chat"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    # Verifica che l'utente sia membro della chat
    is_member = db_manager.query('''
        SELECT 1 FROM partecipanti_chat 
        WHERE chat_id = %s AND utente_id = %s
    ''', (chat_id, session['user_id']), one=True)
    
    if not is_member:
        return jsonify({'error': 'Non autorizzato'}), 403
    
    # Carica ultimi 100 messaggi
    messages = db_manager.query('''
        SELECT m.*, u.nome, u.cognome, u.username, u.ruolo
        FROM messaggi m
        JOIN utenti u ON m.utente_id = u.id
        WHERE m.chat_id = %s
        ORDER BY m.timestamp DESC
        LIMIT 100
    ''', (chat_id,)) or []
    
    # Reverse per mostrare dal più vecchio al più recente
    messages.reverse()
    
    return jsonify({
        'success': True,
        'messages': messages,
        'chat_id': chat_id
    })


@messaging_api_bp.route('/chat/<int:chat_id>/info', methods=['GET'])
def get_chat_info(chat_id):
    """Ottieni informazioni chat"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    chat = db_manager.query('''
        SELECT c.*, COUNT(pc.utente_id) as membri_count
        FROM chat c
        LEFT JOIN partecipanti_chat pc ON c.id = pc.chat_id
        WHERE c.id = %s
        GROUP BY c.id
    ''', (chat_id,), one=True)
    
    if not chat:
        return jsonify({'error': 'Chat non trovata'}), 404
    
    # Membri
    membri = db_manager.query('''
        SELECT u.id, u.nome, u.cognome, u.username, u.ruolo, u.avatar
        FROM utenti u
        JOIN partecipanti_chat pc ON u.id = pc.utente_id
        WHERE pc.chat_id = %s
        ORDER BY u.nome, u.cognome
    ''', (chat_id,)) or []
    
    return jsonify({
        'success': True,
        'chat': chat,
        'membri': membri
    })
