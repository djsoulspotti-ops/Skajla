"""
SKAILA - Demo Routes
Route demo sicure con SOLO dati mock (nessun accesso database reale)
"""

from flask import Blueprint, render_template

demo_bp = Blueprint('demo', __name__, url_prefix='/demo')

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
    
    return render_template('chat.html',
                         user=demo_user,
                         chats=chats,
                         utenti_online=utenti_online)

@demo_bp.route('/ai-chat')
def demo_ai_chat():
    """Demo AI chat - SOLO DATI MOCK"""
    demo_user = get_demo_session_studente()
    
    return render_template('ai_chat.html', user=demo_user)
