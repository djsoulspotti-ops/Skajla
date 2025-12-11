
"""
SKAJLA - Socket.IO Events
Eventi real-time per chat, notifiche e presenza avanzata
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from flask_socketio import emit, join_room, leave_room
from flask import session
from database_manager import db_manager
from gamification import gamification_system
from services.tenant_guard import verify_chat_belongs_to_school, get_current_school_id, TenantGuardException
from ai_chatbot import ai_bot

# Connection tracking per heartbeat e rate limiting
_active_connections = {}
_last_heartbeat = {}
_message_rate_limit = defaultdict(list)  # user_id -> [timestamps]

# Rate limiting config
RATE_LIMIT_MESSAGES = 30  # max messaggi
RATE_LIMIT_WINDOW = 60    # in secondi


def check_rate_limit(user_id):
    """Verifica se l'utente ha superato il rate limit"""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    
    _message_rate_limit[user_id] = [
        ts for ts in _message_rate_limit[user_id] if ts > cutoff
    ]
    
    if len(_message_rate_limit[user_id]) >= RATE_LIMIT_MESSAGES:
        return False
    
    _message_rate_limit[user_id].append(now)
    return True


def register_socket_events(socketio):
    """Registra tutti gli eventi Socket.IO"""
    
    @socketio.on('connect')
    def handle_connect():
        if 'user_id' in session:
            join_room(f"user_{session['user_id']}")

            # SECURITY: Join school-scoped room per tenant isolation
            try:
                school_id = get_current_school_id()
                join_room(f"school_{school_id}")
                
                db_manager.execute('UPDATE utenti SET status_online = %s WHERE id = %s', (True, session['user_id']))

                # Emit solo alla scuola dell'utente, NON broadcast globale
                emit('user_connected', {
                    'user_id': session['user_id'],
                    'nome': session['nome'],
                    'cognome': session['cognome'],
                    'ruolo': session['ruolo']
                }, to=f"school_{school_id}")
            except TenantGuardException:
                # User senza school_id, skip presence broadcast
                pass

    @socketio.on('disconnect')
    def handle_disconnect():
        if 'user_id' in session:
            leave_room(f"user_{session['user_id']}")

            # SECURITY: Emit solo alla scuola dell'utente, NON broadcast globale
            try:
                school_id = get_current_school_id()
                
                db_manager.execute('UPDATE utenti SET status_online = %s WHERE id = %s', (False, session['user_id']))

                emit('user_disconnected', {
                    'user_id': session['user_id'],
                    'nome': session['nome'],
                    'cognome': session['cognome']
                }, to=f"school_{school_id}")
                
                leave_room(f"school_{school_id}")
            except TenantGuardException:
                # User senza school_id, skip presence broadcast
                pass

    @socketio.on('request_online_users')
    def handle_request_online_users():
        """Return list of currently online users for this school"""
        if 'user_id' not in session:
            return
        
        try:
            school_id = get_current_school_id()
            online_users = db_manager.query('''
                SELECT id, nome, cognome, ruolo FROM utenti 
                WHERE scuola_id = %s AND status_online = true AND attivo = true
            ''', (school_id,))
            
            user_ids = []
            for u in (online_users or []):
                if isinstance(u, tuple):
                    user_ids.append(u[0])
                elif isinstance(u, dict):
                    user_ids.append(u.get('id'))
                    
            emit('online_users_list', {'users': user_ids})
        except TenantGuardException:
            pass

    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        if 'user_id' not in session:
            emit('error', {'message': 'Non autorizzato'})
            return

        conversation_id = data.get('conversation_id')
        if not conversation_id:
            emit('error', {'message': 'conversation_id mancante'})
            return

        # SECURITY: Tenant guard - verifica che la chat appartenga alla scuola
        try:
            school_id = get_current_school_id()
            if not verify_chat_belongs_to_school(conversation_id, school_id):
                emit('error', {'message': 'Chat non appartiene alla tua scuola'})
                return
        except TenantGuardException:
            emit('error', {'message': 'Errore di autenticazione scuola'})
            return

        # SECURITY: Verifica che l'utente sia membro della chat
        is_member = db_manager.query('''
            SELECT 1 FROM partecipanti_chat 
            WHERE chat_id = %s AND utente_id = %s
        ''', (conversation_id, session['user_id']), one=True)

        if not is_member:
            emit('error', {'message': 'Non autorizzato ad accedere a questa chat'})
            return

        join_room(f"chat_{conversation_id}")

        emit('joined_conversation', {
            'conversation_id': conversation_id
        })

    @socketio.on('send_message')
    def handle_send_message(data):
        if 'user_id' not in session:
            emit('error', {'message': 'Non autorizzato'})
            return
        
        user_id = session['user_id']
        
        if not check_rate_limit(user_id):
            emit('error', {'message': 'Stai inviando troppi messaggi. Attendi qualche secondo.'})
            return

        conversation_id = data.get('conversation_id')
        contenuto = data.get('contenuto', '')

        if not conversation_id:
            emit('error', {'message': 'conversation_id mancante'})
            return

        if not contenuto.strip():
            emit('error', {'message': 'Messaggio vuoto'})
            return

        # SECURITY: Tenant guard - verifica che la chat appartenga alla scuola
        try:
            school_id = get_current_school_id()
            if not verify_chat_belongs_to_school(conversation_id, school_id):
                emit('error', {'message': 'Chat non appartiene alla tua scuola'})
                return
        except TenantGuardException:
            emit('error', {'message': 'Errore di autenticazione scuola'})
            return

        # SECURITY: Verifica che l'utente sia membro della chat
        is_member = db_manager.query('''
            SELECT 1 FROM partecipanti_chat 
            WHERE chat_id = %s AND utente_id = %s
        ''', (conversation_id, session['user_id']), one=True)

        if not is_member:
            emit('error', {'message': 'Non autorizzato a inviare messaggi in questa chat'})
            return

        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO messaggi (chat_id, utente_id, contenuto)
                VALUES (%s, %s, %s)
            ''', (conversation_id, session['user_id'], contenuto))

            message_id = cursor.lastrowid

            messaggio = conn.execute('''
                SELECT m.*, u.nome, u.cognome, u.username, u.ruolo,
                       m.timestamp as data_invio
                FROM messaggi m
                JOIN utenti u ON m.utente_id = u.id
                WHERE m.id = %s
            ''', (message_id,)).fetchone()

        # Gamification
        gamification_system.award_xp(session['user_id'], 'message_sent', multiplier=1.0, context="Messaggio in chat")

        emit('new_message', dict(messaggio), to=f"chat_{conversation_id}")

    @socketio.on('typing_start')
    def handle_typing_start(data):
        if 'user_id' not in session:
            return

        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return

        # SECURITY: Tenant guard
        try:
            school_id = get_current_school_id()
            if not verify_chat_belongs_to_school(conversation_id, school_id):
                return
        except TenantGuardException:
            return

        # SECURITY: Verifica che l'utente sia membro della chat
        is_member = db_manager.query('''
            SELECT 1 FROM partecipanti_chat 
            WHERE chat_id = %s AND utente_id = %s
        ''', (conversation_id, session['user_id']), one=True)

        if not is_member:
            return

        emit('user_typing', {
            'conversation_id': conversation_id,
            'user_name': session['nome'],
            'typing': True
        }, to=f"chat_{conversation_id}", include_self=False)

    @socketio.on('typing_stop')
    def handle_typing_stop(data):
        if 'user_id' not in session:
            return

        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return

        # SECURITY: Tenant guard
        try:
            school_id = get_current_school_id()
            if not verify_chat_belongs_to_school(conversation_id, school_id):
                return
        except TenantGuardException:
            return

        # SECURITY: Verifica che l'utente sia membro della chat
        is_member = db_manager.query('''
            SELECT 1 FROM partecipanti_chat 
            WHERE chat_id = %s AND utente_id = %s
        ''', (conversation_id, session['user_id']), one=True)

        if not is_member:
            return

        emit('user_typing', {
            'conversation_id': conversation_id,
            'user_name': session['nome'],
            'typing': False
        }, to=f"chat_{conversation_id}", include_self=False)

    @socketio.on('ai_message')
    def handle_ai_message(data):
        """Gestisce messaggi per il chatbot AI"""
        if 'user_id' not in session:
            emit('ai_error', {'message': 'Non autorizzato'})
            return
        
        message = data.get('message', '').strip()
        if not message:
            emit('ai_error', {'message': 'Messaggio vuoto'})
            return
        
        try:
            # Genera risposta AI
            response = ai_bot.generate_response(
                message=message,
                user_name=session.get('nome', 'Studente'),
                user_role=session.get('ruolo', 'studente'),
                user_id=session['user_id']
            )
            
            # Invia risposta all'utente
            emit('ai_response', {
                'message': response,
                'timestamp': time.time()
            })
            
            # Award XP per utilizzo AI coach
            gamification_system.award_xp(
                session['user_id'], 
                'ai_interaction', 
                context="Interazione con SKAJLA Coach"
            )
            
        except Exception as e:
            print(f"Errore AI chatbot: {e}")
            emit('ai_error', {
                'message': 'Errore durante la generazione della risposta. Riprova.'
            })

    # ========== HEARTBEAT / PING-PONG ==========
    
    @socketio.on('heartbeat')
    def handle_heartbeat():
        """Client invia heartbeat per confermare connessione attiva"""
        if 'user_id' in session:
            user_id = session['user_id']
            _last_heartbeat[user_id] = time.time()
            emit('heartbeat_ack', {'timestamp': time.time()})
    
    @socketio.on('ping_presence')
    def handle_ping_presence():
        """Ping per verificare presenza e aggiornare last_seen"""
        if 'user_id' not in session:
            return
        
        user_id = session['user_id']
        try:
            db_manager.execute('''
                UPDATE utenti SET last_seen = NOW() 
                WHERE id = %s
            ''', (user_id,))
            emit('pong_presence', {'status': 'alive', 'server_time': time.time()})
        except Exception:
            pass

    # ========== READ RECEIPTS ==========
    
    @socketio.on('mark_messages_read')
    def handle_mark_messages_read(data):
        """Segna messaggi come letti e notifica mittenti"""
        if 'user_id' not in session:
            return
        
        conversation_id = data.get('conversation_id')
        message_ids = data.get('message_ids', [])
        
        if not conversation_id:
            return
        
        try:
            school_id = get_current_school_id()
            if not verify_chat_belongs_to_school(conversation_id, school_id):
                return
        except TenantGuardException:
            return
        
        user_id = session['user_id']
        
        is_member = db_manager.query('''
            SELECT 1 FROM partecipanti_chat 
            WHERE chat_id = %s AND utente_id = %s
        ''', (conversation_id, user_id), one=True)
        
        if not is_member:
            return
        
        if message_ids:
            for msg_id in message_ids:
                db_manager.execute('''
                    INSERT INTO messaggi_letti (messaggio_id, utente_id, letto_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (messaggio_id, utente_id) DO NOTHING
                ''', (msg_id, user_id))
        else:
            db_manager.execute('''
                INSERT INTO messaggi_letti (messaggio_id, utente_id, letto_at)
                SELECT m.id, %s, NOW()
                FROM messaggi m
                WHERE m.chat_id = %s 
                  AND m.utente_id != %s
                  AND NOT EXISTS (
                      SELECT 1 FROM messaggi_letti ml 
                      WHERE ml.messaggio_id = m.id AND ml.utente_id = %s
                  )
            ''', (user_id, conversation_id, user_id, user_id))
        
        emit('messages_read', {
            'conversation_id': conversation_id,
            'reader_id': user_id,
            'reader_name': session.get('nome', '')
        }, to=f"chat_{conversation_id}", include_self=False)

    # ========== NOTIFICATIONS SYSTEM ==========
    
    @socketio.on('send_notification')
    def handle_send_notification(data):
        """Invia notifica a utente specifico o gruppo (role-restricted)"""
        if 'user_id' not in session:
            return
        
        target_type = data.get('target_type')  # 'user', 'class', 'school'
        target_id = data.get('target_id')
        notification_type = data.get('type', 'info')
        title = data.get('title', '')
        message = data.get('message', '')
        ruolo = session.get('ruolo', '')
        
        if not all([target_type, target_id, message]):
            return
        
        try:
            school_id = get_current_school_id()
        except TenantGuardException:
            return
        
        if target_type == 'school' and ruolo not in ['professore', 'dirigente', 'admin']:
            emit('error', {'message': 'Solo docenti e dirigenti possono inviare notifiche alla scuola'})
            return
        
        if target_type == 'class':
            if ruolo == 'studente':
                emit('error', {'message': 'Studenti non possono inviare notifiche alla classe'})
                return
            is_teacher_of_class = db_manager.query('''
                SELECT 1 FROM docenti_classi dc
                JOIN classi c ON dc.classe_id = c.id
                WHERE dc.docente_id = %s AND c.id = %s AND c.scuola_id = %s
            ''', (session['user_id'], target_id, school_id), one=True)
            if not is_teacher_of_class and ruolo not in ['dirigente', 'admin']:
                emit('error', {'message': 'Non sei docente di questa classe'})
                return
        
        if target_type == 'user':
            target_same_school = db_manager.query('''
                SELECT 1 FROM utenti WHERE id = %s AND scuola_id = %s
            ''', (target_id, school_id), one=True)
            if not target_same_school:
                emit('error', {'message': 'Utente non trovato nella tua scuola'})
                return
        
        notification_data = {
            'type': notification_type,
            'title': title,
            'message': message,
            'sender_id': session['user_id'],
            'sender_name': f"{session.get('nome', '')} {session.get('cognome', '')}",
            'timestamp': time.time()
        }
        
        if target_type == 'user':
            emit('notification', notification_data, to=f"user_{target_id}")
        elif target_type == 'class':
            emit('notification', notification_data, to=f"class_{target_id}")
        elif target_type == 'school':
            emit('notification', notification_data, to=f"school_{school_id}")
    
    @socketio.on('broadcast_announcement')
    def handle_broadcast_announcement(data):
        """Annuncio broadcast (solo docenti/dirigenti)"""
        if 'user_id' not in session:
            return
        
        ruolo = session.get('ruolo', '')
        if ruolo not in ['professore', 'dirigente', 'admin']:
            emit('error', {'message': 'Non autorizzato a inviare annunci'})
            return
        
        try:
            school_id = get_current_school_id()
        except TenantGuardException:
            return
        
        announcement = {
            'type': 'announcement',
            'title': data.get('title', 'Annuncio'),
            'message': data.get('message', ''),
            'priority': data.get('priority', 'normal'),  # normal, high, urgent
            'sender': f"{session.get('nome', '')} {session.get('cognome', '')}",
            'sender_role': ruolo,
            'timestamp': time.time()
        }
        
        target_class = data.get('class_id')
        if target_class:
            emit('announcement', announcement, to=f"class_{target_class}")
        else:
            emit('announcement', announcement, to=f"school_{school_id}")

    # ========== CLASS/SUBJECT ROOMS ==========
    
    @socketio.on('join_class_room')
    def handle_join_class_room(data):
        """Unisciti alla room della classe per ricevere annunci e notifiche"""
        if 'user_id' not in session:
            return
        
        class_id = data.get('class_id')
        if not class_id:
            return
        
        try:
            school_id = get_current_school_id()
            is_member = db_manager.query('''
                SELECT 1 FROM utenti u
                JOIN classi c ON u.classe_id = c.id
                WHERE u.id = %s AND c.id = %s AND c.scuola_id = %s
                UNION
                SELECT 1 FROM docenti_classi dc
                JOIN classi c ON dc.classe_id = c.id
                WHERE dc.docente_id = %s AND c.id = %s AND c.scuola_id = %s
            ''', (session['user_id'], class_id, school_id, 
                  session['user_id'], class_id, school_id), one=True)
            
            if is_member:
                join_room(f"class_{class_id}")
                emit('joined_class_room', {'class_id': class_id})
        except TenantGuardException:
            pass
    
    @socketio.on('leave_class_room')
    def handle_leave_class_room(data):
        """Lascia la room della classe"""
        class_id = data.get('class_id')
        if class_id:
            leave_room(f"class_{class_id}")

    @socketio.on('join_subject_room')
    def handle_join_subject_room(data):
        """Unisciti alla room di una materia (con verifica iscrizione)"""
        if 'user_id' not in session:
            return
        
        subject_id = data.get('subject_id')
        if not subject_id:
            return
        
        try:
            school_id = get_current_school_id()
            user_id = session['user_id']
            ruolo = session.get('ruolo', '')
            
            if ruolo == 'studente':
                is_enrolled = db_manager.query('''
                    SELECT 1 FROM iscrizioni_materie im
                    JOIN materie m ON im.materia_id = m.id
                    WHERE im.studente_id = %s AND m.id = %s AND m.scuola_id = %s
                    UNION
                    SELECT 1 FROM materie m
                    JOIN classi c ON m.classe_id = c.id
                    JOIN utenti u ON u.classe_id = c.id
                    WHERE u.id = %s AND m.id = %s AND m.scuola_id = %s
                ''', (user_id, subject_id, school_id, user_id, subject_id, school_id), one=True)
            elif ruolo == 'professore':
                is_enrolled = db_manager.query('''
                    SELECT 1 FROM docenti_materie dm
                    JOIN materie m ON dm.materia_id = m.id
                    WHERE dm.docente_id = %s AND m.id = %s AND m.scuola_id = %s
                ''', (user_id, subject_id, school_id), one=True)
            else:
                is_enrolled = True
            
            if is_enrolled:
                join_room(f"subject_{subject_id}_{school_id}")
                emit('joined_subject_room', {'subject_id': subject_id})
            else:
                emit('error', {'message': 'Non sei iscritto a questa materia'})
        except TenantGuardException:
            pass

    # ========== ENHANCED PRESENCE ==========
    
    @socketio.on('get_room_presence')
    def handle_get_room_presence(data):
        """Ottieni presenza dettagliata per una room"""
        if 'user_id' not in session:
            return
        
        room_type = data.get('room_type')  # 'chat', 'class', 'school'
        room_id = data.get('room_id')
        
        if not all([room_type, room_id]):
            return
        
        try:
            school_id = get_current_school_id()
            
            if room_type == 'chat':
                if not verify_chat_belongs_to_school(room_id, school_id):
                    return
                
                members = db_manager.query('''
                    SELECT u.id, u.nome, u.cognome, u.ruolo, u.status_online, u.last_seen
                    FROM partecipanti_chat pc
                    JOIN utenti u ON pc.utente_id = u.id
                    WHERE pc.chat_id = %s AND u.attivo = true
                ''', (room_id,))
                
            elif room_type == 'class':
                members = db_manager.query('''
                    SELECT u.id, u.nome, u.cognome, u.ruolo, u.status_online, u.last_seen
                    FROM utenti u
                    WHERE u.classe_id = %s AND u.scuola_id = %s AND u.attivo = true
                ''', (room_id, school_id))
            else:
                return
            
            presence_list = []
            for m in (members or []):
                if isinstance(m, dict):
                    presence_list.append({
                        'id': m.get('id'),
                        'nome': m.get('nome'),
                        'cognome': m.get('cognome'),
                        'ruolo': m.get('ruolo'),
                        'online': m.get('status_online', False),
                        'last_seen': str(m.get('last_seen', ''))
                    })
            
            emit('room_presence', {
                'room_type': room_type,
                'room_id': room_id,
                'members': presence_list
            })
            
        except TenantGuardException:
            pass

    # ========== MESSAGE DELIVERY CONFIRMATION ==========
    
    @socketio.on('confirm_message_received')
    def handle_confirm_message_received(data):
        """Conferma ricezione messaggio (delivery receipt)"""
        if 'user_id' not in session:
            return
        
        message_id = data.get('message_id')
        conversation_id = data.get('conversation_id')
        
        if not all([message_id, conversation_id]):
            return
        
        try:
            school_id = get_current_school_id()
            if not verify_chat_belongs_to_school(conversation_id, school_id):
                return
        except TenantGuardException:
            return
        
        is_member = db_manager.query('''
            SELECT 1 FROM partecipanti_chat 
            WHERE chat_id = %s AND utente_id = %s
        ''', (conversation_id, session['user_id']), one=True)
        
        if not is_member:
            return
        
        emit('message_delivered', {
            'message_id': message_id,
            'receiver_id': session['user_id'],
            'delivered_at': time.time()
        }, to=f"chat_{conversation_id}", include_self=False)

    # ========== STUDY GROUPS REAL-TIME ==========
    
    def verify_study_group_membership(group_id, user_id):
        result = db_manager.query("""
            SELECT id FROM study_group_members 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id), one=True)
        return result is not None
    
    @socketio.on('join_study_group')
    def handle_join_study_group(data):
        if 'user_id' not in session:
            return
        
        group_id = data.get('group_id')
        if not group_id:
            return
        
        if not verify_study_group_membership(group_id, session['user_id']):
            return
        
        room = f"study_group_{group_id}"
        join_room(room)
        
        emit('user_joined_study_group', {
            'user_id': session['user_id'],
            'user_name': f"{session.get('nome', '')} {session.get('cognome', '')}",
            'group_id': group_id
        }, to=room, include_self=False)
    
    @socketio.on('leave_study_group')
    def handle_leave_study_group(data):
        if 'user_id' not in session:
            return
        
        group_id = data.get('group_id')
        if not group_id:
            return
        
        room = f"study_group_{group_id}"
        leave_room(room)
    
    @socketio.on('study_group_message')
    def handle_study_group_message(data):
        if 'user_id' not in session:
            return
        
        group_id = data.get('group_id')
        message = data.get('message')
        
        if not group_id or not message:
            return
        
        if not verify_study_group_membership(group_id, session['user_id']):
            return
        
        room = f"study_group_{group_id}"
        emit('study_group_message', {
            'group_id': group_id,
            'message': message
        }, to=room, include_self=False)
    
    @socketio.on('study_group_task_update')
    def handle_study_group_task_update(data):
        if 'user_id' not in session:
            return
        
        group_id = data.get('group_id')
        if not group_id:
            return
        
        if not verify_study_group_membership(group_id, session['user_id']):
            return
        
        room = f"study_group_{group_id}"
        emit('study_group_task_update', {
            'group_id': group_id
        }, to=room, include_self=False)
    
    @socketio.on('study_group_typing')
    def handle_study_group_typing(data):
        if 'user_id' not in session:
            return
        
        group_id = data.get('group_id')
        if not group_id:
            return
        
        if not verify_study_group_membership(group_id, session['user_id']):
            return
        
        room = f"study_group_{group_id}"
        emit('study_group_typing', {
            'group_id': group_id,
            'user_id': session['user_id'],
            'user_name': f"{session.get('nome', '')} {session.get('cognome', '')}"
        }, to=room, include_self=False)
