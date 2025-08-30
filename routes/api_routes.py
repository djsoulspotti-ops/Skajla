
"""
SKAILA - API Routes
Tutte le API REST centralizzate
"""

from flask import Blueprint, request, session, jsonify
from database_manager import db_manager
from cache_manager import cache_manager
from gamification import gamification_system
from ai_chatbot import AISkailaBot
import time

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Inizializza AI bot
ai_bot = AISkailaBot()

@api_bp.route('/conversations')
def conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        user_id = session['user_id']
        user_role = session['ruolo']
        cache_key = f"conversations_{user_id}_{user_role}"
        
        # Controlla cache
        cached = cache_manager.get_user_data(user_id, 'conversations')
        if cached:
            return jsonify(cached)

        with db_manager.get_connection() as conn:
            if user_role == 'admin':
                conversations = conn.execute('''
                    SELECT c.*, 
                           COUNT(DISTINCT pc.utente_id) as partecipanti_count,
                           m.contenuto as ultimo_messaggio,
                           m.timestamp as ultimo_messaggio_data,
                           u.nome || ' ' || u.cognome as ultimo_mittente
                    FROM chat c
                    LEFT JOIN partecipanti_chat pc ON c.id = pc.chat_id
                    LEFT JOIN messaggi m ON c.id = m.chat_id 
                        AND m.timestamp = (SELECT MAX(timestamp) FROM messaggi WHERE chat_id = c.id)
                    LEFT JOIN utenti u ON m.utente_id = u.id
                    GROUP BY c.id
                    ORDER BY ultimo_messaggio_data DESC NULLS LAST
                ''').fetchall()
            else:
                conversations = conn.execute('''
                    SELECT c.*, 
                           COUNT(DISTINCT pc.utente_id) as partecipanti_count,
                           m.contenuto as ultimo_messaggio,
                           m.timestamp as ultimo_messaggio_data,
                           u.nome || ' ' || u.cognome as ultimo_mittente
                    FROM chat c
                    JOIN partecipanti_chat pc ON c.id = pc.chat_id
                    LEFT JOIN messaggi m ON c.id = m.chat_id 
                        AND m.timestamp = (SELECT MAX(timestamp) FROM messaggi WHERE chat_id = c.id)
                    LEFT JOIN utenti u ON m.utente_id = u.id
                    WHERE pc.utente_id = ? OR c.classe = ?
                    GROUP BY c.id
                    ORDER BY ultimo_messaggio_data DESC NULLS LAST
                ''', (user_id, session.get('classe', ''))).fetchall()

        conversations_list = [dict(conv) for conv in conversations]
        
        # Cache risultato
        cache_manager.cache_user_data(user_id, 'conversations', conversations_list, ttl=30)
        return jsonify(conversations_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/messages/<int:conversation_id>')
def messages(conversation_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        with db_manager.get_connection() as conn:
            messages = conn.execute('''
                SELECT m.*, u.nome, u.cognome, u.username, u.ruolo,
                       m.timestamp as data_invio
                FROM messaggi m
                JOIN utenti u ON m.utente_id = u.id
                WHERE m.chat_id = ?
                ORDER BY m.timestamp ASC
                LIMIT 100
            ''', (conversation_id,)).fetchall()

        return jsonify([dict(msg) for msg in messages])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message.strip():
            return jsonify({'error': 'Messaggio vuoto'}), 400

        # Genera risposta AI
        response = ai_bot.generate_response(
            message, 
            session['nome'], 
            session['ruolo'],
            session['user_id']
        )

        # Salva conversazione
        with db_manager.get_connection() as conn:
            subject_detected = ai_bot.detect_subject(message)
            sentiment_analysis = ','.join(ai_bot.analyze_user_sentiment(message))
            
            conn.execute('''
                INSERT INTO ai_conversations 
                (utente_id, message, response, subject_detected, sentiment_analysis, timestamp)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (session['user_id'], message, response, subject_detected, sentiment_analysis))

        # Gamification
        gamification_system.award_xp(
            session['user_id'], 
            'ai_question', 
            description=f"Domanda AI su {subject_detected}"
        )

        return jsonify({
            'response': response,
            'bot_name': 'SKAILA Assistant',
            'bot_avatar': '🤖',
            'subject_detected': subject_detected,
            'personalized': True
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/gamification/profile')
def gamification_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        profile = gamification_system.get_or_create_user_profile(session['user_id'])
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/gamification/leaderboard')
def gamification_leaderboard():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        period = request.args.get('period', 'weekly')
        class_filter = request.args.get('class_filter', session.get('classe'))

        leaderboard_data = gamification_system.get_leaderboard(
            session['user_id'], 
            period, 
            class_filter
        )
        return jsonify(leaderboard_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
