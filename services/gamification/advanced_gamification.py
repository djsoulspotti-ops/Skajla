"""
Advanced Gamification System for SKAJLA
Complete gamification with ranks, battle pass, challenges, kudos, and leaderboards
Adapted for SKAJLA's DatabaseManager pattern
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
from services.database.database_manager import db_manager
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# RANK CONFIGURATION - Germoglio → Immortale progression
# =============================================================================

RANK_CONFIG = {
    'Germoglio': {'min_xp': 0, 'icon': '🌱', 'color': '#90EE90'},
    'Cadetto': {'min_xp': 200, 'icon': '🎖️', 'color': '#87CEEB'},
    'Cavaliere': {'min_xp': 600, 'icon': '⚔️', 'color': '#DDA0DD'},
    'Guardiano': {'min_xp': 1200, 'icon': '🛡️', 'color': '#FFD700'},
    'Campione': {'min_xp': 2200, 'icon': '🏆', 'color': '#FFA500'},
    'Leggenda': {'min_xp': 3800, 'icon': '⭐', 'color': '#FF6347'},
    'Maestro': {'min_xp': 6000, 'icon': '👑', 'color': '#9370DB'},
    'Grande Maestro': {'min_xp': 9000, 'icon': '💎', 'color': '#00CED1'},
    'Immortale': {'min_xp': 13000, 'icon': '🔥', 'color': '#FF4500'}
}

RANK_ORDER = ['Germoglio', 'Cadetto', 'Cavaliere', 'Guardiano', 'Campione', 
              'Leggenda', 'Maestro', 'Grande Maestro', 'Immortale']

# =============================================================================
# XP CONFIGURATION
# =============================================================================

XP_CONFIG = {
    # Messaggistica
    'messaggio_base': 5,
    'messaggio_primo_giorno': 15,
    'messaggio_risposta_veloce': 5,
    'messaggio_con_emoji': 3,
    'conversazione_gruppo': 20,
    'aiutare_compagno': 30,
    'reaction_ricevuta': 2,
    
    # Chatbot
    'chatbot_prima_interazione': 20,
    'chatbot_domanda': 5,
    'chatbot_conversazione_lunga': 50,
    'chatbot_studio': 25,
    'chatbot_feedback': 15,
    'chatbot_problema_risolto': 40,
    
    # Quiz
    'quiz_completato': 50,
    'quiz_perfetto': 100,
    'quiz_buono': 75,
    
    # Streak bonus
    'streak_3_giorni': 50,
    'streak_7_giorni': 150,
    'streak_14_giorni': 350,
    'streak_30_giorni': 800,
    
    # Limiti giornalieri
    'max_xp_messaggi': 500,
    'max_xp_chatbot': 300,
    'max_xp_quiz': 400
}


def calcola_rango(xp_totale: int) -> str:
    """Calculate rank based on total XP"""
    rango = 'Germoglio'
    for rank_name in RANK_ORDER:
        if xp_totale >= RANK_CONFIG[rank_name]['min_xp']:
            rango = rank_name
    return rango


def xp_per_prossimo_rango(rango_attuale: str) -> int:
    """Get XP required for next rank"""
    try:
        idx = RANK_ORDER.index(rango_attuale)
        if idx < len(RANK_ORDER) - 1:
            return RANK_CONFIG[RANK_ORDER[idx + 1]]['min_xp']
        return RANK_CONFIG['Immortale']['min_xp'] + 5000  # Post-Immortale
    except ValueError:
        return 200  # Default to Cadetto requirement


class AdvancedGamificationManager:
    """Complete gamification system with advanced features"""
    
    def __init__(self):
        self.xp_config = XP_CONFIG
        self.rank_config = RANK_CONFIG
    
    def init_advanced_tables(self):
        """Initialize all advanced gamification tables"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                is_postgres = db_manager.db_type == 'postgresql'
                serial_type = 'SERIAL' if is_postgres else 'INTEGER'
                timestamp_default = 'CURRENT_TIMESTAMP'
                
                # User Gamification V2 - Extended profile
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_gamification_v2 (
                        id {serial_type} PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL,
                        xp_totale INTEGER DEFAULT 0,
                        xp_stagionale INTEGER DEFAULT 0,
                        xp_settimanale INTEGER DEFAULT 0,
                        xp_giornaliero INTEGER DEFAULT 0,
                        rango VARCHAR(50) DEFAULT 'Germoglio',
                        rango_max_raggiunto VARCHAR(50) DEFAULT 'Germoglio',
                        streak_giorni INTEGER DEFAULT 0,
                        streak_max INTEGER DEFAULT 0,
                        ultimo_accesso TIMESTAMP DEFAULT {timestamp_default},
                        battle_pass_livello INTEGER DEFAULT 0,
                        battle_pass_premium BOOLEAN DEFAULT FALSE,
                        messaggi_inviati INTEGER DEFAULT 0,
                        chatbot_interazioni INTEGER DEFAULT 0,
                        compagni_aiutati INTEGER DEFAULT 0,
                        gruppi_studio_creati INTEGER DEFAULT 0,
                        reactions_ricevute INTEGER DEFAULT 0,
                        quiz_completati INTEGER DEFAULT 0,
                        quiz_perfetti INTEGER DEFAULT 0,
                        avatar_id VARCHAR(50),
                        tema_colore VARCHAR(50),
                        titolo VARCHAR(100),
                        cornice_profilo VARCHAR(50),
                        effetto_messaggio VARCHAR(50),
                        pet_id VARCHAR(50),
                        created_at TIMESTAMP DEFAULT {timestamp_default},
                        updated_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # XP Logs - Transaction history
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS xp_logs (
                        id {serial_type} PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        amount INTEGER NOT NULL,
                        source VARCHAR(100) NOT NULL,
                        description TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # Badges definition
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS badges_v2 (
                        id {serial_type} PRIMARY KEY,
                        codice VARCHAR(50) UNIQUE NOT NULL,
                        nome VARCHAR(100) NOT NULL,
                        descrizione TEXT NOT NULL,
                        icon VARCHAR(20),
                        rarita VARCHAR(20) DEFAULT 'comune',
                        stagionale BOOLEAN DEFAULT FALSE,
                        stagione_id INTEGER,
                        segreto BOOLEAN DEFAULT FALSE,
                        condizioni JSONB,
                        reward_xp INTEGER DEFAULT 0,
                        reward_titolo VARCHAR(100),
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # User badges (unlocked)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_badges_v2 (
                        id {serial_type} PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        badge_id INTEGER NOT NULL,
                        unlocked_at TIMESTAMP DEFAULT {timestamp_default},
                        notified BOOLEAN DEFAULT FALSE,
                        UNIQUE(user_id, badge_id)
                    )
                ''')
                
                # Challenges definition
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS challenges_v2 (
                        id {serial_type} PRIMARY KEY,
                        codice VARCHAR(50) UNIQUE NOT NULL,
                        nome VARCHAR(100) NOT NULL,
                        descrizione TEXT NOT NULL,
                        tipo VARCHAR(20) NOT NULL,
                        difficolta VARCHAR(20) DEFAULT 'media',
                        anno_min INTEGER,
                        anno_max INTEGER,
                        obiettivi JSONB NOT NULL,
                        reward_xp INTEGER NOT NULL,
                        reward_badge_id INTEGER,
                        reward_extra JSONB,
                        attiva BOOLEAN DEFAULT TRUE,
                        stagione_id INTEGER,
                        data_inizio TIMESTAMP,
                        data_fine TIMESTAMP,
                        reset_giornaliero BOOLEAN DEFAULT FALSE,
                        reset_settimanale BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # User challenges (progress)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_challenges_v2 (
                        id {serial_type} PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        challenge_id INTEGER NOT NULL,
                        progresso JSONB,
                        completato BOOLEAN DEFAULT FALSE,
                        assegnata_at TIMESTAMP DEFAULT {timestamp_default},
                        completata_at TIMESTAMP,
                        reward_claimed BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Seasons
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS seasons (
                        id {serial_type} PRIMARY KEY,
                        numero INTEGER UNIQUE NOT NULL,
                        nome VARCHAR(100) NOT NULL,
                        tema VARCHAR(50),
                        data_inizio TIMESTAMP NOT NULL,
                        data_fine TIMESTAMP NOT NULL,
                        attiva BOOLEAN DEFAULT FALSE,
                        descrizione TEXT,
                        narrativa TEXT,
                        moneta_stagionale VARCHAR(50),
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # Battle Pass Levels
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS battle_pass_levels (
                        id {serial_type} PRIMARY KEY,
                        stagione_id INTEGER NOT NULL,
                        livello INTEGER NOT NULL,
                        reward_free JSONB,
                        reward_premium JSONB,
                        xp_richiesti INTEGER NOT NULL,
                        UNIQUE(stagione_id, livello)
                    )
                ''')
                
                # Leaderboards
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS leaderboards_v2 (
                        id {serial_type} PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL,
                        xp_giornaliero INTEGER DEFAULT 0,
                        xp_settimanale INTEGER DEFAULT 0,
                        xp_mensile INTEGER DEFAULT 0,
                        xp_stagionale INTEGER DEFAULT 0,
                        xp_lifetime INTEGER DEFAULT 0,
                        posizione_classe INTEGER,
                        posizione_scuola INTEGER,
                        posizione_stagionale INTEGER,
                        messaggi_totali INTEGER DEFAULT 0,
                        chatbot_totali INTEGER DEFAULT 0,
                        aiuti_totali INTEGER DEFAULT 0,
                        streak_attuale INTEGER DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # Kudos (peer recognition)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS kudos (
                        id {serial_type} PRIMARY KEY,
                        from_user_id INTEGER NOT NULL,
                        to_user_id INTEGER NOT NULL,
                        motivo TEXT NOT NULL,
                        xp_reward INTEGER DEFAULT 50,
                        reactions JSONB,
                        reactions_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # Power-ups definition
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS powerups (
                        id {serial_type} PRIMARY KEY,
                        codice VARCHAR(50) UNIQUE NOT NULL,
                        nome VARCHAR(100) NOT NULL,
                        descrizione TEXT,
                        tipo VARCHAR(50) NOT NULL,
                        effetto JSONB NOT NULL,
                        durata_minuti INTEGER,
                        costo_xp INTEGER DEFAULT 0,
                        costo_monete INTEGER DEFAULT 0,
                        disponibile BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # User power-ups (owned)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_powerups (
                        id {serial_type} PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        powerup_id INTEGER NOT NULL,
                        quantita INTEGER DEFAULT 1,
                        attivo BOOLEAN DEFAULT FALSE,
                        attivato_at TIMESTAMP,
                        scade_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # Notifications
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS gamification_notifications (
                        id {serial_type} PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        tipo VARCHAR(50) NOT NULL,
                        titolo VARCHAR(200) NOT NULL,
                        messaggio TEXT,
                        data JSONB,
                        letta BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # Events (special events)
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS gamification_events (
                        id {serial_type} PRIMARY KEY,
                        codice VARCHAR(50) UNIQUE NOT NULL,
                        nome VARCHAR(100) NOT NULL,
                        descrizione TEXT,
                        tipo VARCHAR(50) NOT NULL,
                        data_inizio TIMESTAMP NOT NULL,
                        data_fine TIMESTAMP NOT NULL,
                        attivo BOOLEAN DEFAULT FALSE,
                        xp_multiplier FLOAT DEFAULT 1.0,
                        rewards JSONB,
                        sfide_speciali JSONB,
                        created_at TIMESTAMP DEFAULT {timestamp_default}
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_xp_logs_user ON xp_logs(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_xp_logs_created ON xp_logs(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_challenges_user ON user_challenges_v2(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kudos_to_user ON kudos(to_user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_leaderboards_xp ON leaderboards_v2(xp_lifetime DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON gamification_notifications(user_id)')
                
                logger.info("Advanced gamification tables created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error creating advanced gamification tables: {e}")
            return False
    
    def seed_default_badges(self):
        """Seed default badges"""
        try:
            default_badges = [
                {'codice': 'chiacchierone', 'nome': '💬 Chiacchierone', 'descrizione': 'Invia 100 messaggi', 'rarita': 'comune', 'condizioni': {'messaggi_inviati': 100}, 'reward_xp': 100},
                {'codice': 'amico_ai', 'nome': '🤖 Amico dell\'AI', 'descrizione': '50 interazioni con il chatbot', 'rarita': 'comune', 'condizioni': {'chatbot_interazioni': 50}, 'reward_xp': 100},
                {'codice': 'helper', 'nome': '🤝 Helper', 'descrizione': 'Aiuta 10 compagni', 'rarita': 'raro', 'condizioni': {'compagni_aiutati': 10}, 'reward_xp': 200},
                {'codice': 'streak_7', 'nome': '🔥 Settimana Perfetta', 'descrizione': 'Streak di 7 giorni', 'rarita': 'raro', 'condizioni': {'streak_giorni': 7}, 'reward_xp': 200},
                {'codice': 'streak_30', 'nome': '💎 Mese Perfetto', 'descrizione': 'Streak di 30 giorni', 'rarita': 'epico', 'condizioni': {'streak_giorni': 30}, 'reward_xp': 500},
                {'codice': 'quiz_master', 'nome': '🏆 Maestro dei Quiz', 'descrizione': 'Completa 100 quiz', 'rarita': 'epico', 'condizioni': {'quiz_completati': 100}, 'reward_xp': 500},
                {'codice': 'perfectionist', 'nome': '⭐ Perfezionista', 'descrizione': '25 quiz perfetti', 'rarita': 'leggendario', 'condizioni': {'quiz_perfetti': 25}, 'reward_xp': 1000},
                {'codice': 'cavaliere', 'nome': '⚔️ Cavaliere', 'descrizione': 'Raggiungi il rango Cavaliere', 'rarita': 'comune', 'condizioni': {'rango': 'Cavaliere'}, 'reward_xp': 150},
                {'codice': 'leggenda', 'nome': '⭐ Leggenda', 'descrizione': 'Raggiungi il rango Leggenda', 'rarita': 'epico', 'condizioni': {'rango': 'Leggenda'}, 'reward_xp': 500},
                {'codice': 'immortale', 'nome': '🔥 Immortale', 'descrizione': 'Raggiungi il rango Immortale', 'rarita': 'leggendario', 'condizioni': {'rango': 'Immortale'}, 'reward_xp': 2000}
            ]
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                for badge in default_badges:
                    cursor.execute('''
                        INSERT INTO badges_v2 (codice, nome, descrizione, rarita, condizioni, reward_xp)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (codice) DO NOTHING
                    ''', (badge['codice'], badge['nome'], badge['descrizione'], 
                          badge['rarita'], json.dumps(badge['condizioni']), badge['reward_xp']))
                
                logger.info(f"Seeded {len(default_badges)} default badges")
                return True
                
        except Exception as e:
            logger.error(f"Error seeding badges: {e}")
            return False
    
    def seed_default_challenges(self):
        """Seed default challenges"""
        try:
            challenges = [
                # Daily challenges
                {'codice': 'daily_messages_5', 'nome': '📨 Messaggi del Giorno', 'descrizione': 'Invia 5 messaggi oggi', 'tipo': 'giornaliera', 'difficolta': 'facile', 'obiettivi': {'messaggi': 5}, 'reward_xp': 30},
                {'codice': 'daily_chatbot_3', 'nome': '🤖 Parla con SKAJLA', 'descrizione': '3 interazioni con il chatbot', 'tipo': 'giornaliera', 'difficolta': 'facile', 'obiettivi': {'chatbot_interazioni': 3}, 'reward_xp': 25},
                {'codice': 'daily_quiz_1', 'nome': '📝 Quiz Giornaliero', 'descrizione': 'Completa un quiz', 'tipo': 'giornaliera', 'difficolta': 'facile', 'obiettivi': {'quiz': 1}, 'reward_xp': 40},
                {'codice': 'daily_help_1', 'nome': '🤝 Aiuta un Compagno', 'descrizione': 'Aiuta un compagno oggi', 'tipo': 'giornaliera', 'difficolta': 'media', 'obiettivi': {'aiuti': 1}, 'reward_xp': 50},
                
                # Weekly challenges
                {'codice': 'weekly_messages_30', 'nome': '💬 Comunicatore', 'descrizione': 'Invia 30 messaggi questa settimana', 'tipo': 'settimanale', 'difficolta': 'facile', 'obiettivi': {'messaggi': 30}, 'reward_xp': 100},
                {'codice': 'weekly_chatbot_15', 'nome': '🧠 Studioso AI', 'descrizione': '15 interazioni chatbot', 'tipo': 'settimanale', 'difficolta': 'media', 'obiettivi': {'chatbot_interazioni': 15}, 'reward_xp': 150},
                {'codice': 'weekly_quiz_5', 'nome': '📚 Maratoneta Quiz', 'descrizione': 'Completa 5 quiz', 'tipo': 'settimanale', 'difficolta': 'media', 'obiettivi': {'quiz': 5}, 'reward_xp': 200},
                {'codice': 'weekly_streak', 'nome': '🔥 Costanza', 'descrizione': 'Mantieni lo streak per 7 giorni', 'tipo': 'settimanale', 'difficolta': 'difficile', 'obiettivi': {'streak_giorni': 7}, 'reward_xp': 300},
                {'codice': 'weekly_xp_500', 'nome': '⚡ XP Hunter', 'descrizione': 'Guadagna 500 XP', 'tipo': 'settimanale', 'difficolta': 'difficile', 'obiettivi': {'xp_accumulati': 500}, 'reward_xp': 250}
            ]
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                for ch in challenges:
                    cursor.execute('''
                        INSERT INTO challenges_v2 (codice, nome, descrizione, tipo, difficolta, obiettivi, reward_xp, attiva)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                        ON CONFLICT (codice) DO NOTHING
                    ''', (ch['codice'], ch['nome'], ch['descrizione'], ch['tipo'], 
                          ch['difficolta'], json.dumps(ch['obiettivi']), ch['reward_xp']))
                
                logger.info(f"Seeded {len(challenges)} default challenges")
                return True
                
        except Exception as e:
            logger.error(f"Error seeding challenges: {e}")
            return False
    
    def seed_default_powerups(self):
        """Seed default power-ups"""
        try:
            powerups = [
                {'codice': 'xp_boost_2x', 'nome': '⚡ XP Boost 2x', 'descrizione': 'Raddoppia gli XP per 30 minuti', 'tipo': 'moltiplicatore', 'effetto': {'xp_multiplier': 2.0}, 'durata_minuti': 30, 'costo_xp': 100},
                {'codice': 'xp_boost_3x', 'nome': '🔥 XP Boost 3x', 'descrizione': 'Triplica gli XP per 15 minuti', 'tipo': 'moltiplicatore', 'effetto': {'xp_multiplier': 3.0}, 'durata_minuti': 15, 'costo_xp': 200},
                {'codice': 'streak_shield', 'nome': '🛡️ Scudo Streak', 'descrizione': 'Proteggi lo streak per 1 giorno', 'tipo': 'protezione', 'effetto': {'streak_protection': True}, 'durata_minuti': 1440, 'costo_xp': 150},
                {'codice': 'second_chance', 'nome': '🔄 Seconda Possibilità', 'descrizione': 'Ripeti un quiz senza penalità', 'tipo': 'quiz', 'effetto': {'quiz_retry': True}, 'durata_minuti': None, 'costo_xp': 75}
            ]
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                for pu in powerups:
                    cursor.execute('''
                        INSERT INTO powerups (codice, nome, descrizione, tipo, effetto, durata_minuti, costo_xp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (codice) DO NOTHING
                    ''', (pu['codice'], pu['nome'], pu['descrizione'], pu['tipo'],
                          json.dumps(pu['effetto']), pu['durata_minuti'], pu['costo_xp']))
                
                logger.info(f"Seeded {len(powerups)} default power-ups")
                return True
                
        except Exception as e:
            logger.error(f"Error seeding power-ups: {e}")
            return False


# Singleton instance
advanced_gamification = AdvancedGamificationManager()
