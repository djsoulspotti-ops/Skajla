#!/usr/bin/env python3
"""
WSGI entry point per production deployment con Gunicorn + eventlet
SKAILA Platform - Production WSGI Application

Usage with Gunicorn:
  gunicorn --config gunicorn.conf.py wsgi:application
"""

# Eventlet monkey patch MUST happen before any other imports
import eventlet
eventlet.monkey_patch()

import os
import sys

# Aggiungi directory corrente al path Python
sys.path.insert(0, os.path.dirname(__file__))

# Import create_app factory
from main import create_app

# Crea applicazione SKAILA
print("🚀 WSGI: Creating SKAILA application...")
skaila_app = create_app()

# WSGI application per Gunicorn standard
# This is the main entry point that Gunicorn will use
application = skaila_app.app

# Alias for backwards compatibility
app = application
socketio_app = application

print("✅ WSGI: Application created and ready")

if __name__ == "__main__":
    # Development mode - usa run() diretto
    skaila_app.run()