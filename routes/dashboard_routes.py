
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
    
    # Dati gamification
    gamification_data = gamification_system.get_user_dashboard(user_id)
    
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
        'current_streak': gamification_data['profile']['current_streak'],
        'total_xp': gamification_data['profile']['total_xp'],
        'current_level': gamification_data['profile']['current_level']
    }
    
    return render_template('dashboard_studente.html', 
                         user=session, 
                         gamification=gamification_data,
                         stats=dashboard_stats)

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
