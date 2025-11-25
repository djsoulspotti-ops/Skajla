"""
Opportunities API Routes
Handles One-Click Apply and opportunity management
"""

from flask import Blueprint, jsonify, request, session
from shared.middleware.auth import require_login
from services.database.database_manager import DatabaseManager
from services.portfolio.student_portfolio_manager import StudentPortfolioManager
from shared.error_handling import get_logger
import json
from datetime import datetime

logger = get_logger(__name__)
opportunities_api_bp = Blueprint('opportunities_api', __name__)
db_manager = DatabaseManager()
portfolio_manager = StudentPortfolioManager()


@opportunities_api_bp.route('/api/opportunities/apply', methods=['POST'])
@require_login
def one_click_apply():
    """
    POST /api/opportunities/apply
    One-Click Apply: Sends student's Candidate Card to company
    
    Body:
        {
            "opportunity_id": 123,
            "cover_letter": "Optional personal message"
        }
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'Solo gli studenti possono candidarsi'
        }), 403
    
    try:
        data = request.get_json()
        opportunity_id = data.get('opportunity_id')
        cover_letter = data.get('cover_letter', '')
        
        if not opportunity_id:
            return jsonify({
                'success': False,
                'error': 'Bad Request',
                'message': 'ID opportunità richiesto'
            }), 400
        
        # Check if opportunity exists and is active
        opportunity = db_manager.query('''
            SELECT 
                co.*,
                c.nome as company_name,
                c.id as company_id
            FROM company_opportunities co
            JOIN skaila_connect_companies c ON co.company_id = c.id
            WHERE co.id = %s AND co.is_active = TRUE
        ''', (opportunity_id,), one=True)
        
        if not opportunity:
            return jsonify({
                'success': False,
                'error': 'Not Found',
                'message': 'Opportunità non trovata o non più disponibile'
            }), 404
        
        # Check if already applied
        existing = db_manager.query('''
            SELECT id FROM student_applications
            WHERE user_id = %s AND opportunity_id = %s
        ''', (user_id, opportunity_id), one=True)
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Already Applied',
                'message': 'Hai già inviato una candidatura per questa opportunità'
            }), 400
        
        # Generate Candidate Card
        candidate_card = portfolio_manager.generate_candidate_card(
            user_id=user_id,
            include_private=True
        )
        
        if not candidate_card:
            return jsonify({
                'success': False,
                'error': 'Portfolio Error',
                'message': 'Impossibile generare il tuo profilo candidato'
            }), 500
        
        # Atomic capacity check + application creation in single transaction
        # Context manager auto-commits on success, rolls back on exception
        candidate_card_json = json.dumps(candidate_card)
        
        class NoSpotsAvailable(Exception):
            pass
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Step 1: Atomically check and reserve capacity
                cursor.execute('''
                    UPDATE company_opportunities
                    SET spots_filled = spots_filled + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s 
                        AND spots_filled < spots_available
                        AND is_active = TRUE
                    RETURNING id
                ''', (opportunity_id,))
                
                updated = cursor.fetchone()
                
                if not updated:
                    # Raise exception to trigger rollback (context manager only rolls back on exceptions)
                    raise NoSpotsAvailable('No spots available')
                
                # Step 2: Create application (in same transaction)
                cursor.execute('''
                    INSERT INTO student_applications
                    (user_id, opportunity_id, company_id, application_status, 
                     candidate_card_data, cover_letter, applied_at)
                    VALUES (%s, %s, %s, 'pending', %s::jsonb, %s, CURRENT_TIMESTAMP)
                ''', (
                    user_id,
                    opportunity_id,
                    opportunity['company_id'],
                    candidate_card_json,
                    cover_letter
                ))
                
                # COMMIT transaction (implicit at context exit - successful)
                
        except NoSpotsAvailable:
            # Capacity check failed - transaction already rolled back by context manager
            return jsonify({
                'success': False,
                'error': 'No Spots',
                'message': 'Non ci sono più posti disponibili'
            }), 400
        except Exception as e:
            # INSERT failed or other error - transaction already rolled back
            logger.error(
                event_type='application_transaction_failed',
                domain='opportunities',
                user_id=user_id,
                opportunity_id=opportunity_id,
                error=str(e),
                exc_info=True
            )
            return jsonify({
                'success': False,
                'error': 'Transaction Failed',
                'message': 'Errore durante l\'invio della candidatura. Riprova.'
            }), 500
        
        logger.info(
            event_type='application_submitted',
            domain='opportunities',
            user_id=user_id,
            opportunity_id=opportunity_id,
            company_id=opportunity['company_id'],
            company_name=opportunity['company_name']
        )
        
        return jsonify({
            'success': True,
            'message': f'Candidatura inviata con successo a {opportunity["company_name"]}!',
            'application_data': {
                'company': opportunity['company_name'],
                'position': opportunity['position_title'],
                'applied_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='application_error',
            domain='opportunities',
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore durante l\'invio della candidatura'
        }), 500


@opportunities_api_bp.route('/api/opportunities', methods=['GET'])
@require_login
def get_opportunities():
    """
    GET /api/opportunities
    Get all active opportunities with filtering
    
    Query Params:
        - location_type: remote, on-site, hybrid
        - sector: tech, marketing, etc.
        - pcto_certified: true/false
        - min_hours: minimum PCTO hours
    """
    try:
        location_type = request.args.get('location_type')
        sector = request.args.get('sector')
        pcto_certified = request.args.get('pcto_certified')
        min_hours = request.args.get('min_hours', type=int)
        
        # Build dynamic query
        query = '''
            SELECT 
                co.*,
                c.nome as company_name,
                c.citta as city,
                c.settore as sector,
                c.location_type,
                c.pcto_certified,
                c.remote_allowed
            FROM company_opportunities co
            JOIN skaila_connect_companies c ON co.company_id = c.id
            WHERE co.is_active = TRUE
        '''
        params = []
        
        if location_type:
            query += ' AND c.location_type = %s'
            params.append(location_type)
        
        if sector:
            query += ' AND LOWER(c.settore) LIKE %s'
            params.append(f'%{sector.lower()}%')
        
        if pcto_certified:
            query += ' AND c.pcto_certified = TRUE'
        
        if min_hours:
            query += ' AND co.hours_required >= %s'
            params.append(min_hours)
        
        query += ' ORDER BY co.created_at DESC LIMIT 50'
        
        opportunities = db_manager.query(query, tuple(params) if params else None) or []
        
        return jsonify({
            'success': True,
            'count': len(opportunities),
            'opportunities': opportunities
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='opportunities_fetch_error',
            domain='opportunities',
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore durante il caricamento delle opportunità'
        }), 500


@opportunities_api_bp.route('/api/student/applications', methods=['GET'])
@require_login
def get_student_applications():
    """
    GET /api/student/applications
    Get all applications for current student
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({
            'success': False,
            'error': 'Forbidden'
        }), 403
    
    try:
        applications = db_manager.query('''
            SELECT 
                sa.*,
                co.position_title,
                c.nome as company_name
            FROM student_applications sa
            JOIN company_opportunities co ON sa.opportunity_id = co.id
            JOIN skaila_connect_companies c ON sa.company_id = c.id
            WHERE sa.user_id = %s
            ORDER BY sa.applied_at DESC
        ''', (user_id,)) or []
        
        return jsonify({
            'success': True,
            'applications': [
                {
                    'id': app['id'],
                    'company': app['company_name'],
                    'position': app['position_title'],
                    'status': app['application_status'],
                    'applied_at': app['applied_at'].isoformat() if app.get('applied_at') else None
                }
                for app in applications
            ]
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='applications_fetch_error',
            domain='opportunities',
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        
        return jsonify({
            'success': False,
            'error': 'Server Error'
        }), 500


__all__ = ['opportunities_api_bp']
