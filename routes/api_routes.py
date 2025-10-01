
"""
SKAILA - API Routes
Tutte le API REST centralizzate
"""

from flask import Blueprint, request, session, jsonify
from database_manager import db_manager
from cache_manager import cache_manager
from gamification import gamification_system
from ai_chatbot import AISkailaBot
from services.tenant_guard import get_current_school_id, verify_chat_belongs_to_school, TenantGuardException
import time

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Inizializza AI bot
ai_bot = AISkailaBot()

@api_bp.route('/conversations')
def conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        # SECURITY: Tenant guard
        school_id = get_current_school_id()
        
        user_id = session['user_id']
        user_role = session['ruolo']
        cache_key = f"conversations_{user_id}_{user_role}_{school_id}"
        
        # Controlla cache
        cached = cache_manager.get_user_data(user_id, 'conversations')
        if cached:
            return jsonify(cached)

        if user_role == 'admin':
            # SECURITY: Admin vede solo chat della sua scuola
            conversations = db_manager.query('''
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
                WHERE c.scuola_id = ?
                GROUP BY c.id
                ORDER BY ultimo_messaggio_data DESC NULLS LAST
            ''', (school_id,))
        else:
            # SECURITY: Utenti vedono solo chat della loro scuola + membership
            conversations = db_manager.query('''
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
                WHERE c.scuola_id = ? AND (pc.utente_id = ? OR c.classe = ?)
                GROUP BY c.id
                ORDER BY ultimo_messaggio_data DESC NULLS LAST
            ''', (school_id, user_id, session.get('classe', '')))

        conversations_list = conversations
        
        # Cache risultato
        cache_manager.cache_user_data(user_id, 'conversations', conversations_list, ttl=30)
        return jsonify(conversations_list)

    except TenantGuardException as e:
        return jsonify({'error': 'Accesso non autorizzato alla scuola'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/messages/<int:conversation_id>')
def messages(conversation_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        # SECURITY: Tenant guard - verifica che chat appartenga alla scuola
        school_id = get_current_school_id()
        if not verify_chat_belongs_to_school(conversation_id, school_id):
            return jsonify({'error': 'Accesso non autorizzato a questa conversazione'}), 403
        
        messages = db_manager.query('''
            SELECT m.*, u.nome, u.cognome, u.username, u.ruolo,
                   m.timestamp as data_invio
            FROM messaggi m
            JOIN utenti u ON m.utente_id = u.id
            JOIN chat c ON m.chat_id = c.id
            WHERE m.chat_id = ? AND c.scuola_id = ?
            ORDER BY m.timestamp ASC
            LIMIT 100
        ''', (conversation_id, school_id))

        return jsonify(messages)

    except TenantGuardException:
        return jsonify({'error': 'Accesso non autorizzato alla scuola'}), 403
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
        subject_detected = ai_bot.detect_subject(message)
        sentiment_analysis = ','.join(ai_bot.analyze_user_sentiment(message))
        
        db_manager.execute('''
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
"""
SKAILA - API Routes
Endpoints API per AJAX e comunicazioni frontend
"""

from flask import Blueprint, jsonify, request, session
from database_manager import db_manager
from gamification import gamification_system
from ai_chatbot import AISkailaBot

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/user/profile')
def get_user_profile():
    """Ottieni profilo utente corrente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    user_id = session['user_id']
    gamification_data = gamification_system.get_user_dashboard(user_id)
    
    return jsonify({
        'user': {
            'id': session['user_id'],
            'nome': session['nome'],
            'ruolo': session['ruolo'],
            'avatar': session.get('avatar', 'default.jpg')
        },
        'gamification': {
            'xp': gamification_data['profile']['total_xp'],
            'level': gamification_data['profile']['current_level'],
            'streak': gamification_data['profile']['current_streak']
        }
    })

@api_bp.route('/gamification/award-xp', methods=['POST'])
def award_xp():
    """Assegna XP per azione"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    data = request.get_json()
    action_type = data.get('action_type')
    
    result = gamification_system.award_xp(
        session['user_id'], 
        action_type, 
        description=data.get('description', '')
    )
    
    return jsonify(result)

@api_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    """Endpoint per chat AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    data = request.get_json()
    message = data.get('message', '')
    
    ai_bot = AISkailaBot()
    response = ai_bot.generate_response(
        message, 
        session['nome'], 
        session['ruolo'], 
        session['user_id']
    )
    
    # Salva conversazione
    with db_manager.get_connection() as conn:
        conn.execute('''
            INSERT INTO ai_conversations (utente_id, message, response)
            VALUES (?, ?, ?)
        ''', (session['user_id'], message, response))
        conn.commit()
    
    # Award XP per interazione AI
    gamification_system.award_xp(session['user_id'], 'ai_question')
    
    return jsonify({
        'response': response,
        'timestamp': '2024-01-01T12:00:00'  # Da implementare con timestamp reale
    })

@api_bp.route('/leaderboard/<period>')
def get_leaderboard(period):
    """Ottieni classifica per periodo"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    leaderboard = gamification_system.get_leaderboard(
        session['user_id'], 
        period, 
        session.get('classe')
    )
    
    return jsonify(leaderboard)

@api_bp.route('/health')
def health_check():
    """Health check per monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': '2024-01-01T12:00:00',
        'version': '2.0.0'
    })
