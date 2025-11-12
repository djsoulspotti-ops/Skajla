"""
SKAILA Gamification Configuration
Centralized configuration for XP actions, multipliers, levels, badges, and streaks
"""

class XPConfig:
    """Configuration for XP (Experience Points) system"""
    
    ACTIONS = {
        'quiz_completed': 50,
        'quiz_perfect': 100,
        'quiz_good': 75,
        'quiz_passed': 40,
        'message_sent': 5,
        'message_received': 2,
        'study_session_started': 10,
        'study_minute': 2,
        'study_session_completed': 50,
        'study_session_long': 100,
        'material_uploaded': 30,
        'material_downloaded': 10,
        'ai_question_asked': 15,
        'ai_suggestion_used': 20,
        'login_daily': 10,
        'streak_maintained': 25,
        'assignment_submitted': 60,
        'assignment_early': 80,
        'grade_excellent': 100,
        'grade_good': 75,
        'grade_pass': 50,
        'attendance_perfect_week': 50,
        'attendance_perfect_month': 200,
        'help_peer': 40,
        'helped_by_peer': 20,
        'profile_completed': 30,
        'avatar_customized': 15,
        'challenge_joined': 25,
        'challenge_won': 150,
        'badge_earned': 100,
        'level_up': 200,
        'reading_completed': 35,
        'video_watched': 30,
        'discussion_participated': 25,
        'poll_answered': 10,
        'feedback_provided': 20,
        'goal_set': 15,
        'goal_achieved': 100,
        'collaboration_created': 40,
        'project_submitted': 120,
        'certificate_earned': 300,
    }
    
    MULTIPLIERS = {
        'first_time': 2.0,
        'streak_3_days': 1.2,
        'streak_7_days': 1.5,
        'streak_14_days': 1.8,
        'streak_30_days': 2.5,
        'weekend': 1.3,
        'late_night': 1.2,
        'perfect_week': 2.0,
        'team_collaboration': 1.5,
        'helping_others': 1.8,
        'study_pomodoro': 1.4,
        'study_deep_work': 1.6,
        'study_review': 1.3,
        'study_focus': 1.5,
        'early_submission': 1.3,
        'bonus_challenge': 2.0,
    }


class LevelConfig:
    """Configuration for user levels and titles"""
    
    TITLES = {
        1: "🌱 Principiante",
        2: "📖 Studente",
        3: "✏️ Apprendista",
        4: "📚 Lettore",
        5: "🎓 Studioso",
        10: "⭐ Dedicato",
        15: "🏆 Impegnato",
        20: "💎 Esperto",
        25: "👑 Maestro",
        30: "🔥 Veterano",
        35: "🚀 Eccellente",
        40: "💫 Straordinario",
        45: "🌟 Leggenda",
        50: "👨‍🎓 Professore",
        60: "🧙 Saggio",
        70: "🦅 Illuminato",
        80: "⚡ Fulmine",
        90: "🌌 Cosmico",
        100: "🏅 Grande Maestro"
    }


class BadgeConfig:
    """Configuration for achievement badges"""
    
    BADGES = {
        'first_quiz': {
            'name': '🎯 Primo Quiz',
            'description': 'Completa il tuo primo quiz',
            'xp_reward': 50,
            'condition': 'quizzes_completed >= 1'
        },
        'quiz_master': {
            'name': '🏆 Maestro dei Quiz',
            'description': 'Completa 100 quiz',
            'xp_reward': 500,
            'condition': 'quizzes_completed >= 100'
        },
        'perfect_streak_7': {
            'name': '🔥 Settimana Perfetta',
            'description': 'Mantieni uno streak di 7 giorni',
            'xp_reward': 200,
            'condition': 'current_streak >= 7'
        },
        'perfect_streak_30': {
            'name': '💎 Mese Perfetto',
            'description': 'Mantieni uno streak di 30 giorni',
            'xp_reward': 1000,
            'condition': 'current_streak >= 30'
        },
        'social_butterfly': {
            'name': '🦋 Farfalla Sociale',
            'description': 'Invia 500 messaggi',
            'xp_reward': 300,
            'condition': 'messages_sent >= 500'
        },
        'knowledge_seeker': {
            'name': '📚 Cercatore di Conoscenza',
            'description': 'Scarica 50 materiali didattici',
            'xp_reward': 250,
            'condition': 'materials_downloaded >= 50'
        },
        'study_warrior': {
            'name': '⚔️ Guerriero dello Studio',
            'description': 'Completa 100 sessioni di studio',
            'xp_reward': 600,
            'condition': 'study_sessions >= 100'
        },
        'ai_explorer': {
            'name': '🤖 Esploratore AI',
            'description': 'Interagisci 50 volte con SKAILA AI',
            'xp_reward': 400,
            'condition': 'ai_interactions >= 50'
        },
        'perfectionist': {
            'name': '💯 Perfezionista',
            'description': 'Ottieni 10 quiz perfetti',
            'xp_reward': 500,
            'condition': 'perfect_quizzes >= 10'
        },
        'team_player': {
            'name': '🤝 Giocatore di Squadra',
            'description': 'Vinci 5 sfide di gruppo',
            'xp_reward': 750,
            'condition': 'team_challenges_won >= 5'
        },
    }


class StreakConfig:
    """Configuration for streak system"""
    
    STREAK_XP_BONUS = {
        3: 50,
        7: 150,
        14: 350,
        21: 600,
        30: 1000,
        60: 2500,
        90: 5000,
        180: 10000,
        365: 25000,
    }
    
    STREAK_TITLES = {
        3: "🔥 In Fiamme",
        7: "⚡ Fulmine",
        14: "💪 Determinato",
        21: "🚀 Inarrestabile",
        30: "👑 Leggenda",
        60: "🌟 Fenomeno",
        90: "💎 Diamante",
        180: "🦅 Aquila",
        365: "🏆 Grande Campione"
    }


__all__ = ['XPConfig', 'LevelConfig', 'BadgeConfig', 'StreakConfig']
