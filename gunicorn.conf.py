"""
Gunicorn configuration per SKAILA production deployment
Ottimizzato per SocketIO + eventlet workers
"""

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"

# TEMPORARY FIX: Switch to sync worker to resolve eventlet mainloop blocking
# Will revert to eventlet after resolving compatibility issues
workers = 1  # Single worker for now 
worker_class = "sync"  # Changed from eventlet to sync temporarily
# worker_connections = 1000  # Not needed for sync worker

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

# Timeouts
timeout = 120  # Increased per SocketIO long polling
keepalive = 5
graceful_timeout = 30

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
    server.log.info("SKAILA Server ready - eventlet monkey patching handled in wsgi.py")

def worker_int(worker):
    """Graceful shutdown per SocketIO connections"""
    worker.log.info("Worker ricevuto SIGINT - graceful shutdown SocketIO")

def on_exit(server):
    """Cleanup on server exit"""
    server.log.info("SKAILA Server shutdown completato")