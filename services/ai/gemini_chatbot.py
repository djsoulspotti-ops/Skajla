"""
SKAILA Gemini Chatbot - AI Coach with Gamification Integration
Uses Google Gemini API for intelligent tutoring with XP rewards
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from google import genai
from google.genai import types
from services.database.database_manager import DatabaseManager
from services.gamification.xp_manager_v2 import XPManagerV2
from services.gamification.challenge_manager_v2 import ChallengeManagerV2
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)
db_manager = DatabaseManager()


class GeminiChatbot:
    """
    AI Chatbot powered by Google Gemini with gamification integration.
    Awards XP for learning interactions and provides personalized tutoring.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.xp_manager = XPManagerV2()
        self.challenge_manager = ChallengeManagerV2()
        self.gemini_available = False
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.gemini_available = True
                logger.info(
                    event_type='gemini_chatbot_initialized',
                    domain='ai',
                    message='Gemini chatbot initialized successfully'
                )
            except Exception as e:
                logger.error(
                    event_type='gemini_init_failed',
                    domain='ai',
                    error=str(e),
                    exc_info=True
                )
        else:
            logger.warning(
                event_type='gemini_api_key_missing',
                domain='ai',
                message='GEMINI_API_KEY not found - running in mock mode'
            )
    
    def _get_gamification_context(self, user_id: int) -> Dict[str, Any]:
        """Get user's gamification data for personalized responses"""
        try:
            profile = self.xp_manager.get_user_profile(user_id)
            if profile:
                return {
                    'rank': profile.get('rank', 'Germoglio'),
                    'xp_total': profile.get('xp_total', 0),
                    'xp_to_next': profile.get('xp_to_next_rank', 100),
                    'streak_days': profile.get('streak_days', 0),
                    'badges_count': profile.get('badges_count', 0),
                    'challenges_completed': profile.get('challenges_completed', 0)
                }
        except Exception as e:
            logger.warning(
                event_type='gamification_context_failed',
                domain='ai',
                user_id=user_id,
                error=str(e)
            )
        return {}
    
    def _get_user_name(self, user_id: int) -> str:
        """Get user's first name from database"""
        try:
            user = db_manager.query(
                'SELECT nome FROM utenti WHERE id = %s',
                (user_id,),
                one=True
            )
            if user and isinstance(user, dict):
                return user.get('nome', 'Studente')
            return 'Studente'
        except Exception:
            return 'Studente'
    
    def _build_system_prompt(self, user_name: str, gamification: Dict) -> str:
        """Build personalized system prompt with gamification context"""
        rank = gamification.get('rank', 'Germoglio')
        xp_total = gamification.get('xp_total', 0)
        streak = gamification.get('streak_days', 0)
        badges = gamification.get('badges_count', 0)
        
        return f"""Sei SKAILA Coach, un tutor AI amichevole e motivazionale per studenti italiani.

CONTESTO STUDENTE:
- Nome: {user_name}
- Rango attuale: {rank} (XP totali: {xp_total})
- Streak attivo: {streak} giorni consecutivi
- Badge guadagnati: {badges}

LINEE GUIDA:
1. Rispondi sempre in italiano con tono amichevole e incoraggiante
2. Celebra i progressi dello studente (rango, streak, badge)
3. Dai consigli pratici e actionable per lo studio
4. Se lo studente chiede aiuto su una materia, spiega in modo chiaro con esempi
5. Motiva lo studente a continuare il percorso gamificato
6. Usa emoji occasionalmente per rendere le risposte piu coinvolgenti
7. NON usare asterischi o markdown - scrivi in testo semplice e naturale
8. Usa elenchi puntati con trattino (-) invece di asterischi
9. Se lo studente sembra stressato, offri supporto emotivo prima di consigli pratici

GAMIFICATION:
- Ricorda allo studente che sta guadagnando XP per questa conversazione
- Se ha uno streak attivo, incoraggialo a mantenerlo
- Suggerisci sfide e obiettivi quando appropriato

Rispondi come un amico esperto che vuole davvero aiutare lo studente a migliorare."""
    
    def generate_response(self, message: str, user_id: int, 
                         user_name: Optional[str] = None, user_role: str = 'studente') -> Dict[str, Any]:
        """
        Generate AI response with gamification integration.
        Awards XP and returns personalized response.
        """
        if not user_name:
            user_name = self._get_user_name(user_id)
        
        gamification = self._get_gamification_context(user_id)
        
        if self.gemini_available and self.client:
            try:
                system_prompt = self._build_system_prompt(user_name, gamification)
                
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7,
                        max_output_tokens=2048,
                        top_p=0.95
                    )
                )
                
                ai_response = response.text or self._get_fallback_response(user_name, gamification)
                
                xp_result = self._award_chat_xp(user_id, message, ai_response)
                
                updated_gamification = self._get_gamification_context(user_id)
                
                logger.info(
                    event_type='gemini_response_generated',
                    domain='ai',
                    user_id=user_id,
                    message_length=len(message),
                    response_length=len(ai_response),
                    xp_awarded=xp_result.get('xp_assegnati', 0)
                )
                
                return {
                    'success': True,
                    'response': ai_response,
                    'xp_awarded': xp_result.get('xp_assegnati', 0),
                    'rank_up': xp_result.get('rank_up', False),
                    'new_rank': xp_result.get('nuovo_rango'),
                    'gamification': updated_gamification,
                    'ai_mode': 'gemini'
                }
                
            except Exception as e:
                logger.error(
                    event_type='gemini_response_failed',
                    domain='ai',
                    user_id=user_id,
                    error=str(e),
                    exc_info=True
                )
                return self._mock_response(message, user_name, user_id, gamification)
        else:
            return self._mock_response(message, user_name, user_id, gamification)
    
    def _award_chat_xp(self, user_id: int, message: str, response: str) -> Dict:
        """Award XP based on chat interaction quality and update gamification"""
        try:
            is_study_related = any(word in message.lower() for word in [
                'studio', 'esame', 'materia', 'compiti', 'lezione',
                'matematica', 'italiano', 'storia', 'scienze', 'inglese',
                'fisica', 'chimica', 'aiuto', 'capire', 'spiegami',
                'latino', 'filosofia', 'geografia', 'quiz', 'test'
            ])
            
            is_long_conversation = len(message) > 100
            
            is_first_today = self._is_first_interaction_today(user_id)
            
            xp_result = self.xp_manager.xp_chatbot(
                user_id=user_id,
                is_prima_oggi=is_first_today,
                conversazione_lunga=is_long_conversation,
                per_studio=is_study_related
            )
            
            self._update_streak(user_id)
            
            self._update_challenge_progress(user_id, 'chatbot_interazioni', 1)
            
            return xp_result
        except Exception as e:
            logger.warning(
                event_type='xp_award_failed',
                domain='ai',
                user_id=user_id,
                error=str(e)
            )
            return {'xp_assegnati': 0, 'success': False}
    
    def _update_streak(self, user_id: int):
        """Update user's streak on daily interaction"""
        try:
            db_manager.execute('''
                UPDATE user_gamification_v2 
                SET streak_giorni = CASE 
                    WHEN DATE(ultimo_accesso) = CURRENT_DATE - INTERVAL '1 day' 
                    THEN streak_giorni + 1
                    WHEN DATE(ultimo_accesso) = CURRENT_DATE 
                    THEN streak_giorni
                    ELSE 1
                END,
                streak_max = GREATEST(streak_max, CASE 
                    WHEN DATE(ultimo_accesso) = CURRENT_DATE - INTERVAL '1 day' 
                    THEN streak_giorni + 1
                    WHEN DATE(ultimo_accesso) = CURRENT_DATE 
                    THEN streak_giorni
                    ELSE 1
                END),
                ultimo_accesso = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (user_id,))
        except Exception as e:
            logger.warning(
                event_type='streak_update_failed',
                domain='ai',
                user_id=user_id,
                error=str(e)
            )
    
    def _update_challenge_progress(self, user_id: int, action_type: str, amount: int = 1) -> None:
        """Update progress on active challenges based on action type"""
        try:
            challenges_result = db_manager.query('''
                SELECT uc.id, uc.progresso, c.obiettivi, c.reward_xp
                FROM user_challenges_v2 uc
                JOIN challenges_v2 c ON uc.challenge_id = c.id
                WHERE uc.user_id = %s AND uc.completato = FALSE
            ''', (user_id,))
            
            if not challenges_result or not isinstance(challenges_result, list):
                return
            
            for challenge in challenges_result:
                if not isinstance(challenge, dict):
                    continue
                    
                raw_progresso = challenge.get('progresso')
                raw_obiettivi = challenge.get('obiettivi')
                
                progresso: Dict[str, Any] = raw_progresso if isinstance(raw_progresso, dict) else {}
                obiettivi: Dict[str, Any] = raw_obiettivi if isinstance(raw_obiettivi, dict) else {}
                
                if action_type in obiettivi:
                    current = progresso.get(action_type, 0)
                    new_value = current + amount
                    progresso[action_type] = new_value
                    
                    completed = all(
                        progresso.get(k, 0) >= v 
                        for k, v in obiettivi.items()
                    )
                    
                    challenge_id = challenge.get('id')
                    reward_xp = challenge.get('reward_xp', 0)
                    
                    db_manager.execute('''
                        UPDATE user_challenges_v2 
                        SET progresso = %s, completato = %s, completata_at = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END
                        WHERE id = %s
                    ''', (json.dumps(progresso), completed, completed, challenge_id))
                    
                    if completed and isinstance(reward_xp, int):
                        self.xp_manager.assegna_xp(
                            user_id=user_id,
                            amount=reward_xp,
                            source='sfida_completata',
                            description='Sfida completata!'
                        )
                        logger.info(
                            event_type='challenge_completed',
                            domain='gamification',
                            user_id=user_id,
                            challenge_id=challenge_id,
                            reward_xp=reward_xp
                        )
        except Exception as e:
            logger.warning(
                event_type='challenge_progress_update_failed',
                domain='ai',
                user_id=user_id,
                error=str(e)
            )
    
    def _is_first_interaction_today(self, user_id: int) -> bool:
        """Check if this is user's first chatbot interaction today"""
        try:
            result = db_manager.query('''
                SELECT COUNT(*) as count FROM xp_logs
                WHERE user_id = %s 
                  AND source = 'chatbot'
                  AND DATE(created_at) = CURRENT_DATE
            ''', (user_id,), one=True)
            if result and isinstance(result, dict):
                return result.get('count', 0) == 0
            return True
        except Exception:
            return False
    
    def _get_fallback_response(self, user_name: str, gamification: Dict) -> str:
        """Fallback response when Gemini fails"""
        rank = gamification.get('rank', 'Germoglio')
        streak = gamification.get('streak_days', 0)
        
        base = f"Ciao {user_name}! Come {rank}, stai facendo grandi progressi. "
        
        if streak > 0:
            base += f"Complimenti per il tuo streak di {streak} giorni! "
        
        base += "Come posso aiutarti oggi con lo studio?"
        return base
    
    def _mock_response(self, message: str, user_name: str, user_id: int, 
                       gamification: Dict) -> Dict[str, Any]:
        """Generate mock response when Gemini is not available"""
        rank = gamification.get('rank', 'Germoglio')
        streak = gamification.get('streak_days', 0)
        xp_total = gamification.get('xp_total', 0)
        
        responses = {
            'studio': f"Ciao {user_name}! Come {rank} con {xp_total} XP, hai dimostrato grande impegno. Per studiare meglio, ti consiglio: 1) Dividi lo studio in sessioni di 25 minuti 2) Fai pause regolari 3) Usa schemi e mappe concettuali. Ogni domanda che mi fai ti fa guadagnare XP!",
            'aiuto': f"Sono qui per aiutarti, {user_name}! Il tuo rango {rank} dimostra che sei sulla strada giusta. Dimmi di piu su cosa ti serve e insieme troveremo la soluzione. Ricorda: chiedere aiuto e da studenti intelligenti!",
            'stress': f"{user_name}, capisco che a volte lo studio puo essere stressante. Ma guarda quanta strada hai fatto: sei un {rank}! Prenditi un momento per respirare, poi torniamo a lavorare insieme. Sei piu forte di quanto pensi.",
            'default': f"Ciao {user_name}! Sono SKAILA Coach, il tuo tutor AI. Come {rank}, hai gia accumulato {xp_total} XP - ottimo lavoro! Chiedimi qualsiasi cosa sullo studio e guadagnerai altri punti esperienza."
        }
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['studio', 'studiare', 'esame', 'compiti']):
            response = responses['studio']
        elif any(word in message_lower for word in ['aiuto', 'aiutami', 'help']):
            response = responses['aiuto']
        elif any(word in message_lower for word in ['stress', 'ansia', 'difficile', 'non ce la faccio']):
            response = responses['stress']
        else:
            response = responses['default']
        
        if streak > 0:
            response += f" PS: Il tuo streak di {streak} giorni e fantastico!"
        
        xp_result = self._award_chat_xp(user_id, message, response)
        
        updated_gamification = self._get_gamification_context(user_id)
        
        return {
            'success': True,
            'response': response,
            'xp_awarded': xp_result.get('xp_assegnati', 0),
            'rank_up': xp_result.get('rank_up', False),
            'new_rank': xp_result.get('nuovo_rango'),
            'gamification': updated_gamification,
            'ai_mode': 'mock'
        }
    
    def get_study_suggestions(self, user_id: int) -> list:
        """Get personalized study suggestions based on gamification data"""
        gamification = self._get_gamification_context(user_id)
        
        suggestions = [
            "Come posso migliorare il mio metodo di studio?",
            "Dammi consigli per gestire lo stress pre-esame",
            "Come posso organizzare meglio il mio tempo?"
        ]
        
        if gamification.get('streak_days', 0) > 0:
            suggestions.append(f"Come posso mantenere il mio streak di {gamification['streak_days']} giorni?")
        
        if gamification.get('xp_total', 0) > 500:
            suggestions.append("Quali sfide avanzate mi consigli per il mio livello?")
        
        return suggestions


gemini_chatbot = GeminiChatbot()

__all__ = ['GeminiChatbot', 'gemini_chatbot']
