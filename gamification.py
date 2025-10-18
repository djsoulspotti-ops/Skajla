"""
SKAILA Gamification System - Sistema completo di gamification
Sistema avanzato di punti, livelli, achievement e classifiche per motivare gli studenti
+ SISTEMA AVATAR PERSONALIZZABILI
+ GAMIFICATION COLLABORATIVA
+ ANALYTICS AVANZATE
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random
from core.config.gamification_config import XPConfig, LevelConfig, BadgeConfig, StreakConfig

# Assume db_manager is imported and configured elsewhere, providing context manager support
# For demonstration, let's mock a db_manager that supports context managers
class MockDBManager:
    def __init__(self, db_type='sqlite'):
        self.db_type = db_type
        if db_type == 'postgresql':
            import psycopg2
            from psycopg2.extras import DictCursor
            self.psycopg2 = psycopg2
            self.DictCursor = DictCursor

    def get_connection(self):
        if self.db_type == 'postgresql':
            # Replace with your actual PostgreSQL connection details
            try:
                conn = self.psycopg2.connect(
                    dbname="your_db", user="your_user", password="your_password", host="your_host"
                )
                return conn
            except Exception as e:
                print(f"Error connecting to PostgreSQL: {e}")
                return None
        else:
            # SQLite connection (for demonstration, a real implementation would use a persistent file)
            conn = sqlite3.connect(':memory:') # Use in-memory for mock, replace with 'skaila.db' for persistence
            conn.row_factory = sqlite3.Row # Allows dictionary-like access to rows
            return conn

    def query(self, query: str, params: tuple = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith("SELECT"):
                return [dict(row) for row in cursor.fetchall()]
            else:
                conn.commit()
                return cursor.lastrowid if cursor.lastrowid else True
                
# Initialize a mock db_manager for demonstration purposes
# In a real application, this would be imported and configured properly.
db_manager = MockDBManager(db_type='sqlite') # Change to 'postgresql' if needed

class SKAILAGamification:
    def __init__(self):
        # ✅ XP da configurazione centralizzata (SSoT)
        self.xp_multipliers = XPConfig.MULTIPLIERS
        self.xp_actions = XPConfig.ACTIONS

        # Livelli e soglie XP - FORMULA MIGLIORATA
        # Level 1-10: 100 * level
        # Level 11-25: 150 * level  
        # Level 26-50: 200 * level
        # Level 51+: 300 * level
        self.level_thresholds = self._calculate_level_thresholds()

        # Inizializza titoli livelli
        self.level_titles = self._init_level_titles()

        # Inizializza tutti gli altri attributi necessari
        self._initialize_all_attributes()

    def _calculate_level_thresholds(self):
        """Calcola soglie XP con formula scalabile"""
        thresholds = {1: 0}
        total_xp = 0

        for level in range(2, 101):  # Supporta fino a livello 100
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
        """Inizializza titoli per livelli"""
        return {
            1: "🌱 Novizio SKAILA", 2: "📚 Apprendista", 3: "🎓 Studente Attivo", 4: "⭐ Studioso Dedicato", 5: "🏆 Esperto Learner",
            6: "👑 Maestro del Sapere", 7: "🧠 Genio Accademico", 8: "🚀 Leggenda di SKAILA", 9: "💎 Prodigio Supremo", 10: "🌟 SKAILA Master",
            11: "🔥 Elite Scholar", 12: "⚡ Knowledge Lightning", 13: "🎯 Precision Learner", 14: "🌊 Wave Rider", 15: "🔮 Mystic Mind",
            16: "🗡️ Knowledge Warrior", 17: "🏔️ Peak Performer", 18: "🌪️ Study Storm", 19: "🏆 Grand Champion", 20: "👑 Royal Master",
            21: "🌌 Cosmic Scholar", 22: "🔱 Knowledge Titan", 23: "🌟 Stellar Achiever", 24: "⚔️ Academic Gladiator", 25: "🏰 Knowledge Emperor",
            26: "🌠 Shooting Star", 27: "🌋 Eruption Force", 28: "🌈 Spectrum Master", 29: "🎆 Firework Genius", 30: "👑 Elite Emperor",
            31: "🌍 World Shaker", 32: "🌙 Lunar Legend", 33: "☀️ Solar Scholar", 34: "⭐ Star Commander", 35: "🌌 Galaxy Guardian",
            36: "🔥 Phoenix Rising", 37: "🌊 Tsunami Force", 38: "⚡ Thunder Master", 39: "🌪️ Hurricane Hero", 40: "🌋 Volcano Lord",
            41: "🎭 Mythical Mind", 42: "🗿 Ancient Wisdom", 43: "🔮 Oracle of Knowledge", 44: "👑 Supreme Overlord", 45: "🌟 Transcendent",
            46: "🚀 Space Explorer", 47: "🌌 Universe Walker", 48: "⚡ Energy Master", 49: "🌠 Comet Chaser", 50: "🌟 SKAILA LEGEND"
        }

    def _initialize_all_attributes(self):
        """Inizializza tutti gli attributi del sistema gamification"""

        # Rewards per livello specifici
        self.level_rewards = {
            5: {"unlock": "avatar_customization", "description": "🎨 Sblocca personalizzazione avatar!", "bonus_coins": 100},
            10: {"unlock": "study_groups", "description": "👥 Sblocca creazione gruppi di studio!", "bonus_coins": 200},
            15: {"unlock": "advanced_analytics", "description": "📊 Sblocca analytics avanzate!", "bonus_coins": 300},
            20: {"unlock": "mentor_mode", "description": "👨‍🏫 Sblocca modalità mentore!", "bonus_coins": 500},
            25: {"unlock": "course_creation", "description": "🎯 Sblocca strumenti creazione corsi!", "bonus_coins": 750},
            30: {"unlock": "elite_status", "description": "👑 Status Elite + Contenuti esclusivi!", "bonus_coins": 1000},
            35: {"unlock": "ai_tutor_advanced", "description": "🤖 AI Tutor Avanzato personalizzato!", "bonus_coins": 1500},
            40: {"unlock": "global_challenges", "description": "🌍 Accesso sfide globali SKAILA!", "bonus_coins": 2000},
            45: {"unlock": "knowledge_oracle", "description": "🔮 Diventa Oracolo della Conoscenza!", "bonus_coins": 3000},
            50: {"unlock": "legend_status", "description": "🌟 Status LEGGENDA SKAILA!", "bonus_coins": 5000}
        }

        # 🎨 SISTEMA AVATAR E RICOMPENSE VISIVE
        self.available_avatars = {
            # Avatar base (gratuiti)
            'default': {'emoji': '👤', 'name': 'Default', 'unlock_level': 1, 'cost': 0},
            'student': {'emoji': '🎓', 'name': 'Studente', 'unlock_level': 2, 'cost': 0},
            'book_lover': {'emoji': '📚', 'name': 'Amante dei Libri', 'unlock_level': 3, 'cost': 0},
            # Avatar premium (sbloccabili con livelli)
            'genius': {'emoji': '🧠', 'name': 'Genio', 'unlock_level': 5, 'cost': 500},
            'rocket': {'emoji': '🚀', 'name': 'Razzo', 'unlock_level': 6, 'cost': 750},
            'crown': {'emoji': '👑', 'name': 'Corona Reale', 'unlock_level': 7, 'cost': 1000},
            'diamond': {'emoji': '💎', 'name': 'Diamante', 'unlock_level': 8, 'cost': 1500},
            'star': {'emoji': '⭐', 'name': 'Stella Dorata', 'unlock_level': 9, 'cost': 2000},
            'master': {'emoji': '🌟', 'name': 'SKAILA Master', 'unlock_level': 10, 'cost': 3000},
            # Avatar speciali (achievement-based)
            'fire': {'emoji': '🔥', 'name': 'Streak Master', 'unlock_achievement': 'week_warrior', 'cost': 0},
            'lightning': {'emoji': '⚡', 'name': 'Speed Learner', 'unlock_achievement': 'ai_enthusiast', 'cost': 0},
            'trophy': {'emoji': '🏆', 'name': 'Campione', 'unlock_achievement': 'month_legend', 'cost': 0}
        }

        self.ui_themes = {
            'default': {'name': 'SKAILA Default', 'unlock_level': 1, 'cost': 0},
            'dark_mode': {'name': 'Modalità Scura', 'unlock_level': 3, 'cost': 200},
            'neon': {'name': 'Neon Futuristico', 'unlock_level': 5, 'cost': 500},
            'royal': {'name': 'Eleganza Reale', 'unlock_level': 7, 'cost': 1000},
            'master': {'name': 'SKAILA Master Theme', 'unlock_level': 10, 'cost': 2500}
        }

        # 🤝 SFIDE COLLABORATIVE
        self.team_challenges = [
            {
                'id': 'class_knowledge_rush',
                'name': '🧠 Corsa della Conoscenza',
                'description': 'Primo team a completare 50 quiz vince!',
                'type': 'race',
                'target': 50,
                'duration_hours': 48,
                'reward_winner': 300,
                'reward_participant': 100
            },
            {
                'id': 'inter_class_debate',
                'name': '🗣️ Sfida Dibattito',
                'description': 'Dibattito tra classi su tema scientifico',
                'type': 'competition',
                'target': 1,
                'duration_hours': 72,
                'reward_winner': 500,
                'reward_participant': 200
            },
            {
                'id': 'collaborative_study',
                'name': '📚 Studio Collaborativo',
                'description': 'Aiutatevi a studiare per 100 ore totali',
                'type': 'cooperative',
                'target': 100,
                'duration_hours': 168,
                'reward_winner': 400,
                'reward_participant': 150
            },
            {
                'id': 'weekend_warriors',
                'name': '⚔️ Guerrieri del Weekend',
                'description': 'Maggior numero di attività nel weekend',
                'type': 'weekend_special',
                'target': 20,
                'duration_hours': 48,
                'reward_winner': 250,
                'reward_participant': 75
            }
        ]

        # 🏆 SISTEMA BADGE COMPLETO
        self.badge_system = {
            # 🎯 Performance Badges
            'perfect_score_10': {
                'name': '🎯 Perfect Score Master',
                'description': '10 quiz con punteggio perfetto',
                'category': 'performance',
                'condition': lambda stats: stats.get('perfect_quizzes', 0) >= 10,
                'xp_reward': 500,
                'badge_icon': '🎯',
                'rarity': 'rare'
            },
            'speed_learner': {
                'name': '⚡ Speed Learner',
                'description': 'Completa 5 lezioni in tempo record',
                'category': 'performance',
                'condition': lambda stats: stats.get('speed_completions', 0) >= 5,
                'xp_reward': 300,
                'badge_icon': '⚡',
                'rarity': 'uncommon'
            },
            'consistency_king': {
                'name': '👑 Consistency King',
                'description': '30 giorni di studio consecutivi',
                'category': 'performance',
                'condition': lambda stats: stats.get('max_streak', 0) >= 30,
                'xp_reward': 1000,
                'badge_icon': '👑',
                'rarity': 'epic'
            },
            'knowledge_master': {
                'name': '🧠 Knowledge Master',
                'description': 'Supera tutti i test di un corso',
                'category': 'performance',
                'condition': lambda stats: stats.get('courses_mastered', 0) >= 1,
                'xp_reward': 750,
                'badge_icon': '🧠',
                'rarity': 'rare'
            },

            # 🤝 Social Badges
            'helper_badge': {
                'name': '🤝 Helper',
                'description': 'Aiuta 50 studenti',
                'category': 'social',
                'condition': lambda stats: stats.get('help_given', 0) >= 50,
                'xp_reward': 600,
                'badge_icon': '🤝',
                'rarity': 'rare'
            },
            'popular_teacher': {
                'name': '⭐ Popular Teacher',
                'description': 'Ricevi 100 likes su risposte',
                'category': 'social',
                'condition': lambda stats: stats.get('likes_received', 0) >= 100,
                'xp_reward': 800,
                'badge_icon': '⭐',
                'rarity': 'epic'
            },
            'community_leader': {
                'name': '🏛️ Community Leader',
                'description': 'Modera 20 discussioni',
                'category': 'social',
                'condition': lambda stats: stats.get('discussions_moderated', 0) >= 20,
                'xp_reward': 900,
                'badge_icon': '🏛️',
                'rarity': 'epic'
            },
            'mentor_badge': {
                'name': '👨‍🏫 Mentor',
                'description': 'Guida 10 studenti junior',
                'category': 'social',
                'condition': lambda stats: stats.get('mentorship_sessions', 0) >= 10,
                'xp_reward': 1200,
                'badge_icon': '👨‍🏫',
                'rarity': 'legendary'
            },

            # 🔥 Challenge Badges
            'early_bird': {
                'name': '🌅 Early Bird',
                'description': 'Studia prima delle 8:00 per 7 giorni',
                'category': 'challenge',
                'condition': lambda stats: stats.get('early_morning_sessions', 0) >= 7,
                'xp_reward': 400,
                'badge_icon': '🌅',
                'rarity': 'uncommon'
            },
            'night_owl': {
                'name': '🦉 Night Owl',
                'description': 'Studia dopo le 22:00 per 7 giorni',
                'category': 'challenge',
                'condition': lambda stats: stats.get('late_night_sessions', 0) >= 7,
                'xp_reward': 400,
                'badge_icon': '🦉',
                'rarity': 'uncommon'
            },
            'weekend_warrior': {
                'name': '⚔️ Weekend Warrior',
                'description': 'Completa sfide weekend per 4 settimane',
                'category': 'challenge',
                'condition': lambda stats: stats.get('weekend_challenges_completed', 0) >= 4,
                'xp_reward': 600,
                'badge_icon': '⚔️',
                'rarity': 'rare'
            },
            'marathon_runner': {
                'name': '🏃‍♂️ Marathon Runner',
                'description': '6+ ore di studio in un giorno',
                'category': 'challenge',
                'condition': lambda stats: stats.get('longest_study_session', 0) >= 360,
                'xp_reward': 500,
                'badge_icon': '🏃‍♂️',
                'rarity': 'rare'
            },

            # ⭐ Special Badges
            'first_steps': {
                'name': '🌱 First Steps',
                'description': 'Prima lezione completata',
                'category': 'special',
                'condition': lambda stats: stats.get('lessons_completed', 0) >= 1,
                'xp_reward': 50,
                'badge_icon': '🌱',
                'rarity': 'common'
            },
            'veteran': {
                'name': '🎖️ Veteran',
                'description': '1 anno sulla piattaforma',
                'category': 'special',
                'condition': lambda stats: stats.get('days_on_platform', 0) >= 365,
                'xp_reward': 2000,
                'badge_icon': '🎖️',
                'rarity': 'legendary'
            },
            'explorer': {
                'name': '🗺️ Explorer',
                'description': 'Esplora tutti i corsi disponibili',
                'category': 'special',
                'condition': lambda stats: stats.get('courses_explored', 0) >= stats.get('total_courses_available', 10),
                'xp_reward': 1500,
                'badge_icon': '🗺️',
                'rarity': 'epic'
            },
            'innovator': {
                'name': '💡 Innovator',
                'description': 'Suggerisci feature implementata',
                'category': 'special',
                'condition': lambda stats: stats.get('features_suggested_implemented', 0) >= 1,
                'xp_reward': 3000,
                'badge_icon': '💡',
                'rarity': 'legendary'
            }
        }

        # 🔥 SISTEMA STREAK AVANZATO
        self.streak_system = {
            'daily_bonuses': {
                3: {'xp_multiplier': 1.2, 'description': '+20% XP bonus'},
                7: {'xp_multiplier': 1.35, 'description': '+35% XP bonus'},
                14: {'xp_multiplier': 1.5, 'description': '+50% XP bonus'},
                30: {'xp_multiplier': 1.75, 'description': '+75% XP bonus + Badge speciale', 'special_badge': 'streak_master_30'},
                100: {'xp_multiplier': 2.0, 'description': 'Status Legend + Rewards esclusivi', 'special_status': 'legend'}
            },
            'protection_items': {
                'freeze_card': {
                    'name': '❄️ Freeze Card',
                    'description': '1 giorno gratis al mese',
                    'monthly_limit': 1,
                    'cost_coins': 0
                },
                'weekend_pass': {
                    'name': '🎫 Weekend Pass',
                    'description': 'Weekend non rompe streak',
                    'duration_days': 7,
                    'cost_coins': 500
                }
            },
            'streak_milestones': {
                7: {'reward': 'badge', 'badge_id': 'week_warrior', 'bonus_coins': 100},
                30: {'reward': 'badge', 'badge_id': 'streak_master_30', 'bonus_coins': 500},
                60: {'reward': 'special_avatar', 'avatar_id': 'streak_master', 'bonus_coins': 1000},
                100: {'reward': 'legend_status', 'status': 'legend', 'bonus_coins': 2500},
                365: {'reward': 'immortal_status', 'status': 'immortal', 'bonus_coins': 10000}
            }
        }

        # Achievement dinamici (estesi)
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
            },
            # NUOVI ACHIEVEMENT COLLABORATIVI
            'team_player': {
                'name': '🤝 Team Player',
                'description': 'Partecipa a 5 sfide di squadra',
                'xp_reward': 350,
                'condition': lambda stats: stats.get('team_challenges_participated', 0) >= 5,
                'category': 'collaborazione'
            },
            'class_champion': {
                'name': '🏅 Campione della Classe',
                'description': 'Vinci 3 sfide inter-classe',
                'xp_reward': 600,
                'condition': lambda stats: stats.get('team_challenges_won', 0) >= 3,
                'category': 'leadership'
            },
            'mentor_master': {
                'name': '👨‍🏫 Mentore Master',
                'description': 'Conduci 10 sessioni di tutoraggio',
                'xp_reward': 800,
                'condition': lambda stats: stats.get('mentorship_sessions', 0) >= 10,
                'category': 'leadership'
            }
        }

        # Sfide giornaliere (estese)
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
            },
            {
                'id': 'team_helper',
                'name': '🤝 Aiuto Squadra',
                'description': 'Aiuta 2 compagni oggi',
                'target': 2,
                'xp_reward': 120,
                'type': 'team_help'
            }
        ]

        # Sistema multiplier XP dinamico
        self.xp_multipliers = {
            'base': 1.0,
            'streak_7_days': 1.2,
            'streak_14_days': 1.4,
            'streak_30_days': 1.6,
            'streak_60_days': 1.8,
            'streak_100_days': 2.0,
            'perfect_week': 1.5,
            'weekend_warrior': 1.3,
            'early_bird': 1.2,
            'night_owl': 1.2,
            'combo_master': 2.0,
            'team_synergy': 1.8,
            'mentor_bonus': 1.4,
            'elite_status': 1.25
        }

        # Premi speciali con condizioni
        self.special_rewards = {
            'weekend_warrior': {
                'name': '⚡ Weekend Warrior', 
                'bonus_xp': 1.3,
                'condition': 'weekend_activity',
                'description': 'Attivo nel weekend!'
            },
            'early_bird': {
                'name': '🌅 Early Bird', 
                'bonus_xp': 1.2,
                'condition': 'morning_activity',
                'description': 'Prima delle 8:00!'
            },
            'night_owl': {
                'name': '🦉 Night Owl', 
                'bonus_xp': 1.2,
                'condition': 'night_activity',
                'description': 'Dopo le 22:00!'
            },
            'combo_master': {
                'name': '🔥 Combo Master', 
                'bonus_xp': 2.0,
                'condition': 'activity_combo',
                'description': '5+ azioni in 30 minuti!'
            },
            'team_synergy': {
                'name': '🤝 Team Synergy', 
                'bonus_xp': 1.8,
                'condition': 'team_participation',
                'description': 'Collaborazione attiva!'
            },
            'perfect_streak': {
                'name': '🎯 Perfect Streak', 
                'bonus_xp': 1.5,
                'condition': 'daily_goals_met',
                'description': 'Obiettivi giornalieri raggiunti!'
            }
        }

    def init_gamification_tables(self):
        """Inizializza le tabelle per il sistema di gamification completo"""
        conn = sqlite3.connect('skaila.db') # Using SQLite for initialization example
        cursor = conn.cursor()

        # Tabella profili gamification utenti (estesa)
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
                team_challenges_participated INTEGER DEFAULT 0,
                team_challenges_won INTEGER DEFAULT 0,
                mentorship_sessions INTEGER DEFAULT 0,
                current_avatar TEXT DEFAULT 'default',
                current_theme TEXT DEFAULT 'default',
                avatar_coins INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        # Tabella avatar e temi sbloccati
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_unlocked_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_type TEXT, -- 'avatar' o 'theme'
                item_id TEXT,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unlock_method TEXT, -- 'level', 'purchase', 'achievement'
                FOREIGN KEY (user_id) REFERENCES utenti (id),
                UNIQUE(user_id, item_type, item_id)
            )
        ''')

        # Tabella sfide collaborative
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id TEXT,
                challenge_name TEXT,
                class_a TEXT,
                class_b TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active', -- 'active', 'completed', 'cancelled'
                winner_class TEXT,
                class_a_progress INTEGER DEFAULT 0,
                class_b_progress INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabella partecipazioni sfide team
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_challenge_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER,
                user_id INTEGER,
                contribution INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (challenge_id) REFERENCES team_challenges (id),
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        # Tabella analytics giornaliere
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                daily_xp_earned INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,
                ai_questions INTEGER DEFAULT 0,
                quiz_completed INTEGER DEFAULT 0,
                study_minutes INTEGER DEFAULT 0,
                help_given INTEGER DEFAULT 0,
                login_time TIME,
                total_session_time INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES utenti (id),
                UNIQUE(user_id, date)
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

        # Tabella badge utenti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                badge_id TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                xp_earned INTEGER DEFAULT 0,
                rarity TEXT,
                FOREIGN KEY (user_id) REFERENCES utenti (id),
                UNIQUE(user_id, badge_id)
            )
        ''')

        # Tabella protezioni streak
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streak_protections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                protection_type TEXT, -- 'freeze_card', 'weekend_pass'
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        # Tabella statistiche avanzate per badge
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_advanced_stats (
                user_id INTEGER PRIMARY KEY,
                perfect_quizzes INTEGER DEFAULT 0,
                speed_completions INTEGER DEFAULT 0,
                courses_mastered INTEGER DEFAULT 0,
                likes_received INTEGER DEFAULT 0,
                discussions_moderated INTEGER DEFAULT 0,
                early_morning_sessions INTEGER DEFAULT 0,
                late_night_sessions INTEGER DEFAULT 0,
                weekend_challenges_completed INTEGER DEFAULT 0,
                longest_study_session INTEGER DEFAULT 0,
                lessons_completed INTEGER DEFAULT 0,
                days_on_platform INTEGER DEFAULT 0,
                courses_explored INTEGER DEFAULT 0,
                features_suggested_implemented INTEGER DEFAULT 0,
                total_courses_available INTEGER DEFAULT 10,
                freeze_cards_used_this_month INTEGER DEFAULT 0,
                weekend_passes_active INTEGER DEFAULT 0,
                last_freeze_card_reset DATE DEFAULT (DATE('now', 'start of month')),
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Tabelle gamification complete create con successo!")

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
                INSERT INTO user_gamification (user_id, last_activity_date, avatar_coins)
                VALUES (?, DATE('now'), 100)
            ''', (user_id,))

            # Sblocca avatar e tema default
            cursor.execute('''
                INSERT OR IGNORE INTO user_unlocked_items (user_id, item_type, item_id, unlock_method)
                VALUES (?, 'avatar', 'default', 'level'), (?, 'theme', 'default', 'level')
            ''', (user_id, user_id))

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
                'study_minutes': profile[10],
                'team_challenges_participated': profile[11],
                'team_challenges_won': profile[12],
                'mentorship_sessions': profile[13],
                'current_avatar': profile[14],
                'current_theme': profile[15],
                'avatar_coins': profile[16]
            }
        return {}

    # 🎨 FUNZIONI SISTEMA AVATAR E RICOMPENSE VISIVE

    def get_available_avatars(self, user_id: int) -> Dict[str, Any]:
        """Ottieni avatar disponibili per l'utente"""
        profile = self.get_or_create_user_profile(user_id)
        user_level = profile['current_level']

        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Ottieni achievement sbloccati
        unlocked_achievements = cursor.execute('''
            SELECT achievement_id FROM user_achievements WHERE user_id = ?
        ''', (user_id,)).fetchall()
        achievement_ids = [row[0] for row in unlocked_achievements]

        # Ottieni avatar già sbloccati
        unlocked_items = cursor.execute('''
            SELECT item_id FROM user_unlocked_items 
            WHERE user_id = ? AND item_type = 'avatar'
        ''', (user_id,)).fetchall()
        unlocked_avatar_ids = [row[0] for row in unlocked_items]

        conn.close()

        avatar_status = {}
        for avatar_id, avatar_data in self.available_avatars.items():
            can_unlock = False
            unlock_reason = ""

            if avatar_id in unlocked_avatar_ids:
                can_unlock = True
                unlock_reason = "Posseduto"
            elif 'unlock_level' in avatar_data and user_level >= avatar_data['unlock_level']:
                can_unlock = True
                unlock_reason = f"Livello {avatar_data['unlock_level']} raggiunto"
            elif 'unlock_achievement' in avatar_data and avatar_data['unlock_achievement'] in achievement_ids:
                can_unlock = True
                unlock_reason = f"Achievement sbloccato"
            elif 'cost' in avatar_data and profile['avatar_coins'] >= avatar_data['cost']:
                unlock_reason = f"Acquistabile per {avatar_data['cost']} monete"
            else:
                unlock_reason = f"Richiede livello {avatar_data.get('unlock_level', '?')} o achievement"

            avatar_status[avatar_id] = {
                **avatar_data,
                'unlocked': avatar_id in unlocked_avatar_ids,
                'can_unlock': can_unlock,
                'unlock_reason': unlock_reason
            }

        return avatar_status

    def purchase_avatar(self, user_id: int, avatar_id: str) -> Dict[str, Any]:
        """Acquista un avatar con le monete"""
        if avatar_id not in self.available_avatars:
            return {'success': False, 'error': 'Avatar non trovato'}

        profile = self.get_or_create_user_profile(user_id)
        avatar_data = self.available_avatars[avatar_id]
        cost = avatar_data.get('cost', 0)

        if profile['avatar_coins'] < cost:
            return {'success': False, 'error': 'Monete insufficienti'}

        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Controlla se già posseduto
        existing = cursor.execute('''
            SELECT id FROM user_unlocked_items 
            WHERE user_id = ? AND item_type = 'avatar' AND item_id = ?
        ''', (user_id, avatar_id)).fetchone()

        if existing:
            conn.close()
            return {'success': False, 'error': 'Avatar già posseduto'}

        # Acquista avatar
        cursor.execute('''
            INSERT INTO user_unlocked_items (user_id, item_type, item_id, unlock_method)
            VALUES (?, 'avatar', ?, 'purchase')
        ''', (user_id, avatar_id))

        # Sottrai monete
        cursor.execute('''
            UPDATE user_gamification 
            SET avatar_coins = avatar_coins - ?
            WHERE user_id = ?
        ''', (cost, user_id))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'message': f'Avatar {avatar_data["name"]} acquistato!',
            'remaining_coins': profile['avatar_coins'] - cost
        }

    def change_avatar(self, user_id: int, avatar_id: str) -> Dict[str, Any]:
        """Cambia avatar dell'utente"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Verifica possesso
        unlocked = cursor.execute('''
            SELECT id FROM user_unlocked_items 
            WHERE user_id = ? AND item_type = 'avatar' AND item_id = ?
        ''', (user_id, avatar_id)).fetchone()

        if not unlocked:
            conn.close()
            return {'success': False, 'error': 'Avatar non posseduto'}

        # Cambia avatar
        cursor.execute('''
            UPDATE user_gamification 
            SET current_avatar = ?
            WHERE user_id = ?
        ''', (avatar_id, user_id))

        conn.commit()
        conn.close()

        avatar_data = self.available_avatars[avatar_id]
        return {
            'success': True,
            'message': f'Avatar cambiato in {avatar_data["name"]}!',
            'new_avatar': avatar_data
        }

    # 🤝 FUNZIONI GAMIFICATION COLLABORATIVA

    def create_team_challenge(self, challenge_type: str, class_a: str, class_b: str) -> Dict[str, Any]:
        """Crea una nuova sfida tra squadre/classi"""
        challenge_template = next((c for c in self.team_challenges if c['id'] == challenge_type), None)
        if not challenge_template:
            return {'success': False, 'error': 'Tipo sfida non valido'}

        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Calcola date di inizio e fine
        start_date = datetime.now()
        end_date = start_date + timedelta(hours=challenge_template['duration_hours'])

        # Crea sfida
        cursor.execute('''
            INSERT INTO team_challenges 
            (challenge_id, challenge_name, class_a, class_b, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (challenge_type, challenge_template['name'], class_a, class_b, start_date, end_date))

        challenge_db_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            'success': True,
            'challenge_id': challenge_db_id,
            'message': f'Sfida {challenge_template["name"]} creata tra {class_a} e {class_b}!',
            'end_date': end_date.isoformat()
        }

    def join_team_challenge(self, user_id: int, challenge_id: int) -> Dict[str, Any]:
        """Unisciti a una sfida di squadra"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Verifica esistenza sfida
        challenge = cursor.execute('''
            SELECT * FROM team_challenges WHERE id = ? AND status = 'active'
        ''', (challenge_id,)).fetchone()

        if not challenge:
            conn.close()
            return {'success': False, 'error': 'Sfida non trovata o non attiva'}

        # Verifica se utente appartiene a una delle classi
        user_class = cursor.execute('''
            SELECT classe FROM utenti WHERE id = ?
        ''', (user_id,)).fetchone()[0]

        if user_class not in [challenge[3], challenge[4]]:  # class_a, class_b
            conn.close()
            return {'success': False, 'error': 'Non appartienti alle classi partecipanti'}

        # Unisciti alla sfida
        cursor.execute('''
            INSERT OR IGNORE INTO team_challenge_participants (challenge_id, user_id)
            VALUES (?, ?)
        ''', (challenge_id, user_id))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'message': f'Ti sei unito alla sfida {challenge[2]}!'
        }

    def update_team_challenge_progress(self, user_id: int, challenge_id: int, contribution: int = 1) -> Dict[str, Any]:
        """Aggiorna il progresso di una sfida di squadra"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Aggiorna contributo utente
        cursor.execute('''
            UPDATE team_challenge_participants 
            SET contribution = contribution + ?
            WHERE challenge_id = ? AND user_id = ?
        ''', (contribution, challenge_id, user_id))

        # Ottieni classe utente
        user_class = cursor.execute('''
            SELECT classe FROM utenti WHERE id = ?
        ''', (user_id,)).fetchone()[0]

        # Aggiorna progresso classe
        if user_class:
            cursor.execute('''
                UPDATE team_challenges 
                SET class_a_progress = class_a_progress + ?
                WHERE id = ? AND class_a = ?
            ''', (contribution, challenge_id, user_class))

            cursor.execute('''
                UPDATE team_challenges 
                SET class_b_progress = class_b_progress + ?
                WHERE id = ? AND class_b = ?
            ''', (contribution, challenge_id, user_class))

        # Verifica se sfida completata
        challenge = cursor.execute('''
            SELECT * FROM team_challenges WHERE id = ?
        ''', (challenge_id,)).fetchone()

        challenge_template = next((c for c in self.team_challenges if c['id'] == challenge[1]), None)
        if challenge_template:
            target = challenge_template['target']

            # Controlla vincitore
            if challenge[6] >= target or challenge[7] >= target:  # class_a_progress, class_b_progress
                winner = challenge[3] if challenge[6] >= target else challenge[4]
                cursor.execute('''
                    UPDATE team_challenges 
                    SET status = 'completed', winner_class = ?
                    WHERE id = ?
                ''', (winner, challenge_id))

                # Assegna ricompense
                self.distribute_team_challenge_rewards(challenge_id, winner)

        conn.commit()
        conn.close()

        return {'success': True, 'contribution_added': contribution}

    def distribute_team_challenge_rewards(self, challenge_id: int, winner_class: str):
        """Distribuisci ricompense per sfida di squadra completata"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Ottieni partecipanti
        participants = cursor.execute('''
            SELECT tcp.user_id, u.classe, tcp.contribution
            FROM team_challenge_participants tcp
            JOIN utenti u ON tcp.user_id = u.id
            WHERE tcp.challenge_id = ?
        ''', (challenge_id,)).fetchall()

        challenge = cursor.execute('''
            SELECT challenge_id FROM team_challenges WHERE id = ?
        ''', (challenge_id,)).fetchone()

        challenge_template = next((c for c in self.team_challenges if c['id'] == challenge[0]), None)

        if challenge_template:
            for user_id, user_class, contribution in participants:
                if user_class == winner_class:
                    # Vincitori
                    xp_reward = challenge_template['reward_winner']
                    self.award_xp(user_id, 'team_challenge_completed', 1.0, f"Vittoria sfida: {challenge_template['name']}")
                    cursor.execute('''
                        UPDATE user_gamification 
                        SET team_challenges_won = team_challenges_won + 1
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    # Partecipanti
                    xp_reward = challenge_template['reward_participant']
                    self.award_xp(user_id, 'team_challenge_contributed', 1.0, f"Partecipazione sfida: {challenge_template['name']}")

                # Aggiorna contatore partecipazioni
                cursor.execute('''
                    UPDATE user_gamification 
                    SET team_challenges_participated = team_challenges_participated + 1
                    WHERE user_id = ?
                ''', (user_id,))

        conn.commit()
        conn.close()

    def get_active_team_challenges(self, user_class: str = None) -> List[Dict[str, Any]]:
        """Ottieni sfide di squadra attive"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        query = '''
            SELECT * FROM team_challenges 
            WHERE status = 'active' AND end_date > CURRENT_TIMESTAMP
        '''
        params = []

        if user_class:
            query += ' AND (class_a = ? OR class_b = ?)'
            params.extend([user_class, user_class])

        challenges = cursor.execute(query, params).fetchall()
        conn.close()

        result = []
        for challenge in challenges:
            challenge_template = next((c for c in self.team_challenges if c['id'] == challenge[1]), None)
            if challenge_template:
                result.append({
                    'id': challenge[0],
                    'name': challenge[2],
                    'class_a': challenge[3],
                    'class_b': challenge[4],
                    'progress_a': challenge[6],
                    'progress_b': challenge[7],
                    'target': challenge_template['target'],
                    'end_date': challenge[5],
                    'reward_winner': challenge_template['reward_winner'],
                    'reward_participant': challenge_template['reward_participant']
                })

        return result

    # 📈 FUNZIONI ANALYTICS AVANZATE

    def record_daily_activity(self, user_id: int, activity_type: str, value: int = 1):
        """Registra attività giornaliera per analytics"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        today = datetime.now().date()

        # Crea record giornaliero se non esiste
        cursor.execute('''
            INSERT OR IGNORE INTO daily_analytics (user_id, date)
            VALUES (?, ?)
        ''', (user_id, today))

        # Aggiorna attività specifica
        if activity_type == 'message_sent':
            cursor.execute('''
                UPDATE daily_analytics 
                SET messages_sent = messages_sent + ?
                WHERE user_id = ? AND date = ?
            ''', (value, user_id, today))
        elif activity_type == 'ai_question':
            cursor.execute('''
                UPDATE daily_analytics 
                SET ai_questions = ai_questions + ?
                WHERE user_id = ? AND date = ?
            ''', (value, user_id, today))
        elif activity_type == 'quiz_completed':
            cursor.execute('''
                UPDATE daily_analytics 
                SET quiz_completed = quiz_completed + ?
                WHERE user_id = ? AND date = ?
            ''', (value, user_id, today))
        elif activity_type == 'study_minutes':
            cursor.execute('''
                UPDATE daily_analytics 
                SET study_minutes = study_minutes + ?
                WHERE user_id = ? AND date = ?
            ''', (value, user_id, today))
        elif activity_type == 'help_given':
            cursor.execute('''
                UPDATE daily_analytics 
                SET help_given = help_given + ?
                WHERE user_id = ? AND date = ?
            ''', (value, user_id, today))

        conn.commit()
        conn.close()

    def get_user_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Ottieni analytics dettagliate dell'utente"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Analytics giornaliere recenti
        daily_data = cursor.execute('''
            SELECT date, daily_xp_earned, messages_sent, ai_questions, 
                   quiz_completed, study_minutes, help_given
            FROM daily_analytics 
            WHERE user_id = ? AND date > DATE('now', '-{} days')
            ORDER BY date ASC
        '''.format(days), (user_id,)).fetchall()

        # Statistiche aggregate
        totals = cursor.execute('''
            SELECT 
                SUM(daily_xp_earned) as total_xp_period,
                SUM(messages_sent) as total_messages_period,
                SUM(ai_questions) as total_ai_questions_period,
                SUM(quiz_completed) as total_quiz_period,
                SUM(study_minutes) as total_study_minutes_period,
                SUM(help_given) as total_help_period,
                AVG(daily_xp_earned) as avg_daily_xp,
                COUNT(*) as active_days
            FROM daily_analytics 
            WHERE user_id = ? AND date > DATE('now', '-{} days')
        '''.format(days), (user_id,)).fetchone()

        # Trend settimanali
        weekly_trends = cursor.execute('''
            SELECT 
                strftime('%W', date) as week,
                SUM(daily_xp_earned) as week_xp,
                SUM(messages_sent) as week_messages,
                SUM(ai_questions) as week_ai_questions
            FROM daily_analytics 
            WHERE user_id = ? AND date > DATE('now', '-{} days')
            GROUP BY strftime('%W', date)
            ORDER BY week ASC
        '''.format(days), (user_id,)).fetchall()

        # Orari di attività preferiti
        activity_patterns = cursor.execute('''
            SELECT 
                strftime('%H', login_time) as hour,
                COUNT(*) as login_frequency
            FROM daily_analytics 
            WHERE user_id = ? AND login_time IS NOT NULL
                AND date > DATE('now', '-{} days')
            GROUP BY hour
            ORDER BY login_frequency DESC
        '''.format(days), (user_id,)).fetchall()

        conn.close()

        # Processa dati per grafici
        daily_chart_data = []
        for row in daily_data:
            daily_chart_data.append({
                'date': row[0],
                'xp_earned': row[1],
                'messages': row[2],
                'ai_questions': row[3],
                'quiz_completed': row[4],
                'study_minutes': row[5],
                'help_given': row[6]
            })

        weekly_chart_data = []
        for row in weekly_trends:
            weekly_chart_data.append({
                'week': row[0],
                'total_xp': row[1],
                'total_messages': row[2],
                'total_ai_questions': row[3]
            })

        activity_heatmap = {}
        for row in activity_patterns:
            activity_heatmap[int(row[0])] = row[1]

        return {
            'period_days': days,
            'daily_data': daily_chart_data,
            'weekly_trends': weekly_chart_data,
            'activity_heatmap': activity_heatmap,
            'summary_stats': {
                'total_xp_earned': totals[0] or 0,
                'total_messages': totals[1] or 0,
                'total_ai_questions': totals[2] or 0,
                'total_quiz_completed': totals[3] or 0,
                'total_study_minutes': totals[4] or 0,
                'total_help_given': totals[5] or 0,
                'avg_daily_xp': round(totals[6] or 0, 1),
                'active_days': totals[7] or 0,
                'consistency_score': round(((totals[7] or 0) / days) * 100, 1)
            },
            'insights': self.generate_analytics_insights(daily_chart_data, totals)
        }

    def generate_analytics_insights(self, daily_data: List[Dict], totals: tuple) -> List[str]:
        """Genera insights personalizzati dai dati analytics"""
        insights = []

        if not daily_data:
            return ["Non ci sono abbastanza dati per generare insights."]

        # Analisi streak
        current_streak = 0
        for day in reversed(daily_data):
            if day['xp_earned'] > 0:
                current_streak += 1
            else:
                break

        if current_streak >= 7:
            insights.append(f"🔥 Sei in una striscia fantastica di {current_streak} giorni attivi!")
        elif current_streak >= 3:
            insights.append(f"💪 Bella consistenza: {current_streak} giorni di fila attivo!")

        # Analisi produttività
        avg_daily_xp = totals[6] or 0
        if avg_daily_xp > 100:
            insights.append("🚀 Sei un super learner con una media XP alta!")
        elif avg_daily_xp > 50:
            insights.append("📈 Ottima progressione, continua così!")

        # Analisi attività preferite
        total_messages = totals[1] or 0
        total_ai_questions = totals[2] or 0

        if total_ai_questions > total_messages:
            insights.append("🤖 Ami imparare con l'AI! Sei un vero ricercatore di conoscenza.")
        elif total_messages > total_ai_questions * 2:
            insights.append("💬 Sei un social learner! Ti piace condividere e discutere.")

        # Analisi miglioramenti
        if len(daily_data) >= 7:
            recent_avg = sum(day['xp_earned'] for day in daily_data[-7:]) / 7
            older_avg = sum(day['xp_earned'] for day in daily_data[:-7]) / max(1, len(daily_data) - 7)

            if recent_avg > older_avg * 1.2:
                insights.append("📊 Trend in crescita! Stai migliorando settimana dopo settimana.")
            elif recent_avg < older_avg * 0.8:
                insights.append("💡 Potresti tornare ai livelli precedenti con un po' più di focus.")

        return insights[:5]  # Massimo 5 insights

    # Resto delle funzioni esistenti (award_xp, check_level_up, etc.)
    def calculate_dynamic_multiplier(self, user_id: int, action_type: str) -> float:
        """Calcola multiplier XP dinamico basato su condizioni utente"""
        profile = self.get_or_create_user_profile(user_id)
        current_time = datetime.now()
        multiplier = 1.0

        # Streak bonus
        streak = profile['current_streak']
        if streak >= 100:
            multiplier *= self.xp_multipliers['streak_100_days']
        elif streak >= 60:
            multiplier *= self.xp_multipliers['streak_60_days']
        elif streak >= 30:
            multiplier *= self.xp_multipliers['streak_30_days']
        elif streak >= 14:
            multiplier *= self.xp_multipliers['streak_14_days']
        elif streak >= 7:
            multiplier *= self.xp_multipliers['streak_7_days']

        # Time-based bonus
        hour = current_time.hour
        if hour < 8:  # Early bird
            multiplier *= self.xp_multipliers['early_bird']
        elif hour >= 22:  # Night owl
            multiplier *= self.xp_multipliers['night_owl']

        # Weekend bonus
        if current_time.weekday() >= 5:  # Saturday or Sunday
            multiplier *= self.xp_multipliers['weekend_warrior']

        # Level-based bonus per utenti elite
        if profile['current_level'] >= 30:
            multiplier *= self.xp_multipliers['elite_status']

        return multiplier

    def award_xp(self, user_id: int, action_type: str, bonus_multiplier: float = 1.0, description: str = "") -> Dict[str, Any]:
        """Assegna XP per un'azione e controlla achievement e livelli"""
        if action_type not in self.xp_actions:
            return {'success': False, 'error': 'Azione non riconosciuta'}

        base_xp = self.xp_actions[action_type]

        # Calcola multiplier dinamico
        dynamic_multiplier = self.calculate_dynamic_multiplier(user_id, action_type)
        total_multiplier = bonus_multiplier * dynamic_multiplier

        final_xp = int(base_xp * total_multiplier)

        # Log del multiplier per trasparenza
        if total_multiplier > 1.0:
            multiplier_info = f" (Multiplier: {total_multiplier:.1f}x)"
            description = description + multiplier_info if description else f"Bonus multiplier {total_multiplier:.1f}x"

        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Aggiorna profilo utente
        cursor.execute('''
            UPDATE user_gamification 
            SET total_xp = total_xp + ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (final_xp, user_id))

        # Assegna monete avatar (10% dell'XP guadagnato)
        avatar_coins_earned = max(1, final_xp // 10)
        cursor.execute('''
            UPDATE user_gamification 
            SET avatar_coins = avatar_coins + ?
            WHERE user_id = ?
        ''', (avatar_coins_earned, user_id))

        # Log dell'attività
        cursor.execute('''
            INSERT INTO xp_activity_log (user_id, action_type, xp_earned, bonus_multiplier, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action_type, final_xp, bonus_multiplier, description))

        # Aggiorna analytics giornaliere
        cursor.execute('''
            UPDATE daily_analytics 
            SET daily_xp_earned = daily_xp_earned + ?
            WHERE user_id = ? AND date = DATE('now')
        ''', (final_xp, user_id))

        # Registra attività per analytics
        if action_type == 'message_sent':
            self.record_daily_activity(user_id, 'message_sent')
        elif action_type in ['ai_question', 'ai_correct_answer']:
            self.record_daily_activity(user_id, 'ai_question')
        elif action_type == 'quiz_completed':
            self.record_daily_activity(user_id, 'quiz_completed')
        elif action_type == 'help_classmate':
            self.record_daily_activity(user_id, 'help_given')

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
            'avatar_coins_earned': avatar_coins_earned,
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

            # Sblocca avatar e temi per livello
            for avatar_id, avatar_data in self.available_avatars.items():
                if avatar_data.get('unlock_level') == new_level:
                    cursor.execute('''
                        INSERT OR IGNORE INTO user_unlocked_items (user_id, item_type, item_id, unlock_method)
                        VALUES (?, 'avatar', ?, 'level')
                    ''', (user_id, avatar_id))

            for theme_id, theme_data in self.ui_themes.items():
                if theme_data.get('unlock_level') == new_level:
                    cursor.execute('''
                        INSERT OR IGNORE INTO user_unlocked_items (user_id, item_type, item_id, unlock_method)
                        VALUES (?, 'theme', ?, 'level')
                    ''', (user_id, theme_id))

            # Applica reward specifici del livello
            level_reward = self.level_rewards.get(new_level)
            unlock_message = ""
            if level_reward:
                # Aggiungi monete bonus
                bonus_coins = level_reward.get('bonus_coins', 0)
                if bonus_coins > 0:
                    cursor.execute('''
                        UPDATE user_gamification 
                        SET avatar_coins = avatar_coins + ?
                        WHERE user_id = ?
                    ''', (bonus_coins, user_id))

                unlock_message = level_reward.get('description', '')

            conn.commit()
            conn.close()

            level_reward = self.level_rewards.get(new_level, {})
            return {
                'leveled_up': True,
                'old_level': current_level,
                'new_level': new_level,
                'new_title': self.level_titles.get(new_level, f"Livello {new_level}"),
                'bonus_xp': 50 * new_level,  # Bonus XP per level up
                'special_reward': level_reward.get('description', ''),
                'bonus_coins': level_reward.get('bonus_coins', 0),
                'unlock_feature': level_reward.get('unlock', '')
            }

        return {'leveled_up': False}

    def check_new_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """Controlla e sblocca nuovi achievement"""
        profile = self.get_or_create_user_profile(user_id)

        # Achievement sbloccati
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

                    # Sblocca avatar speciali per achievement
                    for avatar_id, avatar_data in self.available_avatars.items():
                        if avatar_data.get('unlock_achievement') == achievement_id:
                            cursor.execute('''
                                INSERT OR IGNORE INTO user_unlocked_items (user_id, item_type, item_id, unlock_method)
                                VALUES (?, 'avatar', ?, 'achievement')
                            ''', (user_id, avatar_id))

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

            if days_diff == 0:
                # Stesso giorno - non aggiornare streak
                conn.close()
                return {'streak_updated': False, 'current_streak': profile['current_streak'], 'streak_broken': False}
            elif days_diff == 1:
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
        return {'streak_updated': False, 'current_streak': 0, 'streak_broken': False}

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
                   ug.current_avatar, ug.current_theme,
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
                    'rank': row[8],
                    'name': f"{row[0]} {row[1]}",
                    'class': row[2],
                    'total_xp': row[3],
                    'level': row[4],
                    'level_title': self.level_titles.get(row[4], 'Studente'),
                    'avatar': self.available_avatars.get(row[6], self.available_avatars['default']),
                    'theme': row[7],
                    'is_current_user': row[5] == user_id
                } for row in leaderboard
            ],
            'user_rank': user_rank,
            'period': period,
            'class_filter': class_filter
        }

    def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Dashboard gamification completa per l'utente"""
        try:
            profile = self.get_or_create_user_profile(user_id)

            # Achievement sbloccati - USA db_manager invece di sqlite3 diretto
            unlocked_achievements = db_manager.query('''
                SELECT ua.achievement_id, ua.unlocked_at, ua.xp_earned
                FROM user_achievements ua
                WHERE ua.user_id = ?
                ORDER BY ua.unlocked_at DESC
            ''', (user_id,))

            # Attività XP recente
            recent_activity = db_manager.query('''
                SELECT action_type, xp_earned, description, timestamp
                FROM xp_activity_log
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (user_id,))

            # Calcola prossimo livello
            current_level = profile['current_level']
            next_level = current_level + 1 if current_level < 10 else 10
            current_xp = profile['total_xp']
            next_level_xp = self.level_thresholds.get(next_level, self.level_thresholds[10])
            level_progress = min(100, (current_xp / next_level_xp) * 100) if next_level_xp > 0 else 100

            # Ottieni badge sbloccati - USA db_manager
            unlocked_badges = db_manager.query('''
                SELECT ub.badge_id, ub.earned_at, ub.xp_earned, ub.rarity
                FROM user_badges ub
                WHERE ub.user_id = ?
                ORDER BY ub.earned_at DESC
            ''', (user_id,))

            # Ottieni statistiche avanzate per badge
            advanced_stats = self.get_or_create_advanced_stats(user_id)

            dashboard_data = {
                'profile': {
                    **profile,
                    'level_title': self.level_titles[current_level],
                    'next_level_xp': next_level_xp,
                    'level_progress': level_progress,
                    'current_avatar_data': self.available_avatars.get(profile['current_avatar'], self.available_avatars['default']),
                    'streak_bonus_active': self.streak_system['daily_bonuses'].get(profile['current_streak'], {}).get('xp_multiplier', 1.0)
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
                'team_challenges': self.get_active_team_challenges(profile.get('classe')),
                'recent_activity': [
                    {
                        'action': row[0],
                        'xp_earned': row[1],
                        'description': row[2],
                        'timestamp': row[3]
                    } for row in recent_activity
                ],
                'leaderboard_position': self.get_leaderboard(user_id, 'weekly'),
                'analytics': self.get_user_analytics(user_id, 30),
                'available_avatars': self.get_available_avatars(user_id),
                'badges': {
                    'unlocked': [
                        {
                            'id': row[0],
                            'name': self.badge_system[row[0]]['name'] if row[0] in self.badge_system else 'Unknown Badge',
                            'description': self.badge_system[row[0]]['description'] if row[0] in self.badge_system else '',
                            'category': self.badge_system[row[0]]['category'] if row[0] in self.badge_system else 'unknown',
                            'rarity': row[3],
                            'badge_icon': self.badge_system[row[0]]['badge_icon'] if row[0] in self.badge_system else '🏆',
                            'earned_at': row[1],
                            'xp_earned': row[2]
                        } for row in unlocked_badges if row[0] in self.badge_system
                    ],
                    'available': [
                        {
                            'id': badge_id,
                            'name': badge['name'],
                            'description': badge['description'],
                            'category': badge['category'],
                            'xp_reward': badge['xp_reward'],
                            'rarity': badge['rarity'],
                            'badge_icon': badge['badge_icon'],
                            'progress': self.calculate_badge_progress(badge_id, {**profile, **advanced_stats})
                        } for badge_id, badge in self.badge_system.items() 
                        if badge_id not in [row[0] for row in unlocked_badges]
                    ]
                },
                'streak_system': {
                    'current_streak': profile['current_streak'],
                    'max_streak': profile['max_streak'],
                    'current_bonus': self.streak_system['daily_bonuses'].get(profile['current_streak'], {}).get('description', 'Nessun bonus'),
                    'next_milestone': self.get_next_streak_milestone(profile['current_streak']),
                    'protections_available': self.get_available_protections(user_id),
                    'freeze_cards_remaining': max(0, 1 - advanced_stats.get('freeze_cards_used_this_month', 0)),
                    'weekend_passes_active': advanced_stats.get('weekend_passes_active', 0)
                },
                'statistics': {
                    'total_achievements': len(unlocked_achievements),
                    'total_badges': len(unlocked_badges),
                    'badge_completion_rate': (len(unlocked_badges) / len(self.badge_system)) * 100,
                    'achievement_completion_rate': (len(unlocked_achievements) / len(self.achievements)) * 100,
                    'daily_streak': profile['current_streak'],
                    'best_streak': profile['max_streak'],
                    'avatar_coins': profile['avatar_coins']
                }
            }

            return dashboard_data
        except Exception as e:
            print(f"❌ Error in get_user_dashboard: {e}")
            return {
                'profile': {'total_xp': 0, 'current_level': 1, 'coins': 0},
                'recent_activities': [],
                'leaderboard': [],
                'achievements': [],
                'daily_challenges': []
            }

    def get_or_create_advanced_stats(self, user_id: int) -> Dict[str, Any]:
        """Ottieni o crea statistiche avanzate per badge"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        stats = cursor.execute('''
            SELECT * FROM user_advanced_stats WHERE user_id = ?
        ''', (user_id,)).fetchone()

        if not stats:
            # Crea nuovo record statistiche
            cursor.execute('''
                INSERT INTO user_advanced_stats (user_id)
                VALUES (?)
            ''', (user_id,))
            conn.commit()

            stats = cursor.execute('''
                SELECT * FROM user_advanced_stats WHERE user_id = ?
            ''', (user_id,)).fetchone()

        conn.close()

        if stats:
            # Convert tuple to dict, mapping column names if available or by index
            # Assuming the columns are in the order they are defined in the CREATE TABLE statement
            # For SQLite, fetchone() returns a tuple. For more robust solutions, use DictCursor if available.
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            if column_names:
                return dict(zip(column_names, stats))
            else:
                # Fallback if column names are not available
                return {
                    'user_id': stats[0], 'perfect_quizzes': stats[1], 'speed_completions': stats[2],
                    'courses_mastered': stats[3], 'likes_received': stats[4], 'discussions_moderated': stats[5],
                    'early_morning_sessions': stats[6], 'late_night_sessions': stats[7],
                    'weekend_challenges_completed': stats[8], 'longest_study_session': stats[9],
                    'lessons_completed': stats[10], 'days_on_platform': stats[11], 'courses_explored': stats[12],
                    'features_suggested_implemented': stats[13], 'total_courses_available': stats[14],
                    'freeze_cards_used_this_month': stats[15], 'weekend_passes_active': stats[16],
                    'last_freeze_card_reset': stats[17]
                }

        return {}


    def check_new_badges(self, user_id: int) -> List[Dict[str, Any]]:
        """Controlla e sblocca nuovi badge"""
        advanced_stats = self.get_or_create_advanced_stats(user_id)
        profile = self.get_or_create_user_profile(user_id)

        # Combina statistiche per controllo badge
        combined_stats = {**profile, **advanced_stats}

        # Ottieni badge già sbloccati
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        unlocked_badges = cursor.execute('''
            SELECT badge_id FROM user_badges WHERE user_id = ?
        ''', (user_id,)).fetchall()
        unlocked_badge_ids = [row[0] for row in unlocked_badges]

        new_badges = []

        # Controlla ogni badge
        for badge_id, badge in self.badge_system.items():
            if badge_id not in unlocked_badge_ids:
                if badge['condition'](combined_stats):
                    # Sblocca badge
                    cursor.execute('''
                        INSERT INTO user_badges (user_id, badge_id, xp_earned, rarity)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, badge_id, badge['xp_reward'], badge['rarity']))

                    # Assegna XP bonus
                    cursor.execute('''
                        UPDATE user_gamification 
                        SET total_xp = total_xp + ? 
                        WHERE user_id = ?
                    ''', (badge['xp_reward'], user_id))

                    new_badges.append({
                        'id': badge_id,
                        'name': badge['name'],
                        'description': badge['description'],
                        'category': badge['category'],
                        'xp_reward': badge['xp_reward'],
                        'rarity': badge['rarity'],
                        'badge_icon': badge['badge_icon']
                    })

        conn.commit()
        conn.close()
        return new_badges

    def apply_streak_bonus(self, user_id: int, base_xp: int) -> int:
        """Applica bonus streak all'XP"""
        profile = self.get_or_create_user_profile(user_id)
        current_streak = profile.get('current_streak', 0)

        # Trova il bonus appropriato
        applicable_bonus = 1.0
        for streak_days, bonus_data in self.streak_system['daily_bonuses'].items():
            if current_streak >= streak_days:
                applicable_bonus = bonus_data['xp_multiplier']

        return int(base_xp * applicable_bonus)

    def use_streak_protection(self, user_id: int, protection_type: str) -> Dict[str, Any]:
        """Usa una protezione streak"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        advanced_stats = self.get_or_create_advanced_stats(user_id)
        current_month = datetime.now().strftime('%Y-%m')

        if protection_type == 'freeze_card':
            # Controlla se può usare freeze card questo mese
            if advanced_stats.get('freeze_cards_used_this_month', 0) >= 1:
                conn.close()
                return {'success': False, 'error': 'Freeze Card già usata questo mese'}

            # Usa freeze card
            cursor.execute('''
                INSERT INTO streak_protections (user_id, protection_type, expires_at)
                VALUES (?, ?, DATETIME('now', '+1 day'))
            ''', (user_id, protection_type))

            cursor.execute('''
                UPDATE user_advanced_stats 
                SET freeze_cards_used_this_month = freeze_cards_used_this_month + 1
                WHERE user_id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()
            return {'success': True, 'message': '❄️ Freeze Card attivata! Streak protetta per 1 giorno.'}

        elif protection_type == 'weekend_pass':
            # Controlla se ha abbastanza monete
            profile = self.get_or_create_user_profile(user_id)
            if profile.get('avatar_coins', 0) < 500:
                conn.close()
                return {'success': False, 'error': 'Monete insufficienti (richieste: 500)'}

            # Acquista weekend pass
            cursor.execute('''
                INSERT INTO streak_protections (user_id, protection_type, expires_at)
                VALUES (?, ?, DATETIME('now', '+7 days'))
            ''', (user_id, protection_type))

            cursor.execute('''
                UPDATE user_gamification 
                SET avatar_coins = avatar_coins - 500
                WHERE user_id = ?
            ''', (user_id,))

            cursor.execute('''
                UPDATE user_advanced_stats 
                SET weekend_passes_active = weekend_passes_active + 1
                WHERE user_id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()
            return {'success': True, 'message': '🎫 Weekend Pass attivato! Streak protetta nei weekend per 1 settimana.'}

        conn.close()
        return {'success': False, 'error': 'Tipo di protezione non valido'}

    def update_advanced_stat(self, user_id: int, stat_name: str, increment: int = 1):
        """Aggiorna una statistica avanzata"""
        conn = sqlite3.connect('skaila.db')
        cursor = conn.cursor()

        # Assicura che il record esista
        self.get_or_create_advanced_stats(user_id)

        # Aggiorna la statistica
        cursor.execute(f'''
            UPDATE user_advanced_stats 
            SET {stat_name} = {stat_name} + ?
            WHERE user_id = ?
        ''', (increment, user_id))

        conn.commit()
        conn.close()

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
        elif achievement_id == 'team_player':
            return min(100, (profile['team_challenges_participated'] / 5) * 100)
        elif achievement_id == 'class_champion':
            return min(100, (profile['team_challenges_won'] / 3) * 100)
        elif achievement_id == 'mentor_master':
            return min(100, (profile['mentorship_sessions'] / 10) * 100)

        return 0.0

    def calculate_badge_progress(self, badge_id: str, combined_stats: Dict[str, Any]) -> float:
        """Calcola il progresso verso un badge"""
        if badge_id == 'perfect_score_10':
            return min(100, (combined_stats.get('perfect_quizzes', 0) / 10) * 100)
        elif badge_id == 'speed_learner':
            return min(100, (combined_stats.get('speed_completions', 0) / 5) * 100)
        elif badge_id == 'consistency_king':
            return min(100, (combined_stats.get('max_streak', 0) / 30) * 100)
        elif badge_id == 'helper_badge':
            return min(100, (combined_stats.get('help_given', 0) / 50) * 100)
        elif badge_id == 'popular_teacher':
            return min(100, (combined_stats.get('likes_received', 0) / 100) * 100)
        elif badge_id == 'early_bird':
            return min(100, (combined_stats.get('early_morning_sessions', 0) / 7) * 100)
        elif badge_id == 'night_owl':
            return min(100, (combined_stats.get('late_night_sessions', 0) / 7) * 100)
        elif badge_id == 'weekend_warrior':
            return min(100, (combined_stats.get('weekend_challenges_completed', 0) / 4) * 100)
        elif badge_id == 'marathon_runner':
            return min(100, (combined_stats.get('longest_study_session', 0) / 360) * 100)
        elif badge_id == 'veteran':
            return min(100, (combined_stats.get('days_on_platform', 0) / 365) * 100)
        elif badge_id == 'explorer':
            total_courses = combined_stats.get('total_courses_available', 10)
            explored = combined_stats.get('courses_explored', 0)
            return min(100, (explored / total_courses) * 100)

        return 0.0

    def get_next_streak_milestone(self, current_streak: int) -> Dict[str, Any]:
        """Ottieni prossima milestone streak"""
        milestones = [3, 7, 14, 30, 100]

        for milestone in milestones:
            if current_streak < milestone:
                days_remaining = milestone - current_streak
                bonus_info = self.streak_system['daily_bonuses'].get(milestone, {})
                return {
                    'days': milestone,
                    'days_remaining': days_remaining,
                    'reward': bonus_info.get('description', 'Bonus speciale'),
                    'xp_multiplier': bonus_info.get('xp_multiplier', 1.0)
                }

        return {
            'days': 365,
            'days_remaining': 365 - current_streak,
            'reward': 'Status Immortale',
            'xp_multiplier': 3.0
        }

    def get_available_protections(self, user_id: int) -> List[Dict[str, Any]]:
        """Ottieni protezioni streak disponibili"""
        advanced_stats = self.get_or_create_advanced_stats(user_id)
        profile = self.get_or_create_user_profile(user_id)

        protections = []

        # Freeze Card
        freeze_cards_used = advanced_stats.get('freeze_cards_used_this_month', 0)
        if freeze_cards_used < 1:
            protections.append({
                'type': 'freeze_card',
                'name': '❄️ Freeze Card',
                'description': '1 giorno gratis al mese',
                'available': True,
                'cost': 0,
                'remaining': 1 - freeze_cards_used
            })

        # Weekend Pass
        avatar_coins = profile.get('avatar_coins', 0)
        protections.append({
            'type': 'weekend_pass',
            'name': '🎫 Weekend Pass',
            'description': 'Weekend non rompe streak (7 giorni)',
            'available': avatar_coins >= 500,
            'cost': 500,
            'currency': 'monete'
        })

        return protections


# Istanza globale del sistema di gamification
gamification_system = SKAILAGamification()

def init_gamification():
    """Inizializza il sistema di gamification"""
    gamification_system.init_gamification_tables()
    print("🎮 Sistema di Gamification SKAILA completo inizializzato!")

if __name__ == "__main__":
    init_gamification()