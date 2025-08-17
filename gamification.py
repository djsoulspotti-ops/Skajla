
"""
SKAILA Gamification System - Sistema completo di gamification
Sistema avanzato di punti, livelli, achievement e classifiche per motivare gli studenti
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random

class SKAILAGamification:
    def __init__(self):
        # Sistema di punti XP
        self.xp_actions = {
            'login_daily': 10,
            'first_login_day': 25,
            'message_sent': 5,
            'ai_question': 15,
            'ai_correct_answer': 30,
            'quiz_completed': 25,
            'study_session_15min': 20,
            'study_session_30min': 40,
            'help_classmate': 35,
            'create_study_group': 50,
            'week_streak': 100,
            'month_streak': 300
        }

        # Livelli e soglie XP
        self.level_thresholds = {
            1: 0,      # Novizio
            2: 100,    # Apprendista
            3: 250,    # Studente
            4: 500,    # Studioso
            5: 1000,   # Esperto
            6: 2000,   # Maestro
            7: 3500,   # Genio
            8: 5500,   # Leggenda
            9: 8000,   # Prodigio
            10: 12000  # SKAILA Master
        }

        # Titoli per livelli
        self.level_titles = {
            1: "🌱 Novizio SKAILA",
            2: "📚 Apprendista",
            3: "🎓 Studente Attivo", 
            4: "⭐ Studioso Dedicato",
            5: "🏆 Esperto Learner",
            6: "👑 Maestro del Sapere",
            7: "🧠 Genio Accademico",
            8: "🚀 Leggenda di SKAILA",
            9: "💎 Prodigio Supremo",
            10: "🌟 SKAILA Master"
        }

        # Achievement dinamici
        self.achievements = {
            # Achievement di base
            'first_steps': {
                'name': '🌱 Primi Passi',
                'description': 'Prima conversazione su SKAILA',
                'xp_reward': 25,
                'condition': lambda stats: stats.get('total_messages', 0) >= 1,
                'category': 'base'
            },
            'social_butterfly': {
                'name': '🦋 Farfalla Sociale',
                'description': 'Scrivi 100 messaggi in chat',
                'xp_reward': 150,
                'condition': lambda stats: stats.get('total_messages', 0) >= 100,
                'category': 'sociale'
            },
            'ai_enthusiast': {
                'name': '🤖 Entusiasta AI',
                'description': 'Fai 50 domande all\'AI',
                'xp_reward': 200,
                'condition': lambda stats: stats.get('ai_interactions', 0) >= 50,
                'category': 'apprendimento'
            },
            'week_warrior': {
                'name': '⚔️ Guerriero della Settimana',
                'description': '7 giorni consecutivi su SKAILA',
                'xp_reward': 300,
                'condition': lambda stats: stats.get('max_streak', 0) >= 7,
                'category': 'persistenza'
            },
            'knowledge_seeker': {
                'name': '🔍 Cercatore di Conoscenza',
                'description': 'Completa 20 quiz AI',
                'xp_reward': 250,
                'condition': lambda stats: stats.get('quizzes_completed', 0) >= 20,
                'category': 'apprendimento'
            },
            'helper_hero': {
                'name': '🦸 Eroe del Supporto',
                'description': 'Aiuta 10 compagni con domande',
                'xp_reward': 400,
                'condition': lambda stats: stats.get('help_given', 0) >= 10,
                'category': 'supporto'
            },
            'subject_master': {
                'name': '🎯 Maestro di Materia',
                'description': 'Raggiungi 80% successo in una materia',
                'xp_reward': 500,
                'condition': lambda stats: any(score >= 0.8 for score in stats.get('subject_scores', {}).values()),
                'category': 'eccellenza'
            },
            'month_legend': {
                'name': '🏆 Leggenda del Mese',
                'description': '30 giorni consecutivi attivo',
                'xp_reward': 1000,
                'condition': lambda stats: stats.get('max_streak', 0) >= 30,
                'category': 'leggenda'
            }
        }

        # Sfide giornaliere
        self.daily_challenges = [
            {
                'id': 'daily_questions',
                'name': '❓ Curioso Giornaliero',
                'description': 'Fai 3 domande all\'AI oggi',
                'target': 3,
                'xp_reward': 50,
                'type': 'ai_questions'
            },
            {
                'id': 'social_day',
                'name': '💬 Socializzatore',
                'description': 'Scrivi 10 messaggi in chat oggi',
                'target': 10,
                'xp_reward': 40,
                'type': 'messages'
            },
            {
                'id': 'study_focus',
                'name': '📚 Concentrazione',
                'description': 'Studia per 30 minuti senza pause',
                'target': 30,
                'xp_reward': 80,
                'type': 'study_time'
            },
            {
                'id': 'quiz_master',
                'name': '🧠 Quiz Master',
                'description': 'Completa 5 quiz con successo',
                'target': 5,
                'xp_reward': 100,
                'type': 'quiz_success'
            }
        ]

        # Premi speciali
        self.special_rewards = {
            'weekend_warrior': {'name': '⚡ Weekend Warrior', 'bonus_xp': 1.5},
            'early_bird': {'name': '🌅 Early Bird', 'bonus_xp': 1.2},
            'night_owl': {'name': '🦉 Night Owl', 'bonus_xp': 1.2},
            'combo_master': {'name': '🔥 Combo Master', 'bonus_xp': 2.0}
        }

    def init_gamification_tables(self):
        """Inizializza le tabelle per il sistema di gamification"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Tabella profili gamification utenti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_gamification (
                user_id INTEGER PRIMARY KEY,
                total_xp INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                last_activity_date DATE,
                total_messages INTEGER DEFAULT 0,
                ai_interactions INTEGER DEFAULT 0,
                quizzes_completed INTEGER DEFAULT 0,
                help_given INTEGER DEFAULT 0,
                study_minutes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        # Tabella achievement utenti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id TEXT,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                xp_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES utenti (id),
                UNIQUE(user_id, achievement_id)
            )
        ''')

        # Tabella sfide giornaliere
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_challenges_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                challenge_id TEXT,
                challenge_date DATE,
                current_progress INTEGER DEFAULT 0,
                target_progress INTEGER,
                completed BOOLEAN DEFAULT 0,
                xp_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES utenti (id),
                UNIQUE(user_id, challenge_id, challenge_date)
            )
        ''')

        # Tabella classifiche
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                period_type TEXT, -- 'daily', 'weekly', 'monthly', 'all_time'
                period_date DATE,
                total_xp INTEGER,
                rank_position INTEGER,
                class_rank INTEGER,
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        # Tabella log attività XP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS xp_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,
                xp_earned INTEGER,
                bonus_multiplier REAL DEFAULT 1.0,
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        # Tabella ricompense speciali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS special_rewards_earned (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reward_type TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bonus_applied REAL,
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Tabelle gamification create con successo!")

    def get_or_create_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Ottieni o crea il profilo gamification dell'utente"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        profile = cursor.execute('''
            SELECT * FROM user_gamification WHERE user_id = ?
        ''', (user_id,)).fetchone()

        if not profile:
            # Crea nuovo profilo
            cursor.execute('''
                INSERT INTO user_gamification (user_id, last_activity_date)
                VALUES (?, DATE('now'))
            ''', (user_id,))
            conn.commit()
            
            profile = cursor.execute('''
                SELECT * FROM user_gamification WHERE user_id = ?
            ''', (user_id,)).fetchone()

        conn.close()

        if profile:
            return {
                'user_id': profile[0],
                'total_xp': profile[1],
                'current_level': profile[2],
                'current_streak': profile[3],
                'max_streak': profile[4],
                'last_activity_date': profile[5],
                'total_messages': profile[6],
                'ai_interactions': profile[7],
                'quizzes_completed': profile[8],
                'help_given': profile[9],
                'study_minutes': profile[10]
            }
        return {}

    def award_xp(self, user_id: int, action_type: str, bonus_multiplier: float = 1.0, description: str = "") -> Dict[str, Any]:
        """Assegna XP per un'azione e controlla achievement e livelli"""
        if action_type not in self.xp_actions:
            return {'success': False, 'error': 'Azione non riconosciuta'}

        base_xp = self.xp_actions[action_type]
        final_xp = int(base_xp * bonus_multiplier)

        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Aggiorna profilo utente
        cursor.execute('''
            UPDATE user_gamification 
            SET total_xp = total_xp + ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (final_xp, user_id))

        # Log dell'attività
        cursor.execute('''
            INSERT INTO xp_activity_log (user_id, action_type, xp_earned, bonus_multiplier, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action_type, final_xp, bonus_multiplier, description))

        # Aggiorna contatori specifici
        if action_type == 'message_sent':
            cursor.execute('UPDATE user_gamification SET total_messages = total_messages + 1 WHERE user_id = ?', (user_id,))
        elif action_type in ['ai_question', 'ai_correct_answer']:
            cursor.execute('UPDATE user_gamification SET ai_interactions = ai_interactions + 1 WHERE user_id = ?', (user_id,))
        elif action_type == 'quiz_completed':
            cursor.execute('UPDATE user_gamification SET quizzes_completed = quizzes_completed + 1 WHERE user_id = ?', (user_id,))
        elif action_type == 'help_classmate':
            cursor.execute('UPDATE user_gamification SET help_given = help_given + 1 WHERE user_id = ?', (user_id,))

        conn.commit()

        # Controlla level up
        level_up_info = self.check_level_up(user_id)
        
        # Controlla nuovi achievement
        new_achievements = self.check_new_achievements(user_id)

        conn.close()

        return {
            'success': True,
            'xp_earned': final_xp,
            'level_up': level_up_info,
            'new_achievements': new_achievements,
            'bonus_applied': bonus_multiplier > 1.0
        }

    def check_level_up(self, user_id: int) -> Dict[str, Any]:
        """Controlla se l'utente ha raggiunto un nuovo livello"""
        profile = self.get_or_create_user_profile(user_id)
        current_xp = profile['total_xp']
        current_level = profile['current_level']

        new_level = current_level
        for level, threshold in self.level_thresholds.items():
            if current_xp >= threshold:
                new_level = level

        if new_level > current_level:
            conn = sqlite3.connect('skaila.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_gamification 
                SET current_level = ? 
                WHERE user_id = ?
            ''', (new_level, user_id))
            
            conn.commit()
            conn.close()

            return {
                'leveled_up': True,
                'old_level': current_level,
                'new_level': new_level,
                'new_title': self.level_titles[new_level],
                'bonus_xp': 50 * new_level  # Bonus XP per level up
            }

        return {'leveled_up': False}

    def check_new_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """Controlla e sblocca nuovi achievement"""
        profile = self.get_or_create_user_profile(user_id)
        
        # Ottieni achievement già sbloccati
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()
        
        unlocked = cursor.execute('''
            SELECT achievement_id FROM user_achievements WHERE user_id = ?
        ''', (user_id,)).fetchall()
        unlocked_ids = [row[0] for row in unlocked]

        new_achievements = []

        # Controlla ogni achievement
        for achievement_id, achievement in self.achievements.items():
            if achievement_id not in unlocked_ids:
                if achievement['condition'](profile):
                    # Sblocca achievement
                    cursor.execute('''
                        INSERT INTO user_achievements (user_id, achievement_id, xp_earned)
                        VALUES (?, ?, ?)
                    ''', (user_id, achievement_id, achievement['xp_reward']))
                    
                    # Assegna XP bonus
                    cursor.execute('''
                        UPDATE user_gamification 
                        SET total_xp = total_xp + ? 
                        WHERE user_id = ?
                    ''', (achievement['xp_reward'], user_id))

                    new_achievements.append({
                        'id': achievement_id,
                        'name': achievement['name'],
                        'description': achievement['description'],
                        'xp_reward': achievement['xp_reward'],
                        'category': achievement['category']
                    })

        conn.commit()
        conn.close()
        return new_achievements

    def update_streak(self, user_id: int) -> Dict[str, Any]:
        """Aggiorna lo streak dell'utente"""
        profile = self.get_or_create_user_profile(user_id)
        today = datetime.now().date()
        last_activity = datetime.strptime(profile['last_activity_date'], '%Y-%m-%d').date() if profile['last_activity_date'] else None

        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        if last_activity:
            days_diff = (today - last_activity).days
            
            if days_diff == 1:
                # Streak continua
                new_streak = profile['current_streak'] + 1
                new_max_streak = max(profile['max_streak'], new_streak)
                
                cursor.execute('''
                    UPDATE user_gamification 
                    SET current_streak = ?, max_streak = ?, last_activity_date = DATE('now')
                    WHERE user_id = ?
                ''', (new_streak, new_max_streak, user_id))

                # Bonus XP per streak
                if new_streak % 7 == 0:  # Weekly streak bonus
                    self.award_xp(user_id, 'week_streak', description=f'Streak di {new_streak} giorni!')

                conn.commit()
                conn.close()
                return {'streak_updated': True, 'current_streak': new_streak, 'streak_broken': False}
                
            elif days_diff > 1:
                # Streak rotto
                cursor.execute('''
                    UPDATE user_gamification 
                    SET current_streak = 1, last_activity_date = DATE('now')
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                conn.close()
                return {'streak_updated': True, 'current_streak': 1, 'streak_broken': True}
        else:
            # Primo accesso
            cursor.execute('''
                UPDATE user_gamification 
                SET current_streak = 1, max_streak = 1, last_activity_date = DATE('now')
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
            return {'streak_updated': True, 'current_streak': 1, 'streak_broken': False}

        conn.close()
        return {'streak_updated': False}

    def get_daily_challenges(self, user_id: int) -> List[Dict[str, Any]]:
        """Ottieni le sfide giornaliere dell'utente"""
        today = datetime.now().date()
        
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Ottieni progressi delle sfide odierne
        current_progress = cursor.execute('''
            SELECT challenge_id, current_progress, completed, xp_earned
            FROM daily_challenges_progress 
            WHERE user_id = ? AND challenge_date = DATE('now')
        ''', (user_id,)).fetchall()

        progress_dict = {row[0]: {'progress': row[1], 'completed': row[2], 'xp_earned': row[3]} for row in current_progress}

        challenges = []
        for challenge in self.daily_challenges:
            challenge_data = challenge.copy()
            if challenge['id'] in progress_dict:
                challenge_data.update(progress_dict[challenge['id']])
            else:
                challenge_data.update({'progress': 0, 'completed': False, 'xp_earned': 0})
                
                # Crea record per la sfida
                cursor.execute('''
                    INSERT OR IGNORE INTO daily_challenges_progress 
                    (user_id, challenge_id, challenge_date, target_progress)
                    VALUES (?, ?, DATE('now'), ?)
                ''', (user_id, challenge['id'], challenge['target']))

            challenges.append(challenge_data)

        conn.commit()
        conn.close()
        return challenges

    def update_challenge_progress(self, user_id: int, challenge_type: str, increment: int = 1) -> Dict[str, Any]:
        """Aggiorna il progresso di una sfida giornaliera"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Trova sfide del tipo specificato
        matching_challenges = [c for c in self.daily_challenges if c['type'] == challenge_type]
        
        results = []
        for challenge in matching_challenges:
            # Aggiorna progresso
            cursor.execute('''
                UPDATE daily_challenges_progress 
                SET current_progress = current_progress + ?
                WHERE user_id = ? AND challenge_id = ? AND challenge_date = DATE('now')
            ''', (increment, user_id, challenge['id']))

            # Controlla se completata
            progress = cursor.execute('''
                SELECT current_progress, target_progress, completed
                FROM daily_challenges_progress 
                WHERE user_id = ? AND challenge_id = ? AND challenge_date = DATE('now')
            ''', (user_id, challenge['id'])).fetchone()

            if progress and progress[0] >= progress[1] and not progress[2]:
                # Sfida completata!
                cursor.execute('''
                    UPDATE daily_challenges_progress 
                    SET completed = 1, xp_earned = ?
                    WHERE user_id = ? AND challenge_id = ? AND challenge_date = DATE('now')
                ''', (challenge['xp_reward'], user_id, challenge['id']))

                # Assegna XP
                self.award_xp(user_id, 'quiz_completed', 1.0, f"Sfida completata: {challenge['name']}")

                results.append({
                    'challenge_completed': True,
                    'challenge_name': challenge['name'],
                    'xp_earned': challenge['xp_reward']
                })

        conn.commit()
        conn.close()
        return {'challenges_updated': results}

    def get_leaderboard(self, user_id: int, period: str = 'weekly', class_filter: str = None) -> Dict[str, Any]:
        """Ottieni classifica per periodo specificato"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Query base per classifica
        base_query = '''
            SELECT u.nome, u.cognome, u.classe, ug.total_xp, ug.current_level, u.id,
                   ROW_NUMBER() OVER (ORDER BY ug.total_xp DESC) as rank
            FROM user_gamification ug
            JOIN utenti u ON ug.user_id = u.id
            WHERE u.attivo = 1
        '''

        params = []

        # Filtro per classe se specificato
        if class_filter:
            base_query += ' AND u.classe = ?'
            params.append(class_filter)

        # Filtro per periodo
        if period == 'weekly':
            base_query += ' AND ug.updated_at > DATE("now", "-7 days")'
        elif period == 'monthly':
            base_query += ' AND ug.updated_at > DATE("now", "-30 days")'

        base_query += ' ORDER BY ug.total_xp DESC LIMIT 20'

        leaderboard = cursor.execute(base_query, params).fetchall()

        # Trova posizione utente corrente
        user_rank_query = '''
            SELECT COUNT(*) + 1 as user_rank
            FROM user_gamification ug2
            JOIN utenti u2 ON ug2.user_id = u2.id
            WHERE ug2.total_xp > (
                SELECT total_xp FROM user_gamification WHERE user_id = ?
            ) AND u2.attivo = 1
        '''

        if class_filter:
            user_rank_query = user_rank_query.replace('u2.attivo = 1', f'u2.attivo = 1 AND u2.classe = "{class_filter}"')

        user_rank = cursor.execute(user_rank_query, (user_id,)).fetchone()[0]

        conn.close()

        return {
            'leaderboard': [
                {
                    'rank': row[6],
                    'name': f"{row[0]} {row[1]}",
                    'class': row[2],
                    'total_xp': row[3],
                    'level': row[4],
                    'level_title': self.level_titles.get(row[4], 'Studente'),
                    'is_current_user': row[5] == user_id
                } for row in leaderboard
            ],
            'user_rank': user_rank,
            'period': period,
            'class_filter': class_filter
        }

    def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Ottieni dashboard completa gamification per l'utente"""
        profile = self.get_or_create_user_profile(user_id)
        
        # Achievement sbloccati
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()
        
        unlocked_achievements = cursor.execute('''
            SELECT ua.achievement_id, ua.unlocked_at, ua.xp_earned
            FROM user_achievements ua
            WHERE ua.user_id = ?
            ORDER BY ua.unlocked_at DESC
        ''', (user_id,)).fetchall()

        # Attività XP recente
        recent_activity = cursor.execute('''
            SELECT action_type, xp_earned, description, timestamp
            FROM xp_activity_log
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (user_id,)).fetchall()

        conn.close()

        # Calcola prossimo livello
        current_level = profile['current_level']
        next_level = current_level + 1 if current_level < 10 else 10
        current_xp = profile['total_xp']
        next_level_xp = self.level_thresholds.get(next_level, self.level_thresholds[10])
        level_progress = min(100, (current_xp / next_level_xp) * 100) if next_level_xp > 0 else 100

        return {
            'profile': {
                **profile,
                'level_title': self.level_titles[current_level],
                'next_level_xp': next_level_xp,
                'level_progress': level_progress
            },
            'achievements': {
                'unlocked': [
                    {
                        'id': row[0],
                        'name': self.achievements[row[0]]['name'],
                        'description': self.achievements[row[0]]['description'],
                        'unlocked_at': row[1],
                        'xp_earned': row[2],
                        'category': self.achievements[row[0]]['category']
                    } for row in unlocked_achievements if row[0] in self.achievements
                ],
                'available': [
                    {
                        'id': ach_id,
                        'name': ach['name'],
                        'description': ach['description'],
                        'xp_reward': ach['xp_reward'],
                        'category': ach['category'],
                        'progress': self.calculate_achievement_progress(ach_id, profile)
                    } for ach_id, ach in self.achievements.items() 
                    if ach_id not in [row[0] for row in unlocked_achievements]
                ]
            },
            'daily_challenges': self.get_daily_challenges(user_id),
            'recent_activity': [
                {
                    'action': row[0],
                    'xp_earned': row[1],
                    'description': row[2],
                    'timestamp': row[3]
                } for row in recent_activity
            ],
            'leaderboard_position': self.get_leaderboard(user_id, 'weekly'),
            'statistics': {
                'total_achievements': len(unlocked_achievements),
                'completion_rate': (len(unlocked_achievements) / len(self.achievements)) * 100,
                'daily_streak': profile['current_streak'],
                'best_streak': profile['max_streak']
            }
        }

    def calculate_achievement_progress(self, achievement_id: str, profile: Dict[str, Any]) -> float:
        """Calcola il progresso verso un achievement"""
        if achievement_id == 'social_butterfly':
            return min(100, (profile['total_messages'] / 100) * 100)
        elif achievement_id == 'ai_enthusiast':
            return min(100, (profile['ai_interactions'] / 50) * 100)
        elif achievement_id == 'week_warrior':
            return min(100, (profile['max_streak'] / 7) * 100)
        elif achievement_id == 'knowledge_seeker':
            return min(100, (profile['quizzes_completed'] / 20) * 100)
        elif achievement_id == 'helper_hero':
            return min(100, (profile['help_given'] / 10) * 100)
        elif achievement_id == 'month_legend':
            return min(100, (profile['max_streak'] / 30) * 100)
        
        return 0.0


# Istanza globale del sistema di gamification
gamification_system = SKAILAGamification()

def init_gamification():
    """Inizializza il sistema di gamification"""
    gamification_system.init_gamification_tables()
    print("🎮 Sistema di Gamification SKAILA inizializzato!")

if __name__ == "__main__":
    init_gamification()
