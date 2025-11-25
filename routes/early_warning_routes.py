"""
SKAILA Early Warning System Routes
Dashboard and management for early warning alerts
Part of Feature #1: Smart AI-Tutoring & Early-Warning Engine
"""

from flask import Blueprint, request, jsonify, session, render_template
from services.telemetry.telemetry_engine import telemetry_engine
from services.database.database_manager import db_manager
from shared.middleware.auth import require_login, require_role
from shared.error_handling import get_logger

logger = get_logger(__name__)

early_warning_bp = Blueprint('early_warning', __name__, url_prefix='/early-warning')


@early_warning_bp.route('/dashboard')
@require_login
@require_role('docente')
def early_warning_dashboard():
    """Dashboard for teachers to view early warning alerts"""
    try:
        teacher_id = session.get('user_id')
        
        alerts = telemetry_engine.get_active_alerts_for_teacher(teacher_id)
        
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        high_alerts = [a for a in alerts if a['severity'] == 'high']
        medium_alerts = [a for a in alerts if a['severity'] == 'medium']
        
        return render_template('early_warning_dashboard.html',
            critical_alerts=critical_alerts,
            high_alerts=high_alerts,
            medium_alerts=medium_alerts,
            total_alerts=len(alerts)
        )
        
    except Exception as e:
        logger.error(
            event_type='early_warning_dashboard_failed',
            domain='early_warning',
            error=str(e),
            exc_info=True
        )
        return render_template('error.html', 
            error_message="Errore nel caricamento dashboard early warning"), 500


@early_warning_bp.route('/api/alerts', methods=['GET'])
@require_login
@require_role('docente')
def get_alerts_api():
    """Get active alerts as JSON (for API/AJAX calls)"""
    try:
        teacher_id = session.get('user_id')
        alerts = telemetry_engine.get_active_alerts_for_teacher(teacher_id)
        
        return jsonify({
            "success": True,
            "alerts": alerts,
            "count": len(alerts)
        })
        
    except Exception as e:
        logger.error(
            event_type='get_alerts_api_failed',
            domain='early_warning',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            "success": False,
            "error": "Failed to fetch alerts"
        }), 500


@early_warning_bp.route('/api/alert/<int:alert_id>/acknowledge', methods=['POST'])
@require_login
@require_role('docente')
def acknowledge_alert(alert_id):
    """Teacher acknowledges an alert"""
    try:
        teacher_id = session.get('user_id')
        data = request.json
        notes = data.get('notes', '')
        
        db_manager.execute('''
            UPDATE early_warning_alerts
            SET status = %s,
                acknowledged_by = %s,
                acknowledged_at = CURRENT_TIMESTAMP,
                teacher_notes = %s
            WHERE id = %s
        ''', ('acknowledged', teacher_id, notes, alert_id))
        
        logger.info(
            event_type='alert_acknowledged',
            domain='early_warning',
            alert_id=alert_id,
            teacher_id=teacher_id
        )
        
        return jsonify({
            "success": True,
            "message": "Alert riconosciuto con successo"
        })
        
    except Exception as e:
        logger.error(
            event_type='acknowledge_alert_failed',
            domain='early_warning',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            "success": False,
            "error": "Failed to acknowledge alert"
        }), 500


@early_warning_bp.route('/api/alert/<int:alert_id>/resolve', methods=['POST'])
@require_login
@require_role('docente')
def resolve_alert(alert_id):
    """Mark alert as resolved"""
    try:
        data = request.json
        resolution_method = data.get('resolution_method', 'manual_resolution')
        
        db_manager.execute('''
            UPDATE early_warning_alerts
            SET status = %s,
                resolved_at = CURRENT_TIMESTAMP,
                resolution_method = %s
            WHERE id = %s
        ''', ('resolved', resolution_method, alert_id))
        
        logger.info(
            event_type='alert_resolved',
            domain='early_warning',
            alert_id=alert_id
        )
        
        return jsonify({
            "success": True,
            "message": "Alert risolto con successo"
        })
        
    except Exception as e:
        logger.error(
            event_type='resolve_alert_failed',
            domain='early_warning',
            error=str(e),
            exc_info=True
        )
        return jsonify({
            "success": False,
            "error": "Failed to resolve alert"
        }), 500
