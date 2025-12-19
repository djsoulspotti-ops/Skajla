"""
Instant Groups Cleanup Background Job
Auto-cleanup gruppi istantanei scaduti e inattivi
"""

import schedule
import time
import threading
import logging
from services.messaging.instant_groups_service import instant_groups_service

logger = logging.getLogger(__name__)


class InstantGroupsCleanupJob:
    """Background job per cleanup gruppi istantanei"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Avvia background job"""
        if self.running:
            logger.warning("Cleanup job già in esecuzione")
            return
        
        self.running = True
        
        # Schedule jobs
        schedule.every().hour.do(self.cleanup_expired)
        schedule.every(6).hours.do(self.cleanup_inactive)
        
        # Esegui prima volta immediatamente
        self.cleanup_expired()
        
        # Avvia thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("🚀 Instant Groups cleanup job started")
    
    def stop(self):
        """Ferma background job"""
        self.running = False
        schedule.clear()
        logger.info("Instant Groups cleanup job stopped")
    
    def _run_scheduler(self):
        """Loop scheduler"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check ogni minuto
            except Exception as e:
                logger.error(f"Errore scheduler cleanup: {e}")
                time.sleep(300)  # Wait 5 min su errore
    
    def cleanup_expired(self):
        """Cleanup gruppi scaduti"""
        try:
            count = instant_groups_service.cleanup_expired_groups()
            if count > 0:
                logger.info(f"🗑️ Eliminati {count} gruppi scaduti")
        except Exception as e:
            logger.error(f"Errore cleanup expired: {e}")
    
    def cleanup_inactive(self):
        """Cleanup gruppi inattivi (24h senza messaggi)"""
        try:
            count = instant_groups_service.cleanup_inactive_groups(hours=24)
            if count > 0:
                logger.info(f"🗑️ Eliminati {count} gruppi inattivi")
        except Exception as e:
            logger.error(f"Errore cleanup inactive: {e}")


# Istanza globale
cleanup_job = InstantGroupsCleanupJob()
