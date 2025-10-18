"""
SKAILA - Tenant Guard System
Sistema centralizzato per garantire isolamento multi-tenant tra scuole
"""

from flask import session
from database_manager import db_manager


class TenantGuardException(Exception):
    """Eccezione sollevata quando un'operazione viola l'isolamento tenant"""
    pass


def get_current_school_id():
    """
    Ottiene lo school_id dell'utente corrente dalla sessione
    Se non presente, lo recupera dal database e lo aggiunge alla sessione
    Raises TenantGuardException se non trovato
    """
    school_id = session.get('school_id')
    
    if not school_id:
        # Fallback: recupera dal database usando user_id
        user_id = session.get('user_id')
        if not user_id:
            raise TenantGuardException("user_id non trovato in sessione")
        
        user = db_manager.query('''
            SELECT school_id FROM utenti WHERE id = ?
        ''', (user_id,), one=True)
        
        if not user or not user.get('school_id'):
            raise TenantGuardException(f"school_id non trovato per utente {user_id}")
        
        # Aggiorna la sessione per le prossime richieste
        school_id = user['school_id']
        session['school_id'] = school_id
    
    return school_id


def verify_chat_belongs_to_school(chat_id, school_id=None):
    """
    Verifica che una chat appartenga alla scuola dell'utente
    Returns: True se la chat appartiene alla scuola, False altrimenti
    """
    if school_id is None:
        school_id = get_current_school_id()
    
    result = db_manager.query('''
        SELECT 1 FROM chat 
        WHERE id = ? AND school_id = ?
    ''', (chat_id, school_id), one=True)
    
    return result is not None


def verify_user_belongs_to_school(user_id, school_id=None):
    """
    Verifica che un utente appartenga alla scuola
    Returns: True se l'utente appartiene alla scuola, False altrimenti
    """
    if school_id is None:
        school_id = get_current_school_id()
    
    result = db_manager.query('''
        SELECT 1 FROM utenti 
        WHERE id = ? AND school_id = ?
    ''', (user_id, school_id), one=True)
    
    return result is not None


def get_school_filtered_query(base_query, table_alias=''):
    """
    Aggiunge automaticamente il filtro school_id a una query
    
    Args:
        base_query: Query SQL base
        table_alias: Alias della tabella principale (opzionale)
    
    Returns:
        Tupla (query_with_filter, params) con school_id aggiunto
    """
    school_id = get_current_school_id()
    
    # Determina il prefisso della tabella
    prefix = f"{table_alias}." if table_alias else ""
    
    # Aggiunge il filtro school_id
    if 'WHERE' in base_query.upper():
        filtered_query = base_query + f" AND {prefix}school_id = ?"
    else:
        filtered_query = base_query + f" WHERE {prefix}school_id = ?"
    
    return filtered_query, school_id


def require_same_school(user_id_to_check):
    """
    Decorator/helper che verifica che un user_id appartenga alla stessa scuola
    Raises TenantGuardException se la verifica fallisce
    """
    current_school = get_current_school_id()
    
    if not verify_user_belongs_to_school(user_id_to_check, current_school):
        raise TenantGuardException(
            f"Utente {user_id_to_check} non appartiene alla scuola {current_school}"
        )
    
    return True


def get_chat_members_query(chat_id, school_id=None):
    """
    Query sicura per ottenere i membri di una chat con tenant filtering
    """
    if school_id is None:
        school_id = get_current_school_id()
    
    # Verifica prima che la chat appartenga alla scuola
    if not verify_chat_belongs_to_school(chat_id, school_id):
        raise TenantGuardException(f"Chat {chat_id} non appartiene alla scuola {school_id}")
    
    return db_manager.query('''
        SELECT u.* FROM utenti u
        JOIN partecipanti_chat pc ON u.id = pc.utente_id
        WHERE pc.chat_id = ? AND u.school_id = ?
    ''', (chat_id, school_id))


# Helper per statistiche con tenant guard
def get_school_stats(school_id=None):
    """
    Ottiene statistiche filtrate per scuola
    """
    if school_id is None:
        school_id = get_current_school_id()
    
    stats = {}
    
    # Conta utenti della scuola
    stats['total_users'] = db_manager.query('''
        SELECT COUNT(*) as count FROM utenti 
        WHERE school_id = ? AND attivo = ?
    ''', (school_id, True), one=True)['count']
    
    # Conta messaggi della scuola (via chat)
    stats['total_messages'] = db_manager.query('''
        SELECT COUNT(*) as count FROM messaggi m
        JOIN chat c ON m.chat_id = c.id
        WHERE c.school_id = ?
    ''', (school_id,), one=True)['count']
    
    # Conta chat della scuola
    stats['active_chats'] = db_manager.query('''
        SELECT COUNT(*) as count FROM chat 
        WHERE school_id = ?
    ''', (school_id,), one=True)['count']
    
    return stats
