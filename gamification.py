"""
SKAILA Gamification System - Sistema completo di gamification
Sistema avanzato di punti, livelli, achievement e classifiche per motivare gli studenti
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random
from core.config.gamification_config import XPConfig, LevelConfig, BadgeConfig, StreakConfig
from database_manager import db_manager

class SKAILAGamification:
    def __init__(self):
        self.xp_multipliers = XPConfig.MULTIPLIERS
        self.xp_actions = XPConfig.ACTIONS
        self.level_thresholds = self._calculate_level_thresholds()
        self.level_titles = self._init_level_titles()

    def _calculate_level_thresholds(self):
        thresholds = {1: 0}
        total_xp = 0
        for level in range(2, 101):
            if level <= 10:
                xp_needed = 100 * level
            elif level <= 25:
                xp_needed = 150 * level
            elif level <= 50:
                xp_needed = 200 * level
            else:
                xp_needed = 300 * level
            total_xp += xp_needed
            thresholds[level] = total_xp
        return thresholds

    def _init_level_titles(self):
        return LevelConfig.TITLES

    def init_gamification_tables(self):
        """Inizializza le tabelle per il sistema di gamification completo"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                is_postgres = db_manager.db_type == 'postgresql'
                timestamp_type = 'TIMESTAMP' if is_postgres else 'DATETIME'
                serial_type = 'SERIAL PRIMARY KEY' if is_postgres else 'INTEGER PRIMARY KEY AUTOINCREMENT'
                
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_gamification (
                        user_id INTEGER PRIMARY KEY,
                        total_xp INTEGER DEFAULT 0,
                        current_level INTEGER DEFAULT 1,
                        current_streak INTEGER DEFAULT 0,
                        longest_streak INTEGER DEFAULT 0,
                        last_activity_date DATE,
                        achievements_unlocked INTEGER DEFAULT 0,
                        badges_earned INTEGER DEFAULT 0,
                        quizzes_completed INTEGER DEFAULT 0,
                        perfect_quizzes INTEGER DEFAULT 0,
                        messages_sent INTEGER DEFAULT 0,
                        materials_downloaded INTEGER DEFAULT 0,
                        study_sessions INTEGER DEFAULT 0,
                        avatar_id TEXT DEFAULT 'default',
                        theme_id TEXT DEFAULT 'purple',
                        team_challenges_participated INTEGER DEFAULT 0,
                        team_challenges_won INTEGER DEFAULT 0,
                        created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        updated_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_unlocked_items (
                        id {serial_type},
                        user_id INTEGER,
                        item_type TEXT,
                        item_id TEXT,
                        unlocked_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        xp_cost INTEGER DEFAULT 0,
                        UNIQUE(user_id, item_type, item_id)
                    )
                ''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS team_challenges (
                        id {serial_type},
                        challenge_id TEXT,
                        challenge_name TEXT,
                        class_a TEXT,
                        class_b TEXT,
                        start_date {timestamp_type},
                        end_date {timestamp_type},
                        class_a_progress INTEGER DEFAULT 0,
                        class_b_progress INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        winner_class TEXT,
                        created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS team_challenge_participants (
                        id {serial_type},
                        challenge_id INTEGER,
                        user_id INTEGER,
                        contribution INTEGER DEFAULT 0,
                        joined_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(challenge_id, user_id)
                    )
                ''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS daily_analytics (
                        id {serial_type},
                        user_id INTEGER,
                        date DATE,
                        xp_earned INTEGER DEFAULT 0,
                        quizzes_completed INTEGER DEFAULT 0,
                        messages_sent INTEGER DEFAULT 0,
                        materials_downloaded INTEGER DEFAULT 0,
                        study_time_minutes INTEGER DEFAULT 0,
                        ai_interactions INTEGER DEFAULT 0,
                        perfect_scores INTEGER DEFAULT 0,
                        achievements_unlocked INTEGER DEFAULT 0,
                        badges_earned INTEGER DEFAULT 0,
                        created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, date)
                    )
                ''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_achievements (
                        id {serial_type},
                        user_id INTEGER,
                        achievement_id TEXT,
                        unlocked_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        xp_earned INTEGER DEFAULT 0,
                        UNIQUE(user_id, achievement_id)
                    )
                ''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_badges (
                        id {serial_type},
                        user_id INTEGER,
                        badge_id TEXT,
                        earned_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        xp_earned INTEGER DEFAULT 0,
                        rarity TEXT,
                        UNIQUE(user_id, badge_id)
                    )
                ''')

                conn.commit()
                print("✅ Tabelle gamification create con successo")
                
        except Exception as e:
            print(f"⚠️ Errore creazione tabelle gamification: {e}")

    def award_xp(self, user_id: int, action: str, multiplier: float = 1.0, context: str = None) -> Dict[str, Any]:
        """Assegna XP per un'azione (stub minimal)"""
        try:
            xp_amount = self.xp_actions.get(action, 10) * multiplier
            return {'success': True, 'xp_earned': int(xp_amount), 'level_up': False}
        except Exception as e:
            print(f"⚠️ Errore award_xp: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Ottieni statistiche utente (stub minimal)"""
        try:
            result = db_manager.query(
                'SELECT * FROM user_gamification WHERE user_id = %s',
                (user_id,),
                one=True
            )
            if result:
                return dict(result)
            return {
                'user_id': user_id,
                'total_xp': 0,
                'current_level': 1,
                'current_streak': 0
            }
        except Exception as e:
            print(f"⚠️ Errore get_user_stats: {e}")
            return {'user_id': user_id, 'total_xp': 0, 'current_level': 1}

gamification_system = SKAILAGamification()

def init_gamification():
    """Inizializza il sistema di gamification"""
    try:
        gamification_system.init_gamification_tables()
        print("🎮 Sistema di Gamification SKAILA completo inizializzato!")
    except Exception as e:
        print(f"⚠️ Errore inizializzazione gamification: {e}")

if __name__ == "__main__":
    init_gamification()
