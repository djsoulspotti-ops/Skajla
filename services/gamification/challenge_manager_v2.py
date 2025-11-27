"""
Challenge Manager V2 - Manages daily, weekly, and class challenges
Adapted for SKAILA's DatabaseManager pattern
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
from services.database.database_manager import db_manager
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)


class ChallengeManagerV2:
    """Manages challenge assignment, validation, and completion"""
    
    def __init__(self):
        pass
    
    # =========================================================================
    # CHALLENGE ASSIGNMENT
    # =========================================================================
    
    def assegna_sfida_giornaliera(self, user_id: int) -> Dict:
        """Assign a random daily challenge to user"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user already has a daily challenge today
                cursor.execute('''
                    SELECT uc.id, c.nome, c.descrizione, uc.progresso, c.obiettivi, c.reward_xp
                    FROM user_challenges_v2 uc
                    JOIN challenges_v2 c ON uc.challenge_id = c.id
                    WHERE uc.user_id = %s AND c.tipo = 'giornaliera' 
                    AND uc.assegnata_at::date = CURRENT_DATE
                ''', (user_id,))
                
                existing = cursor.fetchone()
                if existing:
                    return {
                        'success': False,
                        'message': 'Sfida giornaliera già assegnata oggi',
                        'challenge': {
                            'id': existing[0],
                            'nome': existing[1],
                            'descrizione': existing[2],
                            'progresso': existing[3],
                            'obiettivi': existing[4],
                            'reward_xp': existing[5]
                        }
                    }
                
                # Get available daily challenges
                cursor.execute('''
                    SELECT id, nome, descrizione, obiettivi, reward_xp, difficolta
                    FROM challenges_v2
                    WHERE tipo = 'giornaliera' AND attiva = TRUE
                    ORDER BY RANDOM() LIMIT 1
                ''')
                
                challenge = cursor.fetchone()
                if not challenge:
                    return {'success': False, 'message': 'Nessuna sfida disponibile'}
                
                challenge_id, nome, descrizione, obiettivi, reward_xp, difficolta = challenge
                
                # Initialize progress
                if isinstance(obiettivi, str):
                    obiettivi = json.loads(obiettivi)
                
                progresso = {k: 0 for k in obiettivi.keys()}
                
                # Create user challenge
                cursor.execute('''
                    INSERT INTO user_challenges_v2 (user_id, challenge_id, progresso)
                    VALUES (%s, %s, %s)
                    RETURNING id
                ''', (user_id, challenge_id, json.dumps(progresso)))
                
                uc_id = cursor.fetchone()[0]
                
                return {
                    'success': True,
                    'challenge': {
                        'id': uc_id,
                        'challenge_id': challenge_id,
                        'nome': nome,
                        'descrizione': descrizione,
                        'obiettivi': obiettivi,
                        'progresso': progresso,
                        'reward_xp': reward_xp,
                        'difficolta': difficolta,
                        'tipo': 'giornaliera'
                    }
                }
                
        except Exception as e:
            logger.error(f"Error assigning daily challenge: {e}")
            return {'success': False, 'message': str(e)}
    
    def assegna_sfide_settimanali(self, user_id: int) -> Dict:
        """Assign 3 weekly challenges (easy, medium, hard)"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean old uncompleted weekly challenges
                cursor.execute('''
                    DELETE FROM user_challenges_v2
                    WHERE user_id = %s AND challenge_id IN (
                        SELECT id FROM challenges_v2 WHERE tipo = 'settimanale'
                    ) AND completato = FALSE
                    AND assegnata_at < date_trunc('week', CURRENT_DATE)
                ''', (user_id,))
                
                sfide_assegnate = []
                
                for difficolta in ['facile', 'media', 'difficile']:
                    # Get a random challenge for this difficulty
                    cursor.execute('''
                        SELECT id, nome, descrizione, obiettivi, reward_xp
                        FROM challenges_v2
                        WHERE tipo = 'settimanale' AND difficolta = %s AND attiva = TRUE
                        AND id NOT IN (
                            SELECT challenge_id FROM user_challenges_v2
                            WHERE user_id = %s AND assegnata_at >= date_trunc('week', CURRENT_DATE)
                        )
                        ORDER BY RANDOM() LIMIT 1
                    ''', (difficolta, user_id))
                    
                    challenge = cursor.fetchone()
                    if challenge:
                        challenge_id, nome, descrizione, obiettivi, reward_xp = challenge
                        
                        if isinstance(obiettivi, str):
                            obiettivi = json.loads(obiettivi)
                        
                        progresso = {k: 0 for k in obiettivi.keys()}
                        
                        cursor.execute('''
                            INSERT INTO user_challenges_v2 (user_id, challenge_id, progresso)
                            VALUES (%s, %s, %s)
                            RETURNING id
                        ''', (user_id, challenge_id, json.dumps(progresso)))
                        
                        uc_id = cursor.fetchone()[0]
                        
                        sfide_assegnate.append({
                            'id': uc_id,
                            'challenge_id': challenge_id,
                            'nome': nome,
                            'descrizione': descrizione,
                            'obiettivi': obiettivi,
                            'progresso': progresso,
                            'reward_xp': reward_xp,
                            'difficolta': difficolta
                        })
                
                return {
                    'success': True,
                    'message': f'{len(sfide_assegnate)} sfide settimanali assegnate',
                    'challenges': sfide_assegnate
                }
                
        except Exception as e:
            logger.error(f"Error assigning weekly challenges: {e}")
            return {'success': False, 'message': str(e)}
    
    # =========================================================================
    # CHALLENGE RETRIEVAL
    # =========================================================================
    
    def get_sfida_giornaliera(self, user_id: int) -> Optional[Dict]:
        """Get today's daily challenge for user"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT uc.id, uc.challenge_id, c.nome, c.descrizione, 
                           uc.progresso, c.obiettivi, c.reward_xp, c.difficolta,
                           uc.completato, uc.assegnata_at
                    FROM user_challenges_v2 uc
                    JOIN challenges_v2 c ON uc.challenge_id = c.id
                    WHERE uc.user_id = %s AND c.tipo = 'giornaliera'
                    AND uc.assegnata_at::date = CURRENT_DATE
                ''', (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                obiettivi = row[5] if isinstance(row[5], dict) else json.loads(row[5])
                progresso = row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else {}
                
                return {
                    'id': row[0],
                    'challenge_id': row[1],
                    'nome': row[2],
                    'descrizione': row[3],
                    'progresso': progresso,
                    'obiettivi': obiettivi,
                    'reward_xp': row[6],
                    'difficolta': row[7],
                    'completato': row[8],
                    'assegnata_at': row[9].isoformat() if row[9] else None,
                    'tipo': 'giornaliera'
                }
                
        except Exception as e:
            logger.error(f"Error getting daily challenge: {e}")
            return None
    
    def get_sfide_settimanali(self, user_id: int) -> List[Dict]:
        """Get this week's challenges for user"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT uc.id, uc.challenge_id, c.nome, c.descrizione, 
                           uc.progresso, c.obiettivi, c.reward_xp, c.difficolta,
                           uc.completato, uc.assegnata_at
                    FROM user_challenges_v2 uc
                    JOIN challenges_v2 c ON uc.challenge_id = c.id
                    WHERE uc.user_id = %s AND c.tipo = 'settimanale'
                    AND uc.assegnata_at >= date_trunc('week', CURRENT_DATE)
                    ORDER BY c.difficolta
                ''', (user_id,))
                
                sfide = []
                for row in cursor.fetchall():
                    obiettivi = row[5] if isinstance(row[5], dict) else json.loads(row[5])
                    progresso = row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else {}
                    
                    sfide.append({
                        'id': row[0],
                        'challenge_id': row[1],
                        'nome': row[2],
                        'descrizione': row[3],
                        'progresso': progresso,
                        'obiettivi': obiettivi,
                        'reward_xp': row[6],
                        'difficolta': row[7],
                        'completato': row[8],
                        'assegnata_at': row[9].isoformat() if row[9] else None,
                        'tipo': 'settimanale'
                    })
                
                return sfide
                
        except Exception as e:
            logger.error(f"Error getting weekly challenges: {e}")
            return []
    
    def get_sfide_attive(self, user_id: int) -> Dict:
        """Get all active challenges for user"""
        return {
            'giornaliera': self.get_sfida_giornaliera(user_id),
            'settimanali': self.get_sfide_settimanali(user_id)
        }
    
    # =========================================================================
    # PROGRESS TRACKING
    # =========================================================================
    
    def aggiorna_progresso(self, user_id: int, action_type: str, action_data: Dict = None) -> List[Dict]:
        """
        Update progress for all active challenges based on user action
        
        Args:
            user_id: User ID
            action_type: Action type ('messaggio', 'chatbot', 'aiuto', 'quiz', etc.)
            action_data: Additional data {'count': 1, ...}
        
        Returns:
            List of completed challenges
        """
        if action_data is None:
            action_data = {'count': 1}
        
        completed_challenges = []
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get active challenges
                cursor.execute('''
                    SELECT uc.id, uc.challenge_id, c.nome, uc.progresso, 
                           c.obiettivi, c.reward_xp
                    FROM user_challenges_v2 uc
                    JOIN challenges_v2 c ON uc.challenge_id = c.id
                    WHERE uc.user_id = %s AND uc.completato = FALSE AND c.attiva = TRUE
                ''', (user_id,))
                
                for row in cursor.fetchall():
                    uc_id, challenge_id, nome, progresso, obiettivi, reward_xp = row
                    
                    progresso = progresso if isinstance(progresso, dict) else json.loads(progresso) if progresso else {}
                    obiettivi = obiettivi if isinstance(obiettivi, dict) else json.loads(obiettivi)
                    
                    # Map action types to objective keys
                    action_mapping = {
                        'messaggio': 'messaggi',
                        'chatbot': 'chatbot_interazioni',
                        'aiuto': 'aiuti',
                        'quiz': 'quiz',
                        'gruppo_studio': 'gruppi_studio',
                        'reaction': 'reactions',
                        'xp': 'xp_accumulati',
                        'streak': 'streak_giorni'
                    }
                    
                    obiettivo_key = action_mapping.get(action_type)
                    if obiettivo_key and obiettivo_key in obiettivi:
                        # Update progress
                        current = progresso.get(obiettivo_key, 0)
                        increment = action_data.get('count', 1)
                        progresso[obiettivo_key] = current + increment
                        
                        # Check if challenge is completed
                        is_completed = all(
                            progresso.get(k, 0) >= v 
                            for k, v in obiettivi.items()
                        )
                        
                        # Update database
                        if is_completed:
                            cursor.execute('''
                                UPDATE user_challenges_v2 
                                SET progresso = %s, completato = TRUE, 
                                    completata_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            ''', (json.dumps(progresso), uc_id))
                            
                            completed_challenges.append({
                                'id': uc_id,
                                'challenge_id': challenge_id,
                                'nome': nome,
                                'reward_xp': reward_xp
                            })
                        else:
                            cursor.execute('''
                                UPDATE user_challenges_v2 
                                SET progresso = %s
                                WHERE id = %s
                            ''', (json.dumps(progresso), uc_id))
                
                # Distribute rewards for completed challenges
                for challenge in completed_challenges:
                    self._distribute_reward(cursor, user_id, challenge)
                
                return completed_challenges
                
        except Exception as e:
            logger.error(f"Error updating challenge progress: {e}")
            return []
    
    def _distribute_reward(self, cursor, user_id: int, challenge: Dict):
        """Distribute rewards for completed challenge"""
        from services.gamification.xp_manager_v2 import xp_manager_v2
        
        # Award XP
        xp_manager_v2.xp_sfida_completata(
            user_id=user_id,
            challenge_id=challenge['challenge_id'],
            reward_xp=challenge['reward_xp']
        )
        
        # Create notification
        cursor.execute('''
            INSERT INTO gamification_notifications (user_id, tipo, titolo, messaggio, data)
            VALUES (%s, 'challenge', %s, %s, %s)
        ''', (user_id, f"Sfida Completata: {challenge['nome']}!",
              f"Hai completato la sfida e guadagnato {challenge['reward_xp']} XP!",
              json.dumps({'challenge_id': challenge['challenge_id'], 
                         'reward_xp': challenge['reward_xp']})))
    
    # =========================================================================
    # GLOBAL ASSIGNMENT (for scheduler)
    # =========================================================================
    
    def assegna_sfide_giornaliere_globale(self):
        """Assign daily challenges to all users (run at midnight)"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all active users (logged in last 7 days)
                cursor.execute('''
                    SELECT DISTINCT user_id FROM user_gamification_v2
                    WHERE ultimo_accesso > CURRENT_TIMESTAMP - INTERVAL '7 days'
                ''')
                
                users = [row[0] for row in cursor.fetchall()]
                
                for user_id in users:
                    self.assegna_sfida_giornaliera(user_id)
                
                logger.info(f"Daily challenges assigned to {len(users)} users")
                
        except Exception as e:
            logger.error(f"Error in global daily challenge assignment: {e}")
    
    def assegna_sfide_settimanali_globale(self):
        """Assign weekly challenges to all users (run on Monday)"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all active users
                cursor.execute('''
                    SELECT DISTINCT user_id FROM user_gamification_v2
                    WHERE ultimo_accesso > CURRENT_TIMESTAMP - INTERVAL '7 days'
                ''')
                
                users = [row[0] for row in cursor.fetchall()]
                
                for user_id in users:
                    self.assegna_sfide_settimanali(user_id)
                
                logger.info(f"Weekly challenges assigned to {len(users)} users")
                
        except Exception as e:
            logger.error(f"Error in global weekly challenge assignment: {e}")


# Singleton instance
challenge_manager_v2 = ChallengeManagerV2()
