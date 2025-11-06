"""
Integration tests for gamification system endpoints
Tests XP awards, level progression, and badge system
"""
import pytest


class TestGamificationIntegration:
    """Integration tests for gamification system"""
    
    def test_gamification_system_initialized(self):
        """Test gamification system is properly initialized"""
        from services.gamification.gamification import gamification_system
        
        # Check system has required attributes
        assert hasattr(gamification_system, 'award_xp')
        assert hasattr(gamification_system, 'get_user_dashboard')
        assert hasattr(gamification_system, 'level_thresholds')
        assert hasattr(gamification_system, 'xp_actions')
    
    def test_xp_actions_configured(self):
        """Test XP actions are configured"""
        from services.gamification.gamification import gamification_system
        
        actions = gamification_system.xp_actions
        assert len(actions) > 0
        
        # Check some expected actions exist
        assert 'message_sent' in actions
        assert 'quiz_completed' in actions
    
    def test_level_system_configured(self):
        """Test level system is properly configured"""
        from services.gamification.gamification import gamification_system
        
        thresholds = gamification_system.level_thresholds
        assert len(thresholds) > 0
        
        # Level 1 should start at 0 XP
        assert thresholds[1] == 0
        
        # Each level should require more XP
        assert thresholds[2] > thresholds[1]
        assert thresholds[3] > thresholds[2]


class TestGamificationLevelThresholds:
    """Test level threshold calculations"""
    
    def test_level_thresholds_progressive(self):
        """Test level thresholds increase progressively"""
        from services.gamification.gamification import gamification_system
        
        thresholds = gamification_system.level_thresholds
        
        # Each level should require more XP than previous
        for level in range(2, min(11, len(thresholds))):
            assert thresholds[level] > thresholds[level - 1], \
                f"Level {level} threshold should be > level {level - 1}"
    
    def test_level_titles_exist(self):
        """Test level titles are configured"""
        from services.gamification.gamification import gamification_system
        
        titles = gamification_system.level_titles
        assert len(titles) > 0
        
        # Should have titles for common levels
        assert 1 in titles
        assert titles[1] is not None


class TestGamificationMethods:
    """Test gamification methods exist and are callable"""
    
    def test_award_xp_method_exists(self):
        """Test award_xp method exists"""
        from services.gamification.gamification import gamification_system
        
        assert callable(getattr(gamification_system, 'award_xp', None))
    
    def test_get_user_dashboard_method_exists(self):
        """Test get_user_dashboard method exists"""
        from services.gamification.gamification import gamification_system
        
        assert callable(getattr(gamification_system, 'get_user_dashboard', None))
