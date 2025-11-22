from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate limiter
limiter = Limiter(key_func=get_remote_address,
                  default_limits=["200 per hour"],
                  storage_uri="memory://")
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
            conversations = db_manager.query(
                '''
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
                WHERE c.scuola_id = %s
                GROUP BY c.id
                ORDER BY COALESCE(ultimo_messaggio_data, '1900-01-01') DESC
            ''', (school_id, ))
        else:
            # SECURITY: Utenti vedono solo chat della loro scuola + membership
            conversations = db_manager.query(
                '''
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
                WHERE c.scuola_id = %s AND (pc.utente_id = %s OR c.classe = %s)
                GROUP BY c.id
                ORDER BY COALESCE(ultimo_messaggio_data, '1900-01-01') DESC
            ''', (school_id, user_id, session.get('classe', '')))

        conversations_list = conversations

        # Cache risultato
        cache_manager.cache_user_data(user_id,
                                      'conversations',
                                      conversations_list,
                                      ttl=30)
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
            return jsonify(
                {'error':
                 'Accesso non autorizzato a questa conversazione'}), 403

        messages = db_manager.query(
            '''
            SELECT m.*, u.nome, u.cognome, u.username, u.ruolo,
                   m.timestamp as data_invio
            FROM messaggi m
            JOIN utenti u ON m.utente_id = u.id
            JOIN chat c ON m.chat_id = c.id
            WHERE m.chat_id = %s AND c.scuola_id = %s
            ORDER BY m.timestamp ASC
            LIMIT 100
        ''', (conversation_id, school_id))

        return jsonify(messages)

    except TenantGuardException:
        return jsonify({'error': 'Accesso non autorizzato alla scuola'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/ai/chat', methods=['POST'])
@limiter.limit("30 per minute")
def ai_chat():
    """
    SKAILA Coach - Chatbot soft skills & coaching
    Salva automaticamente conversazioni in coaching_interactions
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message.strip():
            return jsonify({'error': 'Messaggio vuoto'}), 400

        # Genera risposta AI (salva automaticamente in coaching_interactions)
        response = ai_bot.generate_response(message, session['nome'],
                                            session['ruolo'],
                                            session['user_id'])

        # Gamification (già gestito dentro _save_conversation, ma aggiungiamo per interazione chat)
        gamification_system.award_xp(session['user_id'], 'ai_interaction')

        return jsonify({
            'response': response,
            'bot_name': 'SKAILA Coach',
            'bot_avatar': '🎓',
            'personalized': True
        })

    except Exception as e:
        print(f"Errore API /ai/chat: {e}")
        return jsonify(
            {'error': 'Errore durante la generazione della risposta'}), 500


@api_bp.route('/gamification/profile')
def gamification_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        profile = gamification_system.get_or_create_profile(session['user_id'])
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
            session['user_id'], period, class_filter)
        return jsonify(leaderboard_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health/status')
def health_status():
    """Health check endpoint for load testing"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'skaila'
    })


@api_bp.route('/health/db-check')
def health_db_check():
    """Database health check for load testing"""
    try:
        result = db_manager.query('SELECT 1 as status', one=True)
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500
