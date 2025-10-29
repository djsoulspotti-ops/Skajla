"""
SKAILA - API Routes Autenticazione
Endpoint REST JSON per autenticazione (mantiene sistema session-based)
"""

from flask import Blueprint, request, jsonify, session
from services.auth_service import auth_service
from services.password_validator import validate_password
from services.email_validator import validate_email, normalize_email
from school_system import school_system
from gamification import gamification_system
from database_manager import db_manager
from shared.middleware.auth import api_auth_required

api_auth_bp = Blueprint('api_auth', __name__, url_prefix='/api')


@api_auth_bp.route('/register', methods=['POST'])
def api_register():
    """
    POST /api/register
    Registra nuovo utente e restituisce dati JSON
    
    Body JSON:
    {
        "username": "mario.rossi",
        "email": "mario@example.com",
        "password": "SecurePass123!",
        "nome": "Mario",
        "cognome": "Rossi",
        "codice_scuola": "SKAIL-ABC123" (opzionale)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dati mancanti',
                'message': 'Nessun dato ricevuto nella richiesta'
            }), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        nome = data.get('nome', '').strip()
        cognome = data.get('cognome', '').strip()
        codice_scuola = data.get('codice_scuola', '').strip().upper()
        
        if not all([username, email, password, nome, cognome]):
            return jsonify({
                'success': False,
                'error': 'Campi obbligatori mancanti',
                'message': 'Username, email, password, nome e cognome sono obbligatori'
            }), 400
        
        is_valid_email, email_message = validate_email(email)
        if not is_valid_email:
            return jsonify({
                'success': False,
                'error': 'Email non valida',
                'message': email_message
            }), 400
        
        email = normalize_email(email)
        
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({
                'success': False,
                'error': 'Password non valida',
                'message': password_message
            }), 400
        
        existing_user = db_manager.query(
            "SELECT id FROM utenti WHERE email = %s OR username = %s",
            (email, username),
            one=True
        )
        
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Utente già esistente',
                'message': 'Email o username già registrati'
            }), 409
        
        scuola_id = None
        ruolo = 'studente'
        classe = None
        
        if codice_scuola:
            code_info = school_system.verify_activation_code(codice_scuola)
            
            if code_info and code_info.get('valid'):
                scuola_id = code_info.get('school_id')
                
                if code_info.get('type') == 'teacher':
                    ruolo = 'professore'
                elif code_info.get('type') == 'director':
                    ruolo = 'dirigente'
                else:
                    ruolo = 'studente'
                    classe = code_info.get('class_name')
        
        password_hash = auth_service.hash_password(password)
        
        result = db_manager.execute(
            """
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe, scuola_id, avatar)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'default.jpg')
            RETURNING id
            """,
            (username, email, password_hash, nome, cognome, ruolo, classe, scuola_id)
        )
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Errore registrazione',
                'message': 'Impossibile creare account. Riprova'
            }), 500
        
        user_id = result.lastrowid if hasattr(result, 'lastrowid') else (result[0]['id'] if isinstance(result, list) and result else None)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Errore registrazione',
                'message': 'ID utente non disponibile'
            }), 500
        
        if classe and scuola_id:
            try:
                chat_room = school_system.get_or_create_class_chat(scuola_id, classe)
                if chat_room:
                    db_manager.execute(
                        "INSERT INTO partecipanti_chat (chat_id, utente_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (chat_room['id'], user_id)
                    )
            except Exception as e:
                print(f"⚠️ Errore creazione chat classe (non-blocking): {e}")
        
        try:
            gamification_system.initialize_user_gamification(user_id)
        except Exception as e:
            print(f"⚠️ Gamification init error (non-blocking): {e}")
        
        session['user_id'] = user_id
        session['username'] = username
        session['nome'] = nome
        session['cognome'] = cognome
        session['email'] = email
        session['ruolo'] = ruolo
        session['classe'] = classe
        session['avatar'] = 'default.jpg'
        session['scuola_id'] = scuola_id
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': f'Benvenuto {nome}! Account creato con successo',
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'nome': nome,
                'cognome': cognome,
                'ruolo': ruolo,
                'classe': classe,
                'scuola_id': scuola_id
            }
        }), 201
        
    except Exception as e:
        print(f"❌ API Register error: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore server',
            'message': 'Errore interno del server'
        }), 500


@api_auth_bp.route('/login', methods=['POST'])
def api_login():
    """
    POST /api/login
    Autentica utente e restituisce dati JSON
    
    Body JSON:
    {
        "email": "mario@example.com",
        "password": "SecurePass123!",
        "remember_me": true (opzionale)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dati mancanti',
                'message': 'Nessun dato ricevuto nella richiesta'
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Credenziali mancanti',
                'message': 'Email e password sono obbligatori'
            }), 400
        
        if auth_service.is_locked_out(email):
            import time
            last_attempt = auth_service.login_attempts.get(email, {}).get('last_attempt', 0)
            time_since_last_attempt = time.time() - last_attempt
            time_remaining = max(0, auth_service.lockout_duration - time_since_last_attempt)
            minutes_left = max(1, int(time_remaining / 60))
            
            return jsonify({
                'success': False,
                'error': 'Account bloccato',
                'message': f'Troppi tentativi falliti. Riprova tra {minutes_left} minuti',
                'locked_until_minutes': minutes_left
            }), 429
        
        user = auth_service.authenticate_user(email, password)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Credenziali errate',
                'message': 'Email o password non corretti'
            }), 401
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['nome'] = user['nome']
        session['cognome'] = user['cognome']
        session['email'] = user['email']
        session['ruolo'] = user['ruolo']
        session['classe'] = user.get('classe', '')
        session['avatar'] = user.get('avatar', 'default.jpg')
        session['scuola_id'] = user.get('scuola_id')
        session['classe_id'] = user.get('classe_id')
        
        session.permanent = True
        session['remember_me'] = remember_me
        
        if not remember_me:
            from datetime import datetime, timedelta
            session['session_expires'] = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        try:
            gamification_system.update_streak(user['id'])
            gamification_system.award_xp(user['id'], 'login_daily', multiplier=1.0, context="Login giornaliero")
        except Exception as e:
            print(f"⚠️ Gamification error (non-blocking): {e}")
        
        return jsonify({
            'success': True,
            'message': f'Bentornato, {user["nome"]}!',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'ruolo': user['ruolo'],
                'classe': user.get('classe'),
                'avatar': user.get('avatar', 'default.jpg'),
                'scuola_id': user.get('scuola_id')
            }
        }), 200
        
    except Exception as e:
        print(f"❌ API Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore server',
            'message': 'Errore interno del server'
        }), 500


@api_auth_bp.route('/logout', methods=['POST'])
@api_auth_required
def api_logout():
    """
    POST /api/logout
    Effettua logout (invalida sessione)
    """
    try:
        user_nome = session.get('nome', 'Utente')
        
        session.clear()
        
        return jsonify({
            'success': True,
            'message': f'Arrivederci, {user_nome}!'
        }), 200
        
    except Exception as e:
        print(f"❌ API Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore server',
            'message': 'Errore interno del server'
        }), 500


@api_auth_bp.route('/user/me', methods=['GET'])
@api_auth_required
def api_get_current_user():
    """
    GET /api/user/me
    Restituisce dati utente loggato (protetto)
    """
    try:
        user_id = session.get('user_id')
        
        user = db_manager.query(
            """
            SELECT id, username, email, nome, cognome, ruolo, classe, scuola_id, 
                   avatar, data_registrazione
            FROM utenti 
            WHERE id = %s
            """,
            (user_id,),
            one=True
        )
        
        if not user:
            session.clear()
            return jsonify({
                'success': False,
                'error': 'Utente non trovato',
                'message': 'Sessione non valida'
            }), 404
        
        gamification_data = db_manager.query(
            """
            SELECT xp_totale, livello, streak_giorni, ultimo_login, badge_count
            FROM user_gamification
            WHERE user_id = %s
            """,
            (user_id,),
            one=True
        )
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'ruolo': user['ruolo'],
                'classe': user.get('classe'),
                'scuola_id': user.get('scuola_id'),
                'avatar': user.get('avatar', 'default.jpg'),
                'data_registrazione': user.get('data_registrazione').isoformat() if user.get('data_registrazione') else None,
                'gamification': {
                    'xp_totale': gamification_data.get('xp_totale', 0) if gamification_data else 0,
                    'livello': gamification_data.get('livello', 1) if gamification_data else 1,
                    'streak_giorni': gamification_data.get('streak_giorni', 0) if gamification_data else 0,
                    'badge_count': gamification_data.get('badge_count', 0) if gamification_data else 0
                } if gamification_data else None
            }
        }), 200
        
    except Exception as e:
        print(f"❌ API Get User error: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore server',
            'message': 'Errore interno del server'
        }), 500
