"""
SKAILA AI Cost Manager - Sistema di tracciamento e ottimizzazione costi AI
Gestisce budget, cache intelligente, e ottimizzazione modelli OpenAI
Refactored per PostgreSQL con db_manager
"""

from database_manager import db_manager
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
from shared.error_handling import get_logger, log_ai_request

logger = get_logger(__name__)

class AICostManager:
    def __init__(self):
        self.daily_budget_limit = 10.0  # $10 al giorno
        self.monthly_budget_limit = 200.0  # $200 al mese
        self.cache_duration_hours = 24  # Cache risposte per 24h
        
        # Inizializza tabelle di tracking
        self.init_cost_tracking_tables()
        
    def init_cost_tracking_tables(self):
        """Inizializza tabelle per tracking costi e cache"""
        try:
            # Tabella per tracking costi
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS ai_cost_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
                    model_used VARCHAR(50),
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cost_usd DECIMAL(10, 6),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    request_type VARCHAR(50),
                    cached BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Tabella per cache intelligente
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS ai_response_cache (
                    id SERIAL PRIMARY KEY,
                    request_hash VARCHAR(32) UNIQUE,
                    user_context_hash VARCHAR(32),
                    message TEXT,
                    response TEXT,
                    model_used VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hit_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabella per budget limits per utente
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS ai_user_limits (
                    user_id INTEGER PRIMARY KEY REFERENCES utenti(id) ON DELETE CASCADE,
                    daily_limit DECIMAL(10, 2) DEFAULT 2.0,
                    monthly_limit DECIMAL(10, 2) DEFAULT 30.0,
                    current_daily_usage DECIMAL(10, 6) DEFAULT 0.0,
                    current_monthly_usage DECIMAL(10, 6) DEFAULT 0.0,
                    last_reset_daily DATE,
                    last_reset_monthly DATE
                )
            ''')
            
            # Indici per ottimizzazione query
            db_manager.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_cost_user_timestamp 
                ON ai_cost_tracking(user_id, timestamp DESC)
            ''')
            
            db_manager.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_cache_hash 
                ON ai_response_cache(request_hash)
            ''')
            
            db_manager.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_cache_timestamp 
                ON ai_response_cache(timestamp DESC)
            ''')
            
            logger.info(
                event_type='ai_cost_tables_initialized',
                message='Tabelle AI Cost Manager inizializzate (PostgreSQL)',
                domain='ai'
            )
            
        except Exception as e:
            logger.error(
                event_type='ai_cost_tables_init_failed',
                message='Errore inizializzazione tabelle AI Cost Manager',
                domain='ai',
                error=str(e),
                exc_info=True
            )

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calcola il costo per una richiesta OpenAI"""
        costs = {
            'gpt-4': {
                'input': 0.03 / 1000,  # $0.03 per 1K token
                'output': 0.06 / 1000  # $0.06 per 1K token
            },
            'gpt-4o': {
                'input': 0.0025 / 1000,  # $0.0025 per 1K token
                'output': 0.01 / 1000    # $0.01 per 1K token
            },
            'gpt-3.5-turbo': {
                'input': 0.0015 / 1000,  # $0.0015 per 1K token
                'output': 0.002 / 1000   # $0.002 per 1K token
            }
        }
        
        if model not in costs:
            model = 'gpt-3.5-turbo'  # Default
            
        cost = (input_tokens * costs[model]['input'] + 
                output_tokens * costs[model]['output'])
        return round(cost, 6)

    def estimate_tokens(self, text: str) -> int:
        """Stima il numero di token (approssimativo)"""
        # Regola approssimativa: 1 token ≈ 4 caratteri per l'inglese
        # Per l'italiano, usiamo 1 token ≈ 3.5 caratteri
        return max(1, len(text) // 3)

    def generate_request_hash(self, message: str, user_context: str) -> str:
        """Genera hash per identificare richieste simili"""
        # Normalizza il messaggio
        normalized_msg = message.lower().strip()
        combined = f"{normalized_msg}|{user_context}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_cached_response(self, message: str, user_context: str) -> Optional[str]:
        """Cerca una risposta nella cache"""
        try:
            request_hash = self.generate_request_hash(message, user_context)
            
            # Cerca nella cache (non più vecchia di cache_duration_hours)
            cached = db_manager.query('''
                SELECT response, id FROM ai_response_cache 
                WHERE request_hash = %s 
                AND timestamp > NOW() - INTERVAL '1 hour' * %s
                ORDER BY hit_count DESC, last_accessed DESC
                LIMIT 1
            ''', (request_hash, self.cache_duration_hours), one=True)
            
            if cached:
                response = cached.get('response')
                cache_id = cached.get('id')
                
                # Aggiorna statistiche cache
                db_manager.execute('''
                    UPDATE ai_response_cache 
                    SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (cache_id,))
                
                logger.info(
                    event_type='ai_cache_hit',
                    message=f'Cache hit per richiesta: {message[:30]}...',
                    domain='ai',
                    request_hash=request_hash,
                    cache_id=cache_id
                )
                return response
                
            return None
            
        except Exception as e:
            logger.error(
                event_type='ai_cache_lookup_failed',
                message='Errore durante lookup cache AI',
                domain='ai',
                error=str(e),
                request_preview=message[:30],
                exc_info=True
            )
            return None

    def cache_response(self, message: str, response: str, user_context: str, model_used: str):
        """Salva una risposta nella cache"""
        try:
            request_hash = self.generate_request_hash(message, user_context)
            user_context_hash = hashlib.md5(user_context.encode()).hexdigest()
            
            # Inserisci o aggiorna cache (PostgreSQL UPSERT)
            db_manager.execute('''
                INSERT INTO ai_response_cache 
                (request_hash, user_context_hash, message, response, model_used, timestamp, last_accessed)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (request_hash) DO UPDATE SET
                    response = EXCLUDED.response,
                    model_used = EXCLUDED.model_used,
                    timestamp = CURRENT_TIMESTAMP,
                    last_accessed = CURRENT_TIMESTAMP,
                    hit_count = ai_response_cache.hit_count + 1
            ''', (request_hash, user_context_hash, message, response, model_used))
            
            logger.info(
                event_type='ai_response_cached',
                message=f'Risposta salvata in cache: {message[:30]}...',
                domain='ai',
                request_hash=request_hash,
                model_used=model_used
            )
            
        except Exception as e:
            logger.error(
                event_type='ai_cache_save_failed',
                message='Errore durante salvataggio risposta in cache',
                domain='ai',
                error=str(e),
                request_preview=message[:30],
                model_used=model_used,
                exc_info=True
            )

    def check_budget_limits(self, user_id: int, estimated_cost: float) -> Tuple[bool, str]:
        """Controlla se l'utente può fare la richiesta senza superare i limiti"""
        try:
            # Ottieni o crea record budget utente
            user_limits = db_manager.query('''
                SELECT user_id, daily_limit, monthly_limit, current_daily_usage, 
                       current_monthly_usage, last_reset_daily, last_reset_monthly
                FROM ai_user_limits WHERE user_id = %s
            ''', (user_id,), one=True)
            
            today = datetime.now().date()
            current_month = today.replace(day=1)
            
            if not user_limits:
                # Crea record per nuovo utente
                db_manager.execute('''
                    INSERT INTO ai_user_limits 
                    (user_id, last_reset_daily, last_reset_monthly)
                    VALUES (%s, %s, %s)
                ''', (user_id, today, current_month))
                
                user_limits = db_manager.query('''
                    SELECT user_id, daily_limit, monthly_limit, current_daily_usage, 
                           current_monthly_usage, last_reset_daily, last_reset_monthly
                    FROM ai_user_limits WHERE user_id = %s
                ''', (user_id,), one=True)
            
            daily_limit = user_limits.get('daily_limit')
            monthly_limit = user_limits.get('monthly_limit')
            daily_usage = user_limits.get('current_daily_usage')
            monthly_usage = user_limits.get('current_monthly_usage')
            last_reset_daily = user_limits.get('last_reset_daily')
            last_reset_monthly = user_limits.get('last_reset_monthly')
            
            # Reset giornaliero se necessario
            if last_reset_daily != today:
                db_manager.execute('''
                    UPDATE ai_user_limits 
                    SET current_daily_usage = 0.0, last_reset_daily = %s
                    WHERE user_id = %s
                ''', (today, user_id))
                daily_usage = 0.0
            
            # Reset mensile se necessario
            if last_reset_monthly != current_month:
                db_manager.execute('''
                    UPDATE ai_user_limits 
                    SET current_monthly_usage = 0.0, last_reset_monthly = %s
                    WHERE user_id = %s
                ''', (current_month, user_id))
                monthly_usage = 0.0
            
            # Controlli limiti
            daily_usage = float(daily_usage) if daily_usage else 0.0
            monthly_usage = float(monthly_usage) if monthly_usage else 0.0
            daily_limit = float(daily_limit) if daily_limit else 2.0
            monthly_limit = float(monthly_limit) if monthly_limit else 30.0
            
            if daily_usage + estimated_cost > daily_limit:
                return False, f"Limite giornaliero superato (${daily_usage:.3f}/${daily_limit:.2f})"
            
            if monthly_usage + estimated_cost > monthly_limit:
                return False, f"Limite mensile superato (${monthly_usage:.2f}/${monthly_limit:.2f})"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(
                event_type='ai_budget_check_failed',
                message='Errore durante controllo limiti budget AI',
                domain='ai',
                error=str(e),
                user_id=user_id,
                estimated_cost=estimated_cost,
                exc_info=True
            )
            return True, "Errore controllo budget"

    def should_use_premium_model(self, user_profile: Dict, message_complexity: str) -> str:
        """Decide quale modello usare basato su profilo utente e complessità"""
        
        # Usa GPT-4 per:
        # - Utenti premium/admin
        # - Richieste molto complesse
        # - Materie difficili
        
        user_role = user_profile.get('ruolo', 'studente')
        difficulty_pref = user_profile.get('difficulty_preference', 'medium')
        
        if (user_role in ['admin', 'professore'] or 
            message_complexity == 'high' or 
            difficulty_pref == 'advanced'):
            return 'gpt-4o'
        
        return 'gpt-3.5-turbo'

    def track_cost(self, user_id: int, model_used: str, input_tokens: int, 
                   output_tokens: int, cost: float, request_type: str = 'chat', cached: bool = False):
        """Traccia il costo di una richiesta"""
        cost_tracked = False
        budget_updated = False
        
        try:
            # Salva tracking costo
            db_manager.execute('''
                INSERT INTO ai_cost_tracking 
                (user_id, model_used, input_tokens, output_tokens, cost_usd, request_type, cached)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, model_used, input_tokens, output_tokens, cost, request_type, cached))
            cost_tracked = True
            
            # Aggiorna budget utente se non cached
            if not cached:
                db_manager.execute('''
                    UPDATE ai_user_limits 
                    SET current_daily_usage = current_daily_usage + %s,
                        current_monthly_usage = current_monthly_usage + %s
                    WHERE user_id = %s
                ''', (cost, cost, user_id))
                budget_updated = True
            
            log_ai_request(
                model=model_used,
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost,
                duration_ms=0,
                success=True,
                user_id=user_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_type=request_type,
                cached=cached
            )
            
        except Exception as e:
            logger.error(
                event_type='ai_cost_tracking_failed',
                message='Errore durante tracking costo AI',
                domain='ai',
                error=str(e),
                user_id=user_id,
                model_used=model_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                request_type=request_type,
                cached=cached,
                cost_tracked=cost_tracked,
                budget_updated=budget_updated,
                exc_info=True
            )

    def get_usage_stats(self, user_id: int) -> Dict:
        """Ottieni statistiche di utilizzo per un utente"""
        try:
            # Statistiche generali
            stats = db_manager.query('''
                SELECT 
                    COUNT(*) as total_requests,
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COALESCE(AVG(cost_usd), 0) as avg_cost,
                    SUM(CASE WHEN cached = TRUE THEN 1 ELSE 0 END) as cache_hits
                FROM ai_cost_tracking 
                WHERE user_id = %s
            ''', (user_id,), one=True)
            
            # Statistiche per modello
            model_stats = db_manager.query('''
                SELECT model_used, COUNT(*) as count, COALESCE(SUM(cost_usd), 0) as total_cost
                FROM ai_cost_tracking 
                WHERE user_id = %s
                GROUP BY model_used
            ''', (user_id,), many=True)
            
            # Limiti correnti
            limits = db_manager.query('''
                SELECT daily_limit, monthly_limit, current_daily_usage, current_monthly_usage
                FROM ai_user_limits 
                WHERE user_id = %s
            ''', (user_id,), one=True)
            
            total_requests = stats.get('total_requests') if stats else 0
            total_cost = stats.get('total_cost') if stats else 0.0
            avg_cost = stats.get('avg_cost') if stats else 0.0
            cache_hits = stats.get('cache_hits') if stats else 0
            
            return {
                'total_requests': int(total_requests) if total_requests else 0,
                'total_cost': float(total_cost) if total_cost else 0.0,
                'avg_cost': float(avg_cost) if avg_cost else 0.0,
                'cache_hits': int(cache_hits) if cache_hits else 0,
                'cache_rate': (int(cache_hits) / max(int(total_requests), 1)) * 100 if cache_hits else 0.0,
                'model_usage': [{'model': row.get('model_used'), 'count': int(row.get('count')), 'cost': float(row.get('total_cost'))} for row in model_stats] if model_stats else [],
                'limits': {
                    'daily_limit': float(limits.get('daily_limit')) if limits else 2.0,
                    'monthly_limit': float(limits.get('monthly_limit')) if limits else 30.0,
                    'daily_usage': float(limits.get('current_daily_usage')) if limits else 0.0,
                    'monthly_usage': float(limits.get('current_monthly_usage')) if limits else 0.0
                } if limits else None
            }
            
        except Exception as e:
            logger.error(
                event_type='ai_usage_stats_failed',
                message='Errore durante recupero statistiche utilizzo AI',
                domain='ai',
                error=str(e),
                user_id=user_id,
                exc_info=True
            )
            return {}

    def optimize_cache(self):
        """Ottimizza la cache rimuovendo vecchie entry"""
        try:
            # Rimuovi cache più vecchia di 7 giorni
            result = db_manager.execute('''
                DELETE FROM ai_response_cache 
                WHERE timestamp < NOW() - INTERVAL '7 days'
            ''')
            
            # Rimuovi cache con hit_count basso se abbiamo più di 1000 entry
            total_cache = db_manager.query('SELECT COUNT(*) as count FROM ai_response_cache', one=True)
            total_count = total_cache.get('count') if total_cache else 0
            
            if total_count > 1000:
                # Mantieni solo le 800 entry più utilizzate
                db_manager.execute('''
                    DELETE FROM ai_response_cache 
                    WHERE id NOT IN (
                        SELECT id FROM ai_response_cache 
                        ORDER BY hit_count DESC, last_accessed DESC 
                        LIMIT 800
                    )
                ''')
                
            logger.info(
                event_type='ai_cache_optimized',
                message='Cache AI ottimizzata: vecchie entry rimosse',
                domain='ai'
            )
                
        except Exception as e:
            logger.error(
                event_type='ai_cache_optimization_failed',
                message='Errore durante ottimizzazione cache AI',
                domain='ai',
                error=str(e),
                exc_info=True
            )

def analyze_message_complexity(message: str) -> str:
    """Analizza la complessità di un messaggio"""
    word_count = len(message.split())
    complex_keywords = [
        'analizza', 'confronta', 'dimostra', 'spiega dettagliatamente',
        'qual è la differenza', 'come funziona', 'perché', 'cause ed effetti'
    ]
    
    if word_count > 50 or any(keyword in message.lower() for keyword in complex_keywords):
        return 'high'
    elif word_count > 20:
        return 'medium'
    else:
        return 'low'

def optimize_ai_costs(message, user_profile, user_id):
    """Funzione principale per ottimizzare i costi AI"""
    cost_manager = AICostManager()
    
    # 1. Controllo cache
    user_context = f"{user_profile.get('conversation_style', '')}{user_profile.get('learning_preferences', '')}"
    cached_response = cost_manager.get_cached_response(message, user_context)
    if cached_response:
        return cached_response, 0.0  # Costo zero per cache hit
    
    # 2. Analizza complessità messaggio
    complexity = analyze_message_complexity(message)
    
    # 3. Scegli modello ottimale
    optimal_model = cost_manager.should_use_premium_model(user_profile, complexity)
    
    # 4. Stima costi
    input_tokens = cost_manager.estimate_tokens(message)
    estimated_output = 150  # Media token di risposta
    estimated_cost = cost_manager.calculate_cost(optimal_model, input_tokens, estimated_output)
    
    # 5. Controlla budget
    can_proceed, reason = cost_manager.check_budget_limits(user_id, estimated_cost)
    if not can_proceed:
        return f"Mi dispiace, ho raggiunto il limite di budget. {reason} 💰", 0.0
    
    return None, estimated_cost  # Procedi con la richiesta

# Istanza globale per ottimizzazione
cost_manager = AICostManager()
