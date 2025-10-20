
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

class AICostManager:
    def __init__(self):
        self.daily_budget_limit = 10.0  # $10 al giorno
        self.monthly_budget_limit = 200.0  # $200 al mese
        self.cache_duration_hours = 24  # Cache risposte per 24h
        
        # Inizializza tabelle di tracking
        self.init_cost_tracking_tables()
        
    def init_cost_tracking_tables(self):
        """Inizializza tabelle per tracking costi e cache"""
        conn = sqlite3.connect('skaila.db')
        
        # Tabella per tracking costi
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_cost_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                model_used TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost_usd REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                request_type TEXT,
                cached BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tabella per cache intelligente
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_response_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_hash TEXT UNIQUE,
                user_context_hash TEXT,
                message TEXT,
                response TEXT,
                model_used TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hit_count INTEGER DEFAULT 1,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella per budget limits per utente
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_user_limits (
                user_id INTEGER PRIMARY KEY,
                daily_limit REAL DEFAULT 2.0,
                monthly_limit REAL DEFAULT 30.0,
                current_daily_usage REAL DEFAULT 0.0,
                current_monthly_usage REAL DEFAULT 0.0,
                last_reset_daily DATE,
                last_reset_monthly DATE,
                FOREIGN KEY (user_id) REFERENCES utenti (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Tabelle AI Cost Manager inizializzate")

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calcola il costo per una richiesta OpenAI"""
        costs = {
            'gpt-4': {
                'input': 0.03 / 1000,  # $0.03 per 1K token
                'output': 0.06 / 1000  # $0.06 per 1K token
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
            
            conn = sqlite3.connect('skaila.db')
            
            # Cerca nella cache (non più vecchia di cache_duration_hours)
            cached = conn.execute('''
                SELECT response, id FROM ai_response_cache 
                WHERE request_hash = ? 
                AND timestamp > datetime('now', '-{} hours')
                ORDER BY hit_count DESC, last_accessed DESC
                LIMIT 1
            '''.format(self.cache_duration_hours), (request_hash,)).fetchone()
            
            if cached:
                # Aggiorna statistiche cache
                conn.execute('''
                    UPDATE ai_response_cache 
                    SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (cached[1],))
                conn.commit()
                conn.close()
                
                print(f"✅ Cache hit per richiesta: {message[:30]}...")
                return cached[0]
                
            conn.close()
            return None
            
        except Exception as e:
            print(f"❌ Errore cache lookup: {e}")
            return None

    def cache_response(self, message: str, response: str, user_context: str, model_used: str):
        """Salva una risposta nella cache"""
        try:
            request_hash = self.generate_request_hash(message, user_context)
            user_context_hash = hashlib.md5(user_context.encode()).hexdigest()
            
            conn = sqlite3.connect('skaila.db')
            
            # Inserisci o aggiorna cache
            conn.execute('''
                INSERT OR REPLACE INTO ai_response_cache 
                (request_hash, user_context_hash, message, response, model_used)
                VALUES (%s, %s, %s, %s, %s)
            ''', (request_hash, user_context_hash, message, response, model_used))
            
            conn.commit()
            conn.close()
            
            print(f"💾 Risposta salvata in cache: {message[:30]}...")
            
        except Exception as e:
            print(f"❌ Errore salvataggio cache: {e}")

    def check_budget_limits(self, user_id: int, estimated_cost: float) -> Tuple[bool, str]:
        """Controlla se l'utente può fare la richiesta senza superare i limiti"""
        try:
            conn = sqlite3.connect('skaila.db')
            
            # Ottieni o crea record budget utente
            user_limits = conn.execute('''
                SELECT * FROM ai_user_limits WHERE user_id = ?
            ''', (user_id,)).fetchone()
            
            today = datetime.now().date()
            current_month = today.replace(day=1)
            
            if not user_limits:
                # Crea record per nuovo utente
                conn.execute('''
                    INSERT INTO ai_user_limits 
                    (user_id, last_reset_daily, last_reset_monthly)
                    VALUES (%s, %s, %s)
                ''', (user_id, today, current_month))
                conn.commit()
                user_limits = conn.execute('''
                    SELECT * FROM ai_user_limits WHERE user_id = ?
                ''', (user_id,)).fetchone()
            
            # Reset giornaliero se necessario
            if user_limits[5] != today.isoformat():  # last_reset_daily
                conn.execute('''
                    UPDATE ai_user_limits 
                    SET current_daily_usage = 0.0, last_reset_daily = ?
                    WHERE user_id = ?
                ''', (today, user_id))
            
            # Reset mensile se necessario
            if user_limits[6] != current_month.isoformat():  # last_reset_monthly
                conn.execute('''
                    UPDATE ai_user_limits 
                    SET current_monthly_usage = 0.0, last_reset_monthly = ?
                    WHERE user_id = ?
                ''', (current_month, user_id))
            
            # Ricarica dati aggiornati
            user_limits = conn.execute('''
                SELECT * FROM ai_user_limits WHERE user_id = ?
            ''', (user_id,)).fetchone()
            
            daily_limit = user_limits[1]    # daily_limit
            monthly_limit = user_limits[2]  # monthly_limit
            daily_usage = user_limits[3]    # current_daily_usage
            monthly_usage = user_limits[4]  # current_monthly_usage
            
            conn.close()
            
            # Controlli limiti
            if daily_usage + estimated_cost > daily_limit:
                return False, f"Limite giornaliero superato (${daily_usage:.3f}/${daily_limit:.2f})"
            
            if monthly_usage + estimated_cost > monthly_limit:
                return False, f"Limite mensile superato (${monthly_usage:.2f}/${monthly_limit:.2f})"
            
            return True, "OK"
            
        except Exception as e:
            print(f"❌ Errore controllo budget: {e}")
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
            return 'gpt-4'
        
        return 'gpt-3.5-turbo'

    def track_cost(self, user_id: int, model_used: str, input_tokens: int, 
                   output_tokens: int, cost: float, request_type: str = 'chat', cached: bool = False):
        """Traccia il costo di una richiesta"""
        try:
            conn = sqlite3.connect('skaila.db')
            
            # Salva tracking costo
            conn.execute('''
                INSERT INTO ai_cost_tracking 
                (user_id, model_used, input_tokens, output_tokens, cost_usd, request_type, cached)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, model_used, input_tokens, output_tokens, cost, request_type, cached))
            
            # Aggiorna budget utente se non cached
            if not cached:
                conn.execute('''
                    UPDATE ai_user_limits 
                    SET current_daily_usage = current_daily_usage + ?,
                        current_monthly_usage = current_monthly_usage + ?
                    WHERE user_id = ?
                ''', (cost, cost, user_id))
            
            conn.commit()
            conn.close()
            
            print(f"💰 Costo tracciato: ${cost:.4f} ({model_used}) per user {user_id}")
            
        except Exception as e:
            print(f"❌ Errore tracking costo: {e}")

    def get_usage_stats(self, user_id: int) -> Dict:
        """Ottieni statistiche di utilizzo per un utente"""
        try:
            conn = sqlite3.connect('skaila.db')
            
            # Statistiche generali
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(cost_usd) as total_cost,
                    AVG(cost_usd) as avg_cost,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits
                FROM ai_cost_tracking 
                WHERE user_id = ?
            ''', (user_id,)).fetchone()
            
            # Statistiche per modello
            model_stats = conn.execute('''
                SELECT model_used, COUNT(*) as count, SUM(cost_usd) as total_cost
                FROM ai_cost_tracking 
                WHERE user_id = ?
                GROUP BY model_used
            ''', (user_id,)).fetchall()
            
            # Limiti correnti
            limits = conn.execute('''
                SELECT daily_limit, monthly_limit, current_daily_usage, current_monthly_usage
                FROM ai_user_limits 
                WHERE user_id = ?
            ''', (user_id,)).fetchone()
            
            conn.close()
            
            return {
                'total_requests': stats[0] or 0,
                'total_cost': stats[1] or 0.0,
                'avg_cost': stats[2] or 0.0,
                'cache_hits': stats[3] or 0,
                'cache_rate': (stats[3] / max(stats[0], 1)) * 100,
                'model_usage': [{'model': row[0], 'count': row[1], 'cost': row[2]} for row in model_stats],
                'limits': {
                    'daily_limit': limits[0] if limits else 2.0,
                    'monthly_limit': limits[1] if limits else 30.0,
                    'daily_usage': limits[2] if limits else 0.0,
                    'monthly_usage': limits[3] if limits else 0.0
                } if limits else None
            }
            
        except Exception as e:
            print(f"❌ Errore statistiche utilizzo: {e}")
            return {}

    def optimize_cache(self):
        """Ottimizza la cache rimuovendo vecchie entry"""
        try:
            conn = sqlite3.connect('skaila.db')
            
            # Rimuovi cache più vecchia di 7 giorni
            deleted = conn.execute('''
                DELETE FROM ai_response_cache 
                WHERE timestamp < datetime('now', '-7 days')
            ''').rowcount
            
            # Rimuovi cache con hit_count basso se abbiamo più di 1000 entry
            total_cache = conn.execute('SELECT COUNT(*) FROM ai_response_cache').fetchone()[0]
            
            if total_cache > 1000:
                # Mantieni solo le 800 entry più utilizzate
                conn.execute('''
                    DELETE FROM ai_response_cache 
                    WHERE id NOT IN (
                        SELECT id FROM ai_response_cache 
                        ORDER BY hit_count DESC, last_accessed DESC 
                        LIMIT 800
                    )
                ''')
                
            conn.commit()
            conn.close()
            
            if deleted > 0:
                print(f"🧹 Cache ottimizzata: {deleted} entry rimosse")
                
        except Exception as e:
            print(f"❌ Errore ottimizzazione cache: {e}")

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
