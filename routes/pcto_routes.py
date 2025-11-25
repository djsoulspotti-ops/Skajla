"""
PCTO Workflow & Timesheet Routes
Digital logbook with check-in/check-out and tutor validation
"""

from flask import Blueprint, jsonify, request, session, render_template
from shared.middleware.auth import require_login
from services.database.database_manager import DatabaseManager
from shared.error_handling import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)
pcto_bp = Blueprint('pcto', __name__)
db_manager = DatabaseManager()


@pcto_bp.route('/pcto/tracker')
@require_login
def pcto_tracker():
    """PCTO Tracker Page - Progress visualization and digital logbook"""
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return "Access Denied", 403
    
    # Get active placement
    placement = db_manager.query('''
        SELECT 
            pp.*,
            c.nome as company_name,
            c.citta as city
        FROM pcto_placements pp
        JOIN skaila_connect_companies c ON pp.company_id = c.id
        WHERE pp.user_id = %s AND pp.placement_status = 'active'
        ORDER BY pp.created_at DESC
        LIMIT 1
    ''', (user_id,), one=True)
    
    # Get timesheets
    timesheets = []
    if placement:
        timesheets = db_manager.query('''
            SELECT * FROM pcto_timesheets
            WHERE placement_id = %s
            ORDER BY check_in_time DESC
        ''', (placement['id'],)) or []
    
    return render_template('pcto_tracker.html',
                         user=session,
                         placement=placement,
                         timesheets=timesheets)


@pcto_bp.route('/api/pcto/check-in', methods=['POST'])
@require_login
def check_in():
    """
    POST /api/pcto/check-in
    Student checks in to start work session
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    try:
        data = request.get_json() or {}
        
        # Get active placement
        placement = db_manager.query('''
            SELECT id FROM pcto_placements
            WHERE user_id = %s AND placement_status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,), one=True)
        
        if not placement:
            return jsonify({
                'success': False,
                'error': 'No Active Placement',
                'message': 'Non hai un tirocinio PCTO attivo'
            }), 400
        
        # Check if already checked in
        active_session = db_manager.query('''
            SELECT id FROM pcto_timesheets
            WHERE placement_id = %s AND check_out_time IS NULL
            ORDER BY check_in_time DESC
            LIMIT 1
        ''', (placement['id'],), one=True)
        
        if active_session:
            return jsonify({
                'success': False,
                'error': 'Already Checked In',
                'message': 'Hai già fatto check-in. Fai check-out prima di iniziare una nuova sessione.'
            }), 400
        
        # Create check-in record
        db_manager.execute('''
            INSERT INTO pcto_timesheets
            (placement_id, user_id, check_in_time, activity_description, location)
            VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)
        ''', (
            placement['id'],
            user_id,
            data.get('activity_description', 'Work session'),
            data.get('location', 'On-site')
        ))
        
        logger.info(
            event_type='pcto_check_in',
            domain='pcto',
            user_id=user_id,
            placement_id=placement['id']
        )
        
        return jsonify({
            'success': True,
            'message': 'Check-in effettuato con successo!',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='check_in_error',
            domain='pcto',
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore durante il check-in'
        }), 500


@pcto_bp.route('/api/pcto/check-out', methods=['POST'])
@require_login
def check_out():
    """
    POST /api/pcto/check-out
    Student checks out to end work session
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    try:
        # Get active placement
        placement = db_manager.query('''
            SELECT id, hours_completed, hours_required 
            FROM pcto_placements
            WHERE user_id = %s AND placement_status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,), one=True)
        
        if not placement:
            return jsonify({
                'success': False,
                'error': 'No Active Placement'
            }), 400
        
        # Get active timesheet session
        timesheet = db_manager.query('''
            SELECT * FROM pcto_timesheets
            WHERE placement_id = %s AND check_out_time IS NULL
            ORDER BY check_in_time DESC
            LIMIT 1
        ''', (placement['id'],), one=True)
        
        if not timesheet:
            return jsonify({
                'success': False,
                'error': 'No Active Session',
                'message': 'Non hai una sessione attiva. Fai check-in prima.'
            }), 400
        
        # Calculate hours
        check_in = timesheet['check_in_time']
        check_out = datetime.utcnow()
        hours_diff = (check_out - check_in).total_seconds() / 3600
        hours_logged = round(hours_diff, 2)
        
        # Update timesheet
        db_manager.execute('''
            UPDATE pcto_timesheets
            SET check_out_time = CURRENT_TIMESTAMP,
                hours_logged = %s
            WHERE id = %s
        ''', (hours_logged, timesheet['id']))
        
        # Update placement total hours
        new_total = float(placement.get('hours_completed', 0)) + hours_logged
        db_manager.execute('''
            UPDATE pcto_placements
            SET hours_completed = %s
            WHERE id = %s
        ''', (new_total, placement['id']))
        
        # Check if completed
        if new_total >= placement['hours_required']:
            db_manager.execute('''
                UPDATE pcto_placements
                SET placement_status = 'completed',
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (placement['id'],))
        
        logger.info(
            event_type='pcto_check_out',
            domain='pcto',
            user_id=user_id,
            placement_id=placement['id'],
            hours_logged=hours_logged,
            total_hours=new_total
        )
        
        return jsonify({
            'success': True,
            'message': f'Check-out completato! Ore registrate: {hours_logged:.2f}h',
            'hours_logged': hours_logged,
            'total_hours': new_total,
            'hours_required': placement['hours_required'],
            'is_completed': new_total >= placement['hours_required']
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='check_out_error',
            domain='pcto',
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        
        return jsonify({
            'success': False,
            'error': 'Server Error',
            'message': 'Errore durante il check-out'
        }), 500


@pcto_bp.route('/api/pcto/progress', methods=['GET'])
@require_login
def get_progress():
    """
    GET /api/pcto/progress
    Get PCTO progress for current student
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    try:
        placement = db_manager.query('''
            SELECT 
                pp.*,
                c.nome as company_name
            FROM pcto_placements pp
            JOIN skaila_connect_companies c ON pp.company_id = c.id
            WHERE pp.user_id = %s AND pp.placement_status = 'active'
            ORDER BY pp.created_at DESC
            LIMIT 1
        ''', (user_id,), one=True)
        
        if not placement:
            return jsonify({
                'success': True,
                'has_placement': False,
                'message': 'Nessun tirocinio PCTO attivo'
            }), 200
        
        hours_completed = float(placement.get('hours_completed', 0))
        hours_required = float(placement.get('hours_required', 80))
        progress_percentage = min(100, (hours_completed / hours_required) * 100) if hours_required > 0 else 0
        
        return jsonify({
            'success': True,
            'has_placement': True,
            'placement': {
                'id': placement['id'],
                'company_name': placement['company_name'],
                'hours_completed': hours_completed,
                'hours_required': hours_required,
                'progress_percentage': round(progress_percentage, 1),
                'status': placement['placement_status']
            }
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='progress_fetch_error',
            domain='pcto',
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        
        return jsonify({
            'success': False,
            'error': 'Server Error'
        }), 500


__all__ = ['pcto_bp']
