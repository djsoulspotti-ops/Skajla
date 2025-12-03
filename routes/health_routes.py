"""
SKAILA Health Check Routes
Lightweight endpoints for Autoscale and load balancer health checks.
These endpoints return immediately without expensive database operations.
"""

from flask import Blueprint, jsonify
import time

health_bp = Blueprint('health', __name__)

_start_time = time.time()


@health_bp.route('/healthz')
def healthz():
    """
    Lightweight health check endpoint for Autoscale.
    Returns 200 immediately without any database operations.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'skaila',
        'uptime_seconds': int(time.time() - _start_time)
    }), 200


@health_bp.route('/health')
def health():
    """
    Alternative health check endpoint.
    Returns 200 immediately without any database operations.
    """
    return jsonify({
        'status': 'ok',
        'service': 'skaila'
    }), 200


@health_bp.route('/ready')
def ready():
    """
    Readiness check - indicates if the service is ready to accept traffic.
    Returns 200 immediately. Database checks are optional and non-blocking.
    """
    return jsonify({
        'status': 'ready',
        'service': 'skaila'
    }), 200


@health_bp.route('/health/db')
def health_db():
    """
    Database health check - only use for debugging, not for Autoscale probes.
    This endpoint performs a database query and may be slow.
    """
    try:
        from services.database.database_manager import db_manager
        result = db_manager.query('SELECT 1 as check', one=True)
        if result and result.get('check') == 1:
            return jsonify({
                'status': 'healthy',
                'database': db_manager.db_type,
                'connection': 'ok'
            }), 200
        else:
            return jsonify({
                'status': 'degraded',
                'database': db_manager.db_type,
                'connection': 'error'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
