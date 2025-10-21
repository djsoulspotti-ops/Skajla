#!/usr/bin/env python3
"""
WSGI entry point per production deployment con Gunicorn + eventlet
SKAILA Platform - Production WSGI Application
"""

# Gevent monkey patch per async I/O (più stabile di eventlet)
from gevent import monkey
monkey.patch_all()

import os
import sys

# Aggiungi directory corrente al path Python
sys.path.insert(0, os.path.dirname(__file__))

from main import create_app

# Crea applicazione SKAILA
skaila_app = create_app()

# WSGI application per Gunicorn standard
application = skaila_app.app

# SocketIO WSGI callable per Gunicorn con eventlet worker
# CORRECT: Flask app with SocketIO initialized is the WSGI callable
socketio_app = skaila_app.app

if __name__ == "__main__":
    # Development mode - usa run() diretto
    skaila_app.run()