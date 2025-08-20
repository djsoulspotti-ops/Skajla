
import time
import psutil
import threading
from collections import deque
from datetime import datetime

class PerformanceMonitor:
    """Monitora performance per 30+ utenti simultanei"""
    
    def __init__(self):
        self.metrics = {
            'active_connections': 0,
            'db_queries_per_sec': deque(maxlen=60),
            'memory_usage': deque(maxlen=60),
            'cpu_usage': deque(maxlen=60),
            'response_times': deque(maxlen=100)
        }
        self.start_monitoring()
    
    def start_monitoring(self):
        """Avvia monitoraggio in background"""
        def monitor():
            while True:
                # Raccogli metriche sistema
                self.metrics['memory_usage'].append(psutil.virtual_memory().percent)
                self.metrics['cpu_usage'].append(psutil.cpu_percent())
                time.sleep(1)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def record_db_query(self):
        """Registra query database"""
        self.metrics['db_queries_per_sec'].append(time.time())
    
    def record_response_time(self, duration_ms):
        """Registra tempo risposta"""
        self.metrics['response_times'].append(duration_ms)
    
    def get_stats(self):
        """Ottieni statistiche correnti"""
        now = time.time()
        recent_queries = [t for t in self.metrics['db_queries_per_sec'] if now - t < 1]
        
        return {
            'active_connections': self.metrics['active_connections'],
            'queries_per_second': len(recent_queries),
            'avg_response_time': sum(self.metrics['response_times']) / len(self.metrics['response_times']) if self.metrics['response_times'] else 0,
            'memory_usage': self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else 0,
            'cpu_usage': self.metrics['cpu_usage'][-1] if self.metrics['cpu_usage'] else 0,
            'system_health': 'good' if len(recent_queries) < 50 and (self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else 0) < 80 else 'warning'
        }

# Istanza globale
perf_monitor = PerformanceMonitor()
