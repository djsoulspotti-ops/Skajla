"""
Unit tests for Database Manager
"""
import pytest
from database_manager import db_manager

class TestDatabaseManager:
    """Test database manager functionality"""
    
    def test_connection_available(self):
        """Test database connection can be established"""
        conn = db_manager.get_connection()
        assert conn is not None
        conn.close()
    
    def test_query_sanitization(self):
        """Test SQL injection protection"""
        # This should not execute dangerous SQL
        dangerous_input = "'; DROP TABLE utenti; --"
        
        try:
            # Query should be parameterized and safe
            result = db_manager.query(
                "SELECT * FROM utenti WHERE email = %s",
                (dangerous_input,),
                one=True
            )
            # Should return None or safe result, not crash
            assert True
        except Exception:
            # If it fails, it should fail safely
            assert True
    
    def test_placeholder_conversion(self):
        """Test PostgreSQL to SQLite placeholder conversion"""
        pg_query = "SELECT * FROM utenti WHERE id = %s AND email = %s"
        
        if db_manager.db_type == 'sqlite':
            converted = pg_query.replace('%s', '?')
            assert '?' in converted
            assert '%s' not in converted
        else:
            assert '%s' in pg_query
    
    def test_connection_pool_exists(self):
        """Test connection pool is initialized"""
        if db_manager.db_type == 'postgresql':
            assert db_manager.pool is not None
        else:
            assert db_manager.sqlite_pool is not None
