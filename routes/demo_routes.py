"""
SKAJLA - Demo Routes
Route demo sicure con SOLO dati mock (nessun accesso database reale)
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from services.ai.gemini_chatbot import gemini_chatbot

demo_bp = Blueprint('demo', __name__, url_prefix='/demo')


@demo_bp.route('/dashboard')
def demo_dashboard_redirect():
    """Redirect to student dashboard demo (default)"""
    return redirect(url_for('demo.demo_dashboard_studente'))


@demo_bp.route('/ai/chat', methods=['POST'])
def demo_ai_chat_api():
    """
    Demo AI Chat API endpoint - No authentication required
    Uses GeminiChatbot with mock user for demo purposes
    """
    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message.strip():
            return jsonify({'success': False, 'error': 'Messaggio vuoto'}), 400

        demo_user_id = 1
        demo_user_name = 'Demo'
        
        result = gemini_chatbot.generate_response(
            message=message,
            user_id=demo_user_id,
            user_name=demo_user_name,
            user_role='studente'
        )

        return jsonify({
            'success': result.get('success', True),
            'response': result.get('response', ''),
            'xp_earned': result.get('xp_awarded', 0),
            'xp_awarded': result.get('xp_awarded', 0),
            'rank_up': result.get('rank_up', False),
            'new_rank': result.get('new_rank'),
            'gamification': result.get('gamification', {}),
            'ai_mode': result.get('ai_mode', 'gemini')
        })

    except Exception as e:
        print(f"Errore API /demo/ai/chat: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore durante la generazione della risposta',
            'response': 'Mi dispiace, ho avuto un problema tecnico. Riprova tra poco!'
        }), 500

def get_demo_session_studente():
    """Sessione demo per studente"""
    return {
        'user_id': -999,  # ID speciale per demo
        'nome': 'Marco',
        'cognome': 'Demo',
        'email': 'demo@skaila.it',
        'ruolo': 'studente',
        'classe': '3A',
        'scuola_id': -1,  # Scuola demo (non esiste)
        'demo_mode': True
    }

def get_demo_session_professore():
    """Sessione demo per professore"""
    return {
        'user_id': -998,  # ID speciale per demo
        'nome': 'Prof. Maria',
        'cognome': 'Demo',
        'email': 'prof.demo@skaila.it',
        'ruolo': 'professore',
        'classe': '3A',
        'scuola_id': -1,  # Scuola demo (non esiste)
        'demo_mode': True
    }

@demo_bp.route('/dashboard/studente')
def demo_dashboard_studente():
    """Demo dashboard studente - SOLO DATI MOCK"""
    from datetime import datetime, timedelta
    
    demo_user = get_demo_session_studente()
    
    # Feature abilitate (tutte attive per demo)
    enabled_features = {
        'gamification': True,
        'ai_coach': True,
        'calendario': True,
        'registro_elettronico': True,
        'materiali_didattici': True,
        'skaila_connect': True
    }
    
    # Dati gamification mock
    gamification_data = {
        'profile': {
            'livello': 12,
            'xp_totale': 2450,
            'current_streak': 7,
            'total_xp': 2450,
            'current_level': 12
        },
        'progress': {
            'xp_for_next_level': 3000,
            'progress_percentage': 82
        }
    }
    
    # Voti mock
    voti = [
        {'materia': 'Matematica', 'voto': 9.0, 'tipo_valutazione': 'Scritto', 'data': datetime.now() - timedelta(days=2), 'note': 'Ottimo lavoro'},
        {'materia': 'Italiano', 'voto': 8.5, 'tipo_valutazione': 'Orale', 'data': datetime.now() - timedelta(days=5), 'note': ''},
        {'materia': 'Storia', 'voto': 7.5, 'tipo_valutazione': 'Scritto', 'data': datetime.now() - timedelta(days=8), 'note': ''},
        {'materia': 'Inglese', 'voto': 9.5, 'tipo_valutazione': 'Orale', 'data': datetime.now() - timedelta(days=10), 'note': 'Eccellente pronuncia'},
        {'materia': 'Fisica', 'voto': 6.5, 'tipo_valutazione': 'Scritto', 'data': datetime.now() - timedelta(days=12), 'note': 'Da migliorare'}
    ]
    
    # Medie per materia mock
    medie_materie = [
        {'materia': 'Matematica', 'media': 8.5, 'num_voti': 5, 'ultimo_voto': datetime.now() - timedelta(days=2)},
        {'materia': 'Italiano', 'media': 8.0, 'num_voti': 4, 'ultimo_voto': datetime.now() - timedelta(days=5)},
        {'materia': 'Storia', 'media': 7.5, 'num_voti': 3, 'ultimo_voto': datetime.now() - timedelta(days=8)},
        {'materia': 'Inglese', 'media': 9.0, 'num_voti': 4, 'ultimo_voto': datetime.now() - timedelta(days=10)},
        {'materia': 'Fisica', 'media': 7.0, 'num_voti': 3, 'ultimo_voto': datetime.now() - timedelta(days=12)}
    ]
    
    # Presenze mock
    ultime_presenze = [
        {'data': datetime.now() - timedelta(days=1), 'presente': True, 'giustificato': False, 'ritardo': False, 'note': ''},
        {'data': datetime.now() - timedelta(days=2), 'presente': True, 'giustificato': False, 'ritardo': True, 'note': 'Ritardo 10 min'},
        {'data': datetime.now() - timedelta(days=3), 'presente': False, 'giustificato': True, 'ritardo': False, 'note': 'Visita medica'},
        {'data': datetime.now() - timedelta(days=4), 'presente': True, 'giustificato': False, 'ritardo': False, 'note': ''},
        {'data': datetime.now() - timedelta(days=5), 'presente': True, 'giustificato': False, 'ritardo': False, 'note': ''}
    ]
    
    presenze_stats = {
        'giorni_totali': 50,
        'presenze': 47,
        'assenze': 3,
        'giustificate': 2,
        'ritardi': 4
    }
    
    # Eventi prossimi mock
    upcoming_events = [
        {'id': 1, 'title': 'Verifica di Matematica', 'description': 'Algebra e geometria', 'event_type': 'verifica', 'start_datetime': datetime.now() + timedelta(days=3)},
        {'id': 2, 'title': 'Consegna Progetto Informatica', 'description': 'Progetto Python', 'event_type': 'compito', 'start_datetime': datetime.now() + timedelta(days=5)},
        {'id': 3, 'title': 'Colloquio Genitori', 'description': 'Incontro trimestrale', 'event_type': 'evento', 'start_datetime': datetime.now() + timedelta(days=7)}
    ]
    
    # Dati per grafico
    chart_data = {
        'labels': [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(30, 0, -5)],
        'datasets': {
            'Matematica': [7.5, 8.0, 8.5, 9.0, 8.5, 9.0],
            'Italiano': [7.0, 7.5, 8.0, 8.5, 8.0, 8.5],
            'Inglese': [8.5, 9.0, 9.5, 9.0, 9.5, 9.5]
        }
    }
    
    dashboard_stats = {
        'messages_today': 8,
        'ai_questions_today': 5,
        'current_streak': 7,
        'total_xp': 2450,
        'current_level': 12,
        'media_voti': 8.2,
        'totale_voti': 19,
        'presenze_percentuale': 94,
        'assenze': 3,
        'assenze_giustificate': 2,
        'ritardi': 4,
        'giorni_totali': 50
    }
    
    # Aziende mock
    companies = [
        {
            'id': 1,
            'nome': 'TechItaly SRL',
            'settore': 'Tecnologia',
            'descrizione': 'Startup innovativa nel campo dell\'AI',
            'logo': None,
            'citta': 'Milano',
            'posizione_offerta': 'Stage Sviluppatore Junior',
            'tipo_opportunita': 'Stage',
            'requisiti': 'Conoscenza Python, motivazione',
            'retribuzione': '€800/mese'
        },
        {
            'id': 2,
            'nome': 'Digital Solutions',
            'settore': 'Marketing',
            'descrizione': 'Agenzia di marketing digitale',
            'logo': None,
            'citta': 'Roma',
            'posizione_offerta': 'Social Media Manager',
            'tipo_opportunita': 'Apprendistato',
            'requisiti': 'Creatività, conoscenza social media',
            'retribuzione': '€1200/mese'
        }
    ]
    
    ai_insights = []
    
    return render_template('dashboard_studente.html', 
                         user=demo_user, 
                         gamification=gamification_data,
                         stats=dashboard_stats,
                         companies=companies,
                         ai_insights=ai_insights,
                         enabled_features=enabled_features,
                         voti=voti,
                         medie_materie=medie_materie,
                         ultime_presenze=ultime_presenze,
                         presenze_stats=presenze_stats,
                         upcoming_events=upcoming_events,
                         chart_data=chart_data)

@demo_bp.route('/dashboard/professore')
def demo_dashboard_professore():
    """Demo dashboard professore - SOLO DATI MOCK"""
    demo_user = get_demo_session_professore()
    
    stats = {
        'total_studenti': 24,
        'classi_attive': 2,
        'students_count': 24,
        'recent_activity': [
            {
                'nome': 'Luca Rossi',
                'azione': 'Ha completato il quiz di Matematica',
                'timestamp': '2 ore fa'
            },
            {
                'nome': 'Sara Bianchi',
                'azione': 'Ha caricato un compito',
                'timestamp': '3 ore fa'
            },
            {
                'nome': 'Marco Verdi',
                'azione': 'Ha risposto in chat',
                'timestamp': '5 ore fa'
            }
        ]
    }
    
    return render_template('dashboard_professore.html', 
                         user=demo_user, 
                         stats=stats,
                         total_studenti=24,
                         classi_attive=2)

@demo_bp.route('/calendario')
def demo_calendario():
    """Demo calendario - SOLO DATI MOCK"""
    demo_user = get_demo_session_studente()
    
    # Eventi mock
    events = [
        {
            'id': 1,
            'titolo': 'Verifica di Matematica',
            'descrizione': 'Equazioni di secondo grado',
            'data': '2025-11-05',
            'tipo': 'verifica',
            'classe': '3A'
        },
        {
            'id': 2,
            'titolo': 'Consegna Progetto Storia',
            'descrizione': 'Ricerca sulla Seconda Guerra Mondiale',
            'data': '2025-11-12',
            'tipo': 'compito',
            'classe': '3A'
        },
        {
            'id': 3,
            'titolo': 'Uscita Didattica',
            'descrizione': 'Visita al Museo della Scienza',
            'data': '2025-11-20',
            'tipo': 'evento',
            'classe': '3A'
        }
    ]
    
    return render_template('calendario.html',
                         user=demo_user,
                         events=events)

@demo_bp.route('/chat')
def demo_chat():
    """Demo chat - SOLO DATI MOCK"""
    demo_user = get_demo_session_studente()
    
    # Chat rooms mock
    chats = [
        {
            'id': 1,
            'nome': 'Classe 3A - Generale',
            'tipo': 'classe',
            'classe': '3A',
            'ultimo_messaggio': 'Ragazzi chi ha i compiti di mate?',
            'timestamp': '10 min fa'
        },
        {
            'id': 2,
            'nome': 'Matematica - Discussione',
            'tipo': 'materia',
            'classe': '3A',
            'ultimo_messaggio': 'Le equazioni di secondo grado...',
            'timestamp': '1 ora fa'
        }
    ]
    
    utenti_online = [
        {'id': 101, 'nome': 'Luca', 'cognome': 'Rossi'},
        {'id': 102, 'nome': 'Sara', 'cognome': 'Bianchi'},
        {'id': 103, 'nome': 'Marco', 'cognome': 'Verdi'}
    ]
    
    return render_template('chat_hub.html',
                         user=demo_user,
                         chat_classe=[c for c in chats if c['tipo'] == 'classe'],
                         gruppi_materia=[c for c in chats if c['tipo'] == 'materia'],
                         conversazioni_private=[],
                         available_users=utenti_online)

@demo_bp.route('/ai-chat')
def demo_ai_chat():
    """Demo AI chat - SOLO DATI MOCK"""
    demo_user = get_demo_session_studente()
    
    return render_template('ai_chat.html', user=demo_user)

def get_demo_session_dirigente():
    """Sessione demo per dirigente"""
    return {
        'user_id': -997,
        'nome': 'Dott.',
        'cognome': 'Dirigente Demo',
        'email': 'dirigente.demo@skaila.it',
        'ruolo': 'dirigente',
        'scuola_id': -1,
        'demo_mode': True
    }

@demo_bp.route('/dashboard/dirigente')
def demo_dashboard_dirigente():
    """Demo dashboard dirigente - SOLO DATI MOCK"""
    from datetime import datetime
    
    demo_user = get_demo_session_dirigente()
    
    school_overview = {
        'total_students': 450,
        'total_teachers': 32,
        'total_classes': 18,
        'avg_student_age': 15.5,
        'active_users_today': 287
    }
    
    classes_analytics = [
        {'nome': '1A', 'student_count': 25, 'avg_grade': 7.8, 'attendance_rate': 94},
        {'nome': '1B', 'student_count': 24, 'avg_grade': 7.5, 'attendance_rate': 92},
        {'nome': '2A', 'student_count': 26, 'avg_grade': 7.9, 'attendance_rate': 95},
        {'nome': '2B', 'student_count': 23, 'avg_grade': 7.2, 'attendance_rate': 89},
        {'nome': '3A', 'student_count': 25, 'avg_grade': 8.1, 'attendance_rate': 96},
        {'nome': '3B', 'student_count': 24, 'avg_grade': 7.6, 'attendance_rate': 91}
    ]
    
    teachers_with_ratings = [
        {'nome': 'Prof. Rossi', 'cognome': 'Marco', 'materia': 'Matematica', 'rating': 4.8, 'rating_count': 45},
        {'nome': 'Prof.ssa Bianchi', 'cognome': 'Laura', 'materia': 'Italiano', 'rating': 4.5, 'rating_count': 42},
        {'nome': 'Prof. Verdi', 'cognome': 'Giuseppe', 'materia': 'Storia', 'rating': 4.2, 'rating_count': 38},
        {'nome': 'Prof.ssa Neri', 'cognome': 'Anna', 'materia': 'Inglese', 'rating': 4.7, 'rating_count': 50},
        {'nome': 'Prof. Gialli', 'cognome': 'Paolo', 'materia': 'Fisica', 'rating': 4.0, 'rating_count': 35}
    ]
    
    economic_kpis = {
        'monthly_revenue': 599,
        'cost_per_student': 1.33,
        'revenue_trend': [500, 520, 545, 560, 580, 599],
        'months': ['Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    }
    
    engagement_stats = {
        'weekly_engagement_rate': 78.5,
        'ai_coach_usage': 156,
        'gamification_active_users': 312,
        'parent_engagement': 65.2
    }
    
    grade_distribution = {
        'labels': ['Insufficiente (<6)', 'Sufficiente (6)', 'Buono (7)', 'Distinto (8)', 'Ottimo (9-10)'],
        'data': [45, 120, 180, 150, 105]
    }
    
    return render_template('dashboard_dirigente_new.html',
                         user=demo_user,
                         overview=school_overview,
                         classes=classes_analytics,
                         teachers=teachers_with_ratings,
                         kpis=economic_kpis,
                         engagement=engagement_stats,
                         grades=grade_distribution)

@demo_bp.route('/gamification')
def demo_gamification():
    """Demo gamification dashboard - SOLO DATI MOCK"""
    from datetime import datetime, timedelta
    
    demo_user = get_demo_session_studente()
    
    profile = {
        'rank': 'Esploratore',
        'rank_icon': 'fa-compass',
        'rank_color': '#00d4ff',
        'xp_totale': 2450,
        'xp_for_next_rank': 3000,
        'current_streak': 7,
        'longest_streak': 14,
        'level': 12
    }
    
    challenges = [
        {
            'id': 1,
            'titolo': 'Quiz Master',
            'descrizione': 'Completa 5 quiz oggi',
            'tipo': 'daily',
            'progresso': 3,
            'obiettivo': 5,
            'xp_reward': 50,
            'scadenza': datetime.now() + timedelta(hours=8)
        },
        {
            'id': 2,
            'titolo': 'Studioso Costante',
            'descrizione': 'Mantieni una streak di 7 giorni',
            'tipo': 'weekly',
            'progresso': 7,
            'obiettivo': 7,
            'xp_reward': 200,
            'completata': True,
            'scadenza': datetime.now() + timedelta(days=3)
        },
        {
            'id': 3,
            'titolo': 'AI Explorer',
            'descrizione': 'Fai 10 domande all\'AI Coach',
            'tipo': 'daily',
            'progresso': 6,
            'obiettivo': 10,
            'xp_reward': 75,
            'scadenza': datetime.now() + timedelta(hours=12)
        }
    ]
    
    badges = [
        {'id': 1, 'nome': 'Primo Login', 'icona': 'fa-door-open', 'rarità': 'comune', 'sbloccato': True, 'data': datetime.now() - timedelta(days=30)},
        {'id': 2, 'nome': 'Quiz Perfetto', 'icona': 'fa-star', 'rarità': 'raro', 'sbloccato': True, 'data': datetime.now() - timedelta(days=15)},
        {'id': 3, 'nome': 'Streak Master', 'icona': 'fa-fire', 'rarità': 'epico', 'sbloccato': True, 'data': datetime.now() - timedelta(days=5)},
        {'id': 4, 'nome': 'AI Whisperer', 'icona': 'fa-robot', 'rarità': 'raro', 'sbloccato': True, 'data': datetime.now() - timedelta(days=10)},
        {'id': 5, 'nome': 'Social Butterfly', 'icona': 'fa-comments', 'rarità': 'comune', 'sbloccato': False},
        {'id': 6, 'nome': 'Leggenda', 'icona': 'fa-crown', 'rarità': 'leggendario', 'sbloccato': False}
    ]
    
    leaderboard = [
        {'posizione': 1, 'nome': 'Marco R.', 'xp': 3200, 'rank': 'Maestro'},
        {'posizione': 2, 'nome': 'Sara B.', 'xp': 2950, 'rank': 'Esploratore'},
        {'posizione': 3, 'nome': 'Luca V.', 'xp': 2800, 'rank': 'Esploratore'},
        {'posizione': 4, 'nome': 'Tu', 'xp': 2450, 'rank': 'Esploratore', 'is_current_user': True},
        {'posizione': 5, 'nome': 'Anna M.', 'xp': 2300, 'rank': 'Apprendista'}
    ]
    
    power_ups = [
        {'id': 1, 'nome': 'XP Booster 2x', 'icona': 'fa-rocket', 'descrizione': 'Raddoppia XP per 1 ora', 'costo': 100, 'disponibile': True},
        {'id': 2, 'nome': 'Streak Shield', 'icona': 'fa-shield-alt', 'descrizione': 'Proteggi la tua streak', 'costo': 150, 'disponibile': True},
        {'id': 3, 'nome': 'Seconda Chance', 'icona': 'fa-redo', 'descrizione': 'Ripeti un quiz', 'costo': 75, 'disponibile': True}
    ]
    
    activity_timeline = [
        {'tipo': 'xp', 'descrizione': '+50 XP - Quiz completato', 'timestamp': datetime.now() - timedelta(hours=2)},
        {'tipo': 'badge', 'descrizione': 'Badge sbloccato: Streak Master', 'timestamp': datetime.now() - timedelta(days=1)},
        {'tipo': 'challenge', 'descrizione': 'Sfida completata: Studioso Costante', 'timestamp': datetime.now() - timedelta(days=1)},
        {'tipo': 'xp', 'descrizione': '+25 XP - AI Chat interazione', 'timestamp': datetime.now() - timedelta(days=2)}
    ]
    
    ranks_progression = [
        {'nome': 'Germoglio', 'xp_min': 0, 'icona': 'fa-seedling', 'colore': '#90EE90'},
        {'nome': 'Apprendista', 'xp_min': 200, 'icona': 'fa-book-open', 'colore': '#87CEEB'},
        {'nome': 'Esploratore', 'xp_min': 500, 'icona': 'fa-compass', 'colore': '#00d4ff', 'current': True},
        {'nome': 'Avventuriero', 'xp_min': 1000, 'icona': 'fa-hiking', 'colore': '#FFD700'},
        {'nome': 'Maestro', 'xp_min': 2000, 'icona': 'fa-graduation-cap', 'colore': '#FF6347'},
        {'nome': 'Campione', 'xp_min': 4000, 'icona': 'fa-trophy', 'colore': '#9370DB'},
        {'nome': 'Leggenda', 'xp_min': 7000, 'icona': 'fa-crown', 'colore': '#FF4500'},
        {'nome': 'Mito', 'xp_min': 10000, 'icona': 'fa-dragon', 'colore': '#8B0000'},
        {'nome': 'Immortale', 'xp_min': 13000, 'icona': 'fa-gem', 'colore': '#E6E6FA'}
    ]
    
    return render_template('gamification_dashboard.html',
                         user=demo_user,
                         profile=profile,
                         challenges=challenges,
                         badges=badges,
                         leaderboard=leaderboard,
                         power_ups=power_ups,
                         activity_timeline=activity_timeline,
                         ranks_progression=ranks_progression)
