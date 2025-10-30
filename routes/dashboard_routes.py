
"""
SKAILA - Dashboard Routes
Routes per dashboard specifiche per ruolo
"""

from flask import Blueprint, render_template, session, redirect
from database_manager import db_manager
from gamification import gamification_system
from services.tenant_guard import get_school_stats, get_current_school_id, TenantGuardException
from ai_chatbot import AISkailaBot
from ai_insights_engine import ai_insights_engine
from shared.middleware.auth import require_login
from services.dashboard.dashboard_service import dashboard_service
from services.school.school_features_manager import school_features_manager

dashboard_bp = Blueprint('dashboard', __name__)

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
    school_id = get_current_school_id()
    
    # Ottieni feature abilitate per questa scuola
    enabled_features = school_features_manager.get_school_features(school_id)
    
    # Dati gamification (con fallback se profilo non esiste)
    gamification_data = None
    profile = {}
    
    if enabled_features.get('gamification', True):
        try:
            gamification_data = gamification_system.get_user_dashboard(user_id)
            profile = gamification_data.get('profile', {})
        except Exception as e:
            print(f"⚠️ Gamification error for user {user_id}: {e}")
            # Crea profilo minimo di fallback
            gamification_system.get_or_create_profile(user_id)
            gamification_data = gamification_system.get_user_dashboard(user_id)
            profile = gamification_data.get('profile', {})
    
    # Statistiche recenti - usando DashboardService
    daily_stats = dashboard_service.get_user_daily_stats(user_id)
    
    dashboard_stats = {
        'messages_today': daily_stats['messages_today'],
        'ai_questions_today': daily_stats['ai_interactions_today'],
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
    
    # AI Insights intelligenti (ML + statistica) - Temporaneamente disabilitato
    ai_insights = []  # ai_insights_engine.generate_insights(user_id)
    
    # Attività recenti (dai daily_analytics e achievements)
    recent_activities_list = []
    
    # Achievement recenti - usando DashboardService
    achievements = dashboard_service.get_recent_achievements(user_id, limit=3)
    
    for ach in achievements:
        recent_activities_list.append({
            'action_type': 'achievement',
            'title': 'Achievement Sbloccato',
            'description': ach['achievement_id'].replace('_', ' ').title(),
            'xp_earned': ach['xp_earned'],
            'timestamp': ach['unlocked_at']
        })
    
    # Attività da daily analytics (ultimi 7 giorni)
    daily_stats = db_manager.query('''
        SELECT date, quizzes_completed, messages_sent, ai_interactions, xp_earned
        FROM daily_analytics
        WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY date DESC
        LIMIT 5
    ''', (user_id,)) or []
    
    for stat in daily_stats:
        if stat['quizzes_completed'] and stat['quizzes_completed'] > 0:
            recent_activities_list.append({
                'action_type': 'quiz',
                'title': 'Quiz Completato',
                'description': f"{stat['quizzes_completed']} quiz completati",
                'xp_earned': 0,
                'timestamp': stat['date']
            })
        if stat['messages_sent'] and stat['messages_sent'] > 0:
            recent_activities_list.append({
                'action_type': 'message',
                'title': 'Messaggi Inviati',
                'description': f"{stat['messages_sent']} messaggi",
                'xp_earned': 0,
                'timestamp': stat['date']
            })
    
    # Ordina per timestamp e prendi i primi 5
    recent_activities = sorted(recent_activities_list, key=lambda x: x['timestamp'], reverse=True)[:5]
    
    return render_template('dashboard_studente.html', 
                         user=session, 
                         gamification=gamification_data,
                         stats=dashboard_stats,
                         companies=companies if enabled_features.get('skaila_connect', True) else [],
                         ai_insights=ai_insights if enabled_features.get('ai_coach', True) else [],
                         recent_activities=recent_activities,
                         enabled_features=enabled_features)

@dashboard_bp.route('/dashboard/professore')
@require_login
def dashboard_professore():
    """Dashboard professore - SOLO STATISTICHE AGGREGATE"""
    if session.get('ruolo') != 'professore':
        return redirect('/dashboard')
    
    try:
        # SECURITY: Tenant guard - filtra per school_id
        school_id = get_current_school_id()
        classe = session.get('classe', '')
        
        # 📊 STATISTICHE AGGREGATE CLASSE (no dati individuali)
        students_count = db_manager.query('''
            SELECT COUNT(*) as count FROM utenti 
            WHERE ruolo = %s AND classe = %s AND scuola_id = %s AND attivo = %s
        ''', ('studente', classe, school_id, True), one=True)['count']
        
        # Media voti classe
        avg_grades = db_manager.query('''
            SELECT AVG(voto) as media_classe
            FROM registro_voti rv
            JOIN utenti u ON rv.student_id = u.id
            WHERE u.classe = %s AND u.scuola_id = %s
        ''', (classe, school_id), one=True)
        
        # Tasso presenze aggregato
        attendance = db_manager.query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'presente' THEN 1 ELSE 0 END) as presenti
            FROM registro_presenze rp
            JOIN utenti u ON rp.student_id = u.id
            WHERE u.classe = %s AND u.scuola_id = %s
        ''', (classe, school_id), one=True)
        
        presenza_perc = 0
        if attendance and attendance['total'] > 0:
            presenza_perc = round((attendance['presenti'] / attendance['total']) * 100, 1)
        
        # FIX BUG: Calcola numero reale di classi insegnate dal professore
        # Query tabella docenti_classi per ottenere classi del professore corrente
        user_id = session.get('user_id')
        classi_query = db_manager.query('''
            SELECT COUNT(DISTINCT classe_id) as count
            FROM docenti_classi
            WHERE docente_id = %s
        ''', (user_id,), one=True)
        
        # Se non ci sono record in docenti_classi, fallback a 1 (classe principale del professore)
        classi_attive = classi_query['count'] if classi_query and classi_query['count'] > 0 else 1
        
        stats = {
            'total_studenti': students_count,
            'classi_attive': classi_attive,
            'media_classe': round(avg_grades['media_classe'], 1) if avg_grades and avg_grades['media_classe'] else 0,
            'tasso_presenze': presenza_perc
        }
        
        return render_template('dashboard_professore.html', 
                             user=session, 
                             **stats)
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
        WHERE c.school_id = %s AND DATE(m.timestamp) = CURRENT_DATE
    ''', (school_id,), one=True)['count']
    
    # Utenti per ruolo (filtrati per scuola)
    role_stats = db_manager.query('''
        SELECT ruolo, COUNT(*) as count 
        FROM utenti 
        WHERE school_id = %s AND attivo = %s 
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
            WHERE studente_id = %s 
            ORDER BY data DESC 
            LIMIT 50
        ''', (user_id,))
        
        # Presenze studente
        presenze = db_manager.query('''
            SELECT data, presente, giustificato, ritardo, note
            FROM presenze 
            WHERE studente_id = %s
            ORDER BY data DESC
            LIMIT 30
        ''', (user_id,))
        
        # Media voti per materia
        medie = db_manager.query('''
            SELECT materia, AVG(voto) as media, COUNT(*) as num_voti
            FROM voti
            WHERE studente_id = %s
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
            WHERE ruolo = %s AND classe = %s AND scuola_id = %s AND attivo = %s
            ORDER BY cognome, nome
        ''', ('studente', classe, school_id, True))
        
        return render_template('registro_professore.html',
                             user=session,
                             studenti=studenti or [],
                             ruolo=ruolo)
    
    else:
        return redirect('/dashboard')

@dashboard_bp.route('/gamification')
@require_login
def gamification_page():
    """Pagina Gamification completa"""
    user_id = session['user_id']
    
    try:
        user_stats = gamification_system.get_user_stats(user_id)
        leaderboard = db_manager.query('''
            SELECT u.nome, u.cognome, ug.total_xp, ug.current_level
            FROM user_gamification ug
            JOIN utenti u ON ug.user_id = u.id
            ORDER BY ug.total_xp DESC
            LIMIT 10
        ''')
        
        achievements = db_manager.query('''
            SELECT achievement_id, unlocked_at, xp_earned
            FROM user_achievements
            WHERE user_id = %s
            ORDER BY unlocked_at DESC
        ''', (user_id,))
        
        badges = db_manager.query('''
            SELECT badge_id, earned_at, xp_earned, rarity
            FROM user_badges
            WHERE user_id = %s
            ORDER BY earned_at DESC
        ''', (user_id,))
        
    except Exception as e:
        print(f"⚠️ Errore gamification: {e}")
        user_stats = {'total_xp': 0, 'current_level': 1, 'current_streak': 0}
        leaderboard = []
        achievements = []
        badges = []
    
    return render_template('gamification_dashboard.html',
                         stats=user_stats,
                         leaderboard=leaderboard,
                         achievements=achievements,
                         badges=badges)
