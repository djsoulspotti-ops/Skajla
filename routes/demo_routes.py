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
    demo_user = get_demo_session_studente()
    
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
    
    dashboard_stats = {
        'messages_today': 8,
        'ai_questions_today': 5,
        'current_streak': 7,
        'total_xp': 2450,
        'current_level': 12
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
                         ai_insights=ai_insights)

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
