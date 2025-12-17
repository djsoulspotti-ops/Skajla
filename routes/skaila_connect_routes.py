"""
SKAJLA Connect Routes
Sistema per connettere scuole con aziende per alternanza scuola-lavoro
"""

from flask import Blueprint, render_template, session, redirect, flash, jsonify, request
from shared.middleware.auth import require_login
from shared.middleware.feature_guard import check_feature_enabled, Features
from shared.error_handling import get_logger
from services.database.database_manager import DatabaseManager
from services.tenant_guard import get_current_school_id

logger = get_logger(__name__)
skaila_connect_bp = Blueprint('skaila_connect', __name__)
db_manager = DatabaseManager()

@skaila_connect_bp.before_request
def check_skaila_connect_feature():
    """Verifica che SKAJLA Connect sia abilitato prima di ogni request"""
    if 'user_id' not in session:
        return  # Auth middleware gestirà questo
    
    try:
        school_id = get_current_school_id()
        if not check_feature_enabled(school_id, Features.SKAJLA_CONNECT):
            # API endpoint - ritorna JSON 403
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Feature non disponibile',
                    'message': 'SKAJLA Connect non è disponibile per la tua scuola.',
                    'feature': Features.SKAJLA_CONNECT,
                    'upgrade_required': True
                }), 403
            # Web endpoint - redirect con flash
            flash('⚠️ SKAJLA Connect non è disponibile per la tua scuola.', 'warning')
            return redirect('/dashboard')
    except Exception as e:
        logger.error(
            event_type='feature_check_error',
            domain='skaila_connect',
            user_id=session.get('user_id'),
            school_id=session.get('scuola_id'),
            feature=Features.SKAJLA_CONNECT,
            error=str(e),
            error_type=type(e).__name__,
            message='Error checking SKAJLA Connect feature availability',
            exc_info=True
        )
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Errore di sistema',
                'message': 'Impossibile verificare disponibilità feature. Riprova più tardi.'
            }), 500
        flash('⚠️ Errore nel verificare le funzionalità disponibili.', 'error')
        return redirect('/dashboard')

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
    Hub SKAJLA Connect - Opportunity Marketplace
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    # Get active opportunities from new schema with robust error handling
    opportunities = []
    try:
        opportunities = db_manager.query('''
            SELECT 
                co.id,
                co.position_title,
                co.position_description as description,
                co.opportunity_type,
                co.hours_required,
                co.compensation,
                co.spots_available,
                co.spots_filled,
                c.nome as company_name,
                c.citta as city,
                c.settore as sector,
                c.location_type,
                c.pcto_certified,
                c.remote_allowed
            FROM company_opportunities co
            JOIN skaila_connect_companies c ON co.company_id = c.id
            WHERE co.is_active = TRUE
            ORDER BY co.created_at DESC
            LIMIT 100
        ''') or []
    except Exception as e:
        logger.warning(
            event_type='opportunities_query_fallback',
            domain='skaila_connect',
            user_id=user_id,
            error=str(e),
            message='Opportunity tables not found or query failed',
            fallback='empty_list'
        )
        opportunities = [] # No more mock data fallback for listing to avoid confusion
    
    # Get profile completeness and SKILLS for matching
    profile_completeness = 50
    student_skills_names = []
    
    if ruolo == 'studente':
        try:
            from services.portfolio.student_portfolio_manager import StudentPortfolioManager
            portfolio_manager = StudentPortfolioManager()
            # Get full card (cached-like) mainly for completeness and skills
            # Note: In a real high-scale app, we would fetch only skills specific query.
            candidate_card = portfolio_manager.generate_candidate_card(user_id, include_private=False)
            profile_completeness = candidate_card.get('profile_completeness', 50)
            
            # Extract skill names for matching
            raw_skills = candidate_card.get('skills', [])
            student_skills_names = [s['name'].lower() for s in raw_skills if 'name' in s]
            
        except Exception as e:
            logger.warning(
                event_type='profile_data_fetch_error',
                domain='skaila_connect',
                user_id=user_id,
                error=str(e)
            )
            profile_completeness = 50

    # 🧠 SMART MATCHING ALGORITHM
    # Sort opportunities based on relevance to student skills
    if student_skills_names and opportunities:
        for opp in opportunities:
            score = 0
            # Text to search in
            search_text = (
                str(opp.get('position_title', '')) + " " + 
                str(opp.get('description', '')) + " " + 
                str(opp.get('sector', ''))
            ).lower()
            
            # 1. Skill Match (+10 per skill)
            for skill in student_skills_names:
                if skill in search_text:
                    score += 10
            
            # 2. Location Preference (Placeholder - assumes user city matching could be added)
            # if user_city in opp_city: score += 20
            
            # 3. Remote Bonus (+5)
            if opp.get('remote_allowed'):
                score += 5
                
            opp['matching_score'] = score
            
        # Sort by score DESC
        opportunities.sort(key=lambda x: x.get('matching_score', 0), reverse=True)

    return render_template('skaila_connect_marketplace.html',
                         user=session,
                         opportunities=opportunities,
                         profile_completeness=profile_completeness)


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
        logger.warning(
            event_type='company_detail_query_fallback',
            domain='skaila_connect',
            user_id=session.get('user_id'),
            school_id=session.get('school_id'),
            company_id=company_id,
            error=str(e),
            error_type=type(e).__name__,
            message='Company detail query failed, using mock data',
            fallback='MOCK_COMPANIES'
        )
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
