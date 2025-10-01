
"""
SKAILA - Socket.IO Events
Eventi real-time per chat e notifiche
"""

from flask_socketio import emit, join_room, leave_room
from flask import session
from database_manager import db_manager
from gamification import gamification_system
from services.tenant_guard import verify_chat_belongs_to_school, get_current_school_id, TenantGuardException

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
                
                db_manager.execute('UPDATE utenti SET status_online = ? WHERE id = ?', (True, session['user_id']))

                # Emit solo alla scuola dell'utente, NON broadcast globale
                emit('user_connected', {
                    'nome': session['nome'],
                    'cognome': session['cognome'],
                    'ruolo': session['ruolo']
                }, room=f"school_{school_id}")
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
                
                db_manager.execute('UPDATE utenti SET status_online = ? WHERE id = ?', (False, session['user_id']))

                emit('user_disconnected', {
                    'nome': session['nome'],
                    'cognome': session['cognome']
                }, room=f"school_{school_id}")
                
                leave_room(f"school_{school_id}")
            except TenantGuardException:
                # User senza school_id, skip presence broadcast
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
            WHERE chat_id = ? AND utente_id = ?
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
            WHERE chat_id = ? AND utente_id = ?
        ''', (conversation_id, session['user_id']), one=True)

        if not is_member:
            emit('error', {'message': 'Non autorizzato a inviare messaggi in questa chat'})
            return

        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO messaggi (chat_id, utente_id, contenuto)
                VALUES (?, ?, ?)
            ''', (conversation_id, session['user_id'], contenuto))

            message_id = cursor.lastrowid

            messaggio = conn.execute('''
                SELECT m.*, u.nome, u.cognome, u.username, u.ruolo,
                       m.timestamp as data_invio
                FROM messaggi m
                JOIN utenti u ON m.utente_id = u.id
                WHERE m.id = ?
            ''', (message_id,)).fetchone()

        # Gamification
        gamification_system.award_xp(session['user_id'], 'message_sent', description="Messaggio in chat")

        emit('new_message', dict(messaggio), room=f"chat_{conversation_id}")

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
            WHERE chat_id = ? AND utente_id = ?
        ''', (conversation_id, session['user_id']), one=True)

        if not is_member:
            return

        emit('user_typing', {
            'conversation_id': conversation_id,
            'user_name': session['nome'],
            'typing': True
        }, room=f"chat_{conversation_id}", include_self=False)

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
            WHERE chat_id = ? AND utente_id = ?
        ''', (conversation_id, session['user_id']), one=True)

        if not is_member:
            return

        emit('user_typing', {
            'conversation_id': conversation_id,
            'user_name': session['nome'],
            'typing': False
        }, room=f"chat_{conversation_id}", include_self=False)
