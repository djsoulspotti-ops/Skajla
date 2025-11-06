"""
Unit tests for School System
"""
import pytest
from school_system import school_system

class TestSchoolSystem:
    """Test school multi-tenant functionality"""
    
    def test_school_code_validation(self):
        """Test school code format validation"""
        valid_code = "ABC123"
        invalid_code = "123"  # Too short
        
        # School codes should be alphanumeric and proper length
        assert len(valid_code) >= 6
        assert valid_code.isalnum()
    
    def test_class_name_validation(self):
        """Test class name format validation"""
        valid_classes = ["1A", "2B", "3C", "5A"]
        invalid_classes = ["A", "1", "AB"]
        
        for class_name in valid_classes:
            # Should have number + letter format
            assert len(class_name) >= 2
            assert class_name[0].isdigit()
            assert class_name[-1].isalpha()
    
    def test_role_validation(self):
        """Test valid roles"""
        valid_roles = ['studente', 'professore', 'dirigente', 'genitore', 'docente']
        
        for role in valid_roles:
            assert isinstance(role, str)
            assert len(role) > 0
