"""
Pytest configuration and shared fixtures for SKAILA tests
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import SkailaApp
from database_manager import db_manager

@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing"""
    skaila = SkailaApp()
    skaila.app.config['TESTING'] = True
    skaila.app.config['WTF_CSRF_ENABLED'] = False
    return skaila.app

@pytest.fixture(scope='session')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session():
    """Create clean database session for each test"""
    connection = db_manager.get_connection()
    yield connection
    # Rollback any changes after test
    if hasattr(connection, 'rollback'):
        connection.rollback()
    connection.close()

@pytest.fixture
def mock_user():
    """Mock user data for testing"""
    return {
        'id': 1,
        'email': 'test@example.com',
        'nome': 'Test',
        'cognome': 'User',
        'ruolo': 'studente',
        'scuola_id': 1,
        'classe': '3A',
        'attivo': True
    }

@pytest.fixture
def mock_teacher():
    """Mock teacher data for testing"""
    return {
        'id': 2,
        'email': 'teacher@example.com',
        'nome': 'Teacher',
        'cognome': 'Test',
        'ruolo': 'professore',
        'scuola_id': 1,
        'attivo': True
    }

@pytest.fixture
def mock_admin():
    """Mock admin data for testing"""
    return {
        'id': 3,
        'email': 'admin@example.com',
        'nome': 'Admin',
        'cognome': 'Test',
        'ruolo': 'dirigente',
        'scuola_id': 1,
        'attivo': True
    }

@pytest.fixture
def auth_headers(client, mock_user):
    """Create authenticated session headers"""
    with client.session_transaction() as session:
        session['user_id'] = mock_user['id']
        session['email'] = mock_user['email']
        session['ruolo'] = mock_user['ruolo']
        session['scuola_id'] = mock_user['scuola_id']
    return {}

@pytest.fixture
def sample_xp_data():
    """Sample gamification XP data"""
    return {
        'user_id': 1,
        'action': 'quiz_completed',
        'xp_amount': 50,
        'multiplier': 1.5
    }

@pytest.fixture
def sample_grade_data():
    """Sample grade data for registro"""
    return {
        'student_id': 1,
        'subject': 'matematica',
        'grade': 8.5,
        'date': datetime.now().date(),
        'teacher_id': 2,
        'note': 'Ottimo test'
    }
