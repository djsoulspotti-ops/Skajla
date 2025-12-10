"""
XP Manager V2 - Advanced XP calculation and assignment
Adapted for SKAJLA's DatabaseManager pattern
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from services.database.database_manager import db_manager
from services.gamification.advanced_gamification import (
    XP_CONFIG, RANK_CONFIG, RANK_ORDER, calcola_rango, xp_per_prossimo_rango
)
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)


class XPManagerV2:
    """Manages all XP-related operations"""
    
    def __init__(self):
        self.xp_config = XP_CONFIG
    
    # =========================================================================
    # CORE XP ASSIGNMENT
    # =========================================================================
    
    def assegna_xp(self, user_id: int, amount: int, source: str, 
                   description: str = "", metadata: Dict = None,
                   check_limits: bool = True, apply_multipliers: bool = True) -> Dict:
        """
        Assign XP to a user with all consequences (rank up, badges, etc.)
        
        Args:
            user_id: User ID
            amount: XP amount
            source: XP source ('messaggio', 'chatbot', 'sfida', etc.)
            description: Action description
            metadata: Extra info dict
            check_limits: Apply daily limits
            apply_multipliers: Apply active multipliers
        
        Returns:
            dict with operation info
        """
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get or create user gamification profile
                cursor.execute('''
                    SELECT id, xp_totale, xp_stagionale, xp_settimanale, xp_giornaliero,
                           rango, rango_max_raggiunto, streak_giorni
                    FROM user_gamification_v2 WHERE user_id = %s
                ''', (user_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    # Create new profile
                    cursor.execute('''
                        INSERT INTO user_gamification_v2 (user_id) VALUES (%s)
                        RETURNING id, xp_totale, xp_stagionale, xp_settimanale, xp_giornaliero,
                                  rango, rango_max_raggiunto, streak_giorni
                    ''', (user_id,))
                    row = cursor.fetchone()
                    
                    # Create leaderboard entry
                    cursor.execute('''
                        INSERT INTO leaderboards_v2 (user_id) VALUES (%s)
                        ON CONFLICT (user_id) DO NOTHING
                    ''', (user_id,))
                
                gam_id, xp_totale, xp_stag, xp_sett, xp_giorn, rango, rango_max, streak = row
                
                # Check daily limits
                if check_limits:
                    if not self._check_daily_limit(cursor, user_id, source, amount):
                        return {
                            'success': False,
                            'message': 'Limite giornaliero raggiunto per questa categoria',
                            'xp_assegnati': 0
                        }
                
                # Apply multipliers
                if apply_multipliers:
                    amount = self._apply_multipliers(cursor, user_id, amount)
                
                # Calculate new XP values
                old_rank = rango
                new_xp_totale = xp_totale + amount
                new_xp_stag = xp_stag + amount
                new_xp_sett = xp_sett + amount
                new_xp_giorn = xp_giorn + amount
                
                # Calculate new rank
                nuovo_rango = calcola_rango(new_xp_totale)
                rank_up = nuovo_rango != old_rank
                
                # Update max rank if needed
                new_rango_max = rango_max
                if rank_up:
                    old_idx = RANK_ORDER.index(old_rank) if old_rank in RANK_ORDER else 0
                    new_idx = RANK_ORDER.index(nuovo_rango) if nuovo_rango in RANK_ORDER else 0
                    max_idx = RANK_ORDER.index(rango_max) if rango_max in RANK_ORDER else 0
                    if new_idx > max_idx:
                        new_rango_max = nuovo_rango
                
                # Update user gamification
                cursor.execute('''
                    UPDATE user_gamification_v2 
                    SET xp_totale = %s, xp_stagionale = %s, xp_settimanale = %s, 
                        xp_giornaliero = %s, rango = %s, rango_max_raggiunto = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                ''', (new_xp_totale, new_xp_stag, new_xp_sett, new_xp_giorn,
                      nuovo_rango, new_rango_max, user_id))
                
                # Log XP transaction
                cursor.execute('''
                    INSERT INTO xp_logs (user_id, amount, source, description, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, amount, source, description, json.dumps(metadata or {})))
                
                # Update leaderboard
                self._update_leaderboard(cursor, user_id, amount)
                
                result = {
                    'success': True,
                    'xp_assegnati': amount,
                    'xp_totale': new_xp_totale,
                    'rango': nuovo_rango,
                    'rank_up': rank_up,
                    'nuovo_rango': nuovo_rango if rank_up else None
                }
                
                # Create rank up notification
                if rank_up:
                    self._create_rank_up_notification(cursor, user_id, nuovo_rango)
                
                # Check for badge unlocks
                badges_unlocked = self._check_badge_unlocks(cursor, user_id, new_xp_totale, nuovo_rango)
                if badges_unlocked:
                    result['badges_unlocked'] = badges_unlocked
                
                return result
                
        except Exception as e:
            logger.error(f"Error assigning XP: {e}")
            return {
                'success': False,
                'message': str(e),
                'xp_assegnati': 0
            }
    
    # =========================================================================
    # SPECIFIC ACTION METHODS
    # =========================================================================
    
    def xp_messaggio(self, user_id: int, is_primo_oggi: bool = False,
                     risposta_veloce: bool = False, con_emoji: bool = False,
                     gruppo: bool = False) -> Dict:
        """Assign XP for sending a message"""
        amount = self.xp_config['messaggio_base']
        descrizione = "Messaggio inviato"
        
        if is_primo_oggi:
            amount = self.xp_config['messaggio_primo_giorno']
            descrizione = "Primo messaggio del giorno"
        
        if risposta_veloce:
            amount += self.xp_config['messaggio_risposta_veloce']
            descrizione += " (risposta veloce)"
        
        if con_emoji:
            amount += self.xp_config['messaggio_con_emoji']
            descrizione += " (con emoji)"
        
        if gruppo:
            amount = self.xp_config['conversazione_gruppo']
            descrizione = "Conversazione di gruppo"
        
        # Update message count
        self._increment_stat(user_id, 'messaggi_inviati')
        
        return self.assegna_xp(
            user_id=user_id,
            amount=amount,
            source='messaggio',
            description=descrizione,
            metadata={'tipo': 'messaggio'}
        )
    
    def xp_chatbot(self, user_id: int, is_prima_oggi: bool = False,
                   conversazione_lunga: bool = False, per_studio: bool = False,
                   problema_risolto: bool = False) -> Dict:
        """Assign XP for chatbot interaction"""
        amount = self.xp_config['chatbot_domanda']
        descrizione = "Interazione chatbot"
        
        if is_prima_oggi:
            amount = self.xp_config['chatbot_prima_interazione']
            descrizione = "Prima interazione chatbot oggi"
        
        if conversazione_lunga:
            amount = self.xp_config['chatbot_conversazione_lunga']
            descrizione = "Conversazione lunga con chatbot"
        
        if per_studio:
            amount = self.xp_config['chatbot_studio']
            descrizione = "Uso chatbot per studio"
        
        if problema_risolto:
            amount = self.xp_config['chatbot_problema_risolto']
            descrizione = "Problema risolto con chatbot"
        
        # Update chatbot count
        self._increment_stat(user_id, 'chatbot_interazioni')
        
        return self.assegna_xp(
            user_id=user_id,
            amount=amount,
            source='chatbot',
            description=descrizione,
            metadata={'tipo': 'chatbot'}
        )
    
    def xp_quiz(self, user_id: int, perfetto: bool = False, buono: bool = False) -> Dict:
        """Assign XP for quiz completion"""
        if perfetto:
            amount = self.xp_config['quiz_perfetto']
            descrizione = "Quiz perfetto!"
            self._increment_stat(user_id, 'quiz_perfetti')
        elif buono:
            amount = self.xp_config['quiz_buono']
            descrizione = "Quiz completato con buon punteggio"
        else:
            amount = self.xp_config['quiz_completato']
            descrizione = "Quiz completato"
        
        self._increment_stat(user_id, 'quiz_completati')
        
        return self.assegna_xp(
            user_id=user_id,
            amount=amount,
            source='quiz',
            description=descrizione,
            metadata={'tipo': 'quiz', 'perfetto': perfetto}
        )
    
    def xp_aiuto_compagno(self, user_id: int, compagno_id: int) -> Dict:
        """Assign XP for helping a classmate"""
        self._increment_stat(user_id, 'compagni_aiutati')
        
        return self.assegna_xp(
            user_id=user_id,
            amount=self.xp_config['aiutare_compagno'],
            source='aiuto',
            description="Aiutato compagno",
            metadata={'compagno_id': compagno_id}
        )
    
    def xp_reaction_ricevuta(self, user_id: int) -> Dict:
        """Assign XP for received reaction"""
        self._increment_stat(user_id, 'reactions_ricevute')
        
        return self.assegna_xp(
            user_id=user_id,
            amount=self.xp_config['reaction_ricevuta'],
            source='reaction',
            description="Reaction ricevuta",
            check_limits=False
        )
    
    def xp_sfida_completata(self, user_id: int, challenge_id: int, reward_xp: int) -> Dict:
        """Assign XP for challenge completion"""
        return self.assegna_xp(
            user_id=user_id,
            amount=reward_xp,
            source='sfida',
            description="Sfida completata",
            metadata={'challenge_id': challenge_id},
            check_limits=False
        )
    
    def xp_streak_bonus(self, user_id: int, streak_giorni: int) -> Dict:
        """Assign streak bonus XP"""
        amount = 0
        descrizione = ""
        
        if streak_giorni == 3:
            amount = self.xp_config['streak_3_giorni']
            descrizione = "Streak 3 giorni"
        elif streak_giorni == 7:
            amount = self.xp_config['streak_7_giorni']
            descrizione = "Streak 7 giorni"
        elif streak_giorni == 14:
            amount = self.xp_config['streak_14_giorni']
            descrizione = "Streak 14 giorni"
        elif streak_giorni == 30:
            amount = self.xp_config['streak_30_giorni']
            descrizione = "Streak 30 giorni"
        
        if amount > 0:
            return self.assegna_xp(
                user_id=user_id,
                amount=amount,
                source='streak',
                description=descrizione,
                metadata={'streak_giorni': streak_giorni},
                check_limits=False
            )
        
        return {'success': False, 'message': 'Streak non valido per bonus'}
    
    # =========================================================================
    # USER STATS & PROFILE
    # =========================================================================
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get complete gamification profile for user"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT u.*, l.xp_giornaliero as lb_giorn, l.xp_settimanale as lb_sett,
                           l.xp_mensile as lb_mens, l.xp_lifetime,
                           l.posizione_classe, l.posizione_scuola, l.posizione_stagionale
                    FROM user_gamification_v2 u
                    LEFT JOIN leaderboards_v2 l ON u.user_id = l.user_id
                    WHERE u.user_id = %s
                ''', (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get badge count
                cursor.execute('''
                    SELECT COUNT(*) FROM user_badges_v2 WHERE user_id = %s
                ''', (user_id,))
                badge_count = cursor.fetchone()[0]
                
                # Calculate level progress
                rango = row[5]  # rango column
                xp_totale = row[2]  # xp_totale column
                xp_prossimo = xp_per_prossimo_rango(rango)
                
                rango_config = RANK_CONFIG.get(rango, RANK_CONFIG['Germoglio'])
                xp_start = rango_config['min_xp']
                xp_per_livello = xp_prossimo - xp_start
                xp_attuale_livello = xp_totale - xp_start
                progresso = int((xp_attuale_livello / xp_per_livello) * 100) if xp_per_livello > 0 else 100
                
                return {
                    'user_id': user_id,
                    'xp': {
                        'totale': row[2],
                        'stagionale': row[3],
                        'settimanale': row[4],
                        'giornaliero': row[5] if row[5] else 0,
                        'per_prossimo_livello': xp_prossimo,
                        'progresso_livello': progresso
                    },
                    'rango': {
                        'attuale': rango,
                        'icon': RANK_CONFIG.get(rango, {}).get('icon', '🌱'),
                        'color': RANK_CONFIG.get(rango, {}).get('color', '#90EE90'),
                        'max_raggiunto': row[6]
                    },
                    'streak': {
                        'attuale': row[7],
                        'massimo': row[8]
                    },
                    'statistiche': {
                        'messaggi_inviati': row[11],
                        'chatbot_interazioni': row[12],
                        'compagni_aiutati': row[13],
                        'gruppi_studio_creati': row[14],
                        'reactions_ricevute': row[15],
                        'quiz_completati': row[16],
                        'quiz_perfetti': row[17],
                        'badge_totali': badge_count
                    },
                    'personalizzazione': {
                        'avatar_id': row[18],
                        'tema_colore': row[19],
                        'titolo': row[20],
                        'cornice_profilo': row[21],
                        'effetto_messaggio': row[22],
                        'pet_id': row[23]
                    },
                    'battle_pass': {
                        'livello': row[10],
                        'premium': row[11] if len(row) > 11 else False
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get basic stats
                cursor.execute('''
                    SELECT xp_totale, rango, streak_giorni, messaggi_inviati,
                           chatbot_interazioni, compagni_aiutati, quiz_completati, quiz_perfetti
                    FROM user_gamification_v2 WHERE user_id = %s
                ''', (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get XP earned today
                cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) FROM xp_logs 
                    WHERE user_id = %s AND created_at::date = CURRENT_DATE
                ''', (user_id,))
                xp_oggi = cursor.fetchone()[0]
                
                # Get XP earned this week
                cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) FROM xp_logs 
                    WHERE user_id = %s AND created_at >= date_trunc('week', CURRENT_DATE)
                ''', (user_id,))
                xp_settimana = cursor.fetchone()[0]
                
                return {
                    'xp_totale': row[0],
                    'rango': row[1],
                    'streak': row[2],
                    'xp_oggi': xp_oggi,
                    'xp_settimana': xp_settimana,
                    'messaggi': row[3],
                    'chatbot': row[4],
                    'aiuti': row[5],
                    'quiz': row[6],
                    'quiz_perfetti': row[7]
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return None
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _check_daily_limit(self, cursor, user_id: int, source: str, amount: int) -> bool:
        """Check if user has reached daily limit for category"""
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM xp_logs 
            WHERE user_id = %s AND source = %s AND created_at::date = CURRENT_DATE
        ''', (user_id, source))
        
        xp_today = cursor.fetchone()[0]
        
        limits = {
            'messaggio': self.xp_config['max_xp_messaggi'],
            'chatbot': self.xp_config['max_xp_chatbot'],
            'quiz': self.xp_config['max_xp_quiz']
        }
        
        limit = limits.get(source)
        if limit:
            return (xp_today + amount) <= limit
        
        return True
    
    def _apply_multipliers(self, cursor, user_id: int, amount: int) -> int:
        """Apply active multipliers (power-ups, events)"""
        multiplier = 1.0
        
        # Check for active power-ups
        cursor.execute('''
            SELECT p.effetto FROM user_powerups up
            JOIN powerups p ON up.powerup_id = p.id
            WHERE up.user_id = %s AND up.attivo = TRUE 
            AND (up.scade_at IS NULL OR up.scade_at > CURRENT_TIMESTAMP)
        ''', (user_id,))
        
        for row in cursor.fetchall():
            effetto = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            if 'xp_multiplier' in effetto:
                multiplier *= effetto['xp_multiplier']
        
        # Check for active events
        cursor.execute('''
            SELECT xp_multiplier FROM gamification_events
            WHERE attivo = TRUE AND data_inizio <= CURRENT_TIMESTAMP 
            AND data_fine >= CURRENT_TIMESTAMP
        ''')
        
        for row in cursor.fetchall():
            if row[0] and row[0] > 1.0:
                multiplier *= row[0]
        
        return int(amount * multiplier)
    
    def _update_leaderboard(self, cursor, user_id: int, amount: int):
        """Update leaderboard entry"""
        cursor.execute('''
            UPDATE leaderboards_v2 
            SET xp_giornaliero = xp_giornaliero + %s,
                xp_settimanale = xp_settimanale + %s,
                xp_mensile = xp_mensile + %s,
                xp_stagionale = xp_stagionale + %s,
                xp_lifetime = xp_lifetime + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        ''', (amount, amount, amount, amount, amount, user_id))
    
    def _increment_stat(self, user_id: int, stat_name: str):
        """Increment a user statistic"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE user_gamification_v2 
                    SET {stat_name} = {stat_name} + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                ''', (user_id,))
        except Exception as e:
            logger.error(f"Error incrementing stat {stat_name}: {e}")
    
    def _create_rank_up_notification(self, cursor, user_id: int, nuovo_rango: str):
        """Create notification for rank up"""
        rango_config = RANK_CONFIG.get(nuovo_rango, {})
        cursor.execute('''
            INSERT INTO gamification_notifications (user_id, tipo, titolo, messaggio, data)
            VALUES (%s, 'rank_up', %s, %s, %s)
        ''', (user_id, f"Nuovo Rango: {nuovo_rango}!",
              f"Congratulazioni! Hai raggiunto il rango {nuovo_rango}!",
              json.dumps({'rango': nuovo_rango, 'icon': rango_config.get('icon', '🎖️')})))
    
    def _check_badge_unlocks(self, cursor, user_id: int, xp_totale: int, rango: str) -> List:
        """Check and unlock badges based on current stats"""
        unlocked = []
        
        # Get user stats
        cursor.execute('''
            SELECT messaggi_inviati, chatbot_interazioni, compagni_aiutati,
                   streak_giorni, quiz_completati, quiz_perfetti
            FROM user_gamification_v2 WHERE user_id = %s
        ''', (user_id,))
        
        stats = cursor.fetchone()
        if not stats:
            return unlocked
        
        user_stats = {
            'messaggi_inviati': stats[0],
            'chatbot_interazioni': stats[1],
            'compagni_aiutati': stats[2],
            'streak_giorni': stats[3],
            'quiz_completati': stats[4],
            'quiz_perfetti': stats[5],
            'xp_totale': xp_totale,
            'rango': rango
        }
        
        # Get available badges not yet unlocked
        cursor.execute('''
            SELECT id, codice, nome, condizioni, reward_xp FROM badges_v2
            WHERE id NOT IN (SELECT badge_id FROM user_badges_v2 WHERE user_id = %s)
        ''', (user_id,))
        
        for badge_row in cursor.fetchall():
            badge_id, codice, nome, condizioni, reward_xp = badge_row
            
            if isinstance(condizioni, str):
                condizioni = json.loads(condizioni)
            
            # Check if all conditions are met
            unlocked_badge = True
            for key, value in condizioni.items():
                if key == 'rango':
                    # Special handling for rank conditions
                    if rango != value and RANK_ORDER.index(rango) < RANK_ORDER.index(value):
                        unlocked_badge = False
                        break
                elif user_stats.get(key, 0) < value:
                    unlocked_badge = False
                    break
            
            if unlocked_badge:
                # Unlock the badge
                cursor.execute('''
                    INSERT INTO user_badges_v2 (user_id, badge_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                ''', (user_id, badge_id))
                
                # Create notification
                cursor.execute('''
                    INSERT INTO gamification_notifications (user_id, tipo, titolo, messaggio, data)
                    VALUES (%s, 'badge', %s, %s, %s)
                ''', (user_id, f"Badge Sbloccato: {nome}!",
                      f"Hai sbloccato il badge {nome}!",
                      json.dumps({'badge_id': badge_id, 'codice': codice})))
                
                unlocked.append({'id': badge_id, 'codice': codice, 'nome': nome})
        
        return unlocked
    
    # =========================================================================
    # RESET METHODS
    # =========================================================================
    
    def reset_xp_giornaliero(self):
        """Reset daily XP for all users (run at midnight)"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_gamification_v2 SET xp_giornaliero = 0
                ''')
                cursor.execute('''
                    UPDATE leaderboards_v2 SET xp_giornaliero = 0
                ''')
                logger.info("Daily XP reset completed")
        except Exception as e:
            logger.error(f"Error resetting daily XP: {e}")
    
    def reset_xp_settimanale(self):
        """Reset weekly XP for all users (run on Monday midnight)"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_gamification_v2 SET xp_settimanale = 0
                ''')
                cursor.execute('''
                    UPDATE leaderboards_v2 SET xp_settimanale = 0
                ''')
                logger.info("Weekly XP reset completed")
        except Exception as e:
            logger.error(f"Error resetting weekly XP: {e}")


# Singleton instance
xp_manager_v2 = XPManagerV2()
