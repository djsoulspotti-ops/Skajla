
"""
SKAILA - Socket.IO Events
Eventi real-time per chat e notifiche
"""

import time
from flask_socketio import emit, join_room, leave_room
from flask import session
from database_manager import db_manager
from gamification import gamification_system
from services.tenant_guard import verify_chat_belongs_to_school, get_current_school_id, TenantGuardException
from ai_chatbot import ai_bot

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
                SELECT id FROM utenti 
                WHERE scuola_id = %s AND status_online = true AND attivo = true
            ''', (school_id,))
            
            user_ids = [u[0] if isinstance(u, tuple) else u.get('id', u['id']) for u in (online_users or [])]
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
                context="Interazione con SKAILA Coach"
            )
            
        except Exception as e:
            print(f"Errore AI chatbot: {e}")
            emit('ai_error', {
                'message': 'Errore durante la generazione della risposta. Riprova.'
            })
