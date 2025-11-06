"""
Unit tests for Authentication Service
"""
import pytest
from services.auth_service import auth_service

class TestAuthService:
    """Test authentication service functionality"""
    
    def test_password_hashing(self):
        """Test password hashing is working"""
        password = "SecurePass123!"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert auth_service.verify_password(password, hashed) is True
    
    def test_password_verification_fails_wrong_password(self):
        """Test password verification fails with wrong password"""
        password = "SecurePass123!"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password("WrongPassword", hashed) is False
    
    def test_lockout_after_max_attempts(self):
        """Test account lockout after max failed attempts"""
        email = "test@example.com"
        
        # Record multiple failed attempts
        for _ in range(5):
            auth_service.record_failed_attempt(email)
        
        assert auth_service.is_locked_out(email) is True
    
    def test_lockout_reset_after_successful_login(self):
        """Test lockout counter resets after successful login"""
        email = "test@example.com"
        
        # Record failed attempts
        auth_service.record_failed_attempt(email)
        auth_service.record_failed_attempt(email)
        
        # Reset after successful login
        auth_service.reset_attempts(email)
        
        assert auth_service.is_locked_out(email) is False
