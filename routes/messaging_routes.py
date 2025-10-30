"""
SKAILA - Messaging Routes
Sistema messaggistica granulare: 1-to-1, gruppi materia, chat classe
"""

from flask import Blueprint, render_template, session, redirect, request, jsonify
from database_manager import db_manager
from services.tenant_guard import get_current_school_id
from gamification import gamification_system
from shared.middleware.auth import require_login

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/chat')
@require_login
def chat_hub():
    """Hub messaggistica - mostra tutte le conversazioni disponibili"""
    user_id = session['user_id']
    school_id = get_current_school_id()
    
    # Chat classe (ordinata per ultimo messaggio)
    chat_classe = db_manager.query('''
        SELECT c.*, 
               COUNT(DISTINCT m.id) as message_count,
               MAX(m.timestamp) as ultimo_messaggio
        FROM chat c
        LEFT JOIN messaggi m ON c.id = m.chat_id
        WHERE c.scuola_id = %s AND c.classe = %s AND c.tipo = 'classe'
        GROUP BY c.id
        ORDER BY ultimo_messaggio DESC NULLS LAST
    ''', (school_id, session.get('classe', '')))
    
    # Gruppi materia (una sola chat per materia, ordinata per ultimo messaggio - più recente in cima)
    gruppi_materia = db_manager.query('''
        WITH chat_with_last_message AS (
            SELECT c.*, 
                   COUNT(DISTINCT m.id) as message_count,
                   MAX(m.timestamp) as ultimo_messaggio
            FROM chat c
            LEFT JOIN messaggi m ON c.id = m.chat_id
            JOIN partecipanti_chat pc ON c.id = pc.chat_id
            WHERE c.scuola_id = %s AND c.tipo = 'materia' AND pc.utente_id = %s
            GROUP BY c.id
        ),
        ranked_chats AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY materia ORDER BY ultimo_messaggio DESC NULLS LAST) as rn
            FROM chat_with_last_message
        )
        SELECT * FROM ranked_chats WHERE rn = 1
        ORDER BY ultimo_messaggio DESC NULLS LAST
    ''', (school_id, user_id))
    
    # Conversazioni 1-to-1 (ordinate per ultimo messaggio)
    conversazioni_private = db_manager.query('''
        SELECT c.*, 
               u.nome, 
               u.cognome, 
               u.ruolo,
               COUNT(DISTINCT m.id) as message_count,
               MAX(m.timestamp) as ultimo_messaggio
        FROM chat c
        JOIN partecipanti_chat pc ON c.id = pc.chat_id
        JOIN utenti u ON pc.utente_id = u.id
        LEFT JOIN messaggi m ON c.id = m.chat_id
        WHERE c.scuola_id = %s AND c.tipo = 'privata' 
        AND c.id IN (SELECT chat_id FROM partecipanti_chat WHERE utente_id = %s)
        AND u.id != %s
        GROUP BY c.id, u.id, u.nome, u.cognome, u.ruolo
        ORDER BY ultimo_messaggio DESC NULLS LAST
    ''', (school_id, user_id, user_id))
    
    # Lista utenti per nuova chat 1-to-1
    available_users = db_manager.query('''
        SELECT id, nome, cognome, ruolo
        FROM utenti
        WHERE scuola_id = %s AND id != %s AND attivo = true
        ORDER BY cognome, nome
    ''', (school_id, user_id))
    
    return render_template('chat_hub.html',
                         user=session,
                         chat_classe=chat_classe or [],
                         gruppi_materia=gruppi_materia or [],
                         conversazioni_private=conversazioni_private or [],
                         available_users=available_users or [])

@messaging_bp.route('/chat/private/<int:recipient_id>')
@require_login
def private_chat(recipient_id):
    """Apri chat privata 1-to-1"""
    user_id = session['user_id']
    school_id = get_current_school_id()
    
    # Controlla se esiste già una chat tra questi utenti
    existing_chat = db_manager.query('''
        SELECT c.id
        FROM chat c
        JOIN partecipanti_chat pc1 ON c.id = pc1.chat_id
        JOIN partecipanti_chat pc2 ON c.id = pc2.chat_id
        WHERE c.tipo = 'privata' 
        AND c.scuola_id = %s
        AND pc1.utente_id = %s 
        AND pc2.utente_id = %s
        LIMIT 1
    ''', (school_id, user_id, recipient_id), one=True)
    
    if existing_chat:
        chat_id = existing_chat[0]
    else:
        # Crea nuova chat privata
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO chat (nome, tipo, scuola_id, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            ''', (f'Chat privata', 'privata', school_id))
            chat_id = cursor.fetchone()[0]
            
            # Aggiungi partecipanti
            conn.execute('''
                INSERT INTO partecipanti_chat (chat_id, utente_id)
                VALUES (%s, %s), (%s, %s)
            ''', (chat_id, user_id, chat_id, recipient_id))
            conn.commit()
    
    return redirect(f'/chat/room/{chat_id}')

@messaging_bp.route('/chat/group/materia/<materia>')
@require_login
def group_chat_materia(materia):
    """Apri gruppo materia o crealo se non esiste"""
    user_id = session['user_id']
    school_id = get_current_school_id()
    classe = session.get('classe', '')
    
    # Controlla se esiste gruppo per questa materia
    existing_group = db_manager.query('''
        SELECT id FROM chat
        WHERE tipo = 'materia' 
        AND scuola_id = %s 
        AND classe = %s
        AND nome LIKE %s
        LIMIT 1
    ''', (school_id, classe, f'%{materia}%'), one=True)
    
    if existing_group:
        chat_id = existing_group[0]
    else:
        # Crea gruppo materia
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO chat (nome, descrizione, tipo, classe, scuola_id, created_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            ''', (f'📚 {materia} - {classe}', f'Gruppo di studio per {materia}', 'materia', classe, school_id))
            chat_id = cursor.fetchone()[0]
            
            # Aggiungi tutti gli studenti della classe
            conn.execute('''
                INSERT INTO partecipanti_chat (chat_id, utente_id)
                SELECT %s, id FROM utenti 
                WHERE classe = %s AND scuola_id = %s AND ruolo = 'studente' AND attivo = true
            ''', (chat_id, classe, school_id))
            conn.commit()
    
    return redirect(f'/chat/room/{chat_id}')

@messaging_bp.route('/chat/room/<int:chat_id>')
@require_login
def chat_room(chat_id):
    """Stanza chat specifica"""
    user_id = session['user_id']
    school_id = get_current_school_id()
    
    # Verifica accesso
    is_participant = db_manager.query('''
        SELECT 1 FROM partecipanti_chat
        WHERE chat_id = %s AND utente_id = %s
    ''', (chat_id, user_id), one=True)
    
    # O è admin/professore della scuola
    is_authorized = is_participant or session.get('ruolo') in ['admin', 'professore']
    
    if not is_authorized:
        return redirect('/chat')
    
    # Info chat
    chat_info = db_manager.query('''
        SELECT * FROM chat WHERE id = %s AND scuola_id = %s
    ''', (chat_id, school_id), one=True)
    
    if not chat_info:
        return redirect('/chat')
    
    # Messaggi
    messages = db_manager.query('''
        SELECT m.*, u.nome, u.cognome
        FROM messaggi m
        JOIN utenti u ON m.utente_id = u.id
        WHERE m.chat_id = %s
        ORDER BY m.timestamp ASC
        LIMIT 100
    ''', (chat_id,))
    
    # Partecipanti
    participants = db_manager.query('''
        SELECT u.id, u.nome, u.cognome, u.ruolo
        FROM utenti u
        JOIN partecipanti_chat pc ON u.id = pc.utente_id
        WHERE pc.chat_id = %s
    ''', (chat_id,))
    
    return render_template('chat_room.html',
                         user=session,
                         chat=chat_info,
                         messages=messages or [],
                         participants=participants or [])

@messaging_bp.route('/materiali')
@require_login
def materiali():
    """Materiali didattici"""
    try:
        user_id = session['user_id']
        school_id = get_current_school_id()
        
        if not school_id:
            return render_template('materiali.html',
                                 user=session,
                                 materials=[],
                                 ruolo=session.get('ruolo', 'studente'),
                                 error='Scuola non configurata. Contatta l\'amministratore.')
        
        ruolo = session.get('ruolo', 'studente')
        
        if ruolo == 'studente':
            # Studenti vedono materiali della loro classe
            materials = db_manager.query('''
                SELECT * FROM materiali_didattici
                WHERE scuola_id = %s AND classe = %s
                ORDER BY data_upload DESC
            ''', (school_id, session.get('classe', '')))
        else:
            # Professori vedono i loro materiali
            materials = db_manager.query('''
                SELECT * FROM materiali_didattici
                WHERE scuola_id = %s AND professore_id = %s
                ORDER BY data_upload DESC
            ''', (school_id, user_id))
        
        return render_template('materiali.html',
                             user=session,
                             materials=materials or [],
                             ruolo=ruolo)
    except Exception as e:
        print(f"❌ Errore materiali: {e}")
        return render_template('materiali.html',
                             user=session,
                             materials=[],
                             ruolo=session.get('ruolo', 'studente'))

@messaging_bp.route('/quiz')
@require_login
def quiz_hub():
    """Hub quiz e test"""
    try:
        user_id = session['user_id']
        school_id = get_current_school_id()
        
        if not school_id:
            return render_template('quiz_hub.html',
                                 user=session,
                                 available_quizzes=[],
                                 completed_quizzes=[],
                                 error='Scuola non configurata. Contatta l\'amministratore.')
        
        # Quiz disponibili
        available_quizzes = db_manager.query('''
            SELECT * FROM quiz
            WHERE scuola_id = %s AND attivo = true
            ORDER BY materia, difficolta
        ''', (school_id,))
        
        # Storico quiz completati
        completed_quizzes = db_manager.query('''
            SELECT q.*, qr.punteggio, qr.data_completamento
            FROM quiz q
            JOIN quiz_results qr ON q.id = qr.quiz_id
            WHERE qr.studente_id = %s
            ORDER BY qr.data_completamento DESC
            LIMIT 10
        ''', (user_id,))
        
        return render_template('quiz_hub.html',
                             user=session,
                             available_quizzes=available_quizzes or [],
                             completed_quizzes=completed_quizzes or [])
    except Exception as e:
        print(f"❌ Errore quiz: {e}")
        return render_template('quiz_hub.html',
                             user=session,
                             available_quizzes=[],
                             completed_quizzes=[])

@messaging_bp.route('/calendario')
@require_login
def calendario():
    """Calendario eventi"""
    try:
        user_id = session['user_id']
        school_id = get_current_school_id()
        
        if not school_id:
            return render_template('calendario.html',
                                 user=session,
                                 events=[],
                                 error='Scuola non configurata. Contatta l\'amministratore.')
        
        # Eventi futuri
        upcoming_events = db_manager.query('''
            SELECT * FROM eventi
            WHERE scuola_id = %s AND data >= CURRENT_DATE
            ORDER BY data ASC
            LIMIT 20
        ''', (school_id,))
        
        return render_template('calendario.html',
                             user=session,
                             events=upcoming_events or [])
    except Exception as e:
        print(f"❌ Errore calendario: {e}")
        # Fallback: mostra calendario senza eventi
        return render_template('calendario.html',
                             user=session,
                             events=[])

# API Endpoints
@messaging_bp.route('/api/chat/send', methods=['POST'])
def send_message():
    """Invia messaggio in chat"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401
    
    data = request.get_json()
    chat_id = data.get('chat_id')
    content = data.get('message')
    
    if not chat_id or not content:
        return jsonify({'error': 'Parametri mancanti'}), 400
    
    user_id = session['user_id']
    
    with db_manager.get_connection() as conn:
        cursor = conn.execute('''
            INSERT INTO messaggi (chat_id, utente_id, contenuto, timestamp)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        ''', (chat_id, user_id, content))
        message_id = cursor.fetchone()[0]
        conn.commit()
    
    # Award XP per partecipazione
    gamification_system.award_xp(user_id, 'message_sent', 5)
    
    return jsonify({
        'success': True,
        'message_id': message_id
    })
