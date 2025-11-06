"""
Integration tests for Messaging Endpoints
"""
import pytest

class TestMessagingEndpoints:
    """Test messaging and chat functionality"""
    
    def test_chat_requires_auth(self, client):
        """Test chat page requires authentication"""
        response = client.get('/chat')
        assert response.status_code == 302  # Redirect to login
    
    def test_chat_accessible_when_authenticated(self, client):
        """Test authenticated users can access chat"""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['ruolo'] = 'studente'
            session['scuola_id'] = 1
        
        response = client.get('/chat')
        assert response.status_code == 200
    
    def test_messaging_api_requires_auth(self, client):
        """Test messaging API requires authentication"""
        response = client.get('/api/messaging/rooms')
        # Should require auth
        assert response.status_code in [302, 401, 403, 404]
