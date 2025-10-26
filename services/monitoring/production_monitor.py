# Sistema di monitoring produzione per SKAILA
# Ottimizzato per ambiente scolastico ad alto traffico

import time
import psutil
import threading
import logging
import json
from datetime import datetime
from database_manager import db_manager
from performance_cache import get_cache_health

class ProductionMonitor:
    """Sistema monitoring per deployment produzione"""
    
    def __init__(self):
        self.metrics = {
            'requests_count': 0,
            'errors_count': 0,
            'active_users': 0,
            'response_times': [],
            'db_connections': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        
        self.logger = logging.getLogger('skaila_production')
        self.setup_logging()
        self.start_monitoring()
    
    def setup_logging(self):
        """Configura logging per produzione - IMPORTANTE: usa stdout per autoscale"""
        import sys
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.logger.info("✅ Logging configurato per stdout (autoscale-friendly)")
    
    def start_monitoring(self):
        """Avvia thread monitoring background"""
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        self.logger.info("🚀 Sistema monitoring produzione avviato")
    
    def _monitor_loop(self):
        """Loop monitoring continuo"""
        while True:
            try:
                # Metriche sistema
                self.metrics['memory_usage'] = psutil.virtual_memory().percent
                self.metrics['cpu_usage'] = psutil.cpu_percent()
                
                # Metriche database
                self._check_db_health()
                
                # Log metriche ogni 5 minuti
                if int(time.time()) % 300 == 0:
                    self.log_metrics()
                
                time.sleep(30)  # Check ogni 30 secondi
                
            except Exception as e:
                self.logger.error(f"Errore monitoring: {e}")
    
    def _check_db_health(self):
        """Monitora salute database"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                if db_manager.db_type == 'postgresql':
                    # Query di health check PostgreSQL
                    cursor.execute("""
                        SELECT 
                            numbackends as active_connections,
                            xact_commit + xact_rollback as transactions,
                            tup_returned + tup_fetched as tuples_accessed
                        FROM pg_stat_database 
                        WHERE datname = current_database()
                    """)
                    stats = cursor.fetchone()
                    if stats:
                        self.metrics['db_connections'] = stats[0] or 0
                else:
                    # SQLite health check semplice
                    cursor.execute("SELECT COUNT(*) FROM utenti")
                    cursor.fetchone()
                    
        except Exception as e:
            self.logger.warning(f"DB health check failed: {e}")
            self.metrics['errors_count'] += 1
    
    def record_request(self, response_time, status_code):
        """Registra metriche richiesta"""
        self.metrics['requests_count'] += 1
        self.metrics['response_times'].append(response_time)
        
        # Mantieni solo ultimi 1000 tempi di risposta
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
        
        if status_code >= 400:
            self.metrics['errors_count'] += 1
    
    def update_active_users(self, count):
        """Aggiorna conteggio utenti attivi"""
        self.metrics['active_users'] = count
    
    def log_metrics(self):
        """Log metriche dettagliate"""
        avg_response_time = 0
        if self.metrics['response_times']:
            avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        
        cache_stats = get_cache_health()
        
        metrics_summary = {
            'timestamp': datetime.now().isoformat(),
            'performance': {
                'requests_total': self.metrics['requests_count'],
                'errors_total': self.metrics['errors_count'],
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'active_users': self.metrics['active_users']
            },
            'system': {
                'memory_usage_percent': self.metrics['memory_usage'],
                'cpu_usage_percent': self.metrics['cpu_usage'],
                'db_connections': self.metrics['db_connections']
            },
            'cache': cache_stats
        }
        
        self.logger.info(f"METRICS: {json.dumps(metrics_summary, indent=2)}")
        
        # Alert se metriche critiche
        if self.metrics['memory_usage'] > 85:
            self.logger.warning(f"⚠️ MEMORIA ALTA: {self.metrics['memory_usage']}%")
        
        if self.metrics['cpu_usage'] > 90:
            self.logger.warning(f"⚠️ CPU ALTA: {self.metrics['cpu_usage']}%")
        
        if avg_response_time > 2.0:  # > 2 secondi
            self.logger.warning(f"⚠️ RESPONSE TIME ALTO: {avg_response_time:.2f}s")
    
    def get_health_status(self):
        """Status salute per endpoint /health"""
        avg_response_time = 0
        if self.metrics['response_times']:
            avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        
        # Determina status complessivo
        status = "healthy"
        if (self.metrics['memory_usage'] > 85 or 
            self.metrics['cpu_usage'] > 90 or 
            avg_response_time > 2.0):
            status = "warning"
        
        if (self.metrics['memory_usage'] > 95 or 
            self.metrics['cpu_usage'] > 95 or 
            avg_response_time > 5.0):
            status = "critical"
        
        return {
            'status': status,
            'uptime': time.time(),
            'metrics': {
                'requests_total': self.metrics['requests_count'],
                'errors_total': self.metrics['errors_count'], 
                'active_users': self.metrics['active_users'],
                'avg_response_time': round(avg_response_time, 3),
                'memory_usage_percent': self.metrics['memory_usage'],
                'cpu_usage_percent': self.metrics['cpu_usage'],
                'db_connections': self.metrics['db_connections']
            },
            'cache_health': get_cache_health()
        }

# Istanza globale monitoring
production_monitor = ProductionMonitor()

def monitor_request(func):
    """Decorator per monitorare richieste - FIXED: evita conflicts Flask endpoint"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            response_time = time.time() - start_time
            production_monitor.record_request(response_time, 200)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            production_monitor.record_request(response_time, 500)
            raise e
    return wrapper

print("✅ Sistema monitoring produzione configurato")