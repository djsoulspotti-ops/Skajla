"""
SKAILA Structured Logging System
Task 7: Enhanced error handling and structured logging
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredLogger:
    """Production-ready structured logging for SKAILA"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """Configure structured logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Log with structured context"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }
        
        if context:
            log_entry.update(context)
        
        log_message = json.dumps(log_entry)
        
        if level == 'ERROR':
            self.logger.error(log_message)
        elif level == 'WARNING':
            self.logger.warning(log_message)
        elif level == 'INFO':
            self.logger.info(log_message)
        elif level == 'DEBUG':
            self.logger.debug(log_message)
    
    def info(self, message: str, **kwargs):
        """Log info level"""
        self.log('INFO', message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level"""
        self.log('ERROR', message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level"""
        self.log('WARNING', message, kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level"""
        self.log('DEBUG', message, kwargs)

# Create logger instances for different modules
auth_logger = StructuredLogger('skaila.auth')
api_logger = StructuredLogger('skaila.api')
db_logger = StructuredLogger('skaila.database')
security_logger = StructuredLogger('skaila.security')
