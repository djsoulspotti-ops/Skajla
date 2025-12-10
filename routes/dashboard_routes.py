"""
SKAJLA - Dashboard Routes
Routes per dashboard specifiche per ruolo
"""

from flask import Blueprint, render_template, session, redirect, flash
from database_manager import db_manager
from gamification import gamification_system
from services.tenant_guard import get_school_stats, get_current_school_id, TenantGuardException
from ai_chatbot import AISkailaBot
from ai_insights_engine import ai_insights_engine
from shared.middleware.auth import require_login, require_auth, require_teacher
from services.dashboard.dashboard_service import dashboard_service
from services.school.school_features_manager import school_features_manager
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@require_login
def dashboard():
    """Dashboard principale che reindirizza al ruolo specifico"""
    ruolo = session.get('ruolo', 'studente')

    if ruolo == 'admin':
        return redirect('/dashboard/admin')
    elif ruolo == 'dirigente':
        return redirect('/dashboard/dirigente')
    elif ruolo == 'professore':
        return redirect('/dashboard/professore')
    elif ruolo == 'genitore':
        return redirect('/dashboard/genitore')
    else:
        return redirect('/dashboard/studente')

@dashboard_bp.route('/dashboard/studente')
@require_login
def dashboard_studente():
    """Dashboard studente con gamification e dati reali"""
    from datetime import datetime, timedelta
    
    user_id = session['user_id']
    school_id = get_current_school_id()

    # Ottieni feature abilitate per questa scuola
    enabled_features = school_features_manager.get_school_features(school_id)

    # ========== VOTI REALI DAL DATABASE (TENANT-ISOLATED) ==========
    # Ultimi voti dello studente - filtro per scuola_id per isolamento tenant
    voti = db_manager.query('''
        SELECT materia, voto, tipo_valutazione, data, note
        FROM voti 
        WHERE studente_id = %s AND scuola_id = %s
        ORDER BY data DESC 
        LIMIT 10
    ''', (user_id, school_id)) or []

    # Media voti per materia - filtro per scuola_id
    medie_materie = db_manager.query('''
        SELECT materia, 
               ROUND(AVG(voto)::numeric, 2) as media, 
               COUNT(*) as num_voti,
               MAX(data) as ultimo_voto
        FROM voti
        WHERE studente_id = %s AND scuola_id = %s
        GROUP BY materia
        ORDER BY materia
    ''', (user_id, school_id)) or []

    # Media generale - filtro per scuola_id
    media_generale = db_manager.query('''
        SELECT ROUND(AVG(voto)::numeric, 2) as media_generale,
               COUNT(*) as totale_voti
        FROM voti
        WHERE studente_id = %s AND scuola_id = %s
    ''', (user_id, school_id), one=True) or {'media_generale': 0, 'totale_voti': 0}

    # Trend voti ultimi 90 giorni per grafico - filtro per scuola_id
    voti_trend = db_manager.query('''
        SELECT data, voto, materia
        FROM voti
        WHERE studente_id = %s AND scuola_id = %s
        AND data >= CURRENT_DATE - INTERVAL '90 days'
        ORDER BY data ASC
    ''', (user_id, school_id)) or []

    # ========== PRESENZE/ASSENZE DAL DATABASE (TENANT-ISOLATED) ==========
    presenze_stats = db_manager.query('''
        SELECT 
            COUNT(*) as giorni_totali,
            SUM(CASE WHEN presente = true THEN 1 ELSE 0 END) as presenze,
            SUM(CASE WHEN presente = false THEN 1 ELSE 0 END) as assenze,
            SUM(CASE WHEN giustificato = true THEN 1 ELSE 0 END) as giustificate,
            SUM(CASE WHEN ritardo > 0 THEN 1 ELSE 0 END) as ritardi
        FROM presenze
        WHERE studente_id = %s AND scuola_id = %s
    ''', (user_id, school_id), one=True) or {
        'giorni_totali': 0, 'presenze': 0, 'assenze': 0, 
        'giustificate': 0, 'ritardi': 0
    }

    # Calcola percentuale presenze
    percentuale_presenze = 0
    if presenze_stats['giorni_totali'] and presenze_stats['giorni_totali'] > 0:
        percentuale_presenze = round(
            (presenze_stats['presenze'] or 0) / presenze_stats['giorni_totali'] * 100, 1
        )

    # Ultime presenze/assenze - filtro per scuola_id
    ultime_presenze = db_manager.query('''
        SELECT data, presente, giustificato, ritardo, note
        FROM presenze
        WHERE studente_id = %s AND scuola_id = %s
        ORDER BY data DESC
        LIMIT 10
    ''', (user_id, school_id)) or []

    # ========== PROSSIMI EVENTI (verifiche, compiti, scadenze) ==========
    upcoming_events = db_manager.query('''
        SELECT id, title, description, event_type, start_datetime, end_datetime
        FROM calendar_events
        WHERE (user_id = %s OR is_school_wide = true)
        AND start_datetime >= CURRENT_TIMESTAMP
        ORDER BY start_datetime ASC
        LIMIT 5
    ''', (user_id,)) or []

    # ========== DATI GAMIFICATION ==========
    gamification_data = None
    profile = {}

    if enabled_features.get('gamification', True):
        try:
            gamification_data = gamification_system.get_user_dashboard(user_id)
            profile = gamification_data.get('profile', {})
        except Exception as e:
            print(f"⚠️ Gamification error for user {user_id}: {e}")
            gamification_system.get_or_create_profile(user_id)
            gamification_data = gamification_system.get_user_dashboard(user_id)
            profile = gamification_data.get('profile', {})

    # Statistiche recenti - usando DashboardService
    daily_stats_service = dashboard_service.get_user_daily_stats(user_id)

    # ========== STATISTICHE DASHBOARD COMPLETE ==========
    dashboard_stats = {
        'messages_today': daily_stats_service['messages_today'],
        'ai_questions_today': daily_stats_service['ai_interactions_today'],
        'current_streak': profile.get('current_streak', 0),
        'total_xp': profile.get('total_xp', 0),
        'current_level': profile.get('current_level', 1),
        'media_voti': media_generale['media_generale'] or 0,
        'totale_voti': media_generale['totale_voti'] or 0,
        'presenze_percentuale': percentuale_presenze,
        'assenze': presenze_stats['assenze'] or 0,
        'assenze_giustificate': presenze_stats['giustificate'] or 0,
        'ritardi': presenze_stats['ritardi'] or 0,
        'giorni_totali': presenze_stats['giorni_totali'] or 0
    }

    # SKAJLA Connect - Aziende disponibili
    companies = db_manager.query('''
        SELECT id, nome, settore, descrizione, logo, citta, posizione_offerta, 
               tipo_opportunita, requisiti, retribuzione
        FROM skaila_connect_companies 
        WHERE attiva = true 
        ORDER BY created_at DESC 
        LIMIT 3
    ''') or []

    # AI Insights
    ai_insights = []

    # Attività recenti
    recent_activities_list = []
    achievements = dashboard_service.get_recent_achievements(user_id, limit=3)

    for ach in achievements:
        recent_activities_list.append({
            'action_type': 'achievement',
            'title': 'Achievement Sbloccato',
            'description': ach['achievement_id'].replace('_', ' ').title(),
            'xp_earned': ach['xp_earned'],
            'timestamp': ach['unlocked_at']
        })

    # Attività da daily analytics
    daily_analytics = db_manager.query('''
        SELECT date, quizzes_completed, messages_sent, ai_interactions, xp_earned
        FROM daily_analytics
        WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY date DESC
        LIMIT 5
    ''', (user_id,)) or []

    for stat in daily_analytics:
        if stat['quizzes_completed'] and stat['quizzes_completed'] > 0:
            recent_activities_list.append({
                'action_type': 'quiz',
                'title': 'Quiz Completato',
                'description': f"{stat['quizzes_completed']} quiz completati",
                'xp_earned': 0,
                'timestamp': stat['date']
            })

    recent_activities = sorted(recent_activities_list, key=lambda x: x['timestamp'], reverse=True)[:5]

    # Prepara dati per Chart.js (trend voti)
    chart_data = {
        'labels': [],
        'datasets': {}
    }
    for voto in voti_trend:
        data_str = voto['data'].strftime('%d/%m') if hasattr(voto['data'], 'strftime') else str(voto['data'])
        materia = voto['materia']
        if materia not in chart_data['datasets']:
            chart_data['datasets'][materia] = []
        chart_data['datasets'][materia].append({
            'x': data_str,
            'y': float(voto['voto'])
        })

    return render_template('dashboard_studente.html', 
                         user=session, 
                         gamification=gamification_data,
                         stats=dashboard_stats,
                         voti=voti,
                         medie_materie=medie_materie,
                         ultime_presenze=ultime_presenze,
                         presenze_stats=presenze_stats,
                         upcoming_events=upcoming_events,
                         chart_data=chart_data,
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

        # Calcola numero classi nella scuola (semplificato)
        user_id = session.get('user_id')
        classi_query = db_manager.query('''
            SELECT COUNT(*) as count FROM classi WHERE scuola_id = %s
        ''', (school_id,), one=True)

        # Numero di classi attive nella scuola
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
    """Dashboard genitore - Vista semplificata: solo voti, assenze, ritardi"""
    if session.get('ruolo') != 'genitore':
        return redirect('/dashboard')
    
    parent_id = session.get('user_id')
    school_id = session.get('school_id', 1)
    
    linked_student = db_manager.query('''
        SELECT u.id, u.nome, u.cognome, u.email
        FROM parent_student_links psl
        JOIN utenti u ON psl.student_id = u.id
        WHERE psl.parent_id = %s AND psl.is_active = true
        LIMIT 1
    ''', (parent_id,), one=True)
    
    if not linked_student:
        return render_template('dashboard_genitore.html', 
                             user=session, 
                             studente=None,
                             voti=[],
                             medie_materie=[],
                             presenze_stats={},
                             ultime_presenze=[])
    
    student_id = linked_student['id']
    
    voti = db_manager.query('''
        SELECT materia, voto, tipo_valutazione, data, note
        FROM voti
        WHERE studente_id = %s AND scuola_id = %s
        ORDER BY data DESC
        LIMIT 15
    ''', (student_id, school_id)) or []
    
    medie_materie = db_manager.query('''
        SELECT materia, 
               ROUND(AVG(voto)::numeric, 2) as media, 
               COUNT(*) as num_voti
        FROM voti
        WHERE studente_id = %s AND scuola_id = %s
        GROUP BY materia
        ORDER BY materia
    ''', (student_id, school_id)) or []
    
    presenze_stats = db_manager.query('''
        SELECT 
            COUNT(*) as giorni_totali,
            SUM(CASE WHEN presente = true THEN 1 ELSE 0 END) as presenze,
            SUM(CASE WHEN presente = false THEN 1 ELSE 0 END) as assenze,
            SUM(CASE WHEN giustificato = true THEN 1 ELSE 0 END) as giustificate,
            SUM(CASE WHEN ritardo > 0 THEN 1 ELSE 0 END) as ritardi
        FROM presenze
        WHERE studente_id = %s AND scuola_id = %s
    ''', (student_id, school_id), one=True) or {
        'giorni_totali': 0, 'presenze': 0, 'assenze': 0, 
        'giustificate': 0, 'ritardi': 0
    }
    
    ultime_presenze = db_manager.query('''
        SELECT data, presente, giustificato, ritardo, note
        FROM presenze
        WHERE studente_id = %s AND scuola_id = %s
        ORDER BY data DESC
        LIMIT 10
    ''', (student_id, school_id)) or []
    
    return render_template('dashboard_genitore.html', 
                         user=session,
                         studente=linked_student,
                         voti=voti,
                         medie_materie=medie_materie,
                         presenze_stats=presenze_stats,
                         ultime_presenze=ultime_presenze)

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

@dashboard_bp.route('/calendario')
@require_auth
def calendario():
    """Calendario accademico"""
    return render_template('calendario.html', user=session)

@dashboard_bp.route('/registro-professore')
@require_auth
@require_teacher
def registro_professore():
    """Registro elettronico per professori"""
    try:
        # Carica studenti della classe del professore
        school_id = get_current_school_id()
        classe = session.get('classe', '')

        studenti = []
        if classe:
            studenti = db_manager.query('''
                SELECT id, nome, cognome, classe 
                FROM utenti 
                WHERE scuola_id = %s AND classe = %s AND ruolo = 'studente'
                ORDER BY cognome, nome
            ''', (school_id, classe))

        return render_template('registro_professore.html', 
                             user=session,
                             studenti=studenti or [])
    except Exception as e:
        logger.error(
            event_type='registro_professore_error',
            domain='dashboard',
            message='Failed to load registro professore page',
            user_id=session.get('user_id'),
            error=str(e),
            exc_info=True
        )
        flash('Errore nel caricare il registro elettronico', 'error')
        return redirect('/dashboard')


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
    """Pagina Gamification V2 completa"""
    from services.gamification.xp_manager_v2 import xp_manager_v2
    from services.gamification.advanced_gamification import RANK_CONFIG, RANK_ORDER
    
    user_id = session['user_id']
    user_data = {
        'id': user_id,
        'nome': session.get('nome', ''),
        'cognome': session.get('cognome', ''),
        'ruolo': session.get('ruolo', 'studente')
    }

    try:
        profile = xp_manager_v2.get_user_profile(user_id)
        if not profile:
            profile = {
                'xp_totale': 0,
                'rango': 'Germoglio',
                'rank_icon': '🌱',
                'livello': 1,
                'streak_corrente': 0,
                'progress_percentage': 0,
                'xp_prossimo_rango': 200,
                'xp_mancanti': 200,
                'prossimo_rango': 'Esploratore',
                'giorni_attivi': 0,
                'sfide_completate': 0
            }
        
        ranks = []
        for rank_name in RANK_ORDER:
            config = RANK_CONFIG[rank_name]
            ranks.append({
                'nome': rank_name,
                'min_xp': config['min_xp'],
                'icon': config['icon'],
                'color': config['color']
            })

    except Exception as e:
        print(f"⚠️ Errore gamification V2: {e}")
        profile = {
            'xp_totale': 0,
            'rango': 'Germoglio',
            'rank_icon': '🌱',
            'livello': 1,
            'streak_corrente': 0,
            'progress_percentage': 0,
            'xp_prossimo_rango': 200,
            'xp_mancanti': 200,
            'prossimo_rango': 'Esploratore',
            'giorni_attivi': 0,
            'sfide_completate': 0
        }
        ranks = []

    return render_template('gamification_dashboard.html',
                         user=user_data,
                         profile=profile,
                         ranks=ranks)


@dashboard_bp.route('/dashboard/dirigente')
@require_login
def dashboard_dirigente():
    """Dashboard Dirigente - Panoramica completa della scuola con KPI avanzati"""
    from datetime import datetime, timedelta
    import random
    
    if session.get('ruolo') != 'dirigente':
        flash('Accesso riservato ai dirigenti', 'error')
        return redirect('/dashboard')
    
    try:
        school_id = get_current_school_id()
    except TenantGuardException:
        session.clear()
        return redirect('/login')
    
    # ========== SCHOOL OVERVIEW SECTION ==========
    # Total students count
    total_students = db_manager.query('''
        SELECT COUNT(*) as count FROM utenti 
        WHERE scuola_id = %s AND ruolo = 'studente' AND attivo = true
    ''', (school_id,), one=True)
    
    # Total teachers count
    total_teachers = db_manager.query('''
        SELECT COUNT(*) as count FROM utenti 
        WHERE scuola_id = %s AND ruolo = 'professore' AND attivo = true
    ''', (school_id,), one=True)
    
    # Total classes count
    total_classes = db_manager.query('''
        SELECT COUNT(*) as count FROM classi 
        WHERE scuola_id = %s
    ''', (school_id,), one=True)
    
    # Average student age - use default value since data_nascita column may not exist
    # In a real scenario, schools would have this data from student records
    avg_student_age = {'avg_age': 15.5}  # Default average age for Italian high schools
    
    # Active users today (filtered by school - join with utenti for tenant isolation)
    active_users_today = db_manager.query('''
        SELECT COUNT(DISTINCT da.user_id) as count 
        FROM daily_analytics da
        JOIN utenti u ON da.user_id = u.id
        WHERE da.date = CURRENT_DATE AND u.scuola_id = %s
    ''', (school_id,), one=True)
    
    overview_stats = {
        'total_students': total_students['count'] if total_students else 0,
        'total_teachers': total_teachers['count'] if total_teachers else 0,
        'total_classes': total_classes['count'] if total_classes else 0,
        'avg_student_age': avg_student_age['avg_age'] if avg_student_age and avg_student_age['avg_age'] else 15.5,
        'active_users_today': active_users_today['count'] if active_users_today else 0
    }
    
    # ========== CLASSES SECTION ==========
    # List of classes with student count, average grade, and attendance rate
    classes_data = db_manager.query('''
        SELECT 
            c.id,
            c.nome as class_name,
            c.anno_scolastico,
            COUNT(DISTINCT u.id) as student_count
        FROM classi c
        LEFT JOIN utenti u ON u.classe_id = c.id AND u.ruolo = 'studente' AND u.attivo = true
        WHERE c.scuola_id = %s
        GROUP BY c.id, c.nome, c.anno_scolastico
        ORDER BY c.nome
    ''', (school_id,)) or []
    
    # Get average grades per class
    class_grades = db_manager.query('''
        SELECT 
            u.classe_id,
            ROUND(AVG(v.voto)::numeric, 2) as avg_grade
        FROM voti v
        JOIN utenti u ON v.studente_id = u.id
        WHERE u.scuola_id = %s AND u.ruolo = 'studente'
        GROUP BY u.classe_id
    ''', (school_id,)) or []
    
    grade_map = {g['classe_id']: g['avg_grade'] for g in class_grades}
    
    # Get attendance rate per class
    class_attendance = db_manager.query('''
        SELECT 
            u.classe_id,
            ROUND(
                (SUM(CASE WHEN p.presente = true THEN 1 ELSE 0 END)::numeric / 
                NULLIF(COUNT(*)::numeric, 0)) * 100, 1
            ) as attendance_rate
        FROM presenze p
        JOIN utenti u ON p.studente_id = u.id
        WHERE u.scuola_id = %s AND u.ruolo = 'studente'
        GROUP BY u.classe_id
    ''', (school_id,)) or []
    
    attendance_map = {a['classe_id']: a['attendance_rate'] for a in class_attendance}
    
    # Combine classes data
    for cls in classes_data:
        cls['avg_grade'] = grade_map.get(cls['id'], 0) or 0
        cls['attendance_rate'] = attendance_map.get(cls['id'], 0) or 0
    
    # ========== TEACHERS SECTION WITH RATINGS ==========
    teachers_data = db_manager.query('''
        SELECT 
            u.id,
            u.nome,
            u.cognome,
            u.email,
            'Materie varie' as subject
        FROM utenti u
        WHERE u.scuola_id = %s AND u.ruolo = 'professore' AND u.attivo = true
        ORDER BY u.cognome, u.nome
    ''', (school_id,)) or []
    
    # Get teacher ratings
    teacher_ratings = db_manager.query('''
        SELECT 
            teacher_id,
            ROUND(AVG(rating)::numeric, 2) as avg_rating,
            COUNT(*) as rating_count
        FROM teacher_ratings
        WHERE scuola_id = %s
        GROUP BY teacher_id
    ''', (school_id,)) or []
    
    rating_map = {r['teacher_id']: {'avg_rating': r['avg_rating'], 'count': r['rating_count']} for r in teacher_ratings}
    
    # Combine teachers data with ratings
    for teacher in teachers_data:
        rating_data = rating_map.get(teacher['id'], {'avg_rating': 0, 'count': 0})
        teacher['avg_rating'] = float(rating_data['avg_rating']) if rating_data['avg_rating'] else 0
        teacher['rating_count'] = rating_data['count']
    
    # ========== ECONOMIC PERFORMANCE SECTION (Tenant-Scoped) ==========
    # Using €599/month professional tier pricing for THIS school only
    PRICE_PER_MONTH = 599
    
    # Check if THIS school has an active subscription (tenant-isolated)
    school_subscription = db_manager.query('''
        SELECT attiva FROM scuole WHERE id = %s
    ''', (school_id,), one=True)
    
    is_active = school_subscription['attiva'] if school_subscription else True
    subscription_count = 1 if is_active else 0  # Only count THIS school
    monthly_revenue = PRICE_PER_MONTH  # Revenue for THIS school only
    
    # Cost per student calculation for THIS school
    total_active_students = overview_stats['total_students']
    cost_per_student = round(monthly_revenue / max(total_active_students, 1), 2)
    
    # Revenue trend for THIS school (simulated growth from school activation)
    revenue_trend = []
    months = ['Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    base_revenue = monthly_revenue * 0.85  # Starting point for this school
    for i, month in enumerate(months):
        growth_factor = 1 + (i * 0.02)  # 2% monthly growth for this school
        revenue_trend.append({
            'month': month,
            'revenue': round(base_revenue * growth_factor)
        })
    
    economic_stats = {
        'monthly_revenue': monthly_revenue,
        'active_subscriptions': subscription_count,
        'cost_per_student': cost_per_student,
        'revenue_trend': revenue_trend,
        'yoy_growth': 18.5  # Fixed growth rate indicator for professional tier
    }
    
    # ========== ADDITIONAL KPIs ==========
    # Platform engagement rate (filtered by school)
    total_users = overview_stats['total_students'] + overview_stats['total_teachers']
    active_last_7_days = db_manager.query('''
        SELECT COUNT(DISTINCT da.user_id) as count 
        FROM daily_analytics da
        JOIN utenti u ON da.user_id = u.id
        WHERE da.date >= CURRENT_DATE - INTERVAL '7 days' AND u.scuola_id = %s
    ''', (school_id,), one=True)
    
    engagement_rate = 0
    if total_users > 0 and active_last_7_days:
        engagement_rate = round((active_last_7_days['count'] / max(total_users, 1)) * 100, 1)
    
    # AI Coach usage statistics (filtered by school)
    ai_usage = db_manager.query('''
        SELECT 
            COUNT(*) as total_interactions,
            COUNT(DISTINCT ac.utente_id) as unique_users
        FROM ai_conversations ac
        JOIN utenti u ON ac.utente_id = u.id
        WHERE ac.timestamp >= CURRENT_DATE - INTERVAL '30 days' AND u.scuola_id = %s
    ''', (school_id,), one=True) or {'total_interactions': 0, 'unique_users': 0}
    
    # Gamification participation rate (filtered by school)
    gamification_participants = db_manager.query('''
        SELECT COUNT(DISTINCT xl.user_id) as count 
        FROM xp_logs xl
        JOIN utenti u ON xl.user_id = u.id
        WHERE xl.created_at >= CURRENT_DATE - INTERVAL '30 days' AND u.scuola_id = %s
    ''', (school_id,), one=True)
    
    gamification_rate = 0
    if overview_stats['total_students'] > 0 and gamification_participants:
        gamification_rate = round((gamification_participants['count'] / max(overview_stats['total_students'], 1)) * 100, 1)
    
    # Parent engagement rate
    parent_count = db_manager.query('''
        SELECT COUNT(*) as count FROM utenti 
        WHERE scuola_id = %s AND ruolo = 'genitore' AND attivo = true
    ''', (school_id,), one=True)
    
    active_parents = db_manager.query('''
        SELECT COUNT(DISTINCT u.id) as count 
        FROM utenti u
        JOIN daily_analytics da ON da.user_id = u.id
        WHERE u.scuola_id = %s AND u.ruolo = 'genitore' 
        AND da.date >= CURRENT_DATE - INTERVAL '7 days'
    ''', (school_id,), one=True)
    
    parent_engagement = 0
    if parent_count and parent_count['count'] > 0 and active_parents:
        parent_engagement = round((active_parents['count'] / max(parent_count['count'], 1)) * 100, 1)
    
    kpis = {
        'engagement_rate': min(engagement_rate, 100),
        'ai_total_interactions': ai_usage['total_interactions'] or 0,
        'ai_unique_users': ai_usage['unique_users'] or 0,
        'gamification_rate': min(gamification_rate, 100),
        'parent_engagement': min(parent_engagement, 100),
        'parent_count': parent_count['count'] if parent_count else 0
    }
    
    # ========== ATTENDANCE TREND (Last 30 days) ==========
    attendance_trend = db_manager.query('''
        SELECT 
            data as date,
            COUNT(*) as total,
            SUM(CASE WHEN presente = true THEN 1 ELSE 0 END) as present,
            ROUND(
                (SUM(CASE WHEN presente = true THEN 1 ELSE 0 END)::numeric / 
                NULLIF(COUNT(*)::numeric, 0)) * 100, 1
            ) as rate
        FROM presenze p
        JOIN utenti u ON p.studente_id = u.id
        WHERE u.scuola_id = %s AND p.data >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY p.data
        ORDER BY p.data
    ''', (school_id,)) or []
    
    # ========== GRADE DISTRIBUTION ==========
    grade_distribution = db_manager.query('''
        SELECT 
            CASE 
                WHEN voto >= 9 THEN 'Eccellente (9-10)'
                WHEN voto >= 7 THEN 'Buono (7-8)'
                WHEN voto >= 6 THEN 'Sufficiente (6)'
                ELSE 'Insufficiente (<6)'
            END as category,
            COUNT(*) as count
        FROM voti v
        JOIN utenti u ON v.studente_id = u.id
        WHERE u.scuola_id = %s
        GROUP BY 1
        ORDER BY MIN(voto) DESC
    ''', (school_id,)) or []
    
    # School average grade
    school_avg_grade = db_manager.query('''
        SELECT ROUND(AVG(voto)::numeric, 2) as avg_grade
        FROM voti v
        JOIN utenti u ON v.studente_id = u.id
        WHERE u.scuola_id = %s
    ''', (school_id,), one=True)
    
    # School name
    school_info = db_manager.query('''
        SELECT nome FROM scuole WHERE id = %s
    ''', (school_id,), one=True)
    
    return render_template('dashboard_dirigente_new.html',
                         user=session,
                         school_name=school_info['nome'] if school_info else 'La tua scuola',
                         overview=overview_stats,
                         classes=classes_data,
                         teachers=teachers_data,
                         economic=economic_stats,
                         kpis=kpis,
                         attendance_trend=attendance_trend,
                         grade_distribution=grade_distribution,
                         school_avg_grade=school_avg_grade['avg_grade'] if school_avg_grade and school_avg_grade['avg_grade'] else 0)