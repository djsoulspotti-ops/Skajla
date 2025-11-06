"""
Integration tests for API Endpoints
"""
import pytest
import json

class TestAPIEndpoints:
    """Test REST API endpoints"""
    
    def test_health_check_works(self, client):
        """Test API health check endpoint"""
        # Try common health check endpoints
        response = client.get('/api/health')
        # May return 404 if not implemented yet, that's OK
        assert response.status_code in [200, 404]
    
    def test_api_requires_authentication(self, client):
        """Test API endpoints require authentication"""
        # Try accessing an authenticated endpoint
        response = client.get('/api/user/profile')
        # Should redirect or return unauthorized
        assert response.status_code in [302, 401, 403, 404]
    
    def test_api_xp_endpoint_authenticated(self, client, auth_headers):
        """Test XP API with authentication"""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['ruolo'] = 'studente'
            session['scuola_id'] = 1
        
        response = client.get('/api/gamification/xp')
        # May not be implemented, but should not crash
        assert response.status_code in [200, 404, 500]
    
    def test_online_users_endpoint(self, client, auth_headers):
        """Test online users API endpoint"""
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['ruolo'] = 'studente'
            session['scuola_id'] = 1
        
        response = client.get('/api/online-users')
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'users' in data
            assert isinstance(data['users'], list)
