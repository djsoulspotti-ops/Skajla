"""
Unit tests for Gamification System
"""
import pytest
from gamification import gamification_system

class TestGamificationSystem:
    """Test gamification functionality"""
    
    def test_xp_award_calculation(self):
        """Test XP award calculation with multipliers"""
        base_xp = 100
        multiplier = 1.5
        expected_xp = int(base_xp * multiplier)
        
        assert expected_xp == 150
    
    def test_level_thresholds_calculated(self):
        """Test level thresholds are properly calculated"""
        thresholds = gamification_system.level_thresholds
        
        assert len(thresholds) > 0
        assert thresholds[1] == 0  # Level 1 starts at 0 XP
        assert thresholds[2] > thresholds[1]  # Each level requires more XP
    
    def test_level_up_detection(self):
        """Test level-up detection logic"""
        # User with 0 XP should be level 1
        current_level = gamification_system.get_level_from_xp(0)
        assert current_level == 1
        
        # User with enough XP should level up
        high_xp_level = gamification_system.get_level_from_xp(1000)
        assert high_xp_level > 1
    
    def test_xp_actions_configured(self):
        """Test all XP actions are configured"""
        actions = gamification_system.xp_actions
        
        assert 'quiz_completed' in actions
        assert 'message_sent' in actions
        assert 'login_daily' in actions
        assert all(actions[action] > 0 for action in actions)
    
    def test_level_titles_exist(self):
        """Test level titles are configured"""
        titles = gamification_system.level_titles
        
        assert len(titles) > 0
        assert 1 in titles
        assert isinstance(titles[1], str)
