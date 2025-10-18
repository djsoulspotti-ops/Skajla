"""
SKAILA - Configurazioni Gamification (SSoT)
Single Source of Truth per XP, livelli, badge e achievements
"""

from typing import Dict, List, Tuple

class XPConfig:
    """Configurazione sistema XP"""
    
    ACTIONS = {
        # Login e streak
        'login_daily': 10,
        'first_login_day': 25,
        'week_streak': 100,
        'month_streak': 300,
        
        # Lezioni e corsi
        'lesson_completion_easy': 50,
        'lesson_completion_medium': 100,
        'lesson_completion_hard': 200,
        'course_completion': 750,
        'bonus_challenge': 250,
        'lesson_completed': 30,
        'homework_submitted': 40,
        
        # Quiz e valutazioni
        'quiz_completed': 50,
        'quiz_perfect_score_easy': 100,
        'quiz_perfect_score_medium': 200,
        'quiz_perfect_score_hard': 300,
        'assignment_submit': 100,
        'milestone_achievement': 350,
        'quiz_perfect': 100,
        
        # Interazioni AI
        'ai_question': 15,
        'ai_correct_answer': 30,
        
        # Social learning
        'message_sent': 5,
        'help_classmate': 60,
        'peer_tutoring_session': 120,
        'create_study_group': 80,
        'join_study_group': 30,
        'help_peer': 25,
        'first_message': 20,
        
        # Studio e tempo
        'study_session_15min': 20,
        'study_session_30min': 40,
        'study_session_60min': 80,
        'focus_session_completed': 50,
        'study_session': 35,
        
        # Collaborative e team
        'team_challenge_completed': 150,
        'team_challenge_contributed': 75,
        'inter_class_victory': 200,
        'mentorship_session': 100,
        'collaborative_project': 120,
        
        # Special achievements
        'perfect_week': 400,
        'knowledge_master': 500,
        'community_leader': 300,
        'achievement_unlocked': 100,
        'streak_milestone': 50,
        
        # Profilo e onboarding
        'complete_profile': 50,
        
        # SKAILA Connect (carriera)
        'skaila_connect_apply': 50,
        'first_skaila_connect': 50,
        'career_action': 50
    }
    
    MULTIPLIERS = {
        'daily_streak': 1.2,
        'weekend': 1.5,
        'weekend_bonus': 1.5,
        'birthday': 2.0,
        'event_special': 1.3,
        'perfect_week': 1.5,
        'perfect_score': 2.0,
        'helping_others': 1.3,
        'first_time': 1.1
    }
    
    BONUS_THRESHOLDS = {
        'perfect_attendance_week': (7, 100),
        'perfect_attendance_month': (30, 500),
        'study_streak_7': (7, 150),
        'study_streak_30': (30, 1000)
    }

class LevelConfig:
    """Configurazione sistema livelli"""
    
    THRESHOLDS: List[Tuple[int, int]] = [
        (1, 0),
        (2, 100),
        (3, 250),
        (4, 500),
        (5, 1000),
        (6, 1750),
        (7, 2750),
        (8, 4000),
        (9, 5500),
        (10, 7500),
        (11, 10000),
        (12, 13000),
        (13, 16500),
        (14, 20500),
        (15, 25000),
        (16, 30000),
        (17, 36000),
        (18, 43000),
        (19, 51000),
        (20, 60000),
        (21, 70000),
        (22, 82000),
        (23, 95000),
        (24, 110000),
        (25, 127000),
        (26, 146000),
        (27, 167000),
        (28, 190000),
        (29, 215000),
        (30, 243000),
        (31, 274000),
        (32, 308000),
        (33, 346000),
        (34, 388000),
        (35, 435000),
        (36, 487000),
        (37, 545000),
        (38, 609000),
        (39, 680000),
        (40, 758000),
        (41, 844000),
        (42, 938000),
        (43, 1041000),
        (44, 1154000),
        (45, 1277000),
        (46, 1411000),
        (47, 1557000),
        (48, 1715000),
        (49, 1886000),
        (50, 2071000)
    ]
    
    TITLES = {
        1: "Novizio",
        5: "Apprendista",
        10: "Studente",
        15: "Esperto",
        20: "Maestro",
        25: "Veterano",
        30: "Elite",
        35: "Campione",
        40: "Leggenda",
        45: "Mito",
        50: "SKAILA Master"
    }
    
    @classmethod
    def get_level_from_xp(cls, xp: int) -> int:
        """Calcola il livello dall'XP"""
        for level, threshold in reversed(cls.THRESHOLDS):
            if xp >= threshold:
                return level
        return 1
    
    @classmethod
    def get_xp_for_next_level(cls, current_xp: int) -> int:
        """Calcola XP necessari per il prossimo livello"""
        current_level = cls.get_level_from_xp(current_xp)
        if current_level >= 50:
            return 0
        
        for level, threshold in cls.THRESHOLDS:
            if level == current_level + 1:
                return threshold - current_xp
        return 0

class BadgeConfig:
    """Configurazione sistema badge"""
    
    BADGES = {
        'first_steps': {
            'name': 'Primi Passi',
            'description': 'Completa il tuo primo quiz',
            'icon': '🎯',
            'rarity': 'common',
            'xp_reward': 50
        },
        'chat_master': {
            'name': 'Maestro della Chat',
            'description': 'Invia 100 messaggi',
            'icon': '💬',
            'rarity': 'uncommon',
            'xp_reward': 100
        },
        'quiz_genius': {
            'name': 'Genio dei Quiz',
            'description': 'Ottieni 10 quiz perfetti',
            'icon': '🧠',
            'rarity': 'rare',
            'xp_reward': 250
        },
        'study_warrior': {
            'name': 'Guerriero dello Studio',
            'description': 'Studia per 7 giorni consecutivi',
            'icon': '⚔️',
            'rarity': 'epic',
            'xp_reward': 500
        },
        'skaila_legend': {
            'name': 'Leggenda SKAILA',
            'description': 'Raggiungi il livello 50',
            'icon': '👑',
            'rarity': 'legendary',
            'xp_reward': 1000
        },
        'ai_enthusiast': {
            'name': 'Entusiasta AI',
            'description': 'Fai 50 domande a SKAILA AI',
            'icon': '🤖',
            'rarity': 'uncommon',
            'xp_reward': 150
        },
        'perfect_attendance': {
            'name': 'Presenza Perfetta',
            'description': 'Nessuna assenza per un mese',
            'icon': '✅',
            'rarity': 'rare',
            'xp_reward': 300
        },
        'top_grades': {
            'name': 'Voti Eccellenti',
            'description': 'Media superiore a 9.0',
            'icon': '🌟',
            'rarity': 'epic',
            'xp_reward': 400
        }
    }
    
    RARITY_COLORS = {
        'common': '#808080',
        'uncommon': '#00ff00',
        'rare': '#0070dd',
        'epic': '#a335ee',
        'legendary': '#ff8000'
    }

class StreakConfig:
    """Configurazione sistema streak"""
    
    MILESTONES = [7, 14, 30, 60, 100, 180, 365]
    
    REWARDS = {
        7: {'xp': 100, 'badge': 'week_warrior'},
        14: {'xp': 250, 'badge': 'fortnight_fighter'},
        30: {'xp': 500, 'badge': 'month_master'},
        60: {'xp': 1000, 'badge': 'two_month_titan'},
        100: {'xp': 2000, 'badge': 'centurion'},
        180: {'xp': 5000, 'badge': 'semester_star'},
        365: {'xp': 10000, 'badge': 'year_legend'}
    }
    
    MAX_STREAK_FREEZE_DAYS = 3

gamification_config = {
    'xp': XPConfig,
    'level': LevelConfig,
    'badge': BadgeConfig,
    'streak': StreakConfig
}
