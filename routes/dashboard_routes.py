
"""
SKAILA - Dashboard Routes
Routes per dashboard specifiche per ruolo
"""

from flask import Blueprint, render_template, session, redirect
from database_manager import db_manager
from gamification import gamification_system
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
    with db_manager.get_connection() as conn:
        recent_messages = conn.execute('''
            SELECT COUNT(*) FROM messaggi 
            WHERE utente_id = ? AND DATE(timestamp) = DATE('now')
        ''', (user_id,)).fetchone()[0]
        
        ai_interactions = conn.execute('''
            SELECT COUNT(*) FROM ai_conversations 
            WHERE utente_id = ? AND DATE(timestamp) = DATE('now')
        ''', (user_id,)).fetchone()[0]
    
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
    
    with db_manager.get_connection() as conn:
        # Statistiche classe
        students_count = conn.execute('''
            SELECT COUNT(*) FROM utenti 
            WHERE ruolo = 'studente' AND classe = ? AND attivo = 1
        ''', (session.get('classe', ''),)).fetchone()[0]
        
        # Messaggi recenti
        recent_activity = conn.execute('''
            SELECT u.nome, u.cognome, m.contenuto, m.timestamp
            FROM messaggi m
            JOIN utenti u ON m.utente_id = u.id
            WHERE u.classe = ? AND DATE(m.timestamp) = DATE('now')
            ORDER BY m.timestamp DESC
            LIMIT 10
        ''', (session.get('classe', ''),)).fetchall()
    
    stats = {
        'students_count': students_count,
        'recent_activity': recent_activity
    }
    
    return render_template('dashboard_professore.html', 
                         user=session, 
                         stats=stats)

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
    
    with db_manager.get_connection() as conn:
        # Statistiche generali
        total_users = conn.execute('SELECT COUNT(*) FROM utenti WHERE attivo = 1').fetchone()[0]
        total_messages = conn.execute('SELECT COUNT(*) FROM messaggi WHERE DATE(timestamp) = DATE("now")').fetchone()[0]
        active_chats = conn.execute('SELECT COUNT(*) FROM chat').fetchone()[0]
        
        # Utenti per ruolo
        role_stats = conn.execute('''
            SELECT ruolo, COUNT(*) as count 
            FROM utenti 
            WHERE attivo = 1 
            GROUP BY ruolo
        ''').fetchall()
    
    admin_stats = {
        'total_users': total_users,
        'messages_today': total_messages,
        'active_chats': active_chats,
        'role_distribution': {row[0]: row[1] for row in role_stats}
    }
    
    return render_template('dashboard_admin.html', 
                         user=session, 
                         stats=admin_stats)
