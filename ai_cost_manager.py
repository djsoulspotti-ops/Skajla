
import json
import time
from datetime import datetime, timedelta
import hashlib

class AICostManager:
    def __init__(self):
        self.cache = {}
        self.usage_stats = {
            'daily_requests': 0,
            'monthly_cost': 0.0,
            'cache_hits': 0,
            'api_calls': 0
        }
        self.cost_limits = {
            'daily_max': 5.0,  # $5 al giorno
            'monthly_max': 100.0,  # $100 al mese
            'per_user_max': 0.10  # $0.10 per utente al mese
        }
        
    def should_use_premium_model(self, user_profile, message_complexity):
        """Decide se usare GPT-4 o GPT-3.5 basandosi su budget e complessità"""
        
        # Studenti premium o messaggi complessi → GPT-4o Mini
        if (user_profile.get('subscription') == 'premium' or 
            message_complexity > 0.7 or 
            any(subject in message_complexity for subject in ['fisica', 'matematica'])):
            return 'gpt-4o-mini'
        
        # Conversazioni semplici → GPT-3.5 Turbo
        return 'gpt-3.5-turbo'
    
    def get_cached_response(self, message, user_context):
        """Controlla cache per risposte simili"""
        cache_key = hashlib.md5(f"{message.lower()}{user_context}".encode()).hexdigest()
        
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            # Cache valida per 1 ora
            if time.time() - cache_data['timestamp'] < 3600:
                self.usage_stats['cache_hits'] += 1
                return cache_data['response']
        
        return None
    
    def cache_response(self, message, user_context, response):
        """Salva risposta in cache"""
        cache_key = hashlib.md5(f"{message.lower()}{user_context}".encode()).hexdigest()
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def estimate_tokens(self, text):
        """Stima approssimativa dei token (1 token ≈ 4 caratteri)"""
        return len(text) // 4
    
    def calculate_cost(self, model, input_tokens, output_tokens):
        """Calcola costo della richiesta"""
        costs = {
            'gpt-4o-mini': {'input': 0.15/1000000, 'output': 0.60/1000000},
            'gpt-3.5-turbo': {'input': 0.50/1000000, 'output': 1.50/1000000},
            'claude-3.5-haiku': {'input': 0.25/1000000, 'output': 1.25/1000000}
        }
        
        if model in costs:
            return (input_tokens * costs[model]['input'] + 
                   output_tokens * costs[model]['output'])
        return 0.0
    
    def check_budget_limits(self, estimated_cost):
        """Controlla se la richiesta supera i limiti di budget"""
        daily_projected = self.usage_stats['monthly_cost'] / 30
        
        if (daily_projected + estimated_cost > self.cost_limits['daily_max'] or
            self.usage_stats['monthly_cost'] + estimated_cost > self.cost_limits['monthly_max']):
            return False
        
        return True
    
    def get_cost_analytics(self):
        """Genera analytics sui costi"""
        cache_efficiency = (self.usage_stats['cache_hits'] / 
                          max(self.usage_stats['api_calls'] + self.usage_stats['cache_hits'], 1)) * 100
        
        return {
            'monthly_cost': self.usage_stats['monthly_cost'],
            'daily_average': self.usage_stats['monthly_cost'] / 30,
            'cache_efficiency': f"{cache_efficiency:.1f}%",
            'cost_per_user': self.usage_stats['monthly_cost'] / 1000,  # Assumendo 1000 utenti
            'budget_utilization': (self.usage_stats['monthly_cost'] / self.cost_limits['monthly_max']) * 100
        }

# Integrazione con il chatbot esistente
def optimize_ai_costs(message, user_profile, user_id):
    """Funzione principale per ottimizzare i costi AI"""
    cost_manager = AICostManager()
    
    # 1. Controllo cache
    cached_response = cost_manager.get_cached_response(message, str(user_profile))
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
    if not cost_manager.check_budget_limits(estimated_cost):
        return "Mi dispiace, ho raggiunto il limite di budget giornaliero. Riprova domani! 💰", 0.0
    
    return None, estimated_cost  # Procedi con API call

def analyze_message_complexity(message):
    """Analizza la complessità del messaggio per scegliere il modello"""
    complexity_indicators = {
        'high': ['equazione', 'teorema', 'dimostra', 'calcola', 'fisica quantistica', 'derivata'],
        'medium': ['spiegami', 'perché', 'come funziona', 'differenza'],
        'low': ['ciao', 'grazie', 'come stai', 'aiuto']
    }
    
    message_lower = message.lower()
    
    for indicator in complexity_indicators['high']:
        if indicator in message_lower:
            return 0.8
    
    for indicator in complexity_indicators['medium']:
        if indicator in message_lower:
            return 0.5
    
    return 0.3
