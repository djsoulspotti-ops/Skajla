"""
Gunicorn configuration per SKAJLA production deployment
Ottimizzato per SocketIO + eventlet workers
"""

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"

# Production-ready configuration per 100+ utenti simultanei
import multiprocessing

# Calcola workers ottimali: (2 * CPU cores) + 1
cpu_count = multiprocessing.cpu_count()
workers = min((cpu_count * 2) + 1, 4)  # Max 4 workers per Replit

# Eventlet worker per async I/O + SocketIO support
worker_class = "eventlet"
worker_connections = 1000  # Connessioni per worker

# Application - module specified in command line
# module = "wsgi:socketio_app"  # Specificato nel comando

# Process naming
proc_name = "skaila-production"

# Logging
accesslog = "-"  # stdout per container compatibility
errorlog = "-"   # stderr per container compatibility
loglevel = "info"
capture_output = True

# Performance
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# Timeouts ottimizzati per Autoscale health checks
timeout = 30  # 30 secondi - Autoscale expects fast responses
keepalive = 5  # Shorter keepalive for Autoscale compatibility
graceful_timeout = 30  # Graceful shutdown timeout

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Development vs Production
if os.getenv('ENVIRONMENT') == 'development':
    reload = True
    loglevel = "debug"
else:
    reload = False
    loglevel = "warning"

# Eventlet monkey patching moved to wsgi.py (happens before imports)
def when_ready(server):
    """Server ready callback - monkey patching now handled in wsgi.py"""
    server.log.info("SKAJLA Server ready - eventlet monkey patching handled in wsgi.py")

def worker_int(worker):
    """Graceful shutdown per SocketIO connections"""
    worker.log.info("Worker ricevuto SIGINT - graceful shutdown SocketIO")

def on_exit(server):
    """Cleanup on server exit"""
    server.log.info("SKAJLA Server shutdown completato")