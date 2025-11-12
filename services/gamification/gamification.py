"""
SKAILA Gamification System - Sistema completo di gamification
Sistema avanzato di punti, livelli, achievement e classifiche per motivare gli studenti
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random
from services.gamification.gamification_config import XPConfig, LevelConfig, BadgeConfig, StreakConfig
from services.database.database_manager import db_manager

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

    def award_xp(self, user_id: int, action: str, multiplier: float = 1.0, context: str = "") -> Dict[str, Any]:
        """Assegna XP per un'azione e persiste nel database (atomico, concurrency-safe)"""
        try:
            xp_amount = int(self.xp_actions.get(action, 10) * multiplier)
            today = datetime.now().date()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO user_gamification (user_id, total_xp, current_level, last_activity_date)
                    VALUES (%s, %s, 1, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET total_xp = user_gamification.total_xp + %s,
                        last_activity_date = %s,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING total_xp, current_level
                ''', (user_id, xp_amount, today, xp_amount, today))
                
                result = cursor.fetchone()
                new_xp = result[0]
                old_level = result[1]
                new_level = self._calculate_level_from_xp(new_xp)
                level_up = new_level > old_level
                
                if level_up:
                    cursor.execute('''
                        UPDATE user_gamification
                        SET current_level = %s
                        WHERE user_id = %s
                    ''', (new_level, user_id))
                
                cursor.execute('''
                    INSERT INTO daily_analytics (user_id, date, xp_earned)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, date) DO UPDATE
                    SET xp_earned = daily_analytics.xp_earned + %s
                ''', (user_id, today, xp_amount, xp_amount))
                
                conn.commit()
            
            return {
                'success': True,
                'xp_earned': xp_amount,
                'total_xp': new_xp,
                'old_level': old_level,
                'new_level': new_level,
                'level_up': level_up,
                'context': context
            }
        except Exception as e:
            print(f"⚠️ Errore award_xp: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_level_from_xp(self, total_xp: int) -> int:
        """Calcola il livello basato sull'XP totale"""
        for level in range(100, 0, -1):
            if total_xp >= self.level_thresholds.get(level, 0):
                return level
        return 1

    def get_user_stats(self, user_id: int) :
        """Ottieni statistiche utente (stub minimal)"""
        try:
            result = db_manager.query(
                'SELECT * FROM user_gamification WHERE user_id = %s',
                (user_id,),
                one=True
            )
            
            return result
        except Exception as e:
            print(f"⚠️ Errore get_user_stats: {e}")
            return {'user_id': user_id, 'total_xp': 0, 'current_level': 1}

    def get_or_create_profile(self, user_id: int) -> Dict[str, Any]:
        """Ottieni o crea profilo gamification utente"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prova a ottenere profilo esistente
                cursor.execute('SELECT * FROM user_gamification WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(zip([desc[0] for desc in cursor.description], result))
                
                # Crea nuovo profilo
                cursor.execute('''
                    INSERT INTO user_gamification (user_id, total_xp, current_level, current_streak)
                    VALUES (%s, 0, 1, 0)
                    RETURNING *
                ''', (user_id,))
                
                result = cursor.fetchone()
                conn.commit()
                
                return dict(zip([desc[0] for desc in cursor.description], result))
        except Exception as e:
            print(f"⚠️ Errore get_or_create_profile: {e}")
            return {
                'user_id': user_id,
                'total_xp': 0,
                'current_level': 1,
                'current_streak': 0,
                'longest_streak': 0,
                'achievements_unlocked': 0,
                'badges_earned': 0,
                'quizzes_completed': 0
            }

    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Alias per get_user_dashboard - retrocompatibilità"""
        return self.get_user_dashboard(user_id)
    
    def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Ottieni dati dashboard completi per utente"""
        try:
            profile = self.get_or_create_profile(user_id)
            
            # Calcola progresso al prossimo livello
            current_level = profile.get('current_level', 1)
            total_xp = profile.get('total_xp', 0)
            
            next_level_xp = self.level_thresholds.get(current_level + 1, total_xp + 1000)
            current_level_xp = self.level_thresholds.get(current_level, 0)
            xp_progress = total_xp - current_level_xp
            xp_needed = next_level_xp - current_level_xp
            progress_percent = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 0
            
            return {
                'profile': profile,
                'level_info': {
                    'current_level': current_level,
                    'level_title': self.level_titles.get(current_level, 'Studente'),
                    'total_xp': total_xp,
                    'xp_to_next_level': xp_needed - xp_progress,
                    'progress_percent': progress_percent
                },
                'achievements': [],
                'badges': [],
                'recent_activity': []
            }
        except Exception as e:
            print(f"⚠️ Errore get_user_dashboard: {e}")
            return {
                'profile': {
                    'user_id': user_id,
                    'total_xp': 0,
                    'current_level': 1,
                    'current_streak': 0
                },
                'level_info': {
                    'current_level': 1,
                    'level_title': 'Studente',
                    'total_xp': 0,
                    'xp_to_next_level': 100,
                    'progress_percent': 0
                },
                'achievements': [],
                'badges': [],
                'recent_activity': []
            }

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
