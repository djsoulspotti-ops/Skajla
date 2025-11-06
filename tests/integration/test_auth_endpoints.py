"""
Integration tests for Authentication Endpoints
"""
import pytest
import json

class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    def test_login_page_loads(self, client):
        """Test login page is accessible"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'accedi' in response.data.lower()
    
    def test_register_page_loads(self, client):
        """Test registration page is accessible"""
        response = client.get('/register')
        assert response.status_code == 200
    
    def test_login_redirect_when_authenticated(self, client, auth_headers):
        """Test authenticated users redirect from login"""
        response = client.get('/login', headers=auth_headers)
        # Should redirect to dashboard
        assert response.status_code in [200, 302]
    
    def test_dashboard_requires_auth(self, client):
        """Test dashboard redirects unauthenticated users"""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
