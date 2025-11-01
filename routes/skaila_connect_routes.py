"""
SKAILA Connect Routes
Sistema per connettere scuole con aziende per alternanza scuola-lavoro
"""

from flask import Blueprint, render_template, session, redirect, flash, jsonify, request
from shared.middleware.auth import require_login
from shared.middleware.feature_guard import check_feature_enabled, Features
from services.database.database_manager import DatabaseManager
from services.tenant_guard import get_current_school_id

skaila_connect_bp = Blueprint('skaila_connect', __name__)
db_manager = DatabaseManager()

@skaila_connect_bp.before_request
def check_skaila_connect_feature():
    """Verifica che SKAILA Connect sia abilitato prima di ogni request"""
    if 'user_id' not in session:
        return  # Auth middleware gestirà questo
    
    try:
        school_id = get_current_school_id()
        if not check_feature_enabled(school_id, Features.SKAILA_CONNECT):
            # API endpoint - ritorna JSON 403
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Feature non disponibile',
                    'message': 'SKAILA Connect non è disponibile per la tua scuola.',
                    'feature': Features.SKAILA_CONNECT,
                    'upgrade_required': True
                }), 403
            # Web endpoint - redirect con flash
            flash('⚠️ SKAILA Connect non è disponibile per la tua scuola.', 'warning')
            return redirect('/dashboard')
    except Exception:
        pass

# Shared mock data for fallback when companies table doesn't exist
MOCK_COMPANIES = [
    {
        'id': 1,
        'nome': 'TechItaly SRL',
        'settore': 'Tecnologia',
        'descrizione': 'Startup innovativa specializzata in AI e Machine Learning',
        'citta': 'Milano',
        'posizione_offerta': 'Stage Sviluppatore Junior',
        'tipo_opportunita': 'Stage',
        'requisiti': 'Conoscenza Python, passione per tecnologia',
        'retribuzione': '€800/mese',
        'durata': '6 mesi'
    },
    {
        'id': 2,
        'nome': 'Digital Solutions',
        'settore': 'Marketing Digitale',
        'descrizione': 'Agenzia leader nel settore marketing e comunicazione',
        'citta': 'Roma',
        'posizione_offerta': 'Social Media Manager',
        'tipo_opportunita': 'Alternanza Scuola-Lavoro',
        'requisiti': 'Creatività, conoscenza social media',
        'retribuzione': 'Non retribuito - Crediti formativi',
        'durata': '3 mesi'
    },
    {
        'id': 3,
        'nome': 'Green Energy Italia',
        'settore': 'Energia Rinnovabile',
        'descrizione': 'Azienda leader nel settore energie rinnovabili',
        'citta': 'Bologna',
        'posizione_offerta': 'Analista Junior Sostenibilità',
        'tipo_opportunita': 'Stage',
        'requisiti': 'Interesse per ambiente, buone capacità analitiche',
        'retribuzione': '€600/mese',
        'durata': '4 mesi'
    },
    {
        'id': 4,
        'nome': 'FinTech Solutions',
        'settore': 'Finanza',
        'descrizione': 'Startup fintech innovativa',
        'citta': 'Torino',
        'posizione_offerta': 'Data Analyst Trainee',
        'tipo_opportunita': 'Apprendistato',
        'requisiti': 'Excel avanzato, interesse per dati',
        'retribuzione': '€1000/mese',
        'durata': '12 mesi'
    },
    {
        'id': 5,
        'nome': 'Creative Studio',
        'settore': 'Design & Creatività',
        'descrizione': 'Studio di design e comunicazione visiva',
        'citta': 'Firenze',
        'posizione_offerta': 'Graphic Designer Junior',
        'tipo_opportunita': 'Alternanza Scuola-Lavoro',
        'requisiti': 'Conoscenza Photoshop, creatività',
        'retribuzione': 'Non retribuito - Crediti formativi',
        'durata': '3 mesi'
    },
    {
        'id': 6,
        'nome': 'MedTech Innovations',
        'settore': 'Biotecnologia',
        'descrizione': 'Ricerca e sviluppo in campo medicale',
        'citta': 'Milano',
        'posizione_offerta': 'Assistente Ricerca',
        'tipo_opportunita': 'Stage',
        'requisiti': 'Interesse scienze, precisione',
        'retribuzione': '€700/mese',
        'durata': '6 mesi'
    }
]


@skaila_connect_bp.route('/skaila-connect')
@require_login
def connect_hub():
    """
    Hub SKAILA Connect - Connessione scuole-aziende per alternanza scuola-lavoro
    """
    user_id = session.get('user_id')
    school_id = session.get('school_id')
    
    # Query aziende disponibili (mock per ora, poi sarà integrato con sistema reale)
    try:
        companies = db_manager.query('''
            SELECT * FROM companies
            WHERE attiva = TRUE
            ORDER BY created_at DESC
            LIMIT 20
        ''') or []
    except Exception as e:
        # Se la tabella companies non esiste, usa dati mock
        print(f"⚠️ Tabella companies non trovata, uso dati mock: {e}")
        companies = []
    
    # Se nessuna azienda trovata, usa dati mock (lista condivisa)
    if not companies:
        companies = MOCK_COMPANIES
    
    # Statistiche utente (candidature inviate, ecc.)
    user_stats = {
        'candidature_inviate': 0,
        'candidature_accettate': 0,
        'profilo_completo': True
    }
    
    return render_template('skaila_connect.html',
                         user=session,
                         companies=companies,
                         stats=user_stats)


@skaila_connect_bp.route('/skaila-connect/company/<int:company_id>')
@require_login
def company_detail(company_id):
    """Dettaglio azienda specifica"""
    # Query azienda dal database
    company = None
    try:
        company = db_manager.query('''
            SELECT * FROM companies WHERE id = %s
        ''', (company_id,), one=True)
    except Exception as e:
        print(f"⚠️ Errore query companies table (uso mock): {e}")
        company = None
    
    if not company:
        # Fallback a dati mock (usa la stessa lista condivisa del hub)
        company = next((c for c in MOCK_COMPANIES if c['id'] == company_id), None)
    
    if not company:
        return redirect('/skaila-connect')
    
    return render_template('company_detail.html',
                         user=session,
                         company=company)


__all__ = ['skaila_connect_bp']
