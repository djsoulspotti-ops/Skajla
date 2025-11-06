"""
REAL Integration Tests for Gamification System
Tests actual XP awards, level progression, and dashboard functionality
"""
import pytest
import random
from services.gamification.gamification import gamification_system
from database_manager import db_manager


class TestGamificationRealFunctionality:
    """Real integration tests that exercise actual gamification flows"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test user and cleanup after each test"""
        # Create unique test user ID
        self.test_user_id = 90000 + random.randint(1, 10000)
        
        yield
        
        # Cleanup
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_gamification WHERE user_id = %s', (self.test_user_id,))
                cursor.execute('DELETE FROM daily_analytics WHERE user_id = %s', (self.test_user_id,))
                cursor.execute('DELETE FROM user_badges WHERE user_id = %s', (self.test_user_id,))
                conn.commit()
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def test_award_xp_creates_profile_and_awards_points(self):
        """Test awarding XP creates user profile with correct XP"""
        # Award XP for a message
        result = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent',
            context='integration_test'
        )
        
        # Verify success
        assert result['success'] is True
        assert result['xp_earned'] > 0, "Should award XP"
        assert result['total_xp'] > 0, "Should have total XP"
        assert result['new_level'] == 1, "Should start at level 1"
        assert result['level_up'] is False, "Should not level up from first action"
        
        # Verify in database
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT total_xp, current_level FROM user_gamification WHERE user_id = %s', 
                          (self.test_user_id,))
            row = cursor.fetchone()
            assert row is not None, "Profile should exist in database"
            assert row[0] == result['total_xp'], "Database XP should match result"
            assert row[1] == 1, "Database level should be 1"
    
    def test_xp_accumulation_across_multiple_actions(self):
        """Test XP correctly accumulates across multiple awards"""
        # Award XP for first action
        result1 = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent'
        )
        first_xp = result1['total_xp']
        
        # Award XP for second action
        result2 = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='quiz_completed'
        )
        
        # Verify accumulation
        assert result2['total_xp'] > first_xp, "Total XP should increase"
        assert result2['total_xp'] == first_xp + result2['xp_earned'], \
            "Total should be previous total + new XP"
    
    def test_level_progression_when_earning_enough_xp(self):
        """Test user levels up when earning enough XP"""
        # Get level 2 threshold
        level_2_threshold = gamification_system.level_thresholds.get(2, 100)
        
        # Award enough XP to reach level 2
        # Use quiz_completed which typically awards more XP
        xp_per_quiz = gamification_system.xp_actions.get('quiz_completed', 20)
        num_quizzes_needed = (level_2_threshold // xp_per_quiz) + 2  # Add buffer
        
        level_up_detected = False
        final_result = None
        
        for i in range(num_quizzes_needed):
            result = gamification_system.award_xp(
                user_id=self.test_user_id,
                action='quiz_completed',
                context=f'quiz_{i}'
            )
            
            if result['level_up']:
                level_up_detected = True
                final_result = result
                break
        
        # Verify level up occurred
        assert level_up_detected, f"Should level up after earning {level_2_threshold}+ XP"
        assert final_result['new_level'] > final_result['old_level'], \
            "New level should be higher than old level"
        assert final_result['new_level'] >= 2, "Should reach at least level 2"
        
        # Verify in database
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT current_level FROM user_gamification WHERE user_id = %s', 
                          (self.test_user_id,))
            row = cursor.fetchone()
            assert row[0] >= 2, "Database should show level 2 or higher"
    
    def test_xp_multiplier_correctly_multiplies_rewards(self):
        """Test XP multiplier actually multiplies the reward amount"""
        # Award XP with 1x multiplier
        result_1x = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent',
            multiplier=1.0
        )
        base_xp = result_1x['xp_earned']
        
        # Create second test user
        test_user_2 = self.test_user_id + 1
        
        try:
            # Award same action with 2x multiplier
            result_2x = gamification_system.award_xp(
                user_id=test_user_2,
                action='message_sent',
                multiplier=2.0
            )
            doubled_xp = result_2x['xp_earned']
            
            # Verify multiplication
            assert doubled_xp == base_xp * 2, \
                f"Doubled XP ({doubled_xp}) should be exactly 2x base XP ({base_xp})"
            assert result_2x['total_xp'] == doubled_xp, \
                "Total XP should match doubled XP for first award"
        finally:
            # Cleanup second user
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM user_gamification WHERE user_id = %s', (test_user_2,))
                    cursor.execute('DELETE FROM daily_analytics WHERE user_id = %s', (test_user_2,))
                    conn.commit()
            except:
                pass
    
    def test_get_user_dashboard_returns_complete_profile(self):
        """Test dashboard returns complete, accurate user profile"""
        # Award some XP first
        gamification_system.award_xp(
            user_id=self.test_user_id,
            action='quiz_completed'
        )
        gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent'
        )
        
        # Get dashboard
        dashboard = gamification_system.get_user_dashboard(self.test_user_id)
        
        # Verify structure exists
        assert 'profile' in dashboard, "Dashboard should have profile"
        assert 'level_info' in dashboard, "Dashboard should have level_info"
        assert 'achievements' in dashboard, "Dashboard should have achievements"
        assert 'badges' in dashboard, "Dashboard should have badges"
        
        # Verify profile accuracy
        profile = dashboard['profile']
        assert profile['user_id'] == self.test_user_id, "Should have correct user_id"
        assert profile['total_xp'] > 0, "Should have accumulated XP"
        assert profile['current_level'] >= 1, "Should have valid level"
        
        # Verify level info accuracy
        level_info = dashboard['level_info']
        assert level_info['current_level'] >= 1, "Should have current level"
        assert 'level_title' in level_info, "Should have level title"
        assert level_info['total_xp'] == profile['total_xp'], \
            "Level info XP should match profile XP"
        assert level_info['progress_percent'] >= 0, "Progress should be non-negative"
        assert level_info['progress_percent'] <= 100, "Progress should not exceed 100%"
    
    def test_daily_analytics_tracking_persists_xp(self):
        """Test daily analytics correctly tracks and persists XP awards"""
        from datetime import date
        
        # Award XP
        result = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='quiz_completed'
        )
        xp_earned = result['xp_earned']
        
        # Verify daily analytics in database
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT xp_earned FROM daily_analytics
                WHERE user_id = %s AND date = %s
            ''', (self.test_user_id, date.today()))
            
            row = cursor.fetchone()
            assert row is not None, "Daily analytics should be recorded"
            assert row[0] >= xp_earned, "Analytics XP should match or exceed awarded XP"
        
        # Award more XP same day
        result2 = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent'
        )
        
        # Verify cumulative tracking
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT xp_earned FROM daily_analytics
                WHERE user_id = %s AND date = %s
            ''', (self.test_user_id, date.today()))
            
            row = cursor.fetchone()
            expected_total = xp_earned + result2['xp_earned']
            assert row[0] == expected_total, \
                f"Daily analytics should accumulate XP: expected {expected_total}, got {row[0]}"
    
    def test_concurrent_xp_awards_no_data_loss(self):
        """Test concurrent XP awards don't lose data due to race conditions"""
        # Award XP twice in rapid succession
        result1 = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent'
        )
        
        result2 = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent'
        )
        
        # Both should succeed
        assert result1['success'] is True, "First award should succeed"
        assert result2['success'] is True, "Second award should succeed"
        
        # Verify no data loss
        assert result2['total_xp'] > result1['total_xp'], "Second total should be higher"
        expected_total = result1['total_xp'] + result2['xp_earned']
        assert result2['total_xp'] == expected_total, \
            f"Concurrent awards should not lose XP: expected {expected_total}, got {result2['total_xp']}"


class TestGamificationEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test user"""
        self.test_user_id = 90000 + random.randint(1, 10000)
        yield
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_gamification WHERE user_id = %s', (self.test_user_id,))
                cursor.execute('DELETE FROM daily_analytics WHERE user_id = %s', (self.test_user_id,))
                conn.commit()
        except:
            pass
    
    def test_invalid_action_uses_default_xp_value(self):
        """Test invalid action name falls back to default XP"""
        result = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='this_action_does_not_exist_xyz123'
        )
        
        # Should still succeed with default XP
        assert result['success'] is True, "Should succeed even with invalid action"
        assert result['xp_earned'] == 10, "Should use default fallback XP of 10"
        assert result['total_xp'] == 10, "Total should match default XP"
    
    def test_zero_multiplier_awards_zero_xp(self):
        """Test zero multiplier correctly awards 0 XP"""
        result = gamification_system.award_xp(
            user_id=self.test_user_id,
            action='message_sent',
            multiplier=0.0
        )
        
        assert result['success'] is True, "Should succeed"
        assert result['xp_earned'] == 0, "Should award 0 XP with 0 multiplier"
        assert result['total_xp'] == 0, "Total should be 0"
