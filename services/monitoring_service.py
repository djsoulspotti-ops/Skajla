"""
Production Monitoring Service per SKAILA
Structured logging, metrics collection, e performance monitoring
"""

import json
import time
import logging
import eventlet
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, Optional
from database_manager import db_manager
from environment_manager import env_manager

class ProductionLogger:
    """Structured logging per production monitoring"""
    
    def __init__(self):
        self.logger = self._setup_structured_logger()
        
    def _setup_structured_logger(self):
        """Configura logger strutturato per production"""
        logger = logging.getLogger('skaila_monitoring')
        logger.setLevel(logging.INFO)
        
        # Rimuovi handler esistenti
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler per stdout (container-friendly)
        handler = logging.StreamHandler()
        
        # Formatter JSON per structured logging
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.propagate = False
        
        return logger
    
    def info(self, event: str, **kwargs):
        """Log info event con structured data"""
        self._log('INFO', event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning event con structured data"""
        self._log('WARNING', event, **kwargs)
    
    def error(self, event: str, error: Optional[Exception] = None, **kwargs):
        """Log error event con structured data"""
        if error:
            kwargs['error_type'] = error.__class__.__name__
            kwargs['error_message'] = str(error)
        self._log('ERROR', event, **kwargs)
    
    def _log(self, level: str, event: str, **kwargs):
        """Internal logging con structured format"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'event': event,
            'service': 'skaila',
            'environment': 'production' if env_manager.is_production() else 'development',
            **kwargs
        }
        
        getattr(self.logger, level.lower())(json.dumps(log_data))

class StructuredFormatter(logging.Formatter):
    """Formatter JSON per structured logs"""
    
    def format(self, record):
        """Format log record come JSON"""
        # Se il message è già JSON, usalo direttamente
        try:
            log_data = json.loads(record.getMessage())
            return json.dumps(log_data, separators=(',', ':'))
        except (json.JSONDecodeError, ValueError):
            # Fallback per log non-strutturati
            return json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'logger': record.name,
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }, separators=(',', ':'))

class MetricsCollector:
    """Collector per application metrics in real-time"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(deque)
        self.lock = eventlet.semaphore.Semaphore(1)
        
        # Retention policy
        self.max_timer_entries = 1000
        self.timer_retention_hours = 24
        
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Incrementa counter metric"""
        with self.lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set gauge metric value"""
        with self.lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record timing metric"""
        with self.lock:
            key = self._make_key(name, tags)
            timestamp = datetime.utcnow()
            
            self.timers[key].append((timestamp, duration_ms))
            
            # Cleanup old entries
            cutoff = timestamp - timedelta(hours=self.timer_retention_hours)
            while self.timers[key] and self.timers[key][0][0] < cutoff:
                self.timers[key].popleft()
            
            # Limit size
            while len(self.timers[key]) > self.max_timer_entries:
                self.timers[key].popleft()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary di tutte le metrics"""
        with self.lock:
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'timers': {}
            }
            
            # Timer statistics
            for key, timer_data in self.timers.items():
                if timer_data:
                    values = [entry[1] for entry in timer_data]
                    summary['timers'][key] = {
                        'count': len(values),
                        'min_ms': min(values),
                        'max_ms': max(values),
                        'avg_ms': sum(values) / len(values),
                        'p95_ms': self._percentile(values, 95),
                        'p99_ms': self._percentile(values, 99)
                    }
            
            return summary
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create metric key con tags"""
        if not tags:
            return name
        
        tag_parts = [f"{k}={v}" for k, v in sorted(tags.items())]
        return f"{name}{{{',' .join(tag_parts)}}}"
    
    def _percentile(self, values: list, p: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((p / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

class PerformanceMonitor:
    """Monitor per performance dell'applicazione"""
    
    def __init__(self, metrics_collector: MetricsCollector, logger: ProductionLogger):
        self.metrics = metrics_collector
        self.logger = logger
    
    def monitor_request(self, request_path: str, method: str = 'GET'):
        """Context manager per monitoring HTTP requests"""
        return RequestMonitor(self.metrics, self.logger, request_path, method)
    
    def monitor_database_query(self, query_type: str = 'SELECT'):
        """Context manager per monitoring database queries"""
        return DatabaseMonitor(self.metrics, self.logger, query_type)
    
    def log_user_action(self, user_id: str, action: str, **kwargs):
        """Log user action per audit trail"""
        self.logger.info('user_action', 
                        user_id=user_id, 
                        action=action, 
                        **kwargs)
        
        self.metrics.increment_counter('user_actions_total', 
                                     tags={'action': action})

class RequestMonitor:
    """Context manager per monitoring HTTP requests"""
    
    def __init__(self, metrics: MetricsCollector, logger: ProductionLogger, path: str, method: str):
        self.metrics = metrics
        self.logger = logger
        self.path = path
        self.method = method
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - (self.start_time or 0)) * 1000
        
        # Metrics
        tags = {'method': self.method, 'path': self.path}
        self.metrics.record_timer('http_request_duration_ms', duration_ms, tags)
        self.metrics.increment_counter('http_requests_total', tags=tags)
        
        # Log se slow request (>1s)
        if duration_ms > 1000:
            self.logger.warning('slow_request',
                              path=self.path,
                              method=self.method,
                              duration_ms=duration_ms)
        
        # Log se error
        if exc_type:
            self.metrics.increment_counter('http_errors_total', tags=tags)
            self.logger.error('request_error',
                            path=self.path,
                            method=self.method,
                            duration_ms=duration_ms,
                            error=exc_val)

class DatabaseMonitor:
    """Context manager per monitoring database operations"""
    
    def __init__(self, metrics: MetricsCollector, logger: ProductionLogger, query_type: str):
        self.metrics = metrics
        self.logger = logger
        self.query_type = query_type
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - (self.start_time or 0)) * 1000
        
        # Metrics
        tags = {'query_type': self.query_type, 'db_type': db_manager.db_type}
        self.metrics.record_timer('db_query_duration_ms', duration_ms, tags)
        self.metrics.increment_counter('db_queries_total', tags=tags)
        
        # Log se slow query (>500ms)
        if duration_ms > 500:
            self.logger.warning('slow_query',
                              query_type=self.query_type,
                              db_type=db_manager.db_type,
                              duration_ms=duration_ms)
        
        # Log se error
        if exc_type:
            self.metrics.increment_counter('db_errors_total', tags=tags)
            self.logger.error('db_query_error',
                            query_type=self.query_type,
                            db_type=db_manager.db_type,
                            duration_ms=duration_ms,
                            error=exc_val)

# Global instances
production_logger = ProductionLogger()
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector, production_logger)