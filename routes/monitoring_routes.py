"""
Production Monitoring Routes per SKAILA
Health checks, metrics, e system monitoring endpoints
"""

import os
import time
import json
import psutil
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from database_manager import db_manager
from environment_manager import env_manager

monitoring_bp = Blueprint('monitoring', __name__)

# Startup time per uptime calculation
startup_time = datetime.utcnow()

@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint base per load balancers"""
    try:
        # Test database connection
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Basic health status
    health_status = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": db_status
    }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@monitoring_bp.route('/health/live', methods=['GET'])
def liveness_probe():
    """Kubernetes liveness probe - verifica che l'app sia alive"""
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - startup_time).total_seconds()
    }), 200

@monitoring_bp.route('/health/ready', methods=['GET'])
def readiness_probe():
    """Kubernetes readiness probe - verifica che l'app sia ready per traffic"""
    checks = {
        "database": False,
        "environment": False,
        "dependencies": False
    }
    
    # Database and Environment readiness with connectivity test
    try:
        # Test database connectivity explicitly for readiness check
        db_status = env_manager.get_database_status(test_connectivity=True)
        checks["database"] = db_status.get('configured', False)
        
        # Basic environment configuration check
        flask_config = env_manager.get_flask_config()
        checks["environment"] = flask_config.get('SECRET_KEY') is not None
    except:
        checks["environment"] = False
        checks["database"] = False
    
    # Dependencies readiness (basic check)
    checks["dependencies"] = True  # Always true se imports funzionano
    
    all_ready = all(checks.values())
    
    response = {
        "status": "ready" if all_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
    
    status_code = 200 if all_ready else 503
    return jsonify(response), status_code

@monitoring_bp.route('/metrics', methods=['GET'])
def metrics_endpoint():
    """Metrics endpoint in formato Prometheus per monitoring systems"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database metrics
    db_connections = 0
    db_response_time = 0
    
    try:
        start_time = time.time()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if db_manager.db_type == 'postgresql':
                cursor.execute('SELECT count(*) FROM pg_stat_activity')
                result = cursor.fetchone()
                db_connections = result[0] if result else 0
            else:
                # SQLite - connection count sempre 1
                db_connections = 1
        db_response_time = (time.time() - start_time) * 1000  # ms
    except:
        db_response_time = -1
    
    # Application metrics
    app_metrics = {
        "skaila_uptime_seconds": (datetime.utcnow() - startup_time).total_seconds(),
        "skaila_cpu_usage_percent": cpu_percent,
        "skaila_memory_usage_bytes": memory.used,
        "skaila_memory_total_bytes": memory.total,
        "skaila_memory_usage_percent": memory.percent,
        "skaila_disk_usage_bytes": disk.used,
        "skaila_disk_total_bytes": disk.total,
        "skaila_disk_usage_percent": (disk.used / disk.total) * 100,
        "skaila_database_connections": db_connections,
        "skaila_database_response_time_ms": db_response_time,
        "skaila_database_type": 1 if db_manager.db_type == 'postgresql' else 0,
        "skaila_environment_production": 1 if env_manager.is_production() else 0,
        "skaila_ai_enabled": 1 if env_manager.get_ai_status()['mode'] == 'live' else 0
    }
    
    # Formato Prometheus
    output = []
    for metric_name, value in app_metrics.items():
        output.append(f"# HELP {metric_name} SKAILA application metric")
        output.append(f"# TYPE {metric_name} gauge")
        output.append(f"{metric_name} {value}")
        output.append("")
    
    return '\n'.join(output), 200, {'Content-Type': 'text/plain'}

@monitoring_bp.route('/metrics/json', methods=['GET'])
def metrics_json():
    """Metrics in formato JSON per debugging e custom monitoring"""
    
    # System info
    cpu_times = psutil.cpu_times()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database info
    db_info = {
        "type": db_manager.db_type,
        "status": "unknown",
        "response_time_ms": 0
    }
    
    try:
        start_time = time.time()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            db_info["status"] = "connected"
            db_info["response_time_ms"] = (time.time() - start_time) * 1000
    except Exception as e:
        db_info["status"] = f"error: {str(e)}"
        db_info["response_time_ms"] = -1
    
    # Environment info
    env_info = env_manager.get_system_status()
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - startup_time).total_seconds(),
        "system": {
            "cpu": {
                "usage_percent": psutil.cpu_percent(),
                "count": psutil.cpu_count(),
                "times": {
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "idle": cpu_times.idle
                }
            },
            "memory": {
                "total_bytes": memory.total,
                "used_bytes": memory.used,
                "free_bytes": memory.free,
                "usage_percent": memory.percent
            },
            "disk": {
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
                "usage_percent": (disk.used / disk.total) * 100
            }
        },
        "database": db_info,
        "environment": env_info,
        "application": {
            "name": "SKAILA",
            "version": "1.0.0",
            "environment": "production" if env_manager.is_production() else "development"
        }
    }
    
    return jsonify(metrics), 200

@monitoring_bp.route('/debug/info', methods=['GET'])
def debug_info():
    """Debug information endpoint per troubleshooting"""
    
    # Solo in development mode
    if env_manager.is_production():
        return jsonify({"error": "Debug endpoint disabled in production"}), 403
    
    import sys
    
    debug_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "path": sys.path[:5]  # Prime 5 entries
        },
        "environment_variables": {
            key: "***" if "key" in key.lower() or "secret" in key.lower() or "password" in key.lower() else value
            for key, value in os.environ.items()
            if not key.startswith('_')  # Skip private vars
        },
        "database": {
            "type": db_manager.db_type,
            "pool_info": getattr(db_manager, 'pool_stats', {}) if hasattr(db_manager, 'pool_stats') else "No pool stats"
        },
        "system": {
            "platform": os.name,
            "cwd": os.getcwd(),
            "user": os.environ.get('USER', 'unknown')
        }
    }
    
    return jsonify(debug_data), 200