
"""
SKAILA - Dashboard Routes
Routes per dashboard specifiche per ruolo
"""

from flask import Blueprint, render_template, session, redirect
from database_manager import db_manager
from gamification import gamification_system
from services.tenant_guard import get_school_stats, get_current_school_id
from ai_chatbot import AISkailaBot

dashboard_bp = Blueprint('dashboard', __name__)

def require_login(f):
    """Decorator per richiedere login"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@dashboard_bp.route('/dashboard')
@require_login
def dashboard():
    """Dashboard principale che reindirizza al ruolo specifico"""
    ruolo = session.get('ruolo', 'studente')
    
    if ruolo == 'admin':
        return redirect('/dashboard/admin')
    elif ruolo == 'professore':
        return redirect('/dashboard/professore')
    elif ruolo == 'genitore':
        return redirect('/dashboard/genitore')
    else:
        return redirect('/dashboard/studente')

@dashboard_bp.route('/dashboard/studente')
@require_login
def dashboard_studente():
    """Dashboard studente con gamification"""
    user_id = session['user_id']
    
    # Dati gamification (con fallback se profilo non esiste)
    try:
        gamification_data = gamification_system.get_user_dashboard(user_id)
        profile = gamification_data.get('profile', {})
    except Exception as e:
        print(f"⚠️ Gamification error for user {user_id}: {e}")
        # Crea profilo minimo di fallback
        gamification_system.get_or_create_profile(user_id)
        gamification_data = gamification_system.get_user_dashboard(user_id)
        profile = gamification_data.get('profile', {})
    
    # Statistiche recenti
    recent_messages = db_manager.query('''
        SELECT COUNT(*) as count FROM messaggi 
        WHERE utente_id = ? AND DATE(timestamp) = DATE('now')
    ''', (user_id,), one=True)['count']
    
    ai_interactions = db_manager.query('''
        SELECT COUNT(*) as count FROM ai_conversations 
        WHERE utente_id = ? AND DATE(timestamp) = DATE('now')
    ''', (user_id,), one=True)['count']
    
    dashboard_stats = {
        'messages_today': recent_messages,
        'ai_questions_today': ai_interactions,
        'current_streak': profile.get('current_streak', 0),
        'total_xp': profile.get('total_xp', 0),
        'current_level': profile.get('current_level', 1)
    }
    
    # SKAILA Connect - Aziende disponibili
    companies = db_manager.query('''
        SELECT id, nome, settore, descrizione, logo, citta, posizione_offerta, 
               tipo_opportunita, requisiti, retribuzione
        FROM skaila_connect_companies 
        WHERE attiva = true 
        ORDER BY created_at DESC 
        LIMIT 3
    ''') or []
    
    return render_template('dashboard_studente.html', 
                         user=session, 
                         gamification=gamification_data,
                         stats=dashboard_stats,
                         companies=companies)

@dashboard_bp.route('/dashboard/professore')
@require_login
def dashboard_professore():
    """Dashboard professore"""
    if session.get('ruolo') != 'professore':
        return redirect('/dashboard')
    
    try:
        # SECURITY: Tenant guard - filtra per school_id
        school_id = get_current_school_id()
        
        # Statistiche classe (con school_id)
        students_count = db_manager.query('''
            SELECT COUNT(*) as count FROM utenti 
            WHERE ruolo = ? AND classe = ? AND scuola_id = ? AND attivo = ?
        ''', ('studente', session.get('classe', ''), school_id, True), one=True)['count']
        
        # Messaggi recenti (con school_id)
        recent_activity = db_manager.query('''
            SELECT u.nome, u.cognome, m.contenuto, m.timestamp
            FROM messaggi m
            JOIN utenti u ON m.utente_id = u.id
            JOIN chat c ON m.chat_id = c.id
            WHERE u.classe = ? AND u.scuola_id = ? AND c.scuola_id = ? 
            AND DATE(m.timestamp) = DATE('now')
            ORDER BY m.timestamp DESC
            LIMIT 10
        ''', (session.get('classe', ''), school_id, school_id))
        
        stats = {
            'students_count': students_count,
            'recent_activity': recent_activity
        }
        
        return render_template('dashboard_professore.html', 
                             user=session, 
                             stats=stats)
    except TenantGuardException:
        # Session mancante o corrotta - redirect a login
        session.clear()
        return redirect('/login')

@dashboard_bp.route('/dashboard/genitore')
@require_login
def dashboard_genitore():
    """Dashboard genitore"""
    if session.get('ruolo') != 'genitore':
        return redirect('/dashboard')
    
    # Per ora dashboard base - da espandere con dati figli
    return render_template('dashboard_genitore.html', user=session)

@dashboard_bp.route('/dashboard/admin')
@require_login
def dashboard_admin():
    """Dashboard amministratore"""
    if session.get('ruolo') != 'admin':
        return redirect('/dashboard')
    
    try:
        # SECURITY: Usa tenant guard per statistiche filtrate per scuola
        school_id = get_current_school_id()
        school_stats = get_school_stats(school_id)
    except TenantGuardException:
        # Session mancante o corrotta - redirect a login
        session.clear()
        return redirect('/login')
    
    # Messaggi di oggi (filtrati per scuola)
    messages_today = db_manager.query('''
        SELECT COUNT(*) as count FROM messaggi m
        JOIN chat c ON m.chat_id = c.id
        WHERE c.school_id = ? AND DATE(m.timestamp) = DATE('now')
    ''', (school_id,), one=True)['count']
    
    # Utenti per ruolo (filtrati per scuola)
    role_stats = db_manager.query('''
        SELECT ruolo, COUNT(*) as count 
        FROM utenti 
        WHERE school_id = ? AND attivo = ? 
        GROUP BY ruolo
    ''', (school_id, True))
    
    admin_stats = {
        'total_users': school_stats['total_users'],
        'messages_today': messages_today,
        'active_chats': school_stats['active_chats'],
        'role_distribution': {row[0]: row[1] for row in role_stats}
    }
    
    return render_template('dashboard_admin.html', 
                         user=session, 
                         stats=admin_stats)

@dashboard_bp.route('/registro')
@require_login
def registro_online():
    """Registro Online - Sistema completo voti e presenze"""
    user_id = session['user_id']
    ruolo = session.get('ruolo', 'studente')
    
    if ruolo == 'studente':
        # Voti studente
        voti = db_manager.query('''
            SELECT materia, voto, tipo_valutazione, data, note 
            FROM voti 
            WHERE studente_id = ? 
            ORDER BY data DESC 
            LIMIT 50
        ''', (user_id,))
        
        # Presenze studente
        presenze = db_manager.query('''
            SELECT data, presente, giustificato, ritardo, note
            FROM presenze 
            WHERE studente_id = ?
            ORDER BY data DESC
            LIMIT 30
        ''', (user_id,))
        
        # Media voti per materia
        medie = db_manager.query('''
            SELECT materia, AVG(voto) as media, COUNT(*) as num_voti
            FROM voti
            WHERE studente_id = ?
            GROUP BY materia
        ''', (user_id,))
        
        return render_template('registro_online.html',
                             user=session,
                             voti=voti or [],
                             presenze=presenze or [],
                             medie=medie or [],
                             ruolo=ruolo)
    
    elif ruolo == 'professore':
        # Vista professore - voti classe
        classe = session.get('classe', '')
        school_id = get_current_school_id()
        
        studenti = db_manager.query('''
            SELECT id, nome, cognome 
            FROM utenti 
            WHERE ruolo = ? AND classe = ? AND scuola_id = ? AND attivo = ?
            ORDER BY cognome, nome
        ''', ('studente', classe, school_id, True))
        
        return render_template('registro_professore.html',
                             user=session,
                             studenti=studenti or [],
                             ruolo=ruolo)
    
    else:
        return redirect('/dashboard')
